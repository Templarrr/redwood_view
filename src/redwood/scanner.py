import os
import stat
from collections.abc import Callable

from redwood.categories import CATEGORIES, OTHER, categorize


class Node:
    __slots__ = ("name", "parent", "size", "children", "category", "cat_sizes", "error")

    def __init__(self, name: str, parent: "Node | None", size: int = 0, category: int = OTHER):
        self.name = name
        self.parent = parent
        self.size = size
        self.category = category
        self.children: list[Node] | None = None
        self.cat_sizes: list[int] | None = None
        self.error = False

    @property
    def is_dir(self) -> bool:
        return self.children is not None

    @property
    def path(self) -> str:
        if self.parent is None:
            return self.name
        return os.path.join(self.parent.path, self.name)

    def __repr__(self) -> str:
        return f"Node({self.path!r}, {self.size})"


def _dir_node(name: str, parent: Node | None) -> Node:
    node = Node(name, parent)
    node.children = []
    node.cat_sizes = [0] * len(CATEGORIES)
    return node


def scan(
    root: str,
    one_file_system: bool = False,
    apparent_size: bool = False,
    progress: Callable[[int, str], None] | None = None,
) -> Node:
    root = os.path.abspath(root)
    root_dev = os.stat(root).st_dev
    root_node = _dir_node(root, None)
    # Iterative walk so very deep trees can't hit the recursion limit.
    stack = [(root_node, root)]
    visited: list[Node] = []
    seen_inodes: set[tuple[int, int]] = set()
    count = 0

    while stack:
        node, path = stack.pop()
        visited.append(node)
        try:
            with os.scandir(path) as it:
                entries = list(it)
        except OSError:
            node.error = True
            continue

        for entry in entries:
            try:
                st = entry.stat(follow_symlinks=False)
            except OSError:
                continue
            count += 1
            if stat.S_ISDIR(st.st_mode):
                if one_file_system and st.st_dev != root_dev:
                    continue
                child = _dir_node(entry.name, node)
                stack.append((child, entry.path))
            else:
                # Hard links share storage, so only count the first one we meet.
                if st.st_nlink > 1:
                    key = (st.st_dev, st.st_ino)
                    if key in seen_inodes:
                        continue
                    seen_inodes.add(key)
                child = Node(
                    entry.name, node, _size(st, apparent_size), categorize(entry.name, st.st_mode)
                )
            node.children.append(child)
        if progress:
            progress(count, path)

    # Parents were visited before their children, so reversing gives a bottom-up order.
    for node in reversed(visited):
        node.children.sort(key=lambda n: n.size, reverse=True)
        for child in node.children:
            node.size += child.size
            if child.is_dir:
                for i, size in enumerate(child.cat_sizes):
                    node.cat_sizes[i] += size
            else:
                node.cat_sizes[child.category] += child.size
        if node.size:
            node.category = max(range(len(CATEGORIES)), key=node.cat_sizes.__getitem__)
    return root_node


def _size(st: os.stat_result, apparent_size: bool) -> int:
    blocks = getattr(st, "st_blocks", None)
    if apparent_size or blocks is None:
        return st.st_size
    # Allocated size, like du/ncdu; also keeps sparse files such as /proc/kcore at their real cost.
    return blocks * 512
