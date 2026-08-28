"""Allow ``python -m codelock`` to invoke the CLI."""

from codelock.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
