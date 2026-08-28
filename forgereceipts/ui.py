"""Local-only ForgeReceipts UI. Binds 127.0.0.1. No CDN, no telemetry."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from forgereceipts import __version__
from forgereceipts.filing import render_html, render_txt, templates as filing_templates
from forgereceipts.forensics import reverify_bytes, reverify_path, sha256_bytes, sha256_path
from forgereceipts.legal import NOT_LEGAL_ADVICE, reference as legal_reference
from forgereceipts.lock import SessionLock
from forgereceipts.paths import data_dir as resolve_data_dir
from forgereceipts.score import pattern_strength
from forgereceipts.store import ForgeStore, verify_jsonl
from forgereceipts.tools import availability as tools_availability, run as tools_run

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY = 12 * 1024 * 1024

_STATE = threading.local()


def _app_state(data_dir: Path) -> dict[str, Any]:
    # Process-wide singleton keyed by data_dir string.
    cache = getattr(_app_state, "_cache", None)
    if cache is None:
        cache = {}
        setattr(_app_state, "_cache", cache)
    key = str(data_dir.resolve())
    if key not in cache:
        cache[key] = {
            "dir": data_dir,
            "store": ForgeStore(data_dir),
            "lock": SessionLock(data_dir),
        }
    return cache[key]


def reset_state() -> None:
    setattr(_app_state, "_cache", {})


class ForgeHandler(BaseHTTPRequestHandler):
    server_version = "ForgeReceipts/0.1.0"

    @property
    def data_dir(self) -> Path:
        return Path(getattr(self.server, "forge_data_dir"))  # type: ignore[arg-type]

    def log_message(self, fmt: str, *args: object) -> None:
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("127.0.0.1 local %s\n" % (fmt % args))

    def _state(self) -> dict[str, Any]:
        return _app_state(self.data_dir)

    def _send(self, status: int, body: bytes, content_type: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-ForgeReceipts", "local-only")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: Any, status: int = 200) -> None:
        raw = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
        self._send(status, raw, "application/json; charset=utf-8")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length > MAX_BODY:
            raise ValueError("body too large")
        raw = self.rfile.read(length) if length else b"{}"
        if not raw:
            return {}
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON object required")
        return data

    def _spa(self) -> None:
        index = STATIC_DIR / "index.html"
        body = index.read_bytes()
        self._send(200, body, "text/html; charset=utf-8")

    def _static(self, name: str) -> None:
        # Prevent path traversal.
        dest = (STATIC_DIR / name).resolve()
        if STATIC_DIR.resolve() not in dest.parents and dest != STATIC_DIR.resolve():
            self._json({"error": "not found"}, 404)
            return
        if not dest.is_file():
            self._json({"error": "not found"}, 404)
            return
        ctype = mimetypes.guess_type(str(dest))[0] or "application/octet-stream"
        if dest.suffix == ".webmanifest":
            ctype = "application/manifest+json"
        if dest.suffix in {".js", ".css", ".html", ".webmanifest", ".json"}:
            ctype = {
                ".js": "application/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".html": "text/html; charset=utf-8",
                ".webmanifest": "application/manifest+json",
                ".json": "application/json; charset=utf-8",
            }[dest.suffix]
        self._send(200, dest.read_bytes(), ctype)

    def _locked_out(self) -> bool:
        lock: SessionLock = self._state()["lock"]
        return lock.is_set() and not lock.unlocked

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, b"", "text/plain")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/health":
            self._json({"ok": True, "bind": "127.0.0.1", "version": __version__})
            return
        if path in {"/", "/index.html"}:
            self._spa()
            return
        if path == "/manifest.webmanifest":
            self._static("manifest.webmanifest")
            return
        if path.startswith("/static/"):
            self._static(path[len("/static/") :])
            return
        # SPA routes — never 500 a tools/nav page.
        if path in {
            "/home",
            "/incident",
            "/forensics",
            "/journal",
            "/filing",
            "/tools",
            "/verify",
            "/lock",
        }:
            self._spa()
            return

        if path.startswith("/api/"):
            if path not in {"/api/lock", "/api/meta"} and self._locked_out():
                self._json({"error": "locked", "unlocked": False}, 401)
                return
            try:
                self._api_get(path, qs)
            except Exception as exc:  # noqa: BLE001
                self._json({"error": str(exc)}, 400)
            return

        self._spa()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if not path.startswith("/api/"):
            self._json({"error": "not found"}, 404)
            return
        if path not in {"/api/lock/unlock", "/api/lock/set"} and self._locked_out():
            self._json({"error": "locked", "unlocked": False}, 401)
            return
        try:
            body = self._read_json()
            self._api_post(path, body)
        except Exception as exc:  # noqa: BLE001
            self._json({"error": str(exc)}, 400)

    def _api_get(self, path: str, qs: dict[str, list[str]]) -> None:
        state = self._state()
        store: ForgeStore = state["store"]
        store.reload()
        lock: SessionLock = state["lock"]

        if path == "/api/meta":
            self._json(
                {
                    "name": "ForgeReceipts",
                    "version": __version__,
                    "motto": "Child's Best Interests First. Integrity Over Narrative. Local Control. Always.",
                    "disclaimer": NOT_LEGAL_ADVICE,
                    "bind": "127.0.0.1",
                    "local_only": True,
                    "telemetry": False,
                    "accounts": False,
                    "not_legal_advice": True,
                    "download": "https://forgereceipts-download-tracker.vibelock.workers.dev/",
                    "one_counter": True,
                    "lock": lock.status(),
                    "tools": tools_availability(),
                }
            )
            return
        if path == "/api/lock":
            self._json(lock.status())
            return
        if path == "/api/receipts":
            kind = (qs.get("kind") or [None])[0]
            rows = store.records_of(kind) if kind else store.records()
            self._json({"receipts": rows, "length": len(store), "verify": _verify_dict(store)})
            return
        if path == "/api/score":
            self._json(pattern_strength(store.records()))
            return
        if path == "/api/legal":
            jid = (qs.get("jurisdiction") or ["IN"])[0]
            self._json(legal_reference(jid))
            return
        if path == "/api/filing":
            self._json(filing_templates())
            return
        if path == "/api/tools":
            self._json({"available": tools_availability(), "panels": list(tools_availability())})
            return
        if path == "/api/chain.jsonl":
            p = store.path
            text = p.read_text(encoding="utf-8") if p.is_file() else ""
            self._send(200, text.encode("utf-8"), "application/x-ndjson; charset=utf-8")
            return
        self._json({"error": "not found"}, 404)

    def _api_post(self, path: str, body: dict[str, Any]) -> None:
        state = self._state()
        store: ForgeStore = state["store"]
        store.reload()
        lock: SessionLock = state["lock"]

        if path == "/api/lock/set":
            lock.set_passphrase(str(body.get("passphrase") or ""))
            self._json(lock.status())
            return
        if path == "/api/lock/unlock":
            ok = lock.unlock(str(body.get("passphrase") or ""))
            self._json({**lock.status(), "ok": ok}, 200 if ok else 401)
            return
        if path == "/api/lock/clear":
            lock.clear(str(body.get("passphrase") or ""))
            self._json(lock.status())
            return
        if path == "/api/incident":
            row = store.append_incident(
                summary=str(body.get("summary") or ""),
                evidence=str(body.get("evidence") or ""),
                child_impact=str(body.get("child_impact") or ""),
                confidence=float(body.get("confidence") if body.get("confidence") is not None else 1.0),
                timestamp=body.get("timestamp"),
                file_sha256=body.get("file_sha256"),
                file_name=body.get("file_name"),
            )
            self._json({"receipt": row, "verify": _verify_dict(store)})
            return
        if path == "/api/journal":
            row = store.append_journal(
                summary=str(body.get("summary") or ""),
                evidence=str(body.get("evidence") or ""),
                child_impact=str(body.get("child_impact") or ""),
                confidence=float(body.get("confidence") if body.get("confidence") is not None else 1.0),
                timestamp=body.get("timestamp"),
                file_sha256=body.get("file_sha256"),
                file_name=body.get("file_name"),
                private_note=body.get("private_note"),
            )
            self._json({"receipt": row, "verify": _verify_dict(store)})
            return
        if path == "/api/forensics/hash":
            digest, name = _hash_from_body(body)
            impact = str(body.get("child_impact") or "Hash of a local file retained for later re-verification.")
            row = store.append_forensics(
                summary=str(body.get("summary") or f"SHA-256 {name}"),
                file_sha256=digest,
                file_name=name,
                child_impact=impact,
            )
            self._json({"sha256": digest, "file_name": name, "receipt": row})
            return
        if path == "/api/forensics/verify":
            expected = str(body.get("expected") or body.get("file_sha256") or "")
            if body.get("content_b64"):
                data = base64.b64decode(body["content_b64"])
                result = reverify_bytes(data, expected)
            elif body.get("path"):
                result = reverify_path(body["path"], expected)
            else:
                raise ValueError("content_b64 or path required")
            self._json(result)
            return
        if path == "/api/verify":
            text = str(body.get("jsonl") or "")
            if not text and store.path.is_file():
                text = store.path.read_text(encoding="utf-8")
            self._json(verify_jsonl(text))
            return
        if path == "/api/filing/export":
            fmt = str(body.get("format") or "txt").lower()
            content = render_html(body) if fmt == "html" else render_txt(body)
            export_dir = self.data_dir / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            ext = "html" if fmt == "html" else "txt"
            dest = export_dir / f"filing-export.{ext}"
            dest.write_text(content, encoding="utf-8")
            self._json({"path": str(dest), "format": ext, "content": content, "disclaimer": NOT_LEGAL_ADVICE})
            return
        if path.startswith("/api/tools/"):
            name = path.rsplit("/", 1)[-1]
            self._json(tools_run(name, body))
            return
        self._json({"error": "not found"}, 404)


def _hash_from_body(body: dict[str, Any]) -> tuple[str, str]:
    if body.get("content_b64"):
        data = base64.b64decode(body["content_b64"])
        name = str(body.get("file_name") or "upload.bin")
        return sha256_bytes(data), name
    if body.get("path"):
        path = str(body["path"])
        return sha256_path(path), os.path.basename(path)
    raise ValueError("content_b64 or path required")


def _verify_dict(store: ForgeStore) -> dict[str, Any]:
    result = store.verify()
    return {
        "ok": result.ok,
        "verdict": "PASS" if result.ok else "FAIL",
        "length": result.length,
        "errors": list(result.errors),
        "first_hash": result.first_hash,
        "last_hash": result.last_hash,
    }


def make_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    data_dir: str | Path | None = None,
) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("ForgeReceipts binds 127.0.0.1 only")
    directory = resolve_data_dir(data_dir)
    httpd = ThreadingHTTPServer((host, port), ForgeHandler)
    httpd.forge_data_dir = directory  # type: ignore[attr-defined]
    return httpd


def serve(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    data_dir: str | Path | None = None,
) -> None:
    httpd = make_server(host, port, data_dir)
    bound_host, bound_port = httpd.server_address[:2]
    print(
        f"ForgeReceipts {__version__}  http://{bound_host}:{bound_port}/  "
        "(local only, not legal advice)"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
