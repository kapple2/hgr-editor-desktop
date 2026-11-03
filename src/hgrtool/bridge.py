"""Python functions callable from the page (pywebview js_api).

Security model: the page can only write to paths that this process itself obtained from a
native dialog (or the command line) during this session. Attributes starting with an
underscore are not exposed to JavaScript.
"""

import base64
import binascii
import json
import os
import tempfile
from pathlib import Path

from .settings import Settings
from .strings import tr

MAX_READ = 4 * 1024 * 1024
MAX_WRITE = 16 * 1024 * 1024


def _file_types():
    return (tr("filter_hgr"), tr("filter_all"))


def _norm(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


class Api:
    def __init__(self, settings: Settings, startup_files=()):
        self._settings = settings
        self._window = None
        self._allowed: set[str] = set()
        self._startup = [str(p) for p in startup_files]
        # Pushed by the page (see shim.js). The close handler must not call into the page
        # (evaluate_js from the closing event deadlocks the UI thread), so it reads this.
        self._dirty = False

    # ---- internal helpers (underscore: hidden from JS) ----
    def _bind(self, window) -> None:
        self._window = window

    def _allow(self, path: str) -> None:
        self._allowed.add(_norm(path))

    def _read(self, path: str):
        p = Path(path)
        if p.stat().st_size > MAX_READ:
            raise OSError("file too large")
        self._allow(str(p))
        return {
            "path": str(p),
            "name": p.name,
            "data": base64.b64encode(p.read_bytes()).decode("ascii"),
        }

    def _last_dir(self) -> str:
        d = self._settings.get("lastDir") or ""
        return d if d and os.path.isdir(d) else ""

    def _remember_dir(self, path: str) -> None:
        self._settings.update({"lastDir": str(Path(path).parent)})

    # ---- exposed to JS ----
    def open_dialog(self):
        """Native multi-file open dialog. Returns [{path, name, data(base64)}]."""
        import webview

        chosen = self._window.create_file_dialog(
            webview.FileDialog.OPEN,
            directory=self._last_dir(),
            allow_multiple=True,
            file_types=_file_types(),
        )
        files = []
        for path in chosen or ():
            try:
                files.append(self._read(path))
            except OSError:
                continue
        if files:
            self._remember_dir(files[0]["path"])
        return files

    def save_dialog(self, suggested_name):
        """Native save dialog. Returns {path, name} or None if cancelled."""
        import webview

        name = (suggested_name or "").strip() or "untitled.hgr"
        name = os.path.basename(name.replace("\\", "/"))
        chosen = self._window.create_file_dialog(
            webview.FileDialog.SAVE,
            directory=self._last_dir(),
            save_filename=name,
            file_types=_file_types(),
        )
        if not chosen:
            return None
        path = chosen if isinstance(chosen, str) else chosen[0]
        self._allow(path)
        self._remember_dir(path)
        return {"path": path, "name": os.path.basename(path)}

    def write_file(self, path, data_b64):
        """Write bytes to a path previously approved by a dialog. Returns {ok, error?}."""
        try:
            if not isinstance(path, str) or _norm(path) not in self._allowed:
                return {"ok": False, "error": "path was not chosen by the user"}
            data = base64.b64decode(data_b64, validate=True)
            if len(data) > MAX_WRITE:
                return {"ok": False, "error": "data too large"}
            self._write_atomic(path, data)
            return {"ok": True}
        except (OSError, binascii.Error, ValueError, TypeError) as exc:
            return {"ok": False, "error": str(exc)}

    @staticmethod
    def _write_atomic(path: str, data: bytes) -> None:
        directory = os.path.dirname(os.path.abspath(path))
        try:
            fd, tmp = tempfile.mkstemp(dir=directory, prefix=".hgr", suffix=".tmp")
        except OSError:
            with open(path, "wb") as f:  # directory not listable/creatable: write directly
                f.write(data)
            return
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
        except OSError:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            with open(path, "wb") as f:
                f.write(data)

    def set_dirty(self, flag):
        """The page reports whether any open image has unsaved edits."""
        self._dirty = bool(flag)
        return True

    def save_settings(self, json_text):
        try:
            values = json.loads(json_text)
        except (TypeError, ValueError):
            return False
        self._settings.update(values)
        return True

    def get_startup_files(self):
        """Files given on the command line (returned once)."""
        files = []
        for path in self._startup:
            try:
                files.append(self._read(path))
            except OSError:
                continue
        self._startup = []
        return files
