"""Application entry point: window, server, bridge, close prompt."""

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .bridge import Api
from .paths import data_dir, web_dir
from .server import WebServer
from .settings import Settings
from .strings import current_lang, tr


def parse_args(argv):
    p = argparse.ArgumentParser(prog="hgrtool", description="HGRTool Desktop - Apple II hi-res editor")
    p.add_argument("files", nargs="*", help=".hgr files to open")
    p.add_argument("--debug", action="store_true", help="enable the web inspector / context menu")
    p.add_argument("--selftest", action="store_true", help="run an automated smoke test and exit")
    p.add_argument("--selftest-out", help="file to write the self-test result to")
    p.add_argument("--version", action="version", version=f"hgrtool {__version__}")
    return p.parse_args(argv)


def make_closing_handler(window, api):
    """Window-close handler: asks before discarding unsaved edits. Returning False cancels.

    Reads api._dirty (pushed by the page) instead of calling window.evaluate_js: evaluating
    JavaScript from inside the closing event blocks the UI thread forever.
    """

    def on_closing():
        if api._dirty:
            return bool(window.create_confirmation_dialog(tr("window_title"), tr("confirm_discard")))
        return True

    return on_closing


def main(argv=None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    import webview

    debug = args.debug or os.environ.get("HGRTOOL_DEBUG") == "1"
    data = data_dir()
    settings = Settings(data / "settings.json")
    server = WebServer(web_dir(), settings, debug=debug).start()

    files = [Path(f) for f in args.files if Path(f).is_file()]
    api = Api(settings, files)
    # Default 1280x800, but never larger than the (logical) primary screen minus taskbar/title bar.
    width, height = 1280, 800
    try:
        screen = webview.screens[0]
        width = min(width, int(screen.width * 0.92))
        height = min(height, int(screen.height * 0.80))
    except Exception:
        pass
    window = webview.create_window(
        tr("window_title"),
        server.url,
        js_api=api,
        width=width,
        height=height,
        min_size=(min(1024, width), min(640, height)),
        background_color="#535353",
    )
    api._bind(window)

    result = {"code": 0}

    if args.selftest:
        from .selftest import run_selftest

        out = Path(args.selftest_out) if args.selftest_out else data / "selftest-result.txt"
        start_func = lambda: result.update(  # noqa: E731
            code=run_selftest(window, api, out, make_closing_handler(window, api)))
    else:
        start_func = None
        window.events.closing += make_closing_handler(window, api)

    try:
        webview.start(start_func, debug=debug)
    finally:
        server.stop()
    return result["code"]


if __name__ == "__main__":
    sys.exit(main())
