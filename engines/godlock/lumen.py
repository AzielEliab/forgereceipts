"""Lumen capsules: one-way AES-GCM export of receipt + analysis JSON.

After write, the API does not serve plaintext back from disk. The engine
keeps an in-process index of capsule ids and SHA-256 hashes only.

Key source (first match):

1. env ``GODLOCK_LUMEN_KEY`` (64 hex chars, or any string SHA-256'd to 32 bytes)
2. ``<data_dir>/lumen.key`` (generated on first use, gitignored)

Tests decrypt with the same key to verify roundtrip. Wrong key fails.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import uuid
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"GLC1"
NONCE_SIZE = 12
KEY_SIZE = 32


class LumenError(Exception):
    pass


class LumenAuthError(LumenError):
    pass


def derive_key(material: str | bytes) -> bytes:
    if isinstance(material, bytes):
        raw = material
        text = None
    else:
        text = material.strip()
        raw = text.encode("utf-8")
    if len(raw) == KEY_SIZE:
        return raw
    if text is not None and len(text) == 64:
        try:
            out = bytes.fromhex(text)
            if len(out) == KEY_SIZE:
                return out
        except ValueError:
            pass
    return hashlib.sha256(raw).digest()


def load_or_create_key(data_dir: Path | None = None, env_key: str | None = None) -> bytes:
    env_val = env_key if env_key is not None else os.environ.get("GODLOCK_LUMEN_KEY")
    if env_val:
        return derive_key(env_val)
    if data_dir is None:
        return secrets.token_bytes(KEY_SIZE)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "lumen.key"
    if path.is_file():
        return derive_key(path.read_text(encoding="utf-8").strip())
    key = secrets.token_bytes(KEY_SIZE)
    path.write_text(key.hex() + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key


def encrypt_bytes(plaintext: bytes, key: bytes) -> bytes:
    if len(key) != KEY_SIZE:
        raise LumenError("AES-GCM key must be 32 bytes")
    nonce = os.urandom(NONCE_SIZE)
    ct = AESGCM(key).encrypt(nonce, plaintext, MAGIC)
    return MAGIC + nonce + ct


def decrypt_bytes(blob: bytes, key: bytes) -> bytes:
    if len(key) != KEY_SIZE:
        raise LumenError("AES-GCM key must be 32 bytes")
    if not blob.startswith(MAGIC) or len(blob) < len(MAGIC) + NONCE_SIZE + 16:
        raise LumenError("not a GodLock Lumen capsule")
    nonce = blob[len(MAGIC) : len(MAGIC) + NONCE_SIZE]
    ct = blob[len(MAGIC) + NONCE_SIZE :]
    try:
        return AESGCM(key).decrypt(nonce, ct, MAGIC)
    except InvalidTag as exc:
        raise LumenAuthError("wrong key or corrupted capsule") from exc


def export_capsule(payload: dict[str, Any], path: Path, key: bytes) -> dict[str, str]:
    plaintext = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    blob = encrypt_bytes(plaintext, key)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)
    capsule_id = str(uuid.uuid4())
    return {
        "capsule_id": capsule_id,
        "sha256": hashlib.sha256(blob).hexdigest(),
        "path": str(path),
    }


def decrypt_capsule(path: Path, key: bytes) -> dict[str, Any]:
    blob = Path(path).read_bytes()
    plaintext = decrypt_bytes(blob, key)
    return json.loads(plaintext.decode("utf-8"))
