"""UI translations applied at build time (exact-string replacements, like the other patches).

Every entry states how many times its anchor must occur in the patched page, so an upstream
change cannot silently leave a string untranslated or mistranslated: the build fails instead.
English is the original text, so it needs no table.

To add a language: add an entry to LANGUAGES with html / shim lists (and optional css), and a
matching table in src/hgrtool/strings.py.
"""


def _t(old, new, count=1):
    return {"name": old.strip()[:40], "old": old, "new": new, "count": count}


# ------------------------------------------------------------------ Korean: hgrtool.html ---
KO_HTML = [
    _t('<html lang="en">', '<html lang="ko">'),

    # Top bar: labels
    _t('<i class="fa-solid fa-file-circle-plus"></i>New', '<i class="fa-solid fa-file-circle-plus"></i>새 이미지'),
    _t('<i class="fa-solid fa-upload"></i>Open', '<i class="fa-solid fa-upload"></i>열기'),
    _t('<i class="fa-solid fa-floppy-disk"></i>Save', '<i class="fa-solid fa-floppy-disk"></i>저장'),
    _t('<i class="fa-solid fa-file-export"></i>Save As', '<i class="fa-solid fa-file-export"></i>다른 이름'),
    _t('<i class="fa-solid fa-circle-xmark"></i>Close', '<i class="fa-solid fa-circle-xmark"></i>닫기'),
    _t('<i class="fa-solid fa-scissors"></i>Cut', '<i class="fa-solid fa-scissors"></i>잘라내기'),
    _t('<i class="fa-solid fa-copy"></i>Copy', '<i class="fa-solid fa-copy"></i>복사'),
    _t('<i class="fa-solid fa-paste"></i>Paste', '<i class="fa-solid fa-paste"></i>붙여넣기'),
    _t('<i class="fa-solid fa-rotate-left"></i>Undo', '<i class="fa-solid fa-rotate-left"></i>실행 취소'),
    _t('<i class="fa-solid fa-rotate-right"></i>Redo', '<i class="fa-solid fa-rotate-right"></i>다시 실행'),
    # Top bar: tooltips
    _t('Create blank image.', '빈 이미지를 만듭니다.'),
    _t('Open one or more images.', '이미지를 하나 이상 엽니다.'),
    _t('Save image (Ctrl+S).', '이미지를 저장합니다 (Ctrl+S).'),
    _t('Save image with a new name.', '새 이름으로 이미지를 저장합니다.'),
    _t('Close image.', '이미지를 닫습니다.'),
    _t('Cut region (Ctrl+X).', '영역을 잘라냅니다 (Ctrl+X).'),
    _t('Copy region (Ctrl+C).', '영역을 복사합니다 (Ctrl+C).'),
    _t('Paste clipping (Ctrl+V or Enter).', '클립을 붙여넣습니다 (Ctrl+V 또는 Enter).'),
    _t('Undo action (Ctrl+Z).', '실행을 취소합니다 (Ctrl+Z).'),
    _t('Redo action (Ctrl+Y).', '취소한 실행을 다시 합니다 (Ctrl+Y).'),

    # Right bar, bottom bar
    _t('<div class="right-header">Images</div>', '<div class="right-header">이미지</div>'),
    _t('cursor <span class="mono-info">', '커서 <span class="mono-info">'),
    _t('rect <span class="mono-info">', '영역 <span class="mono-info">'),
    _t('size <span class="mono-info">', '크기 <span class="mono-info">'),
    _t('<label for="pictureScaleSlider">scale=</label>', '<label for="pictureScaleSlider">배율=</label>'),
    _t('<label for="useMono">Monochrome</label>', '<label for="useMono">흑백</label>'),
    _t('            Pattern\n            <button id="curcolor-button">',
       '            현재 색\n            <button id="curcolor-button">'),

    # Left bar
    _t('<div class="left-header1">Tools</div>', '<div class="left-header1">도구</div>'),
    _t('<i class="fa-solid fa-up-down-left-right"></i>Pan', '<i class="fa-solid fa-up-down-left-right"></i>이동'),
    _t('<i class="fa-solid fa-object-group"></i>Select', '<i class="fa-solid fa-object-group"></i>선택'),
    _t('<i class="fa-solid fa-pencil"></i>Scribble', '<i class="fa-solid fa-pencil"></i>자유 그리기'),
    _t('<i class="fa-solid fa-lines-leaning"></i>Line', '<i class="fa-solid fa-lines-leaning"></i>선'),
    _t('<i class="fa-solid fa-pen-to-square"></i>Rect Frame', '<i class="fa-solid fa-pen-to-square"></i>사각 테두리'),
    _t('<i class="fa-solid fa-square-full"></i>Rect', '<i class="fa-solid fa-square-full"></i>사각형'),
    _t('<i class="fa-solid fa-circle-notch"></i>Ellipse Frame', '<i class="fa-solid fa-circle-notch"></i>타원 테두리'),
    _t('<i class="fa-solid fa-circle"></i>Ellipse', '<i class="fa-solid fa-circle"></i>타원'),
    _t('<i class="fa-solid fa-keyboard"></i>Text', '<i class="fa-solid fa-keyboard"></i>글자'),
    _t('<i class="fa-solid fa-fill-drip"></i>Fill', '<i class="fa-solid fa-fill-drip"></i>채우기'),
    _t('<div class="left-header2">Configuration</div>', '<div class="left-header2">옵션</div>'),
    _t('<i class="fa-solid fa-font"></i>Choose Font', '<i class="fa-solid fa-font"></i>글꼴 선택'),
    _t('<i class="fa-solid fa-grip-lines-vertical"></i>Line Width', '<i class="fa-solid fa-grip-lines-vertical"></i>선 굵기'),
    _t('<i class="fa-solid fa-gear"></i>Settings', '<i class="fa-solid fa-gear"></i>설정'),
    _t('<i class="fa-solid fa-question"></i>About', '<i class="fa-solid fa-question"></i>정보'),
    # Palette panel (added by this project)
    _t('<div class="left-header3">Color</div>', '<div class="left-header3">색상</div>'),
    _t('title="Current color"', 'title="현재 색상"'),

    # Line width dialog
    _t('>Thin</button>', '>가늘게</button>'),
    _t('>Thick</button>', '>굵게</button>'),
    _t('>Applesoft Thin</button>', '>Applesoft 가늘게</button>'),
    _t('<button id="style-picker-close" class="modal-close">Close</button>',
       '<button id="style-picker-close" class="modal-close">닫기</button>'),

    # Font dialog
    _t('<div class="fp-title">\n            Choose Font\n        </div>',
       '<div class="fp-title">\n            글꼴 선택\n        </div>'),
    _t('Bitmap<br/>font', '비트맵<br/>글꼴'),
    _t('(uses default hi-res font)', '(기본 HGR 글꼴 사용)'),
    _t('Browser<br/>font', '브라우저<br/>글꼴'),
    _t('Style (blank ok):', '스타일 (비워도 됨):'),
    _t('Font family:', '글꼴 이름:'),
    _t('Size (in px, 4-200):', '크기 (px, 4-200):'),
    _t('<button id="font-picker-ok" class="modal-close">OK</button>',
       '<button id="font-picker-ok" class="modal-close">확인</button>'),

    # Text entry dialog
    _t('Enter text:', '텍스트 입력:'),
    _t('<button id="text-entry-ok" class="modal-close">OK</button>',
       '<button id="text-entry-ok" class="modal-close">확인</button>'),

    # Settings dialog
    _t('<div id="settings-title">\n            Settings\n        </div>',
       '<div id="settings-title">\n            설정\n        </div>'),
    _t('Transfer mode for clippings (copy+paste, text)', '클립 전송 방식 (복사+붙여넣기, 글자)'),
    _t('for="setting-xfer-copy">Copy</label>', 'for="setting-xfer-copy">복사</label>'),
    _t('for="setting-xfer-merge">Merge</label>', 'for="setting-xfer-merge">병합</label>'),
    _t('<button id="settings-ok" class="modal-close">OK</button>',
       '<button id="settings-ok" class="modal-close">확인</button>'),

    # About dialog (the legal text itself stays in English)
    _t('Version <span id="about-version">', '버전 <span id="about-version">'),
    _t('The project is available on', '프로젝트 주소:'),
    _t('Legal stuff:', '법적 고지 (영문):'),
    _t('<button id="about-ok" class="modal-close">OK</button>',
       '<button id="about-ok" class="modal-close">확인</button>'),
    _t('" (desktop "', '" (데스크톱 "'),

    # Messages shown by the editor's code
    _t('`You have ${this.pictureList.length} images open.  Please` +',
       '`이미지가 ${this.pictureList.length}개 열려 있습니다.` +', count=3),
    _t('` close one before dragging more in.`', '` 이미지를 끌어 놓으려면 먼저 하나를 닫으세요.`'),
    _t('` close one before creating another.`', '` 새 이미지를 만들려면 먼저 하나를 닫으세요.`'),
    _t('` close one before opening another.`', '` 다른 이미지를 열려면 먼저 하나를 닫으세요.`'),
    _t('"File not recognized"', '"인식할 수 없는 파일입니다"'),
    _t('"No picture."', '"이미지가 없습니다."', count=2),
    _t("`Saved '${this.currentPicture.name}'`", "`'${this.currentPicture.name}' 파일을 저장했습니다`"),
    _t('"ERROR: save failed: "', '"오류: 저장하지 못했습니다: "'),
    _t('"Image saved"', '"이미지를 저장했습니다"'),
    _t('"ERROR: save-as failed: "', '"오류: 다른 이름으로 저장하지 못했습니다: "'),
    _t('confirm("The image has unsaved changes. Close it anyway?")',
       'confirm("저장하지 않은 변경 사항이 있습니다. 그래도 닫으시겠습니까?")'),
    _t('"Nothing is selected"', '"선택된 영역이 없습니다"'),
    _t('"Nothing has been cut or copied"', '"잘라내거나 복사한 내용이 없습니다"'),
]

# ------------------------------------------------------------------ Korean: shim.js ---
KO_SHIM = [
    _t('b.title = "Solid " + i;', 'b.title = "단색 " + i;'),
    _t('b.title = "Pattern " + i;', 'b.title = "패턴 " + i;'),
]

# ------------------------------------------------------------------ Korean: extra CSS ---
KO_CSS = """

/* ---- Korean build: Hangul-capable fonts and slightly smaller labels ---- */
body {
    font-family: "Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans CJK KR", "Noto Sans KR", "NanumGothic", Arial, sans-serif;
}
#topbar .icon-button { font-size: 14px; }
#leftbar .icon-button { font-size: 12px; }
"""

LANGUAGES = {
    "en": {"html": [], "shim": [], "css": ""},
    "ko": {"html": KO_HTML, "shim": KO_SHIM, "css": KO_CSS},
}
