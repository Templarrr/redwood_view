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
