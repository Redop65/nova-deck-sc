import pytest

from app.keyboard import KeyboardSender, ParsedKey, parse_combo


def test_parses_simple_key() -> None:
    assert parse_combo("F1") == [ParsedKey("f1", True)]


def test_parses_combo_and_aliases() -> None:
    assert parse_combo("Ctrl + F12") == [ParsedKey("ctrl", True), ParsedKey("f12", True)]
    assert parse_combo("Alt+N") == [ParsedKey("alt", True), ParsedKey("n", False)]


@pytest.mark.parametrize("combo", ["", "Ctrl+", "Mouse4", "F25", "not-a-key"])
def test_rejects_invalid_combo(combo: str) -> None:
    with pytest.raises(ValueError):
        parse_combo(combo)


def test_sequence_executes_steps_and_pauses_between_them(monkeypatch) -> None:
    sender = KeyboardSender()
    events: list[tuple] = []
    monkeypatch.setattr(
        sender,
        "_send_locked",
        lambda combo, hold_ms=0: events.append(("send", combo, hold_ms)),
    )
    monkeypatch.setattr(
        "app.keyboard.sleep",
        lambda seconds: events.append(("sleep", seconds)),
    )

    sender.send_sequence(
        [
            {"keys": "F1", "hold_ms": 0, "delay_after_ms": 500},
            {"keys": "F2", "hold_ms": 100, "delay_after_ms": 0},
        ]
    )

    assert events == [
        ("send", "F1", 0),
        ("sleep", 0.5),
        ("send", "F2", 100),
    ]
