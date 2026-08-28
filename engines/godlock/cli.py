"""Command-line interface for GodLock.

    godlock serve --host 127.0.0.1 --port 8080
    godlock submit --text "..." [--out receipt.json]
    godlock score --text "..."
    godlock merge --receipt ID --hardening "..."
    godlock rules
    godlock stats
    godlock export-lumen --receipt ID --out FILE.capsule
    godlock version

submit / stats / score work fully offline with ``./.godlock`` (gitignored).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from godlock import __version__
from godlock.config import DATA_DIR_NAME, DEFAULT_BIND_HOST, DEFAULT_BIND_PORT, MOTTO
from godlock.engine import GodLockEngine


def _data_dir(args: argparse.Namespace) -> Path:
    if getattr(args, "data_dir", None):
        return Path(args.data_dir)
    return Path.cwd() / DATA_DIR_NAME


def _engine(args: argparse.Namespace) -> GodLockEngine:
    persist = True if getattr(args, "persist", True) else False
    return GodLockEngine(data_dir=_data_dir(args), persist=persist)


def _print_json(obj: object) -> None:
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="godlock",
        description=(
            "GodLock — ABAD stress-test and resilience engine "
            "(Collin Horton / Aziel the Revealer of the Sealed, 12 July 2026). "
            "Core + receipts. Not an anonymity network."
        ),
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help=f"Local data directory (default: ./{DATA_DIR_NAME}).",
    )
    persist = parser.add_mutually_exclusive_group()
    persist.add_argument(
        "--persist",
        dest="persist",
        action="store_true",
        default=True,
        help="Write receipts/rules as jsonl/json under the data dir (default).",
    )
    persist.add_argument(
        "--no-persist",
        dest="persist",
        action="store_false",
        help="In-memory receipts only. Not a wipe: just skip disk.",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_serve = sub.add_parser("serve", help="Run the localhost HTTP UI/API.")
    p_serve.add_argument("--host", default=DEFAULT_BIND_HOST, help="Bind host (default 127.0.0.1).")
    p_serve.add_argument("--port", type=int, default=DEFAULT_BIND_PORT, help="Bind port (default 8080).")

    p_sub = sub.add_parser("submit", help="Record a counter-argument (offline).")
    p_sub.add_argument("--text", required=True, help="Stress-test text.")
    p_sub.add_argument("--out", default=None, help="Optional path to write receipt JSON.")

    p_score = sub.add_parser("score", help="ABAD engagement score for text (offline).")
    p_score.add_argument("--text", required=True)

    p_merge = sub.add_parser("merge", help="Apply a hardening into the active rules table.")
    p_merge.add_argument("--receipt", required=True, help="Receipt id.")
    p_merge.add_argument("--hardening", default="", help="Hardening text (default: Jeeves suggestion).")

    sub.add_parser("rules", help="List active rules.")
    sub.add_parser("stats", help="Public counter and resilience score (offline).")

    p_ex = sub.add_parser("export-lumen", help="Write an encrypted Lumen capsule.")
    p_ex.add_argument("--receipt", required=True)
    p_ex.add_argument("--out", required=True, help="Output .capsule path.")

    sub.add_parser("version", help="Print the GodLock version and exit.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "version":
        sys.stdout.write(f"godlock {__version__}\n")
        sys.stdout.write(MOTTO + "\n")
        return 0

    if args.cmd == "serve":
        # Local import so `godlock version` does not need uvicorn at import-check time.
        import uvicorn

        from godlock.app import create_app

        engine = _engine(args)
        app = create_app(
            engine=engine,
            persist=args.persist,
            data_dir=_data_dir(args),
            bind_host=args.host,
            bind_port=args.port,
        )
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
        return 0

    engine = _engine(args)

    if args.cmd == "submit":
        result = engine.submit(args.text)
        if args.out:
            Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        _print_json(result)
        return 0

    if args.cmd == "score":
        _print_json(engine.score(args.text))
        return 0

    if args.cmd == "merge":
        rule = engine.merge(args.receipt, args.hardening)
        _print_json(rule.as_dict())
        return 0

    if args.cmd == "rules":
        _print_json([r.as_dict() for r in engine.rules.all()])
        return 0

    if args.cmd == "stats":
        _print_json(engine.stats())
        return 0

    if args.cmd == "export-lumen":
        info = engine.export_lumen(args.receipt, args.out)
        _print_json(info)
        return 0

    parser.error(f"unknown command {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
