"""Where things live: bundled web assets, and the writable data folder."""

import os
import sys
import tempfile
from pathlib import Path

APP_NAME = "HGRTool"
DATA_DIR_NAME = "hgrtool-data"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def web_dir() -> Path:
    """Folder holding the patched web app (bundled by PyInstaller, or src/web/<lang> in development)."""
    if is_frozen():
        return Path(sys._MEIPASS) / "web"  # type: ignore[attr-defined]
    # Development: src/web/<lang>; the language comes from HGRTOOL_LANG (default en).
    return Path(__file__).resolve().parent.parent / "web" / os.environ.get("HGRTOOL_LANG", "en")


def exe_dir() -> Path:
    """Folder that contains the executable (or src/ in development). Never the PyInstaller temp dir."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _user_config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME.lower()


def _is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=path, prefix=".w")
        os.close(fd)
        os.unlink(name)
        return True
    except OSError:
        return False


def data_dir() -> Path:
    """Writable per-user data folder.

    Portable first: <exe dir>/hgrtool-data. If that is not writable (e.g. installed under
    Program Files), fall back to the OS user config directory. HGRTOOL_DATA overrides both
    (used by the tests).
    """
    override = os.environ.get("HGRTOOL_DATA")
    if override:
        p = Path(override)
        p.mkdir(parents=True, exist_ok=True)
        return p
    portable = exe_dir() / DATA_DIR_NAME
    if _is_writable_dir(portable):
        return portable
    fallback = _user_config_dir()
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback
