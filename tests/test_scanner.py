import os

import pytest

from redwood.categories import CATEGORIES
from redwood.scanner import scan


def names(node):
    return [c.name for c in node.children]


def test_sizes_add_up(make_tree):
    root = scan(
        make_tree({"a.txt": 100, "sub/b.mp4": 300, "sub/deeper/c.mp3": 50}), apparent_size=True
    )
    assert root.size == 450
    sub = next(c for c in root.children if c.name == "sub")
    assert sub.size == 350
    assert sub.is_dir


def test_children_sorted_biggest_first(make_tree):
    root = scan(make_tree({"small": 10, "big": 1000, "medium": 100}), apparent_size=True)
    assert names(root) == ["big", "medium", "small"]


def test_size_per_file_type(make_tree):
    root = scan(make_tree({"a.mp4": 300, "b/c.mkv": 200, "d.mp3": 50}), apparent_size=True)
    by_name = dict(zip((c.name for c in CATEGORIES), root.cat_sizes, strict=True))
    assert by_name["video"] == 500
    assert by_name["audio"] == 50
    assert CATEGORIES[root.category].name == "video"


def test_disk_usage_is_default(make_tree):
    root = scan(make_tree({"a": 1}))
    assert root.size == os.stat(root.path + "/a").st_blocks * 512


def test_hard_links_counted_once(make_tree):
    path = make_tree({"a": 1000})
    os.link(path / "a", path / "b")
    assert scan(path, apparent_size=True).size == 1000


def test_symlinks_not_followed(make_tree):
    path = make_tree({"real/a": 1000})
    os.symlink(path / "real", path / "link")
    root = scan(path, apparent_size=True)
    assert root.size < 2000


def test_unreadable_folder_is_skipped(make_tree, monkeypatch):
    path = make_tree({"ok/a": 100, "locked/b": 100})
    real_scandir = os.scandir

    # chmod can't lock out root, so simulate the permission error instead.
    def scandir(p):
        if os.path.basename(p) == "locked":
            raise PermissionError(p)
        return real_scandir(p)

    monkeypatch.setattr(os, "scandir", scandir)
    root = scan(path, apparent_size=True)
    locked = next(c for c in root.children if c.name == "locked")
    assert locked.error
    assert root.size == 100


def test_missing_root_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        scan(str(tmp_path / "nope"))
