"""Local StaticClock UI. Bind 127.0.0.1 only.

Last-known-geo input, Top-30 dropdown, five output fields, read-only
timezone panel. Self-contained CSS. No CDN. No memory of past advisories.
Each /api/advise is one moment, then forget.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import urlparse

from staticclock.anchors import TOP_30
from staticclock.engine import OUTPUT_FIELDS, StaticClock
from staticclock.zones import list_timezones

LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})
WEB = files("staticclock") / "web"
MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


def _web_bytes(name: str) -> bytes:
    return (WEB / name).read_bytes()


class Handler(BaseHTTPRequestHandler):
    server_version = "StaticClock/0.1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, obj: object) -> None:
        body = json.dumps(obj, indent=2, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send(200, _web_bytes("index.html"), MIME[".html"])
            return
        if path == "/style.css":
            self._send(200, _web_bytes("style.css"), MIME[".css"])
            return
        if path == "/app.js":
            self._send(200, _web_bytes("app.js"), MIME[".js"])
            return
        if path == "/api/anchors":
            self._json(200, list(TOP_30))
            return
        if path == "/api/zones":
            self._json(200, list_timezones())
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/advise":
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "JSON body required"})
            return
        geo = ""
        if isinstance(payload, dict):
            geo = str(payload.get("geo") or payload.get("anchor") or "")
        clock = StaticClock()
        try:
            advisory = clock.advise(geo)
            data = advisory.to_dict()
        finally:
            clock.forget()
        # Five fields only. Do not retain the advisory on the server.
        self._json(200, {k: data[k] for k in OUTPUT_FIELDS})


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    if host not in LOOPBACK:
        raise ValueError("StaticClock UI binds loopback only (127.0.0.1)")
    return ThreadingHTTPServer((host, port), Handler)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = make_server(host, port)
    bound_host, bound_port = httpd.server_address[:2]
    print(f"StaticClock UI http://{bound_host}:{bound_port} (loopback only; no memory of advisories)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
