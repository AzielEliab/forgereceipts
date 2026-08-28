"""ShadowLock: a read-only, zero-retention, software-agnostic outcome mirror.

July 2026 whitepaper implementation by Aziel Eliab.

Observes selectively. Computes counterfactual expectations. Reports
financial variance. Forgets everything. Does not control, optimize,
replace, dispatch, schedule, or learn.

Change is optional. Truth is not.

Forks are welcome and always allowed.
"""

from __future__ import annotations

from shadowlock.adapters import CsvAdapter, JsonlAdapter, MemoryAdapter
from shadowlock.counterfactual import Expectation
from shadowlock.envelope import JobEnvelope
from shadowlock.errors import (
    AirgapError,
    ReadOnlyError,
    SessionForgottenError,
)
from shadowlock.ledger import FinancialLedger
from shadowlock.report import Report
from shadowlock.sample import Sampler
from shadowlock.session import ShadowLockSession

__version__ = "0.1.0"
__author__ = "Aziel Eliab"
__all__ = [
    "AirgapError",
    "CsvAdapter",
    "Expectation",
    "FinancialLedger",
    "JobEnvelope",
    "JsonlAdapter",
    "MemoryAdapter",
    "ReadOnlyError",
    "Report",
    "Sampler",
    "SessionForgottenError",
    "ShadowLockSession",
    "__version__",
]
