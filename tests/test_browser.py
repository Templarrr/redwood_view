from redwood.browser import Browser
from redwood.scanner import scan


def test_navigation(make_tree):
    root = scan(make_tree({"big/inner/x": 300, "small/y": 100, "file": 10}), apparent_size=True)
    b = Browser(root)
    assert b.selected.name == "big"

    b.move(1)
    assert b.selected.name == "small"
    b.enter()
    assert b.current.name == "small"
    assert b.selected.name == "y"

    b.leave()
    assert b.current is root
    assert b.selected.name == "small"


def test_moves_stay_in_bounds(make_tree):
    b = Browser(scan(make_tree({"a": 1, "b": 2}), apparent_size=True))
    b.move(-5)
    assert b.index == 0
    b.move(50)
    assert b.index == 1


def test_enter_file_and_leave_root_do_nothing(make_tree):
    root = scan(make_tree({"file": 10}))
    b = Browser(root)
    b.enter()
    b.leave()
    assert b.current is root
