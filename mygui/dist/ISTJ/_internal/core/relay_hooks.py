"""
relay_hooks.py — PSU-dropout relay retry hooks + state tracking.

Wraps STM32RelayController.send_with_retry so that:
1. Relay commands are recorded in RelayStateTracker
2. On PSU error, waits for reconnect and retries
3. After PSU reconnect, relays are replayed to restore state
"""

import time
from core.stm32_commands import STM32RelayController
from core.relay_state_tracker import RelayStateTracker

_screen_ref = None
_original_send_with_retry = None


def install_relay_hooks(screen):
    global _screen_ref, _original_send_with_retry

    _screen_ref = screen

    if _original_send_with_retry is None:
        _original_send_with_retry = STM32RelayController.send_with_retry

    original = _original_send_with_retry
    _orig_func = original.__func__ if hasattr(original, '__func__') else original

    
    def patched_send_with_retry(cls, cmd_func, retries: int = 3) -> bool:
        ok = _orig_func(cls, cmd_func, retries)
        # ✅ Record the command if successful
        if ok and _screen_ref is not None:
            cmd_name = getattr(cmd_func, '__name__', str(cmd_func))
            RelayStateTracker.record(cmd_name, cmd_func)

        # ✅ On failure: wait for PSU, retry once, then record if successful
        if not ok and _screen_ref is not None:
            _screen_ref.log_signal.emit(
                "ERROR: Relay command failed — PSU may be reconnecting, retrying after PSU ready...", 
                True
            )
            
            # Block until PSU reconnect completes (or 5 min timeout)
            _screen_ref._psu_ready_event.wait(timeout=300)

            try:
                _screen_ref.check_abort()
            except Exception:
                return False

            time.sleep(1)
            ok = _orig_func(cls, cmd_func, retries)

            if ok:
                _screen_ref.log_signal.emit(
                    "✅ Relay command succeeded after PSU reconnect retry", 
                    False
                )
                # Record successful retry command
                cmd_name = getattr(cmd_func, '__name__', str(cmd_func))
                RelayStateTracker.record(cmd_name, cmd_func)
            else:
                _screen_ref.log_signal.emit(
                    "ERROR: Relay command failed even after PSU reconnect retry", 
                    True
                )

        return ok

    # ✅ Wrap correctly using classmethod
    STM32RelayController.send_with_retry = classmethod(patched_send_with_retry)


def remove_relay_hooks():
    global _screen_ref, _original_send_with_retry

    if _original_send_with_retry is not None:
        STM32RelayController.send_with_retry = _original_send_with_retry
        _original_send_with_retry = None

    _screen_ref = None