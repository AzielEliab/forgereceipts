"""CodeLockSession: immutable source, gate-checked views, exports.

Plain text is always canonical. Rendered views never mutate source.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from codelock.gate import ACK_PHRASE, Gate, GateClosedError
from codelock.render import TokenStyle, codelock_html, normalize_html, styles_for
from codelock.tokenize import tokenize

PathLike = Union[str, Path]


class CodeLockSession:
    """Hold source immutably and produce Normalize / CodeLock views.

    Parameters
    ----------
    source:
        Canonical plain text. Never mutated.
    seed:
        Deterministic seed for Rosetta transforms.
    hue:
        If True, token styles include a hue spectrum. If False, ``hue_deg``
        is None and HTML has no color/hsl on tokens.
    """

    def __init__(
        self,
        source: str,
        *,
        seed: str | int = 0,
        hue: bool = True,
        gate: Gate | None = None,
    ) -> None:
        self._source = source
        self.seed: str | int = seed
        self.hue = bool(hue)
        self.gate = gate if gate is not None else Gate()

    @property
    def source(self) -> str:
        return self._source

    @property
    def gate_open(self) -> bool:
        return self.gate.gate_open

    def open_gate(self, acknowledgment: str) -> None:
        """Open the gate. Requires the exact phrase in ``ACK_PHRASE``."""
        self.gate.open(acknowledgment)

    def close_gate(self) -> None:
        self.gate.close()

    def tokens(self) -> list[str]:
        return tokenize(self._source)

    def styles(self) -> list[TokenStyle]:
        """Per-token Rosetta styles. Gate must be Open."""
        self.gate.require_open()
        return styles_for(self.tokens(), self.seed, hue=self.hue)

    def normalize_html(self) -> str:
        """Canonical viewing HTML. Always available, gate or not."""
        return normalize_html(self._source)

    def codelock_html(self) -> str:
        """Non-canonical Rosetta HTML. Raises GateClosedError if Closed."""
        self.gate.require_open()
        return codelock_html(self._source, self.seed, hue=self.hue)

    def export_normal(self, path: PathLike) -> Path:
        """Write verbatim source as UTF-8 ``.txt``. Canonical. Always allowed."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(self._source.encode("utf-8"))
        return dest

    def export_codelock(self, path: PathLike) -> Path:
        """Write a self-contained non-canonical HTML artifact. Gate must be Open."""
        self.gate.require_open()
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(self.codelock_html(), encoding="utf-8", newline="\n")
        return dest


# Re-export for callers who import from session.
__all__ = ["ACK_PHRASE", "CodeLockSession", "Gate", "GateClosedError"]
