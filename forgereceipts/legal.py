"""National baseline plus the selected US jurisdiction.

This module does not quote statutes, does not invent holdings, and is
not legal advice. Indiana is the default selector *label* because the
author lives in Indianapolis.
"""

from __future__ import annotations

from typing import Any

from forgereceipts.jurisdictions import (
    DEFAULT_JURISDICTION,
    FEDERAL_ID,
    NOT_LEGAL_ADVICE,
    federal_profile,
    get_jurisdiction,
    list_jurisdictions,
)

# Re-export for existing imports.
__all__ = [
    "FEDERAL_BASELINE",
    "FEDERAL_ID",
    "NATIONAL_BASELINE",
    "NOT_LEGAL_ADVICE",
    "catalog",
    "reference",
]

FEDERAL_BASELINE: list[dict[str, str]] = [
    {
        "id": "troxel",
        "name": "Troxel v. Granville",
        "cite": "530 U.S. 57 (2000)",
        "scope": "federal",
        "blurb": (
            "A United States Supreme Court decision often discussed in "
            "parenting-time and third-party visitation cases. Commentators "
            "commonly describe it as addressing the liberty interest of fit "
            "parents in the care, custody, and control of their children. "
            "This software does not state the holding for your facts. "
            "Read the opinion. National reference — not your state's code. "
            "Not legal advice."
        ),
    },
    {
        "id": "stanley",
        "name": "Stanley v. Illinois",
        "cite": "405 U.S. 645 (1972)",
        "scope": "federal",
        "blurb": (
            "A United States Supreme Court decision often discussed when "
            "unmarried fathers are treated as a class rather than as "
            "individuals. Commentators commonly describe it as rejecting a "
            "blanket presumption of unfitness without an individualized "
            "hearing. This software does not state the holding for your "
            "facts. Read the opinion. National reference — not your state's "
            "code. Not legal advice."
        ),
    },
    {
        "id": "fre",
        "name": "Federal Rules of Evidence",
        "cite": "Fed. R. Evid. (advisory)",
        "scope": "federal",
        "blurb": (
            "A national reference about what a federal court may consider. "
            "Most custody cases are in state court under state evidence "
            "rules. This software does not decide admissibility. "
            "Not legal advice."
        ),
    },
    {
        "id": "frcp",
        "name": "Federal Rules of Civil Procedure",
        "cite": "Fed. R. Civ. P. (advisory)",
        "scope": "federal",
        "blurb": (
            "A national reference about civil-case steps in federal court. "
            "Family court is usually state court with local rules. This "
            "software does not file or serve. Not legal advice."
        ),
    },
    {
        "id": "uccjea",
        "name": "UCCJEA",
        "cite": "Uniform Child Custody Jurisdiction and Enforcement Act",
        "scope": "federal",
        "blurb": (
            "A uniform act, adopted in some form by most U.S. states, that "
            "addresses which state has jurisdiction over a child-custody "
            "proceeding and how orders are enforced across state lines. "
            "This software does not determine jurisdiction, does not pick "
            "a home state, and does not contact any court. National "
            "uniform-act name — confirm your state's version. Not legal advice."
        ),
    },
]

# Backward-compatible alias used by older docs and tests.
NATIONAL_BASELINE = FEDERAL_BASELINE


def catalog() -> dict[str, Any]:
    return {
        "disclaimer": NOT_LEGAL_ADVICE,
        "default": DEFAULT_JURISDICTION,
        "federal_id": FEDERAL_ID,
        "jurisdictions": list_jurisdictions(),
    }


def reference(jurisdiction: str | None = None) -> dict[str, Any]:
    selected = get_jurisdiction(jurisdiction)
    federal = federal_profile()
    return {
        "disclaimer": NOT_LEGAL_ADVICE,
        "jurisdiction": selected,
        "federal": federal,
        "baseline": list(FEDERAL_BASELINE),
        "state": {
            "id": selected["id"],
            "name": selected["name"],
            "kind": selected["kind"],
            "depth": selected["depth"],
            "best_interests_label": selected["best_interests_label"],
            "best_interests_note": selected["best_interests_note"],
            "guidelines_label": selected["guidelines_label"],
            "guidelines_note": selected["guidelines_note"],
            "legal_tags": selected["legal_tags"],
            "parenting_term": selected["parenting_term"],
            "gal_term": selected["gal_term"],
            "efiling": selected["efiling"],
            "exhibit": selected["exhibit"],
            "uccjea": selected["uccjea"],
            "stub": selected["stub"],
        },
        "note": (
            f"State-aware in v0.3.0 means a structured {selected['name']} "
            f"profile (depth: {selected['depth']}) plus the federal baseline "
            "that is always shown. It does not encode a full statute book "
            "and is not bar-certified legal advice. No fabricated case "
            "citations. Not legal advice."
        ),
    }
