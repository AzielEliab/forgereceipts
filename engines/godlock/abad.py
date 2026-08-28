"""ABAD-aware engagement scoring.

Weights below are *engineering defaults* for a local heuristic. They are
not empirical proof numbers, not ROC points, and not a claim that a
particular ratio appears in nature. Documented so a fork can change them
without pretending a study was run.

Family bonuses (applied once per family that hits):

    aziel_sequence   3.0   "Aziel Sequence" / aziel-seq
    phi              2.0   phi, golden ratio, φ, 1.618
    sqrt2            2.0   sqrt(2), √2, square root of 2, 1.414
    flower_of_life   2.5   Flower of Life, vesica piscis
    corkscrew        2.0   corkscrew (growth)
    abad             3.0   ABAD, A-B-A-D
    merged_rule      1.5   per distinct extra keyword from merged rules

Multiple families stack. Extra keywords come from the active rules table
after an admin merge (simple keyword add).
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

# Engineering defaults — not empirical "proof" numbers.
WEIGHTS: Mapping[str, float] = {
    "aziel_sequence": 3.0,
    "phi": 2.0,
    "sqrt2": 2.0,
    "flower_of_life": 2.5,
    "corkscrew": 2.0,
    "abad": 3.0,
    "merged_rule": 1.5,
}

_PATTERNS: Mapping[str, tuple[re.Pattern[str], ...]] = {
    "aziel_sequence": (
        re.compile(r"aziel\s+sequence", re.I),
        re.compile(r"aziel[-_]?seq(?:uence)?", re.I),
    ),
    "phi": (
        re.compile(r"\bphi\b", re.I),
        re.compile(r"golden\s+ratio", re.I),
        re.compile(r"φ"),
        re.compile(r"\b1\.618\d*\b"),
    ),
    "sqrt2": (
        re.compile(r"sqrt\s*\(?\s*2", re.I),
        re.compile(r"√\s*2"),
        re.compile(r"square\s+root\s+of\s+2", re.I),
        re.compile(r"\b1\.414\d*\b"),
    ),
    "flower_of_life": (
        re.compile(r"flower\s+of\s+life", re.I),
        re.compile(r"vesica\s+piscis", re.I),
    ),
    "corkscrew": (
        re.compile(r"corkscrew", re.I),
    ),
    "abad": (
        re.compile(r"\babad\b", re.I),
        re.compile(r"a\s*[-–—]\s*b\s*[-–—]\s*a\s*[-–—]\s*d", re.I),
        re.compile(r"\ba\s*-\s*b\s*-\s*a\s*-\s*d\b", re.I),
    ),
}

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "in",
        "of",
        "for",
        "and",
        "or",
        "to",
        "all",
        "with",
        "from",
        "that",
        "this",
        "require",
        "required",
        "requiring",
        "rule",
        "rules",
        "add",
        "adding",
        "future",
        "submissions",
        "submission",
        "should",
        "must",
        "will",
        "into",
        "active",
        "harden",
        "hardening",
        "suggested",
        "coverage",
        "explicit",
        "check",
        "counter",
        "argument",
        "least",
        "token",
        "tokens",
        "engage",
        "engages",
    }
)


def score_engagement(
    text: str,
    extra_keywords: Sequence[str] | None = None,
) -> dict:
    """Return ``{"score": float, "hits": list[str]}`` for *text*.

    ``hits`` lists family names (and ``merged_rule:<keyword>`` tags).
    Extra keywords are a simple add from merged rules — not a learned model.
    """
    if not text:
        return {"score": 0.0, "hits": []}

    hits: list[str] = []
    score = 0.0
    for family, patterns in _PATTERNS.items():
        if any(p.search(text) for p in patterns):
            hits.append(family)
            score += float(WEIGHTS[family])

    for kw in _normalize_extras(extra_keywords or ()):
        if kw and kw.lower() in text.lower():
            tag = f"merged_rule:{kw}"
            if tag not in hits:
                hits.append(tag)
                score += float(WEIGHTS["merged_rule"])

    return {"score": round(score, 4), "hits": hits}


def extract_keywords(hardening: str) -> list[str]:
    """Pull distinctive tokens out of a merged hardening string."""
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", hardening or "")
    out: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        low = tok.lower()
        if low in STOPWORDS or low in seen:
            continue
        if len(low) < 5:
            continue
        seen.add(low)
        out.append(low)
    return out


def _normalize_extras(extra: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for kw in extra:
        if not kw:
            continue
        low = str(kw).strip().lower()
        if not low or low in seen or low in STOPWORDS:
            continue
        seen.add(low)
        out.append(low)
    return out
