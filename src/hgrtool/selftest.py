"""Automated smoke test run inside the real window (`hgrtool --selftest`).

Checks, using the real page: the palette is always visible and has the right swatches, a click
on a swatch changes the current color (and highlights it), and the open -> save path through the
File System Access shim writes a byte-identical file. The result goes to a text file because the
windowed exe has no console.
"""

import base64
import json
import os
import tempfile
import time
from pathlib import Path

from .strings import current_lang


def _js(window, code, timeout=20.0):
    """Run an async JS snippet and wait for its JSON result (polled; works on every backend)."""
    key = f"__st_{int(time.time() * 1000)}"
    window.evaluate_js(
        f"window.{key}=undefined;(async()=>{{{code}}})()"
        f".then(r=>{{window.{key}=JSON.stringify(r===undefined?null:r)}})"
        f".catch(e=>{{window.{key}=JSON.stringify({{__error:String(e)}})}});1"
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        got = window.evaluate_js(f"window.{key}")
        if got is not None:
            return json.loads(got)
        time.sleep(0.1)
    raise TimeoutError("page did not answer")


def _wait_for(cond, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if cond():
            return True
        time.sleep(0.1)
    return False


def run_selftest(window, api, out_path: Path, closing_handler=None) -> int:
    lines, failures = [], 0

    def check(name, ok, detail=""):
        nonlocal failures
        if not ok:
            failures += 1
        lines.append(f"{'PASS' if ok else 'FAIL'}  {name}{('  ' + str(detail)) if detail else ''}")

    try:
        # Wait for the page and the editor.
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                if window.evaluate_js("!!(window.__hgr && window.pywebview && window.pywebview.api)"):
                    break
            except Exception:
                pass
            time.sleep(0.2)
        check("editor loaded (window.__hgr)", bool(window.evaluate_js("!!window.__hgr")))

        lang = current_lang()
        label = _js(window, "const b = document.getElementById('btn-open').cloneNode(true);"
                            " b.querySelectorAll('i,span').forEach(e => e.remove());"
                            " return {open: b.textContent.trim(),"
                            " htmlLang: document.documentElement.lang,"
                            " color: document.querySelector('#palette-panel .left-header3').textContent.trim()}")
        expect = {"en": ("Open", "en", "Color"), "ko": ("열기", "ko", "색상")}[lang]
        check(f"UI language is {lang}", (label["open"], label["htmlLang"], label["color"]) == expect, label)

        info = _js(window, """
            const solids = document.querySelectorAll('#hgr-color-body .swatch-button').length;
            const dith = document.querySelectorAll('#hgr-dither-body .swatch-button').length;
            const panel = document.getElementById('palette-panel').getBoundingClientRect();
            const dlg = document.getElementById('color-picker-hgr');
            return {solids, dith, expectDith: window.__hgr.picker.ditherPats.length,
                    panelH: panel.height, panelW: panel.width, dialogOpen: dlg.open,
                    chooseVisible: !!document.getElementById('btn-choose-color').offsetParent};
        """)
        check("10 solid swatches", info["solids"] == 10, info["solids"])
        check("dither swatches match the palette", info["dith"] == info["expectDith"] > 50, info["dith"])
        check("palette panel is visible", info["panelH"] > 50 and info["panelW"] > 100, f"{info['panelW']}x{info['panelH']}")
        check("no color dialog", info["dialogOpen"] is False)
        check("old Choose Color button hidden", info["chooseVisible"] is False)

        clicked = _js(window, """
            const pk = window.__hgr.picker;
            const sw = document.querySelectorAll('#hgr-dither-body .swatch-button')[7];
            sw.click();
            const same = pk.currentPat === pk.ditherPats[7];
            const selected = sw.classList.contains('selected');
            const solid = document.querySelectorAll('#hgr-color-body .swatch-button')[2];
            solid.click();
            return {same, selected, solidSame: pk.currentPat === pk.solidPats[2],
                    solidSelected: solid.classList.contains('selected'),
                    oldDeselected: !sw.classList.contains('selected')};
        """)
        check("click on dither swatch sets current color + highlight", clicked["same"] and clicked["selected"], clicked)
        check("click on solid swatch moves the highlight", clicked["solidSame"] and clicked["solidSelected"] and clicked["oldDeselected"], clicked)

        # Open -> Save round trip through the shim, with a real file on disk.
        tmp = Path(tempfile.mkdtemp(prefix="hgrtool-selftest-"))
        target = tmp / "roundtrip.hgr"
        original = os.urandom(8192)
        target.write_bytes(original)
        api._allow(str(target))
        rt = _js(window, f"""
            const files = await window.pywebview.api.get_startup_files();  // empty; just proves the bridge
            const b64 = {json.dumps(base64.b64encode(original).decode())};
            const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
            const h = window.__hgrMakeHandle({json.dumps(str(target))}, 'roundtrip.hgr', bytes);
            await window.__hgr.editor.loadFile(await h.getFile(), h);
            const e = window.__hgr.editor;
            const loaded = e.pictureList.length;
            const dirtyAfterLoad = window.__hgr.isDirty();
            await e.handleSave();
            return {{loaded, dirtyAfterLoad, startupFiles: files.length}};
        """)
        check("file loaded through the handle", rt["loaded"] == 1, rt)
        check("freshly opened file is not dirty", rt["dirtyAfterLoad"] is False)
        check("open -> save is byte-identical", target.read_bytes() == original)

        if closing_handler is not None:
            # Close prompt: clean -> closes without asking; dirty -> asks (answer faked) and can cancel.
            asked = []
            real_confirm = window.create_confirmation_dialog
            window.create_confirmation_dialog = lambda title, msg: asked.append(msg) or False
            try:
                clean_ok = closing_handler() is True and not asked
                _js(window, "const p = window.__hgr.editor.pictureList[0]; p.undoIndex = p.saveIndex + 1;")
                dirty_flag = window.evaluate_js("window.__hgr.isDirty()")
                _wait_for(lambda: api._dirty is True)          # the page pushes the state within ~0.5 s
                cancelled = closing_handler() is False and len(asked) == 1
                _js(window, "const p = window.__hgr.editor.pictureList[0]; p.undoIndex = p.saveIndex;")
                _wait_for(lambda: api._dirty is False)
            finally:
                window.create_confirmation_dialog = real_confirm
            check("close with no edits: no prompt", clean_ok)
            check("close with unsaved edits: prompts and can cancel", dirty_flag is True and cancelled, asked)
            check("dirty flag returns to clean after saving/undo", api._dirty is False)

        # Settings written by the page reach the settings file (page -> bridge -> JSON on disk).
        before = api._settings.get("clipXferMode")
        window.evaluate_js("window.__hgrStore.clipXferMode = 'xor'")
        saved = _wait_for(lambda: api._settings.get("clipXferMode") == "xor")
        on_disk = '"xor"' in api._settings.path.read_text(encoding="utf-8") if saved else False
        check("settings change in the page is saved to the file", saved and on_disk)
        api._settings.update({"clipXferMode": before or "copy"})   # restore

        refused = api.write_file(str(tmp / "not-approved.hgr"), base64.b64encode(b"x").decode())
        check("write to an un-approved path is refused", refused["ok"] is False and not (tmp / "not-approved.hgr").exists())
    except Exception as exc:  # report, never hang
        failures += 1
        lines.append(f"FAIL  selftest crashed: {exc!r}")

    lines.append("RESULT: " + ("OK" if failures == 0 else f"{failures} FAILED"))
    text = "\n".join(lines) + "\n"
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(text, encoding="utf-8")
    except OSError:
        pass
    try:
        print(text)
    except Exception:
        pass
    try:
        window.destroy()
    except Exception:
        pass
    return 0 if failures == 0 else 1
