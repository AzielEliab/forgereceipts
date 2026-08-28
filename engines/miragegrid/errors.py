"""MirageGrid errors."""

from __future__ import annotations


class MirageGridError(Exception):
    """Base error for the assignment + receipt engine."""


class MappingDestroyedError(MirageGridError):
    """Raised when the session-to-node mapping is accessed after close.

    Close is in-process forget of the mapping, not a log wipe.
    """


class ReceiptError(MirageGridError):
    """Raised when a receipt is missing fields or cannot be parsed."""


class IntegrityError(MirageGridError):
    """Raised when live integrity is FAIL and a caller required PASS."""
