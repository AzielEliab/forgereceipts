"""Active rules table. Admin merge applies a Jeeves hardening.

Merge is corkscrew growth: the table only grows. Rules are not deleted
by this API. Keywords extracted from the hardening feed back into
ABAD scoring as extra hits (simple keyword add).
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from godlock.abad import extract_keywords


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class Rule:
    id: str
    receipt_id: str
    hardening: str
    keywords: tuple[str, ...]
    created_at: str

    def as_dict(self) -> dict:
        d = asdict(self)
        d["keywords"] = list(self.keywords)
        return d


class RulesTable:
    def __init__(self, data_dir: Path | None = None, persist: bool = True) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else None
        self.persist = bool(persist)
        self._lock = threading.Lock()
        self._rules: list[Rule] = []
        if self.persist and self.data_dir is not None:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self._load()

    @property
    def path(self) -> Path | None:
        if self.data_dir is None:
            return None
        return self.data_dir / "rules.json"

    def _load(self) -> None:
        path = self.path
        if path is None or not path.is_file():
            return
        raw = json.loads(path.read_text(encoding="utf-8"))
        for item in raw:
            self._rules.append(
                Rule(
                    id=item["id"],
                    receipt_id=item["receipt_id"],
                    hardening=item["hardening"],
                    keywords=tuple(item.get("keywords") or ()),
                    created_at=item["created_at"],
                )
            )

    def _dump(self) -> None:
        if not self.persist or self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [r.as_dict() for r in self._rules]
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def merge(self, receipt_id: str, hardening: str) -> Rule:
        if not (hardening or "").strip():
            raise ValueError("hardening text is required")
        keywords = tuple(extract_keywords(hardening))
        rule = Rule(
            id=str(uuid.uuid4()),
            receipt_id=receipt_id,
            hardening=hardening.strip(),
            keywords=keywords,
            created_at=_utc_now(),
        )
        with self._lock:
            self._rules.append(rule)
            self._dump()
        return rule

    def all(self) -> list[Rule]:
        return list(self._rules)

    def extra_keywords(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for rule in self._rules:
            for kw in rule.keywords:
                low = kw.lower()
                if low not in seen:
                    seen.add(low)
                    out.append(low)
        return out

    def __len__(self) -> int:
        return len(self._rules)
