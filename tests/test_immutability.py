
from __future__ import annotations

from pathlib import Path

import pytest

from temporallock.errors import AppendOnlyError
from forgereceipts.store import ForgeStore


def test_cannot_mutate_receipts(tmp_path: Path) -> None:
    store = ForgeStore(tmp_path)
    store.append_incident(summary="s", evidence="e", child_impact="c")
    rec = store.chain[0]
    with pytest.raises(AppendOnlyError):
        rec.summary = "changed"  # type: ignore[misc]
    with pytest.raises(AppendOnlyError):
        store.chain.pop()
    with pytest.raises(AppendOnlyError):
        store.chain.clear()
    with pytest.raises(AppendOnlyError):
        del store.chain[0]
    with pytest.raises(AppendOnlyError):
        store.refuse_mutate()
