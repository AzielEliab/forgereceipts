"""ForgeReceipts command line.

Human text is the default. Pass --json on doctor and verify-receipt for machines.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from forgereceipts import __version__
from forgereceipts.debug import debug_enabled, debug_log
from forgereceipts.plain import NOT_LEGAL_PROOF, PlainError

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

HELP_TEXT = f"""\
forgereceipts — save a receipt for a file or note on this computer

usage:
  forgereceipts                         what to run next
  forgereceipts ui                      open the local app
  forgereceipts doctor                  check this computer
  forgereceipts verify-receipt <file>   check a saved receipt
  forgereceipts version                 print {__version__}
  forgereceipts help                    show this help

Open http://127.0.0.1:8787 after `forgereceipts ui`.
Listens on this computer only (127.0.0.1). Author: Aziel Eliab.

commands:
  ui                open the local app
  doctor            pass or fail lines for this computer
  verify-receipt    check a .json or .jsonl receipt file
  version           print the version

advanced:
  ui --port 8787
  ui --data-dir PATH
  doctor --json
  doctor --data-dir PATH
  verify-receipt FILE --json

examples:
  forgereceipts ui
  forgereceipts doctor
  forgereceipts verify-receipt receipt.json
  forgereceipts doctor --json
"""

WELCOME_TEXT = """\
ForgeReceipts saves a receipt for a file or a note on this computer.

Next, open the app:
  forgereceipts ui

Then open http://127.0.0.1:8787 and choose Add file.

Also:
  forgereceipts doctor
  forgereceipts --help

Author: Aziel Eliab
"""


class HumanParser(argparse.ArgumentParser):
    """Git-style top-level help, and plain errors with a next step."""

    def __init__(self, *args, primary: bool = False, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.primary = primary

    def format_help(self) -> str:
        if self.primary:
            return HELP_TEXT
        return super().format_help()

    def error(self, message: str) -> None:
        low = message.lower()
        if "invalid choice" in low:
            match = re.search(r"invalid choice: '([^']*)'", message)
            bad = match.group(1) if match else ""
            text = f'Unknown command "{bad}". Try: forgereceipts ui   or   forgereceipts --help\n'
        elif "unrecognized arguments" in low:
            text = "That option is not recognized. Try: forgereceipts --help\n"
        elif "required" in low and "path" in low:
            text = "A receipt file is required. Try: forgereceipts verify-receipt receipt.json\n"
        elif "required" in low:
            text = "More information is required. Try: forgereceipts --help\n"
        else:
            text = f"{message}. Try: forgereceipts --help\n"
        self.exit(2, text)


def _build_parser() -> HumanParser:
    parser = HumanParser(
        prog="forgereceipts",
        primary=True,
        description="Save a receipt for a file or note on this computer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd")

    ui_p = sub.add_parser(
        "ui",
        help="open the local app",
        description="Open the local app on this computer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Prints one line: Open http://127.0.0.1:<port>/",
    )
    ui_p.add_argument("--host", default="127.0.0.1", help="loopback address (127.0.0.1)")
    ui_p.add_argument("--port", type=int, default=8787, help="port (default 8787)")
    ui_p.add_argument("--data-dir", default=None, help="folder for receipts (default ./.forgereceipts)")

    doc_p = sub.add_parser(
        "doctor",
        help="check this computer",
        description="Check that this computer can save receipts.",
    )
    doc_p.add_argument("--data-dir", default=None, help="folder for receipts (default ./.forgereceipts)")
    doc_p.add_argument("--json", action="store_true", help="print JSON for machines")

    ver_p = sub.add_parser(
        "verify-receipt",
        help="check a saved receipt file",
        description="Check that a receipt file still matches its hash.",
    )
    ver_p.add_argument("path", help="path to a .json or .jsonl receipt file")
    ver_p.add_argument("--json", action="store_true", help="print JSON for machines")

    sub.add_parser("version", help="print the version")
    sub.add_parser("help", help="show help")
    return parser


def _print_verify_human(result: dict) -> None:
    print(result.get("verdict") or "FAIL")
    print(result.get("plain") or "")
    if result.get("hash"):
        print(f"hash: {result['hash']}")
    if debug_enabled():
        print(json.dumps(result, indent=2, ensure_ascii=False))
    print(result.get("disclaimer") or NOT_LEGAL_PROOF)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) == 0:
        print(WELCOME_TEXT, end="" if WELCOME_TEXT.endswith("\n") else "\n")
        return 0

    args = parser.parse_args(argv)
    debug_log(f"cli cmd={args.cmd} debug={debug_enabled()}")

    if args.cmd in {None, "help"}:
        parser.print_help()
        return 0

    if args.cmd == "version":
        print(__version__)
        return 0

    if args.cmd == "ui":
        host = args.host
        if host not in LOCAL_HOSTS:
            print(
                "ForgeReceipts only opens on this computer (127.0.0.1). "
                f"Refusing host={host!r}.",
                file=sys.stderr,
            )
            print("Try: forgereceipts ui", file=sys.stderr)
            return 2
        from forgereceipts.ui import serve

        serve(host=host, port=args.port, data_dir=args.data_dir)
        return 0

    if args.cmd == "doctor":
        from forgereceipts.doctor import format_doctor, run_doctor

        report = run_doctor(args.data_dir)
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            sys.stdout.write(format_doctor(report))
        return 0 if report.get("ok") else 1

    if args.cmd == "verify-receipt":
        from forgereceipts.exchange import verify_path

        try:
            result = verify_path(args.path)
        except PlainError as exc:
            if args.json:
                print(json.dumps({"ok": False, "error": str(exc), "plain": True}, ensure_ascii=False))
            else:
                print(str(exc), file=sys.stderr)
                print("Try: forgereceipts verify-receipt receipt.json", file=sys.stderr)
                print(NOT_LEGAL_PROOF, file=sys.stderr)
            return 2
        except OSError:
            if args.json:
                print(
                    json.dumps(
                        {"ok": False, "error": "Could not read that file.", "plain": True},
                        ensure_ascii=False,
                    )
                )
            else:
                print("Could not read that file. Check the path and try again.", file=sys.stderr)
                print("Try: forgereceipts verify-receipt receipt.json", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            _print_verify_human(result)
        return 0 if result.get("ok") else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
