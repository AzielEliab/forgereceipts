"""Internal session receipt (whitepaper section 3.4).

Default: receipts live in memory and are not written to a public API.
The operator may emit a local JSON file with ``--emit-receipt``.

Fields: session_id (hex), mirage_node (1–25), timestamp UTC ISO,
integrity PASS/FAIL, plus an optional canonical SHA-256 (AZE/DIF-E
flavor, no temporallock dependency).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from miragegrid.canon import digest
from miragegrid.errors import ReceiptError
from miragegrid.pool import Node, NodePool, POOL_SIZE, node_id_for


def utc_now() -> str:
    """UTC ISO-8601 with trailing Z, second precision (paper example)."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def evaluate_integrity(
    node_id: str | None,
    pool: NodePool,
    closed: bool,
) -> str:
    """PASS if the node id is in the pool and the session is not closed."""
    if closed or node_id is None:
        return "FAIL"
    if not pool.contains(node_id):
        return "FAIL"
    return "PASS"


def integrity_for_number(mirage_node: int, pool: NodePool) -> str:
    """PASS iff ``mirage_node`` is 1–25 and that node exists in the pool."""
    if not isinstance(mirage_node, int) or not pool.contains_number(mirage_node):
        return "FAIL"
    try:
        node = pool.by_number(mirage_node)
    except IndexError:
        return "FAIL"
    if not pool.contains(node.id):
        return "FAIL"
    return "PASS"


@dataclass(frozen=True)
class Receipt:
    """Frozen internal receipt. Not part of default session dump/str."""

    session_id: str
    mirage_node: int
    timestamp: str
    integrity: str
    hash: str

    @classmethod
    def mint(
        cls,
        *,
        session_id: str,
        node: Node,
        timestamp: str,
        pool: NodePool,
        closed: bool = False,
    ) -> "Receipt":
        integrity = evaluate_integrity(node.id, pool, closed)
        rec_hash = digest(
            session_id=session_id,
            mirage_node=node.number,
            timestamp=timestamp,
            integrity=integrity,
        )
        return cls(
            session_id=session_id,
            mirage_node=node.number,
            timestamp=timestamp,
            integrity=integrity,
            hash=rec_hash,
        )

    def recomputed_hash(self) -> str:
        return digest(
            session_id=self.session_id,
            mirage_node=self.mirage_node,
            timestamp=self.timestamp,
            integrity=self.integrity,
        )

    def hash_ok(self) -> bool:
        return self.recomputed_hash() == self.hash

    def evaluate(self, pool: NodePool) -> str:
        """Recompute integrity against a pool. Forged node ids FAIL.

        Hash mismatch also FAIL. Stored ``integrity`` of FAIL stays FAIL.
        """
        if not self.hash_ok():
            return "FAIL"
        live = integrity_for_number(self.mirage_node, pool)
        if live == "FAIL":
            return "FAIL"
        if self.integrity != "PASS":
            return "FAIL"
        return "PASS"

    def verify(self, pool: NodePool) -> str:
        return self.evaluate(pool)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mirage_node": self.mirage_node,
            "timestamp": self.timestamp,
            "integrity": self.integrity,
            "hash": self.hash,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def write_json(self, path: str | Path) -> None:
        Path(path).write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Receipt":
        required = ("session_id", "mirage_node", "timestamp", "integrity")
        missing = [k for k in required if k not in data]
        if missing:
            raise ReceiptError(f"receipt missing fields: {missing}")
        try:
            mirage_node = int(data["mirage_node"])
        except (TypeError, ValueError) as exc:
            raise ReceiptError("mirage_node must be an integer 1–25") from exc
        integrity = str(data["integrity"])
        session_id = str(data["session_id"])
        timestamp = str(data["timestamp"])
        stored_hash = data.get("hash")
        if stored_hash is None:
            stored_hash = digest(session_id, mirage_node, timestamp, integrity)
        return cls(
            session_id=session_id,
            mirage_node=mirage_node,
            timestamp=timestamp,
            integrity=integrity,
            hash=str(stored_hash),
        )

    @classmethod
    def load(cls, path: str | Path) -> "Receipt":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ReceiptError("receipt file must be a JSON object")
        return cls.from_dict(raw)


def node_id_from_number(mirage_node: int) -> str:
    if mirage_node < 1 or mirage_node > POOL_SIZE:
        return f"node-{mirage_node:02d}"
    return node_id_for(mirage_node - 1)
