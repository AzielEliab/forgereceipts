"""FORGERECEIPTS_DEBUG=1 — extra stderr logs, extra error fields. Off by default.

Never sends anything anywhere. Debug is local stderr only.
"""

from __future__ import annotations

import os
import sys

DEBUG_ENV = "FORGERECEIPTS_DEBUG"


def debug_enabled() -> bool:
    value = os.environ.get(DEBUG_ENV, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def debug_log(message: str) -> None:
    if debug_enabled():
        sys.stderr.write(f"[forgereceipts debug] {message}\n")
        sys.stderr.flush()
