from PyQt5.QtCore import QThread, pyqtSignal
from core.stm32_commands import STM32RelayController


class _GuardAbortThread(QThread):
    """Runs abort_test_internal off the GUI thread. Reuses the screen's
    own cleanup — no duplicated shutdown logic."""
    finished_ok = pyqtSignal()

    def __init__(self, screen, reset_relays: bool):
        super().__init__()
        self.screen = screen
        self.reset_relays = reset_relays

    def run(self):
        self.screen.abort_test_internal(self.reset_relays)
        self.finished_ok.emit()


class RelayFailureGuard:
    """
    Wraps every STM32RelayController.send_with_retry() call made during
    an active test run so relay failures are detected in one place.

    - send_default_states(): 5 consecutive failures -> critical abort
    - send(cmd_func):        1 failure               -> critical abort
    """

    def __init__(self, screen):
        self.screen = screen
        self._default_fail_count = 0
        self._tripped = False

    def reset(self):
        self._default_fail_count = 0
        self._tripped = False

    # ---- Problem 1 -------------------------------------------------
    def send_default_states(self) -> bool:
        ok = STM32RelayController.send_with_retry(STM32RelayController.set_default_states)
        if ok:
            self._default_fail_count = 0
            return True

        self._default_fail_count += 1
        self.screen.log_signal.emit(
            f"ERROR: Failed to set relays to default state "
            f"({self._default_fail_count}/5 consecutive failures)", True
        )
        if self._default_fail_count >= 5:
            self._trip(
                "⚠ Relay Communication Failure",
                "Relay communication has repeatedly failed.\n\n"
                "Possible causes:\n"
                "• ISTJ entered Bad Authentication mode.\n"
                "• USB communication corruption.\n\n"
                "Recommended Action:\n"
                "Abort the current test.\n"
                "Reconnect the ISTJ.\n"
                "Reconnect the USB cable.\n"
                "Restart the application.",
            )
        return False

    # ---- Problem 4 ---------------------------------------------------
    def send(self, cmd_func) -> bool:
        ok = STM32RelayController.send_with_retry(cmd_func)
        if not ok:
            self._trip(
                "⚠ Relay Communication Failed",
                "Relay communication failed.\n\n"
                "Possible causes:\n"
                "USB communication issue.\n"
                "Bad relay connection.\n"
                "STM32 communication failure.\n\n"
                "Please abort the current test.\n"
                "Reconnect the hardware before restarting.",
            )
        return ok

    # ---- shared trip / abort path ------------------------------------
    def _trip(self, title, message):
        if self._tripped:
            return          # don't stack duplicate popups
        self._tripped = True
        screen = self.screen
        screen.abort_event.set()      # unblocks/raises inside check_abort() immediately

        def _on_ok(result, popup):
            worker = _GuardAbortThread(screen, reset_relays=False)  # never re-run set_default_states here
            worker.finished_ok.connect(lambda: setattr(self, "_tripped", False))
            screen._relay_guard_abort_worker = worker   # keep a reference alive
            worker.start()

        screen._queue_popup(title, message, None, "ok", None, callback=_on_ok)