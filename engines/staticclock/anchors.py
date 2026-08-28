"""Top-30 geographic anchors and free-text geo resolution.

Unknown input maps to the nearest anchor (alias, then fuzzy, then
default). No user identification. Resolution is a function of the
string, not of a profile.
"""

from __future__ import annotations

import difflib
import re
import unicodedata

from staticclock.index import anchors as _anchor_map

TOP_30: tuple[str, ...] = (
    "United States",
    "United Kingdom",
    "Germany",
    "France",
    "Spain",
    "Italy",
    "Brazil",
    "Mexico",
    "Canada",
    "India",
    "China",
    "Japan",
    "South Korea",
    "Australia",
    "New Zealand",
    "South Africa",
    "Nigeria",
    "Egypt",
    "Israel",
    "Turkey",
    "Russia",
    "Ukraine",
    "Poland",
    "Netherlands",
    "Sweden",
    "Norway",
    "Finland",
    "Argentina",
    "Chile",
    "Saudi Arabia",
)

DEFAULT_ANCHOR = "United States"

# US states and DC resolve to the United States anchor.
_US_STATES: tuple[str, ...] = (
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "district of columbia",
    "washington dc", "washington d.c.", "dc",
)

_ALIASES: dict[str, str] = {
    "usa": "United States",
    "us": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "america": "United States",
    "united states of america": "United States",
    "indianapolis": "United States",
    "chicago": "United States",
    "new york city": "United States",
    "nyc": "United States",
    "los angeles": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "britain": "United Kingdom",
    "great britain": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    "gb": "United Kingdom",
    "london": "United Kingdom",
    "deutschland": "Germany",
    "berlin": "Germany",
    "paris": "France",
    "madrid": "Spain",
    "rome": "Italy",
    "brasil": "Brazil",
    "sao paulo": "Brazil",
    "são paulo": "Brazil",
    "mexico city": "Mexico",
    "méxico": "Mexico",
    "toronto": "Canada",
    "bharat": "India",
    "hindustan": "India",
    "prc": "China",
    "people's republic of china": "China",
    "peoples republic of china": "China",
    "nippon": "Japan",
    "nihon": "Japan",
    "tokyo": "Japan",
    "korea": "South Korea",
    "republic of korea": "South Korea",
    "rok": "South Korea",
    "seoul": "South Korea",
    "sydney": "Australia",
    "auckland": "New Zealand",
    "aotearoa": "New Zealand",
    "rsa": "South Africa",
    "johannesburg": "South Africa",
    "lagos": "Nigeria",
    "cairo": "Egypt",
    "tel aviv": "Israel",
    "jerusalem": "Israel",
    "turkiye": "Turkey",
    "türkiye": "Turkey",
    "istanbul": "Turkey",
    "moscow": "Russia",
    "kyiv": "Ukraine",
    "kiev": "Ukraine",
    "warsaw": "Poland",
    "holland": "Netherlands",
    "amsterdam": "Netherlands",
    "stockholm": "Sweden",
    "oslo": "Norway",
    "helsinki": "Finland",
    "buenos aires": "Argentina",
    "santiago": "Chile",
    "ksa": "Saudi Arabia",
    "saudi": "Saudi Arabia",
    "riyadh": "Saudi Arabia",
}

for _state in _US_STATES:
    _ALIASES[_state] = "United States"


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", stripped.casefold()).strip()


def _anchor_lookup() -> dict[str, str]:
    table: dict[str, str] = {}
    for name in TOP_30:
        table[_fold(name)] = name
    table.update(_ALIASES)
    return table


def resolve_geo(geo: str) -> str:
    """Map free text to a Top-30 anchor. Never raises on unknown input."""
    folded = _fold(geo)
    if not folded:
        return DEFAULT_ANCHOR
    lookup = _anchor_lookup()
    if folded in lookup:
        return lookup[folded]
    candidates = list(lookup.keys())
    match = difflib.get_close_matches(folded, candidates, n=1, cutoff=0.72)
    if match:
        return lookup[match[0]]
    # Try last token (e.g. "somewhere in Indiana").
    tokens = folded.split()
    if len(tokens) > 1:
        for token in reversed(tokens):
            if token in lookup:
                return lookup[token]
        match = difflib.get_close_matches(tokens[-1], candidates, n=1, cutoff=0.8)
        if match:
            return lookup[match[0]]
    return DEFAULT_ANCHOR


def is_anchor(name: str) -> bool:
    return name in _anchor_map()


def basket_of(anchor: str) -> list[str]:
    rec = _anchor_map()[anchor]
    return list(rec["basket"])
