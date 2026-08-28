"""Anonymous JobEnvelope. Raw identifiers are hashed on ingest; PII is dropped."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


# Keys that must never land on an envelope or in a report.
PII_KEYS = frozenset(
    {
        "name",
        "full_name",
        "first_name",
        "last_name",
        "email",
        "phone",
        "phone_number",
        "mobile",
        "person",
        "person_name",
        "team",
        "team_name",
        "department",
        "department_name",
        "technician",
        "technician_name",
        "worker",
        "worker_name",
        "assignee",
        "assignee_name",
        "employee",
        "employee_name",
        "username",
        "ssn",
        "address",
        "operator",
        "operator_name",
    }
)


def is_pii_key(key: str) -> bool:
    k = key.strip().lower().replace("-", "_")
    if k in PII_KEYS:
        return True
    # Catch host fields like customer_email, user_phone.
    for token in ("email", "phone", "ssn", "fullname"):
        if token in k:
            return True
    if k.endswith("_name") or k.endswith("name"):
        return True
    if k in {"team", "department", "person"}:
        return True
    return False


def sanitize_context(signals: Mapping[str, Any] | None) -> dict[str, Any]:
    """Keep numeric/categorical host fields; drop PII keys and odd types."""
    out: dict[str, Any] = {}
    if not signals:
        return out
    for key, value in signals.items():
        if is_pii_key(str(key)):
            continue
        if isinstance(value, bool):
            out[str(key)] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            out[str(key)] = value
        elif isinstance(value, str):
            # Categorical already-available field. Still drop if it *looks* like an email.
            if "@" in value and "." in value.split("@")[-1]:
                continue
            out[str(key)] = value
        # Nested / other types are dropped (not required by the spec).
    return out


@dataclass(frozen=True)
class JobEnvelope:
    """Anonymous operational record. No raw id, no person/team/department names.

    Fields are the host-available initiation set plus close-out actuals.
    ``hashed_id`` is ``sha256(salt || raw_id).hex()[:12]``.
    ``sampled`` is an internal 1-in-5 flag from the same digest; it is never
    emitted in reports.
    """

    hashed_id: str
    timestamp: str
    task_class: str
    urgency: float
    context_signals: dict[str, Any] = field(default_factory=dict)
    actual_outcome: str | None = None
    actual_revenue: float | None = None
    actual_cost: float | None = None
    actual_duration: float | None = None
    sampled: bool = field(default=False, compare=False, repr=False)

    def initiation_fields(self) -> dict[str, Any]:
        """Fields the host already had at initiation. No actuals."""
        return {
            "task_class": self.task_class,
            "urgency": self.urgency,
            "context_signals": dict(self.context_signals),
        }
