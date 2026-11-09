import threading
import time
import uuid


class Run:
    def __init__(self) -> None:
        self.id = uuid.uuid4().hex[:10]
        self.events: list[dict] = []
        self.done = False
        self._cond = threading.Condition()

    def emit(self, event_type: str, **data) -> None:
        with self._cond:
            self.events.append({"i": len(self.events), "t": time.time(), "type": event_type, **data})
            self._cond.notify_all()

    def finish(self) -> None:
        with self._cond:
            self.done = True
            self._cond.notify_all()

    def wait_for(self, index: int, timeout: float = 15.0) -> tuple[list[dict], bool]:
        with self._cond:
            if index >= len(self.events) and not self.done:
                self._cond.wait(timeout)
            pending = self.events[index:]
            return pending, self.done and not pending


class RunBusyError(RuntimeError):
    pass


_runs: dict[str, Run] = {}
_active: Run | None = None
_lock = threading.Lock()


def create_run() -> Run:
    global _active
    with _lock:
        if _active is not None and not _active.done:
            raise RunBusyError("A run is already in progress")
        _active = Run()
        _runs[_active.id] = _active
        return _active


def get_run(run_id: str) -> Run | None:
    return _runs.get(run_id)


def emit(event_type: str, **data) -> None:
    run = _active
    if run is not None and not run.done:
        run.emit(event_type, **data)
