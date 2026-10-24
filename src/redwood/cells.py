import unicodedata

# Terminals give CJK and most emoji two columns and combining marks none, so str length
# doesn't tell how much room a name takes on screen.


def char_width(c: str) -> int:
    if unicodedata.category(c) in ("Mn", "Me"):
        return 0
    return 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1


def cell_width(s: str) -> int:
    return sum(map(char_width, s))


def clip(s: str, width: int) -> str:
    used = 0
    for i, c in enumerate(s):
        used += char_width(c)
        if used > width:
            return s[:i]
    return s


def fit(s: str, width: int) -> str:
    s = clip(s, width)
    return s + " " * (width - cell_width(s))
