"""
relay_command_tracker.py — Tracks relay commands in sequence.

When PSU disconnects during a test, this module records every STM32 relay
command issued so that after reconnection, the relay state can be fully
restored by replaying the command history (excluding set_default_states).

Usage:
    from relay_command_tracker import RelayCommandTracker
    tracker = RelayCommandTracker()
    tracker.record(STM32RelayController.set_j13_on, "set_j13_on")
    # On reconnect:
    tracker.replay(screen, delay=1.0)
    tracker.clear()
"""

import time
from typing import List, Tuple, Callable, Optional


class RelayCommandTracker:
    """
    Maintains an ordered list (heap/sequence) of relay commands issued
    during a test run. On PSU reconnect the sequence is replayed so the
    relay state matches what it was when the PSU disconnected.

    Rules:
    - set_default_states is NEVER recorded (it resets everything — replaying
      it mid-sequence would be destructive).
    - Each entry is (callable, display_name) so we can log what we're doing.
    - clear() is called at the start of each new test run.
    """

    def __init__(self):
        self._commands: List[Tuple[Callable, str]] = []
        self._enabled: bool = True   # set False during replay to avoid re-recording

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, fn: Callable, name: str) -> None:
        """
        Record a relay command.  Ignores set_default_states.
        Thread-safe: GIL protects list.append on CPython.
        """
        if not self._enabled:
            return
        if "default" in name.lower():
            return   # never record the reset command
        self._commands.append((fn, name))

    def replay(self, screen, delay: float = 1.0) -> bool:
        """
        Replay all recorded relay commands in order.
        Runs on whatever thread calls it (background reconnect thread).

        Args:
            screen: SingleTestScreen instance (for log_signal).
            delay:  Seconds to wait between each command (default 1 s).

        Returns:
            True if all commands succeeded, False if any failed.
        """
        if not self._commands:
            screen.log_signal.emit(
                "🔁 No relay commands to replay (sequence empty)", False
            )
            return True

        screen.log_signal.emit(
            f"🔁 Replaying {len(self._commands)} relay command(s) to restore state…",
            False,
        )

        self._enabled = False   # block re-recording during replay
        all_ok = True

        try:
            from core.stm32_commands import STM32RelayController

            for i, (fn, name) in enumerate(self._commands, start=1):
                if getattr(screen, "abort_event", None) and screen.abort_event.is_set():
                    screen.log_signal.emit(
                        "⚠ Relay replay aborted (abort_event set)", True
                    )
                    all_ok = False
                    break

                screen.log_signal.emit(
                    f"  [{i}/{len(self._commands)}] Replaying: {name}", False
                )
                ok = STM32RelayController.send_with_retry(fn)
                if not ok:
                    screen.log_signal.emit(
                        f"  ⚠ Command failed: {name}", True
                    )
                    all_ok = False
                    # continue — try remaining commands anyway

                time.sleep(delay)

        finally:
            self._enabled = True   # always re-enable recording after replay

        if all_ok:
            screen.log_signal.emit(
                "✅ Relay state fully restored after PSU reconnect.", False
            )
        else:
            screen.log_signal.emit(
                "⚠ Relay replay completed with some failures — check state.", True
            )

        return all_ok

    def clear(self) -> None:
        """Reset the sequence.  Call at the start of every new test run."""
        self._commands.clear()

    def __len__(self) -> int:
        return len(self._commands)

    def snapshot(self) -> List[Tuple[Callable, str]]:
        """Return a shallow copy of the current command list (for debugging)."""
        return list(self._commands)