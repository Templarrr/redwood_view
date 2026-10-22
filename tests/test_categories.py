import stat

import pytest

from redwood.categories import CATEGORIES, categorize


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("movie.MKV", "video"),
        ("song.flac", "audio"),
        ("photo.jpeg", "image"),
        ("backup.tar.gz", "archive"),
        ("report.pdf", "document"),
        ("main.py", "code"),
        ("libc.so.6", "binary"),
        ("README", "other"),
        ("no_idea.qwerty", "other"),
    ],
)
def test_categorize(name, expected):
    assert CATEGORIES[categorize(name)].name == expected


def test_executable_without_known_extension_is_binary():
    mode = stat.S_IFREG | 0o755
    assert CATEGORIES[categorize("python3.13", mode)].name == "binary"
