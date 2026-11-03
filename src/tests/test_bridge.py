import base64
import json
import os
import sys
import types

import pytest

from hgrtool.bridge import Api
from hgrtool.settings import Settings


@pytest.fixture
def api(tmp_path):
    return Api(Settings(tmp_path / "settings.json"))


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def test_write_requires_approved_path(api, tmp_path):
    target = tmp_path / "a.hgr"
    r = api.write_file(str(target), b64(b"x" * 8192))
    assert r["ok"] is False and not target.exists()


def test_write_roundtrip_is_byte_identical(api, tmp_path):
    original = os.urandom(8192)
    target = tmp_path / "pic.hgr"
    target.write_bytes(original)
    info = api._read(str(target))
    assert base64.b64decode(info["data"]) == original and info["name"] == "pic.hgr"
    assert api.write_file(info["path"], info["data"]) == {"ok": True}
    assert target.read_bytes() == original
    assert not [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]


def test_write_overwrites_and_shrinks(api, tmp_path):
    target = tmp_path / "pic.hgr"
    target.write_bytes(b"\xff" * 20000)
    api._allow(str(target))
    assert api.write_file(str(target), b64(b"\x01\x02"))["ok"]
    assert target.read_bytes() == b"\x01\x02"


def test_write_rejects_bad_base64_and_non_strings(api, tmp_path):
    target = tmp_path / "pic.hgr"
    api._allow(str(target))
    assert api.write_file(str(target), "***not base64***")["ok"] is False
    assert api.write_file(None, "AA==")["ok"] is False
    assert api.write_file(str(target), None)["ok"] is False


def test_path_normalisation(api, tmp_path):
    target = tmp_path / "sub" / ".." / "pic.hgr"
    (tmp_path / "sub").mkdir()
    api._allow(str(tmp_path / "pic.hgr"))
    assert api.write_file(str(target), b64(b"ok"))["ok"]


def test_save_settings_filters_unknown_keys(api, tmp_path):
    assert api.save_settings(json.dumps({"clipXferMode": "xor", "evil": "x", "lastDir": 5}))
    s = Settings(tmp_path / "settings.json")
    assert s.as_dict() == {"clipXferMode": "xor"}
    assert api.save_settings("not json") is False


def test_startup_files_returned_once(tmp_path):
    f = tmp_path / "s.hgr"
    f.write_bytes(b"\x00" * 8192)
    api = Api(Settings(tmp_path / "settings.json"), [f, tmp_path / "missing.hgr"])
    files = api.get_startup_files()
    assert [x["name"] for x in files] == ["s.hgr"]
    assert api.get_startup_files() == []
    assert api.write_file(str(f), b64(b"z"))["ok"]      # command-line files are approved


class FakeWindow:
    def __init__(self, result):
        self.result, self.calls = result, []

    def create_file_dialog(self, kind, **kw):
        self.calls.append((kind, kw))
        return self.result


def test_save_dialog_approves_chosen_path(api, tmp_path):
    chosen = str(tmp_path / "new.hgr")
    api._bind(FakeWindow((chosen,)))
    r = api.save_dialog("")
    assert r == {"path": chosen, "name": "new.hgr"}
    assert api._window.calls[0][1]["save_filename"] == "untitled.hgr"
    assert api.write_file(chosen, b64(b"abc"))["ok"]


def test_save_dialog_cancel(api):
    api._bind(FakeWindow(None))
    assert api.save_dialog("x.hgr") is None


def test_open_dialog_reads_files(api, tmp_path):
    f = tmp_path / "o.hgr"
    f.write_bytes(b"\x07" * 8192)
    api._bind(FakeWindow((str(f),)))
    files = api.open_dialog()
    assert len(files) == 1 and base64.b64decode(files[0]["data"]) == b"\x07" * 8192
    assert api._settings.get("lastDir") == str(tmp_path)


def test_underscore_members_hidden_from_js():
    public = [n for n in dir(Api) if not n.startswith("_")]
    assert sorted(public) == ["get_startup_files", "open_dialog", "save_dialog", "save_settings", "set_dirty", "write_file"]


def test_set_dirty(api):
    assert api._dirty is False
    api.set_dirty(True)
    assert api._dirty is True
    api.set_dirty(0)
    assert api._dirty is False


def test_strings_have_all_keys_in_every_language():
    from hgrtool.strings import STRINGS
    keys = set(STRINGS["en"])
    for lang, table in STRINGS.items():
        assert set(table) == keys, lang


def test_dialog_filters_follow_the_language(monkeypatch):
    from hgrtool import bridge
    from hgrtool.strings import STRINGS
    monkeypatch.setattr("hgrtool.strings.current_lang", lambda: "ko")
    assert bridge._file_types() == (STRINGS["ko"]["filter_hgr"], STRINGS["ko"]["filter_all"])
