"""Opaque 1-in-5 sampler.

Exact 1-in-5 is the *rate*, realized via an opaque hash of a session-local
salt concatenated with the identifier:

    int.from_bytes(sha256(salt || id)[:8], "big") % 5 == 0

Internally deterministic: same salt + same id always yields the same
decision. Externally opaque: the salt is session-local and is not a
round-robin counter. Across many distinct ids the sampled count sits
near 20% (hash distribution, not an exact quota on an open stream).
"""

from __future__ import annotations

import hashlib
from typing import Union

IdLike = Union[str, bytes, int]

SAMPLE_MODULUS = 5  # 1 in 5
HASHED_ID_HEX_LEN = 12


def _as_bytes(value: IdLike) -> bytes:
    if isinstance(value, bytes):
        return value
    return str(value).encode("utf-8")


def identity_digest(salt: str | bytes, raw_id: IdLike) -> bytes:
    """SHA-256(salt || id). Salt and id are concatenated as bytes."""
    salt_b = salt if isinstance(salt, bytes) else str(salt).encode("utf-8")
    return hashlib.sha256(salt_b + _as_bytes(raw_id)).digest()


def hashed_id_for(salt: str | bytes, raw_id: IdLike) -> str:
    """Truncated identity hash used in reports: sha256 hex[:12]."""
    return identity_digest(salt, raw_id).hex()[:HASHED_ID_HEX_LEN]


class Sampler:
    """Session-local 1-in-5 sampler.

    Pass the *raw* host id when it is still in the adapter. After ingest
    the envelope only carries ``hashed_id``; sampling of a closed set of
    raw ids uses this class directly.
    """

    modulus = SAMPLE_MODULUS

    def __init__(self, salt: str | bytes):
        self.salt = salt if isinstance(salt, str) else salt.decode("utf-8")

    def digest(self, raw_id: IdLike) -> bytes:
        return identity_digest(self.salt, raw_id)

    def hashed_id(self, raw_id: IdLike) -> str:
        return hashed_id_for(self.salt, raw_id)

    def should_sample(self, raw_id: IdLike) -> bool:
        return int.from_bytes(self.digest(raw_id)[:8], "big") % SAMPLE_MODULUS == 0
