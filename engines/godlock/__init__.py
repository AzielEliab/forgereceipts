"""GodLock: stress-test and resilience engine for the ABAD framework.

July 12 2026 whitepaper implementation by Aziel Eliab.
Shipped under GitHub user AzielEliab.

GodLock does not argue. It records, analyzes, hardens, and grows.

This package is the core + receipts engine. It is not an anonymity
network. MirageGrid and Airlock are in-process logical identities.
Forks are welcome and always allowed.
"""

from __future__ import annotations

from godlock.abad import score_engagement
from godlock.engine import GodLockEngine
from godlock.grid import Airlock, MirageGrid
from godlock.lumen import decrypt_capsule, export_capsule
from godlock.receipts import Receipt

__version__ = "0.1.0"
__author__ = "Aziel Eliab"
__all__ = [
    "Airlock",
    "GodLockEngine",
    "MirageGrid",
    "Receipt",
    "decrypt_capsule",
    "export_capsule",
    "score_engagement",
    "__version__",
]
