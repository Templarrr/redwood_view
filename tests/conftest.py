import os

import pytest


@pytest.fixture
def make_tree(tmp_path):
    """Create files from a {relative_path: size} mapping and return the root folder."""

    def make(files: dict[str, int]):
        for rel, size in files.items():
            path = tmp_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(os.urandom(size))
        return tmp_path

    return make
