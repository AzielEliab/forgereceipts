from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COPY_PATHS = (
    ROOT / "README.md",
    ROOT / "SKILL.md",
    ROOT / "workers" / "download-tracker" / "README.md",
    ROOT / "workers" / "download-tracker" / "src" / "runtime.js",
)

EXCLUSIVE_HEADING = "Use with Grok, ChatGPT, Venice"

FULL_CLIENTS = (
    "ChatGPT (GPT Actions / OpenAI)",
    "Grok (xAI)",
    "Venice",
    "Claude (Anthropic)",
    "Cursor (MCP)",
    "Glama (MCP)",
    "Perplexity",
    "Microsoft Copilot / Bing",
    "Google Gemini / Vertex",
    "Mistral",
    "Meta AI",
    "Apple Intelligence surfaces",
    "Amazon Q tooling",
    "DuckAssist",
    "You.com",
    "Cohere",
    "other MCP/OpenAPI-capable assistants",
)


def test_exclusive_heading_is_gone() -> None:
    hits: list[str] = []
    for path in COPY_PATHS:
        text = path.read_text(encoding="utf-8")
        if EXCLUSIVE_HEADING in text:
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []


def test_copy_lists_full_ai_clients() -> None:
    missing: list[str] = []
    for path in COPY_PATHS:
        text = path.read_text(encoding="utf-8")
        for client in FULL_CLIENTS:
            if client not in text:
                missing.append(f"{path.relative_to(ROOT)}: {client}")
    assert missing == []


def test_readme_section_is_use_with_ai_assistants() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "## Use with AI assistants" in readme
    assert "Aziel Eliab" in readme


def test_embedded_skill_matches_skill_md() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    runtime = (ROOT / "workers" / "download-tracker" / "src" / "runtime.js").read_text(
        encoding="utf-8"
    )
    marker = "const SKILL_MARKDOWN = "
    start = runtime.index(marker) + len(marker)
    end = runtime.index(";", start)
    embedded = ast.literal_eval(runtime[start:end])
    assert embedded == skill
