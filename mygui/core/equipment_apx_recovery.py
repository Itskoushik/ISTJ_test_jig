"""
core/equipment_apx_recovery.py — Dedicated APX / Audio Precision recovery
for the EQUIPMENT SELF TEST screen (equipment_self_check_screen.py) ONLY.

This is intentionally a SEPARATE mechanism from:
  - core/apx_recovery.py         (used by the tuning / Single-Test /
                                   Full-Test workflow — untouched by this
                                   module, not imported, not modified)
  - the generic relay/STM32 recovery in self_dmm.py / self_psu.py
    (_relay_send → CH3 power-cycle + STM32 sync + relay replay)

Neither of those is used or triggered by anything in this file.

Recovery model — TEST-CASE LEVEL, operator-driven Retry button:

  1. An APX crash/disconnect is detected inside a wrapped APX API call
     (read_apx_meter, generator_control, read_apx_thd_freq) made from a
     device's own self-test module (self_audio_analyser.py,
     self_oscilloscope.py, self_istj.py) while it's running under
     Equipment Self Test.
  2. The failed call stops immediately — nothing further in that test
     case runs, and no other test case is touched.
  3. A popup tells the operator the APX connection was lost, to close
     the popup, fix/reconnect the APX analyzer, then click Retry.
  4. A "Retry APX Connection" button appears on the Equipment Self Test
     screen. The worker thread blocks (without freezing the GUI — it's
     already running on SelfTestWorker's own QThread) until the operator
     clicks it.
  5. On Retry: APX is reconnected + reconfigured (kill → relaunch →
     configure — reusing devices.apx_analyzer._reconnect_apx, the
     existing APX-specific reconnect helper). If that fails, the Retry
     button simply reappears so the operator can try again — no popup
     spam, no restart of the whole self test (requirement: repeated
     failures stay in recovery, repeated Retry stays available).
  6. Once APX is back, ONLY the originally-failed API call is retried,
     with the same arguments — i.e. only the current test case is
     re-run. Test cases that already passed are never re-run, and once
     the retry succeeds the calling test module simply continues on to
     the next test case exactly as it would have if the failure had
     never happened.
  7. If that retry crashes again, the whole cycle (popup → Retry →
     reconnect → retry) repeats from the top.
  8. If the operator aborts while recovery is waiting (on the popup or
     on the Retry button), this raises TestAbortRequested so the calling
     test module's existing abort/cleanup tail (turns the generator off,
     de-energizes relays, etc.) runs exactly as it does for any other
     abort — nothing new to maintain there.

Install once per Equipment Self Test run:
    install_equipment_apx_recovery_hooks(worker)   # start of run()
    remove_equipment_apx_recovery_hooks()          # run()'s finally block

`worker` here is the SelfTestWorker instance (equipment_self_check_screen.py)
and must provide: log_signal, operator_signal, _operator_event,
apx_retry_available_signal, _apx_retry_event, abort_event, device_name.
"""

import sys
import time
import devices.apx_analyzer as _apx_module
from devices.apx_analyzer import _reconnect_apx
from core.test_abort import TestAbortRequested

# ── module-level state ──────────────────────────────────────────────────
_active_screen           = None
_original_read_apx_meter = None
_original_generator_ctrl = None
_original_read_thd_freq  = None

# Strings that mean "APX crashed / COM channel lost" (not just a bad
# reading). Kept as its own copy, deliberately NOT shared with
# core/apx_recovery.py, so this module has no dependency on it and can't
# be affected by changes made there (or vice versa).
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
# Recovery flow — runs on the SelfTestWorker (background) thread
# =============================================================================

def _handle_apx_crash(screen, step_label: str) -> bool:
    if getattr(screen, "abort_event", None) is not None and screen.abort_event.is_set():
        return False

    device_label = getattr(screen, "device_name", None) or "the current"
    screen.log_signal.emit(
        f"⚠ APX connection/communication lost during [{step_label}]", True
    )

    # ── Step 1: notify operator, block until they close the popup ────────
    # Single combined popup — the operator must do BOTH things below
    # before clicking OK here; there is no second popup and no button.
    screen._operator_event.clear()
    screen.operator_signal.emit(
        "⚠ APX / Audio Precision Connection Lost",
        "The APX (Audio Precision) Analyzer connection or communication "
        f"was lost during the {device_label} self test "
        f"(step: {step_label}).\n\n"
        "Before clicking OK, please:\n\n"
        "  1.  Look at the APx500 application window and click 'Close' "
        "on the APx error popup that appeared there.\n"
        "  2.  Confirm the APx500 is powered ON (front-panel POWER light "
        "lit) and its USB cable to the PC is firmly connected.\n\n"
        "Once both are done, click OK — reconnection will be retried "
        "automatically. Only the current test step will be re-run, "
        "steps that already passed will not.",
        ""
    )
    screen._operator_event.wait()

    if screen.abort_event.is_set():
        return False

    # ── Step 2: reconnect automatically — no button, no re-prompt.
    #    Keeps retrying quietly in the background until it succeeds
    #    or an abort is requested. ─────────────────────────────────────
    attempt = 0
    while True:
        if screen.abort_event.is_set():
            return False

        attempt += 1
        screen.log_signal.emit(f"[APX RECOVERY] auto-reconnect attempt {attempt}…", False)
        try:
            is_jb = getattr(screen, "is_junction_box_mode", lambda: False)()
            ok = _reconnect_apx(screen, is_jb, attempt=1)
        except Exception as exc:
            print(f"[APX RECOVERY] reconnect raised: {exc}")
            ok = False

        if ok:
            screen.log_signal.emit(
                f"✅ APX reconnected — retrying [{step_label}]…", False
            )
            return True

        print(f"[APX RECOVERY] attempt {attempt} failed — retrying in 5s…")
        for _ in range(25):   # ~5s, abortable in 0.2s slices
            if screen.abort_event.is_set():
                return False
            time.sleep(0.2)


# =============================================================================
# Wrapper factory
# =============================================================================

def _make_recovery_wrapper(step_label, original_fn):
    """
    Wraps an APX API call so that an APX crash pauses just THIS call,
    runs the popup → Retry → reconnect cycle, and then retries this exact
    call (same args) — never anything earlier in the test module.
    """

    def _wrapped(*args, **kwargs):
        screen = args[0] if args else None
        while True:
            try:
                return original_fn(*args, **kwargs)
            except Exception as exc:
                if not _is_apx_crash(exc):
                    raise  # not an APX crash — let it propagate untouched

                if screen is None:
                    raise

                if getattr(screen, "abort_event", None) is not None and screen.abort_event.is_set():
                    raise

                recovered = _handle_apx_crash(screen, step_label)
                if not recovered:
                    # Abort was requested while waiting — let the calling
                    # test module's existing TestAbortRequested handler
                    # (generator OFF / relay OFF cleanup tail) run.
                    raise TestAbortRequested()
                # else: loop around and retry `original_fn` with the exact
                # same arguments — i.e. only this test case, nothing else.

    return _wrapped


def _patch_attr(attr_name: str, old_fn, new_fn):
    """
    Swap every live binding of `attr_name` that currently points at
    `old_fn` (by identity) over to `new_fn` — covers both
    devices.apx_analyzer's own attribute and any module that did
    `from devices.apx_analyzer import <attr_name>` (self_audio_analyser.py,
    self_oscilloscope.py, self_istj.py).
    """
    for mod in list(sys.modules.values()):
        if mod is None:
            continue
        if getattr(mod, attr_name, None) is old_fn:
            try:
                setattr(mod, attr_name, new_fn)
            except Exception:
                pass


# =============================================================================
# Public API
# =============================================================================

def install_equipment_apx_recovery_hooks(screen):
    """
    Install Equipment-Self-Test-only APX recovery around read_apx_meter,
    generator_control and read_apx_thd_freq. Call once at the start of
    SelfTestWorker.run(). Safe to call even for a run where the device
    under test never touches APX (PSU, DMM, Ethernet, RS232/RS422) — the
    wrapped functions simply never get invoked in that case.
    """
    global _active_screen
    global _original_read_apx_meter, _original_generator_ctrl, _original_read_thd_freq

    if _active_screen is not None:
        # Defensive — shouldn't happen (run() always pairs install/remove),
        # but don't double-wrap if it ever does.
        remove_equipment_apx_recovery_hooks()

    _active_screen = screen

    _original_read_apx_meter = _apx_module.read_apx_meter
    _original_generator_ctrl = _apx_module.generator_control
    _original_read_thd_freq  = _apx_module.read_apx_thd_freq

    wrapped_read      = _make_recovery_wrapper("Audio Level Measurement", _original_read_apx_meter)
    wrapped_generator = _make_recovery_wrapper("Generator Control", _original_generator_ctrl)
    wrapped_thd_freq  = _make_recovery_wrapper("THD+N / Frequency Measurement", _original_read_thd_freq)

    _patch_attr("read_apx_meter", _original_read_apx_meter, wrapped_read)
    _patch_attr("generator_control", _original_generator_ctrl, wrapped_generator)
    _patch_attr("read_apx_thd_freq", _original_read_thd_freq, wrapped_thd_freq)

    print("[APX RECOVERY] Equipment Self Test APX recovery hooks installed "
          "(measurement + generator + THD/Freq)")


def remove_equipment_apx_recovery_hooks():
    """Undo install_equipment_apx_recovery_hooks(). Idempotent."""
    global _active_screen
    global _original_read_apx_meter, _original_generator_ctrl, _original_read_thd_freq

    if _original_read_apx_meter is not None:
        current = _apx_module.read_apx_meter
        _patch_attr("read_apx_meter", current, _original_read_apx_meter)
        _original_read_apx_meter = None

    if _original_generator_ctrl is not None:
        current = _apx_module.generator_control
        _patch_attr("generator_control", current, _original_generator_ctrl)
        _original_generator_ctrl = None

    if _original_read_thd_freq is not None:
        current = _apx_module.read_apx_thd_freq
        _patch_attr("read_apx_thd_freq", current, _original_read_thd_freq)
        _original_read_thd_freq = None

    _active_screen = None