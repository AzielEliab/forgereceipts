"""Allow ``python -m staticclock`` to invoke the CLI."""

from staticclock.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
