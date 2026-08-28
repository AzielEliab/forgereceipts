"""Command-line interface for TemporalLock.

    temporallock version
    temporallock genesis --chain FILE.jsonl --summary "..." --evidence "..."
    temporallock append  --chain FILE.jsonl --summary "..." --evidence "..." [--confidence 0.7] [--timestamp ISO]
    temporallock verify FILE.jsonl
    temporallock show FILE.jsonl

Receipts, not truth claims. Forks always allowed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from temporallock import __version__
from temporallock.chain import Chain
from temporallock.errors import AppendOnlyError, ChainError, ReceiptError, TemporalLockError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="temporallock",
        description=(
            "TemporalLock — append-only observation receipts "
            "(Aziel Eliab, July 2026). Receipts, not truth claims."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="Print package version.")

    p_gen = sub.add_parser("genesis", help="Write the first receipt (prev_hash = 64 zeros).")
    p_gen.add_argument("--chain", required=True, help="JSONL chain path (must not already exist).")
    p_gen.add_argument("--summary", required=True, help="Brief summary of what was observed.")
    p_gen.add_argument("--evidence", required=True, help="Supporting evidence (body and/or URI/path).")
    p_gen.add_argument("--confidence", type=float, default=1.0, help="Observer confidence in [0.0, 1.0] (default 1.0).")
    p_gen.add_argument("--timestamp", default=None, help="UTC ISO-8601 timestamp (default: now).")

    p_app = sub.add_parser("append", help="Append a receipt to an existing chain.")
    p_app.add_argument("--chain", required=True, help="JSONL chain path (must already exist).")
    p_app.add_argument("--summary", required=True, help="Brief summary of what was observed.")
    p_app.add_argument("--evidence", required=True, help="Supporting evidence (body and/or URI/path).")
    p_app.add_argument("--confidence", type=float, default=0.7, help="Observer confidence in [0.0, 1.0] (default 0.7).")
    p_app.add_argument("--timestamp", default=None, help="UTC ISO-8601 timestamp (default: now).")

    p_ver = sub.add_parser("verify", help="Walk the chain; exit 0 if intact, nonzero if broken.")
    p_ver.add_argument("file", help="JSONL chain path.")

    p_show = sub.add_parser("show", help="Print receipts in a chain.")
    p_show.add_argument("file", help="JSONL chain path.")

    return parser


def _print_receipt_brief(receipt, index: int | None = None) -> None:
    prefix = f"[{index}] " if index is not None else ""
    print(f"{prefix}{receipt.timestamp}  conf={receipt.confidence:.6f}  hash={receipt.hash}")
    print(f"    prev={receipt.prev_hash}")
    print(f"    summary: {receipt.summary}")
    print(f"    evidence: {receipt.evidence}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.cmd == "version":
            print(f"temporallock {__version__}")
            return 0

        if args.cmd == "genesis":
            path = Path(args.chain)
            chain = Chain.genesis(
                path,
                summary=args.summary,
                evidence=args.evidence,
                confidence=args.confidence,
                timestamp=args.timestamp,
            )
            rec = chain[-1]
            print(f"genesis {rec.hash}")
            return 0

        if args.cmd == "append":
            path = Path(args.chain)
            if not path.is_file() or path.stat().st_size == 0:
                print("chain does not exist; use genesis for the first receipt", file=sys.stderr)
                return 2
            chain = Chain.load(path)
            rec = chain.append(
                summary=args.summary,
                evidence=args.evidence,
                confidence=args.confidence,
                timestamp=args.timestamp,
                require_existing=True,
            )
            print(f"appended {rec.hash}")
            return 0

        if args.cmd == "verify":
            path = Path(args.file)
            if not path.is_file():
                print(f"not found: {path}", file=sys.stderr)
                return 2
            chain = Chain.load(path)
            result = chain.verify()
            payload = {
                "ok": result.ok,
                "length": result.length,
                "first_hash": result.first_hash,
                "last_hash": result.last_hash,
                "errors": result.errors,
            }
            print(json.dumps(payload, indent=2))
            return 0 if result.ok else 1

        if args.cmd == "show":
            path = Path(args.file)
            if not path.is_file():
                print(f"not found: {path}", file=sys.stderr)
                return 2
            chain = Chain.load(path)
            print(f"temporallock chain  n={len(chain)}  path={path}")
            for i, rec in enumerate(chain):
                _print_receipt_brief(rec, i)
            forks = chain.forks()
            if forks:
                print(f"forks: {len(forks)} (allowed; no winner chosen)")
                for f in forks:
                    print(f"  prev={f.prev_hash}")
                    for h in f.child_hashes:
                        print(f"    child={h}")
            return 0

        parser.error(f"unknown command {args.cmd}")
        return 2
    except (ReceiptError, ChainError, AppendOnlyError, TemporalLockError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
