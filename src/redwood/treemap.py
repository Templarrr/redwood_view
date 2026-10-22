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
        row = [areas[i]]
        i += 1
        while (
            i < len(areas)
            and areas[i] > 0
            and _worst(row + [areas[i]], short) <= _worst(row, short)
        ):
            row.append(areas[i])
            i += 1
        row_sum = sum(row)
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


def _worst(row: list[float], short: float) -> float:
    total = sum(row)
    return max(
        max(short * short * a / (total * total), total * total / (short * short * a)) for a in row
    )


def layout(sizes: list[float], area: Rect) -> list[Rect]:
    """Lay sizes out on the character grid; items too small for a cell get a zero-sized rect."""
    rects = squarify(sizes, 0.0, 0.0, float(area.w), area.h * CELL_ASPECT)
    result = []
    # Rounding shared edges the same way keeps neighbours from overlapping or leaving gaps.
    for fx, fy, fw, fh in rects:
        x0, x1 = round(fx), round(fx + fw)
        y0, y1 = round(fy / CELL_ASPECT), round((fy + fh) / CELL_ASPECT)
        result.append(Rect(area.x + x0, area.y + y0, max(0, x1 - x0), max(0, y1 - y0)))
    return result
