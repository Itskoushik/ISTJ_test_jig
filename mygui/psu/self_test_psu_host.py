"""
SelfTestPSUHost
===============

Adapter that lets SelfTestWorker (equipment_self_check_screen.py) drive a
PSUAutomation instance. Per design decision: PSU reconnect during a
self-test is HEADLESS — no OperatorInfoPopup dialogs (SelfTestWorker has
no parent widget to anchor one to). Instead, reconnect prompts are routed
through the worker's existing operator_signal (title, message, image_path)
the same way self_audio_analyser.py already does for its own operator
prompts, and through log_signal for everything else.

Usage inside SelfTestWorker.__init__:

    from psu.psu_automation import PSUAutomation
    from psu.self_test_psu_host import SelfTestPSUHost

    self.psu_host = SelfTestPSUHost(self)
    self.psu = PSUAutomation(self.psu_host)

Then in self_psu.py / any self-test module:

    screen.psu.worker_channel_1()
    screen.psu.psu_send_command("...")
"""

from threading import Event

from psu.psu_automation import PSUAutomationHost


class SelfTestPSUHost(PSUAutomationHost):
    def __init__(self, worker):
        # worker is a SelfTestWorker instance — has log_signal, operator_signal,
        # and _operator_event (threading.Event) already, per
        # equipment_self_check_screen.py.
        self.worker = worker
        self._abort_event = Event()

    def log(self, message: str, is_error: bool = False):
        self.worker.log_signal.emit(message, is_error)

    def is_aborted(self) -> bool:
        return self._abort_event.is_set()

    def request_abort(self):
        """Call this if a self-test needs to bail out of a PSU wait early."""
        self._abort_event.set()

    def notify_disconnect_toast(self):
        # Headless by design — no toast widget without a parent window.
        # The log() call in _background_reconnect already records this.
        pass

    def request_operator_ack(self, title: str, message: str):
        # Reuse the worker's existing operator prompt channel — no image,
        # since this isn't an instructional step, just an acknowledgement gate.
        self.worker._operator_event.clear()
        self.worker.operator_signal.emit(title, message, "")
        self.worker._operator_event.wait()

    def on_reconnect_failed(self):
        self.worker.log_signal.emit(
            "❌ PSU could not be reconnected after multiple attempts. Self-test aborted.",
            True,
        )
        self._abort_event.set()

    def pause_device_listeners(self):
        # SelfTestWorker doesn't own device_listeners (that lives on the
        # screen). Nothing to pause here.
        pass

    def restore_device_listener(self, listener):
        # Self-test PSU reconnect doesn't need to hand the listener back
        # anywhere — it's transient for the duration of this test.
        pass