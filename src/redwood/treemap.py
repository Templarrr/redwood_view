from typing import NamedTuple

# Terminal cells are roughly twice as tall as they are wide.
CELL_ASPECT = 2.0


class Rect(NamedTuple):
    x: int
    y: int
    w: int
    h: int


def squarify(
    sizes: list[float], x: float, y: float, w: float, h: float
) -> list[tuple[float, float, float, float]]:
    """Squarified treemap (Bruls et al.); `sizes` must be sorted in descending order."""
    total = sum(sizes)
    if total <= 0 or w <= 0 or h <= 0:
        return [(x, y, 0.0, 0.0)] * len(sizes)
    scale = w * h / total
    areas = [s * scale for s in sizes]
    rects = []
    i = 0
    while i < len(areas):
        if areas[i] <= 0 or w <= 0 or h <= 0:
            rects.extend([(x, y, 0.0, 0.0)] * (len(areas) - i))
            break
        short = min(w, h)
        # Sizes are sorted, so the row's largest area is its first and the smallest its last;
        # that keeps each aspect-ratio check O(1) instead of rescanning the row.
        row = [areas[i]]
        row_sum = areas[i]
        i += 1
        while i < len(areas) and areas[i] > 0:
            grown = row_sum + areas[i]
            if _worst(grown, row[0], areas[i], short) > _worst(row_sum, row[0], row[-1], short):
                break
            row.append(areas[i])
            row_sum = grown
            i += 1
        if w >= h:
            col_w = row_sum / h
            cy = y
            for area in row:
                rects.append((x, cy, col_w, area / col_w))
                cy += area / col_w
            x += col_w
            w -= col_w
        else:
            row_h = row_sum / w
            cx = x
            for area in row:
                rects.append((cx, y, area / row_h, row_h))
                cx += area / row_h
            y += row_h
            h -= row_h
    return rects


def _worst(total: float, largest: float, smallest: float, short: float) -> float:
    side2 = short * short
    total2 = total * total
    return max(side2 * largest / total2, total2 / (side2 * smallest))


def layout(sizes: list[float], area: Rect) -> tuple[list[Rect], Rect]:
    """Lay sizes out on the character grid.

    Items too small to get a cell of their own are merged into one block, so huge folders cost
    no more than the screen can show. Returns rects for the leading, visible items (possibly
    fewer than `sizes`) and the merged block's rect, which is empty when nothing was merged.
    """
    total = sum(sizes)
    cells = area.w * area.h
    if total <= 0 or cells <= 0:
        return [Rect(area.x, area.y, 0, 0)] * len(sizes), Rect(area.x, area.y, 0, 0)
    shown = 0
    while shown < len(sizes) and sizes[shown] * cells >= total:
        shown += 1
    if shown == len(sizes):
        return _grid(sizes, area), Rect(area.x, area.y, 0, 0)
    rest = total - sum(sizes[:shown])
    # Squarify wants descending sizes, so the merged block goes in at its sorted position.
    pos = next((i for i in range(shown) if sizes[i] < rest), shown)
    rects = _grid(sizes[:pos] + [rest] + sizes[pos:shown], area)
    return rects, rects.pop(pos)


def _grid(sizes: list[float], area: Rect) -> list[Rect]:
    rects = squarify(sizes, 0.0, 0.0, float(area.w), area.h * CELL_ASPECT)
    result = []
    # Rounding shared edges the same way keeps neighbours from overlapping or leaving gaps.
    for fx, fy, fw, fh in rects:
        x0, x1 = round(fx), round(fx + fw)
        y0, y1 = round(fy / CELL_ASPECT), round((fy + fh) / CELL_ASPECT)
        result.append(Rect(area.x + x0, area.y + y0, max(0, x1 - x0), max(0, y1 - y0)))
    return result
