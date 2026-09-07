import time
from core.stm32_commands import STM32RelayController
import core.dmm_reader as _dmm_module
from core.excel_logger import write_self_test_excel
from core.paths import RESOURCES_DIR
from core.oscilloscope_helper import set_ch1_ch2_scale_10v

# ── PSU CH1 control (for CH1 relay/voltage test) ────────────────────────────
def _psu_ch1_apply(screen, voltage: float, current: float):
    """Set PSU CH1 to the given voltage/current and ensure output is ON."""
    try:
        screen.psu.psu_send_command("*CLS")
        screen.psu.psu_send_command("INST:NSEL 1")
        time.sleep(0.1)
        screen.psu.psu_send_command(f"SOUR1:VOLT {voltage}")
        time.sleep(0.05)
        screen.psu.psu_send_command(f"SOUR1:CURR {current}")
        time.sleep(0.05)
        screen.psu.psu_send_command("OUTP ON")
        time.sleep(0.5)
        screen.log_signal.emit(f"PSU CH1 set to {voltage}V / {current}A (PASS)", False)
    except Exception as e:
        screen.log_signal.emit(f"ERROR: PSU CH1 set to {voltage}V / {current}A failed: {e} (FAIL)", True)


def _psu_ch1_off(screen):
    """Turn off PSU CH1."""
    try:
        screen.psu.psu_send_command("INST:NSEL 1")
        time.sleep(0.1)
        screen.psu.psu_send_command("OUTP OFF")
        time.sleep(0.3)
        screen.log_signal.emit("PSU CH1 OFF (PASS)", False)
    except Exception as e:
        screen.log_signal.emit(f"ERROR: PSU CH1 OFF failed: {e} (FAIL)", True)


# ── CH1 relay + voltage test (S23/S21/J30 @ 7V/14V/28V) ─────────────────────
def _run_ch1_relay_voltage_test(screen):

    # ── Step 1: PSU CH1 ON at 7V / 1A ────────────────────────────────────
    _psu_ch1_apply(screen, 7.0, 1.0)
    time.sleep(1.0)

    # ── Turn on S23, S21, then J30 ────────────────────────────────────────
    s23_ok = STM32RelayController.send_with_retry(STM32RelayController.set_s23_remote)
    time.sleep(0.3)
    s21_ok = STM32RelayController.send_with_retry(STM32RelayController.set_s21_on)
    time.sleep(0.3)
    j30_ok = STM32RelayController.send_with_retry(STM32RelayController.set_j30_on)
    time.sleep(1.0)

    if s23_ok:
        screen.log_signal.emit("S23 successfully set to REMOTE", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S23 to REMOTE", True)

    if s21_ok:
        screen.log_signal.emit("S21 successfully set to UP position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S21 to UP position", True)

    if j30_ok:
        screen.log_signal.emit("J30 successfully connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connect J30", True)

    relays_ok = s23_ok and s21_ok and j30_ok

    write_self_test_excel("F29", "CONNECTED" if relays_ok else "FAILED")

    time.sleep(0.5)
    result = _dmm_module.read_voltage_for_self_test(screen, "DMM Voltage Check", "6.0V", "8.0V")
    if result:
        write_self_test_excel("H29", result["observation"])
        write_self_test_excel("I29", result["result"])
    time.sleep(1.0)

    # ── Step 2: PSU CH1 → 14V / 1A ────────────────────────────────────────
    _psu_ch1_apply(screen, 14.0, 1.0)
    time.sleep(1.0)
    result = _dmm_module.read_voltage_for_self_test(screen, "DMM Voltage Check", "13.0V", "15.0V")
    if result:
        write_self_test_excel("H32", result["observation"])
        write_self_test_excel("I32", result["result"])
    time.sleep(1.0)

    # ── Step 3: PSU CH1 → 28V / 1A ────────────────────────────────────────
    _psu_ch1_apply(screen, 28.0, 1.0)
    time.sleep(1.0)
    result = _dmm_module.read_voltage_for_self_test(screen, "DMM Voltage Check", "27.0V", "29.0V")
    if result:
        write_self_test_excel("H35", result["observation"])
        write_self_test_excel("I35", result["result"])
    time.sleep(1.0)

    # ── Turn OFF all relays, then PSU CH1 ─────────────────────────────────
    if STM32RelayController.send_with_retry(STM32RelayController.set_j30_off):
        screen.log_signal.emit("J30 successfully disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J30", True)
    time.sleep(0.3)

    if STM32RelayController.send_with_retry(STM32RelayController.set_s21_off):
        screen.log_signal.emit("S21 successfully set to DOWN position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S21 to DOWN position", True)
    time.sleep(0.3)

    if STM32RelayController.send_with_retry(STM32RelayController.set_s23_local):
        screen.log_signal.emit("S23 successfully set to LOCAL", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S23 to LOCAL", True)
    time.sleep(0.3)

    _psu_ch1_off(screen)









# ── Relay command registry ────────────────────────────────────────────────────
# Maps a logical name to the STM32RelayController callable.
# Only ON-commands live here; OFF-commands are not replayed on recovery.
_RELAY_CMD_MAP = {
    "set_s24_on": STM32RelayController.set_s24_on,
    "set_j67_on": STM32RelayController.set_j67_on,
    "set_j67_off": STM32RelayController.set_j67_off,
    "set_j68_on": STM32RelayController.set_j68_on,
    "set_j68_off": STM32RelayController.set_j68_off,
    "set_s24_off": STM32RelayController.set_s24_off,
}


def _relay_send(screen, cmd_name: str, relay_history: list, *, retry_on_fail: bool = True) -> bool:
    """
    Send a relay command, record it in history on success.
    On failure, if retry_on_fail=True: power-cycle CH3, replay history, retry once.

    Returns True if the command ultimately succeeded, False otherwise.
    """
    fn = _RELAY_CMD_MAP[cmd_name]
    ok = STM32RelayController.send_with_retry(fn)

    if ok:
        relay_history.append(cmd_name)
        return True

    if not retry_on_fail:
        return False

    # ── Recovery: CH3 power-cycle + STM32 sync ───────────────────────────────
    print(f"[RECOVERY] Relay '{cmd_name}' failed — power-cycling CH3 and replaying state...")

    _ch3_power_cycle(screen)
    _stm32_sync_wait(screen)

    # Replay all previously successful commands
    print(f"[RECOVERY] Replaying {len(relay_history)} prior relay command(s)...")
    for prev_cmd in relay_history:
        prev_fn = _RELAY_CMD_MAP[prev_cmd]
        rep_ok = STM32RelayController.send_with_retry(prev_fn)
        status = "✓" if rep_ok else "✗ (non-fatal)"
        print(f"[RECOVERY]   {prev_cmd} → {status}")
        time.sleep(0.3)

    time.sleep(0.5)

    # Retry the originally-failed command (no further recovery to avoid loops)
    print(f"[RECOVERY] Retrying '{cmd_name}'...")
    retry_ok = _relay_send(screen, cmd_name, relay_history, retry_on_fail=False)
    if retry_ok:
        print(f"[RECOVERY] '{cmd_name}' succeeded after recovery ✓")
    else:
        print(f"[RECOVERY] '{cmd_name}' still failed after recovery ✗")
    return retry_ok


def _ch3_power_cycle(screen):
    """Turn CH3 OFF then back ON at 5V/1A via the worker's psu handle."""
    print("[RECOVERY] CH3 → OFF (de-powering board)...")
    try:
        screen.psu.psu_send_command("INST:NSEL 3")
        time.sleep(0.1)
        screen.psu.psu_send_command("OUTP OFF")
        time.sleep(2.0)
        print("[RECOVERY] CH3 OFF ✓")
    except Exception as e:
        print(f"[RECOVERY] CH3 OFF failed (non-fatal): {e}")

    print("[RECOVERY] CH3 → ON (5V/1A, waiting for board boot)...")
    try:
        screen.psu.worker_ch3_5v()
        time.sleep(5.0)   # board boot + USB enumeration
        print("[RECOVERY] CH3 ON ✓")
    except Exception as e:
        print(f"[RECOVERY] CH3 ON failed (non-fatal): {e}")


def _stm32_sync_wait(screen):
    """Send STM32 sync and wait for confirmation."""
    print("[RECOVERY] Syncing STM32...")
    for attempt in range(3):
        try:
            ok = STM32RelayController.send_with_retry(STM32RelayController.sync)
            if ok:
                print("[RECOVERY] STM32 sync confirmed ✓")
                time.sleep(1.0)
                return
        except Exception as e:
            print(f"[RECOVERY] Sync attempt {attempt + 1} raised: {e}")
        time.sleep(2.0)
    print("[RECOVERY] STM32 sync not confirmed after 3 attempts — continuing")


# ── Main test ─────────────────────────────────────────────────────────────────

def run(screen):
    set_ch1_ch2_scale_10v(screen)
    screen.log_signal.emit("==========COMMENCING PSU (POWER SUPPLY UNIT) SELF TEST===========", False)

    screen.operator_signal.emit(
        "⚠ Operator Action Required",
        "• Please ensure that the ISTJ Self test board is properly connected.",
        str(RESOURCES_DIR / "self_test.jpeg")   # empty string "" if no image
    )
    screen._operator_event.wait()

    # ── CH1 relay + voltage test (S23/S21/J30 @ 7V/14V/28V) ─────────────
    _run_ch1_relay_voltage_test(screen)

    screen.log_signal.emit("==========SUCCESSFULLY COMPLETED PSU (POWER SUPPLY UNIT) SELF TEST===========", False)
