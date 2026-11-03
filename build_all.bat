@echo off
rem ============================================================================
rem  HGRTool Desktop - build everything and put the apps in dist\
rem
rem  Builds two versions:   dist\hgrtool.exe     English UI
rem                         dist\hgrtool-ko.exe  Korean UI
rem
rem  Usage:  build_all.bat            single-file exes
rem          build_all.bat onedir     folder builds (dist\hgrtool\, dist\hgrtool-ko\), start faster
rem
rem  All Python work happens in the project venv (.venv). Nothing is installed globally.
rem  See BUILD.md for details.
rem ============================================================================
setlocal
cd /d "%~dp0"

set "PYVER=3.13"
set "VENV=%CD%\.venv"
set "VPY=%VENV%\Scripts\python.exe"
set "LANGS=en ko"
set "ONEDIR="
if /i "%~1"=="onedir" set "ONEDIR=1"

echo [1/7] Checking tools...
where py >nul 2>nul || goto :no_py
py -%PYVER% -c "import sys" >nul 2>nul || goto :no_py

echo [2/7] Creating / updating the venv (%VENV%)...
if not exist "%VPY%" (
    py -%PYVER% -m venv "%VENV%" || goto :fail
)
rem Use only PyPI for this venv (a global pip.ini may point at unreachable extra indexes).
if not exist "%VENV%\pip.ini" (
    >"%VENV%\pip.ini" echo [global]
    >>"%VENV%\pip.ini" echo index-url = https://pypi.org/simple
    >>"%VENV%\pip.ini" echo extra-index-url =
    >>"%VENV%\pip.ini" echo trusted-host =
)
"%VPY%" -m pip install --quiet --disable-pip-version-check -r src\requirements-dev.txt || goto :fail

echo [3/7] Recording checksums of hgrtool-local\ ...
"%VPY%" src\tools\checksum_tree.py write hgrtool-local work\hgrtool-local.sha256 || goto :fail

echo [4/7] Running unit tests...
pushd src
"%VPY%" -m pytest -q || (popd & goto :fail)
popd

if not exist dist mkdir dist
if defined ONEDIR (set "HGRTOOL_ONEDIR=1") else (set "HGRTOOL_ONEDIR=")

echo [5/7] Building each language version...
for %%L in (%LANGS%) do (
    call :build_lang %%L || goto :fail
)
copy /y LICENSES.txt dist\LICENSES.txt >nul
copy /y LICENSE dist\LICENSE.txt >nul

echo [6/7] Smoke-testing each version (a window opens for a few seconds)...
for %%L in (%LANGS%) do (
    call :smoke_lang %%L || goto :fail
)

echo [7/7] Verifying hgrtool-local\ is unchanged...
"%VPY%" src\tools\checksum_tree.py check hgrtool-local work\hgrtool-local.sha256 || goto :fail

echo.
echo BUILD OK:
for %%L in (%LANGS%) do call :print_exe %%L
exit /b 0

:print_exe
call :exe_for %1
echo    %EXE%
exit /b 0

rem ---------------------------------------------------------------------------
:exe_for
rem  %1 = language. Sets EXE to the path of that language's executable.
setlocal EnableDelayedExpansion
if "%~1"=="en" (set "NAME=hgrtool") else (set "NAME=hgrtool-%~1")
if defined ONEDIR (set "P=dist\!NAME!\!NAME!.exe") else (set "P=dist\!NAME!.exe")
endlocal & set "EXE=%P%"
exit /b 0

:build_lang
echo    - %1: generating the web bundle (patched copy of hgrtool-local\)
"%VPY%" src\tools\patch_web.py --lang %1 || exit /b 1
echo    - %1: PyInstaller
set "HGRTOOL_LANG=%1"
"%VPY%" -m PyInstaller --noconfirm --clean --log-level WARN --distpath dist --workpath work\pyi\%1 src\hgrtool.spec || exit /b 1
set "HGRTOOL_LANG="
call :exe_for %1
if not exist "%EXE%" exit /b 1
exit /b 0

:smoke_lang
call :exe_for %1
echo    - %1: %EXE%
set "HGRTOOL_DATA=%CD%\work\selftest-data-%1"
if exist work\selftest-dist-%1.txt del work\selftest-dist-%1.txt
start "" /wait "%EXE%" --selftest --selftest-out "%CD%\work\selftest-dist-%1.txt"
set "HGRTOOL_DATA="
if not exist work\selftest-dist-%1.txt goto :selftest_fail
type work\selftest-dist-%1.txt
findstr /c:"RESULT: OK" work\selftest-dist-%1.txt >nul || goto :selftest_fail
exit /b 0

:selftest_fail
echo ERROR: the smoke test failed - see work\selftest-dist-%1.txt
exit /b 1

:no_py
echo ERROR: Python %PYVER% (python.org) was not found. Install it from https://www.python.org/downloads/
echo        and make sure the "py" launcher is installed ^(py -%PYVER% must work^).
exit /b 1

:fail
echo.
echo BUILD FAILED.
exit /b 1
