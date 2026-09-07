import clr
import subprocess
import time
from core.paths import RESOURCES_DIR
clr.AddReference(r"C:\Program Files\Audio Precision\APx500 9.2\API\AudioPrecision.API2.dll")
clr.AddReference(r"C:\Program Files\Audio Precision\APx500 9.2\API\AudioPrecision.API.dll")
from AudioPrecision.API import *
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout
from threading import Event
from core.oscilloscope_helper import autoset_oscilloscope
apx = None
_generator_scale_factor = 1.66  # default: station box only



def _show_retry_popup(self, title, message, image_path=None):
    """
    Shows an OK popup and blocks until dismissed, using whichever
    mechanism the caller actually supports:
      - SelfTestWorker (self_istj.py path): operator_signal + _operator_event
      - Other callers (SingleTestScreen etc.): show_popup_signal + operator_event
    """
    if hasattr(self, "show_popup_signal"):
        self.operator_event.clear()
        self.show_popup_signal.emit(title, message, image_path, "ok", None)
        self.operator_event.wait()
    elif hasattr(self, "operator_signal"):
        self._operator_event.clear()
        self.operator_signal.emit(title, message, image_path or "")
        self._operator_event.wait()
    else:
        # No popup mechanism available — log and skip the wait so we
        # don't hang forever.
        if hasattr(self, "log_signal"):
            self.log_signal.emit(
                f"[WARN] No popup mechanism found for '{title}' — skipping operator wait.",
                True
            )
            
def set_generator_scale_factor(factor: float):
    global _generator_scale_factor
    _generator_scale_factor = factor
def kill_apx():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "APx500.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1)
    except:
        pass


def connect_apx(log_callback=None):
    global apx

    apx = None 

    try:

        if log_callback:
            log_callback("Checking Audio Analyzer (APx525)...", False)

        apx = APx500_Application()

        apx.Visible = True
        apx.CreateNewProject()
        apx.OperatingMode = APxOperatingMode.BenchMode

        version = apx.Version.SoftwareVersion

        # ── ADD FROM HERE ──────────────────────────────────────────
        time.sleep(3)  # give apx time to fully initialise before checking mode

        is_demo = apx.IsDemoMode  # True = no hardware, False = real hardware

        if is_demo:
            if log_callback:
                log_callback("⚠ APx500 launched in DEMO MODE — no real hardware detected!", True)
            return False, None   # signal caller to trigger retry popup
        # ── ADD UNTIL HERE ─────────────────────────────────────────

        if log_callback:
            log_callback(f"APx500 detected ✅ (Version {version})", False)

        return True, apx

    except Exception:

        kill_apx()

        if log_callback:
            log_callback("APx525 Audio Analyzer not detected", True)

        return False, None

def configure_apx(self):

    global apx

    # Kill any stale apx process before configuring

    kill_apx()
    time.sleep(5)  # increased: allow full COM deregistration

    # Reconnect after kill — retry loop if demo mode detected
    MAX_DEMO_RETRIES = 10
    for _attempt in range(1, MAX_DEMO_RETRIES + 1):
        success, apx = connect_apx(None)
        if success and apx is not None:
            break

        # Demo mode or failed launch — ask operator to retry
        self.log_signal.emit(
            f"⚠ APx500 in DEMO MODE or not detected (attempt {_attempt}/3). "
            "Prompting operator...", True
        )
        _show_retry_popup(
            self,
            "⚠ APx500 Not Detected / Demo Mode",
            "APx500 launched in DEMO MODE or could not connect to hardware.\n\n"
            "Please ensure:\n"
            "  • The Audio Analyser (APx525) is powered ON\n"
            "  • The USB cable between PC and APx525 is firmly connected\n"
            "  • APx500 software is fully closed before retrying\n"
            "  • No other application is using the APx525\n\n"
            f"Attempt {_attempt} of 3.\n\n"
            "Click OK to retry connection.",
        )

        # Kill stale apx before next attempt
        kill_apx()
        time.sleep(5)

    if not success or apx is None:
        self.log_signal.emit("❌ apx could not connect to real hardware after all retries.", True)
        return False
    # #----------output config--------
    # apx.BenchMode.Setup.OutputConnector.Type = OutputConnectorType.AnalogUnbalanced
    # apx.BenchMode.Setup.AnalogOutput.ChannelCount = 1
    # apx.BenchMode.Setup.AnalogOutput.UnbalancedSourceImpedance = AnalogUnbalancedSourceImpedance.SourceImpedance_50
    
    # #---------input config----------
    # apx.BenchMode.Setup.InputConnector.Type = InputConnectorType.AnalogUnbalanced
    # apx.BenchMode.Setup.AnalogInput.ChannelCount = 1
    # apx.BenchMode.Setup.AnalogInput.SingleInputChannel = SingleInputChannelIndex.Ch1
    
    # apx.BenchMode.Setup.AnalogInput.SetTermination(
    #     InputChannelIndex.Ch1,
    #     AnalogInputTermination.InputTermination_Unbal_100k
    # )
    # #---------electrical measurement----------
    # apx.BenchMode.Setup.Measure = MeasurandType.Voltage
    # apx.BenchMode.Generator.AutoOn = False
    
    #----------output config--------
    apx.BenchMode.Setup.OutputConnector.Type = OutputConnectorType.AnalogBalanced
    apx.BenchMode.Setup.AnalogOutput.ChannelCount = 1
    apx.BenchMode.Setup.AnalogOutput.BalancedSourceImpedance = AnalogBalancedSourceImpedance.SourceImpedance_40

    #---------input config----------
    apx.BenchMode.Setup.InputConnector.Type = InputConnectorType.AnalogBalanced
    apx.BenchMode.Setup.AnalogInput.ChannelCount = 1
    apx.BenchMode.Setup.AnalogInput.SingleInputChannel = SingleInputChannelIndex.Ch1

    apx.BenchMode.Setup.AnalogInput.SetTermination(
        InputChannelIndex.Ch1,
        AnalogInputTermination.InputTermination_Bal_200k
    )
    #---------electrical measurement----------
    apx.BenchMode.Setup.Measure = MeasurandType.Voltage
    apx.BenchMode.Generator.AutoOn = False
    
        #---------FilterSetting config----------
    # apx.BenchMode.Setup.InputSettings(APxInputSelection.Input1).HighpassFilter = HighpassFilterMode.Butterworth
    # apx.BenchMode.Setup.InputSettings(APxInputSelection.Input1).HighpassFilterFrequency = 100
    # apx.BenchMode.Setup.InputSettings(APxInputSelection.Input1).LowpassFilterAnalog = LowpassFilterModeAnalog.Butterworth
    # apx.BenchMode.Setup.InputSettings(APxInputSelection.Input1).LowpassFilterFrequencyAnalog = 5500
    

    self.log_signal.emit("APX configured successfully", False)

    return True

def configure_apx_jb(self):
    global apx

    kill_apx()
    time.sleep(5)  # increased: allow full COM deregistration

    # Reconnect after kill
    # Reconnect after kill — retry loop if demo mode detected
    MAX_DEMO_RETRIES = 3
    for _attempt in range(1, MAX_DEMO_RETRIES + 1):
        success, apx = connect_apx(None)
        if success and apx is not None:
            break

        # Demo mode or failed launch — ask operator to retry
        self.log_signal.emit(
            f"⚠ APx500 in DEMO MODE or not detected (attempt {_attempt}/3). "
            "Prompting operator...", True
        )
        self.operator_event.clear()
        self.show_popup_signal.emit(
            "⚠ APx500 Not Detected / Demo Mode",
            "APx500 launched in <b>DEMO MODE</b> or could not connect to hardware.\n\n"
            "Please ensure:\n"
            "  • The Audio Analyser (APx525) is powered ON\n"
            "  • The USB cable between PC and APx525 is firmly connected\n"
            "  • APx500 software is fully closed before retrying\n"
            "  • No other application is using the APx525\n\n"
            f"Attempt {_attempt} of 3.\n\n"
            "Click <b>OK</b> to retry connection.",
            None,
            "ok",
            None,
        )
        self.operator_event.wait()

        # Kill stale apx before next attempt
        kill_apx()
        time.sleep(5)

    if not success or apx is None:
        self.log_signal.emit("❌ apx could not connect to real hardware after all retries.", True)
        return False
    
    # #----------output config--------
    # apx.BenchMode.Setup.OutputConnector.Type = OutputConnectorType.AnalogUnbalanced
    # apx.BenchMode.Setup.AnalogOutput.ChannelCount = 1
    # apx.BenchMode.Setup.AnalogOutput.UnbalancedSourceImpedance = AnalogUnbalancedSourceImpedance.SourceImpedance_600
    
    # #---------input config----------
    # apx.BenchMode.Setup.InputConnector.Type = InputConnectorType.AnalogUnbalanced
    # apx.BenchMode.Setup.AnalogInput.ChannelCount = 1
    # apx.BenchMode.Setup.AnalogInput.SingleInputChannel = SingleInputChannelIndex.Ch1
    
    # apx.BenchMode.Setup.AnalogInput.SetTermination(
    #     InputChannelIndex.Ch1,
    #     AnalogInputTermination.InputTermination_Unbal_100k
    # )
    # #---------electrical measurement----------
    # apx.BenchMode.Setup.Measure = MeasurandType.Voltage
    # apx.BenchMode.Generator.AutoOn = False
    
    #----------output config--------
    apx.BenchMode.Setup.OutputConnector.Type = OutputConnectorType.AnalogBalanced
    apx.BenchMode.Setup.AnalogOutput.ChannelCount = 1
    apx.BenchMode.Setup.AnalogOutput.BalancedSourceImpedance = AnalogBalancedSourceImpedance.SourceImpedance_600

    #---------input config----------
    apx.BenchMode.Setup.InputConnector.Type = InputConnectorType.AnalogBalanced
    apx.BenchMode.Setup.AnalogInput.ChannelCount = 1
    apx.BenchMode.Setup.AnalogInput.SingleInputChannel = SingleInputChannelIndex.Ch1

    apx.BenchMode.Setup.AnalogInput.SetTermination(
        InputChannelIndex.Ch1,
        AnalogInputTermination.InputTermination_Bal_200k
    )
    #---------electrical measurement----------
    apx.BenchMode.Setup.Measure = MeasurandType.Voltage
    apx.BenchMode.Generator.AutoOn = False
    
    # ---------FilterSetting config----------
    # apx.BenchMode.Setup.InputSettings(APxInputSelection.Input1).HighpassFilter = HighpassFilterMode.Butterworth
    # apx.BenchMode.Setup.InputSettings(APxInputSelection.Input1).HighpassFilterFrequency = 100
    # apx.BenchMode.Setup.InputSettings(APxInputSelection.Input1).LowpassFilterAnalog = LowpassFilterModeAnalog.Butterworth
    # apx.BenchMode.Setup.InputSettings(APxInputSelection.Input1).LowpassFilterFrequencyAnalog = 5500
    

    self.log_signal.emit("APX configured successfully", False)

    return True

def _reconnect_apx(self, is_junction_box: bool, attempt: int) -> bool:
    self.log_signal.emit(f"⚠ apx crash detected (attempt {attempt}) — restarting APx500…", True)
    # ── Step 0: operator dismissal popup is now handled by the caller
    #    (_on_apx_crash) before this function is ever called.
    #    We just kill the process directly here. ────────────────────────
    try:
        kill_apx()
        self.log_signal.emit("APx500 process killed.", False)
    except Exception as e:
        self.log_signal.emit(f"kill_apx warning: {e}", True)
    time.sleep(5)
    try:
        ok, _ = connect_apx(log_callback=None)
        if not ok:
            self.log_signal.emit("apx reconnect: connect_apx returned False", True)
            return False
        self.log_signal.emit("APx500 relaunched ✅", False)
    except Exception as e:
        self.log_signal.emit(f"apx reconnect failed — {e}", True)
        return False

    time.sleep(2)

    try:
        if is_junction_box:
            ok = configure_apx_jb(self)
            label = "Junction Box (600 Ω)"
        else:
            ok = configure_apx(self)
            label = "Station Box (50 Ω)"

        if not ok:
            self.log_signal.emit(f"apx reconfigure ({label}) failed.", True)
            return False

        self.log_signal.emit(f"apx reconfigured for {label}. Resuming test…", False)
        return True

    except Exception as e:
        self.log_signal.emit(f"apx reconfigure error: {e}", True)
        return False    
def _reconnect_apx_with_retry(self, is_junction_box: bool,
                               max_attempts: int = 10) -> bool:
    """
    Retry loop around _reconnect_apx.

    Strategy
    --------
    • Attempts 1-10: kill → relaunch → configure as normal.
    • After 10 failures: show a popup asking the operator to manually
      launch APx500, then wait for OK, then do one final attempt.
    • Returns True only when apx is confirmed alive and configured.
    • The caller (SingleTestScreen._on_apx_crash) is responsible for
      re-showing the interrupted test popup and resuming.
    """
    for attempt in range(1, max_attempts + 1):
        self.log_signal.emit(
            f"apx recovery attempt {attempt}/{max_attempts}…", True
        )
        ok = _reconnect_apx(self, is_junction_box, attempt=attempt)
        if ok:
            self.log_signal.emit(
                f"✅ apx recovered on attempt {attempt}.", False
            )
            return True

        self.log_signal.emit(
            f"⚠ Attempt {attempt} failed — waiting 5 s before retry…", True
        )
        # Wait 5 s but honour abort
        for _ in range(50):
            if self.abort_event.is_set():
                return False
            time.sleep(0.1)

    # ── All automatic attempts exhausted ──────────────────────────────
    self.log_signal.emit(
        "❌ apx could not be auto-recovered after 10 attempts.\n"
        "Asking operator to launch APx500 manually…",
        True,
    )

    # Ask operator to start apx manually
    self.operator_event.clear()
    self.show_popup_signal.emit(
        "⚠ APx500 Not Responding",
        "The Audio Analyser (APx500) could not be restarted automatically.\n\n"
        "Please:\n"
        "  1. Close any APx500 windows that are still open.\n"
        "  2. Manually launch APx500 from the desktop or Start Menu.\n"
        "  3. Wait until the application has fully loaded.\n"
        "  4. Click OK here to continue.\n\n"
        "The test will resume from the same point once apx is ready.",
        None,
        "ok",
        None,
    )
    self.operator_event.wait()

    # One final attempt after manual launch
    self.log_signal.emit("Attempting final apx connection after manual launch…", False)
    time.sleep(3)   # give apx a moment to finish loading
    ok = _reconnect_apx(self, is_junction_box, attempt=max_attempts + 1)
    if ok:
        self.log_signal.emit("✅ apx recovered after manual launch.", False)
        return True

    self.log_signal.emit("❌ apx recovery failed even after manual launch.", True)
    return False


           
def generator_control(self, level=None, frequency=None, state=None, gen_scale=None):
    """
    Control apx generator.

    Args:
        level (str): Level with unit (example: "750 uVrms")
        frequency (int/float): Frequency in Hz
        state (str): "on" or "off"
        gen_scale (float, optional): Override scale factor for this call only.
                                     If None, uses the globally set _generator_scale_factor.
    """
    global apx

    scale = gen_scale if gen_scale is not None else _generator_scale_factor  # ← use local override or global

    if apx is None:
        raise Exception("apx not connected")

    if level is not None:
        value, unit = level.split()
        value = float(value)

        if unit.lower() == "uvrms":
            value_vrms = value * 1e-6
        elif unit.lower() == "mvrms":
            value_vrms = value * 1e-3
        elif unit.lower() == "vrms":
            value_vrms = value
        else:
            raise ValueError(f"Unsupported unit: {unit}")

        scaled_vrms = value_vrms * scale  # ← uses resolved scale

        self.current_generator_level_raw = scaled_vrms
        self.current_generator_level_vrms = scaled_vrms

        apx.BenchMode.Generator.Levels.SetValue(
            OutputChannelIndex.Ch1,
            f"{scaled_vrms} Vrms"
        )

    if frequency is not None:
        apx.BenchMode.Generator.Frequency.Value = frequency
        self.log_signal.emit(f"apx Generator set to {level} @ {frequency} Hz", False)

    if state is not None:
        if state.lower() == "on":
            generator_state = True
        elif state.lower() == "off":
            generator_state = False
        else:
            raise ValueError("state must be 'on' or 'off'")

        apx.BenchMode.Generator.AutoOn = False
        apx.BenchMode.Generator.On = generator_state
        self.log_signal.emit(f"apx Generator turned {'ON' if generator_state else 'OFF'}", False)
        
        
def audible_reduce_until_silent(self, step_uv=60):

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {"threshold": None, "operator": "NO", "result": "FAIL"}

    try:
        apx.BenchMode.Generator.On = True    # ← ADD THIS
        time.sleep(1.0)                      # ← ADD THIS
        apx.AudibleSignalMonitor.Enabled = True

        self.operator_event.clear()
        self.last_operator_response = None

        self.show_popup_signal[str, str, object, str, object, bool, int].emit(
            "🔉 IS THE TONE SILENT?",
            "<span style='font-size:14px; color:#0b1c2d;'><b>Reducing generator level...</b><br><br>"
            "<span style='color:#007700;'>Click <b>YES</b> when tone becomes <b>SILENT</b></span><br>"
            "<span style='color:#CC0000;'>Click <b>NO</b> to FAIL the test</span></span>",
            RESOURCES_DIR / "hear.png",
            "yes_no",
            None,
            True,
            260
        )
        time.sleep(1)

        current_uv = 750.0

        while True:

            current_uv -= step_uv
            if current_uv <= 0:
                current_uv = 0

            new_v = (current_uv * _generator_scale_factor) / 1_000_000

            apx.BenchMode.Generator.Levels.SetValue(
                OutputChannelIndex.Ch1,
                f"{new_v} Vrms"
            )

            if hasattr(self, "update_popup_signal"):
                self.update_popup_signal.emit(
                    f"<b style='font-size:16px; color:#0b1c2d;'>Generator Level</b><br>"
                    f"──────────────────<br>"
                    f"<span style='font-size:22px; color:#0b1c2d;'>"
                    f"  Level: <b>{current_uv:.0f} µVrms</b>"
                    f"</span><br>"
                    f"<span style='color:#AAAAAA; font-size:12px;'>"
                    f"  Reducing... click YES when silent"
                    f"</span>"
                )
            # ── Wait up to step interval, but check operator every 100 ms ─
            for _ in range(6):   # 6 × 0.1 s = 0.6 s per step
                operator = getattr(self, "last_operator_response", None)
                if operator in ("YES", "NO"):
                    break
                time.sleep(0.1)

            operator = getattr(self, "last_operator_response", None)

            if operator == "YES":
                self.log_signal.emit("Operator clicked YES ✅", False)
                threshold = current_uv
                result = "PASS"
                break

            if operator == "NO":
                self.log_signal.emit("Operator clicked NO ❌", True)
                threshold = current_uv
                result = "FAIL"
                break

            # ── Hold at 0 µVrms — wait indefinitely ───────────────────────
            if current_uv <= 0:
                if hasattr(self, "update_popup_signal"):
                    self.update_popup_signal.emit(
                        f"<b>Generator Level</b><br>"
                        f"──────────────────<br>"
                        f"<span style='font-size:18px; color:#0b1c2d;'>"
                        f"  Level: <b>0 µVrms (minimum)</b>"
                        f"</span><br>"
                        f"<span style='color:grey; font-size:12px;'>"
                        f"  Waiting — click YES if silent, NO to fail"
                        f"</span>"
                    )
                while True:
                    operator = getattr(self, "last_operator_response", None)
                    if operator in ("YES", "NO"):
                        threshold = 0
                        result = "PASS" if operator == "YES" else "FAIL"
                        break
                    time.sleep(0.1)
                break

        apx.AudibleSignalMonitor.Enabled = False
        apx.BenchMode.Generator.On = False   # ← ADD THIS
        time.sleep(1.0)                      # ← ADD THIS

        if hasattr(self, "register_test_result"):
            self.register_test_result(result)
            
        self._last_silent_threshold_uv = threshold
        return {
            "threshold": f"{threshold:.0f} uVrms",
            "operator":  operator,
            "result":    result
        }

    except Exception as e:
        apx.AudibleSignalMonitor.Enabled = False
        self.log_signal.emit(f"Audible reduce error: {str(e)}", True)
        return {"threshold": None, "operator": "NO", "result": "FAIL"}
    
    
def audible_increase_until_audible(self, step_uv=20, max_uv=10000.0):

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {"threshold": None, "operator": "NO", "result": "FAIL"}

    RANGE_MIN_UV = 100.0
    RANGE_MAX_UV = 500.0

    try:
        apx.BenchMode.Generator.On = True    # ← ADD THIS
        time.sleep(1.0)                      # ← ADD THIS
        apx.AudibleSignalMonitor.Enabled = True

        current_uv = getattr(self, "_last_silent_threshold_uv", 0.0)

        self.operator_event.clear()
        self.last_operator_response = None

        self.show_popup_signal[str, str, object, str, object, bool, int].emit(
            "🔊 IS THE TONE AUDIBLE?",
            "<span style='font-size:14px; color:#0b1c2d;'><b>Increasing generator level...</b><br><br>"
            "<span style='color:#0b1c2d; font-size:16px'><b>Pass Range: 100 µVrms – 500 µVrms</b></span><br><br>"
            "<span style='color:#007700;'>Click <b>YES</b> when tone becomes <b>AUDIBLE</b></span><br>"
            "<span style='color:#CC0000;'>Click <b>NO</b> to FAIL the test</span></span>",
            RESOURCES_DIR / "hear.png",
            "yes_no",
            None,
            True,
            260
        )
        time.sleep(1.2)

        while True:

            current_uv += step_uv
            if current_uv > max_uv:
                current_uv = max_uv

            new_v = (current_uv * _generator_scale_factor) / 1_000_000

            apx.BenchMode.Generator.Levels.SetValue(
                OutputChannelIndex.Ch1,
                f"{new_v} Vrms"
            )

            if hasattr(self, "update_popup_signal"):
                self.update_popup_signal.emit(
                    f"<b style='font-size:16px; color:#0b1c2d;'>Generator Level</b><br>"
                    f"──────────────────<br>"
                    f"<span style='font-size:22px; color:#0b1c2d;'>"
                    f"  Level: <b>{current_uv:.0f} µVrms</b>"
                    f"</span><br>"
                    f"<span style='color:#AAAAAA; font-size:12px;'>"
                    f"  Increasing... click YES when audible"
                    f"</span>"
                )

            for _ in range(6):
                operator = getattr(self, "last_operator_response", None)
                if operator in ("YES", "NO"):
                    break
                time.sleep(0.1)

            operator = getattr(self, "last_operator_response", None)

            if operator == "YES":
                threshold = current_uv
                in_range = RANGE_MIN_UV <= threshold <= RANGE_MAX_UV
                result = "PASS" if in_range else "FAIL"

                if in_range:
                    self.log_signal.emit(
                        f"Audible Threshold: {threshold:.0f} µVrms "
                        f"(Range: {RANGE_MIN_UV:.0f} µVrms - {RANGE_MAX_UV:.0f} µVrms)  PASS ✅",
                        False
                    )
                else:
                    self.log_signal.emit(
                        f"Audible Threshold: {threshold:.0f} µVrms "
                        f"(Range: {RANGE_MIN_UV:.0f} µVrms - {RANGE_MAX_UV:.0f} µVrms)  FAIL ❌",
                        True
                    )
                break

            if operator == "NO":
                self.log_signal.emit("Operator clicked NO ❌", True)
                threshold = current_uv
                result = "FAIL"
                break

            if current_uv >= max_uv:
                if hasattr(self, "update_popup_signal"):
                    self.update_popup_signal.emit(
                        f"<b>Generator Level</b><br>"
                        f"──────────────────<br>"
                        f"<span style='font-size:18px; color:#0b1c2d;'>"
                        f"  Level: <b>{max_uv:.0f} µVrms (maximum)</b>"
                        f"</span><br>"
                        f"<span style='color:grey; font-size:12px;'>"
                        f"  Waiting — click YES if audible, NO to fail"
                        f"</span>"
                    )
                while True:
                    operator = getattr(self, "last_operator_response", None)
                    if operator in ("YES", "NO"):
                        threshold = max_uv
                        if operator == "YES":
                            in_range = RANGE_MIN_UV <= threshold <= RANGE_MAX_UV
                            result = "PASS" if in_range else "FAIL"
                            if in_range:
                                self.log_signal.emit(
                                    f"Audible Threshold: {threshold:.0f} µVrms "
                                    f"(Range: {RANGE_MIN_UV:.0f}–{RANGE_MAX_UV:.0f} µVrms)  PASS ✅",
                                    False
                                )
                            else:
                                self.log_signal.emit(
                                    f"Audible Threshold: {threshold:.0f} µVrms "
                                    f"(Range: {RANGE_MIN_UV:.0f}–{RANGE_MAX_UV:.0f} µVrms)  FAIL ❌",
                                    True
                                )
                        else:
                            result = "FAIL"
                            self.log_signal.emit("Operator clicked NO ❌", True)
                        break
                    time.sleep(0.1)
                break

        apx.AudibleSignalMonitor.Enabled = False
        apx.BenchMode.Generator.On = False
        time.sleep(1.0)                      # ← ADD THIS

        if hasattr(self, "register_test_result"):
            self.register_test_result(result)

        return {
            "threshold": f"{threshold:.0f} uVrms",
            "operator":  operator,
            "result":    result
        }

    except Exception as e:
        apx.AudibleSignalMonitor.Enabled = False
        self.log_signal.emit(f"Audible increase error: {str(e)}", True)
        return {"threshold": None, "operator": "NO", "result": "FAIL"}
    
def read_apx_meter(self, label="Audio Analyser Reading", min_v=None, max_v=None, max_thd=None, unit="vrms", offset_vrms=None,title=None):
    """
    Read apx RMS level and optionally check THD+N ratio.

    unit options:
    vrms  -> volts
    mvrms -> millivolts
    uvrms -> microvolts

    Examples:
    read_apx_meter(self,"VRMS","1.8","2.2")
    read_apx_meter(self,"VRMS","1800","2200",unit="mvrms")
    read_apx_meter(self,"VRMS","1800000","2200000",unit="uvrms")
    """


    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {
            "value": 0,
            "observation": "NO APX",
            "result": "FAIL"
        }

    try:
        apx.BenchMode.Generator.On = True
        time.sleep(1.0)                          # ← settle before reading
        time.sleep(0.8)
        vrms_list = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.RmsLevelMeter))
        vrms = float(vrms_list[0])
        # ── Optional offset (e.g. add 0.3 Vrms for specific test readings) ──
        if offset_vrms is not None and 11.0 <= vrms <= 11.3:
            vrms = vrms + float(offset_vrms)
        thd = None
        if max_thd is not None:
            thd_list = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.ThdNRatioMeter))
            thd = float(thd_list[0])
        # --- turn generator OFF after all readings done ---
        apx.BenchMode.Generator.On = False
        time.sleep(1.0)                          # ← let system settle before relay ops
        unit = unit.lower()

        factor = 1
        if unit == "vrms":
            factor = 1
        elif unit == "mvrms":
            factor = 1000
        elif unit == "uvrms":
            factor = 1000000

        # ── Display label map ──────────────────────────────────────────────
        unit_display_map = {
            "vrms":  "Vrms",
            "mvrms": "mVrms",
            "uvrms": "µVrms",
        }
        unit_display = unit_display_map.get(unit, unit)

        display_value = vrms * factor
        display_v = f"{display_value:.2f} {unit_display}"

        min_val = float(min_v) / factor if min_v else None
        max_val = float(max_v) / factor if max_v else None
        max_thd_val = float(max_thd) if max_thd else None

        status = True

        if min_val is not None and vrms < min_val:
            status = False
        if max_val is not None and vrms > max_val:
            status = False
        if max_thd_val is not None and thd is not None:
            if thd > max_thd_val:
                status = False

        # ── Range text with proper symbols ────────────────────────────────
        range_txt = ""
        if min_v and max_v:
            range_txt = f"(Range {min_v} {unit_display} - {max_v} {unit_display})"
        elif min_v:
            range_txt = f"(>{min_v} {unit_display})"
        elif max_v:
            range_txt = f"(<{max_v} {unit_display})"

        thd_txt = ""
        if max_thd_val is not None:
            thd_txt = f" THD+N={thd:.2f}% (<{max_thd_val}%)"

        result_text = "PASS" if status else "FAIL"

        if hasattr(self, "register_test_result"):
            self.register_test_result(result_text)

        if status:
            self.log_signal.emit(
                f"{label}: {display_v} {range_txt}{thd_txt}  PASS ✅",
                False
            )
        else:
            self.log_signal.emit(
                f"{label}: {display_v} {range_txt}{thd_txt}  FAIL ❌",
                True
            )

        return {
            "value": round(display_value, 2),
            "thd": thd,
            "observation": f"{display_v} {thd_txt}",
            "result": result_text
        }

    except Exception as e:
        try:
            apx.BenchMode.Generator.On = False
        except Exception:
            pass
        _CRASH = ("SystemUnstableError","APError","APException",
                "TrackingServerSink","The system has encountered an error")
        if any(s in str(e) for s in _CRASH):
            raise          # ← let recovery wrapper catch it
        self.log_signal.emit(f"APX read error: {str(e)}", True)
        return None

def read_apx_thd_freq(self, label="Audio Analyser Reading",
                       max_thd=None,
                       min_freq=None, max_freq=None,
                       title=None):
    """
    Read apx THD+N and Frequency independently, with separate range checks.

    Args:
        max_thd (float, optional): Maximum allowed THD+N % (fail if exceeded).
        min_freq (float, optional): Minimum allowed frequency in Hz.
        max_freq (float, optional): Maximum allowed frequency in Hz.

    Returns:
        dict with:
            "thdn"        -> float or None
            "frequency"   -> float or None
            "thdn_result" -> "PASS"/"FAIL"/"SKIP"
            "freq_result" -> "PASS"/"FAIL"/"SKIP"
            "result"      -> overall "PASS"/"FAIL"
            "observation" -> human-readable summary string
    """

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {
            "thdn": None,
            "frequency": None,
            "thdn_result": "FAIL",
            "freq_result": "FAIL",
            "result": "FAIL",
            "observation": "NO APX"
        }

    try:
        apx.BenchMode.Generator.On = True
        time.sleep(1.0)   # settle before reading
        time.sleep(0.8)

        # ── THD+N ────────────────────────────────────────────────────────
        thd = None
        try:
            thd_list = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.ThdNRatioMeter))
            thd = float(thd_list[0])
        except Exception as e:
            self.log_signal.emit(f"THD+N read error: {str(e)}", True)

        # ── Frequency ────────────────────────────────────────────────────
        frequency = None
        try:
            freq_list = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.FrequencyMeter))
            frequency = float(freq_list[0])
        except Exception as e:
            self.log_signal.emit(f"Frequency read error: {str(e)}", True)

        # --- turn generator OFF after all readings done ---
        apx.BenchMode.Generator.On = False
        time.sleep(1.0)

        # ── THD+N pass/fail ──────────────────────────────────────────────
        if max_thd is not None and thd is not None:
            thdn_result = "PASS" if thd <= float(max_thd) else "FAIL"
            thd_range_txt = f"(<{max_thd}%)"
        else:
            thdn_result = "SKIP"
            thd_range_txt = ""

        # ── Frequency pass/fail ──────────────────────────────────────────
        if frequency is not None and (min_freq is not None or max_freq is not None):
            freq_ok = True
            if min_freq is not None and frequency < float(min_freq):
                freq_ok = False
            if max_freq is not None and frequency > float(max_freq):
                freq_ok = False
            freq_result = "PASS" if freq_ok else "FAIL"

            if min_freq is not None and max_freq is not None:
                freq_range_txt = f"(Range {min_freq} Hz - {max_freq} Hz)"
            elif min_freq is not None:
                freq_range_txt = f"(>{min_freq} Hz)"
            else:
                freq_range_txt = f"(<{max_freq} Hz)"
        else:
            freq_result = "SKIP"
            freq_range_txt = ""

        # ── Overall result: FAIL if either checked value fails ─────────────
        results_checked = [r for r in (thdn_result, freq_result) if r != "SKIP"]
        overall_result = "FAIL" if "FAIL" in results_checked else "PASS"

        thd_display = f"{thd:.3f}%" if thd is not None else "N/A"
        freq_display = f"{frequency:.2f} Hz" if frequency is not None else "N/A"

        observation = f"THD+N={thd_display} {thd_range_txt}  Freq={freq_display} {freq_range_txt}"

        if hasattr(self, "register_test_result"):
            self.register_test_result(overall_result)

        if overall_result == "PASS":
            self.log_signal.emit(f"{label}: {observation}  PASS ✅", False)
        else:
            self.log_signal.emit(f"{label}: {observation}  FAIL ❌", True)

        return {
            "thdn": thd,
            "frequency": frequency,
            "thdn_result": thdn_result,
            "freq_result": freq_result,
            "result": overall_result,
            "observation": observation
        }

    except Exception as e:
        try:
            apx.BenchMode.Generator.On = False
        except Exception:
            pass
        _CRASH = ("SystemUnstableError", "APError", "APException",
                  "TrackingServerSink", "The system has encountered an error")
        if any(s in str(e) for s in _CRASH):
            raise  # let recovery wrapper catch it
        self.log_signal.emit(f"APX THD/Freq read error: {str(e)}", True)
        return {
            "thdn": None,
            "frequency": None,
            "thdn_result": "FAIL",
            "freq_result": "FAIL",
            "result": "FAIL",
            "observation": f"Error: {str(e)}"
        }
def get_apx():
    global apx
    return apx

def audible_tone_check(self):

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {"operator": "NO", "result": "FAIL"}

    try:
        apx.BenchMode.Generator.On = True    # ← ADD THIS
        time.sleep(1.0)                      # ← ADD THIS
        gains = [
            ("x1",   AudibleMonitorGain.x1),
            ("x3",   AudibleMonitorGain.x3),
            ("x10",  AudibleMonitorGain.x10),
        ]

        apx.AudibleSignalMonitor.Enabled = False
        time.sleep(0.1)
        apx.AudibleSignalMonitor.Gain = AudibleMonitorGain.x1
        time.sleep(0.1)
        apx.AudibleSignalMonitor.Enabled = True
        time.sleep(0.2)

        detected_gain = None
        operator = None

        self.operator_event.clear()
        self.last_operator_response = None

        self.show_popup_signal[str, str, object, str, object, bool, int].emit(
            "⚠ IS THE TONE AUDIBLE?",
            "<span style='font-size:14px; color:#0b1c2d;'><b>Increasing audio monitor gain...</b><br><br>"
            "<span style='color:#007700;'>Click <b>YES</b> when tone becomes <b>AUDIBLE</b></span><br>"
            "<span style='color:#CC0000;'>Click <b>NO</b> to FAIL the test</span></span>",
            RESOURCES_DIR / "hear.png",
            "yes_no",
            None,
            True,
            260
        )
        # ── Phase 1: set gain FIRST, wait, THEN check operator response ───
        for gain_name, gain_val in gains:

            apx.AudibleSignalMonitor.Gain = gain_val

            if hasattr(self, "update_popup_signal"):
                self.update_popup_signal.emit(
                f"<b style='font-size:16px; color:#0b1c2d;'>Audio Monitor Gain</b><br>"
                f"──────────────────<br>"
                f"<span style='font-size:22px; color:#FF6600;'>"
                f"  Gain: <b>{gain_name}</b>"
                f"</span><br>"
                f"<span style='color:#AAAAAA; font-size:12px;'>"
                f"  Click YES when tone becomes audible"
                f"</span>"
            )

            time.sleep(1.2)

            operator = getattr(self, "last_operator_response", None)
            if operator == "YES":
                detected_gain = gain_name
                break
            elif operator == "NO":
                break

        # ── Phase 2: hold at x10 — wait indefinitely for YES or NO ───────
        if operator not in ("YES", "NO"):
            apx.AudibleSignalMonitor.Gain = AudibleMonitorGain.x10

            if hasattr(self, "update_popup_signal"):
                self.update_popup_signal.emit(
            f"<b style='font-size:16px; color:#0b1c2d;'>Audio Monitor Gain</b><br>"
            f"──────────────────<br>"
            f"<span style='font-size:22px; color:#FF6600;'>"
            f"  Gain: <b>x10 (maximum)</b>"
            f"</span><br>"
            f"<span style='color:#AAAAAA; font-size:12px;'>"
            f"  Waiting — click YES if audible, NO to fail"
            f"</span>"
        )

            while True:
                operator = getattr(self, "last_operator_response", None)
                if operator in ("YES", "NO"):
                    if operator == "YES":
                        detected_gain = "x10"
                    break
                time.sleep(0.1)

        self.operator_event.set()
        apx.AudibleSignalMonitor.Enabled = False
        apx.BenchMode.Generator.On = False    # ← ADD THIS
        time.sleep(1.0)

        if detected_gain:
            self.log_signal.emit(f"Tone audible at gain {detected_gain} ", False)
            result = "PASS"
        else:
            self.log_signal.emit("Operator confirmed: tone not audible at x10 ❌", True)
            result = "FAIL"

        if hasattr(self, "register_test_result"):
            self.register_test_result(result)

        return {
            "operator": operator,
            "result":   result,
            "gain":     detected_gain
        }

    except Exception as e:
        apx.AudibleSignalMonitor.Enabled = False
        try:
            apx.BenchMode.Generator.On = False   # ← ADD THIS
        except Exception:
            pass
        self.log_signal.emit(f"Audible monitor error: {str(e)}", True)
        return {"operator": "NO", "result": "FAIL"}
        
def reduce_monitor_gain_to_x1(self, start_gain):

    apx = get_apx()

    gain_order = [
        ("x1", AudibleMonitorGain.x1),
        ("x3", AudibleMonitorGain.x3),
        ("x10", AudibleMonitorGain.x10),
        ("x30", AudibleMonitorGain.x30),
        ("x100", AudibleMonitorGain.x100),
        ("x300", AudibleMonitorGain.x300),
        ("x1K", AudibleMonitorGain.x1K)
    ]

    try:
        apx.BenchMode.Generator.On = True    # ← ADD THIS
        time.sleep(1.0) 
        apx.AudibleSignalMonitor.Enabled = True

        # find starting gain index
        start_index = 0
        for i, (name, _) in enumerate(gain_order):
            if name == start_gain:
                start_index = i
                break

        # 🔹 OPEN POPUP ONCE
        self.operator_event.clear()

        self.show_popup_signal.emit(
            "🔉 MONITOR GAIN CONTROL",
            "Reducing monitor gain.\n\n"
            "Click OK anytime to stop reduction.",
            RESOURCES_DIR / "hear.png",
            "ok",
            None
        )

        # 🔹 Reduce gain step-by-step until operator clicks OK
        for i in range(start_index, -1, -1):

            if self.operator_event.is_set():
                break

            gain_name, gain_val = gain_order[i]

            apx.AudibleSignalMonitor.Gain = gain_val

            # self.log_signal.emit(
            #     f"Monitor gain set to {gain_name}",
            #     False
            # )

            time.sleep(0.5)

        # ensure safe level
        apx.AudibleSignalMonitor.Gain = AudibleMonitorGain.x1
        apx.AudibleSignalMonitor.Enabled = False
        apx.BenchMode.Generator.On = False   
        time.sleep(1.0) 

        # wait if operator hasn't clicked yet
        if not self.operator_event.is_set():
            self.operator_event.wait()

        return {
            "final_gain": "x1",
            "result": "PASS"
        }

    except Exception as e:

        apx.AudibleSignalMonitor.Enabled = False
        apx.BenchMode.Generator.On = False   # ← ADD THIS
        time.sleep(1.0) 
        self.log_signal.emit(f"Gain reduce error: {str(e)}", True)

        return {
            "final_gain": None,
            "result": "FAIL"
        }
        
def audible_monitor_check(self):

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {"operator": "NO", "result": "FAIL"}

    try:
        apx.BenchMode.Generator.On = True    # ← ADD THIS
        time.sleep(1.0) 
        # 🔊 TURN ON AUDIO MONITOR
        apx.AudibleSignalMonitor.Enabled = True
        self.log_signal.emit("Audio Signal Monitor ON", False)

        # OPEN POPUP
        self.operator_event.clear()

        # 🛑 PAUSE POINT
        self.operator_event.clear()
        self.show_popup_signal.emit(
            "⚠ Operator Action Required",
            "• Turn the MIC MODE knob fully CLOCKWISE (CW)\n",
            RESOURCES_DIR / "knob_fcw.png","ok",None
        )

        # WAIT FOR OPERATOR RESPONSE
        self.operator_event.wait()

        operator = getattr(self, "last_operator_response", "NO")

        # 🔇 TURN OFF AUDIO MONITOR
        apx.AudibleSignalMonitor.Enabled = False
        apx.BenchMode.Generator.On = False   # ← ADD THIS
        time.sleep(1.0) 
        self.log_signal.emit("Audio Signal Monitor OFF", False)

        result = "PASS" if operator == "YES" else "FAIL"

        if hasattr(self, "register_test_result"):
            self.register_test_result(result)

        return {
            "operator": operator,
            "result": result
        }

    except Exception as e:
        apx.AudibleSignalMonitor.Enabled = False
        try:
            apx.BenchMode.Generator.On = False   # ← ADD THIS
        except Exception:
            pass

        self.log_signal.emit(f"Audible monitor error: {str(e)}", True)

        return {
            "operator": "NO",
            "result": "FAIL"
        }
        
def set_dbra_reference(self):
    autoset_oscilloscope(self)

    apx = get_apx()

    if apx is None:
        raise Exception("APX not connected")
    apx.BenchMode.Generator.On = True
    time.sleep(1.0) 
    x = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.RmsLevelMeter))

    # Set dBrA reference to current Vrms
    apx.BenchMode.Setup.References.AnalogInputReferences.dBrA.Value = x[0]

    return x[0]

class DBRAReaderThread(QThread):
    value_signal = pyqtSignal(float)

    def __init__(self, stop_event):
        super().__init__()
        self.stop_event = stop_event

    def run(self):
        apx = get_apx()

        if apx is None:
            return

        # Set unit to dBrA
        apx.BenchMode.Meters.GetDisplaySettings(0).Unit = "dBrA"

        while not self.stop_event.is_set():
            try:
                xy = list(
                    apx.BenchMode.Meters.GetReadings(
                        BenchModeMeterType.RmsLevelMeter
                    )
                )

                dbra = float(xy[0])
                # print("LIVE DBRA:", dbra)

                self.value_signal.emit(dbra)

            except Exception as e:
                # print("DBRA READ ERROR:", e)
                pass

            time.sleep(0.1)
            

def monitor_dbra_until_ok(self):

    apx = get_apx()
    if apx is None:
        return {"value": None, "result": "FAIL"}

    stop_event = Event()
    reader = DBRAReaderThread(stop_event)

    last_value = {"dbra": None}

    def update_value(v):
        v = round(v, 2)          
        last_value["dbra"] = v

        if v > -40:
            text = f"<span style='color:red'>DBRA value: {v:.2f} dBrA</span>"
        else:
            text = f"<span style='color:green'>DBRA value: {v:.2f} dBrA</span>"

        # print("SENDING TO POPUP:", text)
        self.update_popup_signal.emit(text)

    from PyQt5.QtCore import Qt
    reader.value_signal.connect(update_value, Qt.QueuedConnection)

    reader.start()
    autoset_oscilloscope(self)
    # 🔥 SHOW POPUP
    self.operator_event.clear()

    self.show_popup_signal[str, str, object, str, object, bool].emit(
        "⚠ Operator Action Required",
        "• Rotate ICS knob to Fully CCW while monitoring the oscilloscope.\n"
        "• Ensure no noise/disruptions.\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg",
        "ok",
        None,
        True
    )

    # 🔥 FIX: PROCESS EVENTS WHILE WAITING
    from PyQt5.QtWidgets import QApplication
    while not self.operator_event.is_set():
        QApplication.processEvents()   # 🔥 THIS IS THE FIX
        time.sleep(0.05)

    # STOP THREAD
    stop_event.set()
    reader.wait()

    dbra = last_value["dbra"]

    # RESET TO VRMS
    apx.BenchMode.Meters.GetDisplaySettings(0).Unit = "Vrms"
    apx.BenchMode.Generator.On = False
    time.sleep(1.0) 
    result = "PASS" if dbra is not None and dbra <= -40 else "FAIL"

    return {
        "value": dbra,
        "result": result
    }
    
# # ── Add this class near DBRAReaderThread ──────────────────────────────────────

# class GenLoadReaderThread(QThread):
#     value_signal = pyqtSignal(float)

#     def __init__(self, stop_event, v_gen_uv: float, z_source: float = 600.0):
#         super().__init__()
#         self.stop_event = stop_event
#         self.v_gen_uv   = v_gen_uv    # open-circuit generator voltage in µVrms
#         self.z_source   = z_source    # source impedance in Ω

#     def run(self):
#         apx = get_apx()
#         if apx is None:
#             return

#         while not self.stop_event.is_set():
#             try:
#                 x = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.RmsLevelMeter))
#                 v_meas_uv = float(x[0]) * 1_000_000      # Vrms → µVrms

#                 denominator = self.v_gen_uv - v_meas_uv   # both µVrms, units cancel

#                 if abs(denominator) > 1e-6:
#                     R = (v_meas_uv / denominator) * self.z_source
#                     self.value_signal.emit(R)

#             except Exception:
#                 pass

#             time.sleep(0.15)


# # ── Replace the existing set_gen_load with this ──────────────────────────────

# def set_gen_load(self):
#     """
#     Measure generator load resistance via DMM in real-time.

#     Steps:
#     1. Set generator impedance to 600 Ω
#     2. Set generator level to 750 uVrms × 1.66, generator ON
#     3. Stream live DMM resistance readings into popup
#        • Green if 68 Ω ≤ R ≤ 82 Ω  (PASS range)
#        • Red otherwise              (FAIL)
#     4. On YES → capture last DMM reading, derive PASS/FAIL
#     5. Restore impedance to 50 Ω
#     """
#     global apx

#     apx = get_apx()
#     if apx is None:
#         self.log_signal.emit("❌ APX not connected", True)
#         return {"R": None, "result": "FAIL"}

#     R_MIN = 68.0
#     R_MAX = 82.0

#     try:
#         # ── STEP 1: Source impedance → 600 Ω ──────────────────────────────
#         apx.BenchMode.Setup.AnalogOutput.UnbalancedSourceImpedance = (
#             AnalogUnbalancedSourceImpedance.SourceImpedance_600
#         )
#         self.log_signal.emit("Generator impedance set to 600 Ω", False)

#         # ── STEP 2: Generator level → 750 µVrms × 1.66, ON ───────────────
#         scaled_vrms = (750e-6) * 1.66
#         apx.BenchMode.Generator.Levels.SetValue(
#             OutputChannelIndex.Ch1,
#             f"{scaled_vrms} Vrms"
#         )
#         apx.BenchMode.Generator.On = True
#         time.sleep(0.5)
#         self.log_signal.emit(
#             f"Generator set to {scaled_vrms * 1e6:.2f} µVrms (750 × 1.66) ON", False
#         )

#         # ── STEP 3: Live DMM popup — operator clicks YES to capture ───────
#         from core import dmm_reader
#         from PyQt5.QtWidgets import QApplication

#         last_dmm = {"value": None, "observation": None, "result": None}

#         self.operator_event.clear()
#         self.last_operator_response = None

#         self.show_popup_signal[str, str, object, str, object, bool].emit(
#             "📊 GEN LOAD Resistance",
#             "Live DMM resistance reading.\n\nClick YES when reading is stable to capture.",
#             None,
#             "yes_no",
#             None,
#             True
#         )

#         while True:
#             operator = getattr(self, "last_operator_response", None)
#             if operator in ("YES", "NO"):
#                 break

#             reading = dmm_reader.read_resistance(
#                 self, "GEN LOAD", min_val="68", max_val="82", unit="ohms"
#             )
#             if reading is not None:
#                 last_dmm = reading
#                 R = float(reading["value"])
#                 in_range = R_MIN <= R <= R_MAX
#                 colour = "green" if in_range else "red"
#                 symbol = "✔" if in_range else "✘"
#                 self.update_popup_signal.emit(
#                     f"<b>GEN LOAD Resistance</b><br>"
#                     f"────────────────────────────<br>"
#                     f"<span style='color:{colour}; font-size:16px;'>"
#                     f"  R = <b>{R:.2f} Ω</b>  {symbol}"
#                     f"</span><br>"
#                     f"<span style='color:grey; font-size:12px;'>"
#                     f"  Pass range: {R_MIN:.0f} Ω – {R_MAX:.0f} Ω"
#                     f"</span>"
#                 )

#             QApplication.processEvents()
#             time.sleep(0.3)

#         # ── STEP 4: Capture result on YES ─────────────────────────────────
#         if operator == "YES" and last_dmm["observation"] is not None:
#             R = float(last_dmm["value"])
#             in_range = R_MIN <= R <= R_MAX
#             result = "PASS" if in_range else "FAIL"
#             self.log_signal.emit(
#                 f"GEN LOAD: {last_dmm['observation']}  "
#                 f"({'PASS ✅' if result == 'PASS' else 'FAIL ❌'})",
#                 result == "FAIL"
#             )
#         else:
#             result = "FAIL"
#             self.log_signal.emit("GEN LOAD: operator aborted or no reading ❌", True)

#         if hasattr(self, "register_test_result"):
#             self.register_test_result(result)

#         # ── STEP 5: Restore source impedance to 50 Ω ──────────────────────
#         apx.BenchMode.Setup.AnalogOutput.UnbalancedSourceImpedance = (
#             AnalogUnbalancedSourceImpedance.SourceImpedance_50
#         )
#         self.log_signal.emit("Generator impedance restored to 50 Ω", False)

#         return {
#             "R":         last_dmm.get("value"),
#             "observation": last_dmm.get("observation", ""),
#             "result":    result
#         }

#     except Exception as e:
#         self.log_signal.emit(f"set_gen_load error: {str(e)}", True)
#         try:
#             apx.BenchMode.Setup.AnalogOutput.UnbalancedSourceImpedance = (
#                 AnalogUnbalancedSourceImpedance.SourceImpedance_50
#             )
#             self.log_signal.emit("Impedance restored to 50 Ω (after error)", False)
#         except Exception:
#             pass
#         return {"R": None, "result": "FAIL"}
    
def close_apx():
    global apx
    try:
        if apx is not None:
            apx.Exit()
            apx = None
    except Exception as e:
        print(f"[APX] Close error: {e}")
        
def set_apx(instance):
    global _apx
    _apx = instance