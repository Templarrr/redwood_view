import curses

import pytest

from redwood.keys import normalize


@pytest.mark.parametrize(
    ("typed", "expected"),
    [
        ("й", "q"),  # Russian / Ukrainian / Belarusian
        ("Й", "Q"),
        ("о", "j"),
        ("л", "k"),
        ("д", "l"),
        ("ξ", "j"),  # Greek
        ("κ", "k"),
        ("λ", "l"),
        ("Λ", "L"),
        ("σ", "s"),
        ("ς", "w"),
        ("Σ", "S"),
    ],
)
def test_non_latin_letters_map_to_qwerty_position(typed, expected):
    assert normalize(typed) == ord(expected)


def test_latin_and_control_characters_pass_through():
    assert normalize("q") == ord("q")
    assert normalize(";") == ord(";")
    assert normalize("\n") == 10


def test_special_keys_pass_through():
    assert normalize(curses.KEY_UP) == curses.KEY_UP
