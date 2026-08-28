"""Class-conditional empirical prior. No ML. Session-local only.

Expectation is computed from initiation fields only (task_class, urgency,
context_signals) plus a prior built from *previously sampled jobs in this
same in-memory session*. First jobs in a class use optional ``class_priors``
or a conservative default range.

Changing a job's actuals must not change the expectation, only the delta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Any, Mapping, Sequence

# Optional conservative ranges an operator may pass as class_priors.
# When neither history nor class_priors exist, the field is 0-width unknown
# (expected is None; that field does not enter the ledger for that job).
DEFAULT_DURATION_RANGE = (0.0, 1_000_000.0)
DEFAULT_COST_RANGE = (0.0, 1_000_000_000.0)
DEFAULT_REVENUE_RANGE = (0.0, 1_000_000_000.0)


def _mid(lo: float, hi: float) -> float:
    return (lo + hi) / 2.0


def _range_of(values: Sequence[float], fallback: tuple[float, float]) -> tuple[float, float, float]:
    if not values:
        lo, hi = fallback
        return lo, _mid(lo, hi), hi
    lo = min(values)
    hi = max(values)
    return lo, float(median(values)), hi


@dataclass(frozen=True)
class Expectation:
    """Counterfactual envelope at initiation. Actuals are not inputs."""

    duration: float | None
    duration_low: float | None
    duration_high: float | None
    cost: float | None
    cost_low: float | None
    cost_high: float | None
    revenue: float | None
    revenue_low: float | None
    revenue_high: float | None
    unknown: bool = False
    task_class: str = ""
    urgency: float = 0.5

    @classmethod
    def compute(
        cls,
        *,
        task_class: str,
        urgency: float,
        context_signals: Mapping[str, Any] | None = None,
        history: Sequence[Mapping[str, Any]] | None = None,
        class_priors: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> "Expectation":
        """Build an expectation from initiation fields + session history.

        ``history`` items are prior sampled jobs of *any* class; only
        matching ``task_class`` actuals are used. ``context_signals`` is
        accepted (it is an initiation field) and currently used as an
        opaque grouping hint — the baseline is class-conditional median.
        Urgency slightly shortens expected duration (higher urgency →
        less expected time) without looking at actuals.
        """
        del context_signals  # initiation field reserved; baseline is class-conditional
        history = list(history or [])
        same = [h for h in history if str(h.get("task_class")) == str(task_class)]

        durations = [
            float(h["actual_duration"])
            for h in same
            if h.get("actual_duration") is not None
        ]
        costs = [
            float(h["actual_cost"])
            for h in same
            if h.get("actual_cost") is not None
        ]
        revenues = [
            float(h["actual_revenue"])
            for h in same
            if h.get("actual_revenue") is not None
        ]

        prior = (class_priors or {}).get(task_class, {})

        def _resolve(
            values: list[float],
            prior_key: str,
            fallback: tuple[float, float],
        ) -> tuple[float | None, float | None, float | None, bool]:
            if values:
                lo, mid, hi = _range_of(values, fallback)
                return lo, mid, hi, False
            spec = prior.get(prior_key)
            if spec is not None:
                if isinstance(spec, (tuple, list)) and len(spec) >= 2:
                    lo, hi = float(spec[0]), float(spec[1])
                    return lo, _mid(lo, hi), hi, False
                if isinstance(spec, dict) and "low" in spec and "high" in spec:
                    lo, hi = float(spec["low"]), float(spec["high"])
                    return lo, _mid(lo, hi), hi, False
            # 0-width unknown: no invented midpoint. Ledger skips this field.
            return None, None, None, True

        d_lo, d_mid, d_hi, d_unk = _resolve(durations, "duration", DEFAULT_DURATION_RANGE)
        c_lo, c_mid, c_hi, c_unk = _resolve(costs, "cost", DEFAULT_COST_RANGE)
        r_lo, r_mid, r_hi, r_unk = _resolve(revenues, "revenue", DEFAULT_REVENUE_RANGE)

        # Urgency adjustment on duration only: urgency 0 → 1.1×, urgency 1 → 0.9×.
        if d_mid is not None:
            scale = 1.1 - 0.2 * max(0.0, min(1.0, float(urgency)))
            d_mid = d_mid * scale
            if d_lo is not None:
                d_lo = d_lo * scale
            if d_hi is not None:
                d_hi = d_hi * scale

        unknown = d_unk and c_unk and r_unk and not same
        return cls(
            duration=d_mid,
            duration_low=d_lo,
            duration_high=d_hi,
            cost=c_mid,
            cost_low=c_lo,
            cost_high=c_hi,
            revenue=r_mid,
            revenue_low=r_lo,
            revenue_high=r_hi,
            unknown=unknown,
            task_class=str(task_class),
            urgency=float(urgency),
        )


@dataclass
class SessionPrior:
    """In-memory class-conditional prior. Cleared on forget()."""

    class_priors: dict[str, Mapping[str, Any]] = field(default_factory=dict)
    _rows: list[dict[str, Any]] = field(default_factory=list)

    def expect(
        self,
        *,
        task_class: str,
        urgency: float,
        context_signals: Mapping[str, Any] | None = None,
    ) -> Expectation:
        return Expectation.compute(
            task_class=task_class,
            urgency=urgency,
            context_signals=context_signals,
            history=self._rows,
            class_priors=self.class_priors,
        )

    def update(self, envelope_as_dict: Mapping[str, Any]) -> None:
        """Append this job's actuals *after* its expectation was computed."""
        self._rows.append(dict(envelope_as_dict))

    def clear(self) -> None:
        self._rows.clear()
