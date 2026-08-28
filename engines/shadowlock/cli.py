"""Command-line interface for ShadowLock.

    shadowlock version
    shadowlock observe --in jobs.jsonl --format jsonl|csv --out report.json
    shadowlock observe --in jobs.jsonl --stdout

``--out`` writes the anonymous summary JSON only (aggregates, hashed ids).
Input files are opened read-only. Optional ``--airgap`` refuses proxy env vars.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from shadowlock import __version__
from shadowlock.adapters import CsvAdapter, JsonlAdapter
from shadowlock.errors import AirgapError, SessionForgottenError
from shadowlock.session import ShadowLockSession, assert_airgap


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shadowlock",
        description=(
            "ShadowLock — a read-only, zero-retention outcome mirror "
            "(Aziel Eliab, July 2026). Observes; does not control. "
            "Change is optional. Truth is not."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("version", help="Print package version.")

    p_obs = sub.add_parser(
        "observe",
        help="Read a job file, sample 1 in 5, print or write an anonymous report.",
    )
    p_obs.add_argument("--in", dest="inp", required=True, help="Input JSONL or CSV file.")
    p_obs.add_argument(
        "--format",
        choices=("jsonl", "csv"),
        default=None,
        help="Input format (default: infer from extension).",
    )
    p_obs.add_argument(
        "--out",
        dest="out",
        default=None,
        help="Write anonymous summary JSON (aggregates, no raw ids/names).",
    )
    p_obs.add_argument(
        "--stdout",
        action="store_true",
        help="Print the anonymous summary JSON to stdout.",
    )
    p_obs.add_argument(
        "--salt",
        default=None,
        help="Optional session salt (hex/string). Default: random, not retained.",
    )
    p_obs.add_argument(
        "--airgap",
        action="store_true",
        help="Refuse to run if HTTP(S)_PROXY / ALL_PROXY (or lowercase) are set.",
    )
    return parser


def _adapter_for(path: Path, fmt: str | None):
    kind = fmt
    if kind is None:
        suf = path.suffix.lower()
        if suf in {".csv"}:
            kind = "csv"
        else:
            kind = "jsonl"
    if kind == "csv":
        return CsvAdapter(path)
    return JsonlAdapter(path)


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "version":
        sys.stdout.write(f"shadowlock {__version__}\n")
        return 0

    if args.cmd == "observe":
        if args.airgap:
            try:
                assert_airgap()
            except AirgapError as exc:
                sys.stderr.write(f"shadowlock: {exc}\n")
                return 2
        if not args.out and not args.stdout:
            sys.stderr.write("shadowlock: pass --out FILE or --stdout\n")
            return 2
        path = Path(args.inp)
        if not path.is_file():
            sys.stderr.write(f"shadowlock: input not found: {path}\n")
            return 2
        adapter = _adapter_for(path, args.format)
        try:
            with ShadowLockSession(salt=args.salt, airgap=args.airgap) as session:
                report = session.observe(adapter)
                payload = report.to_json()
        except (AirgapError, SessionForgottenError) as exc:
            sys.stderr.write(f"shadowlock: {exc}\n")
            return 2
        if args.stdout:
            sys.stdout.write(payload + "\n")
        if args.out:
            out_path = Path(args.out)
            out_path.write_text(payload + "\n", encoding="utf-8")
        return 0

    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
