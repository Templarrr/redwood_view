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
    rects, rest = layout([500, 300, 120, 50, 20, 10], area)
    assert rest.w * rest.h == 0
    cells = [(x, y) for r in rects for x in range(r.x, r.x + r.w) for y in range(r.y, r.y + r.h)]
    assert len(cells) == len(set(cells)) == area.w * area.h
    assert all(area.x <= x < area.x + area.w and area.y <= y < area.y + area.h for x, y in cells)


def test_layout_merges_items_too_small_to_draw():
    area = Rect(0, 0, 40, 20)
    rects, rest = layout([1_000_000] + [1] * 1000, area)
    assert len(rects) == 1
    assert rest.w * rest.h == 0
    rects, rest = layout([1000] + [1] * 1000, area)
    assert len(rects) == 1
    # Each item alone is under a cell, but together they cover half the map.
    assert rects[0].w * rects[0].h + rest.w * rest.h == area.w * area.h
    assert rest.w * rest.h == pytest.approx(400, rel=0.1)


@pytest.mark.parametrize("sizes", [[], [0, 0]])
def test_layout_with_nothing_to_draw(sizes):
    rects, rest = layout(sizes, Rect(0, 0, 10, 10))
    assert all(r.w * r.h == 0 for r in rects + [rest])
