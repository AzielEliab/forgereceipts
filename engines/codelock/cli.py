"""Command-line interface for CodeLock.

    codelock gate-status
    codelock open-gate --ack "This tool alters perception, not meaning."
    codelock render --in FILE --mode normalize|codelock --out FILE.html [--seed N] [--hue/--no-hue] [--ack "..."]
    codelock export --in FILE --kind normal|codelock --out FILE [--seed N] [--ack "..."]
    codelock version

The gate is per-invocation. Pass ``--ack`` or set env ``CODELOCK_ACK`` to
the exact acknowledgment phrase. Default is Closed. Normalize and
export-normal never need an ack.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from codelock import __version__
from codelock.gate import ACK_PHRASE, AcknowledgmentError, Gate, GateClosedError
from codelock.session import CodeLockSession


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codelock",
        description=(
            "CodeLock — gate-tethered cognitive rendering of source text "
            "(Aziel Eliab, July 2026). This tool alters perception, not "
            "meaning. It is not encryption."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("gate-status", help="Print gate: open|closed for this invocation.")

    p_open = sub.add_parser(
        "open-gate",
        help="Validate the acknowledgment phrase (per-invocation; not persisted).",
    )
    p_open.add_argument(
        "--ack",
        required=True,
        help=f"Exact phrase required: {ACK_PHRASE!r}",
    )

    p_render = sub.add_parser("render", help="Write Normalize or CodeLock HTML.")
    p_render.add_argument("--in", dest="inp", required=True, help="Input source file.")
    p_render.add_argument(
        "--mode",
        required=True,
        choices=("normalize", "codelock"),
        help="normalize is always available; codelock requires an open gate.",
    )
    p_render.add_argument("--out", dest="out", required=True, help="Output HTML path.")
    p_render.add_argument("--seed", default="0", help="Deterministic seed (default 0).")
    p_render.add_argument(
        "--hue",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Hue spectrum on tokens (default: on). --no-hue disables color.",
    )
    p_render.add_argument(
        "--ack",
        default=None,
        help=f"Exact phrase to open the gate: {ACK_PHRASE!r}",
    )

    p_export = sub.add_parser(
        "export",
        help="Export Normal (.txt, canonical) or CodeLock (.html, non-canonical).",
    )
    p_export.add_argument("--in", dest="inp", required=True, help="Input source file.")
    p_export.add_argument(
        "--kind",
        required=True,
        choices=("normal", "codelock"),
        help="normal is always available; codelock requires an open gate.",
    )
    p_export.add_argument("--out", dest="out", required=True, help="Output path.")
    p_export.add_argument("--seed", default="0", help="Deterministic seed (default 0).")
    p_export.add_argument(
        "--hue",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Hue spectrum (CodeLock kind only).",
    )
    p_export.add_argument(
        "--ack",
        default=None,
        help=f"Exact phrase to open the gate: {ACK_PHRASE!r}",
    )

    sub.add_parser("version", help="Print the CodeLock version and exit.")
    return parser


def _ack_from_env() -> str | None:
    val = os.environ.get("CODELOCK_ACK")
    if val is None or val == "":
        return None
    return val


def _open_from_invocation(ack: str | None) -> Gate:
    """Open the gate if --ack or CODELOCK_ACK matches the exact phrase.

    A provided-but-wrong acknowledgment is an error (the user tried to
    open the gate and failed), not a silent Closed state.
    """
    gate = Gate()
    candidate = ack if ack is not None else _ack_from_env()
    if candidate is None:
        return gate
    gate.open(candidate)
    return gate


def _read_source(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"error: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"error: failed to read {path}: {exc}") from exc


def _session(source: str, args: argparse.Namespace) -> CodeLockSession:
    seed = getattr(args, "seed", "0")
    hue = bool(getattr(args, "hue", True))
    ack = getattr(args, "ack", None)
    gate = _open_from_invocation(ack)
    return CodeLockSession(source, seed=seed, hue=hue, gate=gate)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "version":
        sys.stdout.write(f"codelock {__version__}\n")
        return 0

    if args.cmd == "gate-status":
        try:
            gate = _open_from_invocation(_ack_from_env())
        except AcknowledgmentError as exc:
            sys.stderr.write(f"error: {exc}\n")
            sys.stdout.write("gate: closed\n")
            return 2
        state = "open" if gate.gate_open else "closed"
        sys.stdout.write(f"gate: {state}\n")
        return 0

    if args.cmd == "open-gate":
        try:
            gate = Gate()
            gate.open(args.ack)
        except AcknowledgmentError as exc:
            sys.stderr.write(f"error: {exc}\n")
            sys.stdout.write("gate: closed\n")
            return 2
        sys.stdout.write("gate: open\n")
        return 0

    try:
        if args.cmd == "render":
            source = _read_source(args.inp)
            session = _session(source, args)
            if args.mode == "normalize":
                html = session.normalize_html()
            else:
                html = session.codelock_html()
            dest = Path(args.out)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8", newline="\n")
            sys.stdout.write(f"mode={args.mode} out={dest}\n")
            return 0

        if args.cmd == "export":
            source = _read_source(args.inp)
            session = _session(source, args)
            dest = Path(args.out)
            if args.kind == "normal":
                session.export_normal(dest)
            else:
                session.export_codelock(dest)
            sys.stdout.write(f"kind={args.kind} out={dest}\n")
            return 0
    except AcknowledgmentError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    except GateClosedError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2

    parser.error(f"unknown command {args.cmd!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
