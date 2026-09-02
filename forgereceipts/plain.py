"""Plain-English errors. Safe to show a 6th grader. No stack traces."""

from __future__ import annotations

import json
from typing import Any

from forgereceipts.limits import MAX_BODY_MIB, MAX_JSON_CHARS

JSON_ERROR = (
    "That file is not valid JSON. Check commas and quotes, then try again."
)
TOO_BIG = (
    f"That file is too big. ForgeReceipts only takes files up to {MAX_BODY_MIB} MB."
)
NOT_OBJECT = (
    "That JSON is not a receipt object. It must be a set of named fields inside { }."
)
NOT_TEXT = "That file is not text. Use a .json receipt file."
MISSING_RECEIPT = (
    "No receipt was found in that file. Export a receipt and try again."
)
NOT_LEGAL_PROOF = (
    "Not legal advice. A receipt is not legal proof."
)


class PlainError(ValueError):
    """User-facing error. Message is the whole story unless DEBUG is on."""


def decode_text(raw: bytes) -> str:
    if not raw:
        return ""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PlainError(NOT_TEXT) from exc


def loads_json(text: str) -> Any:
    """json.loads with a size cap and a plain error. Extra-data is re-raised."""
    if len(text) > MAX_JSON_CHARS:
        raise PlainError(TOO_BIG)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        if "extra data" in str(exc).lower():
            raise
        raise PlainError(JSON_ERROR) from exc


def parse_json_bytes(raw: bytes) -> dict[str, Any]:
    """HTTP JSON body: a single object, or {} if empty."""
    if not raw:
        return {}
    text = decode_text(raw)
    if not text.strip():
        return {}
    try:
        data = loads_json(text)
    except json.JSONDecodeError as exc:
        raise PlainError(JSON_ERROR) from exc
    if not isinstance(data, dict):
        raise PlainError(NOT_OBJECT)
    return data
