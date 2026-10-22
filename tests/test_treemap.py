import pytest

from redwood.treemap import Rect, layout, squarify


def test_squarify_areas_are_proportional():
    sizes = [6, 6, 4, 3, 2, 2, 1]
    rects = squarify(sizes, 0, 0, 6, 4)
    for size, (_, _, w, h) in zip(sizes, rects, strict=True):
        assert w * h == pytest.approx(size)


def test_squarify_keeps_blocks_squarish():
    rects = squarify([1] * 16, 0, 0, 100, 100)
    for _, _, w, h in rects:
        assert max(w / h, h / w) < 2


def test_layout_tiles_area_without_gaps_or_overlap():
    area = Rect(3, 2, 50, 20)
    rects = layout([500, 300, 120, 50, 20, 10], area)
    cells = [(x, y) for r in rects for x in range(r.x, r.x + r.w) for y in range(r.y, r.y + r.h)]
    assert len(cells) == len(set(cells)) == area.w * area.h
    assert all(area.x <= x < area.x + area.w and area.y <= y < area.y + area.h for x, y in cells)


def test_layout_drops_items_too_small_to_draw():
    rects = layout([1_000_000, 1], Rect(0, 0, 10, 5))
    assert rects[1].w * rects[1].h == 0


@pytest.mark.parametrize("sizes", [[], [0, 0]])
def test_layout_with_nothing_to_draw(sizes):
    assert all(r.w * r.h == 0 for r in layout(sizes, Rect(0, 0, 10, 10)))
