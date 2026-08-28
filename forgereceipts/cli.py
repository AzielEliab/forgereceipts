"""ForgeReceipts command line.

forgereceipts ui       # 127.0.0.1:8787  THE product
forgereceipts version
"""

from __future__ import annotations

import argparse
import sys

from forgereceipts import __version__

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="forgereceipts",
        description=(
            "ForgeReceipts — local-first evidence integrity. "
            "Not legal advice. Binds 127.0.0.1 only."
        ),
    )
    sub = parser.add_subparsers(dest="cmd")

    ui_p = sub.add_parser("ui", help="serve the local product on 127.0.0.1:8787")
    ui_p.add_argument("--host", default="127.0.0.1")
    ui_p.add_argument("--port", type=int, default=8787)
    ui_p.add_argument("--data-dir", default=None, help="override ./.forgereceipts")

    sub.add_parser("version", help="print version")

    args = parser.parse_args(argv)
    if args.cmd == "version":
        print(__version__)
        return 0
    if args.cmd == "ui":
        host = args.host
        if host not in LOCAL_HOSTS:
            print(
                "ForgeReceipts binds local-only (127.0.0.1). Refusing host="
                f"{host!r}.",
                file=sys.stderr,
            )
            return 2
        from forgereceipts.ui import serve

        serve(host=host, port=args.port, data_dir=args.data_dir)
        return 0
    parser.print_help()
    print("\nNot legal advice. Child's Best Interests First.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
