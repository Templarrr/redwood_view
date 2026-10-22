import pytest

from redwood.cli import main


def test_prints_total_when_not_a_terminal(make_tree, capsys):
    path = make_tree({"a": 2048})
    main([str(path), "--apparent-size"])
    assert capsys.readouterr().out.startswith("2.0 KiB\t")


def test_rejects_missing_folder(tmp_path):
    with pytest.raises(SystemExit) as e:
        main([str(tmp_path / "nope")])
    assert "not a directory" in str(e.value.code)
