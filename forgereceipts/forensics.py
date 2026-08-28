"""Local SHA-256 of a file. Store the hash on a receipt; re-verify later."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: str | Path) -> str:
    p = Path(path)
    hasher = hashlib.sha256()
    with p.open("rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def reverify_bytes(data: bytes, expected_hex: str) -> dict[str, object]:
    got = sha256_bytes(data)
    expected = expected_hex.strip().lower()
    ok = got == expected
    return {
        "ok": ok,
        "verdict": "PASS" if ok else "FAIL",
        "got": got,
        "expected": expected,
    }


def reverify_path(path: str | Path, expected_hex: str) -> dict[str, object]:
    got = sha256_path(path)
    expected = expected_hex.strip().lower()
    ok = got == expected
    return {
        "ok": ok,
        "verdict": "PASS" if ok else "FAIL",
        "got": got,
        "expected": expected,
        "path": str(path),
    }
