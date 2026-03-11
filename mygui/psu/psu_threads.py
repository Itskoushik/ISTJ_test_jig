from PyQt5.QtCore import pyqtSignal, QThread
from threading import Event

class VoltageMonitorThread(QThread):
    voltage_signal = pyqtSignal(float, float)  # voltage, current
    error_signal = pyqtSignal(str)

    def __init__(self, psu_send_command, stop_event: Event, parent=None):
        super().__init__(parent)
        self.psu_send_command = psu_send_command
        self.stop_event = stop_event
        self.poll_interval = 0.5  # seconds

    def run(self):
        while not self.stop_event.is_set():
            try:
                voltage = float(self.psu_send_command("MEAS:VOLT?"))
                current = float(self.psu_send_command("MEAS:CURR?"))
                self.voltage_signal.emit(voltage, current)
            except Exception as e:
                # ⚠️ PSU busy / transient timeout — NOT a disconnect
                self.error_signal.emit(f"Voltage monitor warning: {e}")


            self.msleep(int(self.poll_interval * 1000))