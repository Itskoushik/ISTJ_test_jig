from PyQt5.QtCore import QThread, pyqtSignal
import time
from devices.device_types import DeviceType
    
class DeviceListener(QThread):
    disconnected = pyqtSignal(DeviceType, str)

    def __init__(self, device_type, poll_ms=1000):
        super().__init__()
        self.device_type = device_type
        self.poll_ms = poll_ms
        self._running = True
        self._paused = False
        self._polling = False

    def stop(self):
        self._running = False

    def _begin_poll(self) -> bool:
        self._polling = True
        if self._paused:
            self._polling = False
            return False
        return True

    def pause(self):
        self._paused = True
        deadline = time.monotonic() + 1.0      # bounded wait for an in-flight VISA/COM call
        while self._polling and time.monotonic() < deadline:
            time.sleep(0.01)

    def resume(self):
        self._paused = False


class PSUListener(DeviceListener):
    def __init__(self, psu_inst, psu_lock):
        super().__init__(DeviceType.PSU, 1500)
        self.psu_inst = psu_inst
        self.psu_lock = psu_lock
        self.fail_count = 0   # 👈 important

    # AFTER
    def run(self):
        just_resumed = True
        while self._running:
            if self._paused:
                just_resumed = True
                self.msleep(200)
                continue
            # Longer settle specifically on the very first pass after a
            # pause/resume cycle (e.g. right after set_default_states()'s
            # relay sweep) — 300ms is fine for steady-state polling but is
            # too short right after a burst of STM32 serial traffic on
            # systems where the PSU shares a USB hub with the relay
            # controller. Steady-state polling keeps the original 300ms so
            # this doesn't slow down normal operation.
            self.msleep(1200 if just_resumed else 300)
            just_resumed = False
            if not self._begin_poll():   # recheck after settle
                continue
            try:
                with self.psu_lock:
                    resp = self.psu_inst.query("*IDN?")
                self._polling = False
                if not resp:
                    raise Exception("Empty IDN")
                self.fail_count = 0

            except Exception as e:
                self._polling = False
                self.fail_count += 1
                if self.fail_count < 3:
                    self.msleep(self.poll_ms)
                    continue
                self.disconnected.emit(
                    DeviceType.PSU,
                    "Power Supply disconnected (USB/VISA lost)"
                )
                return
            self.msleep(self.poll_ms)




class STM32Listener(DeviceListener):
    # Consecutive *query-exception* failures required before we treat CH3
    # as actually off. A single VISA hiccup while the PSU handle is busy
    # (e.g. self-test writing to another channel at the same instant) must
    # not be mistaken for the board being de-powered.
    CH3_FAIL_THRESHOLD = 3

    # Consecutive OS-level failures (serial handle closed / COM port not
    # listed) required before treating the board as actually disconnected.
    # Right after a self-test's CH3 power-cycle, the port can briefly not
    # enumerate or the OS's port list can momentarily miss it for a single
    # poll — that used to fire "disconnected" (and the reconnect that
    # follows a poll later fired "reconnected"), producing a rapid
    # disconnect/reconnect toast flicker.
    OS_CHECK_FAIL_THRESHOLD = 3

    def __init__(self, serial_port, psu_inst=None, psu_lock=None):
        super().__init__(DeviceType.MCU, 800)
        self.ser = serial_port
        self.psu_inst = psu_inst
        self.psu_lock = psu_lock
        self.ch3_fail_count = 0
        self.os_check_fail_count = 0

    def _psu_ch3_is_on(self) -> bool:
        if self.psu_inst is None or self.psu_lock is None:
            return True  # no PSU handle wired at all — this is a wiring issue, not a device state
        try:
            with self.psu_lock:
                resp = self.psu_inst.query("OUTP? CH3").strip().upper()
            # A real, successful reply is authoritative — reset the
            # failure streak, and if it says OFF, report OFF immediately.
            # This keeps the "OFF is safety-critical" behavior intact.
            self.ch3_fail_count = 0
            return resp in ("1", "ON")
        except Exception:
            # Query itself failed (VISA busy/timeout/etc) — this is NOT a
            # confirmed "CH3 is off", just a failed attempt to check. Only
            # escalate to "not connected" after several of these in a row.
            self.ch3_fail_count += 1
            if self.ch3_fail_count < self.CH3_FAIL_THRESHOLD:
                return True
            return False

    def run(self):
        while self._running:
            if self._paused:
                self.msleep(200)
                continue
            self.msleep(300)   # settle delay — lets port stabilize after resume
            if not self._begin_poll():
                continue
            try:
                # ── ISTJ Controller is only "connected" while PSU CH3 is ON ──
                if not self._psu_ch3_is_on():
                    raise Exception("PSU Channel 3 is OFF")

                # OS-level disconnect — cheapest check, no serial traffic
                if not self.ser.isOpen():
                    raise Exception("Serial port closed")

                # Check port still exists at OS level
                import serial.tools.list_ports
                available = [p.device for p in serial.tools.list_ports.comports()]
                if self.ser.port not in available:
                    raise Exception("COM port vanished from OS")

                # A clean pass resets the OS-level failure streak — only a
                # run of consecutive failures is treated as a real disconnect.
                self._polling = False
                self.os_check_fail_count = 0

            except Exception as e:
                self._polling = False
                self.os_check_fail_count += 1
                if self.os_check_fail_count < self.OS_CHECK_FAIL_THRESHOLD:
                    # Not enough consecutive failures yet to trust this as
                    # a genuine disconnect — likely a transient USB
                    # re-enumeration hiccup. Keep polling instead of
                    # emitting immediately.
                    self.msleep(self.poll_ms)
                    continue
                try:
                    if self.ser and self.ser.is_open:
                        from core.stm32_commands import STM32RelayController
                        if self.ser is not STM32RelayController._default_state_conn:
                            self.ser.close()
                except Exception:
                    pass
                self.disconnected.emit(
                    DeviceType.MCU,
                    f"ISTJ CONTROLLER disconnected ({e})"
                )
                return
            self.msleep(self.poll_ms)

class OscilloscopeListener(DeviceListener):
    def __init__(self, visa_resource):
        super().__init__(DeviceType.OSC, 1500)
        self.resource = visa_resource

    def run(self):
        while self._running:
            if self._paused:
                self.msleep(200)
                continue
            self.msleep(300)   # settle delay — lets new VISA handle stabilize after resume
            if not self._begin_poll():
                continue
            try:
                resp = self.resource.query("*IDN?")
                self._polling = False
                if not resp:
                    raise Exception("Empty IDN")
            except Exception:
                self._polling = False
                self.disconnected.emit(
                    DeviceType.OSC,
                    "Oscilloscope disconnected (VISA lost)"
                )
                return
            self.msleep(self.poll_ms)


class DMMListener(DeviceListener):
    def __init__(self, visa_resource):
        super().__init__(DeviceType.DMM, 1500)
        self.resource = visa_resource

    def run(self):
        while self._running:
            if self._paused:
                self.msleep(200)
                continue
            self.msleep(300)   # settle delay — lets new VISA handle stabilize after resume
            if not self._begin_poll():
                continue
            try:
                resp = self.resource.query("*IDN?")
                self._polling = False
                if not resp:
                    raise Exception("Empty IDN")
            except Exception:
                self._polling = False
                self.disconnected.emit(
                    DeviceType.DMM,
                    "DMM disconnected (VISA lost)"
                )
                return

            self.msleep(self.poll_ms)


class AudioAnalyzerListener(DeviceListener):
    def __init__(self):
        super().__init__(DeviceType.AUDIO, 2000)

    def run(self):
        from devices.apx_analyzer import get_apx   # import inside thread to avoid circular import
        fail_count = 0
        while self._running:
            if self._paused:
                self.msleep(200)
                continue
            self.msleep(300)   # settle delay — lets new VISA handle stabilize after resume
            if not self._begin_poll():
                continue
            try:
                apx = get_apx()
                if apx is None:
                    raise Exception("APx global is None")
                _ = apx.Version
                self._polling = False
                fail_count = 0
            except Exception:
                self._polling = False
                fail_count += 1
                if fail_count < 3:
                    self.msleep(self.poll_ms)
                    continue
                self.disconnected.emit(
                    DeviceType.AUDIO,
                    "Audio Analyzer disconnected (APx DLL lost)"
                )
                return

            self.msleep(self.poll_ms)

# ===============================================================================