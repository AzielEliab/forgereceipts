"""Local filing templates and conceptual e-filing checklists.

Does not contact Odyssey, any court, email, or a cloud portal.
Export is a local .txt or .html file the user prints or uploads themselves.
"""

from __future__ import annotations

import html
from datetime import date
from typing import Any

NOT_LEGAL_ADVICE = (
    "NOT LEGAL ADVICE. This is a local template. It does not file anything. "
    "It does not talk to Odyssey or any court. Have a licensed attorney "
    "review anything you intend to file."
)

EFILING_CHECKLIST = [
    "Ask the clerk (yourself) whether your court accepts electronic filing and which portal it uses. This app does not connect to any portal.",
    "Confirm accepted file types, size limits, and naming rules with the clerk or the court's published instructions.",
    "Caption the motion with the correct court, county, parties, and cause number from *your* papers — not from this app.",
    "Label exhibits: Petitioner's Exhibit 1, 2, 3… or Respondent's Exhibit A, B, C… Keep a hashed copy of each file in Forensics.",
    "Attach a certificate of service if your rules require one. This app does not serve anyone.",
    "Check page limits, font, and margins in the local rules. This app does not know your local rules.",
    "Print or export locally. You upload or walk the papers in. ForgeReceipts never transmits them.",
    "After you file, hash the stamped copy (Forensics) and log a receipt (Incident log). Corrections are new receipts, never edits.",
]


def exhibit_labels(party: str, count: int) -> list[str]:
    party = (party or "petitioner").strip().lower()
    n = max(0, int(count))
    if party.startswith("resp"):
        # Respondent's Exhibit A, B, C…
        labels = []
        for i in range(n):
            name = ""
            x = i
            while True:
                name = chr(ord("A") + (x % 26)) + name
                x = x // 26 - 1
                if x < 0:
                    break
            labels.append(f"Respondent's Exhibit {name}")
        return labels
    return [f"Petitioner's Exhibit {i}" for i in range(1, n + 1)]


def motion_caption(
    *,
    state: str = "Indiana",
    court_name: str = "[COURT NAME]",
    petitioner: str = "[PETITIONER]",
    respondent: str = "[RESPONDENT]",
    cause_no: str = "[CAUSE NO.]",
    party_role: str = "Petitioner",
    title: str = "MOTION",
) -> str:
    return (
        f"STATE OF {state.upper()}\n"
        f"IN THE {court_name}\n\n"
        "IN RE THE CARE / CUSTODY OF A MINOR CHILD\n\n"
        f"{petitioner},\n"
        "    Petitioner,\n\n"
        f"v.                                    Cause No. {cause_no}\n\n"
        f"{respondent},\n"
        "    Respondent.\n\n"
        f"{party_role.upper()}'S {title.upper()}\n"
    )


def render_txt(fields: dict[str, Any]) -> str:
    exhibits = exhibit_labels(fields.get("party") or "petitioner", int(fields.get("exhibit_count") or 0))
    caption = motion_caption(
        state=fields.get("state") or "Indiana",
        court_name=fields.get("court_name") or "[COURT NAME]",
        petitioner=fields.get("petitioner") or "[PETITIONER]",
        respondent=fields.get("respondent") or "[RESPONDENT]",
        cause_no=fields.get("cause_no") or "[CAUSE NO.]",
        party_role=fields.get("party_role") or "Petitioner",
        title=fields.get("title") or "MOTION",
    )
    body = (fields.get("body") or "[Body of the motion. Write in your own words. This is a placeholder.]").strip()
    lines = [
        NOT_LEGAL_ADVICE,
        "",
        caption.strip(),
        "",
        body,
        "",
        "EXHIBITS (labels only — attach the files yourself):",
    ]
    if exhibits:
        lines.extend(f"  - {lab}" for lab in exhibits)
    else:
        lines.append("  (none listed)")
    lines.extend(
        [
            "",
            "CONCEPTUAL E-FILING CHECKLIST (this app does not file):",
            *[f"  [ ] {item}" for item in EFILING_CHECKLIST],
            "",
            f"Exported locally on {date.today().isoformat()}. Not served. Not filed.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(fields: dict[str, Any]) -> str:
    text = render_txt(fields)
    escaped = html.escape(text)
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<title>ForgeReceipts local export — NOT LEGAL ADVICE</title>"
        "<style>body{font:14px/1.45 ui-monospace,monospace;max-width:48rem;"
        "margin:2rem auto;padding:0 1rem;white-space:pre-wrap;background:#f7f4ee;"
        "color:#1b1b18;} .banner{background:#7a1f1f;color:#fff;padding:.6rem .8rem;"
        "font-family:system-ui,sans-serif;margin:0 0 1rem;}</style></head><body>"
        "<div class='banner'>NOT LEGAL ADVICE. Local export only. Not filed. "
        "Does not contact any court.</div>"
        f"<pre>{escaped}</pre></body></html>\n"
    )


def templates() -> dict[str, Any]:
    return {
        "disclaimer": NOT_LEGAL_ADVICE,
        "caption_placeholders": {
            "state": "Indiana",
            "court_name": "[COURT NAME]",
            "petitioner": "[PETITIONER]",
            "respondent": "[RESPONDENT]",
            "cause_no": "[CAUSE NO.]",
            "party_role": "Petitioner",
            "title": "MOTION",
        },
        "exhibit_examples": [
            "Petitioner's Exhibit 1",
            "Petitioner's Exhibit 2",
            "Respondent's Exhibit A",
            "Respondent's Exhibit B",
        ],
        "efiling_checklist": list(EFILING_CHECKLIST),
        "note": "Conceptual checklist only. ForgeReceipts never talks to Odyssey or any court.",
    }
