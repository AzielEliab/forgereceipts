from __future__ import annotations

from pathlib import Path

from forgereceipts.filing import templates
from forgereceipts.guide import topics_for
from forgereceipts.jurisdictions import (
    DISTRICT_IDS,
    STATE_IDS,
    TERRITORY_IDS,
    get_jurisdiction,
    list_jurisdictions,
)
from forgereceipts.legal import FEDERAL_BASELINE, reference
from forgereceipts.settings import load_settings, save_settings


FIFTY = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
}


def test_fifty_states_plus_dc_and_federal() -> None:
    assert set(STATE_IDS) == FIFTY
    assert DISTRICT_IDS == ["DC"]
    ids = {row["id"] for row in list_jurisdictions()}
    assert "US" in ids
    assert "DC" in ids
    assert FIFTY <= ids
    for code in FIFTY | {"DC", "US"}:
        prof = get_jurisdiction(code)
        assert prof["id"] == code
        assert prof["disclaimer"].lower().startswith("not legal advice")


def test_territories_optional_and_honest() -> None:
    assert set(TERRITORY_IDS) == {"AS", "GU", "MP", "PR", "VI"}
    for code in TERRITORY_IDS:
        assert get_jurisdiction(code)["depth"] == "limited"


def test_federal_baseline_always_present() -> None:
    names = {row["name"] for row in FEDERAL_BASELINE}
    assert "Troxel v. Granville" in names
    assert "Stanley v. Illinois" in names
    assert "Federal Rules of Evidence" in names
    assert "Federal Rules of Civil Procedure" in names
    assert "UCCJEA" in names
    for code in ("IN", "TX", "CA", "NY", "US"):
        ref = reference(code)
        assert ref["baseline"] == FEDERAL_BASELINE
        assert ref["federal"]["id"] == "US"
        assert "not legal advice" in ref["disclaimer"].lower()
        assert ref["state"]["id"] == code


def test_state_customizes_tags_and_filing() -> None:
    indiana = reference("IN")
    texas = reference("TX")
    assert "Indiana Parenting Time Guidelines" in indiana["state"]["guidelines_label"]
    assert indiana["state"]["efiling"]["odyssey"] is True
    assert texas["state"]["parenting_term"] == "possession and access"
    assert texas["state"]["efiling"]["name"] == "eFileTexas"
    inn = templates("IN")
    tx = templates("TX")
    assert inn["caption_placeholders"]["state"] == "Indiana"
    assert tx["caption_placeholders"]["state"] == "Texas"
    assert any("Odyssey" in item for item in inn["efiling_checklist"])
    assert any("eFileTexas" in item or "generic" in item.lower() or "Odyssey" in item for item in tx["efiling_checklist"])


def test_guide_mentions_state_terms() -> None:
    ny = topics_for("NY")
    titles = " ".join(t["title"] + t["body"] for t in ny["topics"])
    assert "attorney for the child" in titles.lower()
    assert any(t["scope"] == "federal" for t in ny["topics"])
    assert "not legal advice" in ny["disclaimer"].lower()


def test_settings_persist(tmp_path: Path) -> None:
    first = load_settings(tmp_path)
    assert first["jurisdiction"] == "IN"
    saved = save_settings(tmp_path, jurisdiction="CA")
    assert saved["jurisdiction"] == "CA"
    again = load_settings(tmp_path)
    assert again["jurisdiction"] == "CA"
    assert (tmp_path / "settings.json").is_file()


def test_unknown_jurisdiction_falls_back_to_indiana() -> None:
    assert get_jurisdiction("ZZ")["id"] == "IN"
    assert get_jurisdiction("california")["id"] == "CA"


def test_no_invented_state_case_cites() -> None:
    banned = (" v. ", " v ")
    for row in list_jurisdictions():
        if row["id"] == "US":
            continue
        prof = get_jurisdiction(row["id"])
        blob = " ".join(
            [
                prof["best_interests_note"],
                prof["guidelines_note"],
                prof["efiling"]["note"],
                prof["stub"],
            ]
        )
        # State profiles must not invent case captions. Federal names live in baseline.
        assert "Horton" not in blob
        assert "Altman" not in blob
        assert "GodLock.AZ" not in blob
        for token in banned:
            assert token not in blob
