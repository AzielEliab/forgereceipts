"""National baseline legal *names* as plain-English blurbs.

This module does not quote statutes, does not invent holdings, and is
not legal advice. Indiana is the default selector *label* because the
author lives in Indianapolis — the body is still the national stub.
"""

from __future__ import annotations

from typing import Any

NOT_LEGAL_ADVICE = (
    "Not legal advice. A receipt is not legal proof. This software does "
    "not practice law, does not guarantee any outcome, and does not "
    "contact any court. Consult a licensed attorney in your jurisdiction. "
    "Read the primary sources."
)

NATIONAL_BASELINE: list[dict[str, str]] = [
    {
        "id": "troxel",
        "name": "Troxel v. Granville",
        "cite": "530 U.S. 57 (2000)",
        "blurb": (
            "A United States Supreme Court decision often discussed in "
            "parenting-time and third-party visitation cases. Commentators "
            "commonly describe it as addressing the liberty interest of fit "
            "parents in the care, custody, and control of their children. "
            "This software does not state the holding for your facts. "
            "Read the opinion. Not legal advice."
        ),
    },
    {
        "id": "stanley",
        "name": "Stanley v. Illinois",
        "cite": "405 U.S. 645 (1972)",
        "blurb": (
            "A United States Supreme Court decision often discussed when "
            "unmarried fathers are treated as a class rather than as "
            "individuals. Commentators commonly describe it as rejecting a "
            "blanket presumption of unfitness without an individualized "
            "hearing. This software does not state the holding for your "
            "facts. Read the opinion. Not legal advice."
        ),
    },
    {
        "id": "uccjea",
        "name": "UCCJEA",
        "cite": "Uniform Child Custody Jurisdiction and Enforcement Act",
        "blurb": (
            "A uniform act, adopted in some form by most U.S. states, that "
            "addresses which state has jurisdiction over a child-custody "
            "proceeding and how orders are enforced across state lines. "
            "This software does not determine jurisdiction, does not pick "
            "a home state, and does not contact any court. Ask an attorney "
            "whether and how the UCCJEA applies. Not legal advice."
        ),
    },
]

JURISDICTIONS = [
    {
        "id": "IN",
        "label": "Indiana (default label — author is in Indianapolis)",
        "stub": (
            "Indiana is shown as the default selector because the canonical "
            "author lives in Indianapolis. No Indiana statute, rule, or case "
            "is quoted or summarized here. The national baseline names "
            "above are not Indiana-specific holdings. Consult an Indiana "
            "attorney and the current Indiana Code / trial rules. "
            "Not legal advice."
        ),
    },
    {
        "id": "US",
        "label": "United States (national baseline only)",
        "stub": (
            "National names only (Troxel, Stanley, UCCJEA). No state code. "
            "Not legal advice."
        ),
    },
]


def reference(jurisdiction: str = "IN") -> dict[str, Any]:
    jid = (jurisdiction or "IN").strip().upper()
    match = next((j for j in JURISDICTIONS if j["id"] == jid), JURISDICTIONS[0])
    return {
        "disclaimer": NOT_LEGAL_ADVICE,
        "jurisdiction": match,
        "baseline": list(NATIONAL_BASELINE),
        "note": (
            "State-aware in v0.2.0 means a selector label plus this stub. "
            "It does not encode your state's best-interest factors or "
            "parenting-time guidelines."
        ),
    }
