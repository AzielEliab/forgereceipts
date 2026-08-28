"""Local data directory. Never uploaded. Gitignored as .forgereceipts."""

from __future__ import annotations

import os
from pathlib import Path

DATA_DIR_NAME = ".forgereceipts"


def data_dir(root: str | Path | None = None) -> Path:
    """Resolve the local data directory.

    Order: explicit root, FORGERECEIPTS_DIR, then ``./.forgereceipts``.
    """
    if root is not None:
        path = Path(root)
    else:
        env = os.environ.get("FORGERECEIPTS_DIR")
        path = Path(env) if env else Path.cwd() / DATA_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path
