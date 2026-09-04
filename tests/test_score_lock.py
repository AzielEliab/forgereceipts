from __future__ import annotations

from pathlib import Path

from forgereceipts.lock import SessionLock
from forgereceipts.score import pattern_strength
from forgereceipts.store import ForgeStore


def test_pattern_strength_formula(tmp_path: Path) -> None:
    store = ForgeStore(tmp_path)
    empty = pattern_strength([])
    assert empty["score"] == 0.0
    store.append_journal(
        summary="park",
        evidence="photos on disk",
        child_impact="uninterrupted afternoon",
        file_sha256="ab" * 32,
        file_name="photo.jpg",
    )
    scored = pattern_strength(store.records())
    f = min(1.0, 1 / 10.0)
    c = min(1.0, 1 / 20.0)
    j = min(1.0, 1 / 10.0)
    expected = round(100.0 * (0.40 * f + 0.35 * c + 0.25 * j), 1)
    assert scored["score"] == expected
    assert scored["components"]["corroborated_hashed_files"] == 1
    assert scored["components"]["chain_length"] == 1
    assert scored["components"]["journal_entries"] == 1
    disc = scored["disclaimer"].lower()
    assert "win probability" in disc or "not a court-win" in disc
    assert scored["next_best_move"]["plain"]
    assert scored["sway"]["journal"] == 1
    assert scored["flags"]


def test_pbkdf2_lock(tmp_path: Path) -> None:
    lock = SessionLock(tmp_path)
    assert lock.unlocked is True
    lock.set_passphrase("correct-horse")
    lock.lock_session()
    assert lock.unlocked is False
    assert lock.unlock("nope") is False
    assert lock.unlock("correct-horse") is True
    lock.clear("correct-horse")
    assert lock.is_set() is False
