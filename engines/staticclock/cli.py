"""Command-line interface for StaticClock.

    staticclock version
    staticclock anchors
    staticclock advise --geo "United States"
    staticclock advise --geo "Indiana"
    staticclock advise --geo "United States" --json
    staticclock zones
    staticclock ui
    staticclock serve

Advisory only. Five fields. No reasoning dump. Forks always allowed.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from staticclock import __version__
from staticclock.anchors import TOP_30
from staticclock.engine import OUTPUT_FIELDS, StaticClock
from staticclock.zones import list_timezones


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="staticclock",
        description=(
            "StaticClock — chrono-linguistic release advisory "
            "(Aziel Eliab, 2026). Advisory hygiene, not strategy. "
            "It does not help messages travel farther. It helps them arrive intact."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="Print package version.")
    sub.add_parser("anchors", help="List the Top-30 geographic anchors.")

    p_adv = sub.add_parser(
        "advise",
        help="Emit one advisory for a last-known geo (five fields only).",
    )
    p_adv.add_argument(
        "--geo",
        required=True,
        help="Last-known geo (free text) or a Top-30 country name.",
    )
    p_adv.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print the five fields as JSON. No scores, no because.",
    )

    sub.add_parser(
        "zones",
        help="Read-only IANA zones with computed current local times.",
    )

    p_ui = sub.add_parser(
        "ui",
        help="Serve the local advisory UI on 127.0.0.1 (no memory of past advisories).",
    )
    p_ui.add_argument("--host", default="127.0.0.1", help="Loopback host (default 127.0.0.1).")
    p_ui.add_argument("--port", type=int, default=8765, help="Port (default 8765).")

    p_serve = sub.add_parser(
        "serve",
        help="Alias for ui. Bind 127.0.0.1 only.",
    )
    p_serve.add_argument("--host", default="127.0.0.1", help="Loopback host (default 127.0.0.1).")
    p_serve.add_argument("--port", type=int, default=8765, help="Port (default 8765).")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "version":
        print(f"staticclock {__version__}")
        return 0

    if args.cmd == "anchors":
        for name in TOP_30:
            print(name)
        return 0

    if args.cmd == "advise":
        clock = StaticClock()
        try:
            advisory = clock.advise(args.geo)
        finally:
            clock.forget()
        payload = advisory.to_dict()
        if args.as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            for key in OUTPUT_FIELDS:
                print(f"{key}: {payload[key]}")
        return 0

    if args.cmd == "zones":
        rows = list_timezones()
        for row in rows:
            print(
                f"{row['region']:16}  {row['iana']:36}  "
                f"{row['local_date']} {row['local_time']}  UTC{row['utc_offset']}"
            )
        return 0

    if args.cmd in {"ui", "serve"}:
        from staticclock.ui import serve

        try:
            serve(host=args.host, port=args.port)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return 0

    parser.error(f"unknown command {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
