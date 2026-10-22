from redwood.scanner import Node


class Browser:
    def __init__(self, root: Node):
        self.root = root
        self.current = root
        self.index = 0

    @property
    def entries(self) -> list[Node]:
        return self.current.children

    @property
    def selected(self) -> Node | None:
        return self.entries[self.index] if self.entries else None

    def move(self, delta: int) -> None:
        if self.entries:
            self.index = max(0, min(len(self.entries) - 1, self.index + delta))

    def move_to(self, index: int) -> None:
        self.move(index - self.index)

    def enter(self) -> None:
        node = self.selected
        if node is not None and node.is_dir:
            self.current = node
            self.index = 0

    def leave(self) -> None:
        if self.current.parent is None:
            return
        came_from = self.current
        self.current = came_from.parent
        self.index = self.current.children.index(came_from)
