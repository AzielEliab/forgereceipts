"""Rosetta Render: deterministic per-token view-layer styles.

Styles are derived from ``hashlib.sha256(seed, token_index, token)``.
They never mutate the source. Normalize HTML applies a fixed monospace
face and zero transforms. CodeLock HTML applies size, optional hue,
micro-rotation, and spacing variance.

This module does not encrypt, obfuscate, or hide text.
"""

from __future__ import annotations

import hashlib
import html
from typing import Mapping, Sequence, TypedDict

from codelock.gate import ACK_PHRASE
from codelock.tokenize import tokenize

FONT_SIZE_MIN_PX = 11
FONT_SIZE_MAX_PX = 22
ROTATE_DEG = 4.0
SPACING_EM = 0.08
NORMALIZE_FONT_PX = 14
MONOSPACE = (
    "ui-monospace, SFMono-Regular, Menlo, Consolas, "
    '"Liberation Mono", monospace'
)


class TokenStyle(TypedDict):
    font_size_px: int
    hue_deg: int | None
    rotate_deg: float
    letter_spacing_em: float
    word_spacing_em: float


def _digest(seed: str | int, index: int, token: str) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(str(seed).encode("utf-8"))
    hasher.update(b"\0")
    hasher.update(str(index).encode("ascii"))
    hasher.update(b"\0")
    hasher.update(token.encode("utf-8"))
    return hasher.digest()


def _map_signed(byte: int, amplitude: float) -> float:
    return round((byte / 255.0) * 2.0 * amplitude - amplitude, 6)


def style_for(
    seed: str | int,
    index: int,
    token: str,
    *,
    hue: bool = True,
) -> TokenStyle:
    digest = _digest(seed, index, token)
    span = FONT_SIZE_MAX_PX - FONT_SIZE_MIN_PX + 1  # 12 values, 11–22
    font_size_px = FONT_SIZE_MIN_PX + (digest[0] % span)
    hue_deg: int | None = None
    if hue:
        hue_deg = int.from_bytes(digest[4:6], "big") % 360
    return TokenStyle(
        font_size_px=font_size_px,
        hue_deg=hue_deg,
        rotate_deg=_map_signed(digest[1], ROTATE_DEG),
        letter_spacing_em=_map_signed(digest[2], SPACING_EM),
        word_spacing_em=_map_signed(digest[3], SPACING_EM),
    )


def styles_for(
    tokens: Sequence[str],
    seed: str | int = 0,
    *,
    hue: bool = True,
) -> list[TokenStyle]:
    """Per-token style dicts. Deterministic for (tokens, seed, hue)."""
    return [style_for(seed, i, tok, hue=hue) for i, tok in enumerate(tokens)]


def _css_escape_comment(text: str) -> str:
    return text.replace("*/", "* /")


def _script_plain_source(source: str) -> str:
    """Embed source in a ``<script type="text/plain">`` without breakout.

    HTML script data ends at a case-insensitive ``</script``. We only
    rewrite that closer; every other character is stored verbatim so the
    artifact remains inspectable with standard tools. A matching
    ``<textarea>`` holds an HTML-escaped copy as a second inspectable
    channel (entities decode to the original in the DOM).
    """
    return source.replace("</", "<\\/")


def normalize_html(source: str) -> str:
    """Canonical viewing state: fixed-size monospace, zero transforms."""
    escaped = html.escape(source)
    return f"""<!DOCTYPE html>
<html lang="en" data-canonical="true">
<head>
<meta charset="utf-8">
<title>CodeLock Normalize (canonical)</title>
<style>
  html, body {{
    margin: 0;
    background: #111;
    color: #ddd;
  }}
  .banner {{
    font-family: {MONOSPACE};
    font-size: 13px;
    padding: 0.75rem 1rem;
    background: #1e3a2f;
    color: #cfe;
    border-bottom: 1px solid #3a6;
  }}
  pre.canonical {{
    font-family: {MONOSPACE};
    font-size: {NORMALIZE_FONT_PX}px;
    line-height: 1.45;
    letter-spacing: 0;
    word-spacing: normal;
    transform: none;
    white-space: pre;
    margin: 1rem;
    tab-size: 4;
  }}
</style>
</head>
<body>
<div class="banner">Canonical view (Normalize). Fixed-size monospace. Zero transforms. Source is the single source of truth.</div>
<pre class="canonical" data-canonical="true">{escaped}</pre>
</body>
</html>
"""


def _token_span(token: str, style: Mapping[str, object]) -> str:
    escaped = html.escape(token)
    if token.isspace():
        return escaped
    rules = [
        f"font-size:{int(style['font_size_px'])}px",
        f"transform:rotate({style['rotate_deg']}deg)",
        f"letter-spacing:{style['letter_spacing_em']}em",
        f"word-spacing:{style['word_spacing_em']}em",
        "display:inline-block",
        f"font-family:{MONOSPACE}",
        "transform-origin:50% 50%",
    ]
    hue = style.get("hue_deg")
    if hue is not None:
        rules.append(f"color:hsl({int(hue)},70%,55%)")
    return f'<span class="tok" style="{";".join(rules)}">{escaped}</span>'


def codelock_html(
    source: str,
    seed: str | int = 0,
    *,
    hue: bool = True,
) -> str:
    """Non-canonical Rosetta Render HTML artifact. Does not encrypt.

    The original source is stored inspectably in
    ``<script type="text/plain" id="codelock-source">`` and in a
    ``<textarea id="codelock-source-text">``. The document is marked
    ``data-canonical="false"`` with a visible banner and an HTML comment.
    """
    tokens = tokenize(source)
    styles = styles_for(tokens, seed, hue=hue)
    spans = "".join(_token_span(tok, st) for tok, st in zip(tokens, styles))
    embedded = _script_plain_source(source)
    escaped = html.escape(source)
    seed_s = html.escape(str(seed))
    ack = html.escape(ACK_PHRASE)
    return f"""<!DOCTYPE html>
<html lang="en" data-canonical="false">
<head>
<meta charset="utf-8">
<title>CodeLock visual artifact (non-canonical)</title>
<!--
  NON-CANONICAL visual artifact. This is not the source of truth.
  Canonical source is plain text in #codelock-source.
  { _css_escape_comment(ACK_PHRASE) }
  CodeLock does not encrypt, hide, or obfuscate. Seed={seed_s}
-->
<style>
  html, body {{
    margin: 0;
    background: #0b0b0f;
    color: #eee;
  }}
  .banner {{
    font-family: {MONOSPACE};
    font-size: 13px;
    padding: 0.85rem 1rem;
    background: #4a1c1c;
    color: #f8d0d0;
    border-bottom: 2px solid #c44;
  }}
  .banner strong {{ letter-spacing: 0.04em; }}
  pre.rosetta {{
    font-family: {MONOSPACE};
    font-size: {NORMALIZE_FONT_PX}px;
    line-height: 1.7;
    white-space: pre-wrap;
    margin: 1rem;
    tab-size: 4;
  }}
  span.tok {{
    display: inline-block;
    vertical-align: baseline;
  }}
  .inspect {{
    font-family: {MONOSPACE};
    margin: 1rem;
    padding: 0.75rem;
    border: 1px dashed #666;
    background: #161616;
  }}
  .inspect h2 {{
    font-size: 14px;
    margin: 0 0 0.5rem 0;
  }}
  textarea#codelock-source-text {{
    width: 100%;
    min-height: 8rem;
    font-family: {MONOSPACE};
    font-size: 13px;
    background: #000;
    color: #cfc;
    border: 1px solid #333;
    white-space: pre;
  }}
</style>
</head>
<body>
<div class="banner" data-canonical="false">
  <strong>NON-CANONICAL</strong> visual artifact &mdash; not a substitute for source.
  {ack}
</div>
<pre class="rosetta" data-canonical="false" data-seed="{seed_s}">{spans}</pre>
<section class="inspect">
  <h2>Canonical source (inspectable, not encrypted)</h2>
  <p>This tool alters perception, not meaning. Plain text below is the single source of truth.</p>
  <textarea id="codelock-source-text" readonly>{escaped}</textarea>
</section>
<script type="text/plain" id="codelock-source">{embedded}</script>
</body>
</html>
"""
