"""Pattern Strength Score — a transparent local heuristic.

This is NOT a court-win probability, NOT a prediction, and NOT a claim
that a filing will succeed. It is a counting aid so the user can see
whether they have been documenting consistently.

Formula (documented here so it cannot hide):

    PSS = 100 * (0.40 * F + 0.35 * C + 0.25 * J)

    F = min(1.0, corroborated_hashed_files / 10)
        corroborated_hashed_files = unique file_sha256 values stored
        on receipts (incident, journal, or forensics). Live re-verify
        of the bytes is a separate Forensics action; the score counts
        hashes that were taken, not a claim the file still exists.

    C = min(1.0, chain_length / 20)
        chain_length = number of TemporalLock receipts on the ledger.

    J = min(1.0, journal_entries / 10)
        journal_entries = receipts with kind == "journal"
        (Time with Child).

Caps at 100. Zero data yields 0. The weights are engineering defaults,
not an empirical model of any court.
"""

from __future__ import annotations

from typing import Any, Iterable

from forgereceipts.store import KIND_JOURNAL, hashed_file_count


def pattern_strength(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(records)
    chain_length = len(rows)
    journal_entries = sum(1 for r in rows if r.get("kind") == KIND_JOURNAL)
    files = hashed_file_count(rows)
    f = min(1.0, files / 10.0)
    c = min(1.0, chain_length / 20.0)
    j = min(1.0, journal_entries / 10.0)
    pss = 100.0 * (0.40 * f + 0.35 * c + 0.25 * j)
    return {
        "score": round(pss, 1),
        "max": 100.0,
        "formula": "100 * (0.40*min(1, hashed_files/10) + 0.35*min(1, chain_length/20) + 0.25*min(1, journal_entries/10))",
        "components": {
            "corroborated_hashed_files": files,
            "chain_length": chain_length,
            "journal_entries": journal_entries,
            "F": round(f, 4),
            "C": round(c, 4),
            "J": round(j, 4),
        },
        "disclaimer": (
            "Pattern Strength Score is a local counting heuristic. "
            "It is not a court-win probability and not legal advice."
        ),
    }
