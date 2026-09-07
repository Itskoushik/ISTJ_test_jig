import time
from threading import Event, Lock
from core.dmm_discovery import discover_dmm

# ============================================================================
# MODULE STATE
# ============================================================================
_dmm = None
_rm = None   # kept for parity with prior module; not otherwise used

# Guards actual hardware I/O (write/query) against concurrent access.
_dmm_lock = Lock()

# Guards the recovery/reconnect *sequence* itself so only one popup/reconnect
# flow ever runs at a time, no matter how many callers hit a transport error
# around the same moment (mirrors the PSU _reconnect_lock pattern).
_dmm_reconnect_lock = Lock()

# Cleared while a recovery sequence is in progress; anything that needs the
# DMM can wait on this instead of starting its own recovery.
_dmm_ready_event = Event()
_dmm_ready_event.set()


class DMMOperationAborted(Exception):
    """Raised when the operator aborts the test while DMM recovery is pending."""
    pass


# ============================================================================
# TRANSPORT vs MEASUREMENT ERROR CLASSIFICATION
# ============================================================================
_TRANSPORT_ERROR_TOKENS = (
    "visaioerror", "resource not found", "timeout", "not connected",
    "unable to connect", "no listeners", "vi_error", "access denied",
    "object reference", "invalid session", "session not found",
    "resource busy", "i/o operation", "device not responding",
    "invalid handle", "connection lost", "connection refused",
    "connection reset", "connection error", "no connection",
    "usb error",
)

def _abort_aware_wait(event: Event, screen, poll_interval: float = 0.1, timeout: float = 600) -> bool:
    """
    Waits on `event` in short polling increments instead of one blocking
    call, so screen.abort_event is checked continuously and Abort is
    noticed within one poll_interval instead of only after the popup is
    dismissed (or never, until thread.terminate() is forced).
    Returns True if `event` was set, False on abort or timeout.
    """
    waited = 0.0
    while True:
        if event.wait(poll_interval):
            return True
        waited += poll_interval
        if screen.abort_event.is_set():
            return False
        if waited >= timeout:
            return False


def _get_claimed_visa_resources(screen):
    """
    Best-effort VISA resource strings already owned by PSU/oscilloscope,
    so DMM discovery skips them (mirrors the oscilloscope's own
    claimed-resource pre-filter). Never raises; returns {} if unknown.
    """
    claimed = set()
    try:
        psu_inst = getattr(screen, "psu_inst", None)
        res = getattr(psu_inst, "resource_name", None) if psu_inst else None
        if res:
            claimed.add(res)
    except Exception:
        pass
    try:
        osc_conn = getattr(screen, "osc_conn", None)
        osc_inst = getattr(osc_conn, "instrument", None) if osc_conn else None
        res = getattr(osc_inst, "resource_name", None) if osc_inst else None
        if res:
            claimed.add(res)
    except Exception:
        pass
    return claimed

def _is_transport_error(exc: Exception) -> bool:
    """
    True only for genuine DMM connectivity/transport failures (VISA I/O
    errors, lost USB, stale/invalid session, timeouts, etc). SCPI/command
    errors, malformed responses, and value-parsing problems are NOT
    transport errors and must not trigger the reconnect workflow.
    """
    return any(tok in str(exc).lower() for tok in _TRANSPORT_ERROR_TOKENS)


# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================
def _close_dmm_handle():
    global _dmm
    with _dmm_lock:
        if _dmm is not None:
            try:
                _dmm.close()
            except Exception:
                pass
            _dmm = None


def _recover_dmm(screen, context: str = "") -> bool:
    """
    Single entry point for DMM recovery. Thread-safe: only one recovery
    popup/reconnect sequence runs at a time. A concurrent caller that hits
    a failure while recovery is already underway waits abort-safely on
    _dmm_ready_event instead of showing a second popup.

    Returns True once _dmm is a valid, freshly-verified connection.
    Returns False if the operator aborted the test while waiting.
    """
    global _dmm

    acquired = _dmm_reconnect_lock.acquire(blocking=False)
    if not acquired:
        # Abort-aware: previously an uninterruptible wait(timeout=600).
        _abort_aware_wait(_dmm_ready_event, screen, timeout=600)
        return _dmm is not None and not screen.abort_event.is_set()

    try:
        _dmm_ready_event.clear()

        print("[DMM] Closing stale VISA handle.")
        _close_dmm_handle()

        if screen.abort_event.is_set():
            screen.log_signal.emit("[DMM] Recovery cancelled because test abort was requested.", True)
            return False

        screen.log_signal.emit(
            f"[DMM] Connection lost{f' during {context}' if context else ''}.", True
        )
        print("[DMM] Waiting for operator confirmation.")

        while True:
            if screen.abort_event.is_set():
                screen.log_signal.emit("[DMM] Recovery cancelled because test abort was requested.", True)
                return False

            ev = Event()
            screen._queue_popup(
                "⚠ DMM Disconnected",
                "The Digital Multimeter (DMM) is not connected or is not responding.\n\n"
                "Please check the following:\n"
                "  • DMM power switch is ON\n"
                "  • DMM USB cable is properly connected\n"
                "  • USB cable is firmly seated\n"
                "  • DMM is powered and ready for measurement\n\n"
                "Click OK after checking the above. The system will attempt "
                "to reconnect to the DMM automatically.",
                None, "ok", None,
                callback=lambda result, popup: ev.set()
            )

            # Abort-aware: this is the wait that previously left the test
            # thread stuck until thread.terminate() was forced.
            confirmed = _abort_aware_wait(ev, screen, timeout=600)

            if screen.abort_event.is_set():
                screen.log_signal.emit("[DMM] Recovery cancelled because test abort was requested.", True)
                return False

            if not confirmed:
                screen.log_signal.emit("[DMM] Recovery cancelled — no operator response.", True)
                return False

            print("[DMM] Operator confirmed DMM is ready.")
            print("[DMM] Starting fresh VISA discovery.")

            claimed = _get_claimed_visa_resources(screen)
            ok, msg, inst = discover_dmm(
                exclude_resources=claimed,
                log_fn=lambda m: print(m),
            )
            if ok:
                with _dmm_lock:
                    _dmm = inst
                print("[DMM] Fresh DMM connection verified.")
                print("[DMM] DMM successfully reconnected.")
                return True

            screen.log_signal.emit(f"[DMM] Reconnect failed: {msg}", True)
    finally:
        # Lock/event release happens FIRST and unconditionally, before any
        # logging that could itself throw — guarantees requirement that the
        # recovery lock is never left stuck.
        _dmm_ready_event.set()
        _dmm_reconnect_lock.release()
        try:
            print("[DMM] Recovery sequence ended.")
        except Exception:
            pass

import pyvisa as _pyvisa

_RIGOL_DMM_VID = "0x1AB1"   # Rigol vendor ID — matches the working candidate
                             # seen in the log: USB::0x1AB1::0x0C94::...::INSTR

_selftest_dmm_reconnect_lock = Lock()
_selftest_dmm_ready_event = Event()
_selftest_dmm_ready_event.set()


def _selftest_probe_existing_handle(screen) -> bool:
    """Lightweight liveness check on the existing _dmm handle — a single
    cheap query, no close/reopen. True only if it actually answers."""
    global _dmm
    if _dmm is None:
        return False
    try:
        with _dmm_lock:
            _dmm.write(":FUNCtion:VOLTage:DC")
            time.sleep(0.1)
            _dmm.query(":MEASure:VOLTage:DC?")
        print("[DMM][SELF-TEST] Existing DMM handle verified ✓")
        return True
    except Exception as e:
        # Not a failure yet — falling through to discovery is the normal
        # next step, so terminal only.
        print(f"[DMM][SELF-TEST] Existing handle unusable ({e}) — will search.")
        return False


def _selftest_discover_rigol_usb(screen) -> bool:
    """USB-only Rigol discovery. Never touches ASRL/serial resources and
    never probes non-Rigol USB VISA resources (PSU, oscilloscope, etc.)."""
    global _dmm
    try:
        rm = _pyvisa.ResourceManager()
        resources = rm.list_resources()
    except Exception as e:
        msg = f"[DMM][SELF-TEST] VISA resource list failed: {e}"
        screen.log_signal.emit(msg, True)
        return False

    candidates = [r for r in resources if r.startswith("USB") and _RIGOL_DMM_VID in r]
    if not candidates:
        msg = "[DMM][SELF-TEST] No Rigol USB candidates found."
        screen.log_signal.emit(msg, True)
        return False

    print(f"[DMM][SELF-TEST] Searching USB Rigol DMM resources only... {candidates}")

    for res in candidates:
        try:
            inst = rm.open_resource(res)
            idn = inst.query("*IDN?").strip()
            if "RIGOL" in idn.upper():
                with _dmm_lock:
                    _dmm = inst
                print(f"[DMM][SELF-TEST] Rigol DMM verified ✓ ({res})")
                return True
            inst.close()
        except Exception as e:
            # Individual candidate rejection is expected discovery noise,
            # not a failure — terminal only.
            print(f"[DMM][SELF-TEST] Candidate {res} rejected: {e}")

    # No candidate worked — this IS a failure, goes to GUI log.
    msg = "[DMM][SELF-TEST] No working Rigol DMM found among USB candidates."
    screen.log_signal.emit(msg, True)
    return False


def ensure_dmm_connected_for_self_test(screen) -> bool:
    """
    PSU/DMM self-test-only connection path.
      1. Reuse + verify an existing handle if one exists (no forced close).
      2. Only if that fails, run a USB-only Rigol discovery (no ASRL scan,
         no probing the PSU/scope VISA resources).
      3. Only show the operator popup if step 1 AND step 2 both fail.
    Does not touch the generic _recover_dmm / discover_dmm path at all.
    """
    if _selftest_probe_existing_handle(screen):
        return True

    print("[DMM][SELF-TEST] Existing DMM handle unavailable.")

    if _selftest_discover_rigol_usb(screen):
        print("[DMM][SELF-TEST] DMM ready for self-test ✓")
        return True

    # Both reuse and discovery failed — genuine failure, GUI log + popup.
    return _selftest_recover_dmm(screen)

def read_resistance_for_self_test(screen, label="Resistance", min_val=None, max_val=None):
    """Same logic/return shape as read_resistance(), routed through the
    self-test-only connect/recover path instead of the generic one."""
    try:
        raw = execute_dmm_operation_for_self_test(screen, _raw_resistance_query)
    except DMMOperationAborted:
        screen.log_signal.emit(f"❌ DMM unavailable — {label} not recorded", True)
        return {"value": 0, "observation": "NO DMM", "result": "FAIL"}
    except Exception as e:
        screen.log_signal.emit(f"DMM read error ({label}): {str(e)}", True)
        return {"value": 0, "observation": "READ ERROR", "result": "FAIL"}

    try:
        measured = float(raw)
        min_ohm = _to_ohms(min_val)
        max_ohm = _to_ohms(max_val)
        display_val = _format_resistance(measured)

        if min_ohm is None and max_ohm is None:
            screen.log_signal.emit(f"{label}: {display_val}", False)
            return {"value": measured, "observation": display_val, "result": "OK"}

        status = True
        if min_ohm is not None and measured < min_ohm:
            status = False
        if max_ohm is not None and measured > max_ohm:
            status = False

        range_txt = ""
        if min_ohm is not None and max_ohm is not None:
            range_txt = f"(Range {_format_resistance(min_ohm)} - {_format_resistance(max_ohm)})"
        elif min_ohm is not None:
            range_txt = f"(> {_format_resistance(min_ohm)})"
        elif max_ohm is not None:
            range_txt = f"(< {_format_resistance(max_ohm)})"

        result_text = "PASS" if status else "FAIL"
        if hasattr(screen, "register_test_result"):
            screen.register_test_result(result_text)

        screen.log_signal.emit(
            f"{label}: {display_val} {range_txt}  {result_text} {'✅' if status else '❌'}",
            not status
        )
        return {"value": measured, "observation": display_val, "result": result_text}

    except Exception as e:
        screen.log_signal.emit(f"DMM read error ({label}): {str(e)}", True)
        return {"value": 0, "observation": "READ ERROR", "result": "FAIL"}

def _selftest_recover_dmm(screen) -> bool:
    """Operator-gated recovery, USB-Rigol-only rediscovery. Structurally
    mirrors _recover_dmm but never calls discover_dmm() (which scans ASRL)."""
    acquired = _selftest_dmm_reconnect_lock.acquire(blocking=False)
    if not acquired:
        _abort_aware_wait(_selftest_dmm_ready_event, screen, timeout=600)
        return _dmm is not None and not screen.abort_event.is_set()

    try:
        _selftest_dmm_ready_event.clear()
        while True:
            if screen.abort_event.is_set():
                return False

            ev = Event()
            screen._queue_popup(
                "⚠ DMM Disconnected",
                "The Digital Multimeter (DMM) is not connected or is not responding.\n\n"
                "Please check the DMM power/USB connection, then click OK.",
                None, "ok", None,
                callback=lambda result, popup: ev.set()
            )
            confirmed = _abort_aware_wait(ev, screen, timeout=600)
            if screen.abort_event.is_set() or not confirmed:
                return False

            if _selftest_discover_rigol_usb(screen):
                return True
            screen.log_signal.emit("[DMM][SELF-TEST] Reconnect attempt failed — retrying.", True)
    finally:
        _selftest_dmm_ready_event.set()
        _selftest_dmm_reconnect_lock.release()


def execute_dmm_operation_for_self_test(screen, operation):
    if _dmm is None:
        if not ensure_dmm_connected_for_self_test(screen):
            raise DMMOperationAborted()
    try:
        return operation()
    except DMMOperationAborted:
        raise
    except Exception as exc:
        if not _is_transport_error(exc):
            raise
        if not ensure_dmm_connected_for_self_test(screen):
            raise DMMOperationAborted()
        print("[DMM][SELF-TEST] Retrying measurement...")
        return operation()


def read_voltage_for_self_test(screen, label="Voltage", min_val=None, max_val=None):
    """Same logic/return shape as read_voltage(), routed through the
    self-test-only connect/recover path instead of the generic one."""
    try:
        raw = execute_dmm_operation_for_self_test(screen, _raw_voltage_query)
    except DMMOperationAborted:
        screen.log_signal.emit(f"❌ DMM unavailable — {label} not recorded", True)
        return {"value": 0, "observation": "NO DMM", "result": "FAIL"}
    except Exception as e:
        screen.log_signal.emit(f"DMM read error ({label}): {str(e)}", True)
        return {"value": 0, "observation": "READ ERROR", "result": "FAIL"}

    # ── identical parsing/range-check logic to read_voltage() from here ──
    measured = float(raw)
    min_v = _to_volts(min_val)
    max_v = _to_volts(max_val)
    display_val = _format_voltage(measured)
    status = True
    if min_v is not None and measured < min_v:
        status = False
    if max_v is not None and measured > max_v:
        status = False

    range_txt = ""
    if min_v is not None and max_v is not None:
        range_txt = f"(Range {_format_voltage(min_v)} - {_format_voltage(max_v)})"
    elif min_v is not None:
        range_txt = f"(>{_format_voltage(min_v)})"
    elif max_v is not None:
        range_txt = f"(<{_format_voltage(max_v)})"

    result_text = "PASS" if status else "FAIL"
    if hasattr(screen, "register_test_result"):
        screen.register_test_result(result_text)
    screen.log_signal.emit(
        f"{label}: {display_val} {range_txt}  {result_text} {'✅' if status else '❌'}", not status
    )
    return {"value": measured, "observation": display_val, "result": result_text}
def execute_dmm_operation(screen, operation):
    """
    Universal wrapper for any DMM hardware operation.

    `operation` is a zero-arg callable that talks to the module-global
    `_dmm` handle and returns a raw value (e.g. a query response string).
    On a genuine transport failure, this function pauses, prompts the
    operator via the existing popup queue, performs a fresh reconnect, and
    retries the SAME operation exactly once. Non-transport errors (bad
    SCPI, malformed response, parsing problems) are re-raised untouched so
    callers keep their own measurement-validation behavior.
    """
    global _dmm

    if _dmm is None:
        if not _recover_dmm(screen, context="DMM not connected"):
            raise DMMOperationAborted()

    try:
        return operation()
    except DMMOperationAborted:
        raise
    except Exception as exc:
        if not _is_transport_error(exc):
            raise
        _close_dmm_handle()
        if not _recover_dmm(screen, context="measurement"):
            raise DMMOperationAborted()
        print("[DMM] Retrying measurement...")
        return operation()

def force_reset_dmm_state():
    """
    Call this after a worker QThread is forcibly killed via terminate()
    while it may have been holding _dmm_lock / _dmm_reconnect_lock /
    _selftest_dmm_reconnect_lock. terminate() kills the OS thread without
    running Python's finally/with cleanup, so a lock held at that instant
    stays acquired forever and deadlocks every future DMM read. Since a
    Lock that was never released can't be safely reused, swap in fresh
    Lock objects instead and re-arm the ready events.
    """
    global _dmm_lock, _dmm_reconnect_lock, _selftest_dmm_reconnect_lock
    _dmm_lock = Lock()
    _dmm_reconnect_lock = Lock()
    _selftest_dmm_reconnect_lock = Lock()
    _dmm_ready_event.set()
    _selftest_dmm_ready_event.set()
    print("[DMM] Lock state force-reset after worker termination.")
    
def release_dmm():
    """
    Explicitly close the DMM VISA session after each read sequence.
    This releases the USB interrupt endpoint so the STM32 COM port
    can respond again on a shared USB hub.
    """
    _close_dmm_handle()


def ensure_dmm_connected(screen):
    global _dmm
    claimed = _get_claimed_visa_resources(screen)
    ok, msg, inst = discover_dmm(
    exclude_resources=claimed,
    log_fn=lambda m: print(m),
)
    if ok:
        with _dmm_lock:
            _dmm = inst
        print(f"[DMM] Connected: {msg}")
        return True

    _dmm = None
    return _recover_dmm(screen, context="test start")


def reset_dmm():
    """Call this if you want to force a fresh DMM connection."""
    _close_dmm_handle()


# ===============================
# UNIT STRING → OHMS
# ===============================
def _to_ohms(value):
    """
    Converts:
    1M, 1.2K, 500, 2.2Mohm → ohms
    """

    if value is None:
        return None

    s = str(value).upper().replace("OHM", "").replace("Ω", "").strip()

    multiplier = 1

    if "G" in s:
        multiplier = 1e9
        s = s.replace("G", "")
    elif "M" in s:
        multiplier = 1e6
        s = s.replace("M", "")
    elif "K" in s:
        multiplier = 1e3
        s = s.replace("K", "")

    return float(s) * multiplier


# ===============================
# AUTO FORMAT LIKE REAL DMM
# ===============================
def _format_resistance(value_ohm):
    OVERLOAD_THRESHOLD = 1e10   # anything >= 10 GΩ = overload

    if value_ohm >= OVERLOAD_THRESHOLD:
        return f"> 10 GΩ (OL)"

    if value_ohm >= 1e6:
        return f"{value_ohm/1e6:.2f} MΩ"
    elif value_ohm >= 1e3:
        return f"{value_ohm/1e3:.2f} kΩ"
    else:
        return f"{value_ohm:.2f} Ω"


# ===============================
# LOW-LEVEL HARDWARE I/O (goes through execute_dmm_operation)
# ===============================
def _raw_resistance_query():
    with _dmm_lock:
        dmm = _dmm
        if dmm is None:
            raise ConnectionError("No DMM handle")
        dmm.write(":FUNCtion:RESistance")
        time.sleep(0.25)
        return dmm.query(":MEASure:RESistance?").strip()


def _raw_voltage_query():
    with _dmm_lock:
        dmm = _dmm
        if dmm is None:
            raise ConnectionError("No DMM handle")
        dmm.write(":FUNCtion:VOLTage:DC")
        time.sleep(0.25)
        return dmm.query(":MEASure:VOLTage:DC?").strip()


# ===============================
# MAIN FUNCTION
# ===============================
def read_resistance(screen, label="Resistance", min_val=None, max_val=None):
    """
    Smart resistance reader with range check + auto unit display

    Examples:
    read_resistance(screen,"R1")
    read_resistance(screen,"R1","1M")
    read_resistance(screen,"R1",None,"500")
    read_resistance(screen,"R1","1K","10K")
    """

    try:
        raw = execute_dmm_operation(screen, _raw_resistance_query)
    except DMMOperationAborted:
        screen.log_signal.emit(f"❌ DMM unavailable — {label} not recorded", True)
        return {
            "value": 0,
            "observation": "NO DMM",
            "result": "FAIL"
        }
    except Exception as e:
        screen.log_signal.emit(f"DMM read error ({label}): {str(e)}", True)
        return {
            "value": 0,
            "observation": "READ ERROR",
            "result": "FAIL"
        }

    try:
        measured = float(raw)

        # convert limits
        min_ohm = _to_ohms(min_val)
        max_ohm = _to_ohms(max_val)

        display_val = _format_resistance(measured)

        # ================= ONLY READING =================
        if min_ohm is None and max_ohm is None:
            screen.log_signal.emit(f"{label}: {display_val}", False)
            return {
                "value": measured,
                "observation": display_val,
                "result": "OK"
            }

        # ================= RANGE CHECK =================
        status = True

        if min_ohm is not None and measured < min_ohm:
            status = False

        if max_ohm is not None and measured > max_ohm:
            status = False

        # range text
        range_txt = ""
        if min_ohm is not None and max_ohm is not None:
            range_txt = f"(Range {_format_resistance(min_ohm)} - {_format_resistance(max_ohm)})"
        elif min_ohm is not None:
            range_txt = f"(> {_format_resistance(min_ohm)})"
        elif max_ohm is not None:
            range_txt = f"(< {_format_resistance(max_ohm)})"

        # ================= RESULT =================
        result_text = "PASS" if status else "FAIL"
        # 🔴 Update overall flag
        if hasattr(screen, "register_test_result"):
            screen.register_test_result(result_text)

        # emit log
        if status:
            screen.log_signal.emit(
                f"{label}: {display_val} {range_txt}  PASS ✅",
                False
            )
        else:
            screen.log_signal.emit(
                f"{label}: {display_val} {range_txt}  FAIL ❌",
                True
            )

        # return structured data
        return {
            "value": measured,
            "observation": display_val,
            "result": result_text
        }

    except Exception as e:
        # Parsing / formatting problem — NOT a connectivity issue, so this
        # does not touch the DMM handle or trigger reconnect.
        screen.log_signal.emit(f"DMM read error ({label}): {str(e)}", True)
        return {
            "value": 0,
            "observation": "READ ERROR",
            "result": "FAIL"
        }


# ===============================
# UNIT STRING → VOLTS
# ===============================
def _to_volts(value):
    """
    Converts:
    5, 5V, 500mV, 0.5V → volts
    """

    if value is None:
        return None

    s = str(value).upper().replace("V", "").strip()

    multiplier = 1

    if "MV" in str(value).upper():
        multiplier = 1e-3
        s = s.replace("MV", "")
    elif "KV" in str(value).upper():
        multiplier = 1e3
        s = s.replace("KV", "")

    return float(s) * multiplier


# ===============================
# AUTO FORMAT VOLTAGE LIKE DMM
# ===============================
def _format_voltage(v):
    if abs(v) >= 1:
        return f"{v:.2f} V"
    else:
        return f"{v*1000:.2f} mV"


# ===============================
# DC VOLTAGE READER
# ===============================
def read_voltage(screen, label="Voltage", min_val=None, max_val=None):
    """
    Smart DC voltage reader

    Examples:
    read_voltage(screen,"V1")
    read_voltage(screen,"V1","5")
    read_voltage(screen,"V1",None,"12V")
    read_voltage(screen,"V1","4.5","5.5")
    read_voltage(screen,"V1","500mV","1V")
    """

    try:
        raw = execute_dmm_operation(screen, _raw_voltage_query)
    except DMMOperationAborted:
        screen.log_signal.emit(f"❌ DMM unavailable — {label} not recorded", True)
        return {
            "value": 0,
            "observation": "NO DMM",
            "result": "FAIL"
        }
    except Exception as e:
        screen.log_signal.emit(f"DMM read error ({label}): {str(e)}", True)
        return {
            "value": 0,
            "observation": "READ ERROR",
            "result": "FAIL"
        }

    try:
        measured = float(raw)

        # convert limits
        min_v = _to_volts(min_val)
        max_v = _to_volts(max_val)

        display_val = _format_voltage(measured)

        # ===== ONLY READING =====
        if min_v is None and max_v is None:
            screen.log_signal.emit(f"{label}: {display_val}", False)

            return {
                "value": measured,
                "observation": display_val,
                "result": "PASS"
            }

        status = True

        if min_v is not None and measured < min_v:
            status = False

        if max_v is not None and measured > max_v:
            status = False

        # range text
        range_txt = ""
        if min_v is not None and max_v is not None:
            range_txt = f"(Range {_format_voltage(min_v)} - {_format_voltage(max_v)})"
        elif min_v is not None:
            range_txt = f"(>{_format_voltage(min_v)})"
        elif max_v is not None:
            range_txt = f"(<{_format_voltage(max_v)})"

        # result text
        result_text = "PASS" if status else "FAIL"
        # 🔴 Update overall flag
        if hasattr(screen, "register_test_result"):
            screen.register_test_result(result_text)

        # emit log
        if status:
            screen.log_signal.emit(
                f"{label}: {display_val} {range_txt}  PASS ✅",
                False
            )
        else:
            screen.log_signal.emit(
                f"{label}: {display_val} {range_txt}  FAIL ❌",
                True
            )

        # return structured data
        return {
            "value": measured,
            "observation": display_val,
            "result": result_text
        }

    except Exception as e:
        # Parsing / formatting problem — NOT a connectivity issue, so this
        # does not touch the DMM handle or trigger reconnect.
        screen.log_signal.emit(f"DMM read error ({label}): {str(e)}", True)
        return {
            "value": 0,
            "observation": "READ ERROR",
            "result": "FAIL"
        }