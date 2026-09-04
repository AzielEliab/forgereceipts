"""Beginner procedure guide. Educational stubs only. Not legal advice."""

from __future__ import annotations

from typing import Any

from forgereceipts.jurisdictions import FEDERAL_ID, get_jurisdiction
from forgereceipts.legal import FEDERAL_BASELINE, NOT_LEGAL_ADVICE


def _topic(
    tid: str,
    title: str,
    body: str,
    *,
    scope: str = "state",
) -> dict[str, str]:
    return {"id": tid, "title": title, "body": body, "scope": scope}


def topics_for(jurisdiction: str | None = None) -> dict[str, Any]:
    state = get_jurisdiction(jurisdiction)
    federal = get_jurisdiction(FEDERAL_ID)
    name = state["name"]
    parenting = state["parenting_term"]
    gal = state["gal_term"]
    exhibit_p = state["exhibit"]["petitioner"]
    exhibit_r = state["exhibit"]["respondent"]
    efile = state["efiling"]
    guidelines = state["guidelines_label"]
    bi = state["best_interests_label"]

    state_topics = [
        _topic(
            "motions",
            "Motions (asking the court for something)",
            (
                f"A motion is a written ask. In {name}, you usually caption it "
                "with the court, the parties, and the cause number from *your* "
                "papers. Write in your own words. This app can fill a blank "
                "caption locally. It does not file the motion. Have an attorney "
                "review anything you intend to file. Not legal advice."
            ),
        ),
        _topic(
            "contempt",
            "Contempt (someone did not follow an order)",
            (
                f"Contempt is about an existing order, not a new fight. In {name}, "
                "people often keep a dated log of what the order said and what "
                "happened. Hash the order and the proof (Forensics). This app "
                "does not decide whether anyone is in contempt. Not legal advice."
            ),
        ),
        _topic(
            "gal",
            f"Child's lawyer / {gal}",
            (
                f"In {name} the person appointed to speak to the child's "
                f"interests is often called a {gal}. Names differ by court. "
                "This app does not contact that person. You can log meetings "
                "and hash reports you already have. Not legal advice."
            ),
        ),
        _topic(
            "discovery",
            "Discovery (exchanging information)",
            (
                f"{name} courts may allow requests for documents, written "
                "questions, or depositions. Deadlines and forms are local. "
                "This app does not send discovery and does not talk to the "
                "other side. Keep hashed copies of what you send or receive. "
                "Not legal advice."
            ),
        ),
        _topic(
            "uccjea",
            "UCCJEA (when more than one state is involved)",
            (
                f"{state['uccjea']['note']} "
                f"If the child has lived in more than one place, {name} and "
                "another state may both look at home-state questions. This app "
                "does not pick a home state. Ask an attorney. Not legal advice."
            ),
        ),
        _topic(
            "exhibits",
            "How to label exhibits",
            (
                f"A common {name} pattern is {exhibit_p} if you are the "
                f"petitioner, or {exhibit_r} if you are the respondent. "
                "Keep a hashed copy of each file in Forensics. Confirm local "
                "practice with the clerk. Not legal advice."
            ),
        ),
        _topic(
            "best_interests",
            bi,
            (
                f"{state['best_interests_note']} "
                f"Every Log and Journal entry in this app asks how the facts "
                f"relate to the child — including {parenting}."
            ),
        ),
        _topic(
            "guidelines",
            guidelines,
            state["guidelines_note"],
        ),
        _topic(
            "efiling",
            f"E-filing in {name}",
            (
                f"{efile['note']} "
                + (
                    "This profile marks Odyssey because that system is widely "
                    "described for this jurisdiction. "
                    if efile.get("odyssey")
                    else "If your court does not use Odyssey, follow the clerk's "
                    "generic e-filing or paper steps. "
                )
                + "Print or export locally. You upload. ForgeReceipts never transmits."
            ),
        ),
    ]

    federal_topics = [
        _topic(
            "federal_baseline",
            "Federal / national baseline (always on)",
            (
                f"{federal['stub']} Troxel and Stanley are United States "
                "Supreme Court names often discussed in parenting cases. "
                "Federal Rules of Evidence and Federal Rules of Civil Procedure "
                "are advisory — most custody cases are in state court. UCCJEA "
                "is a uniform state act about interstate custody. None of this "
                f"replaces {name} law. Not legal advice."
            ),
            scope="federal",
        ),
        _topic(
            "federal_evidence",
            "Federal Rules of Evidence (advisory)",
            (
                "The Federal Rules of Evidence are a national reference about "
                "what courts may consider. Family court is usually state court "
                "with state evidence rules. This app does not decide "
                "admissibility. Not legal advice."
            ),
            scope="federal",
        ),
        _topic(
            "federal_civil",
            "Federal Rules of Civil Procedure (advisory)",
            (
                "The Federal Rules of Civil Procedure are a national reference "
                "about civil-case steps. Your {name} family court uses local "
                "and state rules. This app does not file or serve. "
                "Not legal advice.".replace("{name}", name)
            ),
            scope="federal",
        ),
    ]

    return {
        "disclaimer": NOT_LEGAL_ADVICE,
        "jurisdiction": {
            "id": state["id"],
            "name": state["name"],
            "kind": state["kind"],
            "depth": state["depth"],
        },
        "federal": {"id": FEDERAL_ID, "name": federal["name"]},
        "topics": state_topics + federal_topics,
        "baseline": list(FEDERAL_BASELINE),
        "honesty": (
            f"Depth for {name} is '{state['depth']}'. "
            "Named labels are public titles only. No fabricated holdings. "
            "Not legal advice."
        ),
    }
