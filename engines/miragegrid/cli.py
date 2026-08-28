"""Command-line interface for MirageGrid.

    miragegrid version
    miragegrid nodes
    miragegrid assign [--emit-receipt FILE.json]
    miragegrid verify-receipt FILE.json
    miragegrid ui [--host 127.0.0.1] [--port 8080]
    miragegrid serve [--host 127.0.0.1] [--port 8080]

Logical identities only. Not a VPN, proxy, or anonymity network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from miragegrid import __version__
from miragegrid.errors import MappingDestroyedError, ReceiptError
from miragegrid.pool import NodePool
from miragegrid.receipt import Receipt
from miragegrid.session import MirageSession
from miragegrid.ui import DEFAULT_HOST, DEFAULT_PORT, serve


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="miragegrid",
        description=(
            "MirageGrid — distributed identity abstraction for AZ-OS "
            "(Aziel Eliab, 2026). Assignment + receipt engine. "
            "Not an anonymity network, VPN, or proxy mesh."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="Print package version.")
    sub.add_parser("nodes", help="List the 25 logical nodes.")

    p_as = sub.add_parser(
        "assign",
        help="Assign a logical node for one session; print node id and session id.",
    )
    p_as.add_argument(
        "--emit-receipt",
        default=None,
        metavar="FILE.json",
        help="Write the internal receipt JSON the operator asked for.",
    )
    p_as.add_argument(
        "--config",
        default=None,
        help="Optional JSON with endpoint labels (labels only; never connected).",
    )

    p_ver = sub.add_parser("verify-receipt", help="Verify a local receipt JSON file.")
    p_ver.add_argument("file", help="Receipt JSON path.")

    p_ui = sub.add_parser("ui", help="Localhost HTML UI (127.0.0.1 only).")
    p_ui.add_argument("--host", default=DEFAULT_HOST, help="Bind host (default 127.0.0.1).")
    p_ui.add_argument("--port", type=int, default=DEFAULT_PORT, help="Bind port (default 8080).")

    p_serve = sub.add_parser("serve", help="Alias for ui. Localhost only.")
    p_serve.add_argument("--host", default=DEFAULT_HOST, help="Bind host (default 127.0.0.1).")
    p_serve.add_argument("--port", type=int, default=DEFAULT_PORT, help="Bind port (default 8080).")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "version":
        sys.stdout.write(f"miragegrid {__version__}\n")
        return 0

    if args.cmd == "nodes":
        pool = NodePool()
        for node in pool:
            extra = f"  endpoint={node.endpoint}" if node.endpoint else ""
            sys.stdout.write(f"{node.id}  {node.label}{extra}\n")
        return 0

    if args.cmd == "assign":
        pool = NodePool.from_config(args.config) if args.config else NodePool()
        try:
            with MirageSession(pool=pool) as session:
                node = session.node
                sys.stdout.write(f"{node.id}\n")
                sys.stdout.write(f"session_id={session.session_id}\n")
                if args.emit_receipt:
                    session.receipt.write_json(args.emit_receipt)
                    sys.stderr.write(f"wrote receipt {args.emit_receipt}\n")
        except MappingDestroyedError as exc:
            sys.stderr.write(f"miragegrid: {exc}\n")
            return 2
        return 0

    if args.cmd == "verify-receipt":
        path = Path(args.file)
        if not path.is_file():
            sys.stderr.write(f"miragegrid: not found: {path}\n")
            return 2
        try:
            rec = Receipt.load(path)
        except (ReceiptError, OSError, json.JSONDecodeError) as exc:
            sys.stderr.write(f"miragegrid: {exc}\n")
            return 2
        status = rec.verify(NodePool())
        payload = {
            "integrity": status,
            "session_id": rec.session_id,
            "mirage_node": rec.mirage_node,
            "timestamp": rec.timestamp,
            "hash_ok": rec.hash_ok(),
        }
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return 0 if status == "PASS" else 1

    if args.cmd in ("ui", "serve"):
        host = args.host or DEFAULT_HOST
        if host not in ("127.0.0.1", "localhost", "::1"):
            sys.stderr.write("miragegrid: refusing non-loopback bind; using 127.0.0.1\n")
            host = DEFAULT_HOST
        serve(host=host, port=int(args.port))
        return 0

    parser.error(f"unknown command {args.cmd}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
