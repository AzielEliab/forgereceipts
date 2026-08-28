"""Financial ledger over sampled close-outs.

    money_made              sum of positive revenue deltas
    money_lost              sum of negative revenue deltas (as +$) plus cost overruns
    money_left_on_table     expected revenue high-end minus actual, when actual < expected
    net_variance            money_made - money_lost
    efficiency_score        0–1 mean of per-job time/cost/revenue efficiency (clipped)

Opportunity cost (money_left_on_table) is reported separately and is not
subtracted again inside net_variance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shadowlock.counterfactual import Expectation
from shadowlock.envelope import JobEnvelope


def _clip01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _job_efficiency(env: JobEnvelope, exp: Expectation) -> float | None:
    parts: list[float] = []
    if env.actual_duration and exp.duration and env.actual_duration > 0:
        parts.append(_clip01(exp.duration / env.actual_duration))
    if env.actual_cost and exp.cost and env.actual_cost > 0:
        parts.append(_clip01(exp.cost / env.actual_cost))
    if env.actual_revenue is not None and exp.revenue and exp.revenue > 0:
        parts.append(_clip01(env.actual_revenue / exp.revenue))
    if not parts:
        return None
    return sum(parts) / len(parts)


@dataclass
class FinancialLedger:
    money_made: float = 0.0
    money_lost: float = 0.0
    money_left_on_table: float = 0.0
    net_variance: float = 0.0
    efficiency_score: float = 0.0
    _efficiencies: list[float] = field(default_factory=list, repr=False)

    def add(self, env: JobEnvelope, exp: Expectation) -> None:
        actual_rev = env.actual_revenue
        expected_rev = exp.revenue
        if actual_rev is not None and expected_rev is not None:
            delta = actual_rev - expected_rev
            if delta > 0:
                self.money_made += delta
            elif delta < 0:
                self.money_lost += -delta
            if actual_rev < expected_rev:
                high = exp.revenue_high if exp.revenue_high is not None else expected_rev
                self.money_left_on_table += max(0.0, high - actual_rev)

        actual_cost = env.actual_cost
        expected_cost = exp.cost
        if actual_cost is not None and expected_cost is not None:
            overrun = actual_cost - expected_cost
            if overrun > 0:
                self.money_lost += overrun

        eff = _job_efficiency(env, exp)
        if eff is not None:
            self._efficiencies.append(eff)

        self.net_variance = self.money_made - self.money_lost
        if self._efficiencies:
            self.efficiency_score = sum(self._efficiencies) / len(self._efficiencies)
        else:
            self.efficiency_score = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "money_made": round(self.money_made, 6),
            "money_lost": round(self.money_lost, 6),
            "money_left_on_table": round(self.money_left_on_table, 6),
            "net_variance": round(self.net_variance, 6),
            "efficiency_score": round(self.efficiency_score, 6),
        }
