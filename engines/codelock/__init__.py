"""CodeLock: gate-tethered cognitive rendering of source text.

July 2026 whitepaper implementation by Aziel Eliab.

Plain text is always canonical. Rendered views never mutate source.
This tool alters perception, not meaning. It is not encryption.

Forks are welcome and always allowed.
"""

from __future__ import annotations

from codelock.gate import ACK_PHRASE, AcknowledgmentError, Gate, GateClosedError
from codelock.render import styles_for
from codelock.session import CodeLockSession
from codelock.tokenize import tokenize, tokenize_kinds

__version__ = "0.1.0"
__author__ = "Aziel Eliab"
__all__ = [
    "ACK_PHRASE",
    "AcknowledgmentError",
    "CodeLockSession",
    "Gate",
    "GateClosedError",
    "styles_for",
    "tokenize",
    "tokenize_kinds",
    "__version__",
]
