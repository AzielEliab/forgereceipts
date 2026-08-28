"""Immutable stress-test receipts and the public resilience counter.

A receipt is append-only. There is no wipe, no redact-in-place, and no
anti-forensics API. Optional persistence is jsonl (one object per line)
or in-memory. Operators who want a log can keep it; this tool will not
pretend to erase it.

Hash is SHA-256 of the canonical JSON of id, timestamp, ingress_node,
egress_node, and text.
"""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from godlock.grid import Airlock, AirlockPair


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_payload(receipt_id: str, timestamp: str, ingress_node: str, egress_node: str, text: str) -> bytes:
    body = {
        "id": receipt_id,
        "timestamp": timestamp,
        "ingress_node": ingress_node,
        "egress_node": egress_node,
        "text": text,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def receipt_hash(receipt_id: str, timestamp: str, ingress_node: str, egress_node: str, text: str) -> str:
    return hashlib.sha256(canonical_payload(receipt_id, timestamp, ingress_node, egress_node, text)).hexdigest()


@dataclass(frozen=True)
class Receipt:
    id: str
    timestamp: str
    ingress_node: str
    egress_node: str
    text: str
    hash: str

    def as_dict(self) -> dict:
        return asdict(self)

    def verify(self) -> bool:
        expected = receipt_hash(self.id, self.timestamp, self.ingress_node, self.egress_node, self.text)
        return expected == self.hash

    @classmethod
    def mint(cls, text: str, pair: AirlockPair, receipt_id: str | None = None, timestamp: str | None = None) -> "Receipt":
        rid = receipt_id or str(uuid.uuid4())
        ts = timestamp or _utc_now()
        digest = receipt_hash(rid, ts, pair.ingress_node, pair.egress_node, text)
        return cls(
            id=rid,
            timestamp=ts,
            ingress_node=pair.ingress_node,
            egress_node=pair.egress_node,
            text=text,
            hash=digest,
        )


class ImmutableReceiptError(Exception):
    """Raised when a caller tries to overwrite or mutate a stored receipt."""


class ReceiptStore:
    """Append-only receipt log plus a public integer counter.

    ``persist=False`` keeps everything in memory.
    ``persist=True`` appends JSON lines under ``data_dir``. There is no
    method that truncates or shreds the log.
    """

    def __init__(self, data_dir: Path | None = None, persist: bool = True) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else None
        self.persist = bool(persist)
        self._lock = threading.Lock()
        self._by_id: dict[str, Receipt] = {}
        self._order: list[str] = []
        self._counter = 0
        if self.persist and self.data_dir is not None:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self._load()

    @property
    def path(self) -> Path | None:
        if self.data_dir is None:
            return None
        return self.data_dir / "receipts.jsonl"

    @property
    def counter(self) -> int:
        return self._counter

    def __len__(self) -> int:
        return len(self._order)

    def _load(self) -> None:
        path = self.path
        if path is None or not path.is_file():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            rec = Receipt(
                id=raw["id"],
                timestamp=raw["timestamp"],
                ingress_node=raw["ingress_node"],
                egress_node=raw["egress_node"],
                text=raw["text"],
                hash=raw["hash"],
            )
            if rec.id in self._by_id:
                continue
            self._by_id[rec.id] = rec
            self._order.append(rec.id)
        self._counter = len(self._order)

    def append(self, receipt: Receipt) -> Receipt:
        if not isinstance(receipt, Receipt):
            raise TypeError("only Receipt instances may be stored")
        if not receipt.verify():
            raise ImmutableReceiptError("receipt hash does not match canonical payload")
        with self._lock:
            existing = self._by_id.get(receipt.id)
            if existing is not None:
                if existing != receipt:
                    raise ImmutableReceiptError(f"receipt {receipt.id} already exists and cannot be replaced")
                return existing
            self._by_id[receipt.id] = receipt
            self._order.append(receipt.id)
            self._counter += 1
            if self.persist and self.path is not None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(receipt.as_dict(), ensure_ascii=False) + "\n")
        return receipt

    def get(self, receipt_id: str) -> Receipt:
        try:
            return self._by_id[receipt_id]
        except KeyError as exc:
            raise KeyError(f"unknown receipt {receipt_id}") from exc

    def recent(self, n: int = 20) -> list[Receipt]:
        ids = self._order[-n:]
        return [self._by_id[i] for i in reversed(ids)]

    def all(self) -> list[Receipt]:
        return [self._by_id[i] for i in self._order]

    def __iter__(self) -> Iterator[Receipt]:
        return iter(self.all())


def mint_receipt(text: str, airlock: Airlock) -> Receipt:
    pair = airlock.open()
    return Receipt.mint(text, pair)
