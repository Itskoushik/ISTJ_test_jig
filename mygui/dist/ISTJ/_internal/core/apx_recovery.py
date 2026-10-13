"""
apx_recovery.py — APx500 crash / disconnect recovery coordinator.

When any APx operation raises SystemUnstableError or a COM/remoting error:

  1. Popup  → "Click Close on the APx error dialog, then OK here"
  2. Popup  → "Is APx powered on?" (yes / no)
  3. Kill → relaunch → configure APx (jbox or station-box mode)
  4. Restore last generator state (level + frequency)
  5. Popup  → "APx reconnected – click OK to resume"
  6. Retry the failed operation (read or generator call)

Also wraps generator_control so the last generator state is always
tracked and can be restored after a reconnect.

Install order in start_test():
  install_tuning_hooks(screen)    ← tuning layer  (inner)
  install_apx_recovery_hooks(screen)  ← recovery layer (outer)

Remove order in remove_tuning_hooks():
  remove_apx_recovery_hooks()     ← outer first
  … then restore tuning originals
"""

import time
import threading
import devices.apx_analyzer as _apx_module

from PyQt5.QtCore  import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame
)
from PyQt5.QtGui import QFont

# ── module-level state ────────────────────────────────────────────────────────
_active_screen        = None
_coordinator          = None
_original_read_apx    = None   # points at whichever fn was current when we installed
_original_gen_control = None
_recovery_in_progress = False

# Last known generator state — restored after reconnect
_last_gen_state = {
    "level":     None,   # e.g. "750.0 uVrms"
    "frequency": None,   # e.g. 1000
    "state":     "on",
}

# Strings that mean "APx crashed / COM channel lost" (not just a bad reading)
_CRASH_SIGNALS = (
    "SystemUnstableError",
    "APError",
    "APException",
    "The system has encountered an error",
    "TrackingServerSink",
    "RemotingException",
    "COMException",
    "connection to the instrument was lost",
    "RPC",
    "PrivateInvoke",
)


def _is_apx_crash(exc: Exception) -> bool:
    msg = str(exc)
    return any(s in msg for s in _CRASH_SIGNALS)


# =============================================================================
# Coordinator — all Qt / popup work on the main thread via QTimer
# =============================================================================

class APxRecoveryCoordinator:
    """
    Shows blocking modal dialogs from a background thread by posting
    requests to the main thread via a 50 ms QTimer.
    """

    def __init__(self, screen):
        self.screen = screen
        self._req_event  = threading.Event()
        self._done_event = threading.Event()
        self._title   = ""
        self._msg     = ""
        self._kind    = "ok"     # "ok" or "yes_no"
        self._result  = "ok"

        self._timer = QTimer()
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    # ── background-thread API ────────────────────────────────────────────
    def show_and_wait(self, title: str, msg: str, kind: str = "ok") -> str:
        """Block the calling (background) thread until the operator clicks."""
        self._title = title
        self._msg   = msg
        self._kind  = kind
        self._done_event.clear()
        self._req_event.set()
        self._done_event.wait()
        return self._result

    def stop(self):
        self._timer.stop()

    # ── main-thread poll ─────────────────────────────────────────────────
    def _tick(self):
        if not self._req_event.is_set():
            return
        self._req_event.clear()
        self._build_and_exec_dialog()

    def _build_and_exec_dialog(self):
        dlg = QDialog(self.screen)
        dlg.setWindowTitle(self._title)
        dlg.setMinimumWidth(480)
        dlg.setWindowFlags(
            dlg.windowFlags()
            | Qt.WindowStaysOnTopHint
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
        )
        dlg.setModal(True)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        icon_lbl = QLabel("⚠")
        icon_lbl.setFont(QFont("Arial", 30))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("color: #d32f2f;")
        lay.addWidget(icon_lbl)

        title_lbl = QLabel(f"<b>{self._title}</b>")
        title_lbl.setTextFormat(Qt.RichText)
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setFont(QFont("Arial", 11))
        lay.addWidget(title_lbl)

        sep1 = QFrame(); sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("color:#e0e0e0;"); lay.addWidget(sep1)

        msg_lbl = QLabel(self._msg)
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_lbl.setFont(QFont("Arial", 10))
        msg_lbl.setStyleSheet("color:#333; padding:4px;")
        lay.addWidget(msg_lbl)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color:#e0e0e0;"); lay.addWidget(sep2)

        btn_row = QHBoxLayout(); btn_row.setSpacing(12)

        if self._kind == "yes_no":
            yes_btn = QPushButton("✔  Yes — APx is Ready")
            yes_btn.setMinimumHeight(42)
            yes_btn.setFont(QFont("Arial", 10, QFont.Bold))
            yes_btn.setStyleSheet(
                "QPushButton{background:#2e7d32;color:white;border:none;"
                "border-radius:4px;padding:8px 16px;font-weight:bold}"
                "QPushButton:hover{background:#1b5e20}"
            )
            yes_btn.clicked.connect(
                lambda: (setattr(self, "_result", "yes"), dlg.accept())
            )

            no_btn = QPushButton("✘  No — APx is OFF")
            no_btn.setMinimumHeight(42)
            no_btn.setFont(QFont("Arial", 10, QFont.Bold))
            no_btn.setStyleSheet(
                "QPushButton{background:#d32f2f;color:white;border:none;"
                "border-radius:4px;padding:8px 16px;font-weight:bold}"
                "QPushButton:hover{background:#b71c1c}"
            )
            no_btn.clicked.connect(
                lambda: (setattr(self, "_result", "no"), dlg.accept())
            )
            btn_row.addWidget(yes_btn)
            btn_row.addWidget(no_btn)

        else:   # "ok"
            ok_btn = QPushButton("OK")
            ok_btn.setMinimumHeight(42)
            ok_btn.setMinimumWidth(140)
            ok_btn.setFont(QFont("Arial", 10, QFont.Bold))
            ok_btn.setStyleSheet(
                "QPushButton{background:#1a5da8;color:white;border:none;"
                "border-radius:4px;padding:8px 20px;font-weight:bold}"
                "QPushButton:hover{background:#154a8a}"
            )
            ok_btn.clicked.connect(
                lambda: (setattr(self, "_result", "ok"), dlg.accept())
            )
            btn_row.addWidget(ok_btn)

        lay.addLayout(btn_row)
        dlg.exec_()
        self._done_event.set()


# =============================================================================
# Recovery flow  (runs entirely on the background test thread)
# =============================================================================

def _run_apx_recovery(screen, is_junction_box: bool) -> bool:
    coord = _coordinator
    if coord is None:
        return False

    # ── WAIT FOR PSU FIRST — if PSU disconnect happened simultaneously ────
    psu_ready = getattr(screen, "_psu_ready_event", None)
    if psu_ready is not None and not psu_ready.is_set():
        screen.log_signal.emit(
            "⏸ APx recovery waiting for PSU reconnect to complete first…", False
        )
        psu_ready.wait(timeout=300)
        if getattr(screen, "abort_event", None) and screen.abort_event.is_set():
            return False
        screen.log_signal.emit("▶ PSU ready — proceeding with APx recovery.", False)

    # ── STEP 1: ask operator to dismiss the APx error dialog ─────────────
    coord.show_and_wait(
        "⚠ APx500 Error Detected",
        "The Audio Analyser (APx500) has encountered an error or lost connection.\n\n"
        "Please:\n"
        "  1.  Look at the APx500 application window.\n"
        "  2.  Click  'Close'  on the APx error popup that appeared there.\n"
        "  3.  Click  OK  here once you have dismissed it.",
        "ok",
    )

    # ── STEP 2: confirm APx is powered on ────────────────────────────────
    answer = coord.show_and_wait(
        "APx500 Power Check",
        "Is the APx500 Audio Analyser powered ON and the front-panel\n"
        "POWER light is lit?\n\n"
        "Please make sure APx500 Audio Analyser is connected to the PC via USB .\n\n"
        "Click  'Yes – APx is Ready'  to proceed with reconnection.\n"
        "Click  'No – APx is OFF'  if you need to power it on first.",
        "yes_no",
    )

    if answer == "no":
        coord.show_and_wait(
            "⏳ Please Power On APx500",
            "Please:\n"
            "  1.  Power on the APx500 Audio Analyser.\n"
            "  2.  Please make sure APx500 Audio Analyser is connected to the PC via USB .\n"
            "  3.  Wait until the instrument has fully booted.\n"
            "  4.  Click OK when it is ready.",
            "ok",
        )

    # ── STEP 3: kill → relaunch → configure (up to 5 attempts) ───────────
    from devices.apx_analyzer import kill_apx, connect_apx, configure_apx, configure_apx_jb

    MAX_ATTEMPTS = 5
    recovered = False

    for attempt in range(1, MAX_ATTEMPTS + 1):
        screen.log_signal.emit(
            f"🔄 APx recovery attempt {attempt}/{MAX_ATTEMPTS}…", True
        )
        try:
            kill_apx()
            time.sleep(5)   # allow full COM deregistration

            success, _ = connect_apx(log_callback=None)
            if not success:
                screen.log_signal.emit(
                    f"  Attempt {attempt}: connect_apx returned False", True
                )
                time.sleep(3)
                continue

            screen.log_signal.emit(f"  Attempt {attempt}: APx launched ✓", False)

            if is_junction_box:
                cfg_ok = configure_apx_jb(screen)
                cfg_label = "Junction Box (600 Ω)"
            else:
                cfg_ok = configure_apx(screen)
                cfg_label = "Station Box (50 Ω)"

            if cfg_ok:
                screen.log_signal.emit(
                    f"  APx configured for {cfg_label} ✓", False
                )
                recovered = True
                break
            else:
                screen.log_signal.emit(
                    f"  Attempt {attempt}: configure returned False", True
                )

        except Exception as exc:
            screen.log_signal.emit(
                f"  Attempt {attempt} exception: {exc}", True
            )

        # honour abort between attempts
        for _ in range(30):
            if screen.abort_event.is_set():
                return False
            time.sleep(0.1)

    if not recovered:
        coord.show_and_wait(
            "❌ APx500 Recovery Failed",
            f"APx500 could not be reconnected after {MAX_ATTEMPTS} attempts.\n\n"
            "The test will now be aborted.\n"
            "Please check the APx500 connection and restart the test.",
            "ok",
        )
        screen.abort_event.set()
        return False

    # ── STEP 4: restore last generator state ─────────────────────────────
    gs = _last_gen_state.copy()
    if gs["level"] is not None or gs["frequency"] is not None:
        try:
            screen.log_signal.emit(
                f"🔁 Restoring generator: {gs['level']} @ {gs['frequency']} Hz", False
            )
            # Call the ORIGINAL unwrapped generator_control so we don't
            # create recursive recovery loops
            if _original_gen_control is not None:
                _original_gen_control(
                    screen,
                    level=gs["level"],
                    frequency=gs["frequency"],
                    state="on",   # always on — meter needs a signal
                )
                time.sleep(0.5)
        except Exception as exc:
            screen.log_signal.emit(
                f"⚠ Generator restore warning: {exc}", True
            )

    # ── STEP 5: success popup ─────────────────────────────────────────────
    coord.show_and_wait(
        "✅ APx500 Reconnected",
        "The Audio Analyser has been reconnected and configured.\n\n"
        "The test will now resume from the point where it stopped.\n\n"
        "Click OK to continue.",
        "ok",
    )

    screen.log_signal.emit("✅ APx500 recovery complete — resuming test.", False)
    return True


# =============================================================================
# Wrappers
# =============================================================================

def _make_read_apx_wrapper(wrapped_fn):
    """
    Outer wrapper around read_apx_meter (which may itself already be
    tuning-wrapped).  Catches APx crash exceptions, runs recovery, retries.
    """

    def _wrapped(screen, label="Audio Analyser Reading",
                 min_v=None, max_v=None, max_thd=None,
                 unit="vrms", offset_vrms=None):
        global _recovery_in_progress

        try:
            return wrapped_fn(screen, label, min_v, max_v, max_thd, unit, offset_vrms)

        except Exception as exc:
            if not _is_apx_crash(exc):
                raise   # not a crash — let the normal exception propagate
            
            if getattr(screen, "abort_event", None) and screen.abort_event.is_set():
                return {"value": 0, "observation": "APX INTERRUPTED DURING ABORT", "result": "FAIL"}

            if _recovery_in_progress:
                raise   # already recovering — surface so outer caller can abort

            _recovery_in_progress = True
            screen.log_signal.emit(
                f"⚠ APx connection interrupted during [{label}]: {type(exc).__name__}", True
            )

            try:
                is_jb = getattr(screen, "is_junction_box_mode", lambda: False)()
                ok = _run_apx_recovery(screen, is_junction_box=is_jb)

                if not ok:
                    return {
                        "value": 0,
                        "observation": "APX RECOVERY FAILED",
                        "result": "FAIL",
                    }

                # ── Final PSU check before retry ─────────────────────────
                psu_ready = getattr(screen, "_psu_ready_event", None)
                if psu_ready is not None and not psu_ready.is_set():
                    screen.log_signal.emit(
                        "⏸ APx recovered — waiting for PSU before retrying…", False
                    )
                    psu_ready.wait(timeout=300)
                    if getattr(screen, "abort_event", None) and screen.abort_event.is_set():
                        return {
                            "value": 0,
                            "observation": "ABORTED DURING PSU WAIT",
                            "result": "FAIL",
                        }
                    screen.log_signal.emit("▶ PSU ready — retrying test step.", False)

                # Retry through the full chain (tuning wrapper is still active)
                screen.log_signal.emit(f"🔁 Retrying: [{label}]", False)
                result = wrapped_fn(
                    screen, label, min_v, max_v, max_thd, unit, offset_vrms
                )
                if result is None:
                    result = {
                        "value": 0,
                        "observation": "NO READING AFTER RECOVERY",
                        "result": "FAIL",
                    }
                return result

            finally:
                _recovery_in_progress = False

    return _wrapped


def _make_gen_control_wrapper(original_fn):
    """
    Wraps generator_control to:
      (a) track last generator state for post-recovery restore
      (b) recover and retry on APx crash
    """

    def _wrapped(screen, level=None, frequency=None, state=None, gen_scale=None):
        global _recovery_in_progress

        # Track state BEFORE calling so we know what to restore
        if level     is not None:
            _last_gen_state["level"]     = level
        if frequency is not None:
            _last_gen_state["frequency"] = frequency
        if state     is not None:
            _last_gen_state["state"]     = state

        try:
            return original_fn(
                screen, level=level, frequency=frequency,
                state=state, gen_scale=gen_scale
            )

        except Exception as exc:
            if not _is_apx_crash(exc):
                raise
            if getattr(screen, "abort_event", None) and screen.abort_event.is_set():
                return   # silently skip — generator off during abort doesn't need recovery
            
            if _recovery_in_progress:
                raise

            _recovery_in_progress = True
            screen.log_signal.emit(
                f"⚠ APx connection interrupted during generator_control: {type(exc).__name__}", True
            )

            try:
                is_jb = getattr(screen, "is_junction_box_mode", lambda: False)()
                ok = _run_apx_recovery(screen, is_junction_box=is_jb)

                if not ok:
                    return

                # ── Final PSU check before retry ─────────────────────────
                psu_ready = getattr(screen, "_psu_ready_event", None)
                if psu_ready is not None and not psu_ready.is_set():
                    screen.log_signal.emit(
                        "⏸ Generator retry waiting for PSU…", False
                    )
                    psu_ready.wait(timeout=300)
                    if getattr(screen, "abort_event", None) and screen.abort_event.is_set():
                        return

                # Retry the original generator call
                screen.log_signal.emit("🔁 Retrying generator_control…", False)
                original_fn(
                    screen, level=level, frequency=frequency,
                    state=state, gen_scale=gen_scale
                )

            finally:
                _recovery_in_progress = False

    return _wrapped


# =============================================================================
# Public API
# =============================================================================

def install_apx_recovery_hooks(screen):
    """
    Install APx recovery wrappers.

    MUST be called AFTER install_tuning_hooks() so that the recovery layer
    sits outside the tuning layer:
        recovery_wrapper( tuning_wrapper( original_fn ) )
    """
    global _original_read_apx, _original_gen_control
    global _active_screen, _coordinator

    _active_screen = screen

    if _coordinator is not None:
        _coordinator.stop()
    _coordinator = APxRecoveryCoordinator(screen)

    # ── read_apx_meter ─────────────────────────────────────────────────────
    # At this point _apx_module.read_apx_meter may already be tuning-wrapped.
    # We wrap whatever is current (tuning-wrapped or original).
    _original_read_apx = _apx_module.read_apx_meter
    recovery_read = _make_read_apx_wrapper(_original_read_apx)
    _apx_module.read_apx_meter = recovery_read

    # Patch test-module local bindings that were already patched by tuning hooks
    import sys
    for mod in list(sys.modules.values()):
        if mod is None or mod is _apx_module:
            continue
        if getattr(mod, "read_apx_meter", None) is _original_read_apx:
            try:
                setattr(mod, "read_apx_meter", recovery_read)
            except Exception:
                pass

    # ── generator_control ──────────────────────────────────────────────────
    _original_gen_control = _apx_module.generator_control
    recovery_gen = _make_gen_control_wrapper(_original_gen_control)
    _apx_module.generator_control = recovery_gen

    import sys
    for mod in list(sys.modules.values()):
        if mod is None or mod is _apx_module:
            continue
        if getattr(mod, "generator_control", None) is _original_gen_control:
            try:
                setattr(mod, "generator_control", recovery_gen)
            except Exception:
                pass

    screen.log_signal.emit("APx recovery hooks installed (read + generator)", False)


def remove_apx_recovery_hooks():
    """
    Restore functions to what they were before install_apx_recovery_hooks().
    Call this BEFORE remove_tuning_hooks() so the chain is unwound correctly.
    """
    global _original_read_apx, _original_gen_control
    global _active_screen, _coordinator

    if _coordinator is not None:
        _coordinator.stop()
        _coordinator = None

    import sys

    if _original_read_apx is not None:
        _apx_module.read_apx_meter = _original_read_apx
        for mod in list(sys.modules.values()):
            if mod is None or mod is _apx_module:
                continue
            if hasattr(mod, "read_apx_meter"):
                try:
                    setattr(mod, "read_apx_meter", _original_read_apx)
                except Exception:
                    pass
        _original_read_apx = None

    if _original_gen_control is not None:
        _apx_module.generator_control = _original_gen_control
        for mod in list(sys.modules.values()):
            if mod is None or mod is _apx_module:
                continue
            if hasattr(mod, "generator_control"):
                try:
                    setattr(mod, "generator_control", _original_gen_control)
                except Exception:
                    pass
        _original_gen_control = None

    _active_screen = None