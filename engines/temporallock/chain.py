"""Append-only receipt chain.

``chain.append(...)`` only. No modify, no delete. Corrections and
disputes are new receipts. Divergent chains (forks) are valid and
detectable; this module does not pick a winner.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Sequence

from temporallock.errors import AppendOnlyError, ChainError
from temporallock.hashing import GENESIS_PREV_HASH
from temporallock.receipt import Receipt


@dataclass(frozen=True)
class VerifyResult:
    """Result of walking a chain: hashes and links, nothing interpretive."""

    ok: bool
    length: int
    first_hash: str | None
    last_hash: str | None
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Fork:
    """A prev_hash with more than one child. Forks are allowed."""

    prev_hash: str
    child_hashes: tuple[str, ...]


def detect_forks(receipts: Sequence[Receipt]) -> list[Fork]:
    """Find prev_hash values that have more than one child.

    Does not pick a winner. Order of forks follows first appearance of
    the parent hash; child hashes follow receipt order.
    """
    children: dict[str, list[str]] = {}
    order: list[str] = []
    for rec in receipts:
        if rec.prev_hash not in children:
            order.append(rec.prev_hash)
            children[rec.prev_hash] = []
        children[rec.prev_hash].append(rec.hash)
    return [
        Fork(prev_hash=ph, child_hashes=tuple(children[ph]))
        for ph in order
        if len(children[ph]) > 1
    ]


def _receipt_json_line(receipt: Receipt) -> str:
    """One JSONL line. Confidence stored as a JSON number; hash included.

    This is the *file* encoding, not the canonical hash encoding.
    """
    body = receipt.to_dict()
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _append_line(path: Path, receipt: Receipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Append-only: mode 'a' never rewrites earlier bytes.
    with path.open("a", encoding="utf-8") as fh:
        fh.write(_receipt_json_line(receipt))
        fh.write("\n")
        fh.flush()


class Chain:
    """In-memory and/or JSONL-backed append-only sequence of receipts."""

    def __init__(
        self,
        receipts: Sequence[Receipt] | None = None,
        path: str | Path | None = None,
    ) -> None:
        self._receipts: tuple[Receipt, ...] = tuple(receipts or ())
        self._path: Path | None = Path(path) if path is not None else None

    @property
    def path(self) -> Path | None:
        return self._path

    def __len__(self) -> int:
        return len(self._receipts)

    def __iter__(self) -> Iterator[Receipt]:
        return iter(self._receipts)

    def __getitem__(self, index: int) -> Receipt:
        return self._receipts[index]

    def __bool__(self) -> bool:
        return bool(self._receipts)

    def _refuse(self, action: str) -> None:
        raise AppendOnlyError(
            f"cannot {action}: TemporalLock is append-only; "
            "record a correction as a new receipt"
        )

    def pop(self, *args: object, **kwargs: object) -> None:
        self._refuse("pop")

    def insert(self, *args: object, **kwargs: object) -> None:
        self._refuse("insert")

    def remove(self, *args: object, **kwargs: object) -> None:
        self._refuse("remove")

    def clear(self) -> None:
        self._refuse("clear")

    def reverse(self) -> None:
        self._refuse("reverse")

    def __setitem__(self, *args: object, **kwargs: object) -> None:
        self._refuse("replace")

    def __delitem__(self, *args: object, **kwargs: object) -> None:
        self._refuse("delete")

    @classmethod
    def load(cls, path: str | Path) -> "Chain":
        """Read a JSONL file (core fields). Extra keys are ignored.

        After load the file is only ever opened again in mode ``'a'``.
        Does not rewrite. Call ``verify()`` to check hashes and links.
        """
        path = Path(path)
        receipts: list[Receipt] = []
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                receipts.append(Receipt.from_dict(json.loads(line)))
        return cls(receipts, path=path)

    @classmethod
    def genesis(
        cls,
        path: str | Path,
        *,
        summary: str,
        evidence: str,
        confidence: float = 1.0,
        timestamp: str | None = None,
    ) -> "Chain":
        """Create the first receipt in a new JSONL file. File must be absent or empty."""
        path = Path(path)
        if path.exists() and path.stat().st_size > 0:
            raise ChainError(f"chain already exists: {path}; use append")
        chain = cls((), path=path)
        chain.append(
            summary=summary,
            evidence=evidence,
            confidence=confidence,
            timestamp=timestamp,
        )
        return chain

    def append(
        self,
        summary: str,
        evidence: str,
        confidence: float = 1.0,
        timestamp: str | None = None,
        *,
        require_existing: bool = False,
    ) -> Receipt:
        """Append a new receipt. First receipt is genesis (prev_hash = 64 zeros).

        If ``require_existing`` is true (CLI ``append``), the chain must
        already contain at least one receipt.
        """
        if require_existing and not self._receipts:
            raise ChainError("chain does not exist or is empty; use genesis")
        if self._receipts:
            prev = self._receipts[-1].hash
        else:
            prev = GENESIS_PREV_HASH
        receipt = Receipt.create(
            summary=summary,
            evidence=evidence,
            confidence=confidence,
            timestamp=timestamp,
            prev_hash=prev,
        )
        if self._path is not None:
            _append_line(self._path, receipt)
        self._receipts = self._receipts + (receipt,)
        return receipt

    def verify(self) -> VerifyResult:
        """Walk the chain. Check each hash and each consecutive link.

        Forks stored as a single linear JSONL will fail the consecutive
        link check (store divergent chains separately). Hash mismatches
        and broken prev_hash links are errors. Forks themselves are not
        a verdict; see ``forks()``.
        """
        errors: list[str] = []
        n = len(self._receipts)
        first = self._receipts[0].hash if n else None
        last = self._receipts[-1].hash if n else None

        for i, rec in enumerate(self._receipts):
            expected = rec.recomputed_hash()
            if rec.hash != expected:
                errors.append(
                    f"index {i}: stored hash {rec.hash} != recomputed {expected}"
                )
            if i == 0:
                continue
            prev = self._receipts[i - 1]
            if rec.prev_hash != prev.hash:
                errors.append(
                    f"index {i}: prev_hash {rec.prev_hash} != previous.hash {prev.hash}"
                )

        return VerifyResult(
            ok=not errors,
            length=n,
            first_hash=first,
            last_hash=last,
            errors=errors,
        )

    def forks(self) -> list[Fork]:
        """prev_hash values with more than one child. Does not pick a winner."""
        return detect_forks(self._receipts)
