import hashlib
from pathlib import Path

import pytest

import patch_web

PROJECT = Path(__file__).resolve().parents[2]
UPSTREAM = PROJECT / "hgrtool-local"
OVERLAY = PROJECT / "src" / "web_overlay"


def tree_hash(root: Path) -> dict:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


@pytest.mark.parametrize("lang", ["en", "ko"])
def test_build_leaves_upstream_untouched_and_applies_patches(tmp_path, lang):
    before = tree_hash(UPSTREAM)
    out = tmp_path / "web"
    patch_web.build(UPSTREAM, OVERLAY, out, lang)
    assert tree_hash(UPSTREAM) == before
    assert (out / "lang.txt").read_text().strip() == lang

    html = (out / "hgrtool.html").read_text(encoding="utf-8")
    assert '<script src="settings.js">' in html and '<script src="shim.js">' in html
    assert "localStorage.colorSwatchClose" not in html and "localStorage.clipXferMode" not in html
    assert html.count("window.__hgrStore.") == 4
    assert 'id="palette-panel"' in html
    # swatch containers exist exactly once, and now outside the dialog
    assert html.count('id="hgr-color-body"') == 1 and html.count('id="hgr-dither-body"') == 1
    dialog = html[html.index('<dialog id="color-picker-hgr"'):html.index("</dialog>", html.index('<dialog id="color-picker-hgr"'))]
    assert "hgr-color-body" not in dialog and "hgr-picker-close" in dialog
    assert "window.__hgr = {" in html
    assert (out / "shim.js").is_file() and (out / "fa" / "all.min.css").is_file()
    assert "#palette-panel" in (out / "editor.css").read_text(encoding="utf-8")


def test_missing_anchor_fails():
    with pytest.raises(patch_web.PatchError, match="expected 1x but found 0x"):
        patch_web.apply_patches("nothing here", [patch_web._p("x", "anchor", "y")])


def test_duplicate_anchor_fails():
    with pytest.raises(patch_web.PatchError, match="expected 1x but found 2x"):
        patch_web.apply_patches("anchor anchor", [patch_web._p("x", "anchor", "y")])


def test_refuses_to_write_into_upstream(tmp_path):
    with pytest.raises(patch_web.PatchError):
        patch_web.build(UPSTREAM, OVERLAY, UPSTREAM / "web")


def test_refuses_to_delete_foreign_output_dir(tmp_path):
    out = tmp_path / "web"
    out.mkdir()
    (out / "precious.txt").write_text("keep me")
    with pytest.raises(patch_web.PatchError):
        patch_web.build(UPSTREAM, OVERLAY, out)
    assert (out / "precious.txt").exists()


def test_korean_build_is_translated(tmp_path):
    out = tmp_path / "ko"
    patch_web.build(UPSTREAM, OVERLAY, out, "ko")
    html = (out / "hgrtool.html").read_text(encoding="utf-8")
    assert '<html lang="ko">' in html
    for ko in ("새 이미지", "열기", "저장", "잘라내기", "붙여넣기", "실행 취소", "도구", "자유 그리기",
               "색상", "글꼴 선택", "선 굵기", "정보", "흑백", "이미지를 저장했습니다"):
        assert ko in html, ko
    # visible English labels that must be gone
    for en in (">Open<", "</i>Open", "</i>Scribble", "</i>Ellipse", "Create blank image", "Monochrome</label>",
               "Nothing is selected", "Close it anyway?", "Enter text:"):
        assert en not in html, en
    assert "단색 " in (out / "shim.js").read_text(encoding="utf-8")
    assert "Malgun Gothic" in (out / "editor.css").read_text(encoding="utf-8")


def test_english_build_is_original_text(tmp_path):
    out = tmp_path / "en"
    patch_web.build(UPSTREAM, OVERLAY, out, "en")
    html = (out / "hgrtool.html").read_text(encoding="utf-8")
    assert "</i>Scribble" in html and "Close it anyway?" in html and "열기" not in html


def test_unknown_language_fails(tmp_path):
    with pytest.raises(patch_web.PatchError, match="unknown language"):
        patch_web.build(UPSTREAM, OVERLAY, tmp_path / "x", "xx")


def test_every_translation_anchor_is_strict():
    # each anchor carries an expected count (1 unless a message appears several times)
    from translations import LANGUAGES
    for lang, tr in LANGUAGES.items():
        for patch in tr["html"] + tr["shim"]:
            assert patch["count"] >= 1 and patch["old"] != patch["new"], (lang, patch["name"])
