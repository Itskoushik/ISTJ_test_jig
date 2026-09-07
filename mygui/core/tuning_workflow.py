"""
tuning_workflow.py — QTimer-based coordinator, all Qt work on main thread.
Supports: DMM voltage, DMM resistance, APX meter readings.
Skips tuning popup when instrument not connected or STM32 command fails.

CRITICAL: microphone_audio.py and any test file that calls read_apx_meter
MUST import it as:
    import devices.apx_analyzer as apx_module
    apx_module.read_apx_meter(screen, ...)
NOT as:
    from devices.apx_analyzer import read_apx_meter
The latter binds a local reference that cannot be patched.
"""

import time
import threading
import core.dmm_reader as _dmm_module

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui  import QFont

from dialogs.tuning_popup import TuningPopup

_original_read_voltage    = None
_original_read_resistance = None
_original_read_apx_meter  = None
_apx_module_ref           = None   # keep reference for restore
_active_screen            = None
_coordinator              = None

# Observation strings that mean "instrument not available" — skip popup
_SKIP_OBSERVATIONS = {
    "NO DMM", "READ ERROR", "NO APX", "NO READING",
    "DMM NOT CONNECTED", "APX NOT CONNECTED",
}

_popup_section_title = ""

def set_popup_title(title: str):
    """Call once before a test section to label all tuning popups."""
    global _popup_section_title
    _popup_section_title = title

def _should_skip_tuning(result: dict) -> bool:
    """
    Return True when the failure is an instrument/connection issue,
    not a real out-of-range reading — no popup should be shown.
    """
    if result is None:
        return True
    obs = str(result.get("observation", "")).strip().upper()
    for skip in _SKIP_OBSERVATIONS:
        if skip in obs:
            return True
    # value==0 with a connection-error observation also skips
    if result.get("value", None) == 0 and result.get("result") == "FAIL":
        if obs in _SKIP_OBSERVATIONS:
            return True
    return False


# =============================================================================
# Tune-or-Skip decision popup
# =============================================================================

class TuningOrSkipPopup(QDialog):
    def __init__(self, label, parent=None, section_title=""):
        super().__init__(parent)
        self.setWindowTitle("Test Step Failed")
        self.setMinimumWidth(440)
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowStaysOnTopHint
            | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        self._choice = "tune"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        
        if section_title:
            sec_lbl = QLabel(section_title)
            sec_lbl.setAlignment(Qt.AlignCenter)
            sec_lbl.setFont(QFont("Arial", 9, QFont.Bold))
            sec_lbl.setStyleSheet(
                "color: white; background: #1a5da8; border-radius: 4px; padding: 4px 10px;"
            )
            layout.addWidget(sec_lbl)

        icon = QLabel("✘")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Arial", 32))
        icon.setStyleSheet("color: #d32f2f;")
        layout.addWidget(icon)

        msg = QLabel(f"<b>{label}</b><br><br>Test step <b>FAILED</b>.")
        msg.setTextFormat(Qt.RichText)
        msg.setAlignment(Qt.AlignCenter)
        msg.setFont(QFont("Arial", 10))
        layout.addWidget(msg)

        hint = QLabel(
            "Click <b>Start Tuning</b> to adjust hardware and retry,\n"
            "or <b>Skip</b> to continue to the next step."
        )
        hint.setTextFormat(Qt.RichText)
        hint.setAlignment(Qt.AlignCenter)
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet("color: #666;")
        layout.addWidget(hint)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(sep)

        btn_row = QHBoxLayout(); btn_row.setSpacing(12)

        tune_btn = QPushButton("🔧  Start Tuning")
        tune_btn.setMinimumHeight(46)
        tune_btn.setFont(QFont("Arial", 10, QFont.Bold))
        tune_btn.setStyleSheet(
            "QPushButton{background:#1a5da8;color:white;border:none;border-radius:4px}"
            "QPushButton:hover{background:#154a8a}")
        tune_btn.clicked.connect(self._pick_tune)

        skip_btn = QPushButton("⏭  Skip / Continue")
        skip_btn.setMinimumHeight(46)
        skip_btn.setFont(QFont("Arial", 10, QFont.Bold))
        skip_btn.setStyleSheet(
            "QPushButton{background:#757575;color:white;border:none;border-radius:4px}"
            "QPushButton:hover{background:#616161}")
        skip_btn.clicked.connect(self._pick_skip)

        btn_row.addWidget(tune_btn); btn_row.addWidget(skip_btn)
        layout.addLayout(btn_row)

    def _pick_tune(self): self._choice = "tune"; self.accept()
    def _pick_skip(self): self._choice = "skip"; self.accept()
    def closeEvent(self, e): self._choice = "tune"; e.accept()
    def get_choice(self): return self._choice


# =============================================================================
# Coordinator — all Qt interaction on main thread via QTimer
# =============================================================================

class TuningCoordinator:
    def __init__(self, screen):
        self.screen = screen
        self._label = ""; self._unit = "voltage"
        self._min = None; self._max = None

        self._decision_req    = threading.Event()
        self._decision_done   = threading.Event()
        self._decision_choice = "tune"
        self._decision_popup  = None

        self._tuning_open_req = threading.Event()
        self._tuning_done     = threading.Event()
        self._tuning_close    = threading.Event()
        self._tuning_popup    = None

        self._update_req    = threading.Event()
        self._update_value  = ""
        self._update_status = ""
        self._last_forced_value = None

        self._timer = QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # bg-thread API
    def ask_decision(self, label, unit, min_val, max_val):
        self._label = label; self._unit = unit
        self._min = min_val; self._max = max_val
        self._decision_done.clear()
        self._decision_req.set()
        self._decision_done.wait()
        return self._decision_choice

    def open_tuning(self, label, unit, min_val, max_val):
        self._label = label; self._unit = unit
        self._min = min_val; self._max = max_val
        self._tuning_done.clear()
        self._tuning_open_req.set()

    def update_live(self, display_value, status):
        self._update_value = display_value
        self._update_status = status
        self._update_req.set()

    def wait_tuning_done(self):
        self._tuning_done.wait()

    def close_tuning(self):
        self._tuning_close.set()

    def stop(self):
        self._timer.stop()
        for p in [self._decision_popup, self._tuning_popup]:
            if p is not None:
                try: p.close()
                except RuntimeError: pass
        self._decision_popup = None; self._tuning_popup = None

    # main-thread poll
    def _tick(self):
        if self._decision_req.is_set() and self._decision_popup is None:
            self._decision_req.clear()
            popup = TuningOrSkipPopup(self._label, parent=self.screen, section_title=_popup_section_title)
            popup.setWindowModality(Qt.ApplicationModal)
            self._decision_popup = popup
            popup.exec_()
            self._decision_choice = popup.get_choice()
            self._decision_popup = None
            self._decision_done.set()

        if self._tuning_open_req.is_set() and self._tuning_popup is None:
            self._tuning_open_req.clear()
            popup = TuningPopup(
            title=f"Tuning: {self._label}", unit=self._unit,
            min_val=self._min, max_val=self._max, parent=self.screen,
            section_title=_popup_section_title
        )
            popup.tuning_done.connect(self._on_tuning_done)
            popup.setWindowFlags(popup.windowFlags() | Qt.WindowStaysOnTopHint)
            popup.setWindowModality(Qt.NonModal)
            popup.show()
            QApplication.processEvents()
            self._tuning_popup = popup

        if self._update_req.is_set():
            self._update_req.clear()
            if self._tuning_popup is not None:
                try:
                    self._tuning_popup.update_reading(
                        self._update_value, self._update_status)
                except RuntimeError:
                    self._tuning_popup = None

        if self._tuning_close.is_set():
            self._tuning_close.clear()
            if self._tuning_popup is not None:
                try: self._tuning_popup.close()
                except RuntimeError: pass
                self._tuning_popup = None

    def _on_tuning_done(self):
        # Capture forced value before _tick clears _tuning_popup
        self._last_forced_value = None
        if self._tuning_popup is not None:
            try:
                self._last_forced_value = self._tuning_popup.get_forced_value()
            except RuntimeError:
                pass
        self._tuning_done.set()


# =============================================================================
# Helpers
# =============================================================================

def _parse_limit(s, unit):
    if s is None: return None
    s = str(s).strip().upper()
    if unit in ("voltage", "vrms", "mvrms", "uvrms"):
        s = s.replace("V", "")
        mult = 1e-3 if "M" in s else 1
        return float(s.replace("M", "")) * mult
    else:  # resistance
        s = s.replace("OHM", "").replace("Ω", "")
        if   "G" in s: return float(s.replace("G", "")) * 1e9
        elif "M" in s: return float(s.replace("M", "")) * 1e6
        elif "K" in s: return float(s.replace("K", "")) * 1e3
        return float(s)


def _check_limits(value, unit, min_val, max_val):
    try:
        lo = _parse_limit(min_val, unit)
        hi = _parse_limit(max_val, unit)
        if lo is not None and value < lo: return "FAIL"
        if hi is not None and value > hi: return "FAIL"
        return "PASS"
    except Exception:
        return "FAIL"


def _fmt_voltage(v):
    return f"{v:.2f} V" if abs(v) >= 1 else f"{v * 1000:.2f} mV"

def _fmt_resistance(v):
    if v >= 1e6: return f"{v / 1e6:.2f} MΩ"
    if v >= 1e3: return f"{v / 1e3:.2f} kΩ"
    return f"{v:.2f} Ω"

def _fmt_apx(v, unit="vrms"):
    u = unit.lower()
    if u == "mvrms": return f"{v:.2f} mVrms"
    if u == "uvrms": return f"{v:.2f} µVrms"
    return f"{v:.2f} Vrms"


def _live_read_dmm(unit):
    try:
        dmm = _dmm_module._dmm
        if dmm is None: return None
        if unit == "voltage":
            dmm.write(":FUNCtion:VOLTage:DC"); time.sleep(0.12)
            return float(dmm.query(":MEASure:VOLTage:DC?").strip())
        else:
            dmm.write(":FUNCtion:RESistance"); time.sleep(0.12)
            return float(dmm.query(":MEASure:RESistance?").strip())
    except Exception:
        return None


def _live_read_apx(unit="vrms"):
    try:
        from devices.apx_analyzer import get_apx
        from AudioPrecision.API import BenchModeMeterType
        apx = get_apx()
        if apx is None: return None
        readings = list(apx.BenchMode.Meters.GetReadings(BenchModeMeterType.RmsLevelMeter))
        vrms = float(readings[0])
        u = unit.lower()
        if u == "mvrms": return vrms * 1000
        if u == "uvrms": return vrms * 1_000_000
        return vrms
    except Exception:
        return None


# =============================================================================
# Core tuning flow (background thread)
# =============================================================================

def _handle_fail(original_fn, unit, label, min_val, max_val,
                 original_result, args, kwargs):
    coord = _coordinator; screen = _active_screen
    if coord is None or screen is None:
        return original_result

    choice = coord.ask_decision(label, unit, min_val, max_val)
    if choice == "skip":
        screen.log_signal.emit(f"⏭ Skipping tuning for [{label}]", False)
        return original_result

    screen.log_signal.emit(f"🔧 Tuning mode: [{label}]", False)

    # ── Turn generator ON for live monitoring ────────────────────────────
    if unit not in ("voltage", "resistance"):   # APX units only
        try:
            from devices.apx_analyzer import get_apx
            _apx = get_apx()
            if _apx is not None:
                _apx.BenchMode.Generator.On = True
                time.sleep(0.5)   # brief settle before live readings start
        except Exception as e:
            screen.log_signal.emit(f"[Tuning] Generator ON failed: {e}", True)

    coord.open_tuning(label, unit, min_val, max_val)

    stop_live = threading.Event()
    is_apx = unit not in ("voltage", "resistance")

    def _live_loop():
        while not stop_live.is_set() and not coord._tuning_done.is_set():
            val = _live_read_apx(unit) if is_apx else _live_read_dmm(unit)
            if val is not None:
                display = (_fmt_apx(val, unit) if is_apx
                           else (_fmt_voltage(val) if unit == "voltage"
                                 else _fmt_resistance(val)))
                status  = _check_limits(val, unit, min_val, max_val)
                coord.update_live(display, status)
            time.sleep(0.35)

    t = threading.Thread(target=_live_loop, daemon=True)
    t.start()
    coord.wait_tuning_done()
    stop_live.set(); t.join(timeout=1.0)

    # ── Check if operator used Ctrl+F Force Pass ──────────────────────────
    forced = coord._last_forced_value
    coord.close_tuning()

    if forced is not None:
        if unit == "voltage":
            obs = _fmt_voltage(forced)
        elif unit == "resistance":
            obs = _fmt_resistance(forced)
        else:
            obs = _fmt_apx(forced, unit)
        forced_status = _check_limits(forced, unit, min_val, max_val)
        status_icon = "✅" if forced_status == "PASS" else "❌"
        screen.log_signal.emit(
            f"[{label}]{obs} ({forced_status}) {status_icon}", False)
        if hasattr(screen, "register_test_result"):
            screen.register_test_result(forced_status)
        return {
            "value": round(forced, 2),
            "observation": f"{obs}",
            "result": forced_status
        }

    # ── Turn generator OFF before retry ──────────────────────────────────
    # read_apx_meter will do its own ON→settle→read→OFF sequence
    if unit not in ("voltage", "resistance"):
        try:
            from devices.apx_analyzer import get_apx
            _apx = get_apx()
            if _apx is not None:
                _apx.BenchMode.Generator.On = False
                time.sleep(1.0)   # let APx settle before retry fires
        except Exception as e:
            screen.log_signal.emit(f"[Tuning] Generator OFF failed: {e}", True)

    screen.log_signal.emit(f"🔁 Retrying: [{label}]", False)
    retry = original_fn(*args, **kwargs)   # ← read_apx_meter handles ON/OFF here
    if retry is None:
        retry = {"value": 0, "observation": "NO READING", "result": "FAIL"}

    if retry.get("result") == "PASS":
        screen.log_signal.emit(f"✅ [{label}] PASSED after tuning", False)
    else:
        screen.log_signal.emit(f"❌ [{label}] still FAILED after tuning – continuing", True)
        if hasattr(screen, "register_test_result"):
            screen.register_test_result("FAIL")
    return retry


# =============================================================================
# Wrappers
# =============================================================================

def _make_voltage_wrapper(original_fn):
    def _wrapped(screen, label="Voltage", min_val=None, max_val=None):
        result = original_fn(screen, label, min_val, max_val)
        if (result and result.get("result") == "FAIL"
                and not _should_skip_tuning(result)
                and _coordinator is not None):
            result = _handle_fail(
                original_fn, "voltage", label, min_val, max_val,
                result, args=(screen, label, min_val, max_val), kwargs={})
        return result
    return _wrapped


def _make_resistance_wrapper(original_fn):
    def _wrapped(screen, label="Resistance", min_val=None, max_val=None):
        result = original_fn(screen, label, min_val, max_val)
        if (result and result.get("result") == "FAIL"
                and not _should_skip_tuning(result)
                and _coordinator is not None):
            result = _handle_fail(
                original_fn, "resistance", label, min_val, max_val,
                result, args=(screen, label, min_val, max_val), kwargs={})
        return result
    return _wrapped


def _make_apx_wrapper(original_fn):
    """
    Wraps read_apx_meter(screen, label, min_v, max_v, max_thd, unit, offset_vrms).
    min_v / max_v are plain floats in the chosen unit.
    """
    def _wrapped(screen, label="Audio Analyser Reading",
                 min_v=None, max_v=None, max_thd=None, unit="vrms", offset_vrms=None):
        result = original_fn(screen, label, min_v, max_v, max_thd, unit, offset_vrms)
        if (result and result.get("result") == "FAIL"
                and not _should_skip_tuning(result)
                and _coordinator is not None):
            result = _handle_fail(
                original_fn, unit, label, min_v, max_v,
                result,
                args=(screen, label, min_v, max_v, max_thd, unit, offset_vrms),
                kwargs={})
        return result
    return _wrapped


# =============================================================================
# Public API
# =============================================================================

def install_tuning_hooks(screen):
    """
    MUST be called from the main thread (called inside start_test()).
    Patches both the dmm_reader module AND the apx_analyzer module so
    that calls through the module namespace are intercepted.
    """
    global _original_read_voltage, _original_read_resistance, _original_read_apx_meter
    global _apx_module_ref, _active_screen, _coordinator

    _active_screen = screen

    if _coordinator is not None:
        _coordinator.stop()
    _coordinator = TuningCoordinator(screen)

    # ── DMM hooks ─────────────────────────────────────────────────────────
    if _original_read_voltage is None:
        _original_read_voltage    = _dmm_module.read_voltage
        _original_read_resistance = _dmm_module.read_resistance

    _dmm_module.read_voltage    = _make_voltage_wrapper(_original_read_voltage)
    _dmm_module.read_resistance = _make_resistance_wrapper(_original_read_resistance)

    # ── APX hook ──────────────────────────────────────────────────────────
    try:
        import devices.apx_analyzer as _apx_mod
        _apx_module_ref = _apx_mod

        if _original_read_apx_meter is None:
            _original_read_apx_meter = _apx_mod.read_apx_meter

        wrapped = _make_apx_wrapper(_original_read_apx_meter)
        _apx_mod.read_apx_meter = wrapped

        # Also patch every test module that already did
        # "from devices.apx_analyzer import read_apx_meter"
        # so their local binding is updated too.
        import sys
        for mod_name, mod in list(sys.modules.items()):
            if mod is None or mod is _apx_mod:
                continue
            if getattr(mod, "read_apx_meter", None) is _original_read_apx_meter:
                try:
                    setattr(mod, "read_apx_meter", wrapped)
                except Exception:
                    pass

        print("Tuning hooks installed (DMM + APX)")
    except Exception as e:
        print(
            f"Tuning hooks installed (DMM only — APX hook failed: {e})")
    # ── APx crash recovery hooks (outer layer — must be last) ────────────
    try:
        from core.apx_recovery import install_apx_recovery_hooks
        install_apx_recovery_hooks(screen)
    except Exception as e:
        print(f"APx recovery hooks skipped: {e}")

def remove_tuning_hooks():
    global _original_read_voltage, _original_read_resistance, _original_read_apx_meter
    global _apx_module_ref, _active_screen, _coordinator
    # ── Remove recovery layer FIRST — unwinds outermost wrapper first ────
    try:
        from core.apx_recovery import remove_apx_recovery_hooks
        remove_apx_recovery_hooks()
    except Exception:
        pass
    if _coordinator is not None:
        _coordinator.stop(); _coordinator = None

    if _original_read_voltage is not None:
        _dmm_module.read_voltage    = _original_read_voltage
        _dmm_module.read_resistance = _original_read_resistance
        _original_read_voltage = None
        _original_read_resistance = None

    if _original_read_apx_meter is not None:
        # Restore apx_analyzer module
        if _apx_module_ref is not None:
            try:
                _apx_module_ref.read_apx_meter = _original_read_apx_meter
            except Exception:
                pass

        # Restore any test-module local bindings we patched
        import sys
        cur_wrapped = None
        if _apx_module_ref is not None:
            cur_wrapped = getattr(_apx_module_ref, "read_apx_meter", None)

        for mod_name, mod in list(sys.modules.items()):
            if mod is None or mod is _apx_module_ref:
                continue
            if (getattr(mod, "read_apx_meter", None) is cur_wrapped or
                    getattr(mod, "read_apx_meter", None) is not _original_read_apx_meter):
                try:
                    if hasattr(mod, "read_apx_meter"):
                        setattr(mod, "read_apx_meter", _original_read_apx_meter)
                except Exception:
                    pass

        _original_read_apx_meter = None
        _apx_module_ref = None

    _active_screen = None