"""Shared constants for the GodLock core.

Bind default is localhost. MirageGrid/Airlock are logical identities
only — not a real network, not Tor, not a proxy chain.
"""

from __future__ import annotations

DEFAULT_BIND_HOST = "127.0.0.1"
DEFAULT_BIND_PORT = 8080

GRID_SIZE = 25
NODE_PREFIX = "grid"
# Short session-identity rotation. Entropy-driven, in-process only.
DEFAULT_ROTATE_INTERVAL_S = 0.05

JEEVES_MODEL = "godlock-jeeves-heuristic-0.1"

MOTTO = "GodLock does not argue. It records, analyzes, hardens, and grows."

AUTHOR = "Aziel Eliab"
PAPER_DATE = "12 July 2026"
LICENSE_ID = "Apache-2.0"

DATA_DIR_NAME = ".godlock"
LUMEN_KEY_FILENAME = "lumen.key"
RECEIPTS_FILENAME = "receipts.jsonl"
RULES_FILENAME = "rules.json"
ANALYSES_FILENAME = "analyses.json"
CAPSULE_INDEX_FILENAME = "capsule_index.json"
