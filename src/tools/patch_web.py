"""Build the desktop web bundle from the untouched upstream copy.

    python patch_web.py [--lang en|ko] [--src hgrtool-local] [--overlay src/web_overlay] [--out src/web/<lang>]

Reads --src (never writes to it), applies exact-string patches, adds the overlay files and writes
the result to --out. Every patch states how many times its anchor must occur; any mismatch
aborts the build, so an upstream change can never silently produce a broken app. Standard
library only.
"""

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from translations import LANGUAGES  # noqa: E402

MARKER = ".generated-by-patch_web"

HERE = Path(__file__).resolve().parent
SRC_ROOT = HERE.parent                 # .../src
PROJECT = SRC_ROOT.parent


class PatchError(Exception):
    pass


def _p(name, old, new, count=1):
    return {"name": name, "old": old, "new": new, "count": count}


# ---------------------------------------------------------------------------- patches ---
PALETTE_PANEL_AFTER = """        <button class="icon-button" id="btn-about">
            <i class="fa-solid fa-question"></i>About
        </button>
"""

HTML_PATCHES = [
    # P1: settings + shim scripts run before the editor script.
    _p("P1 load settings.js and shim.js",
       '<div id="snackbar">Hello, world!</div>\n',
       '<div id="snackbar">Hello, world!</div>\n\n'
       '<script src="settings.js"></script>\n<script src="shim.js"></script>\n'),

    # P2: localStorage -> file-backed store.
    _p("P2a settings store (colorSwatchClose)", "localStorage.colorSwatchClose",
       "window.__hgrStore.colorSwatchClose", count=2),
    _p("P2b settings store (clipXferMode)", "localStorage.clipXferMode",
       "window.__hgrStore.clipXferMode", count=2),

    # P3: swatch containers leave the dialog; the palette panel goes into the left bar.
    _p("P3a remove swatch bodies from the color dialog",
       '        <div id="hgr-color-body"><!--generated--></div>\n'
       '        <div id="hgr-dither-body"><!--generated--></div>\n', ""),
    _p("P3b palette panel in the left bar", PALETTE_PANEL_AFTER,
       PALETTE_PANEL_AFTER + "@@PALETTE_HTML@@"),

    # P4: nothing to close any more.
    _p("P4 swatch click no longer closes a dialog",
       '        if (event.type === "dblclick" || this.colorSwatchClose == Settings.SWATCH_CLOSE_SINGLE) {\n'
       '            document.getElementById("color-picker-hgr").close();\n'
       '        }\n', ""),

    # P5: the (bottom bar) current-color button now just brings the palette into view.
    _p("P5 handleSelectColor focuses the palette",
       'document.getElementById("color-picker-hgr").showModal();',
       'document.getElementById("palette-panel").scrollIntoView({ block: "nearest" });'),

    # P6: remove the Choose Color button (a hidden stub keeps the editor's listener binding).
    _p("P6 hide Choose Color button",
       '<button class="icon-button" id="btn-choose-color">',
       '<button class="icon-button" id="btn-choose-color" hidden style="display:none">'),

    # P7: hide the obsolete "close dialog on single/double click" setting (elements must stay).
    _p("P7a hide swatch-close setting label",
       "        <div>\n            Close the color selection dialog when a swatch is...\n        </div>\n",
       "        <div hidden>\n            Close the color selection dialog when a swatch is...\n        </div>\n"),
    _p("P7b hide swatch-close setting radios",
       '        <div class="settings-radios">\n            <input type="radio" id="setting-swatch-single"',
       '        <div class="settings-radios" hidden>\n            <input type="radio" id="setting-swatch-single"'),

    # P8: keep the large palette indicator in sync with the current color.
    _p("P8 palette indicator follows onColorChanged",
       "    onColorChanged() {\n",
       "    onColorChanged() {\n"
       "        if (window.__hgrDrawCurrent) { window.__hgrDrawCurrent(this.currentPicture); }\n"),

    # P10: show the desktop wrapper version in the About box.
    _p("P10 About shows desktop version",
       "versionTextElem.innerText = VERSION;",
       'versionTextElem.innerText = VERSION + (window.__hgrDesktopVersion ? " (desktop " + window.__hgrDesktopVersion + ")" : "");'),

    # P11: expose what the native side and the self-test need (the editor lives in an IIFE).
    _p("P11 expose window.__hgr",
       "const gAbout = new About();\n",
       "const gAbout = new About();\n\n"
       "// HGRTool Desktop hooks.\n"
       "window.__hgr = {\n"
       "    editor: imgEdit,\n"
       "    picker: gColorPickerHgr,\n"
       "    isDirty: () => imgEdit.pictureList.some((p) => p.isDirty),\n"
       "};\n"
       "imgEdit.onColorChanged();\n"),
]


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def apply_patches(text: str, patches, values: dict | None = None) -> str:
    values = values or {}
    for patch in patches:
        found = text.count(patch["old"])
        if found != patch["count"]:
            raise PatchError(
                f"patch '{patch['name']}': anchor expected {patch['count']}x but found {found}x "
                f"(upstream hgrtool.html changed?)"
            )
        new = patch["new"]
        for key, val in values.items():
            new = new.replace(key, val)
        text = text.replace(patch["old"], new)
    return text


def build(src: Path, overlay: Path, out: Path, lang: str = "en") -> None:
    if lang not in LANGUAGES:
        raise PatchError(f"unknown language '{lang}' (known: {', '.join(LANGUAGES)})")
    tr = LANGUAGES[lang]
    src, overlay, out = Path(src).resolve(), Path(overlay).resolve(), Path(out).resolve()
    for need in (src / "hgrtool.html", src / "editor.css", src / "fa", overlay / "shim.js",
                 overlay / "palette.css", overlay / "palette.html"):
        if not need.exists():
            raise PatchError(f"missing input: {need}")
    if out == src or src in out.parents:
        raise PatchError("refusing to write inside the upstream source folder")

    # Patch in memory first, so a failure leaves the previous output untouched.
    html = _normalize((src / "hgrtool.html").read_text(encoding="utf-8"))
    palette_html = _normalize((overlay / "palette.html").read_text(encoding="utf-8"))
    html = apply_patches(html, HTML_PATCHES, {"@@PALETTE_HTML@@": palette_html})
    html = apply_patches(html, tr["html"])                       # translations (strict, too)
    css = _normalize((src / "editor.css").read_text(encoding="utf-8"))
    css += _normalize((overlay / "palette.css").read_text(encoding="utf-8"))
    css += tr["css"]
    shim = apply_patches(_normalize((overlay / "shim.js").read_text(encoding="utf-8")), tr["shim"])

    if out.exists():
        if not (out / MARKER).exists():
            raise PatchError(f"{out} exists and was not generated by this tool; refusing to delete it")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / MARKER).write_text("generated; safe to delete\n")
    (out / "lang.txt").write_text(lang + "\n")
    (out / "hgrtool.html").write_text(html, encoding="utf-8", newline="\n")
    (out / "editor.css").write_text(css, encoding="utf-8", newline="\n")
    shutil.copytree(src / "fa", out / "fa")
    for name in ("favicon.ico", "LegalStuff.txt"):
        if (src / name).exists():
            shutil.copy2(src / name, out / name)
    (out / "shim.js").write_text(shim, encoding="utf-8", newline="\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default=str(PROJECT / "hgrtool-local"))
    ap.add_argument("--overlay", default=str(SRC_ROOT / "web_overlay"))
    ap.add_argument("--lang", default="en", choices=sorted(LANGUAGES))
    ap.add_argument("--out", help="output folder (default: src/web/<lang>)")
    args = ap.parse_args(argv)
    out = Path(args.out) if args.out else SRC_ROOT / "web" / args.lang
    try:
        build(Path(args.src), Path(args.overlay), out, args.lang)
    except PatchError as exc:
        print(f"PATCH ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"web bundle [{args.lang}] written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
