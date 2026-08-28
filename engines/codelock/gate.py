"""Gate tethering for CodeLock Mode.

Cognitive-altering modes require explicit acknowledgment of:

    This tool alters perception, not meaning.

Normalize mode is always available, whether the gate is Open or Closed.
"""

from __future__ import annotations

ACK_PHRASE = "This tool alters perception, not meaning."


class GateClosedError(RuntimeError):
    """Raised when CodeLock Mode is requested while the gate is Closed."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or (
                "CodeLock Mode is disabled while the gate is Closed. "
                "Normalize remains available. Open the gate by acknowledging: "
                f"{ACK_PHRASE!r}"
            )
        )


class AcknowledgmentError(ValueError):
    """Raised when open() is given a phrase other than ACK_PHRASE."""

    def __init__(self, got: str) -> None:
        super().__init__(
            "Opening the gate requires acknowledging the exact phrase: "
            f"{ACK_PHRASE!r} (got {got!r})"
        )


class Gate:
    """Visible, enforceable gate. Closed by default.

    The only way to open the gate is ``open(acknowledgment)`` with the
    exact phrase in ``ACK_PHRASE``. The ``gate_open`` flag is readable;
    it cannot be flipped to True by assignment.
    """

    def __init__(self, *, open: bool = False) -> None:
        # ``open=True`` is refused: the ack phrase is the only key.
        if open:
            raise AcknowledgmentError(
                "Gate(open=True) is not allowed; call Gate.open(ACK_PHRASE)"
            )
        self._open = False

    @property
    def gate_open(self) -> bool:
        return self._open

    @property
    def is_open(self) -> bool:
        return self._open

    def open(self, acknowledgment: str) -> None:
        """Open the gate. ``acknowledgment`` must match ACK_PHRASE exactly
        (leading/trailing whitespace is ignored)."""
        got = acknowledgment if isinstance(acknowledgment, str) else str(acknowledgment)
        if got.strip() != ACK_PHRASE:
            raise AcknowledgmentError(got)
        self._open = True

    def close(self) -> None:
        self._open = False

    def require_open(self) -> None:
        if not self._open:
            raise GateClosedError()

    def __repr__(self) -> str:
        state = "Open" if self._open else "Closed"
        return f"Gate({state})"
