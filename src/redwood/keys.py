import curses

# Terminals report characters, not physical keys, so letters typed on a non-Latin
# layout are translated back to the US QWERTY key in the same position.
_QWERTY = "`qwertyuiop[]asdfghjkl;'zxcvbnm,."
_LAYOUTS = {
    "russian": "ёйцукенгшщзхъфывапролджэячсмитьбю",
    "ukrainian": "'йцукенгшщзхїфівапролджєячсмитьбю",
    "belarusian": "ёйцукенгшўзх'фывапролджэячсмітьбю",
    "greek": "`;ςερτυθιοπ[]ασδφγηξκλ΄'ζχψωβνμ,.",
}


def _build() -> dict[str, str]:
    table: dict[str, str] = {}
    for chars in _LAYOUTS.values():
        for char, latin in zip(chars, _QWERTY, strict=True):
            if char.isascii():
                continue
            table.setdefault(char, latin)
            # Skips final sigma, whose upper case belongs to σ.
            if char.upper().lower() == char:
                table.setdefault(char.upper(), latin.upper())
    return table


_TO_LATIN = _build()


def normalize(key: int | str) -> int:
    """Turn a get_wch() result into a getch()-style code, mapping layouts to QWERTY."""
    if isinstance(key, int):
        return key
    return ord(_TO_LATIN.get(key, key))


def read_key(screen: curses.window) -> int:
    return normalize(screen.get_wch())
