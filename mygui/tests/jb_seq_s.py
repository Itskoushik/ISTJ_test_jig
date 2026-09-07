from tests import (
    power_supply,
    user_override_cvr_output,
    user_override_ics_vol,
    user_primary_ics_sonic,
    user_primary_ics_vol,
    user_primary_ics_control,
    user_primary_tx_ptt,
    user_private_ics_vol,
    user_transmit_tx_output,
    user_recieve_rx_select,
    ground_crew_ics_volume,
    ground_crew_ics_limiter,
    ground_crew_private,
    ground_crew_override,
    ground_crew_cvr_output,
    box_init
)

import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from core.paths import RESOURCES_DIR
from devices.apx_analyzer import close_apx
from core.excel_logger import reset_column_offset, next_column, reset_row_offset, next_row
_CONNECTOR_IMAGES = {
    "J103": RESOURCES_DIR / "j103.jpeg",
    "J104": RESOURCES_DIR / "j104.jpeg",
    "J105": RESOURCES_DIR / "j105.jpeg",
    "J106": RESOURCES_DIR / "j106.jpeg",
    "J107": RESOURCES_DIR / "j107.jpeg",
}

def _connector_image(connector):
    """Return path to the connector's reference image (e.g. j103.jpeg)."""
    return _CONNECTOR_IMAGES.get(connector)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def should_run(screen, parent, sub=None):
    for t in screen.selected_tests:
        if "::" in t:
            p, s = t.split("::")
        else:
            p = t
            s = None
        if p.strip() == parent and (sub is None or s == sub):
            return True
    return False
_GROUND_CREW_PARENTS = {
    "GROUND CREW PRIMARY INTERCOM CHANNEL TEST",
    "GROUND CREW PRIVATE INTERCOM CHANNEL TEST",
    "GROUND CREW OVERRIDE INTERCOM CHANNEL TEST",
    "GROUND CREW CVR OUTPUT LEVEL TEST",
}

def _has_user_tests(screen):
    return any(
        (t.split("::")[0].strip() if "::" in t else t.strip()) not in _GROUND_CREW_PARENTS
        for t in screen.selected_tests
    )

def _has_ground_crew_tests(screen):
    return any(
        (t.split("::")[0].strip() if "::" in t else t.strip()) in _GROUND_CREW_PARENTS
        for t in screen.selected_tests
    )

# ---------------------------------------------------------------------------
# Per-connector metadata
# ---------------------------------------------------------------------------

# Maps connector name → (column_offset, cvr_on_fn, cvr_off_fn, cvr_label,
#                         tx_row_offset, rx_row_offset)
# column_offset of 0 means J103 baseline — no next_column() call needed.
# tx_row_offset / rx_row_offset of 0 means baseline — no next_row() call needed.
_CONNECTOR_META = {
    "J103": (0,  STM32RelayController.set_j18_on, STM32RelayController.set_j18_off, "J18",  0,   0),
    "J104": (1,  STM32RelayController.set_j19_on, STM32RelayController.set_j19_off, "J19",  12,  50),
    "J105": (2,  STM32RelayController.set_j20_on, STM32RelayController.set_j20_off, "J20",  24,  100),
    "J106": (3,  STM32RelayController.set_j21_on, STM32RelayController.set_j21_off, "J21",  36,  150),
    "J107": (4,  STM32RelayController.set_j22_on, STM32RelayController.set_j22_off, "J22",  48,  200),
}

_CONNECTOR_ORDER = ["J103", "J104", "J105", "J106", "J107"]


# ---------------------------------------------------------------------------
# Internal: set column context for a connector (used before every test block)
# ---------------------------------------------------------------------------

def _set_col(col_off):
    """Reset offsets and apply column for this connector."""
    reset_row_offset()
    reset_column_offset()
    if col_off:
        next_column(col_off)


# ---------------------------------------------------------------------------
# Single-connector NORM run
# Precondition: column context already set by caller.
# ---------------------------------------------------------------------------

def _run_norm_for_connector(screen, connector):
    col_off, cvr_on, cvr_off, cvr_label, tx_row, rx_row = _CONNECTOR_META[connector]

    screen.check_abort()

    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    # NOTE: old J103 NORM had an extra time.sleep(1) here before private ICS —
    # preserved via the sleep at the end of TX PTT block above.
    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    # ── CVR ──
    screen.log_signal.emit(
        f"Connecting the audio analyser input to CVR Connector {cvr_label}", False)
    QApplication.processEvents()
    if STM32RelayController.send_with_retry(cvr_on):
        screen.log_signal.emit(
            f"{cvr_label} successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit(
            f"ERROR: Failed to Connect {cvr_label} to CVR Connector", True)
    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_norm(screen)

    screen.log_signal.emit(
        f"Disconnecting the audio analyser input to CVR Connector {cvr_label}", False)
    QApplication.processEvents()
    if STM32RelayController.send_with_retry(cvr_off):
        screen.log_signal.emit(
            f"{cvr_label} successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit(
            f"ERROR: Failed to Disconnect {cvr_label} from CVR Connector", True)
    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()

    # ── TX ──
    reset_row_offset()
    reset_column_offset()
    if tx_row:
        next_row(tx_row)
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    # ── RX ──
    reset_row_offset()
    reset_column_offset()
    if rx_row:
        next_row(rx_row)
    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    # Restore column context for caller
    _set_col(col_off)


# ---------------------------------------------------------------------------
# Single-connector STBY run
# Precondition: column context already set by caller.
# ---------------------------------------------------------------------------

def _run_stby_for_connector(screen, connector):
    col_off, cvr_on, cvr_off, cvr_label, tx_row, rx_row = _CONNECTOR_META[connector]

    screen.check_abort()

    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    # ── CVR ──
    screen.log_signal.emit(
        f"Connecting the audio analyser input to CVR Connector {cvr_label}", False)
    QApplication.processEvents()
    if STM32RelayController.send_with_retry(cvr_on):
        screen.log_signal.emit(
            f"{cvr_label} successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit(
            f"ERROR: Failed to Connect {cvr_label} to CVR Connector", True)
    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_stby(screen)

    screen.log_signal.emit(
        f"Disconnecting the audio analyser input to CVR Connector {cvr_label}", False)
    QApplication.processEvents()
    if STM32RelayController.send_with_retry(cvr_off):
        screen.log_signal.emit(
            f"{cvr_label} successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit(
            f"ERROR: Failed to Disconnect {cvr_label} from CVR Connector", True)
    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()

    # ── TX ──
    reset_row_offset()
    reset_column_offset()
    if tx_row:
        next_row(tx_row)
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    # ── RX ──
    reset_row_offset()
    reset_column_offset()
    if rx_row:
        next_row(rx_row)
    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    # Restore column context for caller
    _set_col(col_off)


# ---------------------------------------------------------------------------
# Ground-crew tests  (norm then stby, one popup each)
# ---------------------------------------------------------------------------

def _run_ground_crew(screen, mode: str, row_offset=0):
    """Run ground-crew tests for the given mode ('norm' or 'stby').
    Caller is responsible for the 'connect to any connector' popup ONCE
    before calling norm, and again before stby if needed."""
    reset_row_offset()
    reset_column_offset()
    if row_offset:
        next_row(row_offset)

    if mode == "norm":
        if should_run(screen, "GROUND CREW PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
            ground_crew_ics_volume.run_norm(screen)
        time.sleep(1)
        screen.check_abort()
        if should_run(screen, "GROUND CREW PRIMARY INTERCOM CHANNEL TEST", "ICS LIMITER TEST"):
            ground_crew_ics_limiter.run_norm(screen)
        time.sleep(1)
        screen.check_abort()
        if should_run(screen, "GROUND CREW PRIVATE INTERCOM CHANNEL TEST", None):
            ground_crew_private.run_norm(screen)
        time.sleep(1)
        screen.check_abort()
        if should_run(screen, "GROUND CREW OVERRIDE INTERCOM CHANNEL TEST", None):
            ground_crew_override.run_norm(screen)
        time.sleep(1)
        screen.check_abort()
        if should_run(screen, "GROUND CREW CVR OUTPUT LEVEL TEST", None):
            ground_crew_cvr_output.run_norm(screen)
        time.sleep(1)
    else:
        if should_run(screen, "GROUND CREW PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
            ground_crew_ics_volume.run_stby(screen)
        time.sleep(1)
        screen.check_abort()
        if should_run(screen, "GROUND CREW PRIMARY INTERCOM CHANNEL TEST", "ICS LIMITER TEST"):
            ground_crew_ics_limiter.run_stby(screen)
        time.sleep(1)
        screen.check_abort()
        if should_run(screen, "GROUND CREW PRIVATE INTERCOM CHANNEL TEST", None):
            ground_crew_private.run_stby(screen)
        time.sleep(1)
        screen.check_abort()
        if should_run(screen, "GROUND CREW OVERRIDE INTERCOM CHANNEL TEST", None):
            ground_crew_override.run_stby(screen)
        time.sleep(1)
        screen.check_abort()
        if should_run(screen, "GROUND CREW CVR OUTPUT LEVEL TEST", None):
            ground_crew_cvr_output.run_stby(screen)
        time.sleep(1)


# ---------------------------------------------------------------------------
# Per-connector NORM + STBY cycle
# ---------------------------------------------------------------------------
def _run_ground_crew_only(screen, connector):
    """Called when ONLY ground-crew tests are selected. Runs on one connector."""

    # ══════════════════════════════════════════
    #  SS OFF — S27 OFF
    # ══════════════════════════════════════════

    # ── GROUND CREW NORM (R1) ──
    close_apx()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Switching all Relays to Default state", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
    time.sleep(1)
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Connect J63 Connector to {connector} Connector using test cable.\n",
        _connector_image(connector), "ok", None
    )
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()

    box_init.run_init_jbox(screen)
    screen.log_signal.emit("==========GROUND CREW TESTS — NORMAL MODE (SS OFF)==========", False)
    _run_ground_crew(screen, "norm")
    screen.log_signal.emit("==========COMPLETED GROUND CREW TESTS IN NORMAL MODE (SS OFF)==========", False)

    # ── GROUND CREW STBY (R1) ──
    close_apx()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Switching all Relays to Default state", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
    time.sleep(1)


    box_init.run_init_jbox_stby(screen)
    screen.log_signal.emit("==========GROUND CREW TESTS — STANDBY MODE (SS OFF)==========", False)

    # ══════════════════════════════════════════
    #  SS ON — S27 ON, row offset +44
    # ══════════════════════════════════════════

    # ── GROUND CREW NORM (R2) ──
    close_apx()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Switching all Relays to Default state", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
    time.sleep(1)

    box_init.run_init_jbox(screen)
    if STM32RelayController.send_with_retry(STM32RelayController.set_s27_on):
        screen.log_signal.emit("STBY SWITCH S27 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect STBY SWITCH S27", True)
    QApplication.processEvents()
    time.sleep(0.5)

    screen.log_signal.emit("==========GROUND CREW TESTS — NORMAL MODE (SS ON)==========", False)
    _run_ground_crew(screen, "norm", row_offset=44)
    screen.log_signal.emit("==========COMPLETED GROUND CREW TESTS IN NORMAL MODE (SS ON)==========", False)

    # ── GROUND CREW STBY (R2) ──
    close_apx()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Switching all Relays to Default state", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
    time.sleep(1)

    box_init.run_init_jbox_stby(screen)
    if STM32RelayController.send_with_retry(STM32RelayController.set_s27_on):
        screen.log_signal.emit("STBY SWITCH S27 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect STBY SWITCH S27", True)
    QApplication.processEvents()
    time.sleep(0.5)

    screen.log_signal.emit("==========GROUND CREW TESTS — STANDBY MODE (SS ON)==========", False)
    _run_ground_crew(screen, "stby", row_offset=44)
    screen.log_signal.emit("==========COMPLETED GROUND CREW TESTS IN STANDBY MODE (SS ON)==========", False)

    # Final relay reset
    close_apx()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Switching all Relays to Default state", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
    time.sleep(1)

    # Disconnect popup — only at the very end after R2 STBY
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Disconnect J63 Connector from {connector} Connector using test cable.\n",
        _connector_image(connector), "ok", None
    )
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
def _run_connector_pair(screen, connector, is_first_connector):
    """
    Full NORM → STBY cycle for one connector.

    Uniform behaviour for ALL connectors in BOTH modes:
      • NORM: relay-reset + box_init.run_init_jbox before tests
      • STBY: relay-reset + box_init.run_init_jbox_stby before tests

    Ground-crew tests run immediately after the STBY of the FIRST selected
    connector (new requested behaviour).  The "connect to any connector" popup
    replaces what was previously a disconnect popup for that connector,
    matching the old code where J107 had no disconnect popup before ground crew.
    """
    col_off = _CONNECTOR_META[connector][0]

    # ════════════════════════════════════════════
    #  N O R M   entry
    # ════════════════════════════════════════════

    # Relay reset before NORM: only needed for the very first connector
    if is_first_connector:
        close_apx()
        time.sleep(0.5)
        screen.check_abort()
        screen.log_signal.emit("Switching all Relays to Default state", False)
        if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
            screen.log_signal.emit("All relays successfully set to default states", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
        time.sleep(1)

    # Connect cable for NORM
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Connect J63 Connector to {connector} Connector using test cable.\n",
        _connector_image(connector), "ok", None
    )
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()

    # Box init for NORM: ALL connectors (same as STBY)
    box_init.run_init_jbox(screen)

    # Run NORM tests
    screen.log_signal.emit(f"==========COMMENCING NORMAL MODE — {connector}==========", False)
    _set_col(col_off)
    _run_norm_for_connector(screen, connector)
    screen.log_signal.emit(f"==========COMPLETED NORMAL MODE — {connector}==========", False)
    # ════════════════════════════════════════════
    #  S T B Y   entry
    #  Cable stays connected — same port as NORM.
    #  Just reset relays and re-init for STBY mode.
    # ════════════════════════════════════════════
    
    close_apx()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit(f"==========COMMENCING STANDBY MODE — {connector}==========", False)
    # Relay reset before STBY
    screen.log_signal.emit("Switching all Relays to Default state", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
    time.sleep(1)

    # Box init for STBY: ALL connectors
    box_init.run_init_jbox_stby(screen)
    time.sleep(1)

    _set_col(col_off)
    _run_stby_for_connector(screen, connector)
    screen.log_signal.emit(f"==========COMPLETED STANDBY MODE — {connector}==========", False)
    # ════════════════════════════════════════════
    #  Post-STBY: ground crew OR disconnect
    # ════════════════════════════════════════════

    # Post-STBY: always disconnect — ground crew now runs once, up front,
    # before the connector loop (see run()).
    close_apx()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Switching all Relays to Default state", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
    time.sleep(1)
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Disconnect J63 Connector from {connector} Connector using test cable.\n",
        _connector_image(connector), "ok", None
    )
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(screen):
    """
    Single entry point. For every selected connector (J103 → J107 order):
      1. NORM tests
      2. STBY tests
      3. Ground-crew NORM + STBY  ← only after the VERY FIRST selected connector

    Column/row offsets are identical to the original code.
    """
    reset_column_offset()
    reset_row_offset()

    screen.log_signal.emit("========== STARTING JUNCTION BOX TESTS ==========", False)

    selected = [c for c in _CONNECTOR_ORDER if c in screen.selected_connectors]

    if not selected:
        screen.log_signal.emit("No connectors selected — nothing to test.", True)
        return

    # Case A: ground-crew tests only → run once on the first selected connector
    if not _has_user_tests(screen):
        connector = selected[0]
        screen.log_signal.emit(f"========== GROUND CREW ONLY — CONNECTOR {connector} ==========", False)
        _run_ground_crew_only(screen, connector)
        screen.log_signal.emit("========== ALL JUNCTION BOX TESTS COMPLETED ==========", False)
        return

    # Case B: ground crew FIRST (on the first selected connector's cable),
    # then the full NORM/STBY connector loop.
    if _has_ground_crew_tests(screen):
        screen.log_signal.emit(f"========== GROUND CREW — CONNECTOR {selected[0]} ==========", False)
        _run_ground_crew_only(screen, selected[0])

    for idx, connector in enumerate(selected):
        is_first = (idx == 0)
        screen.log_signal.emit(f"========== CONNECTOR {connector} ==========", False)
        _run_connector_pair(screen, connector, is_first_connector=is_first)

    screen.log_signal.emit("========== ALL JUNCTION BOX TESTS COMPLETED ==========", False)


# ---------------------------------------------------------------------------
# Legacy shims
# ---------------------------------------------------------------------------

def run_norm(screen):
    """Deprecated — delegates to run()."""
    run(screen)


def run_stby(screen):
    """Deprecated — STBY is now handled inside run()."""
    pass