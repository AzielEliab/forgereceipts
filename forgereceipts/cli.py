"""ForgeReceipts command line.

forgereceipts ui              # 127.0.0.1:8787  THE product
forgereceipts doctor          # local health check
forgereceipts verify-receipt  # check a saved receipt file
forgereceipts version
"""

from __future__ import annotations

import argparse
import sys

from forgereceipts import __version__
from forgereceipts.debug import debug_enabled, debug_log
from forgereceipts.plain import NOT_LEGAL_PROOF, PlainError

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="forgereceipts",
        description=(
            "ForgeReceipts — local-first evidence integrity. "
            "Not legal advice. A receipt is not legal proof. "
            "Local UI: `forgereceipts ui` at http://127.0.0.1:8787. "
            "Binds 127.0.0.1 only. No telemetry."
        ),
    )
    sub = parser.add_subparsers(dest="cmd")

    ui_p = sub.add_parser("ui", help="serve the local product on 127.0.0.1:8787")
    ui_p.add_argument("--host", default="127.0.0.1")
    ui_p.add_argument("--port", type=int, default=8787)
    ui_p.add_argument("--data-dir", default=None, help="override ./.forgereceipts")

    doc_p = sub.add_parser("doctor", help="check that this computer can save receipts")
    doc_p.add_argument("--data-dir", default=None, help="override ./.forgereceipts")
    doc_p.add_argument("--json", action="store_true", help="print JSON instead of plain text")

    ver_p = sub.add_parser("verify-receipt", help="check that a receipt file still matches its hash")
    ver_p.add_argument("path", help="path to a .json or .jsonl receipt file")

    sub.add_parser("version", help="print version")

    args = parser.parse_args(argv)
    debug_log(f"cli cmd={args.cmd} debug={debug_enabled()}")

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

    if args.cmd == "doctor":
        from forgereceipts.doctor import format_doctor, run_doctor
        import json as json_lib

        report = run_doctor(args.data_dir)
        if args.json:
            print(json_lib.dumps(report, indent=2, ensure_ascii=False))
        else:
            sys.stdout.write(format_doctor(report))
        return 0 if report.get("ok") else 1

    if args.cmd == "verify-receipt":
        from forgereceipts.exchange import verify_path
        import json as json_lib

        try:
            result = verify_path(args.path)
        except PlainError as exc:
            print(str(exc), file=sys.stderr)
            print(NOT_LEGAL_PROOF, file=sys.stderr)
            return 2
        except OSError:
            print("Could not read that file.", file=sys.stderr)
            return 2
        print(result.get("verdict") or "FAIL")
        print(result.get("plain") or "")
        if result.get("hash"):
            print(f"hash: {result['hash']}")
        if debug_enabled():
            print(json_lib.dumps(result, indent=2, ensure_ascii=False))
        print(result.get("disclaimer") or NOT_LEGAL_PROOF)
        return 0 if result.get("ok") else 1

    parser.print_help()
    print("\nNot legal advice. A receipt is not legal proof. Child's Best Interests First.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
