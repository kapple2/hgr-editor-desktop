"""Persistent settings stored as a small JSON file."""

import json
import os
import tempfile
import threading
from pathlib import Path

# Keys the web app (and this wrapper) may store. Anything else is ignored.
ALLOWED_KEYS = ("clipXferMode", "colorSwatchClose", "lastDir")
MAX_VALUE_LEN = 1024


class Settings:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._data: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(raw, dict):
            self._data = self._clean(raw)

    @staticmethod
    def _clean(raw: dict) -> dict[str, str]:
        out = {}
        for key in ALLOWED_KEYS:
            value = raw.get(key)
            if isinstance(value, str) and len(value) <= MAX_VALUE_LEN:
                out[key] = value
        return out

    def get(self, key: str, default: str | None = None) -> str | None:
        with self._lock:
            return self._data.get(key, default)

    def as_dict(self) -> dict[str, str]:
        with self._lock:
            return dict(self._data)

    def update(self, values: dict) -> None:
        """Merge values (unknown keys / non-strings dropped) and write the file."""
        cleaned = self._clean(values if isinstance(values, dict) else {})
        with self._lock:
            self._data.update(cleaned)
            self._write()

    def _write(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".settings", suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass  # settings are a convenience; never crash the app over them
