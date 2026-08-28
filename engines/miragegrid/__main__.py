"""Allow ``python -m miragegrid`` to invoke the CLI."""

from miragegrid.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
