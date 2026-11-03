# ARCHITECTURE

[한국어](ARCHITECTURE.md) | **English**

HGRTool Desktop wraps the upstream HGRTool web editor (`hgrtool-local/`, by fadden) in a native
window. The editor's own HTML/JS is reused; Python provides the window, native file dialogs, a
settings file and the unsaved-changes prompt. One enhancement was added to the UI: an
always-visible color palette. The app is built in two languages, English and Korean, from the same code.

## 1. Repository layout

```
proj2-apple2-hgr-editor/
├─ README.md README_en.md             overview (Korean default / English)
├─ ARCHITECTURE.md ARCHITECTURE_en.md these docs
├─ BUILD.md BUILD_en.md               build instructions
├─ LICENSE LICENSES.txt               Apache 2.0 text; third-party notices (copied to dist/)
├─ build_all.bat / build_all.sh       one-command build of both languages into dist/
├─ hgrtool-local/                     UPSTREAM COPY. Never modified (checksummed by the build).
├─ docs/                              screenshots used by the READMEs
├─ .venv/                             project virtual environment (not committed)
├─ src/
│  ├─ requirements.txt                pinned runtime dependencies (bundled into the exe)
│  ├─ requirements-dev.txt            build/test tools (PyInstaller, pytest); includes requirements.txt
│  ├─ pytest.ini                      test configuration
│  ├─ run_hgrtool.py                  PyInstaller entry point
│  ├─ hgrtool.spec                    PyInstaller spec (one language per run; onefile or onedir)
│  ├─ hgrtool/                        the Python application package
│  │  ├─ app.py                       main(): args, window, server, close prompt
│  │  ├─ bridge.py                    class Api: functions callable from JavaScript
│  │  ├─ server.py                    loopback HTTP server for the bundled web files
│  │  ├─ settings.py                  JSON settings file
│  │  ├─ paths.py                     bundled-resource and data-folder locations
│  │  ├─ strings.py                   texts shown by the Python side, per language
│  │  └─ selftest.py                  `--selftest`: automated smoke test in the real window
│  ├─ web_overlay/                    our additions to the web app
│  │  ├─ shim.js                      File System Access emulation, settings store, dirty reporting
│  │  ├─ palette.css                  compact left bar + palette styling
│  │  └─ palette.html                 palette panel markup
│  ├─ tools/
│  │  ├─ patch_web.py                 builds src/web/<lang>/ from hgrtool-local/ + overlay (stdlib only)
│  │  ├─ translations.py              the Korean string table applied by patch_web.py
│  │  └─ checksum_tree.py             proves hgrtool-local/ is unchanged
│  ├─ web/en/  web/ko/                GENERATED bundles (patched copies); one is embedded in each exe
│  ├─ res/icon.ico                    exe icon (from the upstream favicon)
│  └─ tests/                          pytest unit tests
├─ work/                              scratch: checksums, self-test output
└─ dist/                              build output: hgrtool.exe (English), hgrtool-ko.exe (Korean), licenses
```

## 2. How it works at run time

```
 double-click hgrtool.exe  (or hgrtool-ko.exe)
   │  PyInstaller bootloader unpacks to a temp folder (onefile) and starts Python
   ▼
 app.main()
   ├─ data_dir()             <exe folder>/hgrtool-data, else the OS user-config folder
   ├─ Settings(settings.json)
   ├─ WebServer(web/).start()      http://127.0.0.1:<random port>/   (thread)
   ├─ Api(settings, files-from-command-line)   (js_api: the JS <-> Python bridge)
   ├─ webview.create_window(title, server.url, js_api=api, size fitted to the screen)
   ├─ window.events.closing += close handler
   └─ webview.start()        native window with the system web view (WebView2 / WKWebView / WebKitGTK)
```

The language is decided at build time. The bundle's `web/lang.txt` says `en` or `ko`; the Python side
(`strings.py`) reads it to pick its few texts (window title, close prompt, file-dialog filters).

### 2.1 The page
The window loads `hgrtool.html` from the loopback server. The server serves only files under
the bundled `web/` folder, binds to 127.0.0.1, rejects other `Host` headers (DNS-rebinding
protection), refuses path traversal and non-GET methods. It also generates `/settings.js`, which
puts the saved settings in `window.__hgrInitialSettings` *before* the editor script runs. (A
random port means a new browser origin on each launch, so `localStorage` would not persist.)

### 2.2 File System Access shim (`web_overlay/shim.js`)
The editor opens and saves files with `showOpenFilePicker()` / `showSaveFilePicker()` and
`handle.createWritable()`. The shim defines those functions on top of the Python bridge, so the
editor's open/save code runs **unchanged**:

| Editor calls | Shim does |
|---|---|
| `showOpenFilePicker()` | `api.open_dialog()` → native dialog → handles with `getFile()` |
| `showSaveFilePicker({suggestedName})` | `api.save_dialog(name)` → native dialog; cancel → `AbortError` |
| `handle.createWritable()` → `truncate/write/close` | buffer in memory; `close()` calls `api.write_file(path, base64)` |

Bytes cross the bridge as base64 (files are 8 KB). The shim also provides `window.__hgrStore`,
a synchronous settings object that replaces `localStorage`, writing changes through
`api.save_settings()`; opens command-line files at startup; blocks the browser context menu
(unless `--debug`); and every 300 ms reports whether any image has unsaved edits via
`api.set_dirty()`.

### 2.3 Python bridge (`bridge.py`)
Public methods (callable from JS): `open_dialog`, `save_dialog`, `write_file`, `save_settings`,
`get_startup_files`, `set_dirty`. Members starting with `_` are not exposed.

Security rule: `write_file` only writes to paths this process itself obtained from a native
dialog or the command line in the current session (`_allowed`). A compromised page therefore
cannot write arbitrary files. Writes are atomic (temp file + rename) with a direct-write fallback.

### 2.4 Settings and data folder
`<exe folder>/hgrtool-data/settings.json` (portable). If that folder is not writable it falls
back to `%APPDATA%\HGRTool`, `~/Library/Application Support/HGRTool` or `~/.config/hgrtool`.
`HGRTOOL_DATA` overrides the location (used by tests). Only known keys are stored
(`clipXferMode`, `colorSwatchClose`, `lastDir`), with length limits; a corrupt file is ignored.
The English and Korean executables use the same folder name, so they share one settings file when placed together.

### 2.5 Unsaved-changes prompt
The window's `closing` event handler shows a native confirmation if `api._dirty` is true, and
returns `False` to cancel the close. It deliberately **reads a flag that the page pushes**
instead of calling `window.evaluate_js()`: calling into the page from inside the closing event
blocks the UI thread (this was observed: the window hung as "not responding").

## 3. Build-time patching (`src/tools/patch_web.py`)

Run once per language: `patch_web.py --lang en|ko` reads `hgrtool-local/` and writes
`src/web/<lang>/`; it never writes upstream. Each patch is an exact string
replacement with an expected occurrence count; a mismatch aborts the build (so an upstream
change cannot silently break the app). The patches:

| # | Change | Why |
|---|---|---|
| P1 | add `<script src="settings.js">` and `shim.js` before the editor script | load settings + shim first |
| P2 | `localStorage.x` → `window.__hgrStore.x` (4 places) | settings file instead of localStorage |
| P3 | move `#hgr-color-body` / `#hgr-dither-body` from the color dialog into `#palette-panel` in the left bar | always-visible palette (the editor still builds the swatches into these ids) |
| P4 | `handleSwatchClick`: drop the "close dialog" branch | nothing to close |
| P5 | `handleSelectColor()` scrolls to the palette | the bottom-bar "Pattern" button still does something sensible |
| P6 | hide the Choose Color button (a hidden stub remains so the editor's listener binds) | remove the pop-up entry point |
| P7 | hide the "close color dialog when swatch is…" setting (elements kept) | obsolete; `Settings` still reads those elements |
| P8 | `onColorChanged()` also redraws the big current-color box | current-color indicator |
| P10 | About box shows `(desktop <version>)` | identify the wrapper version |
| P11 | expose `window.__hgr = {editor, picker, isDirty}` | dirty reporting and self-test (the editor lives in an IIFE) |

(P9, a canvas-size patch, turned out to be unnecessary: CSS scaling gives good swatches.)
`editor.css` gets `web_overlay/palette.css` appended; `palette.html` is inserted into the left bar.

### 3.1 Translation (Korean build)
After the patches above, `patch_web.py --lang ko` applies the table in `src/tools/translations.py` to the
patched page and to `shim.js`: about 85 exact-string replacements covering every visible label, tooltip,
dialog text, and the messages the editor's code shows (including the `confirm()` question). Each entry has an
expected count, so a missing or changed anchor fails the build instead of leaving English text behind.
The Korean build also sets `<html lang="ko">` and appends CSS that selects Hangul-capable fonts (Malgun Gothic,
Apple SD Gothic Neo, Noto Sans CJK KR) and slightly smaller button labels so the longer words fit.
Left in English on purpose: the legal text in the About box, and technical error text coming from the operating
system.

To add another language: add an entry to `LANGUAGES` in `translations.py`, a table in `hgrtool/strings.py`, and
the language code to `LANGS` in the build scripts.

## 4. The palette

The left bar became a compact scrolling column: Tools (10 buttons), Configuration (4 buttons),
then **Color**: a large current-color box, the 10 solid colors (2 rows of 5) and the 108 dither
patterns (11 × 10). Clicking a swatch runs the editor's existing `handleSwatchClick` →
`setColor` → `onColorChanged`, so the highlight (white outline), current pattern and both
indicators (large box and the bottom bar's "Pattern" box) update at once. Because only
`currentPat` changes, an in-progress selection, clipping or text is not disturbed. The picker's
state is global, so the color stays when you switch images. If the window is too short the left
bar scrolls.

## 5. Tests

- `src/tests` (pytest, run inside `.venv`): patcher (anchors, no upstream writes, both languages,
  Korean strings present and English labels gone), bridge (path approval, byte-identical round trip, bad
  input), string tables, server (traversal, Host check, methods), settings and data-folder fallback.
- `hgrtool --selftest [--selftest-out file]`: runs in a real window against the real exe; checks the UI
  language, palette presence/behaviour, open → save byte identity through the shim, settings persistence,
  the close prompt logic and the write-approval rule. `build_all` runs it on each built exe.

## 6. Platform notes

| | Window | Notes |
|---|---|---|
| Windows | WebView2 (via pythonnet) | needs the WebView2 runtime (preinstalled on Windows 11) |
| macOS | WKWebView (pyobjc) | build produces `HGRTool.app` / `HGRTool-ko.app`; **untested** |
| Linux | WebKitGTK (PyGObject) | system packages required; **untested** |
