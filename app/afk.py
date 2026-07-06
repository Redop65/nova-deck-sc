from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from threading import Event, Lock, Thread, current_thread
from time import monotonic
from typing import Callable


class AfkController:
    """Ejecuta F2 en el PC sin depender del ciclo de vida del navegador móvil."""

    def __init__(
        self,
        send_key: Callable[[str], None],
        *,
        min_delay_seconds: float = 210,
        max_delay_seconds: float = 270,
        logger: logging.Logger | None = None,
    ) -> None:
        self._send_key = send_key
        self._min_delay = min_delay_seconds
        self._max_delay = max_delay_seconds
        self._logger = logger or logging.getLogger("nova_deck.afk")
        self._lock = Lock()
        self._stop = Event()
        self._thread: Thread | None = None
        self._enabled = False
        self._test_mode = False
        self._next_run = 0.0
        self._last_run: str | None = None
        self._last_error: str | None = None

    def start(self, *, test_mode: bool = False) -> dict:
        with self._lock:
            if self._enabled:
                return self._status_locked()
            self._enabled = True
            self._test_mode = test_mode
            self._last_error = None
            self._schedule_locked()
            self._stop.clear()
            self._thread = Thread(target=self._run, name="nova-deck-afk", daemon=True)
            self._thread.start()
            status = self._status_locked()
        self._logger.info("Modo AFK activado (%s)", "prueba" if test_mode else "real")
        return status

    def stop(self) -> dict:
        with self._lock:
            self._enabled = False
            self._next_run = 0.0
            self._stop.set()
            thread = self._thread
            self._thread = None
        if thread and thread is not current_thread():
            thread.join(timeout=1)
        self._logger.info("Modo AFK desactivado")
        return self.status()

    def status(self) -> dict:
        with self._lock:
            return self._status_locked()

    def _status_locked(self) -> dict:
        remaining = max(0, int(round(self._next_run - monotonic()))) if self._enabled else 0
        return {
            "enabled": self._enabled,
            "test_mode": self._test_mode,
            "next_in_seconds": remaining,
            "last_run": self._last_run,
            "last_error": self._last_error,
        }

    def _schedule_locked(self) -> None:
        self._next_run = monotonic() + random.uniform(self._min_delay, self._max_delay)

    def _run(self) -> None:
        while True:
            with self._lock:
                if not self._enabled:
                    return
                delay = max(0, self._next_run - monotonic())
            if self._stop.wait(delay):
                return

            try:
                with self._lock:
                    if not self._enabled:
                        return
                    test_mode = self._test_mode
                if not test_mode:
                    self._send_key("F2")
                with self._lock:
                    self._last_run = datetime.now(timezone.utc).isoformat()
                    self._last_error = None
                self._logger.info("Modo AFK: F2 %s", "simulado" if test_mode else "enviado")
            except (ValueError, RuntimeError, OSError) as exc:
                with self._lock:
                    self._last_error = str(exc)
                self._logger.warning("Modo AFK: no se pudo enviar F2: %s", exc)
            finally:
                with self._lock:
                    if not self._enabled:
                        return
                    self._schedule_locked()
