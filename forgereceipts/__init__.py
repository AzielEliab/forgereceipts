"""ForgeReceipts: local-first evidence integrity for pro se fathers.

July 2026. Author: Aziel Eliab, Indianapolis.

Child's Best Interests First. Integrity Over Narrative. Local Control. Always.

This software is not legal advice and does not guarantee any court outcome.
It does not contact courts, Odyssey, email, or any cloud service.
No telemetry. No accounts. Forks are welcome and always allowed.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ENGINES = _ROOT / "engines"
if _ENGINES.is_dir():
    _engine_str = str(_ENGINES)
    if _engine_str not in sys.path:
        sys.path.insert(0, _engine_str)

__version__ = "0.2.0"
__author__ = "Aziel Eliab"
__all__ = ["__version__"]
