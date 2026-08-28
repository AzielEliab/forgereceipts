"""Bundled static language / geography index.

v0.1 ships the Top-30 anchor set. A full 100+ language index is a
replacement update of this JSON, not a network fetch and not a learned
model.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any


@lru_cache(maxsize=1)
def load_index() -> dict[str, Any]:
    raw = files("staticclock").joinpath("data/index.json").read_text(encoding="utf-8")
    return json.loads(raw)


def anchors() -> dict[str, Any]:
    return load_index()["anchors"]


def languages() -> dict[str, list[str]]:
    data = load_index()["languages"]
    return {k: list(v) for k, v in data.items()}


def record(name: str) -> dict[str, Any]:
    return dict(anchors()[name])
