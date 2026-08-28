
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from forgereceipts.ui import make_server, reset_state


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture
def store(data_dir: Path):
    from forgereceipts.store import ForgeStore
    return ForgeStore(data_dir)


@pytest.fixture
def httpd(data_dir: Path):
    reset_state()
    server = make_server("127.0.0.1", 0, data_dir=data_dir)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    reset_state()


@pytest.fixture
def base_url(httpd) -> str:
    host, port = httpd.server_address[:2]
    return f"http://{host}:{port}"
