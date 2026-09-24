"""Homepage Download stays the counted one-click asset link.

Focus, a quiet footer, and prefers-color-scheme are part of the landing.
The /download route, default asset, and fork keys are unchanged.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "workers" / "download-tracker" / "src" / "index.js").read_text(
    encoding="utf-8"
)
HTML = INDEX[INDEX.index("<!doctype html>") : INDEX.rindex("</html>") + 7]


def test_primary_download_is_the_counted_asset() -> None:
    assert 'const DEFAULT_ASSET = "forgereceipts-0.3.0.tar.gz"' in INDEX
    assert 'id="downloadBtn" class="btn block primary dl" href="/download?asset=${DEFAULT_ASSET}"' in HTML
    assert ">Download</a>" in HTML
    assert 'url.pathname === "/download"' in INDEX
    assert "await increment(env, dims" in INDEX


def test_landing_has_focus_footer_and_color_scheme() -> None:
    assert "a:focus-visible, button:focus-visible, input:focus-visible" in HTML
    assert "outline: 2px solid var(--focus)" in HTML
    assert '<footer class="quiet">' in HTML
    assert "prefers-color-scheme: light" in HTML
    assert "prefers-color-scheme: dark" in HTML
    assert 'name="viewport"' in HTML
    assert "Aziel Eliab" in HTML
