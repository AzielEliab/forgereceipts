"""ShadowLockSession — the mirror.

Holds envelopes in memory until ``forget()`` or context-manager exit.
Does not create a data directory, sqlite store, or ``.shadowlock`` path.
Does not write to host systems.
"""

from __future__ import annotations

import os
import secrets
from typing import Any, Mapping

from shadowlock.adapters import ReadOnlyAdapter
from shadowlock.counterfactual import SessionPrior
from shadowlock.envelope import JobEnvelope
from shadowlock.errors import AirgapError, SessionForgottenError
from shadowlock.ledger import FinancialLedger
from shadowlock.report import Report
from shadowlock.sample import Sampler

PROXY_ENV_VARS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "FTP_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "ftp_proxy",
)


def assert_airgap() -> None:
    present = [k for k in PROXY_ENV_VARS if os.environ.get(k)]
    if present:
        raise AirgapError(
            "air-gap requested but proxy environment variables are set: "
            + ", ".join(present)
        )


class ShadowLockSession:
    """In-memory outcome mirror.

    After ``forget()`` (also invoked on context-manager exit), held job
    payloads are dropped. A subsequent ``observe()`` raises
    ``SessionForgottenError``. A ``Report`` already returned to the caller
    is a snapshot of anonymous aggregates (hashed ids only) and is not
    retained by the session.
    """

    def __init__(
        self,
        salt: str | None = None,
        class_priors: Mapping[str, Mapping[str, Any]] | None = None,
        airgap: bool = False,
    ):
        if airgap:
            assert_airgap()
        self.salt = salt if salt is not None else secrets.token_hex(16)
        self.sampler = Sampler(self.salt)
        self._prior = SessionPrior(class_priors=dict(class_priors or {}))
        self._envelopes: list[JobEnvelope] = []
        self._forgotten = False
        self._airgap = airgap

    def observe(self, adapter: ReadOnlyAdapter) -> Report:
        """Read the adapter, sample 1 in 5, compute counterfactuals, return a report.

        The adapter is used only via ``iter_jobs`` / ``load``. Nothing is
        written back.
        """
        if self._forgotten:
            raise SessionForgottenError(
                "session has forgotten its payloads; start a new ShadowLockSession"
            )
        if self._airgap:
            assert_airgap()

        observed = 0
        sampled_envs: list[JobEnvelope] = []
        ledger = FinancialLedger()
        by_class: dict[str, int] = {}

        for env in adapter.iter_jobs(self.salt):
            observed += 1
            # 1-in-5 from the same digest as hashed_id: sha256(salt||raw_id).
            # The raw id is already gone; ``env.sampled`` is the opaque bit.
            if not env.sampled:
                continue
            sampled_envs.append(env)
            exp = self._prior.expect(
                task_class=env.task_class,
                urgency=env.urgency,
                context_signals=env.context_signals,
            )
            ledger.add(env, exp)
            self._prior.update(
                {
                    "task_class": env.task_class,
                    "actual_duration": env.actual_duration,
                    "actual_cost": env.actual_cost,
                    "actual_revenue": env.actual_revenue,
                }
            )
            by_class[env.task_class] = by_class.get(env.task_class, 0) + 1

        self._envelopes.extend(sampled_envs)
        return Report(
            observed=observed,
            sampled=len(sampled_envs),
            sample_rate=0.2,
            hashed_ids=[e.hashed_id for e in sampled_envs],
            ledger=ledger,
            by_task_class=by_class,
        )

    def forget(self) -> None:
        """Drop every held envelope and the in-memory class prior. Irreversible."""
        self._envelopes.clear()
        self._prior.clear()
        self._forgotten = True

    @property
    def forgotten(self) -> bool:
        return self._forgotten

    def held_payload_count(self) -> int:
        """Number of sampled envelopes still in memory. 0 after forget()."""
        return len(self._envelopes)

    def __enter__(self) -> "ShadowLockSession":
        return self

    def __exit__(self, *exc: object) -> bool:
        self.forget()
        return False
