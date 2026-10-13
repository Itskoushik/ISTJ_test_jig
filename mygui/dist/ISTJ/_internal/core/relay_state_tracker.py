"""
relay_state_tracker.py — Tracks relay state for recovery after PSU reconnect.
"""

import time
from typing import Dict, Callable, Optional


class RelayStateTracker:
    """
    Records relay commands in order so state can be restored after PSU reconnect.
    """
    
    _commands: Dict[str, Callable] = {}
    _command_order = []
    _enabled = True

    # after
    _EXCLUDED_SUBSTRINGS = ("default", "sync")

    @classmethod
    def record(cls, cmd_name: str, cmd_func: Callable) -> None:
        """Record a relay command."""
        if not cls._enabled:
            return
        name_lower = cmd_name.lower()
        if any(token in name_lower for token in cls._EXCLUDED_SUBSTRINGS):
            return
        cls._commands[cmd_name] = cmd_func
        if cmd_name not in cls._command_order:
            cls._command_order.append(cmd_name)

    @classmethod
    def restore_all(cls, screen=None, delay: float = 1.0) -> bool:
        """Replay all recorded relay commands to restore state."""
        if not cls._command_order:
            if screen:
                screen.log_signal.emit("No relay state to restore", False)
            return True

        if screen:
            screen.log_signal.emit(
                f"🔁 Restoring {len(cls._command_order)} relay command(s)…",
                False
            )

        cls._enabled = False
        all_ok = True

        try:
            from core.stm32_commands import STM32RelayController

            for i, cmd_name in enumerate(cls._command_order, 1):
                if getattr(screen, "abort_event", None) and screen.abort_event.is_set():
                    if screen:
                        screen.log_signal.emit("Relay restore aborted", True)
                    all_ok = False
                    break

                # after
                cmd_func = cls._commands[cmd_name]
                print(f"[RELAY RESTORE] [{i}/{len(cls._command_order)}] {cmd_name}")
                
                ok = STM32RelayController.send_with_retry(cmd_func)
                if not ok:
                    if screen:
                        screen.log_signal.emit(f"  ⚠ Failed: {cmd_name}", True)
                    all_ok = False

                time.sleep(delay)

        finally:
            cls._enabled = True

        if all_ok and screen:
            screen.log_signal.emit("✅ Relay state restored successfully", False)
        elif not all_ok and screen:
            screen.log_signal.emit("⚠ Relay restore completed with failures", True)

        return all_ok

    @classmethod
    def clear(cls) -> None:
        """Clear all recorded commands. Call at start of each test."""
        cls._commands.clear()
        cls._command_order.clear()