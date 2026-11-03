"""Loopback HTTP server for the bundled web assets.

Serves only files under the web directory, plus a dynamic /settings.js that carries the
saved settings into the page *synchronously* (before the editor script runs). It listens on
127.0.0.1 only and rejects unexpected Host headers (DNS-rebinding protection). File access
for the editor goes through the pywebview bridge, not through this server.
"""

import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import __version__

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/x-icon", ".ico")

INDEX = "hgrtool.html"


def settings_js(values: dict, debug: bool) -> bytes:
    # json.dumps output is valid JS; escape "</" so it can never be read as an HTML end tag.
    payload = json.dumps(values).replace("</", "<\\/")
    text = (
        f"window.__hgrInitialSettings = {payload};\n"
        f"window.__hgrDesktopVersion = {json.dumps(__version__)};\n"
        f"window.__hgrDebug = {'true' if debug else 'false'};\n"
    )
    return text.encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    server_version = "HGRToolServer"
    protocol_version = "HTTP/1.0"

    def log_message(self, fmt, *args):  # keep quiet
        pass

    def _send(self, code: int, body: bytes = b"", ctype: str = "text/plain") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _host_ok(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b"forbidden")
        path = unquote(urlparse(self.path).path)
        if path == "/settings.js":
            body = settings_js(self.server.settings.as_dict(), self.server.debug)
            return self._send(200, body, "text/javascript; charset=utf-8")
        if path in ("", "/"):
            path = "/" + INDEX
        root: Path = self.server.root
        try:
            target = (root / path.lstrip("/")).resolve()
            target.relative_to(root)
        except (ValueError, OSError):
            return self._send(404, b"not found")
        if not target.is_file():
            return self._send(404, b"not found")
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype == "application/javascript":
            ctype += "; charset=utf-8"
        self._send(200, target.read_bytes(), ctype)

    def do_POST(self):
        # Read (and discard) a small request body first, so the client never sees a reset.
        try:
            remaining = min(int(self.headers.get("Content-Length", "0")), 1 << 20)
        except ValueError:
            remaining = 0
        while remaining > 0:
            chunk = self.rfile.read(min(remaining, 65536))
            if not chunk:
                break
            remaining -= len(chunk)
        self._send(405, b"method not allowed")

    do_PUT = do_DELETE = do_PATCH = do_POST


class WebServer:
    def __init__(self, root: Path, settings, debug: bool = False):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.httpd.root = Path(root).resolve()
        self.httpd.settings = settings
        self.httpd.debug = debug
        self.httpd.daemon_threads = True
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return self.httpd.server_address[1]

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/{INDEX}"

    def start(self) -> "WebServer":
        self._thread.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
