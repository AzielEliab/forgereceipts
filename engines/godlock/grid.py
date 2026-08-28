"""MirageGrid + Airlock as *logical* identities.

This module never opens sockets, never hops IPs, never talks to Tor, and
never builds a proxy chain. ``node_id`` is a string like ``grid-07``.

MirageGrid: 25 named logical nodes. Session identity rotates on a short
interval, driven by process entropy (``secrets``). Pure in-process.

Airlock: a request is accepted on one logical ingress node, processed
internally, and the response is attributed to a *different* logical
egress node. No sockets dropped. No real IPs. Ingress is never equal to
egress.

Public traffic in the July 12 2026 paper would sit *behind* an existing
ops layer. This repo models that layer as names, not a ghost network.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from godlock.config import DEFAULT_ROTATE_INTERVAL_S, GRID_SIZE, NODE_PREFIX

NODES: tuple[str, ...] = tuple(
    f"{NODE_PREFIX}-{i:02d}" for i in range(1, GRID_SIZE + 1)
)


class MirageGrid:
    """25-node in-process identity roster with entropy-driven rotation."""

    def __init__(
        self,
        rotate_interval_s: float = DEFAULT_ROTATE_INTERVAL_S,
        rng: secrets.SystemRandom | None = None,
    ) -> None:
        if len(NODES) != GRID_SIZE:
            raise RuntimeError("MirageGrid must expose exactly 25 logical nodes")
        self.nodes: tuple[str, ...] = NODES
        self.rotate_interval_s = float(rotate_interval_s)
        self._rng = rng or secrets.SystemRandom()
        self._index = self._rng.randrange(GRID_SIZE)
        self._last_rotate = time.monotonic()
        self._rotations = 0

    @property
    def size(self) -> int:
        return len(self.nodes)

    @property
    def rotations(self) -> int:
        return self._rotations

    def current_node(self) -> str:
        self._maybe_rotate()
        return self.nodes[self._index]

    def _maybe_rotate(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_rotate
        if elapsed < self.rotate_interval_s and self._rotations > 0:
            return
        # Interval 0 (or first observation after construct) always rotates
        # onto a *different* node so tests can see motion without sleeping.
        if self._rotations == 0 and elapsed < self.rotate_interval_s and self.rotate_interval_s > 0:
            # First call: keep the seeded identity, mark the clock.
            self._last_rotate = now
            self._rotations = 1
            return
        self._rotate_now(now)

    def force_rotate(self) -> str:
        self._rotate_now(time.monotonic())
        return self.nodes[self._index]

    def _rotate_now(self, now: float) -> None:
        new = self._rng.randrange(GRID_SIZE)
        if new == self._index:
            new = (new + 1) % GRID_SIZE
        self._index = new
        self._last_rotate = now
        self._rotations += 1


@dataclass(frozen=True)
class AirlockPair:
    ingress_node: str
    egress_node: str


class Airlock:
    """Logical ingress/egress split. No sockets. No dropped connections."""

    def __init__(self, grid: MirageGrid | None = None) -> None:
        self.grid = grid or MirageGrid()

    def open(self) -> AirlockPair:
        ingress = self.grid.current_node()
        # Internal processing is a no-op; attribution uses a different node.
        egress = self.grid.current_node()
        if egress == ingress:
            others = [n for n in self.grid.nodes if n != ingress]
            egress = others[self.grid._rng.randrange(len(others))]
        return AirlockPair(ingress_node=ingress, egress_node=egress)
