"""
core/device_reconnect_handler.py

Shared DMM / Oscilloscope disconnect+reconnect flow, used by both
SingleTestScreen and FullTestScreen's on_device_disconnected handler.
Mirrors the PSU reconnect pattern, but reuses OperatorInfoPopup via
each screen's existing _queue_popup — same as everything else.
"""

from threading import Event
from devices.device_listeners import DMMListener, OscilloscopeListener


def handle_dmm_disconnected(screen):
    if getattr(screen, "_dmm_error_handled", False):
        return
    screen._dmm_error_handled = True
    import threading
    threading.Thread(target=_reconnect_dmm, args=(screen,), daemon=True, name="DMM-reconnect").start()


def _reconnect_dmm(screen):
    from core import dmm_reader
    screen.log_signal.emit("⚠ DMM disconnected.", True)
    dmm_reader.reset_dmm()
    # ensure_dmm_connected already shows the "check USB / power, click OK to retry"
    # OperatorInfoPopup loop and blocks on an Event until reconnected or aborted.
    ok = dmm_reader.ensure_dmm_connected(screen)
    if ok:
        screen.log_signal.emit("✅ DMM reconnected.", False)
        _restart_listener(screen, DMMListener, lambda: dmm_reader._dmm)
    else:
        screen.log_signal.emit("❌ DMM reconnect abandoned (test aborted).", True)
    screen._dmm_error_handled = False


def handle_oscilloscope_disconnected(screen):
    if getattr(screen, "_osc_error_handled", False):
        return
    screen._osc_error_handled = True
    import threading
    threading.Thread(target=_reconnect_oscilloscope, args=(screen,), daemon=True, name="OSC-reconnect").start()


def _reconnect_oscilloscope(screen):
    from devices.oscilloscope_connection import OscilloscopeConnection
    screen.log_signal.emit("⚠ Oscilloscope disconnected.", True)

    try:
        if getattr(screen, "osc_conn", None):
            screen.osc_conn.close()
    except Exception:
        pass
    screen.osc_conn = None

    while True:
        conn = OscilloscopeConnection()
        if conn.discover_and_connect():
            screen.osc_conn = conn
            screen.log_signal.emit("✅ Oscilloscope reconnected.", False)
            _restart_listener(screen, OscilloscopeListener, lambda: conn.instrument)
            break

        if screen.abort_event.is_set():
            screen.log_signal.emit("❌ Oscilloscope reconnect abandoned (test aborted).", True)
            break

        ev = Event()
        screen._queue_popup(
            "⚠ Oscilloscope Disconnected",
            "Please reconnect the oscilloscope.\n\n"
            "Check that:\n"
            "  • The USB cable is firmly connected\n"
            "  • The oscilloscope is powered ON\n\n"
            "Click OK once reconnected — the system will retry the connection.",
            None, "ok", None,
            callback=lambda result, popup: ev.set()
        )
        ev.wait()

        if screen.abort_event.is_set():
            screen.log_signal.emit("❌ Oscilloscope reconnect abandoned (test aborted).", True)
            break

    screen._osc_error_handled = False


def _restart_listener(screen, listener_cls, get_resource):
    """Swap in a fresh listener instance pointing at the reconnected resource."""
    try:
        resource = get_resource()
        if resource is None:
            return
        new_listener = listener_cls(resource)
        new_listener.disconnected.connect(screen.on_device_disconnected)
        screen.device_listeners = [
            l for l in screen.device_listeners if not isinstance(l, listener_cls)
        ]
        screen.device_listeners.append(new_listener)
        new_listener.start()
    except Exception:
        pass