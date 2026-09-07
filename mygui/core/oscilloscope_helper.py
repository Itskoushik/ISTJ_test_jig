import time
import logging
from typing import Optional
 
logger = logging.getLogger(__name__)
 
# ---------------------------------------------------------------------------
# Measurement slot assignment
#   MEAS1 → CH1  FREQuency
#   MEAS2 → CH1  RMS
#   MEAS3 → CH2  FREQuency
#   MEAS4 → CH2  RMS
#   MEAS5 → MATH FREQuency
#   MEAS6 → MATH RMS          ← returned value
# ---------------------------------------------------------------------------
 
_SETTLE_MS = 200   # ms to wait after display-on before measuring
 
 
from threading import Event, Lock
from devices.oscilloscope_connection import OscilloscopeConnection


# ============================================================================
# UNIVERSAL OSCILLOSCOPE RECOVERY LAYER
# ----------------------------------------------------------------------------
# Every Oscilloscope operation in this file (and any future one) must go
# through ensure_oscilloscope_connected() / osc_write_with_recovery() /
# osc_query_with_recovery(). There is exactly ONE recovery code path:
#
#   operation needs the scope
#         -> not connected / comms lost?
#               -> screen._queue_popup(...)   (existing popup infra)
#               -> operator clicks OK
#               -> OscilloscopeConnection().discover_and_connect()
#               -> success -> retry the exact operation that failed
#               -> failure -> show the popup again
#         -> screen.abort_event set at any point -> unwind, no restart
#
# This mirrors the PSU reconnect pattern already used in
# SingleTestScreen/FullTestScreen (_queue_popup + a dedicated Event +
# a lock so concurrent callers don't spawn duplicate popups).
# ============================================================================

# Exception-message fragments that indicate a CONNECTION problem, as opposed
# to a valid device returning a bad/unavailable measurement (e.g. the
# 9.9E+37 "no measurement" sentinel, which must NOT trigger a reconnect).
_OSC_CONNECTION_ERROR_TOKENS = (
    "visaioerror", "vi_error", "resource not found", "timeout",
    "not connected", "unable to connect", "no listeners",
    "invalid session", "invalidsession", "access denied",
    "object reference", "device not found", "io error",
    "handle is invalid", "resource busy", "resource in use",
)

# ── Tokens that just mean "this one call was slow" — a scope that's mid-
# measurement-setup or settling after AUTOSet can legitimately miss a
# timeout window without actually being disconnected. These get a couple
# of quick local retries before we ever treat them as a real drop. Every
# other token above is treated as fatal on first sight, same as before.
_OSC_SOFT_RETRY_TOKENS = ("timeout",)


def _is_osc_connection_error(exc: Exception) -> bool:
    """True only for genuine transport/communication failures."""
    return any(token in str(exc).lower() for token in _OSC_CONNECTION_ERROR_TOKENS)


def _is_osc_soft_retry_error(exc: Exception) -> bool:
    """True for errors worth a quick local retry before escalating."""
    return any(token in str(exc).lower() for token in _OSC_SOFT_RETRY_TOKENS)


def _get_active_non_osc_resources(screen) -> set:
    """
    Collect VISA resource strings currently owned by PSU/DMM so Oscilloscope
    recovery never opens or queries them, even during fallback discovery.
    Read-only — never closes/resets anything.
    """
    excluded = set()

    psu_inst = getattr(screen, "psu_inst", None)
    if psu_inst is not None:
        try:
            excluded.add(psu_inst.resource_name)
        except Exception:
            pass

    try:
        from core import dmm_reader
        dmm_inst = getattr(dmm_reader, "_dmm", None)
        if dmm_inst is not None:
            excluded.add(dmm_inst.resource_name)
    except Exception:
        pass

    return excluded


def _get_osc_state(screen) -> dict:
    """
    Lazily create the per-screen reconnect state (lock + ack event).
    Stored directly on the screen object so it survives across every
    Oscilloscope call for that test run, without touching SingleTestScreen/
    FullTestScreen's __init__.
    """
    state = getattr(screen, "_osc_recovery_state", None)
    if state is None:
        state = {"lock": Lock(), "ack_event": Event()}
        screen._osc_recovery_state = state
    return state


def _show_osc_reconnect_popup_and_wait(screen, state) -> bool:
    """
    Queue the reconnect popup on the existing popup queue and block the
    calling (worker) thread until the operator acknowledges it.
    Returns False the moment screen.abort_event gets set, so this never
    blocks a worker thread forever during an abort.
    """
    if screen.abort_event.is_set():
        return False

    state["ack_event"].clear()
    screen._queue_popup(
        "⚠ Oscilloscope Connection Required",
        "Oscilloscope connection was lost or the Oscilloscope could not be detected.\n\n"
        "Please check the following:\n\n"
        "• Make sure the Oscilloscope is powered ON.\n"
        "• Make sure the Oscilloscope is switched ON.\n"
        "• Check that the USB cable is properly connected.\n"
        "• Check that the USB cable is properly connected to the PC.\n"
        "• Make sure the Oscilloscope is ready for communication.\n\n"
        "After checking the connections, click OK to retry the connection.",
        None,
        "ok",
        None,
        callback=lambda result, popup: state["ack_event"].set(),
    )

    # Poll instead of an unbounded wait() so an abort during the wait
    # unblocks this thread immediately instead of hanging forever.
    while not state["ack_event"].wait(timeout=0.5):
        if screen.abort_event.is_set():
            return False
    return not screen.abort_event.is_set()


def ensure_oscilloscope_connected(screen) -> bool:
    """
    Universal connectivity guard. Returns True once screen.osc_conn is a
    live, *verified* oscilloscope connection (verification happens inside
    OscilloscopeConnection.discover_and_connect(), which already does
    *IDN? + communication validation — reused as-is, not duplicated here).

    Handles both cases identically:
      - scope was never connected / already disconnected
      - scope's Python object still exists but the VISA session is dead
        (an operation upstream is expected to have invalidated
        conn.instrument first — see osc_write_with_recovery/osc_query_with_recovery)
    """
    conn = getattr(screen, "osc_conn", None)
    if conn is not None and conn.is_connected():
        return True
    return _recover_oscilloscope_connection(screen)


def _attempt_reconnect_once(screen) -> bool:
    """
    Single reconnect attempt: known resource first, then isolated discovery.
    Returns True and updates screen.osc_conn on success. PSU/DMM resources
    are never touched. Console-only logging — no UI noise.
    """
    old_conn = getattr(screen, "osc_conn", None)
    excluded_resources = _get_active_non_osc_resources(screen)

    new_conn = OscilloscopeConnection()
    new_conn.claimed_visa_resources = excluded_resources

    reconnected = False

    if old_conn is not None and getattr(old_conn, "resource_string", None):
        prev_ident = old_conn.get_identification()
        print(f"[OSC] Reconnecting (known resource: {old_conn.resource_string})...")
        reconnected = new_conn.reconnect_specific(
            old_conn.resource_string,
            expected_manufacturer=getattr(prev_ident, "manufacturer", None),
            expected_model=getattr(prev_ident, "model", None),
            expected_serial=getattr(prev_ident, "serial_number", None),
        )

    if not reconnected:
        print("[OSC] Reconnecting (isolated discovery)...")
        reconnected = new_conn.discover_and_connect()

    if reconnected:
        screen.osc_conn = new_conn
        if old_conn is not None and old_conn is not new_conn:
            try:
                old_conn.close_instrument_only()
            except Exception:
                pass
        print("[OSC] Oscilloscope reconnected successfully.")
        return True

    return False


def _try_silent_reconnect(screen, attempts: int = 2, delay: float = 1.0) -> bool:
    """
    A few quiet attempts to recover before ever bothering the operator.
    Console-only — nothing reaches Running Logs or a popup here.
    """
    for i in range(1, attempts + 1):
        if screen.abort_event.is_set():
            return False
        print(f"[OSC] Silent reconnect attempt {i}/{attempts}...")
        if _attempt_reconnect_once(screen):
            print("[OSC] Recovered silently — no operator action needed.")
            return True
        time.sleep(delay)
    return False


def _recover_oscilloscope_connection(screen) -> bool:
    state = _get_osc_state(screen)

    # Only one reconnect cycle at a time. If another thread is already
    # mid-recovery, wait for it instead of showing a second identical popup.
    if not state["lock"].acquire(blocking=False):
        state["lock"].acquire()
        state["lock"].release()
        conn = getattr(screen, "osc_conn", None)
        return conn is not None and conn.is_connected()

    try:
        print("[OSC] Connection unavailable — attempting silent reconnect...")

        # ── Try quietly first. Most drops are transient comms glitches
        # where the scope is still physically present — recover without
        # ever showing the operator a popup. ──
        if _try_silent_reconnect(screen):
            return True

        # ── Silent attempts exhausted — now the operator needs to check ──
        while True:
            if screen.abort_event.is_set():
                return False
            if not _show_osc_reconnect_popup_and_wait(screen, state):
                return False

            print("[OSC] Operator confirmed — attempting reconnect...")

            if _attempt_reconnect_once(screen):
                screen.log_signal.emit("✓ Oscilloscope reconnected successfully.", False)
                return True

            print("[OSC] Reconnect failed. PSU/DMM sessions were not modified.")
            # loop back → popup shown again, no crash, no test restart
    finally:
        state["lock"].release()

_OSC_SOFT_RETRY_ATTEMPTS = 3
_OSC_SOFT_RETRY_DELAY_S = 0.3


def osc_write_with_recovery(screen, command: str) -> None:
    """
    Single choke point for every Oscilloscope *write*. Any future
    Oscilloscope feature should call this instead of touching
    screen.osc_conn.instrument directly.
    """
    soft_attempts = 0
    while True:
        if screen.abort_event.is_set():
            return
        if not ensure_oscilloscope_connected(screen):
            return  # operator aborted while the scope was unavailable

        conn = screen.osc_conn
        try:
            conn.instrument.write(command)
            return
        except Exception as exc:
            if not _is_osc_connection_error(exc):
                logger.exception(f"[OSC] Non-connection error writing '{command}'")
                raise

            # ── A slow/timeout response gets a few quick local retries
            # before we ever mark the session stale — most of these are
            # the scope being briefly busy, not an actual disconnect.
            if _is_osc_soft_retry_error(exc) and soft_attempts < _OSC_SOFT_RETRY_ATTEMPTS:
                soft_attempts += 1
                print(f"[OSC] Slow response writing '{command}' (attempt {soft_attempts}/{_OSC_SOFT_RETRY_ATTEMPTS}) — retrying locally: {exc}")
                time.sleep(_OSC_SOFT_RETRY_DELAY_S)
                continue

            screen.log_signal.emit(
                f"⚠ Oscilloscope communication lost while sending '{command}'.", True
            )
            try:
                conn.instrument = None  # mark the session stale
            except Exception:
                pass
            screen.log_signal.emit(f"↻ Retrying Oscilloscope operation: {command}", False)
            soft_attempts = 0
            # loop → ensure_oscilloscope_connected() detects the stale
            # session and runs the full popup/reconnect cycle again


def osc_query_with_recovery(screen, command: str) -> str:
    """Single choke point for every Oscilloscope *query*."""
    soft_attempts = 0
    while True:
        if screen.abort_event.is_set():
            return ""
        if not ensure_oscilloscope_connected(screen):
            return ""

        conn = screen.osc_conn
        try:
            return conn.instrument.query(command).strip()
        except Exception as exc:
            if not _is_osc_connection_error(exc):
                logger.exception(f"[OSC] Non-connection error querying '{command}'")
                raise

            # ── Same soft-retry window as the write path above ──
            if _is_osc_soft_retry_error(exc) and soft_attempts < _OSC_SOFT_RETRY_ATTEMPTS:
                soft_attempts += 1
                print(f"[OSC] Slow response querying '{command}' (attempt {soft_attempts}/{_OSC_SOFT_RETRY_ATTEMPTS}) — retrying locally: {exc}")
                time.sleep(_OSC_SOFT_RETRY_DELAY_S)
                continue

            print(f"[OSC] Communication lost while sending '{command}': {exc}")
            try:
                conn.instrument = None  # mark the session stale
            except Exception:
                pass
            print(f"[OSC] Retrying Oscilloscope operation: {command}")
            soft_attempts = 0


def setup_channels_math_and_measure(screen) -> Optional[float]:
    """
    Configure the TBS1000C oscilloscope for a CH1−CH2 residual measurement:
 
    1. Turn CH1 and CH2 display ON.
    2. Define MATH waveform as CH1−CH2, label it "RES", and turn it ON.
    3. Configure six on-screen measurements:
         MEAS1 → CH1   FREQuency
         MEAS2 → CH1   RMS
         MEAS3 → CH2   FREQuency
         MEAS4 → CH2   RMS
         MEAS5 → MATH  FREQuency
         MEAS6 → MATH  RMS
    4. Return the RMS value read from MEAS6 (MATH/RES channel) as a float,
       or None on any error.
 
    Args:
        screen: The test-screen object that owns ``osc_conn``
                (an OscilloscopeConnection instance) and ``log_signal``.
 
    Returns:
        float | None  — RMS voltage of the MATH (RES) waveform, or None.
    """
    if not ensure_oscilloscope_connected(screen):
        # Operator aborted the test while the Oscilloscope was unavailable.
        return None

    def w(cmd: str) -> None:
        """Write a SCPI command — transparently recovers from disconnects."""
        logger.debug(f"[OSC] write: {cmd}")
        osc_write_with_recovery(screen, cmd)
 
    def q(cmd: str) -> str:
        """Query a SCPI command — transparently recovers from disconnects."""
        resp = osc_query_with_recovery(screen, cmd)
        logger.debug(f"[OSC] query: {cmd}  →  {resp}")
        return resp
 
    try:
        # ------------------------------------------------------------------
        # Step 1 — Enable CH1 and CH2 display
        # ------------------------------------------------------------------
        print("OSC: Enabling CH1 and CH2")
        w("SELect:CH1 ON")
        w("SELect:CH2 ON")
        time.sleep(_SETTLE_MS / 1000)
 
        # ------------------------------------------------------------------
        # Step 2 — Configure MATH: CH1−CH2, label "RES", display ON
        # ------------------------------------------------------------------
        print("OSC: Configuring MATH = CH1−CH2, label \"RES\" …")
        w('MATH:DEFINE "CH1-CH2"')   # operator is baked into the expression
        w('MATH:LABel "RES"')
        w("SELect:MATH ON")
        time.sleep(_SETTLE_MS / 1000)
 
        # ------------------------------------------------------------------
        # Step 3 — Configure six on-screen measurements
        # ------------------------------------------------------------------
        print("OSC: Configuring measurements (MEAS1–MEAS6) …")

        meas_cfg = [
            # (slot, source,  type)
            (1, "CH1",  "FREQuency"),
            (2, "CH1",  "RMS"),
            (3, "CH2",  "FREQuency"),
            (4, "CH2",  "RMS"),
            (5, "MATH", "FREQuency"),
            (6, "MATH", "RMS"),
        ]
 
        for slot, source, mtype in meas_cfg:
            w(f"MEASUrement:MEAS{slot}:SOUrce1 {source}")
            w(f"MEASUrement:MEAS{slot}:TYPe {mtype}")
            w(f"MEASUrement:MEAS{slot}:STATE ON")
            logger.info(f"[OSC] MEAS{slot}: {source} {mtype} → ON")
 
        # Allow the scope one acquisition cycle to populate measurement values
        time.sleep(0.5)
 
        # ------------------------------------------------------------------
        # Step 4 — Read RMS from MEAS6 (MATH/RES channel)
        # ------------------------------------------------------------------
        print("OSC: Reading RMS from MATH (RES) channel …")
        raw = q("MEASUrement:MEAS6:VALue?")
 
        try:
            rms_value = float(raw)
        except ValueError:
            print(
                f"⚠ OSC: Could not parse MEAS6 value: {raw!r}"
            )
            return None
 
        # 9.9E+37 is the scope's sentinel for "measurement not available"
        if rms_value > 9.0e37:
            print(
                "⚠ OSC: MEAS6 RMS returned overflow sentinel — "
                "check signal / trigger"
            )
            return None
 
        print(
            f"OSC: MATH (RES) RMS = {rms_value:.6f} V"
        )
        return rms_value
 
    except Exception as exc:
        if screen.abort_event.is_set():
            return None
        print(f"⚠ OSC: setup_channels_math_and_measure error: {exc}")
        logger.exception("[OSC] setup_channels_math_and_measure failed")
        return None
    
    
def read_osc_meter(screen, min_v: float, max_v: float) -> dict | None:
    """
    Reads RMS from MATH (RES) channel and checks if it's within [min_v, max_v].

    Returns:
        dict with keys:
            "observation" → formatted string e.g. "0.748000 V"
            "result"      → "PASS" or "FAIL"
        or None if measurement could not be taken.
    """
    rms = setup_channels_math_and_measure(screen)

    if rms is None:
        screen.log_signal.emit("⚠ OSC: Could not read RMS — returning None", True)
        return None

    observation = f"{rms:.2f} V"
    result = "PASS" if min_v <= rms <= max_v else "FAIL"

    screen.log_signal.emit(
    f"OSC Reading: {observation} | Range: {min_v} V - {max_v} V | {result}", False
    )
    return {"observation": observation, "result": result}    

def autoset_oscilloscope(screen):
    if not ensure_oscilloscope_connected(screen):
        return  # operator aborted while the scope was unavailable

    try:
        idn = osc_query_with_recovery(screen, "*IDN?")
        if idn:
            print(f"OSC: Detected — {idn}")
            print(f"Oscilloscope detected: {idn} — sending AUTOSET")

        osc_write_with_recovery(screen, "AUTOSet EXECute")
        time.sleep(3.0)   # AUTOSET takes a few seconds on TBS1000C

        print("Oscilloscope AUTOSET complete")

    except Exception as exc:
        if screen.abort_event.is_set():
            return
        screen.log_signal.emit(f"⚠ Oscilloscope autoset error: {exc}", True)
        logger.exception("[OSC] autoset_oscilloscope failed")
        
def set_ch1_ch2_scale_10v(screen) -> bool:
    """
    Turn CH1 and CH2 on and set both vertical scales to 10.00 V/div.

    Args:
        screen: The test-screen object that owns ``osc_conn``
                (an OscilloscopeConnection instance) and ``abort_event``.

    Returns:
        bool — True if the commands were sent successfully, False if the
        operator aborted while the Oscilloscope was unavailable.
    """
    if not ensure_oscilloscope_connected(screen):
        # Operator aborted the test while the Oscilloscope was unavailable.
        return False

    def w(cmd: str) -> None:
        """Write a SCPI command — transparently recovers from disconnects."""
        logger.debug(f"[OSC] write: {cmd}")
        osc_write_with_recovery(screen, cmd)

    try:
        print("OSC: Enabling CH1 and CH2, setting scale to 10.00 V/div each")

        w("SELect:CH1 ON")
        w("CH1:SCAle 10.0")

        w("SELect:CH2 ON")
        w("CH2:SCAle 10.0")

        time.sleep(_SETTLE_MS / 1000)

        print("OSC: CH1 and CH2 scale set to 10.00 V/div")
        return True

    except Exception as exc:
        if screen.abort_event.is_set():
            return False
        print(f"⚠ OSC: set_ch1_ch2_scale_10v error: {exc}")
        logger.exception("[OSC] set_ch1_ch2_scale_10v failed")
        return False