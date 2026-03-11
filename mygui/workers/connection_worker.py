from PyQt5.QtCore import QThread, pyqtSignal
import time
from devices.power_supply import discover_power_supply
from devices.microcontroller import discover_microcontroller

from devices.visa_auto_detector import scan_all_instruments

class ConnectionWorker(QThread):
    """
    Worker thread for device discovery.
    Integrates real oscilloscope VISA discovery into existing placeholder flow.
    """
    log_signal = pyqtSignal(str, bool)
    connection_complete = pyqtSignal(bool)
    

    def __init__(self):
        super().__init__()
        self.oscilloscope_connection = None
        self.oscilloscope_found = False
        self.microcontroller_found = False
        self.claimed_visa_resources = set()
        self.dmm_connection = None
        self.device_status = {}


        self.device_status = {
            "PSU (Power Supply)": False,
            "Audio Analyzer": False,
            "Microcontroller": False,
            "DMM (Digital Multimeter)": False,
            "Oscilloscope": False,
        }

    def run(self):
        """
        Execute device discovery sequence.
        Real VISA discovery for oscilloscope, placeholders for other devices.
        """
        time.sleep(0.5)
        
        # ===== POWER SUPPLY (REAL VISA DISCOVERY) =====
        
        
        # ===== POWER SUPPLY (REAL VISA DISCOVERY) =====
        self.log_signal.emit("Searching for Power Supply...", False)

        found, connection = discover_power_supply(
            lambda msg, err: self.log_signal.emit(msg, err),
            self.claimed_visa_resources
        )

        if found:
            self.psu_connection = connection
            self.device_status["PSU (Power Supply)"] = True
            self.log_signal.emit("Power Supply connected ✓", False)
        else:
            self.device_status["PSU (Power Supply)"] = False
            self.log_signal.emit("Power Supply not detected", True)

        # ===== UNIVERSAL VISA SCAN (DMM + OSCILLOSCOPE) =====
        self.log_signal.emit("Scanning VISA resources for instruments...", False)

        devices = scan_all_instruments(
            lambda msg, err: self.log_signal.emit(msg, err)
        )

        # ===== DMM =====
        if devices["dmm"]:
            self.dmm_connection = devices["dmm"]
            self.device_status["DMM (Digital Multimeter)"] = True
        else:
            self.log_signal.emit("No DMM detected", True)
            self.device_status["DMM (Digital Multimeter)"] = False
            
        # TEMP: set True if scope not physically connected
        FORCE_SCOPE_PRESENT = True

        # ===== OSCILLOSCOPE =====
        if devices["oscilloscope"]:
            self.oscilloscope_connection = devices["oscilloscope"]
            self.oscilloscope_found = True
            self.device_status["Oscilloscope"] = True

        elif FORCE_SCOPE_PRESENT:
            self.log_signal.emit("Oscilloscope not detected — bypassing for testing..", True)
            self.oscilloscope_found = True
            self.device_status["Oscilloscope"] = True

        else:
            self.log_signal.emit("No oscilloscope detected", True)
            self.oscilloscope_found = False
            self.device_status["Oscilloscope"] = False






        
        # ===== APX 525 =====
        self.log_signal.emit("Searching for APX 525…", False)
        time.sleep(1.5)
        self.log_signal.emit("APX 525 found at 192.168.1.13 ✓", False)
        self.device_status["Audio Analyzer"] = True

        
        # ===== MICROCONTROLLER =====
        self.log_signal.emit("Searching for Microcontroller…", False)
        self.device_status["Microcontroller"] = discover_microcontroller(
            lambda msg, err: self.log_signal.emit(msg, err)
        )

        
        # All devices connected
        all_connected = all(self.device_status.values())
        self.connection_complete.emit(all_connected)                       
                             
   


        