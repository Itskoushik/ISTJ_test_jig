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

    def stop(self):
        self._running = False


class PSUListener(DeviceListener):
    def __init__(self, psu_inst, psu_lock):
        super().__init__(DeviceType.PSU, 1500)
        self.psu_inst = psu_inst
        self.psu_lock = psu_lock
        self.fail_count = 0   # 👈 important

    def run(self):
        while self._running:
            try:
                with self.psu_lock:   # 🔑 CRITICAL
                    self.psu_inst.write("*IDN?")
                    self.psu_inst.read()

                self.fail_count = 0  # reset on success

            except Exception as e:
                self.fail_count += 1

                # 🔕 Ignore transient PSU busy states
                if self.fail_count < 3:
                    self.msleep(self.poll_ms)
                    continue

                # ❌ 3 consecutive failures = REAL disconnect
                self.disconnected.emit(
                    DeviceType.PSU,
                    "Power Supply disconnected (USB/VISA lost)"
                )
                return

            self.msleep(self.poll_ms)




class STM32Listener(DeviceListener):
    def __init__(self, serial_port):
        super().__init__(DeviceType.MCU, 800)
        self.ser = serial_port

    def run(self):
        while self._running:
            try:
                # 🔴 OS-level disconnect detection
                if not self.ser.is_open:
                    raise Exception("Serial port closed")

                self.ser.write(b'\x02\x01\x03')
                time.sleep(0.1)

                data = self.ser.read(1)
                if not data:
                    raise Exception("No heartbeat")

            except Exception:
                self.disconnected.emit(
                    DeviceType.MCU,
                    "Microcontroller disconnected (COM port lost)"
                )
                return

            self.msleep(self.poll_ms)



# ===============================================================================