from PyQt5.QtCore import QThread, pyqtSignal
import time
from devices.power_supply import discover_power_supply
from devices.microcontroller import discover_microcontroller
from devices.apx_analyzer import connect_apx
from devices.visa_auto_detector import scan_all_instruments
from devices.oscilloscope import OscilloscopeConnection

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
        self.scope_manager = OscilloscopeConnection()


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
            
        

        # ===== OSCILLOSCOPE =====
        self.log_signal.emit("Searching for Oscilloscope...", False)

        try:

            # pass claimed resources so scope doesn't steal PSU/DMM
            self.scope_manager.claimed_visa_resources = self.claimed_visa_resources

            found = self.scope_manager.discover_and_connect()

            if found:

                self.oscilloscope_connection = self.scope_manager.instrument
                self.oscilloscope_found = True
                self.device_status["Oscilloscope"] = True

                ident = self.scope_manager.get_identification()

                if ident:
                    self.log_signal.emit(
                        f"Oscilloscope detected: {ident.manufacturer} {ident.model} ✓",
                        False
                    )

                # mark VISA resource as used
                if self.scope_manager.resource_string:
                    self.claimed_visa_resources.add(self.scope_manager.resource_string)

            else:
                self.log_signal.emit("No oscilloscope detected", True)
                self.device_status["Oscilloscope"] = False
                self.oscilloscope_found = False

        except Exception as e:

            self.log_signal.emit(f"Oscilloscope detection error: {e}", True)
            self.device_status["Oscilloscope"] = False
            self.oscilloscope_found = False






        
        # ===== AUDIO ANALYZER (APX525) =====
        self.log_signal.emit("Searching for Audio Analyzer (APx525)...", False)

        found, connection = connect_apx(
            lambda msg, err: self.log_signal.emit(msg, err)
        )

        if found:
            self.apx_connection = connection
            self.device_status["Audio Analyzer"] = True
            self.log_signal.emit("Audio Analyzer connected ✓", False)
        else:
            self.device_status["Audio Analyzer"] = False
            self.log_signal.emit("Audio Analyzer not detected", True)

        
        # ===== MICROCONTROLLER =====
        self.log_signal.emit("Searching for Microcontroller…", False)
        self.device_status["Microcontroller"] = discover_microcontroller(
            lambda msg, err: self.log_signal.emit(msg, err)
        )

        
        # All devices connected
        all_connected = all(self.device_status.values())
        self.connection_complete.emit(all_connected)                       
                             
   


        