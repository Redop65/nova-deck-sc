from __future__ import annotations

from threading import Event

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
