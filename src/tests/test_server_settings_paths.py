import http.client
import json
import os
import stat
import sys

import pytest

from hgrtool import paths
from hgrtool.server import WebServer
from hgrtool.settings import Settings


@pytest.fixture
def server(tmp_path):
    root = tmp_path / "web"
    root.mkdir()
    (root / "hgrtool.html").write_text("<html>hi</html>")
    (root / "shim.js").write_text("// js")
    (root / "font.woff2").write_bytes(b"\x00\x01")
    (tmp_path / "secret.txt").write_text("secret")
    settings = Settings(tmp_path / "s.json")
    settings.update({"clipXferMode": "merge"})
    srv = WebServer(root, settings).start()
    yield srv
    srv.stop()


def get(srv, path, host=None):
    c = http.client.HTTPConnection("127.0.0.1", srv.port, timeout=5)
    c.putrequest("GET", path, skip_host=True)
    c.putheader("Host", host or f"127.0.0.1:{srv.port}")
    c.endheaders()
    r = c.getresponse()
    return r.status, r.getheader("Content-Type"), r.read()


def test_serves_index_and_assets(server):
    assert get(server, "/")[0] == 200
    s, ctype, body = get(server, "/shim.js")
    assert s == 200 and "javascript" in ctype
    assert get(server, "/font.woff2")[1] == "font/woff2"


def test_traversal_and_missing(server):
    for p in ("/../secret.txt", "/..%2fsecret.txt", "/%2e%2e/secret.txt", "/nope.js"):
        assert get(server, p)[0] == 404, p


def test_bad_host_header_rejected(server):
    assert get(server, "/", host="evil.example.com")[0] == 403


def test_settings_js_carries_saved_values(server):
    s, ctype, body = get(server, "/settings.js")
    text = body.decode()
    assert s == 200 and '"clipXferMode": "merge"' in text and "__hgrDesktopVersion" in text


def test_post_not_allowed(server):
    c = http.client.HTTPConnection("127.0.0.1", server.port, timeout=5)
    c.request("POST", "/settings.js", body=b"x")
    assert c.getresponse().status == 405


def test_settings_persist_and_survive_corruption(tmp_path):
    p = tmp_path / "s.json"
    s = Settings(p)
    s.update({"clipXferMode": "xor", "bogus": "1"})
    assert Settings(p).as_dict() == {"clipXferMode": "xor"}
    p.write_text("{ not json")
    assert Settings(p).as_dict() == {}


def test_data_dir_override(tmp_path, monkeypatch):
    monkeypatch.setenv("HGRTOOL_DATA", str(tmp_path / "d"))
    assert paths.data_dir() == tmp_path / "d" and (tmp_path / "d").is_dir()


def test_data_dir_falls_back_when_portable_dir_unwritable(tmp_path, monkeypatch):
    monkeypatch.delenv("HGRTOOL_DATA", raising=False)
    monkeypatch.setattr(paths, "exe_dir", lambda: tmp_path / "ro")
    monkeypatch.setattr(paths, "_is_writable_dir", lambda p: False)
    monkeypatch.setattr(paths, "_user_config_dir", lambda: tmp_path / "cfg")
    assert paths.data_dir() == tmp_path / "cfg"


def test_data_dir_portable_when_writable(tmp_path, monkeypatch):
    monkeypatch.delenv("HGRTOOL_DATA", raising=False)
    monkeypatch.setattr(paths, "exe_dir", lambda: tmp_path)
    assert paths.data_dir() == tmp_path / paths.DATA_DIR_NAME
