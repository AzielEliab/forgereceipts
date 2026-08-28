"""Polarize: five-region basket, one-shot shake, pick one.

The shake is deterministic from a session nonce. It is not a user id,
not a profile, and not an engagement optimizer.
"""

from __future__ import annotations

import hashlib


def shake(basket: list[str], nonce: bytes, salt: bytes = b"geo") -> str:
    """Pick one member of ``basket`` from ``nonce``. Order-stable."""
    if not basket:
        raise ValueError("basket must not be empty")
    scored = sorted(
        basket,
        key=lambda item: hashlib.sha256(nonce + salt + item.encode("utf-8")).digest(),
    )
    return scored[0]


def pick_index(n: int, nonce: bytes, salt: bytes) -> int:
    if n <= 0:
        raise ValueError("n must be positive")
    digest = hashlib.sha256(nonce + salt).digest()
    return int.from_bytes(digest[:8], "big") % n
