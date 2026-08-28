"""Session randomization engine (whitepaper section 6).

Protocol
--------
    seed = system_entropy + timestamp
    rng  = cryptographic_random(seed)
    node_index = rng % 25

Exact bytes concatenated for ``seed``
-------------------------------------
    entropy:     32 bytes from ``secrets.token_bytes(32)`` (or caller-supplied)
    timestamp:   UTC ISO-8601 with trailing ``Z`` (second precision), UTF-8
    seed bytes:  ``entropy || timestamp.encode("utf-8")``

``cryptographic_random`` is ``SHA-256(seed)``. The 32-byte digest is
interpreted as a big-endian unsigned integer:

    node_index = int.from_bytes(digest, "big") % 25

Returns ``0..24``. This module does not import the stdlib ``random`` module and does not
use choice-style selection. Paper section 3.2 is a sketch; section 6 is
the protocol this engine implements.
"""

from __future__ import annotations

import hashlib
import secrets

POOL_SIZE = 25
ENTROPY_BYTES = 32


def fresh_entropy() -> bytes:
    """32 bytes of system entropy via ``secrets.token_bytes``."""
    return secrets.token_bytes(ENTROPY_BYTES)


def seed_bytes(entropy: bytes, timestamp: str) -> bytes:
    """Concatenate ``entropy || timestamp.encode("utf-8")``.

    ``timestamp`` is the UTC ISO-8601 string used as the protocol clock
    (example: ``2026-03-04T13:02:12Z``).
    """
    if not isinstance(entropy, (bytes, bytearray)):
        raise TypeError("entropy must be bytes")
    if not isinstance(timestamp, str):
        raise TypeError("timestamp must be a UTC ISO-8601 string")
    return bytes(entropy) + timestamp.encode("utf-8")


def select_index(entropy: bytes, timestamp: str) -> int:
    """Return a deterministic node index in ``0..24`` for entropy+timestamp.

    Same inputs always yield the same index. Does not use ``random.choice``.
    """
    digest = hashlib.sha256(seed_bytes(entropy, timestamp)).digest()
    return int.from_bytes(digest, "big") % POOL_SIZE
