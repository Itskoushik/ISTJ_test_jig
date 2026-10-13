from PyQt5.QtCore import pyqtSignal, QThread
from threading import Event
import time

class VoltageMonitorThread(QThread):
    voltage_signal = pyqtSignal(float, float)
    error_signal = pyqtSignal(str)

    def __init__(self, psu_send_command, stop_event: Event, channel: int = 1, parent=None):
        super().__init__(parent)
        self.psu_send_command = psu_send_command
        self.stop_event = stop_event
        self.channel = channel
        self.poll_interval = 2.0
        self._running = True

    def set_channel(self, channel: int):
        """Live-swap the display channel without restarting the thread."""
        self.channel = channel

    def stop(self):
        self._running = False
        self.stop_event.set()

    def safe_float(self, raw) -> float | None:
        """Convert raw string to float, return None on failure."""
        if raw is None:
            return None
        try:
            val = float(raw.strip())
            return val
        except (ValueError, AttributeError):
            return None

    def run(self):
        consecutive_failures = 0
        MAX_FAILURES = 5        # only die after 5 consecutive real failures

        try:
            while self._running and not self.stop_event.is_set():

                ch = self.channel  # snapshot — may change mid-loop via set_channel()

                # Select channel (write command — returns "", never None unless exception)
                # critical=False: a slow/failed reading here is just this poll cycle
                # missing a value — it must NEVER be mistaken for a real PSU
                # disconnect or trigger the popup-driven reconnect flow.
                self.psu_send_command(f"INST:NSEL {ch}", critical=False)

                if not self._running or self.stop_event.is_set():
                    break

                v_raw = self.psu_send_command("MEAS:VOLT?", critical=False)
                c_raw = self.psu_send_command("MEAS:CURR?", critical=False)

                voltage = self.safe_float(v_raw)
                current = self.safe_float(c_raw)

                if voltage is None or current is None:
                    # Empty string = PSU busy / reconnecting — skip this cycle, don't die
                    consecutive_failures += 1
                    if consecutive_failures >= MAX_FAILURES:
                        # Genuine sustained failure — exit and let reconnect restart us
                        break
                    # Wait a bit longer before retrying during reconnect
                    self.stop_event.wait(min(self.poll_interval * 2, 5.0))
                    continue

                # Successful read — reset failure counter
                consecutive_failures = 0

                if self._running and not self.stop_event.is_set():
                    self.voltage_signal.emit(voltage, current)

                self.stop_event.wait(self.poll_interval)

        except Exception:
            pass

        finally:
            self._running = False