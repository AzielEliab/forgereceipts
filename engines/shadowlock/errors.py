"""ShadowLock errors."""

from __future__ import annotations


class ShadowLockError(Exception):
    """Base error."""


class ReadOnlyError(ShadowLockError):
    """Raised when a write/control method is requested on an adapter."""


class SessionForgottenError(ShadowLockError):
    """Raised when observe/report is requested after forget()."""


class AirgapError(ShadowLockError):
    """Raised when --airgap is set but proxy environment variables are present."""
