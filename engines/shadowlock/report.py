"""Anonymous aggregate report. Hashed ids only. No person/team/department names."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from shadowlock.ledger import FinancialLedger


@dataclass
class Report:
    observed: int = 0
    sampled: int = 0
    sample_rate: float = 0.2
    hashed_ids: list[str] = field(default_factory=list)
    ledger: FinancialLedger = field(default_factory=FinancialLedger)
    by_task_class: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(
        default_factory=lambda: [
            "ShadowLock reports are anonymous aggregates.",
            "Identifiers are sha256 hex[:12] only.",
            "No person, team, or department names are emitted.",
        ]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed": self.observed,
            "sampled": self.sampled,
            "sample_rate_target": self.sample_rate,
            "sampled_hashed_ids": list(self.hashed_ids),
            "ledger": self.ledger.to_dict(),
            "by_task_class": dict(self.by_task_class),
            "notes": list(self.notes),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)
