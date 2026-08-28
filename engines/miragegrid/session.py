"""MirageSession lifecycle: initiate → assign → operate → end.

End destroys the in-process session-to-node mapping (forget, not a
log wipe). After close, ``session.node`` raises MappingDestroyedError
and the internal node reference is None.

This handle never opens sockets, never hops IPs, never speaks Tor,
and never builds a proxy or tunnel. The assigned node is a logical
identity from the static pool of 25.
"""

from __future__ import annotations

import json
import secrets
from typing import Any

from miragegrid.errors import MappingDestroyedError
from miragegrid.pool import Node, NodePool
from miragegrid.receipt import Receipt, evaluate_integrity, utc_now
from miragegrid.rng import fresh_entropy, select_index


class MirageSession:
    """One phone-booth session: a single assigned logical node.

    Constructing a session (or entering the context manager) runs
    initiate: cryptographic selection from the 25-node pool, mint of
    an internal receipt. ``end()`` / context exit drops the mapping.
    """

    def __init__(
        self,
        pool: NodePool | None = None,
        *,
        entropy: bytes | None = None,
        timestamp: str | None = None,
        session_id: str | None = None,
        assign: bool = True,
    ) -> None:
        self.pool = pool if pool is not None else NodePool()
        self.session_id = session_id if session_id is not None else secrets.token_hex(16)
        self._closed = False
        self._node: Node | None = None
        self._receipt: Receipt | None = None
        self._timestamp: str | None = timestamp
        self._entropy: bytes | None = entropy
        if assign:
            self.initiate(entropy=entropy, timestamp=timestamp)

    def initiate(
        self,
        entropy: bytes | None = None,
        timestamp: str | None = None,
    ) -> Node:
        """Assign a node from the pool. Idempotent while the session is open."""
        if self._closed:
            raise MappingDestroyedError(
                "session mapping destroyed; start a new MirageSession"
            )
        if self._node is not None:
            return self._node
        ts = timestamp if timestamp is not None else self._timestamp
        if ts is None:
            ts = utc_now()
        self._timestamp = ts
        ent = entropy if entropy is not None else self._entropy
        if ent is None:
            ent = fresh_entropy()
        self._entropy = ent
        index = select_index(ent, ts)
        node = self.pool.by_index(index)
        self._node = node
        self._receipt = Receipt.mint(
            session_id=self.session_id,
            node=node,
            timestamp=ts,
            pool=self.pool,
            closed=False,
        )
        return node

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def node(self) -> Node:
        if self._closed:
            raise MappingDestroyedError(
                "session mapping destroyed; start a new MirageSession"
            )
        if self._node is None:
            raise MappingDestroyedError("no node assigned")
        return self._node

    @property
    def receipt(self) -> Receipt:
        """Internal receipt. Not included in default dump / str / JSON."""
        if self._receipt is None:
            raise MappingDestroyedError("no receipt; session was never initiated")
        return self._receipt

    @property
    def integrity(self) -> str:
        """Live integrity: PASS iff a pool node is mapped and not closed."""
        node_id = None if self._node is None else self._node.id
        return evaluate_integrity(node_id, self.pool, self._closed)

    def emit_receipt(self) -> dict[str, Any]:
        """Operator-requested receipt dict (for ``--emit-receipt`` / UI)."""
        return self.receipt.to_dict()

    def to_dict(self, *, include_receipt: bool = False) -> dict[str, Any]:
        """Public session dump. Receipt omitted unless ``include_receipt``."""
        payload: dict[str, Any] = {
            "session_id": self.session_id,
            "closed": self._closed,
        }
        if self._closed:
            payload["node_id"] = None
        elif self._node is not None:
            payload["node_id"] = self._node.id
            payload["node_label"] = self._node.label
        if include_receipt and self._receipt is not None:
            payload["receipt"] = self._receipt.to_dict()
        return payload

    def to_json(self, *, include_receipt: bool = False) -> str:
        return json.dumps(self.to_dict(include_receipt=include_receipt), indent=2)

    def __str__(self) -> str:
        if self._closed:
            return f"MirageSession(session_id={self.session_id}, closed=True, node=None)"
        nid = None if self._node is None else self._node.id
        return f"MirageSession(session_id={self.session_id}, node={nid})"

    def __repr__(self) -> str:
        return str(self)

    def end(self) -> None:
        """Destroy the session-to-node mapping. In-process forget, not a wipe.

        The frozen receipt snapshot remains so an operator who already
        asked to emit it can still write the JSON they requested. The
        mapping itself is dropped: ``_node`` is None and ``node`` raises.
        """
        self._node = None
        self._closed = True

    def close(self) -> None:
        self.end()

    def __enter__(self) -> "MirageSession":
        if self._node is None and not self._closed:
            self.initiate()
        return self

    def __exit__(self, *exc: object) -> bool:
        self.end()
        return False
