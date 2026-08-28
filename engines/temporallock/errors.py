"""TemporalLock errors."""

from __future__ import annotations


class TemporalLockError(Exception):
    """Base error for TemporalLock."""


class AppendOnlyError(TemporalLockError):
    """Raised on any attempt to edit, pop, replace, or delete a receipt."""


class ReceiptError(TemporalLockError):
    """Raised when a receipt field is invalid (empty evidence, bad confidence)."""


class ChainError(TemporalLockError):
    """Raised for chain-level problems (missing genesis, append on empty file)."""
