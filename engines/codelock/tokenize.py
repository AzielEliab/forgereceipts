"""Split source into tokens. Whitespace is preserved.

``"".join(tokenize(source)) == source`` for any string, including empty
input, unicode, and mixed whitespace.

Language-agnostic-ish: a regex tokenizer that recognizes identifiers,
keywords (Python keyword set as a convenience), punctuation, whitespace,
comments (#, //, /* */), and strings. Unknown characters become
punctuation so the join roundtrip never drops bytes.
"""

from __future__ import annotations

import re
from typing import NamedTuple

# Python keywords used only to label identifier tokens. The tokenizer
# still treats them as ordinary source text; labels do not change the
# joined string.
KEYWORDS = frozenset(
    {
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    }
)

# Triple-quoted strings before single-quoted; comments before punctuation.
_PATTERN = re.compile(
    r"(?P<comment>\#[^\n]*|//[^\n]*|/\*.*?\*/)"
    r"|(?P<string>"
    r"(?:[rRuUbBfF]{1,3})?"
    r"(?:'''(?:\\.|[^\\])*?'''|\"\"\"(?:\\.|[^\\])*?\"\"\""
    r"|'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")"
    r")"
    r"|(?P<whitespace>\s+)"
    r"|(?P<identifier>[^\W\d]\w*)"
    r"|(?P<number>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    r"|(?P<punctuation>.)",
    re.DOTALL,
)


class Token(NamedTuple):
    kind: str
    text: str

    def __str__(self) -> str:
        return self.text


def tokenize_kinds(source: str) -> list[Token]:
    """Return (kind, text) tokens covering every character of ``source``."""
    if source == "":
        return []
    out: list[Token] = []
    pos = 0
    for match in _PATTERN.finditer(source):
        if match.start() > pos:
            out.append(Token("punctuation", source[pos : match.start()]))
        kind = match.lastgroup or "punctuation"
        text = match.group()
        if kind == "identifier" and text in KEYWORDS:
            kind = "keyword"
        out.append(Token(kind, text))
        pos = match.end()
    if pos < len(source):
        out.append(Token("punctuation", source[pos:]))
    return out


def tokenize(source: str) -> list[str]:
    """Return token strings. ``"".join(tokenize(source)) == source``."""
    return [tok.text for tok in tokenize_kinds(source)]
