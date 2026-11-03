#!/usr/bin/env bash
# HGRTool Desktop - build everything for macOS / Linux and put the apps in dist/.
#
# Builds two versions:  English (hgrtool / HGRTool.app)  and  Korean (hgrtool-ko / HGRTool-ko.app)
#
#   ./build_all.sh            single-file builds
#   ./build_all.sh onedir     folder builds (faster start)
#
# All Python work happens in the project venv (.venv). Nothing is installed globally.
# NOTE: this script has NOT been tested on macOS or Linux yet (see BUILD.md).
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
VENV="$PWD/.venv"
VPY="$VENV/bin/python"
LANGS="en ko"
ONEDIR=""
[ "${1:-}" = "onedir" ] && ONEDIR=1

echo "[1/7] Checking tools..."
command -v "$PY" >/dev/null || { echo "ERROR: $PY not found (need Python 3.10+)"; exit 1; }
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' || { echo "ERROR: Python 3.10+ required"; exit 1; }

echo "[2/7] Creating / updating the venv ($VENV)..."
if [ ! -x "$VPY" ]; then
  if [ "$(uname)" = "Linux" ]; then
    # PyGObject / WebKit2GTK come from the OS, so the venv must see system packages.
    "$PY" -m venv --system-site-packages "$VENV"
  else
    "$PY" -m venv "$VENV"
  fi
fi
# Platform-specific packages are selected by environment markers inside the requirements files.
"$VPY" -m pip install --quiet --disable-pip-version-check -r src/requirements-dev.txt

echo "[3/7] Recording checksums of hgrtool-local/ ..."
"$VPY" src/tools/checksum_tree.py write hgrtool-local work/hgrtool-local.sha256

echo "[4/7] Running unit tests..."
( cd src && "$VPY" -m pytest -q )

mkdir -p dist
export HGRTOOL_ONEDIR="$ONEDIR"

exe_for() {   # $1 = language -> path of that language's executable
  local name="hgrtool"; [ "$1" != "en" ] && name="hgrtool-$1"
  if [ "$(uname)" = "Darwin" ]; then
    local app="HGRTool.app"; [ "$1" != "en" ] && app="HGRTool-$1.app"
    echo "dist/$app/Contents/MacOS/$name"
  elif [ -n "$ONEDIR" ]; then echo "dist/$name/$name"
  else echo "dist/$name"; fi
}

echo "[5/7] Building each language version..."
for L in $LANGS; do
  echo "   - $L: generating the web bundle"
  "$VPY" src/tools/patch_web.py --lang "$L"
  echo "   - $L: PyInstaller"
  HGRTOOL_LANG="$L" "$VPY" -m PyInstaller --noconfirm --clean --log-level WARN \
    --distpath dist --workpath "work/pyi/$L" src/hgrtool.spec
done
cp LICENSES.txt dist/LICENSES.txt
cp LICENSE dist/LICENSE.txt

echo "[6/7] Smoke-testing each version (a window opens for a few seconds)..."
for L in $LANGS; do
  EXE="$(exe_for "$L")"
  echo "   - $L: $EXE"
  rm -f "work/selftest-dist-$L.txt"
  HGRTOOL_DATA="$PWD/work/selftest-data-$L" "$EXE" --selftest --selftest-out "$PWD/work/selftest-dist-$L.txt" || true
  cat "work/selftest-dist-$L.txt"
  grep -q "RESULT: OK" "work/selftest-dist-$L.txt"
done

echo "[7/7] Verifying hgrtool-local/ is unchanged..."
"$VPY" src/tools/checksum_tree.py check hgrtool-local work/hgrtool-local.sha256

echo; echo "BUILD OK:"
for L in $LANGS; do echo "   $(exe_for "$L")"; done
