from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNED = ("Horton", "Collin Horton", "Jack Altman", "GodLock.AZ")
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist"}


def test_tree_does_not_credit_horton() -> None:
    hits: list[str] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".py", ".js", ".html", ".css", ".toml", ".json", ".dart", ".txt", ".sh"}:
            continue
        if path.parent.name == "tests" or path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in BANNED:
            if token in text:
                hits.append(f"{path.relative_to(ROOT)}: {token}")
    assert hits == []
