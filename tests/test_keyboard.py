import pytest

from app.keyboard import ParsedKey, parse_combo


def test_parses_simple_key() -> None:
    assert parse_combo("F1") == [ParsedKey("f1", True)]


def test_parses_combo_and_aliases() -> None:
    assert parse_combo("Ctrl + F12") == [ParsedKey("ctrl", True), ParsedKey("f12", True)]
    assert parse_combo("Alt+N") == [ParsedKey("alt", True), ParsedKey("n", False)]


@pytest.mark.parametrize("combo", ["", "Ctrl+", "Mouse4", "F25", "not-a-key"])
def test_rejects_invalid_combo(combo: str) -> None:
    with pytest.raises(ValueError):
        parse_combo(combo)
