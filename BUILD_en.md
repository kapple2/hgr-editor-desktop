# BUILD

[한국어](BUILD.md) | **English**

## Quick start (Windows)

```
build_all.bat            # single-file exes -> dist\hgrtool.exe (English), dist\hgrtool-ko.exe (Korean)
build_all.bat onedir     # folder builds    -> dist\hgrtool\hgrtool.exe, dist\hgrtool-ko\hgrtool-ko.exe (start faster)
```

`build_all.bat` builds **both language versions** and stops with a clear message at the first failure:

1. checks that Python 3.13 is available through the `py` launcher
2. creates `.venv` and installs the pinned packages from `src\requirements-dev.txt` (which includes `requirements.txt`) into it
3. records SHA-256 checksums of `hgrtool-local\`
4. runs the unit tests (pytest)
5. for each language (`en`, `ko`): generates `src\web\<lang>\` (a patched, and for `ko` translated, copy of
   `hgrtool-local\`), then builds the exe with PyInstaller into `dist\`
6. runs each exe with `--selftest` (a window opens for a few seconds) and checks for `RESULT: OK`
7. re-checks that `hgrtool-local\` is unchanged

The finished apps are `dist\hgrtool.exe` (English) and `dist\hgrtool-ko.exe` (Korean), plus `dist\LICENSE.txt`
and `dist\LICENSES.txt`. They are portable: copy them anywhere. At first run an app creates `hgrtool-data\` next to
itself (settings), or uses `%APPDATA%\HGRTool` if that folder is not writable. Both apps use the same
settings folder name, so when they sit in the same folder they share their settings.

## Tools needed

| Tool | Version | Notes |
|---|---|---|
| Python | 3.13 (python.org) with the `py` launcher | not the Microsoft Store build, not Anaconda |
| Internet | first build only | downloads wheels from PyPI into `.venv` |
| WebView2 runtime | any current | preinstalled on Windows 11; needed to *run* (and to run the smoke tests) |

Python packages (pinned in `src/requirements.txt` for the app and `src/requirements-dev.txt` for build/test tools;
installed only in `.venv`): pywebview, pythonnet (+clr_loader, cffi, pycparser), bottle, proxy_tools,
pyinstaller (+hooks, altgraph, pefile, pywin32-ctypes, packaging, setuptools), pytest (+pluggy, iniconfig,
colorama, Pygments). No Node.js, no C compiler.

## The venv

All Python work uses `.venv` (project root). Nothing is installed globally.

```
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r src\requirements-dev.txt     # Windows (app + build/test tools)
.venv\Scripts\python.exe -m pytest -q                                   # run from src\
.venv\Scripts\python.exe src\tools\patch_web.py --lang en               # or --lang ko
.venv\Scripts\python.exe src\run_hgrtool.py [file.hgr]                  # run from source
```

`build_all.bat` writes `.venv\pip.ini` pinning the index to PyPI only. (On the author's machine a global
pip config listed an extra, unreachable index that made installs fail.) Delete `.venv` to start clean.

To update dependencies: `pip install -U <pkg>` in the venv, test, then update the pinned versions in
`src/requirements.txt` / `src/requirements-dev.txt` (`pip freeze` shows the installed versions).

## Running without building

```
.venv\Scripts\python.exe src\tools\patch_web.py --lang ko
set HGRTOOL_LANG=ko
.venv\Scripts\python.exe src\run_hgrtool.py work\sample.hgr
```
`HGRTOOL_LANG` (default `en`) chooses which generated bundle, `src\web\<lang>\`, a source run uses.
Options: `--debug` (right-click menu + web inspector), `--selftest`, `--version`.
Dev runs keep data in `src\hgrtool-data\` (override with the `HGRTOOL_DATA` environment variable).

## Languages

Each build contains exactly one language. The Korean build differs only by the translated page
(`src/tools/translations.py`), a few Python-side texts (`src/hgrtool/strings.py`) and the exe name.
To add another language, see `ARCHITECTURE_en.md` section 3.1. To fix a Korean wording, edit
`translations.py` (and `strings.py` for dialog/prompt texts) and rebuild; the build fails if a string it is
supposed to translate no longer exists in `hgrtool-local/`.

## macOS and Linux (NOT YET TESTED)

`build_all.sh` mirrors the Windows script, including both languages. It has not been run on a Mac or Linux
machine yet, so expect to fix small things; please report what breaks.

**macOS**: install Python 3.10+ (python.org or Homebrew) and run `./build_all.sh`. The results are
`dist/HGRTool.app` and `dist/HGRTool-ko.app`. Unsigned apps trigger Gatekeeper: right-click → Open the first time.
`src/res/icon.icns` is not provided yet, so the apps use the default icon until one is added.

**Linux**: install the system packages first (Debian/Ubuntu names; others differ), then `./build_all.sh`:
```
sudo apt install python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
                 libgirepository1.0-dev libcairo2-dev pkg-config build-essential
```
The script creates the venv with `--system-site-packages` so PyGObject is visible. The results are
`dist/hgrtool` and `dist/hgrtool-ko`. WebKitGTK must also be installed on machines that run them. For the
Korean build, a Korean font (for example Noto Sans CJK KR) must be installed. Bundling GTK/WebKit with
PyInstaller can need extra hooks; if an exe fails to start, run `python src/run_hgrtool.py` from the
venv to confirm the app itself works.

## Troubleshooting

- **"Python 3.13 was not found"**: install from python.org and tick "py launcher"; `py -3.13 --version` must work.
- **pip fails with `getaddrinfo failed` for another host**: a global pip config points to an unreachable
  index; the venv's `pip.ini` (created by the script) overrides it. If you created the venv yourself, add that file.
- **`PATCH ERROR: anchor expected 1x but found 0x`**: `hgrtool-local/` differs from the version the patcher
  was written for. Update the matching patch in `src/tools/patch_web.py` (or the string in `translations.py`).
- **Blank window / "WebView2 not found"**: install the Evergreen WebView2 runtime from Microsoft.
- **Antivirus flags an exe**: PyInstaller one-file executables are sometimes false-positives.
  Use `build_all.bat onedir`, or code-sign the exe (not set up here).
- **Slow first start (1-2 s)**: one-file builds unpack to a temp folder; use `onedir` for faster starts.
- **Close button does nothing after editing**: that is the "unsaved changes" prompt; answer it.
- **Korean text shows as boxes**: the system has no Hangul font (normal on Windows and macOS; see Linux above).
- **Smoke test fails**: read `work\selftest-dist-en.txt` or `work\selftest-dist-ko.txt`; each line names the failed check.

## Publishing the executables

`dist/` is committed to git on purpose so people can download the exes straight from the repository.
Binary files are not diffed and every rebuild adds roughly 26 MB (two exes) to the repository history, so
rebuild and commit `dist/` only for releases, not for every code change. (GitHub rejects files over 100 MB;
the current ones are about 13 MB each. If the history grows too large, move the exes to GitHub Releases.)

## Not included

Code signing, notarization, installers and auto-update. `src/res/icon.ico` is the upstream 32×32
favicon; replace it with a larger multi-size icon for a sharper taskbar icon.
