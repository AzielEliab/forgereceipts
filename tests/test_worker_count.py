from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "workers" / "download-tracker" / "src" / "index.js").read_text(
    encoding="utf-8"
)


def test_count_returns_views_downloads_and_total() -> None:
    """YELLOW audit: GET /count must not be {project, total} only."""
    assert 'url.pathname === "/count"' in INDEX
    assert "views: stats.views || 0" in INDEX
    assert "downloads: stats.downloads || 0" in INDEX
    assert "total: stats.total || 0" in INDEX
    assert "json({ project: PROJECT, total: stats.total || 0 })" not in INDEX
    # azhub convention: views from __views__, downloads from download keys, total = downloads
    assert "function viewsKey()" in INDEX
    assert "downloads: shown" in INDEX


def test_views_increment_on_home_downloads_on_download() -> None:
    assert "url.pathname === \"/\" && request.method === \"GET\"" in INDEX
    assert "await incrementViews(env)" in INDEX
    assert 'url.pathname === "/download"' in INDEX
    assert "await increment(env, dims)" in INDEX
