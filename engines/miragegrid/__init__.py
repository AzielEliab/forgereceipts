"""MirageGrid: distributed identity abstraction for AZ-OS.

Version 1.0 conceptual architecture, implemented as an open assignment
+ receipt engine by Aziel Eliab (2026).

A static pool of 25 named *logical* nodes. At session init, one is
selected cryptographically as the outward identity. An internal receipt
is minted. The mapping is destroyed when the session ends.

This package is not an anonymity network, VPN, or proxy mesh. Nodes
are identities (`node-01` … `node-25`). Optional endpoint strings are
labels only. Forks are welcome and always allowed.
"""

from __future__ import annotations

from miragegrid.errors import (
    IntegrityError,
    MappingDestroyedError,
    MirageGridError,
    ReceiptError,
)
from miragegrid.pool import Node, NodePool, POOL_SIZE
from miragegrid.receipt import Receipt
from miragegrid.rng import select_index
from miragegrid.session import MirageSession

__version__ = "0.1.0"
__author__ = "Aziel Eliab"
__all__ = [
    "IntegrityError",
    "MappingDestroyedError",
    "MirageGridError",
    "Node",
    "NodePool",
    "POOL_SIZE",
    "Receipt",
    "ReceiptError",
    "MirageSession",
    "select_index",
    "__version__",
]
