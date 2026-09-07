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
# Connector metadata: connector → (col_offset, cvr_on, cvr_off, cvr_label, tx_row, rx_row)
# ---------------------------------------------------------------------------
_CONNECTOR_META = {
    "J103": (0,  STM32RelayController.set_j18_on, STM32RelayController.set_j18_off, "J18",  0,   0),
    "J104": (1,  STM32RelayController.set_j19_on, STM32RelayController.set_j19_off, "J19",  12,  50),
    "J105": (2,  STM32RelayController.set_j20_on, STM32RelayController.set_j20_off, "J20",  24,  100),
    "J106": (3,  STM32RelayController.set_j21_on, STM32RelayController.set_j21_off, "J21",  36,  150),
    "J107": (4,  STM32RelayController.set_j22_on, STM32RelayController.set_j22_off, "J22",  48,  200),
}

_CONNECTOR_ORDER = ["J103", "J104", "J105", "J106", "J107"]


# ---------------------------------------------------------------------------
# Relay reset helper
# ---------------------------------------------------------------------------
def _relay_reset(screen):
    close_apx()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Switching all Relays to Default state", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
    time.sleep(1)


# ---------------------------------------------------------------------------
# User tests — NORM for one connector
# ---------------------------------------------------------------------------
def _run_user_norm(screen, connector):
    col_off, cvr_on, cvr_off, cvr_label, tx_row, rx_row = _CONNECTOR_META[connector]

    # Set column context
    reset_row_offset()
    reset_column_offset()
    if col_off:
        next_column(col_off)

    screen.check_abort()
    power_supply.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    screen.log_signal.emit("==========Commencing User Primary Intercom Channel test===========", False)
    user_primary_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    user_primary_ics_control.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    user_primary_ics_sonic.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    user_primary_tx_ptt.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Primary Intercom Channel test===========", False)

    screen.log_signal.emit("==========Commencing User Private Intercom Channel test===========", False)
    user_private_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Private Intercom Channel test===========", False)

    screen.log_signal.emit("==========Commencing User Override Intercom Channel test===========", False)
    user_override_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    # CVR
    screen.log_signal.emit(f"Connecting the audio analyser input to CVR Connector {cvr_label}", False)
    QApplication.processEvents()
    if STM32RelayController.send_with_retry(cvr_on):
        screen.log_signal.emit(f"{cvr_label} successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit(f"ERROR: Failed to Connect {cvr_label} to CVR Connector", True)
    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()

    user_override_cvr_output.run_norm(screen)

    screen.log_signal.emit(f"Disconnecting the audio analyser input to CVR Connector {cvr_label}", False)
    QApplication.processEvents()
    if STM32RelayController.send_with_retry(cvr_off):
        screen.log_signal.emit(f"{cvr_label} successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit(f"ERROR: Failed to Disconnect {cvr_label} from CVR Connector", True)
    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Override Intercom Channel test===========", False)

    # TX — own row offset
    screen.log_signal.emit("==========Commencing User Transmit Audio test===========", False)
    reset_row_offset()
    reset_column_offset()
    if tx_row:
        next_row(tx_row)
    user_transmit_tx_output.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Transmit Audio test===========", False)

    # RX — own row offset
    screen.log_signal.emit("==========Commencing User Receive Audio test===========", False)
    reset_row_offset()
    reset_column_offset()
    if rx_row:
        next_row(rx_row)
    user_recieve_rx_select.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Receive Audio test===========", False)


# ---------------------------------------------------------------------------
# User tests — STBY for one connector
# ---------------------------------------------------------------------------
def _run_user_stby(screen, connector):
    col_off, cvr_on, cvr_off, cvr_label, tx_row, rx_row = _CONNECTOR_META[connector]

    # Set column context
    reset_row_offset()
    reset_column_offset()
    if col_off:
        next_column(col_off)

    screen.check_abort()
    power_supply.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    screen.log_signal.emit("==========Commencing User Primary Intercom Channel test===========", False)
    user_primary_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    user_primary_ics_control.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    user_primary_ics_sonic.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    user_primary_tx_ptt.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Primary Intercom Channel test===========", False)

    screen.log_signal.emit("==========Commencing User Private Intercom Channel test===========", False)
    user_private_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Private Intercom Channel test===========", False)

    screen.log_signal.emit("==========Commencing User Override Intercom Channel test===========", False)
    user_override_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    # CVR
    screen.log_signal.emit(f"Connecting the audio analyser input to CVR Connector {cvr_label}", False)
    QApplication.processEvents()
    if STM32RelayController.send_with_retry(cvr_on):
        screen.log_signal.emit(f"{cvr_label} successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit(f"ERROR: Failed to Connect {cvr_label} to CVR Connector", True)
    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()

    user_override_cvr_output.run_stby(screen)

    screen.log_signal.emit(f"Disconnecting the audio analyser input to CVR Connector {cvr_label}", False)
    QApplication.processEvents()
    if STM32RelayController.send_with_retry(cvr_off):
        screen.log_signal.emit(f"{cvr_label} successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit(f"ERROR: Failed to Disconnect {cvr_label} from CVR Connector", True)
    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Override Intercom Channel test===========", False)

    # TX — own row offset
    screen.log_signal.emit("==========Commencing User Transmit Audio test===========", False)
    reset_row_offset()
    reset_column_offset()
    if tx_row:
        next_row(tx_row)
    user_transmit_tx_output.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Transmit Audio test===========", False)

    # RX — own row offset
    screen.log_signal.emit("==========Commencing User Receive Audio test===========", False)
    reset_row_offset()
    reset_column_offset()
    if rx_row:
        next_row(rx_row)
    user_recieve_rx_select.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed User Receive Audio test===========", False)


# ---------------------------------------------------------------------------
# Ground crew — NORM
# ---------------------------------------------------------------------------
def _run_ground_crew_norm(screen, row_offset=0):
    reset_row_offset()
    reset_column_offset()
    if row_offset:
        next_row(row_offset)
    screen.log_signal.emit("==========Commencing GROUND CREW PRIMARY INTERCOM CHANNEL test===========", False)
    ground_crew_ics_volume.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    ground_crew_ics_limiter.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed GROUND CREW PRIMARY INTERCOM CHANNEL test===========", False)

    screen.log_signal.emit("==========Commencing GROUND CREW PRIVATE INTERCOM CHANNEL test===========", False)
    ground_crew_private.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed GROUND CREW PRIVATE INTERCOM CHANNEL test===========", False)

    screen.log_signal.emit("==========Commencing GROUND CREW OVERRIDE INTERCOM CHANNEL test===========", False)
    ground_crew_override.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed GROUND CREW OVERRIDE INTERCOM CHANNEL test===========", False)

    screen.log_signal.emit("==========Commencing GROUND CREW CVR OUTPUT LEVEL test===========", False)
    ground_crew_cvr_output.run_norm(screen)
    time.sleep(1)
    screen.log_signal.emit("==========Successfully Completed GROUND CREW CVR OUTPUT LEVEL test===========", False)


# ---------------------------------------------------------------------------
# Ground crew — STBY
# ---------------------------------------------------------------------------
def _run_ground_crew_stby(screen, row_offset=0):
    reset_row_offset()
    reset_column_offset()
    if row_offset:
        next_row(row_offset)
    screen.log_signal.emit("==========Commencing GROUND CREW PRIMARY INTERCOM CHANNEL test===========", False)
    ground_crew_ics_volume.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    ground_crew_ics_limiter.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed GROUND CREW PRIMARY INTERCOM CHANNEL test===========", False)

    screen.log_signal.emit("==========Commencing GROUND CREW PRIVATE INTERCOM CHANNEL test===========", False)
    ground_crew_private.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed GROUND CREW PRIVATE INTERCOM CHANNEL test===========", False)

    screen.log_signal.emit("==========Commencing GROUND CREW OVERRIDE INTERCOM CHANNEL test===========", False)
    ground_crew_override.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("==========Successfully Completed GROUND CREW OVERRIDE INTERCOM CHANNEL test===========", False)

    screen.log_signal.emit("==========Commencing GROUND CREW CVR OUTPUT LEVEL test===========", False)
    ground_crew_cvr_output.run_stby(screen)
    time.sleep(1)
    screen.log_signal.emit("==========Successfully Completed GROUND CREW CVR OUTPUT LEVEL test===========", False)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run_norm(screen):
    """
    Full test sequence. For each connector in order:
      1. Connect popup
      2. box_init NORM
      3. User tests NORM
      4. Relay reset
      5. box_init STBY
      6. User tests STBY
      7. [J103 only] Ground crew NORM then STBY (cable stays on J103)
      8. Disconnect popup
      9. Relay reset
    """
    reset_column_offset()
    reset_row_offset()

    screen.log_signal.emit("========== STARTING FULL JUNCTION BOX TESTS ==========", False)

        # ══════════════════════════════════════════
    #  GROUND CREW FIRST — cable on _CONNECTOR_ORDER[0]
    # ══════════════════════════════════════════
    first_connector = _CONNECTOR_ORDER[0]

    _relay_reset(screen)
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Connect J63 Connector to {first_connector} Connector using test cable.\n",
        _connector_image(first_connector), "ok", None
    )
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()

    # ── SS OFF (R1) ──
    box_init.run_init_jbox(screen)
    time.sleep(1)
    screen.log_signal.emit("==========GROUND CREW TESTS — NORMAL MODE (SS OFF)==========", False)
    _run_ground_crew_norm(screen)
    screen.log_signal.emit("==========COMPLETED GROUND CREW TESTS IN NORMAL MODE (SS OFF)==========", False)

    _relay_reset(screen)
    box_init.run_init_jbox_stby(screen)
    time.sleep(1)
    screen.log_signal.emit("==========GROUND CREW TESTS — STANDBY MODE (SS OFF)==========", False)
    _run_ground_crew_stby(screen)
    screen.log_signal.emit("==========COMPLETED GROUND CREW TESTS IN STANDBY MODE (SS OFF)==========", False)

    # ── SS ON (R2) ──
    _relay_reset(screen)
    box_init.run_init_jbox(screen)
    if STM32RelayController.send_with_retry(STM32RelayController.set_s27_on):
        screen.log_signal.emit("STBY SWITCH S27 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect STBY SWITCH S27", True)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("==========GROUND CREW TESTS — NORMAL MODE (SS ON)==========", False)
    _run_ground_crew_norm(screen, row_offset=44)
    screen.log_signal.emit("==========COMPLETED GROUND CREW TESTS IN NORMAL MODE (SS ON)==========", False)

    _relay_reset(screen)
    box_init.run_init_jbox_stby(screen)
    if STM32RelayController.send_with_retry(STM32RelayController.set_s27_on):
        screen.log_signal.emit("STBY SWITCH S27 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect STBY SWITCH S27", True)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("==========GROUND CREW TESTS — STANDBY MODE (SS ON)==========", False)
    _run_ground_crew_stby(screen, row_offset=44)
    screen.log_signal.emit("==========COMPLETED GROUND CREW TESTS IN STANDBY MODE (SS ON)==========", False)

    _relay_reset(screen)
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Disconnect J63 Connector from {first_connector} Connector using test cable.\n",
        _connector_image(first_connector), "ok", None
    )
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()

    # ══════════════════════════════════════════
    #  CONNECTOR LOOP — NORM/STBY user tests only
    # ══════════════════════════════════════════
    for connector in _CONNECTOR_ORDER:
        screen.log_signal.emit(f"========== CONNECTOR {connector} ==========", False)

        _relay_reset(screen)
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
        time.sleep(1)

        screen.log_signal.emit(f"==========COMMENCING NORMAL MODE — {connector}==========", False)
        _run_user_norm(screen, connector)
        screen.log_signal.emit(f"==========COMPLETED NORMAL MODE — {connector}==========", False)

        _relay_reset(screen)

        box_init.run_init_jbox_stby(screen)
        time.sleep(1)

        screen.log_signal.emit(f"==========COMMENCING STANDBY MODE — {connector}==========", False)
        _run_user_stby(screen, connector)
        screen.log_signal.emit(f"==========COMPLETED STANDBY MODE — {connector}==========", False)

        _relay_reset(screen)
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

    screen.log_signal.emit("========== ALL FULL JUNCTION BOX TESTS COMPLETED ==========", False)

def run_stby(screen):
    """Deprecated — STBY is now handled inside run_norm()."""
    pass