from __future__ import annotations

import gzip
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "workers" / "download-tracker" / "src" / "index.js"
PUBLIC = ROOT / "workers" / "download-tracker" / "public"


def _default_asset() -> str:
    text = WORKER.read_text(encoding="utf-8")
    match = re.search(r'const DEFAULT_ASSET = "([^"]+)";', text)
    assert match, "DEFAULT_ASSET must be set in the download Worker"
    return match.group(1)


def test_default_asset_filename_is_hosted() -> None:
    asset = _default_asset()
    assert asset == "forgereceipts-0.3.0.tar.gz"
    hosted = PUBLIC / asset
    assert hosted.is_file(), f"asset not hosted: {hosted}"
    assert hosted.name == asset
    with gzip.open(hosted, "rb") as fh:
        assert fh.read(2), "hosted asset must be a readable gzip"


def test_identity_is_aziel_eliab_only() -> None:
    text = WORKER.read_text(encoding="utf-8")
    assert "Aziel Eliab" in text
    assert "Horton" not in text
