import pytest

from redwood.humanize import human_size


@pytest.mark.parametrize(
    ("size", "expected"),
    [(0, "0 B"), (1023, "1023 B"), (1536, "1.5 KiB"), (5 * 1024**3, "5.0 GiB")],
)
def test_human_size(size, expected):
    assert human_size(size) == expected
