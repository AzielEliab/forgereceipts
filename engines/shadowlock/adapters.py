"""Read-only host adapters. Map host records into anonymous JobEnvelopes.

Adapters expose only ``iter_jobs()`` / ``load``. Write, save, update,
dispatch, schedule, and modify raise ``ReadOnlyError``. Files are opened
read-only. Raw ids are hashed with the session salt; PII keys are dropped.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from shadowlock.envelope import JobEnvelope, is_pii_key, sanitize_context
from shadowlock.errors import ReadOnlyError
from shadowlock.sample import identity_digest

_WRITE_NAMES = frozenset(
    {
        "write",
        "save",
        "update",
        "create",
        "delete",
        "dispatch",
        "schedule",
        "modify",
        "put",
        "post",
        "insert",
        "upsert",
        "replace",
        "remove",
        "control",
        "optimize",
        "learn",
    }
)

_ID_KEYS = ("id", "job_id", "jobId", "raw_id", "ticket", "ticket_id", "work_order")
_TS_KEYS = ("timestamp", "ts", "created_at", "time", "opened_at")
_CLASS_KEYS = ("task_class", "class", "type", "job_type", "category")
_URGENCY_KEYS = ("urgency", "priority")
_OUTCOME_KEYS = ("actual_outcome", "outcome", "status", "result")
_REVENUE_KEYS = ("actual_revenue", "revenue")
_COST_KEYS = ("actual_cost", "cost")
_DURATION_KEYS = ("actual_duration", "duration")
_CONTEXT_KEYS = ("context_signals", "context", "signals")

_CORE_CONSUMED = frozenset(
    _ID_KEYS
    + _TS_KEYS
    + _CLASS_KEYS
    + _URGENCY_KEYS
    + _OUTCOME_KEYS
    + _REVENUE_KEYS
    + _COST_KEYS
    + _DURATION_KEYS
    + _CONTEXT_KEYS
)

_URGENCY_ENUM = {
    "low": 0.25,
    "medium": 0.5,
    "med": 0.5,
    "high": 0.75,
    "critical": 1.0,
    "urgent": 0.9,
}


def _first(record: Mapping[str, Any], keys: Sequence[str], default: Any = None) -> Any:
    for k in keys:
        if k in record and record[k] not in (None, ""):
            return record[k]
    return default


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_urgency(value: Any) -> float:
    if value is None or value == "":
        return 0.5
    if isinstance(value, str):
        mapped = _URGENCY_ENUM.get(value.strip().lower())
        if mapped is not None:
            return mapped
        try:
            value = float(value)
        except ValueError:
            return 0.5
    n = float(value)
    if n > 1.0:
        # Host used a 1–5 (or 1–10) scale.
        if n <= 5:
            return max(0.0, min(1.0, n / 5.0))
        if n <= 10:
            return max(0.0, min(1.0, n / 10.0))
        return 1.0
    return max(0.0, min(1.0, n))


def _as_timestamp(value: Any) -> str:
    if value is None or value == "":
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    text = str(value).strip()
    return text


def record_to_envelope(record: Mapping[str, Any], salt: str) -> JobEnvelope:
    """Map a host record into an anonymous envelope. Drops raw id and PII."""
    raw_id = _first(record, _ID_KEYS, default=None)
    if raw_id is None:
        # Stable fallback from initiation fields so two adapters still agree
        # if both lack an id and the payload is the same.
        raw_id = json.dumps(
            {k: record[k] for k in sorted(record) if k in _CLASS_KEYS + _TS_KEYS},
            sort_keys=True,
            default=str,
        )
    digest = identity_digest(salt, raw_id)
    hid = digest.hex()[:12]
    sampled = int.from_bytes(digest[:8], "big") % 5 == 0

    ctx_raw = _first(record, _CONTEXT_KEYS, default={})
    if not isinstance(ctx_raw, Mapping):
        ctx_raw = {}
    ctx = dict(ctx_raw)
    for key, value in record.items():
        if key in _CORE_CONSUMED or is_pii_key(str(key)):
            continue
        if str(key) not in ctx:
            ctx[str(key)] = value
    ctx = sanitize_context(ctx)

    return JobEnvelope(
        hashed_id=hid,
        timestamp=_as_timestamp(_first(record, _TS_KEYS)),
        task_class=str(_first(record, _CLASS_KEYS, default="unknown")),
        urgency=_as_urgency(_first(record, _URGENCY_KEYS, default=0.5)),
        context_signals=ctx,
        actual_outcome=(
            None
            if _first(record, _OUTCOME_KEYS) is None
            else str(_first(record, _OUTCOME_KEYS))
        ),
        actual_revenue=_as_float(_first(record, _REVENUE_KEYS)),
        actual_cost=_as_float(_first(record, _COST_KEYS)),
        actual_duration=_as_float(_first(record, _DURATION_KEYS)),
        sampled=sampled,
    )


class ReadOnlyAdapter:
    """Mixin: any write/control attribute raises ReadOnlyError."""

    def __getattr__(self, name: str) -> Any:
        bare = name.lower().lstrip("_")
        if name.lower() in _WRITE_NAMES or bare in _WRITE_NAMES:
            raise ReadOnlyError(
                f"ShadowLock adapters are read-only; {name!r} is not allowed. "
                "This mirror does not write, control, schedule, or modify "
                "external systems."
            )
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def load(self, salt: str) -> list[JobEnvelope]:
        """Read-only load of every mapped envelope (ids already hashed)."""
        return list(self.iter_jobs(salt))

    def iter_jobs(self, salt: str) -> Iterator[JobEnvelope]:  # pragma: no cover - interface
        raise NotImplementedError


class MemoryAdapter(ReadOnlyAdapter):
    """In-memory list of host records. Does not persist. Does not write out."""

    def __init__(self, records: Sequence[Mapping[str, Any]]):
        self._records = [dict(r) for r in records]

    def iter_jobs(self, salt: str) -> Iterator[JobEnvelope]:
        for rec in self._records:
            yield record_to_envelope(rec, salt)


def _open_readonly(path: Path):
    """Open a text file read-only (O_RDONLY on POSIX)."""
    fd = os.open(path, os.O_RDONLY)
    return os.fdopen(fd, "r", encoding="utf-8")


class JsonlAdapter(ReadOnlyAdapter):
    """Read-only JSONL file adapter. One JSON object per line."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def iter_jobs(self, salt: str) -> Iterator[JobEnvelope]:
        with _open_readonly(self.path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if not isinstance(rec, Mapping):
                    continue
                yield record_to_envelope(rec, salt)


class CsvAdapter(ReadOnlyAdapter):
    """Read-only CSV file adapter. Header row required."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def iter_jobs(self, salt: str) -> Iterator[JobEnvelope]:
        with _open_readonly(self.path) as fh:
            reader = csv.DictReader(fh)
            for rec in reader:
                yield record_to_envelope(rec, salt)

