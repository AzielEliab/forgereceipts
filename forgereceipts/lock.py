"""Optional local passphrase. hashlib.pbkdf2_hmac only. Hash in memory.

A verifier (salt + pbkdf2 digest) is stored under .forgereceipts/lock.json
so the same passphrase can unlock a later session. The passphrase itself
is never stored. Derived material lives in process memory for the session.
This is a local unlock, not a threat model against a sophisticated attacker
with the disk — do not treat it as full-disk encryption.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from pathlib import Path
from typing import Any

ITERATIONS = 200_000
ALGO = "sha256"
DKLEN = 32


class SessionLock:
    def __init__(self, data_dir: str | Path) -> None:
        self.path = Path(data_dir) / "lock.json"
        self._unlocked = not self.is_set()
        self._session_key: bytes | None = None

    def is_set(self) -> bool:
        return self.path.is_file()

    @property
    def unlocked(self) -> bool:
        return self._unlocked

    def status(self) -> dict[str, Any]:
        return {
            "lock_set": self.is_set(),
            "unlocked": self._unlocked,
            "algo": "pbkdf2_hmac",
            "hash_name": ALGO,
            "iterations": ITERATIONS,
            "note": "Local passphrase only. Not cloud auth. Not full-disk encryption.",
        }

    def _derive(self, passphrase: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            ALGO,
            passphrase.encode("utf-8"),
            salt,
            ITERATIONS,
            dklen=DKLEN,
        )

    def set_passphrase(self, passphrase: str) -> None:
        if not passphrase or len(passphrase) < 4:
            raise ValueError("passphrase must be at least 4 characters")
        salt = secrets.token_bytes(16)
        digest = self._derive(passphrase, salt)
        payload = {
            "algo": "pbkdf2_hmac",
            "hash_name": ALGO,
            "iterations": ITERATIONS,
            "salt_hex": salt.hex(),
            "verifier_hex": digest.hex(),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        self._session_key = digest
        self._unlocked = True

    def unlock(self, passphrase: str) -> bool:
        if not self.is_set():
            self._unlocked = True
            return True
        data = json.loads(self.path.read_text(encoding="utf-8"))
        salt = bytes.fromhex(data["salt_hex"])
        expected = bytes.fromhex(data["verifier_hex"])
        got = self._derive(passphrase, salt)
        if not secrets.compare_digest(got, expected):
            self._unlocked = False
            return False
        self._session_key = got
        self._unlocked = True
        return True

    def lock_session(self) -> None:
        self._unlocked = not self.is_set()
        self._session_key = None

    def clear(self, passphrase: str) -> None:
        if self.is_set() and not self.unlock(passphrase):
            raise ValueError("passphrase does not match")
        if self.path.is_file():
            os.remove(self.path)
        self._session_key = None
        self._unlocked = True
