"""Per-request cancellation/deadline, kept outside model-controlled arguments."""

import threading
import time
from contextvars import ContextVar

from .common import Fault

CURRENT = ContextVar("verifier_execution_control", default=None)


class Control:
    def __init__(self, timeout, progress=None):
        self.cancelled = threading.Event()
        self.deadline = time.monotonic() + timeout
        self.progress = progress
        self.last_progress = 0
        self.progress_sequence = 0
        self.finishing = False
        self.lock = threading.Lock()

    def check(self):
        if self.finishing:
            return
        if self.cancelled.is_set():
            raise Fault("verification_cancelled", "The verification request was cancelled; saved evidence is retained.")
        if time.monotonic() >= self.deadline:
            raise Fault("verification_timeout", "The complete verification attempt reached its deadline; saved evidence is retained.")

    def notify(self, event):
        if not self.progress or self.cancelled.is_set():
            return
        with self.lock:
            now = time.monotonic()
            if now - self.last_progress < 1 and event != "verification_finished":
                return
            self.last_progress = now
            self.progress_sequence += 1
            # Generated event names only; no tool arguments or model output in UI notifications.
            self.progress(self.progress_sequence, event.replace("_", " ").capitalize())


def checkpoint():
    control = CURRENT.get()
    if control:
        control.check()
