# BUILD (빌드)

**한국어** | [English](BUILD_en.md)

## 빠른 시작 (Windows)

```
build_all.bat            # 단일 파일 exe -> dist\hgrtool.exe (영어), dist\hgrtool-ko.exe (한국어)
build_all.bat onedir     # 폴더 빌드     -> dist\hgrtool\hgrtool.exe, dist\hgrtool-ko\hgrtool-ko.exe (시작이 더 빠름)
```

`build_all.bat`은 **두 언어 버전을 모두** 빌드하며, 실패하면 첫 번째 실패 지점에서 알기 쉬운 메시지와 함께 멈춥니다.

1. `py` 런처로 Python 3.13을 쓸 수 있는지 확인
2. `.venv`를 만들고 `src\requirements-dev.txt`(`requirements.txt` 포함)에 고정된 패키지를 설치
3. `hgrtool-local\`의 SHA-256 체크섬 기록
4. 단위 테스트(pytest) 실행
5. 언어(`en`, `ko`)마다 `src\web\<언어>\`(`hgrtool-local\`을 패치하고 `ko`는 번역까지 한 사본)를 만들고,
   PyInstaller로 exe를 `dist\`에 빌드
6. 각 exe를 `--selftest`로 실행(창이 몇 초 동안 뜸)하여 `RESULT: OK`를 확인
7. `hgrtool-local\`이 바뀌지 않았는지 다시 확인

완성된 앱은 `dist\hgrtool.exe`(영어)와 `dist\hgrtool-ko.exe`(한국어)이고 `dist\LICENSE.txt`,
`dist\LICENSES.txt`가 함께 만들어집니다. 휴대용이므로 어디로 복사해도 됩니다. 처음 실행하면 앱 옆에
`hgrtool-data\`(설정)를 만들고, 그 폴더에 쓸 수 없으면 `%APPDATA%\HGRTool`을 씁니다. 두 앱은 같은 설정 폴더
이름을 쓰므로 같은 폴더에 두면 설정을 함께 씁니다.

## 필요한 도구

| 도구 | 버전 | 비고 |
|---|---|---|
| Python | 3.13 (python.org), `py` 런처 포함 | Microsoft Store 버전이나 Anaconda는 안 됨 |
| 인터넷 | 첫 빌드에만 | PyPI에서 wheel을 `.venv`로 내려받음 |
| WebView2 런타임 | 현재 버전 아무거나 | Windows 11에는 기본 설치. *실행*(과 스모크 테스트)에 필요 |

Python 패키지(앱은 `src/requirements.txt`, 빌드/테스트 도구는 `src/requirements-dev.txt`에 버전 고정, `.venv`
안에만 설치): pywebview, pythonnet(+clr_loader, cffi, pycparser), bottle, proxy_tools, pyinstaller(+hooks,
altgraph, pefile, pywin32-ctypes, packaging, setuptools), pytest(+pluggy, iniconfig, colorama, Pygments).
Node.js도 C 컴파일러도 필요 없습니다.

## 가상 환경 (venv)

모든 Python 작업은 `.venv`(프로젝트 루트)를 씁니다. 전역에는 아무것도 설치하지 않습니다.

```
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r src\requirements-dev.txt     # Windows (앱 + 빌드/테스트 도구)
.venv\Scripts\python.exe -m pytest -q                                   # src\에서 실행
.venv\Scripts\python.exe src\tools\patch_web.py --lang en               # 또는 --lang ko
.venv\Scripts\python.exe src\run_hgrtool.py [file.hgr]                  # 소스에서 실행
```

`build_all.bat`은 인덱스를 PyPI로만 고정하는 `.venv\pip.ini`를 만듭니다. (제작자의 컴퓨터에서는 전역 pip 설정에
접속할 수 없는 추가 인덱스가 있어 설치가 실패했습니다.) `.venv`를 지우면 처음부터 다시 시작합니다.

의존성을 올리려면 venv에서 `pip install -U <패키지>`를 하고 테스트한 뒤 `src/requirements.txt` /
`src/requirements-dev.txt`의 고정 버전을 고치세요(`pip freeze`로 설치된 버전을 볼 수 있습니다).

## 빌드하지 않고 실행

```
.venv\Scripts\python.exe src\tools\patch_web.py --lang ko
set HGRTOOL_LANG=ko
.venv\Scripts\python.exe src\run_hgrtool.py work\sample.hgr
```
`HGRTOOL_LANG`(기본값 `en`)은 소스 실행이 생성된 번들 `src\web\<언어>\` 중 무엇을 쓸지 정합니다.
옵션: `--debug`(오른쪽 클릭 메뉴 + 웹 인스펙터), `--selftest`, `--version`.
개발 실행은 데이터를 `src\hgrtool-data\`에 둡니다(`HGRTOOL_DATA` 환경 변수로 바꿀 수 있음).

## 언어

각 빌드에는 정확히 한 언어만 들어 있습니다. 한국어 빌드가 다른 점은 번역된 페이지
(`src/tools/translations.py`), Python 쪽 몇몇 텍스트(`src/hgrtool/strings.py`), 그리고 exe 이름뿐입니다.
다른 언어를 추가하려면 `ARCHITECTURE.md` 3.1절을 보세요. 한국어 표현을 고치려면 `translations.py`(대화상자/확인
문구는 `strings.py`)를 고치고 다시 빌드하면 됩니다. 번역하기로 한 문자열이 `hgrtool-local/`에서 사라지면
빌드가 실패합니다.

## macOS와 Linux (아직 테스트하지 않음)

`build_all.sh`는 두 언어를 포함해 Windows 스크립트와 같은 순서로 동작합니다. 아직 Mac이나 Linux에서 실행해
보지 않았으므로 사소한 수정이 필요할 수 있습니다. 문제가 생기면 알려 주세요.

**macOS**: Python 3.10 이상(python.org 또는 Homebrew)을 설치하고 `./build_all.sh`를 실행하세요. 결과물은
`dist/HGRTool.app`과 `dist/HGRTool-ko.app`입니다. 서명하지 않은 앱은 Gatekeeper가 막으므로 처음에는
오른쪽 클릭 → 열기를 하세요. `src/res/icon.icns`는 아직 없어서 아이콘을 추가하기 전까지 기본 아이콘이 쓰입니다.

**Linux**: 먼저 시스템 패키지를 설치한 뒤(Debian/Ubuntu 이름이며 배포판마다 다름) `./build_all.sh`를 실행하세요.
```
sudo apt install python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
                 libgirepository1.0-dev libcairo2-dev pkg-config build-essential
```
스크립트는 PyGObject가 보이도록 `--system-site-packages`로 venv를 만듭니다. 결과물은 `dist/hgrtool`과
`dist/hgrtool-ko`입니다. 실행하는 컴퓨터에도 WebKitGTK가 설치되어 있어야 하고, 한국어판에는 한글 글꼴(예: Noto Sans
CJK KR)이 설치되어 있어야 합니다. PyInstaller로 GTK/WebKit을 묶으려면 추가 훅이 필요할 수 있습니다. exe가
시작되지 않으면 venv에서 `python src/run_hgrtool.py`를 실행해 앱 자체는 동작하는지 확인하세요.

## 문제 해결

- **"Python 3.13을 찾을 수 없음"**: python.org에서 설치하고 "py launcher"를 선택하세요. `py -3.13 --version`이 동작해야 합니다.
- **다른 호스트에 대해 `getaddrinfo failed`로 pip 실패**: 전역 pip 설정이 접속할 수 없는 인덱스를 가리킵니다.
  스크립트가 만드는 venv의 `pip.ini`가 이를 덮어씁니다. venv를 직접 만들었다면 그 파일을 추가하세요.
- **`PATCH ERROR: anchor expected 1x but found 0x`**: `hgrtool-local/`이 패처가 기준으로 삼은 버전과
  다릅니다. `src/tools/patch_web.py`의 해당 패치(또는 `translations.py`의 문자열)를 고치세요.
- **빈 창 / "WebView2 not found"**: Microsoft의 Evergreen WebView2 런타임을 설치하세요.
- **백신이 exe를 의심함**: PyInstaller 단일 파일 exe는 가끔 오탐됩니다. `build_all.bat onedir`을 쓰거나
  exe에 코드 서명을 하세요(여기서는 설정하지 않음).
- **처음 시작이 느림 (1-2초)**: 단일 파일 빌드는 실행할 때 임시 폴더에 풀기 때문입니다. 더 빠른 시작에는
  `onedir`을 쓰세요.
- **편집한 뒤 닫기 버튼이 안 되는 것 같음**: "저장하지 않은 변경 사항" 확인 창입니다. 응답하세요.
- **한글이 네모로 보임**: 시스템에 한글 글꼴이 없는 경우입니다(Windows와 macOS에서는 정상 설치됨, Linux는 위 참조).
- **스모크 테스트 실패**: `work\selftest-dist-en.txt` 또는 `work\selftest-dist-ko.txt`를 읽으세요. 각 줄에
  실패한 검사 이름이 있습니다.

## 포함되지 않은 것

코드 서명, 공증(notarization), 설치 프로그램, 자동 업데이트. `src/res/icon.ico`는 원본의 32×32 파비콘입니다.
작업 표시줄 아이콘을 선명하게 하려면 더 큰 다중 크기 아이콘으로 바꾸세요.
