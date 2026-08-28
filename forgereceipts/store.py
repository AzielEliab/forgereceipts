"""Append-only ForgeReceipts ledger on top of TemporalLock.

TemporalLock hashes core fields only (timestamp, summary, evidence,
confidence, prev_hash). ForgeReceipts extra keys (kind, child_impact,
file_sha256, private_note, ...) ride on the JSONL line and are ignored
by the core hash. Child impact is *also* written into evidence so it
is hashed. Private notes are extra-only and are never hashed.

There is no modify and no delete. Corrections are new receipts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from temporallock.chain import Chain, VerifyResult
from temporallock.errors import AppendOnlyError
from temporallock.receipt import Receipt

CORE_KEYS = ("timestamp", "summary", "evidence", "confidence", "prev_hash", "hash")

KIND_INCIDENT = "incident"
KIND_JOURNAL = "journal"
KIND_FORENSICS = "forensics"


def compose_evidence(
    body: str,
    *,
    kind: str,
    child_impact: str,
    file_sha256: str | None = None,
    file_name: str | None = None,
) -> str:
    """Put required child-impact (and optional file hash) into hashed evidence."""
    lines = [
        f"KIND: {kind}",
        f"CHILD_IMPACT: {child_impact.strip()}",
    ]
    if file_sha256:
        lines.append(f"FILE_SHA256: {file_sha256}")
    if file_name:
        lines.append(f"FILE_NAME: {file_name}")
    lines.append("")
    lines.append(body.rstrip() if body else "(no additional body)")
    return "\n".join(lines)


class ForgeStore:
    """JSONL-backed store. Chain is in-memory; this class writes extras."""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.path = self.data_dir / "chain.jsonl"
        self._load()

    def _load(self) -> None:
        receipts: list[Receipt] = []
        extras: list[dict[str, Any]] = []
        if self.path.is_file():
            text = self.path.read_text(encoding="utf-8")
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                receipts.append(Receipt.from_dict(obj))
                extras.append({k: v for k, v in obj.items() if k not in CORE_KEYS})
        self.chain = Chain(receipts)
        self._extras = extras

    def reload(self) -> None:
        self._load()

    def __len__(self) -> int:
        return len(self.chain)

    def records(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for rec, extra in zip(self.chain, self._extras, strict=True):
            row = rec.to_dict()
            row.update(extra)
            out.append(row)
        return out

    def records_of(self, kind: str) -> list[dict[str, Any]]:
        return [r for r in self.records() if r.get("kind") == kind]

    def append(
        self,
        *,
        summary: str,
        evidence: str,
        confidence: float = 1.0,
        timestamp: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        extra = dict(extra or {})
        rec = self.chain.append(
            summary=summary,
            evidence=evidence,
            confidence=confidence,
            timestamp=timestamp,
        )
        self._extras.append(extra)
        row = rec.to_dict()
        row.update(extra)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            fh.write("\n")
            fh.flush()
        return row

    def append_incident(
        self,
        *,
        summary: str,
        evidence: str,
        child_impact: str,
        confidence: float = 1.0,
        timestamp: str | None = None,
        file_sha256: str | None = None,
        file_name: str | None = None,
    ) -> dict[str, Any]:
        child_impact = (child_impact or "").strip()
        if not child_impact:
            raise ValueError("child_impact is required")
        composed = compose_evidence(
            evidence,
            kind=KIND_INCIDENT,
            child_impact=child_impact,
            file_sha256=file_sha256,
            file_name=file_name,
        )
        extra: dict[str, Any] = {
            "kind": KIND_INCIDENT,
            "child_impact": child_impact,
        }
        if file_sha256:
            extra["file_sha256"] = file_sha256
        if file_name:
            extra["file_name"] = file_name
        return self.append(
            summary=summary,
            evidence=composed,
            confidence=confidence,
            timestamp=timestamp,
            extra=extra,
        )

    def append_journal(
        self,
        *,
        summary: str,
        evidence: str,
        child_impact: str,
        confidence: float = 1.0,
        timestamp: str | None = None,
        file_sha256: str | None = None,
        file_name: str | None = None,
        private_note: str | None = None,
    ) -> dict[str, Any]:
        child_impact = (child_impact or "").strip()
        if not child_impact:
            raise ValueError("child_impact is required")
        composed = compose_evidence(
            evidence,
            kind=KIND_JOURNAL,
            child_impact=child_impact,
            file_sha256=file_sha256,
            file_name=file_name,
        )
        extra: dict[str, Any] = {
            "kind": KIND_JOURNAL,
            "child_impact": child_impact,
        }
        if file_sha256:
            extra["file_sha256"] = file_sha256
        if file_name:
            extra["file_name"] = file_name
        if private_note:
            # Extra-only: not part of TemporalLock core hash.
            extra["private_note"] = private_note
        return self.append(
            summary=summary,
            evidence=composed,
            confidence=confidence,
            timestamp=timestamp,
            extra=extra,
        )

    def append_forensics(
        self,
        *,
        summary: str,
        file_sha256: str,
        file_name: str,
        child_impact: str = "Hash of a local file retained for later re-verification.",
        confidence: float = 1.0,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        if not file_sha256:
            raise ValueError("file_sha256 is required")
        composed = compose_evidence(
            f"SHA-256 of local file {file_name!r} stored for chain-of-custody.",
            kind=KIND_FORENSICS,
            child_impact=child_impact,
            file_sha256=file_sha256,
            file_name=file_name,
        )
        extra = {
            "kind": KIND_FORENSICS,
            "child_impact": child_impact,
            "file_sha256": file_sha256,
            "file_name": file_name,
        }
        return self.append(
            summary=summary,
            evidence=composed,
            confidence=confidence,
            timestamp=timestamp,
            extra=extra,
        )

    def verify(self) -> VerifyResult:
        return self.chain.verify()

    def refuse_mutate(self) -> None:
        raise AppendOnlyError(
            "cannot mutate: ForgeReceipts/TemporalLock is append-only; "
            "record a correction as a new receipt"
        )


def verify_jsonl(text: str) -> dict[str, Any]:
    """Load a chain JSONL string and return PASS/FAIL plus TemporalLock details."""
    receipts: list[Receipt] = []
    errors: list[str] = []
    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            receipts.append(Receipt.from_dict(obj))
        except Exception as exc:  # noqa: BLE001 — surface parse errors to the UI
            errors.append(f"line {i}: {exc}")
    if errors and not receipts:
        return {
            "ok": False,
            "verdict": "FAIL",
            "length": 0,
            "errors": errors,
            "first_hash": None,
            "last_hash": None,
        }
    result = Chain(receipts).verify()
    all_errors = errors + list(result.errors)
    ok = result.ok and not errors
    return {
        "ok": ok,
        "verdict": "PASS" if ok else "FAIL",
        "length": result.length,
        "errors": all_errors,
        "first_hash": result.first_hash,
        "last_hash": result.last_hash,
    }


def hashed_file_count(records: Iterable[dict[str, Any]]) -> int:
    n = 0
    seen: set[str] = set()
    for rec in records:
        digest = rec.get("file_sha256")
        if isinstance(digest, str) and digest and digest not in seen:
            seen.add(digest)
            n += 1
    return n
