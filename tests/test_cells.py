import pytest

from redwood.cells import cell_width, clip, fit


@pytest.mark.parametrize(
    ("s", "width"),
    [("abc", 3), ("Привіт", 6), ("日本語", 6), ("café", 4), ("😀", 2), ("", 0)],
)
def test_cell_width(s, width):
    assert cell_width(s) == width


def test_clip_never_splits_a_wide_char():
    assert clip("日本語", 5) == "日本"
    assert clip("日本語", 6) == "日本語"


def test_clip_keeps_combining_marks_with_their_letter():
    assert clip("café au lait", 4) == "café"


def test_fit_pads_to_exact_width():
    assert fit("ab", 4) == "ab  "
    assert fit("日本語", 5) == "日本 "
    assert cell_width(fit("Привіт світ", 8)) == 8
