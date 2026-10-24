import os
import sys

import pytest

from redwood.cells import cell_width
from redwood.scanner import scan
from redwood.ui import App


class FakeScreen:
    encoding = "utf-8"

    def __init__(self):
        self.writes = []

    def addstr(self, y, x, s, attr=0):
        self.writes.append((y, x, s))


@pytest.fixture
def app(tmp_path):
    return App(FakeScreen(), scan(str(tmp_path)), color=False)


@pytest.mark.parametrize("name", ["日本語のファイル名.txt", "Документи та фото", "😀😀😀😀😀😀"])
def test_text_fits_display_width(app, name):
    app.text(0, 0, name, 7)
    ((_, _, written),) = app.screen.writes
    assert cell_width(written) <= 7
    assert written


def test_text_pads_wide_names_to_width(app):
    app.text(0, 0, "日本語", 10, pad=True)
    assert app.screen.writes == [(0, 0, "日本語    ")]


@pytest.mark.skipif(sys.platform != "linux", reason="only Linux allows non-UTF-8 file names")
def test_undecodable_name_shown_with_placeholder(tmp_path):
    open(os.path.join(os.fsencode(tmp_path), b"bad\xffname"), "wb").close()
    root = scan(str(tmp_path))
    app = App(FakeScreen(), root, color=False)
    app.text(0, 0, root.children[0].name, 20)
    assert app.screen.writes == [(0, 0, "bad?name")]


def test_windows_console_code_page_does_not_hide_cyrillic(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    screen = FakeScreen()
    screen.encoding = "cp437"
    app = App(screen, scan(str(tmp_path)), color=False)
    app.text(0, 0, "Документи та фото", 40)
    assert screen.writes == [(0, 0, "Документи та фото")]


@pytest.mark.skipif(sys.platform == "win32", reason="Windows ignores the code page")
def test_characters_the_terminal_cannot_encode_become_placeholders(tmp_path):
    screen = FakeScreen()
    screen.encoding = "ascii"
    app = App(screen, scan(str(tmp_path)), color=False)
    app.text(0, 0, "Дом.txt", 20)
    assert screen.writes == [(0, 0, "???.txt")]
