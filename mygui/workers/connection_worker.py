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
        self.psu_inst = None  # ✅ Store live PSU instance


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
        
        # ── Fresh VISA state before every discovery run ──────────────────
        try:
            from devices.power_supply import reset_resource_manager
            reset_resource_manager()
        except Exception:
            pass

        found, connection, inst = discover_power_supply(
            lambda msg, err: self.log_signal.emit(msg, err),
            self.claimed_visa_resources
        )

        if found:
            self.psu_connection = connection
            self.psu_inst = inst  # ✅ Keep live instance
            self.device_status["PSU (Power Supply)"] = True
            self.log_signal.emit("Power Supply connected ✓", False)

            # ✅ Turn on CH3 at 5V / 1A immediately after PSU is found
            self._initialize_psu_ch3(inst)

        else:
            self.device_status["PSU (Power Supply)"] = False
            self.log_signal.emit("Power Supply not detected", True)

        # ===== UNIVERSAL VISA SCAN (DMM + OSCILLOSCOPE) =====
        self.log_signal.emit("Scanning VISA resources for instruments...", False)

        devices = scan_all_instruments(
            lambda msg, err: self.log_signal.emit(msg, err),
            skip_resources=self.claimed_visa_resources
        )
        # ── Close stale DMM handle before fresh discovery ─────────────────
        if self.dmm_connection:
            try:
                self.dmm_connection.close()
            except Exception:
                pass
            self.dmm_connection = None
        # ===== DMM =====
        if devices["dmm"]:
            self.dmm_connection = devices["dmm"]
            self.device_status["DMM (Digital Multimeter)"] = True
        else:
            self.log_signal.emit("No DMM detected", True)
            self.device_status["DMM (Digital Multimeter)"] = False
            
        # ── Close stale oscilloscope handle before fresh discovery ────────
        if self.oscilloscope_connection:
            try:
                self.oscilloscope_connection.close()
            except Exception:
                pass
            self.oscilloscope_connection = None    
        # ===== OSCILLOSCOPE =====
        scope_inst = devices.get("oscilloscope")
        if scope_inst:
            self.oscilloscope_connection = scope_inst
            self.oscilloscope_found = True
            self.device_status["Oscilloscope"] = True
        else:
            self.log_signal.emit("No oscilloscope detected", True)
            self.device_status["Oscilloscope"] = False
            self.oscilloscope_found = False

        # ── Close stale APx session before attempting fresh connect ──────
        try:
            from devices.apx_analyzer import close_apx
            close_apx()
            self.log_signal.emit("APx previous session closed ✓", False)
        except Exception:
            pass  # No previous session or close_apx not yet implemented — safe to ignore
        
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

    def _initialize_psu_ch3(self, inst):
        """
        After PSU discovery: turn on CH3 at 5V / 1A.
        Called immediately after a successful PSU connection.
        """
        try:
            self.log_signal.emit("Initializing PSU — enabling CH3 (5V / 1A)...", False)

            inst.write("SYST:REM")          # enter remote control mode
            time.sleep(0.2)

            inst.write("INST:NSEL 3")       # select channel 3
            time.sleep(0.1)

            inst.write("SOUR3:VOLT 5.0")    # set voltage to 5 V
            inst.write("SOUR3:CURR 1.0")    # set current limit to 1 A

            inst.write("OUTP ON")           # enable output for CH3
            time.sleep(0.5)                 # let PSU settle

            self.log_signal.emit("PSU CH3 ON: 5V / 1A ✓", False)

        except Exception as e:
            self.log_signal.emit(f"PSU CH3 initialization failed: {e}", True)

    def reset(self):
        """Call this before re-running discovery on reconnect."""
        from devices.power_supply import reset_resource_manager
        reset_resource_manager()
        self.claimed_visa_resources.clear()
        self.psu_inst = None
        # Close and clear all instrument handles so retry gets fresh instances
        if self.dmm_connection:
            try:
                self.dmm_connection.close()
            except Exception:
                pass
            self.dmm_connection = None

        if self.oscilloscope_connection:
            try:
                self.oscilloscope_connection.close()
            except Exception:
                pass
            self.oscilloscope_connection = None

        try:
            from devices.apx_analyzer import close_apx
            close_apx()
        except Exception:
            pass
        self.device_status = {k: False for k in self.device_status}