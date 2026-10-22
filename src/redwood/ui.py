import curses
import locale

from redwood.browser import Browser
from redwood.categories import CATEGORIES, OTHER
from redwood.humanize import human_size
from redwood.scanner import Node
from redwood.treemap import Rect, layout

HELP = "↑↓ move  →/Enter open  ←/Bksp up  l legend  q quit"
HELP_ASCII = "Up/Down move  Right/Enter open  Left/Bksp up  l legend  q quit"
BAR_WIDTH = 8

_HIGHLIGHT_PAIR = len(CATEGORIES) + 1


class Styles:
    def __init__(self, color: bool):
        self.color = color and curses.has_colors()
        if self.color:
            curses.start_color()
            try:
                curses.use_default_colors()
                default_bg = -1
            except curses.error:
                default_bg = curses.COLOR_BLACK
            for i, cat in enumerate(CATEGORIES):
                if i == OTHER:
                    curses.init_pair(i + 1, curses.COLOR_WHITE, default_bg)
                else:
                    curses.init_pair(i + 1, curses.COLOR_BLACK, cat.color)
            curses.init_pair(_HIGHLIGHT_PAIR, curses.COLOR_YELLOW, default_bg)
            self.highlight = curses.color_pair(_HIGHLIGHT_PAIR) | curses.A_BOLD | curses.A_REVERSE
        else:
            self.highlight = curses.A_BOLD | curses.A_REVERSE

    def fill(self, category: int, alt: bool) -> tuple[str, int]:
        # Alternating texture keeps neighbouring blocks of the same type apart.
        if self.color:
            if category == OTHER:
                char = ":" if alt else "."
            else:
                char = "." if alt else " "
            return char, curses.color_pair(category + 1)
        return CATEGORIES[category].char, curses.A_BOLD if alt else curses.A_NORMAL

    def swatch(self, category: int) -> tuple[str, int]:
        char, attr = self.fill(category, False)
        return char * 2, attr


class App:
    def __init__(self, screen, root: Node, color: bool):
        self.screen = screen
        self.browser = Browser(root)
        self.styles = Styles(color)
        self.show_legend = False
        self.list_top = 0
        self.encoding = screen.encoding or locale.getpreferredencoding()
        self.unicode = "utf" in self.encoding.lower()
        self.unreadable = _count_errors(root)
        self._tiles_key = None
        self._tiles: list[tuple[Rect, int, bool]] = []
        self._top_rects: list[Rect] = []

    def run(self) -> None:
        curses.curs_set(0)
        while True:
            self.draw()
            key = self.screen.getch()
            if key in (ord("q"), ord("Q")):
                return
            self.handle(key)

    def handle(self, key: int) -> None:
        b = self.browser
        page = max(1, self.screen.getmaxyx()[0] - 3)
        actions = {
            curses.KEY_UP: lambda: b.move(-1),
            ord("k"): lambda: b.move(-1),
            curses.KEY_DOWN: lambda: b.move(1),
            ord("j"): lambda: b.move(1),
            curses.KEY_PPAGE: lambda: b.move(-page),
            curses.KEY_NPAGE: lambda: b.move(page),
            curses.KEY_HOME: lambda: b.move_to(0),
            curses.KEY_END: lambda: b.move_to(len(b.entries) - 1),
            curses.KEY_RIGHT: b.enter,
            curses.KEY_ENTER: b.enter,
            10: b.enter,
            13: b.enter,
            curses.KEY_LEFT: b.leave,
            curses.KEY_BACKSPACE: b.leave,
            127: b.leave,
            8: b.leave,
            ord("l"): self.toggle_legend,
        }
        action = actions.get(key)
        if action:
            action()

    def toggle_legend(self) -> None:
        self.show_legend = not self.show_legend

    def text(self, y: int, x: int, s: str, width: int, attr: int = 0) -> None:
        if width <= 0:
            return
        s = s.encode(self.encoding, "replace").decode(self.encoding)
        s = "".join(c if c.isprintable() else "?" for c in s)
        try:
            self.screen.addnstr(y, x, s, width, attr)
        except curses.error:
            pass  # writing the bottom-right cell moves the cursor off-screen

    def draw(self) -> None:
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        if width < 40 or height < 8:
            self.text(0, 0, "Terminal too small", width)
            self.screen.refresh()
            return
        list_w = min(max(width * 2 // 5, 36), 64)
        map_area = Rect(0, 1, width - list_w - 1, height - 2)
        self.draw_header(width)
        self.draw_treemap(map_area)
        self.draw_separator(width - list_w - 1, 1, height - 2)
        self.draw_list(Rect(width - list_w, 1, list_w, height - 2))
        if self.show_legend:
            self.draw_legend(map_area)
        self.text(
            height - 1,
            0,
            (HELP if self.unicode else HELP_ASCII).ljust(width),
            width,
            curses.A_REVERSE,
        )
        self.screen.refresh()

    def draw_header(self, width: int) -> None:
        cur = self.browser.current
        right = f" {human_size(cur.size)}  {len(cur.children)} items "
        if self.unreadable:
            right = f" {self.unreadable} unreadable |" + right
        left = f" redwood  {cur.path}"
        line = left[: max(0, width - len(right))].ljust(width - len(right)) + right
        self.text(0, 0, line, width, curses.A_REVERSE)

    def draw_separator(self, x: int, y: int, h: int) -> None:
        try:
            self.screen.vline(y, x, curses.ACS_VLINE, h)
        except curses.error:
            pass

    def draw_treemap(self, area: Rect) -> None:
        cur = self.browser.current
        key = (id(cur), area)
        if key != self._tiles_key:
            self._tiles = []
            self._top_rects = layout([c.size for c in cur.children], area)
            for i, (child, rect) in enumerate(zip(cur.children, self._top_rects, strict=True)):
                self._collect(child, _frame_inner(child, rect), i % 2 == 1)
            self._tiles_key = key

        for rect, category, alt in self._tiles:
            char, attr = self.styles.fill(category, alt)
            for row in range(rect.y, rect.y + rect.h):
                self.text(row, rect.x, char * rect.w, rect.w, attr)

        for i, (child, rect) in enumerate(zip(cur.children, self._top_rects, strict=True)):
            if not rect.w or not rect.h:
                continue
            selected = i == self.browser.index
            label = f" {child.name}{'/' if child.is_dir else ''} {human_size(child.size)} "
            if _frame_inner(child, rect) != rect:
                self.draw_frame(rect, self.styles.highlight if selected else curses.A_NORMAL)
                self.text(
                    rect.y, rect.x + 1, label, rect.w - 2, self.styles.highlight if selected else 0
                )
            elif selected:
                attr = self.styles.highlight
                for row in range(rect.y, rect.y + rect.h):
                    self.text(row, rect.x, " " * rect.w, rect.w, attr)
                self.text(rect.y, rect.x, label.strip(), rect.w, attr)
            elif rect.w >= 6:
                self.text(
                    rect.y,
                    rect.x,
                    label.strip(),
                    rect.w,
                    self.styles.fill(child.category, i % 2 == 1)[1],
                )

    def _collect(self, node: Node, rect: Rect, alt: bool) -> None:
        if not rect.w or not rect.h:
            return
        if not node.is_dir or not node.size or rect.w * rect.h < 2:
            self._tiles.append((rect, node.category, alt))
            return
        rects = layout([c.size for c in node.children], rect)
        for i, (child, child_rect) in enumerate(zip(node.children, rects, strict=True)):
            self._collect(child, child_rect, alt ^ (i % 2 == 1))

    def draw_frame(self, r: Rect, attr: int) -> None:
        s = self.screen
        right, bottom = r.x + r.w - 1, r.y + r.h - 1
        try:
            s.hline(r.y, r.x + 1, curses.ACS_HLINE | attr, r.w - 2)
            s.hline(bottom, r.x + 1, curses.ACS_HLINE | attr, r.w - 2)
            s.vline(r.y + 1, r.x, curses.ACS_VLINE | attr, r.h - 2)
            s.vline(r.y + 1, right, curses.ACS_VLINE | attr, r.h - 2)
            s.addch(r.y, r.x, curses.ACS_ULCORNER, attr)
            s.addch(r.y, right, curses.ACS_URCORNER, attr)
            s.addch(bottom, r.x, curses.ACS_LLCORNER, attr)
            s.addch(bottom, right, curses.ACS_LRCORNER, attr)
        except curses.error:
            pass

    def draw_list(self, area: Rect) -> None:
        b = self.browser
        entries = b.entries
        if not entries:
            msg = "(unreadable)" if b.current.error else "(empty)"
            self.text(area.y, area.x + 1, msg, area.w - 1)
            return
        if b.index < self.list_top:
            self.list_top = b.index
        elif b.index >= self.list_top + area.h:
            self.list_top = b.index - area.h + 1
        self.list_top = max(0, min(self.list_top, len(entries) - area.h))

        biggest = entries[0].size or 1
        total = b.current.size or 1
        for row, i in enumerate(range(self.list_top, min(len(entries), self.list_top + area.h))):
            node = entries[i]
            y = area.y + row
            swatch, swatch_attr = self.styles.swatch(node.category)
            filled = round(BAR_WIDTH * node.size / biggest)
            bar = "#" * filled + " " * (BAR_WIDTH - filled)
            mark = "!" if node.error else " "
            name = node.name + ("/" if node.is_dir else "")
            line = f"{human_size(node.size):>9} {node.size * 100 / total:5.1f}% [{bar}]{mark}{name}"
            attr = curses.A_REVERSE if i == b.index else 0
            self.text(y, area.x + 1, swatch, 2, swatch_attr)
            self.text(y, area.x + 3, line.ljust(area.w), area.w - 3, attr)

    def draw_legend(self, area: Rect) -> None:
        cur = self.browser.current
        cats = sorted(
            (i for i in range(len(CATEGORIES)) if cur.cat_sizes[i]),
            key=lambda i: cur.cat_sizes[i],
            reverse=True,
        )
        total = cur.size or 1
        lines = []
        for i in cats:
            size = cur.cat_sizes[i]
            lines.append(
                (i, f"{CATEGORIES[i].name:<9}{human_size(size):>10} {size * 100 / total:5.1f}%")
            )
        w = 2 + 3 + max((len(t) for _, t in lines), default=16)
        h = len(lines) + 2
        box = Rect(area.x + 1, area.y + area.h - h - 1, w + 1, h)
        if box.y < area.y or box.w > area.w:
            return
        for row in range(box.y, box.y + box.h):
            self.text(row, box.x, " " * box.w, box.w)
        self.draw_frame(box, curses.A_BOLD)
        self.text(box.y, box.x + 2, " legend ", box.w - 3, curses.A_BOLD)
        if not lines:
            self.text(box.y + 1, box.x + 2, "(nothing here)", box.w - 3)
        for row, (i, line) in enumerate(lines):
            swatch, attr = self.styles.swatch(i)
            self.text(box.y + 1 + row, box.x + 2, swatch, 2, attr)
            self.text(box.y + 1 + row, box.x + 5, line, box.w - 6)


def _frame_inner(node: Node, rect: Rect) -> Rect:
    if node.is_dir and rect.w >= 6 and rect.h >= 3:
        return Rect(rect.x + 1, rect.y + 1, rect.w - 2, rect.h - 2)
    return rect


def _count_errors(root: Node) -> int:
    count, stack = 0, [root]
    while stack:
        node = stack.pop()
        count += node.error
        stack.extend(c for c in node.children if c.is_dir)
    return count


def run(root: Node, color: bool = True) -> None:
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(lambda screen: App(screen, root, color).run())
