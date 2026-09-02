"""Import and export receipts as JSON. Verify a file without trusting it.

A receipt is a local hash record. It is not legal proof and not a court filing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forgereceipts import __version__
from forgereceipts.debug import debug_log
from forgereceipts.limits import MAX_JSON_CHARS
from forgereceipts.plain import (
    JSON_ERROR,
    MISSING_RECEIPT,
    NOT_LEGAL_PROOF,
    NOT_OBJECT,
    NOT_TEXT,
    TOO_BIG,
    PlainError,
    decode_text,
    loads_json,
)
from temporallock.receipt import Receipt

FORMAT_RECEIPT = "forgereceipts.receipt/v1"
FORMAT_BUNDLE = "forgereceipts.bundle/v1"
SAVED_PLAIN = "Saved a receipt for this file"


def envelope_for(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": FORMAT_RECEIPT,
        "product": "forgereceipts",
        "product_version": __version__,
        "disclaimer": NOT_LEGAL_PROOF,
        "not_legal_advice": True,
        "not_legal_proof": True,
        "receipt": dict(receipt),
    }


def bundle_for(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "format": FORMAT_BUNDLE,
        "product": "forgereceipts",
        "product_version": __version__,
        "disclaimer": NOT_LEGAL_PROOF,
        "not_legal_advice": True,
        "not_legal_proof": True,
        "receipts": [dict(r) for r in receipts],
    }


def dump_receipt(receipt: dict[str, Any]) -> str:
    return json.dumps(envelope_for(receipt), indent=2, ensure_ascii=False) + "\n"


def dump_bundle(receipts: list[dict[str, Any]]) -> str:
    return json.dumps(bundle_for(receipts), indent=2, ensure_ascii=False) + "\n"


def _as_receipt_dict(obj: Any) -> dict[str, Any] | None:
    if not isinstance(obj, dict):
        return None
    if isinstance(obj.get("receipt"), dict):
        return obj["receipt"]
    if "hash" in obj and "summary" in obj and "evidence" in obj:
        return obj
    return None


def _parse_jsonl(text: str) -> list[Any]:
    rows: list[Any] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise PlainError(JSON_ERROR) from exc
    return rows


def parse_payload(text: str) -> dict[str, Any]:
    """Parse envelope, bundle, bare receipt, or JSONL into a structured payload."""
    if len(text) > MAX_JSON_CHARS:
        raise PlainError(TOO_BIG)
    stripped = text.strip()
    if not stripped:
        raise PlainError(MISSING_RECEIPT)

    obj: Any | None = None
    extra = False
    try:
        obj = loads_json(stripped)
    except json.JSONDecodeError:
        extra = True
        obj = None
    except PlainError:
        raise

    if extra:
        rows = _parse_jsonl(stripped)
        receipts = []
        for row in rows:
            rec = _as_receipt_dict(row)
            if rec is None:
                raise PlainError(NOT_OBJECT)
            receipts.append(rec)
        if not receipts:
            raise PlainError(MISSING_RECEIPT)
        return {"kind": "jsonl", "receipts": receipts}

    if isinstance(obj, list):
        receipts = []
        for row in obj:
            rec = _as_receipt_dict(row)
            if rec is None:
                raise PlainError(NOT_OBJECT)
            receipts.append(rec)
        if not receipts:
            raise PlainError(MISSING_RECEIPT)
        return {"kind": "list", "receipts": receipts}

    if not isinstance(obj, dict):
        raise PlainError(NOT_OBJECT)

    if isinstance(obj.get("receipts"), list):
        receipts = []
        for row in obj["receipts"]:
            rec = _as_receipt_dict(row)
            if rec is None:
                raise PlainError(NOT_OBJECT)
            receipts.append(rec)
        if not receipts:
            raise PlainError(MISSING_RECEIPT)
        return {"kind": "bundle", "receipts": receipts, "raw": obj}

    rec = _as_receipt_dict(obj)
    if rec is None:
        raise PlainError(MISSING_RECEIPT)
    return {"kind": "receipt", "receipts": [rec], "raw": obj}


def verify_one(receipt: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    try:
        rec = Receipt.from_dict(receipt)
    except Exception as exc:  # noqa: BLE001 — surface as FAIL, not a crash
        debug_log(f"verify_one from_dict: {type(exc).__name__}: {exc}")
        return {
            "ok": False,
            "verdict": "FAIL",
            "plain": "This file does not look like a receipt.",
            "disclaimer": NOT_LEGAL_PROOF,
            "hash": receipt.get("hash"),
            "errors": [str(exc)],
        }
    ok = rec.hash_ok()
    if not ok:
        errors.append("stored hash does not match SHA-256 of the receipt fields")
    plain = (
        "This receipt looks whole. The hash matches."
        if ok
        else "This receipt does not match its hash."
    )
    result = {
        "ok": ok,
        "verdict": "PASS" if ok else "FAIL",
        "plain": plain,
        "disclaimer": NOT_LEGAL_PROOF,
        "hash": rec.hash,
        "recomputed_hash": rec.recomputed_hash(),
        "errors": errors,
        "not_legal_proof": True,
        "not_legal_advice": True,
    }
    debug_log(f"verify_one verdict={result['verdict']} hash={rec.hash}")
    return result


def verify_payload(payload: dict[str, Any]) -> dict[str, Any]:
    receipts: list[dict[str, Any]] = list(payload.get("receipts") or [])
    if not receipts:
        raise PlainError(MISSING_RECEIPT)
    results = [verify_one(r) for r in receipts]
    ok = all(r["ok"] for r in results)
    if payload.get("kind") in {"jsonl", "bundle", "list"} and len(receipts) > 1:
        from forgereceipts.store import verify_jsonl

        jsonl = "\n".join(
            json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            for r in receipts
        )
        chain = verify_jsonl(jsonl)
        chain_ok = bool(chain.get("ok"))
        ok = ok and chain_ok
        return {
            "ok": ok,
            "verdict": "PASS" if ok else "FAIL",
            "plain": (
                "These receipts look whole. The hashes match."
                if ok
                else "One or more receipts failed the hash check."
            ),
            "disclaimer": NOT_LEGAL_PROOF,
            "count": len(receipts),
            "receipts": results,
            "chain": chain,
            "not_legal_proof": True,
            "not_legal_advice": True,
        }
    first = results[0]
    first["count"] = 1
    return first


def verify_text(text: str) -> dict[str, Any]:
    payload = parse_payload(text)
    return verify_payload(payload)


def verify_path(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise PlainError("That path is not a file on this computer.")
    try:
        raw = p.read_bytes()
    except OSError as exc:
        raise PlainError("Could not read that file.") from exc
    try:
        text = decode_text(raw)
    except PlainError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise PlainError(NOT_TEXT) from exc
    return verify_text(text)


def load_receipts_from_text(text: str) -> list[dict[str, Any]]:
    return list(parse_payload(text).get("receipts") or [])


def roundtrip(receipt: dict[str, Any]) -> dict[str, Any]:
    """Export then parse then verify. Hash must match the original."""
    text = dump_receipt(receipt)
    loaded = load_receipts_from_text(text)
    if not loaded:
        raise PlainError(MISSING_RECEIPT)
    got = loaded[0]
    result = verify_one(got)
    match = got.get("hash") == receipt.get("hash") and result["ok"]
    result["roundtrip"] = True
    result["roundtrip_hash_match"] = match
    result["ok"] = bool(result["ok"] and match)
    result["verdict"] = "PASS" if result["ok"] else "FAIL"
    if result["ok"]:
        result["plain"] = "Export then import kept the same hash."
    return result
