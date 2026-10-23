# Redwood View

A console disk usage viewer in the spirit of SequoiaView: a treemap fills most of the
window, and an ncdu-style folder list on the right is used for navigation. The selected
entry is highlighted on the treemap, and blocks are coloured by file type so you can see
not only which folder is big but what is filling it.

Pure Python standard library (`curses`), so it works on any server you can `ssh` into.

![Home folder overview with the file type legend open](https://raw.githubusercontent.com/Templarrr/redwood_view/main/docs/screenshots/overview.png)

Inside a folder: nested blocks of the same type are told apart by a dotted texture. Files too
small to get a cell of their own are merged into one block labelled "+N small items",
which keeps folders with tens of thousands of files quick to draw.

![Videos folder](https://raw.githubusercontent.com/Templarrr/redwood_view/main/docs/screenshots/videos.png)

Without colour (`--no-color`, or a terminal that has none) each file type gets its own
character instead.

![Monochrome mode](https://raw.githubusercontent.com/Templarrr/redwood_view/main/docs/screenshots/nocolor.png)

## Install

```sh
uv tool install redwood-view
```

or `pipx install redwood-view`. Either puts the `redwood` command on your `PATH`.

To get the latest unreleased code instead, install from the repo:
`uv tool install git+https://github.com/Templarrr/redwood_view`, or from a checkout,
`uv tool install .`

## Update

```sh
uv tool upgrade redwood-view   # or: pipx upgrade redwood-view
```

If you installed from the repo, the same command fetches the latest commit, even when the
version number hasn't changed. A pinned commit or tag (`...redwood_view@<ref>`) stays
pinned, so install again without it instead:

```sh
uv tool install --reinstall git+https://github.com/Templarrr/redwood_view
```

From a checkout, `git pull` and then `uv tool install --reinstall .`

## Use

```sh
redwood /          # scan everything
redwood ~/Videos   # scan one folder
redwood -x /       # stay on the root filesystem (skip /proc, mounted drives, ...)
```

Folders that can't be read are skipped and marked with `!` in the list.

| Key                    | Action                    |
|------------------------|---------------------------|
| Up / Down, `j` / `k`   | move selection            |
| PgUp / PgDn, Home / End| jump                      |
| Right / Enter          | open folder               |
| Left / Backspace       | go to parent              |
| `l`                    | toggle file type legend   |
| `q`                    | quit                      |

Letter keys work by position on Russian, Ukrainian, Belarusian and Greek layouts too,
so `й` acts as `q` without switching to English.

Options: `--apparent-size` uses file sizes instead of disk usage, `--no-color` draws
file types with characters instead of colours.

## Development

```sh
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

### Releasing

Bump the version with `uv version --bump minor` (or `patch`, `major`), commit, then push a
matching tag:

```sh
git tag v0.2.0
git push origin v0.2.0
```

The release workflow checks that the tag matches the version in `pyproject.toml`, runs
the tests, builds the package and publishes it to PyPI.
