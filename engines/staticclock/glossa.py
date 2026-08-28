"""Glossa: region → primary language, then one dialect of five.

Routing uses the static bundled index only. Not a learned model. Not
100+ languages in v0.1 — Top-30 plus five dialectal variants each.
"""

from __future__ import annotations

from staticclock.index import languages as _languages
from staticclock.index import record
from staticclock.polarize import shake


def primary_language(region: str) -> str:
    return str(record(region)["language"])


def dialects_for(language: str) -> list[str]:
    table = _languages()
    if language not in table:
        raise KeyError(language)
    return list(table[language])


def pick_dialect(language: str, nonce: bytes) -> str:
    return shake(dialects_for(language), nonce, salt=b"dialect")
