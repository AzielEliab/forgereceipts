"""Local settings persisted in the data dir. Never uploaded."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgereceipts.jurisdictions import DEFAULT_JURISDICTION, get_jurisdiction
from forgereceipts.plain import PlainError

SETTINGS_NAME = "settings.json"


def settings_path(data_dir: str | Path) -> Path:
    return Path(data_dir) / SETTINGS_NAME


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_settings() -> dict[str, Any]:
    return {
        "jurisdiction": DEFAULT_JURISDICTION,
        "updated": None,
    }


def load_settings(data_dir: str | Path) -> dict[str, Any]:
    path = settings_path(data_dir)
    data = default_settings()
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = {}
        if isinstance(raw, dict):
            if raw.get("jurisdiction"):
                data["jurisdiction"] = get_jurisdiction(str(raw["jurisdiction"]))["id"]
            if raw.get("updated"):
                data["updated"] = raw["updated"]
    return data


def save_settings(data_dir: str | Path, **updates: Any) -> dict[str, Any]:
    directory = Path(data_dir)
    directory.mkdir(parents=True, exist_ok=True)
    current = load_settings(directory)
    if "jurisdiction" in updates:
        code = str(updates.get("jurisdiction") or "").strip()
        if not code:
            raise PlainError("Pick a state from the list.")
        current["jurisdiction"] = get_jurisdiction(code)["id"]
    current["updated"] = _now()
    path = settings_path(directory)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return current
