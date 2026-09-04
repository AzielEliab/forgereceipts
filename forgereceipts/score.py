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

from forgereceipts.store import KIND_FORENSICS, KIND_INCIDENT, KIND_JOURNAL, hashed_file_count

HEURISTIC_DISCLAIMER = (
    "Local counting only. Not a court-win probability, not a prediction, "
    "and not legal advice."
)


def _counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "all": len(rows),
        "journal": sum(1 for r in rows if r.get("kind") == KIND_JOURNAL),
        "incident": sum(1 for r in rows if r.get("kind") == KIND_INCIDENT),
        "forensics": sum(1 for r in rows if r.get("kind") == KIND_FORENSICS),
        "files": hashed_file_count(rows),
        "with_child_impact": sum(1 for r in rows if str(r.get("child_impact") or "").strip()),
    }


def filing_flags(records: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    n = _counts(list(records))
    flags: list[dict[str, str]] = []
    if n["all"] == 0:
        flags.append({"id": "empty", "plain": "No receipts yet. Start with Log or Journal."})
    if n["files"] == 0:
        flags.append({"id": "no_hash", "plain": "No file hash yet. Forensics can hash a file on this computer."})
    if n["journal"] == 0:
        flags.append({"id": "no_journal", "plain": "No Time with Child notes yet. Positive parenting docs help balance the file."})
    if n["incident"] == 0 and n["all"] > 0:
        flags.append({"id": "no_log", "plain": "No incident notes yet. Use Log when something happens."})
    if not flags:
        flags.append({"id": "ok", "plain": "You have hashed files, log notes, and journal notes on this computer."})
    return flags


def next_best_move(records: Iterable[dict[str, Any]]) -> dict[str, str]:
    n = _counts(list(records))
    if n["all"] == 0:
        return {
            "id": "start_log",
            "plain": "Write what happened in Log, or try a sample on Import/Export.",
        }
    if n["files"] == 0:
        return {
            "id": "hash_file",
            "plain": "Hash one file in Forensics so you can re-check the same bytes later.",
        }
    if n["journal"] == 0:
        return {
            "id": "journal",
            "plain": "Add a Time with Child note so the file is not only problems.",
        }
    if n["incident"] == 0:
        return {
            "id": "log",
            "plain": "Use Log the next time you need a dated note with child impact.",
        }
    return {
        "id": "verify",
        "plain": "Open Verify and check that your saved receipts still match.",
    }


def concern_sway(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    n = _counts(list(records))
    total = n["incident"] + n["journal"]
    if total == 0:
        journal_share = 50.0
        label = "No notes yet"
    else:
        journal_share = 100.0 * n["journal"] / total
        if journal_share >= 60:
            label = "More Time with Child than incident notes"
        elif journal_share <= 40:
            label = "More incident notes than Time with Child"
        else:
            label = "About even"
    return {
        "journal_share": round(journal_share, 1),
        "incident": n["incident"],
        "journal": n["journal"],
        "label": label,
        "disclaimer": (
            "Concern / Sway Meter is a local count of journal vs incident "
            "notes. It is not a prediction of who a court will believe. "
            "Not legal advice."
        ),
    }


def pattern_strength(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(records)
    n = _counts(rows)
    chain_length = n["all"]
    journal_entries = n["journal"]
    files = n["files"]
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
        "flags": filing_flags(rows),
        "next_best_move": next_best_move(rows),
        "sway": concern_sway(rows),
        "disclaimer": (
            "Pattern Strength Score is a local counting heuristic. "
            "It is not a court-win probability and not legal advice."
        ),
        "heuristic_disclaimer": HEURISTIC_DISCLAIMER,
    }
