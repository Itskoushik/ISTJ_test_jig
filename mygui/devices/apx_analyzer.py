import clr
import subprocess
import time
apx = None
from core.paths import RESOURCES_DIR
clr.AddReference(r"C:\Program Files\Audio Precision\APx500 9.2\API\AudioPrecision.API2.dll")
clr.AddReference(r"C:\Program Files\Audio Precision\APx500 9.2\API\AudioPrecision.API.dll")
from AudioPrecision.API import *


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

    if apx is not None:
        if log_callback:
            log_callback("APx already connected ✓", False)
        return True, apx

    try:

        if log_callback:
            log_callback("Checking Audio Analyzer (APx525)...", False)

        

        apx = APx500_Application()

        apx.Visible = False
        apx.CreateNewProject()
        apx.OperatingMode = APxOperatingMode.BenchMode

        version = apx.Version.SoftwareVersion

        if log_callback:
            log_callback(f"APx500 detected ✓ (Version {version})", False)

        return True, apx

    except Exception:

        kill_apx()

        if log_callback:
            log_callback("APx525 Audio Analyzer not detected", True)

        return False, None

def configure_apx(self):

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("APX not connected", True)
        return False

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
    

    self.log_signal.emit("APX configured successfully", False)

    return True


def generator_control(self,level=None, frequency=None, state=None):
    """
    Control APx generator.

    Args:
        level (str): Level with unit (example: "750 uVrms")
        frequency (int/float): Frequency in Hz
        state (str): "on" or "off"
    """
    #---------Generator config---------
    global apx

    if apx is None:
        raise Exception("APx not connected")

    # Set level
    if level is not None:
        apx.BenchMode.Generator.Levels.SetValue(
            OutputChannelIndex.Ch1,
            level
        )

    # Set frequency
    if frequency is not None:
        apx.BenchMode.Generator.Frequency.Value = frequency
        self.log_signal.emit(f"APx Generator set to {level} @ {frequency} Hz", False)
    # Handle generator state
    if state is not None:

        if state.lower() == "on":
            generator_state = True
        elif state.lower() == "off":
            generator_state = False
        else:
            raise ValueError("state must be 'on' or 'off'")

        apx.BenchMode.Generator.AutoOn = False
        apx.BenchMode.Generator.On = generator_state
        self.log_signal.emit(f"APx Generator turned {'ON' if generator_state else 'OFF'}", False)
        
        
def audible_reduce_until_silent(self, step_uv=30):

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {"threshold": None, "operator": "NO", "result": "FAIL"}

    try:

        apx.AudibleSignalMonitor.Enabled = True

        current_v = float(
            apx.BenchMode.Generator.Levels.GetValue(OutputChannelIndex.Ch1)
        )

        current_uv = current_v * 1_000_000

        self.operator_event.clear()
        self.last_operator_response = None

        self.show_popup_signal.emit(
            "🔉 IS THE TONE SILENT?",
            "Reducing generator level...\n\n"
            "Click YES when tone becomes silent.\n"
            "Click NO to fail the test.",
            RESOURCES_DIR / "hear.png",
            "yes_no",
            None
        )

        while True:

            current_uv -= step_uv

            if current_uv <= 0:
                current_uv = 0

            new_v = current_uv / 1_000_000

            apx.BenchMode.Generator.Levels.SetValue(
                OutputChannelIndex.Ch1,
                f"{new_v} Vrms"
            )

            if hasattr(self, "update_popup_signal"):
                self.update_popup_signal.emit(
                    f"🔉 Reducing Generator Level\n\n"
                    f"Current Level : {current_uv:.0f} uVrms"
                )

            time.sleep(0.6)

            operator = getattr(self, "last_operator_response", None)

            if operator == "YES":
                self.log_signal.emit("Operator clicked YES ✓", False)
                threshold = current_uv
                result = "PASS"
                break

            if operator == "NO":
                self.log_signal.emit("Operator clicked NO ❌", True)
                threshold = current_uv
                result = "FAIL"
                break

        apx.AudibleSignalMonitor.Enabled = False

        if hasattr(self, "register_test_result"):
            self.register_test_result(result)

        return {
            "threshold": f"{threshold:.0f} uVrms",
            "operator": operator,
            "result": result
        }

    except Exception as e:

        apx.AudibleSignalMonitor.Enabled = False
        self.log_signal.emit(f"Audible reduce error: {str(e)}", True)

        return {"threshold": None, "operator": "NO", "result": "FAIL"}
    
    
def audible_increase_until_audible(self, step_uv=30):

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {"threshold": None, "operator": "NO", "result": "FAIL"}

    try:

        apx.AudibleSignalMonitor.Enabled = True

        current_v = float(
            apx.BenchMode.Generator.Levels.GetValue(OutputChannelIndex.Ch1)
        )

        current_uv = current_v * 1_000_000

        self.operator_event.clear()
        self.last_operator_response = None

        # OPEN POPUP
        self.show_popup_signal.emit(
            "🔊 IS THE TONE AUDIBLE?",
            "Increasing generator level...\n\n"
            "Click YES when tone becomes audible.\n"
            "Click NO to fail the test.",
            RESOURCES_DIR / "hear.png",
            "yes_no",
            None
        )

        while True:

            # increase level
            current_uv += step_uv
            new_v = current_uv / 1_000_000

            apx.BenchMode.Generator.Levels.SetValue(
                OutputChannelIndex.Ch1,
                f"{new_v} Vrms"
            )

            if hasattr(self, "update_popup_signal"):
                self.update_popup_signal.emit(
                    f"🔊 Increasing Generator Level\n\n"
                    f"Current Level : {current_uv:.0f} uVrms"
                )

            time.sleep(0.6)

            operator = getattr(self, "last_operator_response", None)

            if operator == "YES":
                self.log_signal.emit("Operator clicked YES ✓", False)
                threshold = current_uv
                result = "PASS"
                break

            if operator == "NO":
                self.log_signal.emit("Operator clicked NO ❌", True)
                threshold = current_uv
                result = "FAIL"
                break

        apx.AudibleSignalMonitor.Enabled = False

        if hasattr(self, "register_test_result"):
            self.register_test_result(result)

        return {
            "threshold": f"{threshold:.0f} uVrms",
            "operator": operator,
            "result": result
        }

    except Exception as e:

        apx.AudibleSignalMonitor.Enabled = False
        self.log_signal.emit(f"Audible increase error: {str(e)}", True)

        return {"threshold": None, "operator": "NO", "result": "FAIL"}
    
def read_apx_meter(self,label="Audio Analyser Reading",min_v=None,max_v=None,max_thd=None,unit="vrms"):
    """
    Read APx RMS level and optionally check THD+N ratio.

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

        # -------- VRMS READ --------
        vrms_list = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.RmsLevelMeter))
        vrms = float(vrms_list[0])  # APX always returns Vrms

        # -------- THD+N READ --------
        thd = None
        if max_thd is not None:
            thd_list = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.ThdNRatioMeter))
            thd = float(thd_list[0])

        # -------- UNIT CONVERSION --------
        unit = unit.lower()

        factor = 1
        if unit == "vrms":
            factor = 1
        elif unit == "mvrms":
            factor = 1000
        elif unit == "uvrms":
            factor = 1000000

        display_value = vrms * factor
        display_v = f"{display_value:.4f} {unit}"

        # convert limits to Vrms
        min_val = float(min_v) / factor if min_v else None
        max_val = float(max_v) / factor if max_v else None
        max_thd_val = float(max_thd) if max_thd else None

        status = True

        # ----- VRMS CHECK -----
        if min_val is not None and vrms < min_val:
            status = False

        if max_val is not None and vrms > max_val:
            status = False

        # ----- THD CHECK -----
        if max_thd_val is not None and thd is not None:
            if thd > max_thd_val:
                status = False

        # -------- RANGE TEXT --------
        range_txt = ""

        if min_v and max_v:
            range_txt = f"(Range {min_v} - {max_v} {unit})"

        elif min_v:
            range_txt = f"(>{min_v} {unit})"

        elif max_v:
            range_txt = f"(<{max_v} {unit})"

        thd_txt = ""
        if max_thd_val is not None:
            thd_txt = f" THD+N={thd:.2f}% (<{max_thd_val}%)"

        result_text = "PASS" if status else "FAIL"

        if hasattr(self, "register_test_result"):
            self.register_test_result(result_text)

        # -------- LOG --------
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
            "value": display_value,
            "thd": thd,
            "observation": f"{display_v} {thd_txt}",
            "result": result_text
        }

    except Exception as e:
        self.log_signal.emit(f"APX read error: {str(e)}", True)
        return None


def get_apx():
    global apx
    return apx

def audible_tone_check(self):

    apx = get_apx()

    if apx is None:
        self.log_signal.emit("❌ APX not connected", True)
        return {"operator": "NO", "result": "FAIL"}

    try:

        gains = [
            ("x1", AudibleMonitorGain.x1),
            ("x3", AudibleMonitorGain.x3),
            ("x10", AudibleMonitorGain.x10),
            ("x30", AudibleMonitorGain.x30),
            ("x100", AudibleMonitorGain.x100),
            ("x300", AudibleMonitorGain.x300),
            ("x1K", AudibleMonitorGain.x1K)
        ]

        apx.AudibleSignalMonitor.Enabled = True

        detected_gain = None
        operator = "NO"

        # open popup once
        self.operator_event.clear()

        self.show_popup_signal.emit(
            "⚠ IS THE TONE AUDIBLE?",
            "Increasing audio monitor gain...\n\n"
            "Click YES when tone becomes audible.",
            RESOURCES_DIR / "hear.png",
            "yes_no",
            30
        )

        for gain_name, gain_val in gains:

            apx.AudibleSignalMonitor.Gain = gain_val

            if hasattr(self, "update_popup_signal"):
                self.update_popup_signal.emit(
                    f"🔊 Increasing Monitor Gain\n\n"
                    f"Current Gain : {gain_name}\n\n"
                    f"Click YES when tone becomes audible."
                )

            time.sleep(2)

            operator = getattr(self, "last_operator_response", None)

            if operator == "YES":
                detected_gain = gain_name
                break

        self.operator_event.set()

        apx.AudibleSignalMonitor.Enabled = False

        if detected_gain:
            self.log_signal.emit(
                f"Tone audible at gain {detected_gain} ✓",
                False
            )
            result = "PASS"
        else:
            self.log_signal.emit(
                "Tone not audible even at maximum gain x1K ❌",
                True
            )
            result = "FAIL"

        return {
            "operator": operator,
            "result": result,
            "gain": detected_gain
        }

    except Exception as e:

        apx.AudibleSignalMonitor.Enabled = False
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

        # wait if operator hasn't clicked yet
        if not self.operator_event.is_set():
            self.operator_event.wait()

        return {
            "final_gain": "x1",
            "result": "PASS"
        }

    except Exception as e:

        apx.AudibleSignalMonitor.Enabled = False
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
        self.log_signal.emit("Audio Signal Monitor OFF", False)

        result = "PASS" if operator == "YES" else "FAIL"

        if hasattr(self, "register_test_result"):
            self.register_test_result(result)

        return {
            "operator": operator,
            "result": result
        }

    except Exception as e:

        try:
            apx.AudibleSignalMonitor.Enabled = False
        except:
            pass

        self.log_signal.emit(f"Audible monitor error: {str(e)}", True)

        return {
            "operator": "NO",
            "result": "FAIL"
        }