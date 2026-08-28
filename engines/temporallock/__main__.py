"""Allow ``python -m temporallock`` to invoke the CLI."""

from temporallock.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
