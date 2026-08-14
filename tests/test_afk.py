from __future__ import annotations

import json
from threading import Event
from pathlib import Path

from fastapi.testclient import TestClient

from app.afk import AfkController
from app.main import create_app


def test_afk_controller_runs_repeatedly_without_browser() -> None:
    calls: list[str] = []
    completed = Event()

    def capture(key: str) -> None:
        calls.append(key)
        if len(calls) >= 2:
            completed.set()

    controller = AfkController(
        capture, min_delay_seconds=0.01, max_delay_seconds=0.01
    )
    controller.start()
    assert completed.wait(timeout=1)
    status = controller.stop()

    assert calls[:2] == ["F2", "F2"]
    assert status["enabled"] is False


def test_afk_test_mode_cycles_without_sending_key() -> None:
    called = Event()
    controller = AfkController(
        lambda key: called.set(), min_delay_seconds=0.01, max_delay_seconds=0.01
    )
    controller.start(test_mode=True)
    assert not called.wait(timeout=0.05)
    status = controller.status()
    controller.stop()

    assert status["enabled"] is True
    assert status["test_mode"] is True
    assert status["last_run"] is not None


def test_afk_range_can_be_reconfigured() -> None:
    controller = AfkController(lambda key: None)
    status = controller.configure_range(60, 180)

    assert status["min_delay_seconds"] == 60
    assert status["max_delay_seconds"] == 180
    assert status["interval_seconds"] == 120


def test_afk_api_can_start_report_and_stop() -> None:
    app = create_app(force_test_mode=True)
    with TestClient(app) as client:
        initial = client.get("/api/afk")
        started = client.put("/api/afk", json={"enabled": True})
        current = client.get("/api/afk")
        stopped = client.put("/api/afk", json={"enabled": False})

    assert initial.json()["enabled"] is False
    assert started.json()["enabled"] is True
    assert started.json()["test_mode"] is True
    assert current.json()["next_in_seconds"] > 0
    assert stopped.json()["enabled"] is False


def test_afk_api_saves_interval_in_settings(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    buttons = tmp_path / "buttons.json"
    settings = tmp_path / "settings.json"
    buttons.write_text((root / "config" / "buttons.json").read_text(encoding="utf-8"), encoding="utf-8")
    settings.write_text(json.dumps({"app": {}, "obs": {}}), encoding="utf-8")

    with TestClient(create_app(buttons, force_test_mode=True, settings_path=settings)) as client:
        response = client.put("/api/afk/settings", json={"min_interval_seconds": 60, "max_interval_seconds": 180})
        status = client.get("/api/afk")

    assert response.status_code == 200
    assert response.json()["min_delay_seconds"] == 60
    assert response.json()["max_delay_seconds"] == 180
    assert status.json()["interval_seconds"] == 120
    assert json.loads(settings.read_text(encoding="utf-8"))["afk"] == {
        "min_interval_seconds": 60, "max_interval_seconds": 180,
    }
