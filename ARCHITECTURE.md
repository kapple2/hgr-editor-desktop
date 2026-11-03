# ARCHITECTURE (구조)

**한국어** | [English](ARCHITECTURE_en.md)

HGRTool Desktop은 원본 HGRTool 웹 편집기(`hgrtool-local/`, fadden 제작)를 네이티브 창으로 감쌉니다.
편집기의 HTML/JS는 그대로 재사용하고, Python이 창, 네이티브 파일 대화상자, 설정 파일, 저장하지 않은 변경 사항
확인을 맡습니다. UI에는 항상 보이는 색상 팔레트가 하나 추가되었습니다. 앱은 같은 코드로 영어와 한국어 두
가지 언어로 빌드됩니다.

## 1. 저장소 구성

```
proj2-apple2-hgr-editor/
├─ README.md README_en.md             개요 (한국어 기본 / 영어)
├─ ARCHITECTURE.md ARCHITECTURE_en.md 이 문서
├─ BUILD.md BUILD_en.md               빌드 방법
├─ LICENSE LICENSES.txt               Apache 2.0 전문, 외부 구성 요소 고지 (dist/에 복사됨)
├─ build_all.bat / build_all.sh       두 언어를 한 번에 dist/로 빌드
├─ hgrtool-local/                     원본 사본. 절대 수정하지 않음 (빌드가 체크섬으로 확인)
├─ docs/                              README에 쓰는 스크린샷
├─ .venv/                             프로젝트 가상 환경 (커밋하지 않음)
├─ src/
│  ├─ requirements.txt                고정 버전의 런타임 의존성 (exe에 포함됨)
│  ├─ requirements-dev.txt            빌드/테스트 도구 (PyInstaller, pytest). requirements.txt 포함
│  ├─ pytest.ini                      테스트 설정
│  ├─ run_hgrtool.py                  PyInstaller 진입점
│  ├─ hgrtool.spec                    PyInstaller spec (한 번에 한 언어, onefile 또는 onedir)
│  ├─ hgrtool/                        Python 애플리케이션 패키지
│  │  ├─ app.py                       main(): 인자, 창, 서버, 닫기 확인
│  │  ├─ bridge.py                    class Api: JavaScript에서 호출하는 함수들
│  │  ├─ server.py                    번들된 웹 파일을 제공하는 루프백 HTTP 서버
│  │  ├─ settings.py                  JSON 설정 파일
│  │  ├─ paths.py                     번들 리소스와 데이터 폴더 위치
│  │  ├─ strings.py                   Python 쪽에서 보여 주는 텍스트 (언어별)
│  │  └─ selftest.py                  `--selftest`: 실제 창에서 도는 자동 스모크 테스트
│  ├─ web_overlay/                    웹 앱에 더한 부분
│  │  ├─ shim.js                      File System Access 에뮬레이션, 설정 저장소, 변경 여부 보고
│  │  ├─ palette.css                  작아진 왼쪽 막대와 팔레트 스타일
│  │  └─ palette.html                 팔레트 패널 마크업
│  ├─ tools/
│  │  ├─ patch_web.py                 hgrtool-local/ + 오버레이로 src/web/<언어>/ 생성 (표준 라이브러리만 사용)
│  │  ├─ translations.py              patch_web.py가 적용하는 한국어 문자열 표
│  │  └─ checksum_tree.py             hgrtool-local/이 바뀌지 않았음을 증명
│  ├─ web/en/  web/ko/                생성되는 번들 (패치된 사본). 각 exe에 하나씩 포함됨
│  ├─ res/icon.ico                    exe 아이콘 (원본 파비콘)
│  └─ tests/                          pytest 단위 테스트
├─ work/                              임시 작업물: 체크섬, 셀프 테스트 결과
└─ dist/                              빌드 결과: hgrtool.exe (영어), hgrtool-ko.exe (한국어), 라이선스
```

## 2. 실행 시 동작

```
 hgrtool.exe (또는 hgrtool-ko.exe)를 더블클릭
   │  PyInstaller 부트로더가 임시 폴더에 풀고(onefile) Python을 시작
   ▼
 app.main()
   ├─ data_dir()             <exe 폴더>/hgrtool-data, 쓸 수 없으면 OS 사용자 설정 폴더
   ├─ Settings(settings.json)
   ├─ WebServer(web/).start()      http://127.0.0.1:<임의 포트>/   (스레드)
   ├─ Api(settings, 명령줄 파일)    (js_api: JS <-> Python 브리지)
   ├─ webview.create_window(제목, server.url, js_api=api, 화면에 맞춘 크기)
   ├─ window.events.closing += 닫기 핸들러
   └─ webview.start()        시스템 웹 뷰(WebView2 / WKWebView / WebKitGTK)를 쓰는 네이티브 창
```

언어는 빌드할 때 정해집니다. 번들의 `web/lang.txt`에 `en` 또는 `ko`가 적혀 있고, Python 쪽(`strings.py`)이
이를 읽어 몇 안 되는 텍스트(창 제목, 닫기 확인 문구, 파일 대화상자 필터)를 고릅니다.

### 2.1 페이지
창은 루프백 서버에서 `hgrtool.html`을 불러옵니다. 서버는 번들된 `web/` 폴더 아래의 파일만 제공하고,
127.0.0.1에만 바인딩하며, 다른 `Host` 헤더는 거부하고(DNS 리바인딩 방지), 경로 탈출과 GET이 아닌
메서드도 거부합니다. 또 `/settings.js`를 동적으로 만들어 편집기 스크립트가 실행되기 *전에* 저장된 설정을
`window.__hgrInitialSettings`에 넣어 줍니다. (포트가 매번 바뀌면 브라우저 출처(origin)도 매번 달라져
`localStorage`가 유지되지 않기 때문입니다.)

### 2.2 File System Access shim (`web_overlay/shim.js`)
편집기는 `showOpenFilePicker()` / `showSaveFilePicker()`와 `handle.createWritable()`로 파일을 열고 저장합니다.
shim은 이 함수들을 Python 브리지 위에 정의하므로 편집기의 열기/저장 코드는 **그대로** 동작합니다.

| 편집기가 호출 | shim이 하는 일 |
|---|---|
| `showOpenFilePicker()` | `api.open_dialog()` → 네이티브 대화상자 → `getFile()`을 가진 핸들 |
| `showSaveFilePicker({suggestedName})` | `api.save_dialog(name)` → 네이티브 대화상자. 취소하면 `AbortError` |
| `handle.createWritable()` → `truncate/write/close` | 메모리에 모았다가 `close()`에서 `api.write_file(path, base64)` 호출 |

데이터는 base64로 브리지를 건너갑니다(파일은 8KB). shim은 `localStorage`를 대신하는 동기식 설정 객체
`window.__hgrStore`(변경 사항은 `api.save_settings()`로 기록), 시작 시 명령줄 파일 열기, 브라우저 컨텍스트
메뉴 차단(`--debug` 제외), 그리고 300ms마다 `api.set_dirty()`로 저장하지 않은 편집이 있는지 보고하는
기능도 제공합니다.

### 2.3 Python 브리지 (`bridge.py`)
JS에서 호출 가능한 공개 메서드: `open_dialog`, `save_dialog`, `write_file`, `save_settings`,
`get_startup_files`, `set_dirty`. 이름이 `_`로 시작하는 멤버는 노출되지 않습니다.

보안 규칙: `write_file`은 이 프로세스가 현재 세션에서 네이티브 대화상자나 명령줄로 직접 받은 경로(`_allowed`)에만
씁니다. 따라서 페이지가 탈취되어도 임의의 파일을 쓸 수 없습니다. 쓰기는 원자적(임시 파일 + 이름 변경)이며
실패하면 직접 쓰기로 대체합니다.

### 2.4 설정과 데이터 폴더
`<exe 폴더>/hgrtool-data/settings.json`(휴대용). 이 폴더에 쓸 수 없으면 `%APPDATA%\HGRTool`,
`~/Library/Application Support/HGRTool`, `~/.config/hgrtool` 중 해당 OS 위치를 씁니다. `HGRTOOL_DATA`
환경 변수로 위치를 바꿀 수 있습니다(테스트용). 알려진 키(`clipXferMode`, `colorSwatchClose`, `lastDir`)만 길이
제한과 함께 저장하며, 손상된 파일은 무시합니다. 영어판과 한국어판 실행 파일은 같은 폴더 이름을 쓰므로 같은
위치에 두면 하나의 설정 파일을 공유합니다.

### 2.5 저장하지 않은 변경 사항 확인
창의 `closing` 이벤트 핸들러는 `api._dirty`가 참이면 네이티브 확인 창을 띄우고, 닫기를 취소하려면 `False`를
반환합니다. 핸들러는 `window.evaluate_js()`를 호출하는 대신 **페이지가 보내 주는 플래그를 읽습니다**. 닫는 중에
페이지로 호출하면 UI 스레드가 멈춥니다(실제로 창이 "응답 없음"으로 멈추는 것을 확인했습니다).

## 3. 빌드 시 패치 (`src/tools/patch_web.py`)

언어마다 한 번씩 실행합니다. `patch_web.py --lang en|ko`는 `hgrtool-local/`을 읽어 `src/web/<언어>/`에
쓰며, 원본 폴더에는 절대 쓰지 않습니다. 모든 패치는 정확한 문자열 치환이고 기대 출현 횟수가 정해져 있어,
횟수가 다르면 빌드가 중단됩니다(원본이 바뀌어도 조용히 앱이 망가지지 않습니다). 패치 목록:

| # | 변경 | 이유 |
|---|---|---|
| P1 | 편집기 스크립트 앞에 `<script src="settings.js">`와 `shim.js` 추가 | 설정과 shim을 먼저 로드 |
| P2 | `localStorage.x` → `window.__hgrStore.x` (4곳) | localStorage 대신 설정 파일 |
| P3 | `#hgr-color-body` / `#hgr-dither-body`를 색 대화상자에서 왼쪽 막대의 `#palette-panel`로 이동 | 항상 보이는 팔레트 (편집기는 여전히 이 id에 견본을 만듦) |
| P4 | `handleSwatchClick`: "대화상자 닫기" 분기 제거 | 닫을 대화상자가 없음 |
| P5 | `handleSelectColor()`가 팔레트로 스크롤 | 아래 막대의 "현재 색" 버튼이 여전히 의미 있게 동작 |
| P6 | 색 선택(Choose Color) 버튼 숨김 (편집기의 리스너가 붙도록 숨겨진 껍데기는 남김) | 팝업 진입점 제거 |
| P7 | "견본 클릭 시 색 대화상자 닫기" 설정 숨김 (요소는 유지) | 더 이상 의미 없음. `Settings`가 그 요소를 읽음 |
| P8 | `onColorChanged()`가 큰 현재 색 상자도 다시 그림 | 현재 색 표시 |
| P10 | 정보 창에 `(desktop <버전>)` 표시 | 래퍼 버전 확인 |
| P11 | `window.__hgr = {editor, picker, isDirty}` 노출 | 변경 여부 보고와 셀프 테스트 (편집기가 IIFE 안에 있음) |

(캔버스 크기를 바꾸는 P9는 CSS 축소만으로 견본이 잘 보여 필요 없게 되었습니다.)
`editor.css`에는 `web_overlay/palette.css`가 덧붙고, `palette.html`은 왼쪽 막대에 삽입됩니다.

### 3.1 번역 (한국어 빌드)
위 패치 뒤에 `patch_web.py --lang ko`가 `src/tools/translations.py`의 표를 패치된 페이지와 `shim.js`에
적용합니다. 보이는 모든 레이블, 툴팁, 대화상자 텍스트, 편집기 코드가 띄우는 메시지(`confirm()` 질문 포함)를
다루는 정확한 문자열 치환 약 85개입니다. 항목마다 기대 횟수가 있어, 대상 문자열이 없어지거나 바뀌면 영어가
남지 않고 빌드가 실패합니다. 한국어 빌드는 `<html lang="ko">`로 바꾸고, 한글 글꼴(맑은 고딕, Apple SD Gothic Neo,
Noto Sans CJK KR)을 고르며 긴 낱말이 들어가도록 버튼 글자를 조금 줄이는 CSS도 덧붙입니다.
일부러 영어로 둔 것: 정보 창의 법적 고지, 운영체제가 주는 기술적인 오류 문구.

다른 언어를 추가하려면 `translations.py`의 `LANGUAGES`에 항목을, `hgrtool/strings.py`에 표를 추가하고
빌드 스크립트의 `LANGS`에 언어 코드를 넣으면 됩니다.

## 4. 팔레트

왼쪽 막대는 작아진 스크롤 열이 되었습니다. 도구(버튼 10개), 옵션(버튼 4개), 그리고 **색상**: 큰 현재 색 상자,
단색 10개(5개씩 2줄), 디더 패턴 108개(11 × 10). 견본을 클릭하면 편집기의 기존 `handleSwatchClick` →
`setColor` → `onColorChanged`가 실행되어 강조 표시(흰 테두리), 현재 패턴, 두 표시(큰 상자와 아래 막대의
"현재 색" 상자)가 한꺼번에 갱신됩니다. `currentPat`만 바뀌므로 진행 중인 선택, 클립, 글자는 영향받지 않습니다.
색 선택기의 상태는 전역이라 이미지를 바꿔도 색이 유지됩니다. 창이 너무 낮으면 왼쪽 막대가 스크롤됩니다.

## 5. 테스트

- `src/tests` (`.venv` 안에서 pytest): 패처(앵커, 원본에 쓰지 않음, 두 언어, 한국어 문자열 존재와 영어 레이블
  제거), 브리지(경로 승인, 바이트 단위 동일한 왕복, 잘못된 입력), 문자열 표, 서버(경로 탈출, Host 검사,
  메서드), 설정과 데이터 폴더 대체 경로.
- `hgrtool --selftest [--selftest-out 파일]`: 실제 exe의 실제 창에서 실행됩니다. UI 언어, 팔레트의 존재와
  동작, shim을 통한 열기 → 저장의 바이트 동일성, 설정 저장, 닫기 확인 로직, 쓰기 승인 규칙을 검사합니다.
  `build_all`이 빌드된 각 exe에 대해 실행합니다.

## 6. 플랫폼 참고

| | 창 | 비고 |
|---|---|---|
| Windows | WebView2 (pythonnet 경유) | WebView2 런타임 필요 (Windows 11에는 기본 설치) |
| macOS | WKWebView (pyobjc) | 빌드 결과 `HGRTool.app` / `HGRTool-ko.app`. **테스트하지 않음** |
| Linux | WebKitGTK (PyGObject) | 시스템 패키지 필요. **테스트하지 않음** |
