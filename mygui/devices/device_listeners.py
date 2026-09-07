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

    def stop(self):
        self._running = False

    def pause(self):
        self._paused = True

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
            if self._paused:   # recheck after settle
                continue
            try:
                with self.psu_lock:
                    resp = self.psu_inst.query("*IDN?")
                if not resp:
                    raise Exception("Empty IDN")
                self.fail_count = 0

            except Exception as e:
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
    def __init__(self, serial_port, psu_inst=None, psu_lock=None):
        super().__init__(DeviceType.MCU, 800)
        self.ser = serial_port
        self.psu_inst = psu_inst
        self.psu_lock = psu_lock

    def _psu_ch3_is_on(self) -> bool:
        if self.psu_inst is None or self.psu_lock is None:
            return True  # no PSU handle wired at all — this is a wiring issue, not a device state
        try:
            with self.psu_lock:
                resp = self.psu_inst.query("OUTP? CH3").strip().upper()
            return resp in ("1", "ON")
        except Exception:
            # PSU unreachable → we cannot confirm CH3 is powering the board →
            # treat as NOT connected (fail-safe), not "assume fine"
            return False

    def run(self):
        while self._running:
            if self._paused:
                self.msleep(200)
                continue
            self.msleep(300)   # settle delay — lets port stabilize after resume
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

            except Exception as e:
                try:
                    if self.ser and self.ser.is_open:
                        self.ser.close()
                except Exception:
                    pass
                self.disconnected.emit(
                    DeviceType.MCU,
                    f"Microcontroller disconnected ({e})"
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
            try:
                resp = self.resource.query("*IDN?")
                if not resp:
                    raise Exception("Empty IDN")
            except Exception:
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
            try:
                resp = self.resource.query("*IDN?")
                if not resp:
                    raise Exception("Empty IDN")
            except Exception:
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
            try:
                apx = get_apx()
                if apx is None:
                    raise Exception("APx global is None")
                _ = apx.Version
                fail_count = 0
            except Exception:
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