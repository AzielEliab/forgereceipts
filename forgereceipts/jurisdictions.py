"""Structured US jurisdiction profiles for ForgeReceipts.

Honest, best-available public labels only. No invented case citations.
Does not quote statutes as advice. Not legal advice.

Coverage: federal/national baseline, 50 states, District of Columbia,
and five inhabited territories (AS, GU, MP, PR, VI).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

NOT_LEGAL_ADVICE = (
    "Not legal advice. A receipt is not legal proof. This software does "
    "not practice law, does not guarantee any outcome, and does not "
    "contact any court. Consult a licensed attorney in your jurisdiction. "
    "Read the primary sources."
)

DEPTH_NAMED = "named"
DEPTH_BASELINE = "baseline"
DEPTH_LIMITED = "limited"

_GENERIC_EFILING = (
    "Ask the clerk whether courts in your county accept electronic filing "
    "and which portal they use. This app does not connect to any portal. "
    "Not legal advice."
)

_UCCJEA_ADOPTED = (
    "This jurisdiction is widely described as having adopted a form of the "
    "UCCJEA. Confirm the current code with an attorney. This app does not "
    "decide home state or jurisdiction. Not legal advice."
)

_UCCJEA_TERRITORY = (
    "UCCJEA-style interstate custody rules may or may not apply the same "
    "way here. Ask an attorney. This app does not decide home state. "
    "Not legal advice."
)


def _tags(state: str, *, guidelines: str, extras: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    tags = [
        {"id": "best_interests", "label": f"{state} best interests of the child"},
        {"id": "guidelines", "label": guidelines},
        {"id": "uccjea", "label": "UCCJEA (interstate custody) — national"},
        {"id": "federal_evidence", "label": "Federal Rules of Evidence (advisory)"},
        {"id": "federal_civil", "label": "Federal Rules of Civil Procedure (advisory)"},
    ]
    if extras:
        tags.extend(extras)
    return tags


def _profile(
    code: str,
    name: str,
    *,
    kind: str = "state",
    depth: str = DEPTH_BASELINE,
    parenting_term: str = "parenting time",
    gal_term: str = "guardian ad litem (GAL)",
    best_interests_label: str | None = None,
    best_interests_note: str | None = None,
    guidelines_label: str = "Parenting-time / support guidelines",
    guidelines_note: str | None = None,
    efiling_kind: str = "generic",
    efiling_name: str = "Local e-filing / clerk",
    efiling_note: str | None = None,
    uccjea_adopted: bool | None = True,
    uccjea_note: str | None = None,
    extra_tags: list[dict[str, str]] | None = None,
    caption_state: str | None = None,
    exhibit_petitioner: str = "Petitioner's Exhibit 1, 2, 3…",
    exhibit_respondent: str = "Respondent's Exhibit A, B, C…",
    stub: str | None = None,
) -> dict[str, Any]:
    bi_label = best_interests_label or f"{name} best interests of the child"
    bi_note = best_interests_note or (
        f"{name} courts use a best-interests-of-the-child standard. "
        "This app does not quote or apply that jurisdiction's code to your "
        "facts. Read the current statutes and ask a licensed attorney. "
        "Not legal advice."
    )
    g_note = guidelines_note or (
        f"{name} may publish parenting-time or child-support guidelines. "
        "This app does not calculate support or parenting time. "
        "Not legal advice."
    )
    e_note = efiling_note or f"{_GENERIC_EFILING} ({name}.)"
    if uccjea_note is None:
        uccjea_note = _UCCJEA_TERRITORY if kind == "territory" else _UCCJEA_ADOPTED
    caption = caption_state or name
    return {
        "id": code,
        "name": name,
        "kind": kind,
        "depth": depth,
        "caption_state": caption,
        "parenting_term": parenting_term,
        "gal_term": gal_term,
        "best_interests_label": bi_label,
        "best_interests_note": bi_note,
        "guidelines_label": guidelines_label,
        "guidelines_note": g_note,
        "legal_tags": _tags(name, guidelines=guidelines_label, extras=extra_tags),
        "uccjea": {
            "adopted": uccjea_adopted,
            "label": "UCCJEA (interstate custody)",
            "scope": "national_uniform_act",
            "note": uccjea_note,
        },
        "efiling": {
            "kind": efiling_kind,
            "name": efiling_name,
            "odyssey": efiling_kind == "odyssey",
            "note": e_note,
        },
        "exhibit": {
            "petitioner": exhibit_petitioner,
            "respondent": exhibit_respondent,
            "default_party": "petitioner",
            "note": (
                f"Common exhibit labels in {name} papers: "
                f"{exhibit_petitioner} or {exhibit_respondent}. "
                "Confirm local practice. Not legal advice."
            ),
        },
        "stub": stub
        or (
            f"{name} profile is a structured public-label stub (depth: {depth}). "
            "It does not encode a full statute set and is not bar-certified. "
            "Not legal advice."
        ),
        "disclaimer": NOT_LEGAL_ADVICE,
    }


def _odyssey(name: str, portal: str) -> tuple[str, str, str]:
    note = (
        f"{name} courts are widely described as using Tyler Odyssey "
        f"({portal}) in many or all counties. Confirm with your clerk — "
        "portals change. This app does not connect to Odyssey or any court. "
        "Not legal advice."
    )
    return "odyssey", portal, note


def _named(name: str, portal: str) -> tuple[str, str, str]:
    note = (
        f"{name} e-filing is commonly described as {portal}. "
        "Ask your clerk which portal your county actually uses. "
        "This app does not connect to any portal. Not legal advice."
    )
    return "named", portal, note


# Federal first, then states A–Z, DC, territories.
_PROFILES: list[dict[str, Any]] = [
    _profile(
        "US",
        "United States (federal / national baseline)",
        kind="federal",
        depth=DEPTH_NAMED,
        caption_state="United States",
        parenting_term="parenting time",
        gal_term="guardian ad litem (GAL)",
        best_interests_label="Child's best interests (national framing)",
        best_interests_note=(
            "Most U.S. custody cases are heard in state court under that "
            "state's best-interest standard. Federal cases named here "
            "(Troxel, Stanley) are national references, not your state's "
            "code. Not legal advice."
        ),
        guidelines_label="National / federal advisory references",
        guidelines_note=(
            "Federal Rules of Evidence and Federal Rules of Civil Procedure "
            "are advisory references. Family court is usually state court. "
            "Not legal advice."
        ),
        efiling_kind="generic",
        efiling_name="No federal family-court portal in this app",
        efiling_note=(
            "This app does not file in federal or state court. Custody cases "
            "are usually in state court. Not legal advice."
        ),
        uccjea_adopted=None,
        uccjea_note=(
            "UCCJEA is a uniform state act about interstate custody "
            "jurisdiction. It is not itself a federal lawsuit. Not legal advice."
        ),
        stub=(
            "Federal / national baseline only. Always shown next to a state "
            "profile. Not your state's law. Not legal advice."
        ),
    ),
    _profile("AL", "Alabama", efiling_kind="named", efiling_name="AlaFile / local clerk",
             efiling_note=_named("Alabama", "AlaFile or the local clerk")[2]),
    _profile("AK", "Alaska", efiling_kind="named", efiling_name="CourtView / local e-file",
             efiling_note=_named("Alaska", "CourtView or local e-file")[2]),
    _profile(
        "AZ", "Arizona",
        guidelines_label="Arizona parenting-time / support guidelines",
        efiling_kind="named", efiling_name="AZTurboCourt / local Odyssey",
        efiling_note=(
            "Arizona e-filing is commonly described as AZTurboCourt; some "
            "counties also use Odyssey. Ask your clerk. This app does not "
            "connect to any portal. Not legal advice."
        ),
    ),
    _profile("AR", "Arkansas", efiling_kind="named", efiling_name="ARCourts / local clerk",
             efiling_note=_named("Arkansas", "ARCourts or the local clerk")[2]),
    _profile(
        "CA", "California",
        depth=DEPTH_NAMED,
        parenting_term="parenting time",
        gal_term="minor's counsel / child's counsel",
        best_interests_label="California Family Code best-interest standard",
        best_interests_note=(
            "California custody papers commonly refer to the Family Code "
            "best-interest standard. This app does not quote or apply those "
            "sections to your facts. Read the current code. Not legal advice."
        ),
        guidelines_label="California parenting-time / guideline support",
        efiling_kind="named", efiling_name="TrueFiling / local e-file",
        efiling_note=_named("California", "TrueFiling or a county e-file portal")[2],
    ),
    _profile(
        "CO", "Colorado",
        efiling_kind="named", efiling_name="ICCES",
        efiling_note=_named("Colorado", "ICCES")[2],
    ),
    _profile(
        "CT", "Connecticut",
        efiling_kind="named", efiling_name="E-Services",
        efiling_note=_named("Connecticut", "Judicial Branch E-Services")[2],
    ),
    _profile("DE", "Delaware", efiling_kind="named", efiling_name="File & Serve / local clerk",
             efiling_note=_named("Delaware", "File & Serve or the local clerk")[2]),
    _profile(
        "FL", "Florida",
        depth=DEPTH_NAMED,
        best_interests_label="Florida best-interest standard",
        best_interests_note=(
            "Florida custody papers commonly refer to a statutory "
            "best-interest standard. This app does not quote chapter text "
            "or apply it to your facts. Not legal advice."
        ),
        guidelines_label="Florida parenting-plan / support guidelines",
        efiling_kind="named", efiling_name="Florida Courts E-Filing Portal",
        efiling_note=_named("Florida", "the Florida Courts E-Filing Portal")[2],
    ),
    _profile(
        "GA", "Georgia",
        efiling_kind="named", efiling_name="PeachCourt / eFileGA",
        efiling_note=_named("Georgia", "PeachCourt or eFileGA")[2],
    ),
    _profile(
        "HI", "Hawaii",
        efiling_kind="named", efiling_name="eCourt Kokua",
        efiling_note=_named("Hawaii", "eCourt Kokua")[2],
    ),
    _profile(
        "ID", "Idaho",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("Idaho", "iCourt / Odyssey")[1],
        efiling_note=_odyssey("Idaho", "iCourt / Odyssey")[2],
    ),
    _profile(
        "IL", "Illinois",
        depth=DEPTH_NAMED,
        best_interests_label="Illinois IMDMA best-interest factors",
        best_interests_note=(
            "Illinois custody papers commonly refer to best-interest "
            "factors in the Illinois Marriage and Dissolution of Marriage "
            "Act. This app does not quote or apply those factors to your "
            "facts. Not legal advice."
        ),
        guidelines_label="Illinois parenting-time / support guidelines",
        efiling_kind="odyssey",
        efiling_name=_odyssey("Illinois", "Odyssey eFileIL")[1],
        efiling_note=_odyssey("Illinois", "Odyssey eFileIL")[2],
    ),
    _profile(
        "IN", "Indiana",
        depth=DEPTH_NAMED,
        parenting_term="parenting time",
        gal_term="guardian ad litem (GAL) / CASA",
        best_interests_label="Indiana best interests of the child",
        best_interests_note=(
            "Indiana custody and parenting-time papers commonly refer to "
            "the child's best interests. This app does not quote the "
            "Indiana Code or apply it to your facts. Default selector "
            "because the author lives in Indianapolis. Not legal advice."
        ),
        guidelines_label="Indiana Parenting Time Guidelines",
        guidelines_note=(
            "Indiana publishes Parenting Time Guidelines and Child Support "
            "Guidelines. This app does not calculate a schedule or a "
            "support number. Read the current guidelines. Not legal advice."
        ),
        extra_tags=[
            {"id": "in_ptg", "label": "Indiana Parenting Time Guidelines"},
            {"id": "in_csg", "label": "Indiana Child Support Guidelines"},
        ],
        efiling_kind="odyssey",
        efiling_name=_odyssey("Indiana", "Odyssey / mycase.in.gov")[1],
        efiling_note=_odyssey("Indiana", "Odyssey / mycase.in.gov")[2],
        stub=(
            "Indiana is the default selector because the canonical author "
            "lives in Indianapolis. Named public guideline titles only. "
            "Not legal advice."
        ),
    ),
    _profile(
        "IA", "Iowa",
        efiling_kind="named", efiling_name="EDMS",
        efiling_note=_named("Iowa", "EDMS")[2],
    ),
    _profile("KS", "Kansas", efiling_kind="named", efiling_name="eFlex / local Odyssey",
             efiling_note=(
                 "Kansas e-filing is commonly described as eFlex; some "
                 "districts use Odyssey. Ask your clerk. This app does not "
                 "connect to any portal. Not legal advice."
             )),
    _profile(
        "KY", "Kentucky",
        efiling_kind="named", efiling_name="CourtNet / local clerk",
        efiling_note=_named("Kentucky", "CourtNet or the local clerk")[2],
    ),
    _profile(
        "LA", "Louisiana",
        best_interests_label="Louisiana best-interest standard",
        efiling_kind="generic",
        efiling_note=(
            "Louisiana parish practice varies. Ask the clerk which portal "
            "or paper filing they use. This app does not connect to any "
            "portal. Not legal advice."
        ),
    ),
    _profile(
        "ME", "Maine",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("Maine", "Odyssey eCourts")[1],
        efiling_note=_odyssey("Maine", "Odyssey eCourts")[2],
    ),
    _profile(
        "MD", "Maryland",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("Maryland", "MDEC / Odyssey")[1],
        efiling_note=_odyssey("Maryland", "MDEC / Odyssey")[2],
    ),
    _profile(
        "MA", "Massachusetts",
        efiling_kind="named", efiling_name="eFileMA",
        efiling_note=_named("Massachusetts", "eFileMA")[2],
    ),
    _profile(
        "MI", "Michigan",
        depth=DEPTH_NAMED,
        best_interests_label="Michigan Child Custody Act best-interest factors",
        best_interests_note=(
            "Michigan custody papers commonly refer to best-interest "
            "factors in the Child Custody Act. This app does not quote or "
            "apply those factors to your facts. Not legal advice."
        ),
        guidelines_label="Michigan parenting-time / support guidelines",
        efiling_kind="named", efiling_name="MiFILE",
        efiling_note=_named("Michigan", "MiFILE")[2],
    ),
    _profile(
        "MN", "Minnesota",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("Minnesota", "Odyssey / MNCIS")[1],
        efiling_note=_odyssey("Minnesota", "Odyssey / MNCIS")[2],
    ),
    _profile(
        "MS", "Mississippi",
        efiling_kind="named", efiling_name="MEC",
        efiling_note=_named("Mississippi", "MEC")[2],
    ),
    _profile(
        "MO", "Missouri",
        efiling_kind="named", efiling_name="Case.net",
        efiling_note=_named("Missouri", "Case.net")[2],
    ),
    _profile("MT", "Montana"),
    _profile(
        "NE", "Nebraska",
        efiling_kind="named", efiling_name="JUSTICE",
        efiling_note=_named("Nebraska", "JUSTICE")[2],
    ),
    _profile(
        "NV", "Nevada",
        efiling_kind="named", efiling_name="local e-file / some Odyssey",
        efiling_note=(
            "Nevada county practice varies; some courts use Odyssey. Ask "
            "your clerk. This app does not connect to any portal. "
            "Not legal advice."
        ),
    ),
    _profile(
        "NH", "New Hampshire",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("New Hampshire", "Odyssey File & Serve")[1],
        efiling_note=_odyssey("New Hampshire", "Odyssey File & Serve")[2],
    ),
    _profile(
        "NJ", "New Jersey",
        efiling_kind="named", efiling_name="eCourts",
        efiling_note=_named("New Jersey", "eCourts")[2],
    ),
    _profile(
        "NM", "New Mexico",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("New Mexico", "Odyssey")[1],
        efiling_note=_odyssey("New Mexico", "Odyssey")[2],
    ),
    _profile(
        "NY", "New York",
        depth=DEPTH_NAMED,
        gal_term="attorney for the child (AFC)",
        best_interests_label="New York best-interest standard",
        best_interests_note=(
            "New York custody papers commonly refer to a best-interest "
            "standard under the Domestic Relations Law. Children's counsel "
            "is often called the attorney for the child. This app does not "
            "quote or apply those rules to your facts. Not legal advice."
        ),
        guidelines_label="New York parenting-time / CSSA support guidelines",
        efiling_kind="named", efiling_name="NYSCEF",
        efiling_note=_named("New York", "NYSCEF")[2],
    ),
    _profile(
        "NC", "North Carolina",
        efiling_kind="named", efiling_name="eCourts",
        efiling_note=_named("North Carolina", "eCourts")[2],
    ),
    _profile(
        "ND", "North Dakota",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("North Dakota", "Odyssey")[1],
        efiling_note=_odyssey("North Dakota", "Odyssey")[2],
    ),
    _profile(
        "OH", "Ohio",
        depth=DEPTH_NAMED,
        guidelines_label="Ohio standard parenting-time / support guidelines",
        guidelines_note=(
            "Many Ohio counties publish a standard parenting-time schedule "
            "and the state publishes support guidelines. This app does not "
            "calculate either. Ask your clerk. Not legal advice."
        ),
        efiling_kind="named", efiling_name="county e-file / often Odyssey",
        efiling_note=(
            "Ohio e-filing is county-by-county; many counties use Odyssey. "
            "Ask your clerk. This app does not connect to any portal. "
            "Not legal advice."
        ),
    ),
    _profile(
        "OK", "Oklahoma",
        efiling_kind="named", efiling_name="OSCN",
        efiling_note=_named("Oklahoma", "OSCN")[2],
    ),
    _profile(
        "OR", "Oregon",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("Oregon", "Oregon eCourt / Odyssey")[1],
        efiling_note=_odyssey("Oregon", "Oregon eCourt / Odyssey")[2],
    ),
    _profile(
        "PA", "Pennsylvania",
        efiling_kind="named", efiling_name="PACFile",
        efiling_note=_named("Pennsylvania", "PACFile")[2],
    ),
    _profile(
        "RI", "Rhode Island",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("Rhode Island", "Odyssey")[1],
        efiling_note=_odyssey("Rhode Island", "Odyssey")[2],
    ),
    _profile("SC", "South Carolina"),
    _profile(
        "SD", "South Dakota",
        efiling_kind="named", efiling_name="UJS e-file / local clerk",
        efiling_note=_named("South Dakota", "UJS e-file or the local clerk")[2],
    ),
    _profile("TN", "Tennessee", efiling_kind="named", efiling_name="local e-file / some Odyssey",
             efiling_note=(
                 "Tennessee county practice varies; some courts use Odyssey. "
                 "Ask your clerk. This app does not connect to any portal. "
                 "Not legal advice."
             )),
    _profile(
        "TX", "Texas",
        depth=DEPTH_NAMED,
        parenting_term="possession and access",
        gal_term="amicus attorney / attorney ad litem",
        best_interests_label="Texas Family Code best-interest standard",
        best_interests_note=(
            "Texas custody papers commonly refer to the Family Code "
            "best-interest standard and to possession and access. This app "
            "does not quote or apply those sections to your facts. "
            "Not legal advice."
        ),
        guidelines_label="Texas possession / child-support guidelines",
        efiling_kind="named", efiling_name="eFileTexas",
        efiling_note=(
            "Texas statewide e-file is commonly described as eFileTexas; "
            "some counties also use Odyssey/Tyler. Ask your clerk. This "
            "app does not connect to any portal. Not legal advice."
        ),
    ),
    _profile(
        "UT", "Utah",
        efiling_kind="named", efiling_name="Xchange / Green Filing",
        efiling_note=_named("Utah", "Xchange or Green Filing")[2],
    ),
    _profile(
        "VT", "Vermont",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("Vermont", "Odyssey")[1],
        efiling_note=_odyssey("Vermont", "Odyssey")[2],
    ),
    _profile(
        "VA", "Virginia",
        efiling_kind="named", efiling_name="OES eFiling / local clerk",
        efiling_note=_named("Virginia", "OES eFiling or the local clerk")[2],
    ),
    _profile(
        "WA", "Washington",
        depth=DEPTH_NAMED,
        best_interests_label="Washington Parenting Act / parenting plan",
        best_interests_note=(
            "Washington custody papers commonly refer to a parenting plan "
            "under the Parenting Act. This app does not quote or apply "
            "those sections to your facts. Not legal advice."
        ),
        guidelines_label="Washington parenting-plan / support guidelines",
        efiling_kind="named", efiling_name="local e-file / some Odyssey",
        efiling_note=(
            "Washington superior-court e-filing varies by county; some use "
            "Odyssey. Ask your clerk. This app does not connect to any "
            "portal. Not legal advice."
        ),
    ),
    _profile("WV", "West Virginia"),
    _profile(
        "WI", "Wisconsin",
        depth=DEPTH_NAMED,
        efiling_kind="odyssey",
        efiling_name=_odyssey("Wisconsin", "CCAP / Odyssey eFiling")[1],
        efiling_note=_odyssey("Wisconsin", "CCAP / Odyssey eFiling")[2],
    ),
    _profile("WY", "Wyoming"),
    _profile(
        "DC", "District of Columbia",
        kind="district",
        depth=DEPTH_NAMED,
        caption_state="District of Columbia",
        efiling_kind="named", efiling_name="CaseFileXpress / local e-file",
        efiling_note=_named("the District of Columbia", "CaseFileXpress or the local e-file portal")[2],
        stub=(
            "District of Columbia is included with the 50 states. "
            "Structured public-label stub. Not legal advice."
        ),
    ),
    _profile("AS", "American Samoa", kind="territory", depth=DEPTH_LIMITED,
             uccjea_adopted=None, caption_state="American Samoa"),
    _profile("GU", "Guam", kind="territory", depth=DEPTH_LIMITED,
             uccjea_adopted=None, caption_state="Guam"),
    _profile("MP", "Northern Mariana Islands", kind="territory", depth=DEPTH_LIMITED,
             uccjea_adopted=None, caption_state="Northern Mariana Islands"),
    _profile("PR", "Puerto Rico", kind="territory", depth=DEPTH_LIMITED,
             uccjea_adopted=None, caption_state="Puerto Rico",
             parenting_term="custodial time",
             efiling_kind="named", efiling_name="local e-file / clerk",
             efiling_note=_named("Puerto Rico", "the local e-file portal or clerk")[2]),
    _profile("VI", "U.S. Virgin Islands", kind="territory", depth=DEPTH_LIMITED,
             uccjea_adopted=None, caption_state="U.S. Virgin Islands"),
]

JURISDICTIONS: list[dict[str, Any]] = _PROFILES
_BY_ID: dict[str, dict[str, Any]] = {p["id"]: p for p in _PROFILES}

DEFAULT_JURISDICTION = "IN"
FEDERAL_ID = "US"

STATE_IDS = [p["id"] for p in _PROFILES if p["kind"] == "state"]
DISTRICT_IDS = [p["id"] for p in _PROFILES if p["kind"] == "district"]
TERRITORY_IDS = [p["id"] for p in _PROFILES if p["kind"] == "territory"]


def get_jurisdiction(code: str | None) -> dict[str, Any]:
    jid = (code or DEFAULT_JURISDICTION).strip().upper()
    aliases = {
        "USA": "US",
        "FED": "US",
        "FEDERAL": "US",
        "NATIONAL": "US",
        "D.C.": "DC",
        "WASHINGTON DC": "DC",
        "WASHINGTON, DC": "DC",
    }
    jid = aliases.get(jid, jid)
    if jid not in _BY_ID:
        # Accept full names, case-insensitive.
        for prof in _PROFILES:
            if prof["name"].upper() == jid or prof["caption_state"].upper() == jid:
                jid = prof["id"]
                break
        else:
            jid = DEFAULT_JURISDICTION
    return deepcopy(_BY_ID[jid])


def list_jurisdictions() -> list[dict[str, Any]]:
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "kind": p["kind"],
            "depth": p["depth"],
            "odyssey": bool(p["efiling"]["odyssey"]),
        }
        for p in _PROFILES
    ]


def federal_profile() -> dict[str, Any]:
    return deepcopy(_BY_ID[FEDERAL_ID])
