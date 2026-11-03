"""Texts shown by the Python side (the web page's own texts are translated at build time).

The language is fixed per build: the patcher writes lang.txt into the bundled web folder.
"""

from .paths import web_dir

DEFAULT_LANG = "en"

STRINGS = {
    "en": {
        "window_title": "HGRTool",
        "confirm_discard": "You have unsaved changes.\nDiscard them and quit?",
        "filter_hgr": "HGR screens (*.hgr)",
        "filter_all": "All files (*.*)",
    },
    "ko": {
        "window_title": "HGRTool",
        "confirm_discard": "저장하지 않은 변경 사항이 있습니다.\n변경 내용을 버리고 종료하시겠습니까?",
        "filter_hgr": "HGR 화면 (*.hgr)",
        "filter_all": "모든 파일 (*.*)",
    },
}


def current_lang() -> str:
    try:
        lang = (web_dir() / "lang.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return DEFAULT_LANG
    return lang if lang in STRINGS else DEFAULT_LANG


def tr(key: str, lang: str | None = None) -> str:
    table = STRINGS.get(lang or current_lang(), STRINGS[DEFAULT_LANG])
    return table.get(key) or STRINGS[DEFAULT_LANG][key]
