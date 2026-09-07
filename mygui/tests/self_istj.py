import time

from core.paths import RESOURCES_DIR
from core.excel_logger import write_self_test_excel
from core.stm32_commands import STM32RelayController
from core.tuning_workflow import set_popup_title
import core.dmm_reader as _dmm_module
from devices.power_supply import check_current_ch3
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
# ── Relay command registry ──────────────────────────────────────────────────
# Main relays: S21, S22, S23, S26
# Sub relays:  J30 .. J54
# TODO: verify these attribute names against STM32RelayController — naming
# follows the same convention as set_s24_on/off used in self_dmm.py.
_MAIN_RELAYS = ["s21", "s22", "s26"]
_SUB_RELAYS = [f"j{n}" for n in range(30, 55)]  # j30..j54

_RELAY_CMD_MAP = {}
for _name in _MAIN_RELAYS + _SUB_RELAYS:
    _RELAY_CMD_MAP[f"set_{_name}_on"] = getattr(STM32RelayController, f"set_{_name}_on", None)
    _RELAY_CMD_MAP[f"set_{_name}_off"] = getattr(STM32RelayController, f"set_{_name}_off", None)


# ── Per-relay resistance limits (ohms) ───────────────────────────────────────
RESISTANCE_LIMITS = {
    "j30": ("882", "12000"),
    "j54": ("882", "12000"),
    "j53": ("882", "12000"),
    "j52": ("882", "12000"),
    "j51": ("882", "12000"),
    "j36": ("882", "12000"),
    "j31": ("882", "12000"),
    "j32": ("882", "12000"),
    "j33": ("882", "12000"),
    "j34": ("882", "12000"),
    "j35": ("882", "12000"),
    "j37": ("882", "12000"),
    "j38": ("882", "12000"),
    "j50": ("882", "12000"),
    "j49": ("882", "12000"), #2430
    "j48": ("882", "12000"), #3330
    "j47": ("882", "12000"),
    "j46": ("882", "12000"),
    "j45": ("882", "12000"),
    "j44": ("882", "12000"),
    "j43": ("882", "12000"),
    "j42": ("882", "12000"),
    "j41": ("882", "12000"),
    "j40": ("882", "12000"),
    "j39": ("882", "12000"),
}

# OL display string used by the resistance spec
RESISTANCE_OL_TEXT = "OL"


def _format_ohms(value) -> str:
    """Convert a raw ohm value (numeric or numeric-string) into a human
    readable string using Ω / kΩ / MΩ, auto-selecting the unit.
    Falls back to str(value) unchanged if it can't be parsed as a number."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)

    if v >= 1_000_000:
        scaled, unit = v / 1_000_000, "MΩ"
    elif v >= 1000:
        scaled, unit = v / 1000, "kΩ"
    else:
        # Keep sub-1000 values in plain ohms
        return f"{v:.2f} Ω"

    return f"{scaled:.2f} {unit}"


# ── Relay send w/ recovery (same pattern as self_dmm.py) ───────────────────
def _relay_send(screen, cmd_name: str, relay_history: list, *, retry_on_fail: bool = True) -> bool:
    fn = _RELAY_CMD_MAP.get(cmd_name)
    if fn is None:
        screen.log_signal.emit(f"ERROR: Unknown relay command '{cmd_name}'", True)
        return False

    ok = STM32RelayController.send_with_retry(fn)

    if ok:
        relay_history.append(cmd_name)
        return True

    if not retry_on_fail:
        return False

    print(f"[RECOVERY] Relay '{cmd_name}' failed — power-cycling CH3 and replaying state...")
    _ch3_power_cycle(screen)
    _stm32_sync_wait(screen)

    print(f"[RECOVERY] Replaying {len(relay_history)} prior relay command(s)...")
    for prev_cmd in relay_history:
        prev_fn = _RELAY_CMD_MAP.get(prev_cmd)
        if prev_fn is None:
            continue
        rep_ok = STM32RelayController.send_with_retry(prev_fn)
        status = "✓" if rep_ok else "✗ (non-fatal)"
        print(f"[RECOVERY]   {prev_cmd} → {status}")
        time.sleep(0.3)

    time.sleep(1.2)

    print(f"[RECOVERY] Retrying '{cmd_name}'...")
    retry_ok = _relay_send(screen, cmd_name, relay_history, retry_on_fail=False)
    if retry_ok:
        print(f"[RECOVERY] '{cmd_name}' succeeded after recovery ✓")
    else:
        print(f"[RECOVERY] '{cmd_name}' still failed after recovery ✗")
    return retry_ok


def _ch3_power_cycle(screen):
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
        time.sleep(5.0)
        print("[RECOVERY] CH3 ON ✓")
    except Exception as e:
        print(f"[RECOVERY] CH3 ON failed (non-fatal): {e}")


def _stm32_sync_wait(screen):
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


# ── Core relay-group runner ─────────────────────────────────────────────────
def _run_relay_group(screen, relay_history, group_relays, row_start, limits_table, overload_text=None, skip=None):
    """
    Switches each relay in group_relays ON one at a time, reads the DMM
    resistance, logs F/G/H/I columns starting at row_start, then switches
    that same relay back OFF before moving on to the next one.

    Returns True if every relay in the group passed.
    """
    group_passed = True
    skip = skip or set()

    for offset, relay in enumerate(group_relays):
        row = row_start + offset
        cmd_on = f"set_{relay}_on"
        cmd_off = f"set_{relay}_off"

        if relay in skip:
            print(f"{relay.upper()} skipped (row {row} left as-is)")
            continue

        ok = _relay_send(screen, cmd_on, relay_history)

        write_self_test_excel(f"F{row}", "CONNECTED" if ok else "FAILED")
        if not ok:
            screen.log_signal.emit(f"ERROR: Failed to connect {relay.upper()}", True)
            write_self_test_excel(f"I{row}", "FAIL")
            group_passed = False
            continue

        screen.log_signal.emit(f"{relay.upper()} successfully connected", False)

        min_val, max_val = limits_table.get(relay, (None, None))
        write_self_test_excel(f"G{row}", f"{_format_ohms(min_val)} - {_format_ohms(max_val)}")

        time.sleep(1.2)
        result = _dmm_module.read_resistance_for_self_test(screen, f"{relay.upper()} Resistance", min_val, max_val)
        time.sleep(1.2)

        if result:
            observation = result["observation"]

            if "OL" in str(observation).upper():
                write_self_test_excel(f"H{row}", overload_text)
                write_self_test_excel(f"I{row}", "FAIL")
                group_passed = False
            else:
                write_self_test_excel(f"H{row}", _format_ohms(observation))
                write_self_test_excel(f"I{row}", result["result"])
                if result["result"] != "PASS":
                    group_passed = False
        else:
            write_self_test_excel(f"H{row}", "READ ERROR")
            write_self_test_excel(f"I{row}", "FAIL")
            group_passed = False

        time.sleep(0.3)

        # Turn this relay back off before moving on to the next one
        _relay_send(screen, cmd_off, relay_history)
        time.sleep(0.3)

    return group_passed


# ── Resistance Test ──────────────────────────────────────────────────────────
def _run_resistance_test(screen):
    relay_history: list[str] = []
    overall_pass = True

    write_self_test_excel("D61", "( RESISTANCE MODE)")
    write_self_test_excel("D74", "( RESISTANCE MODE)")
    write_self_test_excel("D91", "( RESISTANCE MODE)")
    write_self_test_excel("G62", "EXPECTED VALUE")
    write_self_test_excel("G75", "EXPECTED VALUE")
    write_self_test_excel("G92", "EXPECTED VALUE")
    write_self_test_excel("H62", "VALUE READ")
    write_self_test_excel("H75", "VALUE READ")
    write_self_test_excel("H92", "VALUE READ")

    # ── Group 1: main relay S21, sub relays J30,J54,J53,J52,J51,J36 ──
    _relay_send(screen, "set_s21_on", relay_history)

    g1_pass = _run_relay_group(
        screen, relay_history,
        ["j30", "j54", "j53", "j52", "j51", "j36"],
        row_start=63,
        limits_table=RESISTANCE_LIMITS, overload_text=RESISTANCE_OL_TEXT
    )
    overall_pass &= g1_pass

    # ── Group 2: S21 OFF, S22 ON, sub relays J31,J32,J33,J34,J35,J37,J38 ──
    _relay_send(screen, "set_s21_off", relay_history)
    _relay_send(screen, "set_s22_on", relay_history)

    g2_pass = _run_relay_group(
        screen, relay_history,
        ["j31", "j32", "j33", "j34", "j35", "j37", "j38"],
        row_start=76,
        limits_table=RESISTANCE_LIMITS, overload_text=RESISTANCE_OL_TEXT
    )
    overall_pass &= g2_pass

    # ── S22 OFF, S26 ON, sub relays J50..J39 ──
    _relay_send(screen, "set_s22_off", relay_history)
    _relay_send(screen, "set_s26_on", relay_history)

    g3_pass = _run_relay_group(
        screen, relay_history,
        ["j50", "j49", "j48", "j47", "j46", "j45", "j44", "j43", "j42", "j41", "j40", "j39"],
        row_start=93,
        limits_table=RESISTANCE_LIMITS, overload_text=RESISTANCE_OL_TEXT,
        skip={"j50"},
    )
    overall_pass &= g3_pass

    _relay_send(screen, "set_s26_off", relay_history)

    if overall_pass:
        screen.log_signal.emit("==========SINGLE RELAY RESISTANCE TEST COMPLETED SUCCESSFULLY==========", False)
    else:
        screen.log_signal.emit("==========SINGLE RELAY RESISTANCE TEST COMPLETED WITH FAILURES==========", True)

    if hasattr(screen, "register_test_result"):
        screen.register_test_result("PASS" if overall_pass else "FAIL")

    return overall_pass

# ── Add these imports at the top of self_istj.py ───────────────────────────
from devices.apx_analyzer import (
    generator_control, read_apx_meter, read_apx_thd_freq, configure_apx,
)
from devices.power_supply import check_current_ch3


# ── Pairing test relay list (S/J only — no sbsel here) ──────────────────────
_PAIRING_RELAYS = [
    ("S1  / J7",  STM32RelayController.set_s01_on, STM32RelayController.set_s01_off,
                  STM32RelayController.set_j07_on, STM32RelayController.set_j07_off),

    ("S2  / J8",  STM32RelayController.set_s02_on, STM32RelayController.set_s02_off,
                  STM32RelayController.set_j08_on, STM32RelayController.set_j08_off),

    ("S3  / J9",  STM32RelayController.set_s03_on, STM32RelayController.set_s03_off,
                  STM32RelayController.set_j09_on, STM32RelayController.set_j09_off),

    ("S4  / J10", STM32RelayController.set_s04_on, STM32RelayController.set_s04_off,
                  STM32RelayController.set_j10_on, STM32RelayController.set_j10_off),

    ("S5  / J11", STM32RelayController.set_s05_on, STM32RelayController.set_s05_off,
                  STM32RelayController.set_j11_on, STM32RelayController.set_j11_off),

    ("S7  / J18", STM32RelayController.set_s07_on, STM32RelayController.set_s07_off,
                  STM32RelayController.set_j18_on, STM32RelayController.set_j18_off),

    ("S8  / J19", STM32RelayController.set_s08_on, STM32RelayController.set_s08_off,
                  STM32RelayController.set_j19_on, STM32RelayController.set_j19_off),

    ("S9  / J20", STM32RelayController.set_s09_on, STM32RelayController.set_s09_off,
                  STM32RelayController.set_j20_on, STM32RelayController.set_j20_off),

    ("S10 / J21", STM32RelayController.set_s10_on, STM32RelayController.set_s10_off,
                  STM32RelayController.set_j21_on, STM32RelayController.set_j21_off),

    ("S11 / J22", STM32RelayController.set_s11_on, STM32RelayController.set_s11_off,
                  STM32RelayController.set_j22_on, STM32RelayController.set_j22_off),

    ("S12 / J23", STM32RelayController.set_s12_on, STM32RelayController.set_s12_off,
                  STM32RelayController.set_j23_on, STM32RelayController.set_j23_off),

    ("S14 / J29", STM32RelayController.set_s14_on, STM32RelayController.set_s14_off,
                  STM32RelayController.set_j29_on, STM32RelayController.set_j29_off),

    ("S19 / J26", STM32RelayController.set_s19_on, STM32RelayController.set_s19_off,
                  STM32RelayController.set_j26_on, STM32RelayController.set_j26_off),

    ("J27 / J7",  STM32RelayController.set_j27_on, STM32RelayController.set_j27_off,
                  STM32RelayController.set_j07_on, STM32RelayController.set_j07_off),

    ("J24 / J12", STM32RelayController.set_j24_on, STM32RelayController.set_j24_off,
                  STM32RelayController.set_j12_on, STM32RelayController.set_j12_off),

    ("S6  / J8",  STM32RelayController.set_s06_on, STM32RelayController.set_s06_off,
                  STM32RelayController.set_j08_on, STM32RelayController.set_j08_off),

    ("S13 / J9",  STM32RelayController.set_s13_on, STM32RelayController.set_s13_off,
                  STM32RelayController.set_j09_on, STM32RelayController.set_j09_off),
]


# ── Pairing test: current-sense relay verification + APx THD/Freq check ────
def _run_pairing_channel(screen, label, s_on, s_off, j_on, j_off, s_row, j_row, gh_row):
    """
    Runs one S/J pairing check:
      1. baseline PSU current
      2. S relay ON → current must rise → CONNECTED/FAILED to F{s_row}
      3. J relay ON → current must rise again → CONNECTED/FAILED to F{j_row}
      4. read_apx_thd_freq → freq/thd/result to G/H/I{gh_row}
      5. J relay OFF, S relay OFF
    """
    s_num = label.split("/")[0].strip()
    j_num = label.split("/")[1].strip()

    pair_pass = True
    pair_label = "/".join(part.strip().upper() for part in label.split("/"))
    screen.log_signal.emit(f"({pair_label}) pair test started", False)

    # ── Baseline current before S relay ON ─────────────────────────────
    time.sleep(1.2)
    baseline = check_current_ch3(screen.psu.psu_inst)
    baseline_val = baseline["value"] if baseline else None

    # ── S relay ON ───────────────────────────────────────────────────────
    s_ok = STM32RelayController.send_with_retry(s_on)
    after_s_val = baseline_val

    if s_ok:
        time.sleep(1.2)
        after_s = check_current_ch3(screen.psu.psu_inst)
        after_s_val = after_s["value"] if after_s else None

        if after_s_val is not None and baseline_val is not None and after_s_val > baseline_val:
            write_self_test_excel(f"F{s_row}", "CONNECTED")
            if s_num.upper().startswith("S"):
                screen.log_signal.emit(f"{s_num} successfully set to UP position", False)
            else:
                screen.log_signal.emit(f"{s_num} successfully connected", False)
        else:
            write_self_test_excel(f"F{s_row}", "FAILED")
            screen.log_signal.emit(f"ERROR: Connector {s_num} current check failed "
                                    f"(baseline={baseline_val}, after={after_s_val})", True)
            pair_pass = False
    else:
        write_self_test_excel(f"F{s_row}", "FAILED")
        if s_num.upper().startswith("S"):
            screen.log_signal.emit(f"ERROR: Failed to set {s_num} to UP position", True)
        else:
            screen.log_signal.emit(f"ERROR: Failed to connect {s_num}", True)
        pair_pass = False

    # ── J relay ON ───────────────────────────────────────────────────────
    j_ok = STM32RelayController.send_with_retry(j_on)

    if j_ok:
        time.sleep(1.2)
        after_j = check_current_ch3(screen.psu.psu_inst)
        after_j_val = after_j["value"] if after_j else None

        if after_j_val is not None and after_s_val is not None and after_j_val > after_s_val:
            write_self_test_excel(f"F{j_row}", "CONNECTED")
            if j_num.upper().startswith("S"):
                screen.log_signal.emit(f"{j_num} successfully set to UP position", False)
            else:
                screen.log_signal.emit(f"{j_num} successfully connected", False)
        else:
            write_self_test_excel(f"F{j_row}", "FAILED")
            screen.log_signal.emit(f"ERROR: Connector {j_num} current check failed "
                                    f"(prev={after_s_val}, after={after_j_val})", True)
            pair_pass = False
    else:
        write_self_test_excel(f"F{j_row}", "FAILED")
        if j_num.upper().startswith("S"):
            screen.log_signal.emit(f"ERROR: Failed to set {j_num} to UP position", True)
        else:
            screen.log_signal.emit(f"ERROR: Failed to connect {j_num}", True)
        pair_pass = False

    # ── APx THD+N / Frequency check ─────────────────────────────────────
    time.sleep(1.2)
    clean_label = " ".join(label.split())
    data = read_apx_thd_freq(
        screen, f"{clean_label} AUDIO ANALYSER READING",
        max_thd=5.0, min_freq=995, max_freq=1005
    )

    if data:
        freq_txt = f"{data['frequency']:.2f} Hz" if data["frequency"] is not None else "N/A"
        thd_txt = f"{data['thdn']:.3f} %" if data["thdn"] is not None else "N/A"
        write_self_test_excel(f"G{gh_row}", freq_txt)
        write_self_test_excel(f"H{gh_row}", thd_txt)
        if data["result"] != "PASS":
            pair_pass = False
        write_self_test_excel(f"I{gh_row}", "PASS" if pair_pass else "FAIL")
    else:
        write_self_test_excel(f"G{gh_row}", "N/A")
        write_self_test_excel(f"H{gh_row}", "N/A")
        write_self_test_excel(f"I{gh_row}", "FAIL")
        pair_pass = False

    # ── Turn OFF J then S relay before next pair ─────────────────────────
    time.sleep(0.3)
    STM32RelayController.send_with_retry(j_off)
    time.sleep(0.3)
    STM32RelayController.send_with_retry(s_off)
    time.sleep(0.3)

    return pair_pass

# ── SB SEL (S35) sub-test relay list ─────────────────────────────────────────
_SBSEL_PAIRS = [
    ("S15/J13", STM32RelayController.set_s15_on, STM32RelayController.set_s15_off,
                STM32RelayController.set_j13_on, STM32RelayController.set_j13_off, 146),
    ("S16/J14", STM32RelayController.set_s16_on, STM32RelayController.set_s16_off,
                STM32RelayController.set_j14_on, STM32RelayController.set_j14_off, 148),
    ("S17/J15", STM32RelayController.set_s17_on, STM32RelayController.set_s17_off,
                STM32RelayController.set_j15_on, STM32RelayController.set_j15_off, 150),
    ("S18/J16", STM32RelayController.set_s18_on, STM32RelayController.set_s18_off,
                STM32RelayController.set_j16_on, STM32RelayController.set_j16_off, 152),
]


def _run_sbsel_test(screen):
    """
    SB SEL (S35) sub-test — runs after all main pairing relays are OFF.

    1. Baseline CH3 current, then S35 ON → current must rise → F145/I145.
    2. For each of S15/J13, S16/J14, S17/J15, S18/J16:
       - S relay ON, current must exceed the SB SEL baseline current → F{s_row}
       - J relay ON, current must exceed the S-relay current → F{j_row}
       - read_apx_thd_freq → G/H/I{gh_row} (gh_row == s_row)
       - turn OFF J then S before the next pair
    3. Turn S35 OFF at the end.

    Rows: F145 (S35), F146/F147 (S15/J13), F148/F149 (S16/J14),
          F150/F151 (S17/J15), F152/F153 (S18/J16).
    G/H/I145 is SB SEL relay-check-only (no APx read for S35 itself).
    G/H/I146,148,150,152 carry the freq/thd/result for each pair.
    """
    screen.log_signal.emit("── SB SEL (S35) sub-test started ──", False)
    sbsel_overall_pass = True

    # ── Baseline CH3 current before S35 ON ──────────────────────────────
    time.sleep(1.2)
    baseline = check_current_ch3(screen.psu.psu_inst)
    baseline_val = baseline["value"] if baseline else None

    # ── S35 (SB SEL) ON ──────────────────────────────────────────────────
    sbsel_ok = STM32RelayController.send_with_retry(STM32RelayController.set_s35_on)
    sbsel_current_val = baseline_val

    if sbsel_ok:
        time.sleep(1.2)
        after_sbsel = check_current_ch3(screen.psu.psu_inst)
        sbsel_current_val = after_sbsel["value"] if after_sbsel else None

        if (sbsel_current_val is not None and baseline_val is not None
                and sbsel_current_val > baseline_val):
            write_self_test_excel("F145", "CONNECTED")
            write_self_test_excel("I145", "PASS")
            screen.log_signal.emit("S35 (SB SEL) successfully set to UP position", False)
        else:
            write_self_test_excel("F145", "FAILED")
            write_self_test_excel("I145", "FAIL")
            screen.log_signal.emit(
                f"ERROR: SB SEL (S35) current check failed "
                f"(baseline={baseline_val}, after={sbsel_current_val})", True
            )
            sbsel_overall_pass = False
    else:
        write_self_test_excel("F145", "FAILED")
        write_self_test_excel("I145", "FAIL")
        screen.log_signal.emit("ERROR: Failed to set S35 (SB SEL) to UP position", True)
        sbsel_overall_pass = False

    # ── S/J pairs, gated on SB SEL current ──────────────────────────────
    for label, s_on, s_off, j_on, j_off, s_row in _SBSEL_PAIRS:
        j_row = s_row + 1
        gh_row = s_row
        pair_pass = True
        s_num, j_num = label.split("/")

        screen.log_signal.emit(f"({label}) pair test started", False)

        # ── S relay ON — must exceed SB SEL current ─────────────────────
        s_ok = STM32RelayController.send_with_retry(s_on)
        after_s_val = sbsel_current_val

        if s_ok:
            time.sleep(1.2)
            after_s = check_current_ch3(screen.psu.psu_inst)
            after_s_val = after_s["value"] if after_s else None

            if (after_s_val is not None and sbsel_current_val is not None
                    and after_s_val > sbsel_current_val):
                write_self_test_excel(f"F{s_row}", "CONNECTED")
                screen.log_signal.emit(f"{s_num} successfully set to UP position", False)
            else:
                write_self_test_excel(f"F{s_row}", "FAILED")
                screen.log_signal.emit(
                    f"ERROR: Connector {s_num} current check failed "
                    f"(sbsel={sbsel_current_val}, after={after_s_val})", True
                )
                pair_pass = False
        else:
            write_self_test_excel(f"F{s_row}", "FAILED")
            screen.log_signal.emit(f"ERROR: Failed to set {s_num} to UP position", True)
            pair_pass = False

        # ── J relay ON — must exceed S-relay current ────────────────────
        j_ok = STM32RelayController.send_with_retry(j_on)

        if j_ok:
            time.sleep(1.2)
            after_j = check_current_ch3(screen.psu.psu_inst)
            after_j_val = after_j["value"] if after_j else None

            if (after_j_val is not None and after_s_val is not None
                    and after_j_val > after_s_val):
                write_self_test_excel(f"F{j_row}", "CONNECTED")
                screen.log_signal.emit(f"{j_num} successfully connected", False)
            else:
                write_self_test_excel(f"F{j_row}", "FAILED")
                screen.log_signal.emit(
                    f"ERROR: Connector {j_num} current check failed "
                    f"(prev={after_s_val}, after={after_j_val})", True
                )
                pair_pass = False
        else:
            write_self_test_excel(f"F{j_row}", "FAILED")
            screen.log_signal.emit(f"ERROR: Failed to connect {j_num}", True)
            pair_pass = False

        # ── APx THD+N / Frequency check ──────────────────────────────────
        time.sleep(1.2)
        data = read_apx_thd_freq(
            screen, f"{label} AUDIO ANALYSER READING",
            max_thd=5.0, min_freq=995, max_freq=1005
        )

        if data:
            freq_txt = f"{data['frequency']:.2f} Hz" if data["frequency"] is not None else "N/A"
            thd_txt = f"{data['thdn']:.3f} %" if data["thdn"] is not None else "N/A"
            write_self_test_excel(f"G{gh_row}", freq_txt)
            write_self_test_excel(f"H{gh_row}", thd_txt)
            if data["result"] != "PASS":
                pair_pass = False
            write_self_test_excel(f"I{gh_row}", "PASS" if pair_pass else "FAIL")
        else:
            write_self_test_excel(f"G{gh_row}", "N/A")
            write_self_test_excel(f"H{gh_row}", "N/A")
            write_self_test_excel(f"I{gh_row}", "FAIL")
            pair_pass = False

        # ── Turn OFF J then S before next pair ───────────────────────────
        time.sleep(0.3)
        STM32RelayController.send_with_retry(j_off)
        time.sleep(0.3)
        STM32RelayController.send_with_retry(s_off)
        time.sleep(0.3)

        sbsel_overall_pass &= pair_pass

    # ── Turn OFF S35 (SB SEL) at the end ─────────────────────────────────
    STM32RelayController.send_with_retry(STM32RelayController.set_s35_off)
    time.sleep(0.3)

    if sbsel_overall_pass:
        screen.log_signal.emit("SB SEL sub-test completed successfully", False)
    else:
        screen.log_signal.emit("SB SEL sub-test completed with failures", True)

    return sbsel_overall_pass

# ── Extra triplet pairing tests: S31→S14→J29 and S28→S19→J26 ──────────────
# Gated on PSU CH1 current (unlike the S/J pairs above, which use CH3).
_EXTRA_TRIPLETS = [
    ("S31/S14/J29",
     STM32RelayController.set_s31_600ohm, STM32RelayController.set_s31_neutral,
     STM32RelayController.set_s14_on, STM32RelayController.set_s14_off,
     STM32RelayController.set_j29_on, STM32RelayController.set_j29_off,
     155),
    ("S28/S19/J26",
     STM32RelayController.set_s28_600ohms, STM32RelayController.set_s28_neutral,
     STM32RelayController.set_s19_on, STM32RelayController.set_s19_off,
     STM32RelayController.set_j26_on, STM32RelayController.set_j26_off,
     158),
]


def _run_extra_triplet_test(screen):
    """
    Extra triplet pairing tests: (S31/S14/J29) and (S28/S19/J26).
    Each triplet is gated on PSU channel 1 current, checked incrementally:
      baseline -> r1 ON (must exceed baseline) -> r2 ON (must exceed r1) ->
      r3 ON (must exceed r2) -> APx THD/Freq read -> turn off r3, r2, r1.

    Rows:
      S31/S14/J29: F155 (S31), F156 (S14), F157 (J29), G/H/I155
      S28/S19/J26: F158 (S28), F159 (S19), F160 (J26), G/H/I158
    """
    screen.log_signal.emit("── Extra triplet pairing sub-test started ──", False)
    overall_pass = True

    for label, r1_on, r1_off, r2_on, r2_off, r3_on, r3_off, row_start in _EXTRA_TRIPLETS:
        r1_row, r2_row, r3_row = row_start, row_start + 1, row_start + 2
        gh_row = row_start
        r1_name, r2_name, r3_name = [p.strip() for p in label.split("/")]
        triplet_pass = True

        screen.log_signal.emit(f"({label}) triplet test started", False)

        # ── Baseline CH1 current before r1 ON ───────────────────────────
        time.sleep(1.2)
        baseline = check_current_ch3(screen.psu.psu_inst)
        baseline_val = baseline["value"] if baseline else None

        # ── r1 (S31/S28) ON ─────────────────────────────────────────────
        r1_ok = STM32RelayController.send_with_retry(r1_on)
        after_r1_val = baseline_val

        if r1_ok:
            time.sleep(1.2)
            after_r1 = check_current_ch3(screen.psu.psu_inst)
            after_r1_val = after_r1["value"] if after_r1 else None

            if after_r1_val is not None and baseline_val is not None and after_r1_val > baseline_val:
                write_self_test_excel(f"F{r1_row}", "CONNECTED")
                screen.log_signal.emit(f"{r1_name} successfully set to 600Ω position", False)
            else:
                write_self_test_excel(f"F{r1_row}", "FAILED")
                screen.log_signal.emit(
                    f"ERROR: Connector {r1_name} current check failed "
                    f"(baseline={baseline_val}, after={after_r1_val})", True
                )
                triplet_pass = False
        else:
            write_self_test_excel(f"F{r1_row}", "FAILED")
            screen.log_signal.emit(f"ERROR: Failed to set {r1_name} to 600Ω", True)
            triplet_pass = False

        # ── r2 (S14/S19) ON ─────────────────────────────────────────────
        r2_ok = STM32RelayController.send_with_retry(r2_on)
        after_r2_val = after_r1_val

        if r2_ok:
            time.sleep(1.2)
            after_r2 = check_current_ch3(screen.psu.psu_inst)
            after_r2_val = after_r2["value"] if after_r2 else None

            if after_r2_val is not None and after_r1_val is not None and after_r2_val > after_r1_val:
                write_self_test_excel(f"F{r2_row}", "CONNECTED")
                screen.log_signal.emit(f"{r2_name} successfully set to UP position", False)
            else:
                write_self_test_excel(f"F{r2_row}", "FAILED")
                screen.log_signal.emit(
                    f"ERROR: Connector {r2_name} current check failed "
                    f"(prev={after_r1_val}, after={after_r2_val})", True
                )
                triplet_pass = False
        else:
            write_self_test_excel(f"F{r2_row}", "FAILED")
            screen.log_signal.emit(f"ERROR: Failed to set {r2_name} to UP position", True)
            triplet_pass = False

        # ── r3 (J29/J26) ON ─────────────────────────────────────────────
        r3_ok = STM32RelayController.send_with_retry(r3_on)

        if r3_ok:
            time.sleep(1.2)
            after_r3 = check_current_ch3(screen.psu.psu_inst)
            after_r3_val = after_r3["value"] if after_r3 else None

            if after_r3_val is not None and after_r2_val is not None and after_r3_val > after_r2_val:
                write_self_test_excel(f"F{r3_row}", "CONNECTED")
                screen.log_signal.emit(f"{r3_name} successfully connected", False)
            else:
                write_self_test_excel(f"F{r3_row}", "FAILED")
                screen.log_signal.emit(
                    f"ERROR: Connector {r3_name} current check failed "
                    f"(prev={after_r2_val}, after={after_r3_val})", True
                )
                triplet_pass = False
        else:
            write_self_test_excel(f"F{r3_row}", "FAILED")
            screen.log_signal.emit(f"ERROR: Failed to connect {r3_name}", True)
            triplet_pass = False

        # ── APx THD+N / Frequency check ─────────────────────────────────
        time.sleep(1.2)
        data = read_apx_thd_freq(
            screen, f"{label} AUDIO ANALYSER READING",
            max_thd=5.0, min_freq=995, max_freq=1005
        )

        if data:
            freq_txt = f"{data['frequency']:.2f} Hz" if data["frequency"] is not None else "N/A"
            thd_txt = f"{data['thdn']:.3f} %" if data["thdn"] is not None else "N/A"
            write_self_test_excel(f"G{gh_row}", freq_txt)
            write_self_test_excel(f"H{gh_row}", thd_txt)
            if data["result"] != "PASS":
                triplet_pass = False
            write_self_test_excel(f"I{gh_row}", "PASS" if triplet_pass else "FAIL")
        else:
            write_self_test_excel(f"G{gh_row}", "N/A")
            write_self_test_excel(f"H{gh_row}", "N/A")
            write_self_test_excel(f"I{gh_row}", "FAIL")
            triplet_pass = False

        # ── Turn OFF r3, r2, r1 before next triplet ──────────────────────
        time.sleep(0.3)
        STM32RelayController.send_with_retry(r3_off)
        time.sleep(0.3)
        STM32RelayController.send_with_retry(r2_off)
        time.sleep(0.3)
        STM32RelayController.send_with_retry(r1_off)
        time.sleep(0.3)

        overall_pass &= triplet_pass

    if overall_pass:
        screen.log_signal.emit("Extra triplet pairing sub-test completed successfully", False)
    else:
        screen.log_signal.emit("Extra triplet pairing sub-test completed with failures", True)

    return overall_pass

_VOLTAGE_RELAY_CMD_MAP = {
    "set_s24_on":  STM32RelayController.set_s24_on,
    "set_s24_off": STM32RelayController.set_s24_off,
    "set_j67_on":  STM32RelayController.set_j67_on,
    "set_j67_off": STM32RelayController.set_j67_off,
    "set_j68_on":  STM32RelayController.set_j68_on,
    "set_j68_off": STM32RelayController.set_j68_off,
    "set_s25_on":  STM32RelayController.set_s25_on,
    "set_s25_off": STM32RelayController.set_s25_off,
    "set_j70_on":  STM32RelayController.set_j70_on,
    "set_j70_off": STM32RelayController.set_j70_off,
    "set_j71_on":  STM32RelayController.set_j71_on,
    "set_j71_off": STM32RelayController.set_j71_off,
}
_RELAY_CMD_MAP.update(_VOLTAGE_RELAY_CMD_MAP)
# ── Voltage relay test: S24/J67,J68 and S25/J70,J71 ─────────────────────────
# Each S relay is a gate; the two J relays under it are tested one at a
# time — current must rise on each ON step relative to the previous
# reading, and the resulting DUT voltage must land in the expected window.
_VOLTAGE_RELAY_GROUPS = [
    ("S24", "set_s24_on", "set_s24_off",
     [("J67", "set_j67_on", "set_j67_off", 195, "9.9V", "12.1V"),   # +11V ±1.1V
      ("J68", "set_j68_on", "set_j68_off", 196, "-12.1V", "-9.9V")]),  # -11V ±1.1V
    ("S25", "set_s25_on", "set_s25_off",
     [("J70", "set_j70_on", "set_j70_off", 197, "9.9V", "12.1V"),   # +11V ±1.1V
      ("J71", "set_j71_on", "set_j71_off", 198, "-12.1V", "-9.9V")]),  # -11V ±1.1V
]


def _run_voltage_relay_channel(screen, relay_history, label, j_on, j_off, row,
                                min_v, max_v):
    """
    Turns a J relay ON, logs CONNECTED/FAILED to F{row} based on relay-send
    success, reads DUT voltage against (min_v, max_v), logs H/I{row}, then
    turns the J relay back OFF.
    """
    channel_pass = True

    j_ok = _relay_send(screen, j_on, relay_history)

    if j_ok:
        write_self_test_excel(f"F{row}", "CONNECTED")
        screen.log_signal.emit(f"{label} successfully connected (PASS)", False)
    else:
        write_self_test_excel(f"F{row}", "FAILED")
        screen.log_signal.emit(f"ERROR: Failed to connect {label} (FAIL)", True)
        channel_pass = False

    time.sleep(0.5)
    result = _dmm_module.read_voltage_for_self_test(screen, f"{label} DMM Voltage Check", min_v, max_v)
    if result:
        write_self_test_excel(f"H{row}", result["observation"])
        write_self_test_excel(f"I{row}", result["result"])
        if result["result"] != "PASS":
            channel_pass = False
    else:
        write_self_test_excel(f"H{row}", "READ ERROR")
        write_self_test_excel(f"I{row}", "FAIL")
        channel_pass = False

    time.sleep(0.3)
    STM32RelayController.send_with_retry(_RELAY_CMD_MAP[j_off])
    time.sleep(0.3)

    return channel_pass


def _run_voltage_relay_test(screen):
    """
    Voltage relay test.
    S24 gate: J67 (+11V ±1.1V) → F195/H195/I195, J68 (-11V ±1.1V) → F196/H196/I196.
    S25 gate: J70 (+11V ±1.1V) → F197/H197/I197, J71 (-11V ±1.1V) → F198/H198/I198.
    """
    screen.log_signal.emit("── Voltage relay test started ──", False)
    relay_history: list[str] = []
    overall_pass = True
    
    _psu_channel_on(screen, 1, 28.0, 1.0)
    time.sleep(0.5)

    for s_label, s_on, s_off, j_steps in _VOLTAGE_RELAY_GROUPS:
        screen.log_signal.emit(f"({s_label}) voltage relay group started", False)

        s_ok = _relay_send(screen, s_on, relay_history)
        if not s_ok:
            screen.log_signal.emit(f"ERROR: Failed to set {s_label} to UP position — skipping group (FAIL)", True)
            for j_label, _j_on, _j_off, row, _min_v, _max_v in j_steps:
                write_self_test_excel(f"F{row}", "FAILED")
                write_self_test_excel(f"H{row}", "N/A")
                write_self_test_excel(f"I{row}", "FAIL")
            overall_pass = False
            continue

        for j_label, j_on, j_off, row, min_v, max_v in j_steps:
            step_pass = _run_voltage_relay_channel(
                screen, relay_history, j_label, j_on, j_off, row, min_v, max_v
            )
            overall_pass &= step_pass

        time.sleep(0.3)
        STM32RelayController.send_with_retry(_RELAY_CMD_MAP[s_off])
        time.sleep(0.3)
        
    _psu_channel_off(screen, 1)
    
    if overall_pass:
        screen.log_signal.emit("==========VOLTAGE RELAY TEST COMPLETED SUCCESSFULLY==========", False)
    else:
        screen.log_signal.emit("==========VOLTAGE RELAY TEST COMPLETED WITH FAILURES==========", True)

    if hasattr(screen, "register_test_result"):
        screen.register_test_result("PASS" if overall_pass else "FAIL")

    return overall_pass

# ── Visual Inspection Check ──────────────────────────────────────────────
def _visual_inspection_check(screen, message, image_filename, h_row, i_row):
    """
    Shows a YES/NO operator popup with an optional reference image,
    waits for the operator's response, then logs it to H{h_row} and
    PASS/FAIL to I{i_row}. Returns True if operator answered YES.
    """
    image_path = str(RESOURCES_DIR / image_filename) if image_filename else ""

    screen._operator_event.clear()
    screen.operator_yesno_signal.emit(
        "⚠ Visual Inspection Check",
        message,
        image_path
    )
    screen._operator_event.wait()

    response = getattr(screen, "last_operator_response", None)
    write_self_test_excel(f"H{h_row}", response or "N/A")

    passed = (response == "YES")
    write_self_test_excel(f"I{i_row}", "PASS" if passed else "FAIL")

    if passed:
        screen.log_signal.emit(f"Operator confirmed: {message.strip()} — YES (PASS)", False)
    else:
        screen.log_signal.emit(f"Operator response: {message.strip()} — {response or 'NO RESPONSE'} (FAIL)", True)

    return passed


def _visual_relay_step(screen, relay_on_fn, relay_off_fn, f_row, ds_label,
                        message, image_filename, h_row, i_row, *, turn_off_after=True):
    """
    Turns a relay ON, logs CONNECTED/FAILED to F{f_row}, runs the visual
    inspection popup (H/I{h_row}/{i_row}), then optionally turns the relay
    back OFF before returning.
    """
    ok = STM32RelayController.send_with_retry(relay_on_fn)
    write_self_test_excel(f"F{f_row}", "CONNECTED" if ok else "FAILED")

    if ok:
        screen.log_signal.emit(f"{ds_label}: relay switched ON (PASS)", False)
    else:
        screen.log_signal.emit(f"ERROR: {ds_label} — failed to switch relay ON (FAIL)", True)

    time.sleep(0.5)
    popup_pass = _visual_inspection_check(screen, message, image_filename, h_row, i_row)

    if turn_off_after and relay_off_fn is not None:
        time.sleep(0.3)
        STM32RelayController.send_with_retry(relay_off_fn)
        time.sleep(0.3)

    return ok and popup_pass

# ── PSU channel control (for visual inspection DUT power) ───────────────────
def _psu_channel_on(screen, channel: int, voltage: float, current: float):
    """Turn on the given PSU channel at the specified voltage/current."""
    try:
        screen.psu.psu_send_command("*CLS")
        screen.psu.psu_send_command(f"INST:NSEL {channel}")
        time.sleep(0.1)
        screen.psu.psu_send_command(f"SOUR{channel}:VOLT {voltage}")
        time.sleep(0.05)
        screen.psu.psu_send_command(f"SOUR{channel}:CURR {current}")
        time.sleep(0.05)
        screen.psu.psu_send_command("OUTP ON")
        time.sleep(0.5)
        screen.log_signal.emit(f"PSU CH{channel} ON — {voltage}V / {current}A", False)
    except Exception as e:
        screen.log_signal.emit(f"ERROR: PSU CH{channel} ON failed: {e}", True)


def _psu_channel_off(screen, channel: int):
    """Turn off the given PSU channel."""
    try:
        screen.psu.psu_send_command(f"INST:NSEL {channel}")
        time.sleep(0.1)
        screen.psu.psu_send_command("OUTP OFF")
        time.sleep(0.3)
        screen.log_signal.emit(f"PSU CH{channel} OFF", False)
    except Exception as e:
        screen.log_signal.emit(f"ERROR: PSU CH{channel} OFF failed: {e}", True)
        
def _run_visual_inspection_test(screen):
    """
    Visual inspection check — cycles relevant relays and asks the operator
    to confirm each indicator LED illuminates.
    PSU CH1 (28V/1A) is powered before the COM key relay sequence (S27..S33)
    and switched off at the end; PSU CH2 (28V/1A) is powered on when S26
    (+28V LIGHT) is switched and also switched off at the end.
    Rows: H173/I173 (DS16), F176-F181/H176-H181/I176-I181 (COM key relays),
          F182-F184/H182-H184/I182-I184 (NORM/STBY/LOCAL),
          F185/H185/I185 (DS10/11), F187/H187/I187 (DS12/13),
          F189/H189/I189 (DS14), F190/H190/I190 (DS15).
    """
    overall_pass = True

    # ── Ensure all relevant relays are OFF before starting ──────────────
    for off_fn in (
        STM32RelayController.set_s27_off, STM32RelayController.set_s29_off,
        STM32RelayController.set_s30_off, STM32RelayController.set_s32_off,
        STM32RelayController.set_s34_off, STM32RelayController.set_s33_off,
        STM32RelayController.set_s21_off, STM32RelayController.set_s22_off,
        STM32RelayController.set_s23_local, STM32RelayController.set_s24_off,
        STM32RelayController.set_s25_off, STM32RelayController.set_s26_off,
    ):
        STM32RelayController.send_with_retry(off_fn)
        time.sleep(0.2)

    time.sleep(0.5)

    # ── ISTJ CONTROLLER PWR INDICATOR — no relay change, popup only ─────────────────
    p = _visual_inspection_check(
        screen, "• ISTJ CONTROLLER PWR INDICATOR LED should illuminate.",
        "ds_16.jpeg", 173, 173
    )
    overall_pass &= p

    # ── PSU CH1 ON — required before the COM key relay sequence starts ──
    _psu_channel_on(screen, 1, 28.0, 1.0)
    time.sleep(0.5)

    # ── COM key relays: S27,S29,S30,S32,S34,S33 → DS1..DS6 ───────────────
    com_steps = [
        (STM32RelayController.set_s27_on, STM32RelayController.set_s27_off, 176, "DS1 (COM 1 KEY)", "ds_01.jpeg", 176, 176),
        (STM32RelayController.set_s29_on, STM32RelayController.set_s29_off, 177, "DS2 (COM 2 KEY)", "ds_02.jpeg", 177, 177),
        (STM32RelayController.set_s30_on, STM32RelayController.set_s30_off, 178, "DS3 (COM 3 KEY)", "ds_03.jpeg", 178, 178),
        (STM32RelayController.set_s32_on, STM32RelayController.set_s32_off, 179, "DS4 (COM 4 KEY)", "ds_04.jpeg", 179, 179),
        (STM32RelayController.set_s34_on, STM32RelayController.set_s34_off, 180, "DS5 (COM 5 KEY)", "ds_05.jpeg", 180, 180),
        (STM32RelayController.set_s33_on, STM32RelayController.set_s33_off, 181, "DS6 (COM 6 KEY)", "ds_06.jpeg", 181, 181),
    ]
    for on_fn, off_fn, f_row, ds_label, img, h_row, i_row in com_steps:
        message = f"• {ds_label} LED should illuminate."
        p = _visual_relay_step(screen, on_fn, off_fn, f_row, ds_label, message, img, h_row, i_row)
        overall_pass &= p

    # ── NORM / STBY / LOCAL: S21, S22, S23(off) → DS7, DS8, DS9 ──────────
    p = _visual_relay_step(
        screen, STM32RelayController.set_s22_on, STM32RelayController.set_s22_off,
        182, "DS7 (NORM PWR)", "• DS7 (NORM PWR) LED should illuminate.", "ds_07.jpeg", 182, 182
    )
    overall_pass &= p
    
    p = _visual_relay_step(
        screen, STM32RelayController.set_s21_on, STM32RelayController.set_s21_off,
        183, "DS8 (STBY PWR)", "• DS8 (STBY PWR) LED should illuminate.", "ds_08.jpeg", 183, 183
    )
    overall_pass &= p

    # DS9 (LOCAL) — S23 OFF only, no prior ON step
    s23_off_ok = STM32RelayController.send_with_retry(STM32RelayController.set_s23_local)
    write_self_test_excel("F184", "CONNECTED" if s23_off_ok else "FAILED")
    if s23_off_ok:
        screen.log_signal.emit("S23 successfully set to LOCAL (PASS)", False)
    else:
        screen.log_signal.emit("ERROR: DS9 (LOCAL) — failed to set S23 to LOCAL (FAIL)", True)
    time.sleep(0.5)
    p = _visual_inspection_check(
        screen, "• DS9 (LOCAL) LED should illuminate.", "ds_09.jpeg", 184, 184
    )
    overall_pass &= (s23_off_ok and p)

    # ── +VN/-VN pairs: S24 → DS10/DS11, S25 → DS12/DS13 ──────────────────
    p = _visual_relay_step(
        screen, STM32RelayController.set_s24_on, STM32RelayController.set_s24_off,
        185, "DS10/DS11 (+VN/-VN)",
        "• DS10 (+VN) and DS11 (-VN) LEDs should illuminate.", "ds_10_11.jpeg", 185, 185
    )
    overall_pass &= p

    p = _visual_relay_step(
        screen, STM32RelayController.set_s25_on, STM32RelayController.set_s25_off,
        187, "DS12/DS13 (+VN/-VN)",
        "• DS12 (+VN) and DS13 (-VN) LEDs should illuminate.", "ds_12_13.jpeg", 187, 187
    )
    overall_pass &= p

    # ── PSU CH2 ON — required when S26 (+28V light) is switched ─────────
    _psu_channel_on(screen, 2, 28.0, 1.0)
    time.sleep(0.5)

    # ── +28V light: S26 → DS14 ───────────────────────────────────────────
    p = _visual_relay_step(
        screen, STM32RelayController.set_s26_on, STM32RelayController.set_s26_off,
        189, "DS14 (+28V LIGHT)",
        "• DS14 (+28V LIGHT) LED should illuminate.", "ds_14.jpeg", 189, 189
    )
    overall_pass &= p

    # ── REMOTE: S23 ON → DS15 ────────────────────────────────────────────
    p = _visual_relay_step(
        screen, STM32RelayController.set_s23_remote, STM32RelayController.set_s23_local,
        190, "DS15 (REMOTE)",
        "• DS15 (REMOTE) LED should illuminate.", "ds_15.jpeg", 190, 190
    )
    overall_pass &= p

    # ── PSU CH1/CH2 OFF — test finished ──────────────────────────────────
    _psu_channel_off(screen, 1)
    _psu_channel_off(screen, 2)

    if overall_pass:
        screen.log_signal.emit("==========VISUAL INSPECTION CHECK COMPLETED SUCCESSFULLY==========", False)
    else:
        screen.log_signal.emit("==========VISUAL INSPECTION CHECK COMPLETED WITH FAILURES==========", True)

    return overall_pass

def _run_norm_stby_remote_test(screen):
    """
    Continuation of visual inspection check — NORM PWR / STBY PWR LED
    behavior under LOCAL vs REMOTE.

    S24 (NORM PWR / DS10,DS11): S23 LOCAL, S24 ON → F206/F208 CONNECTED.
      Popup illuminated (LOCAL) → H206/I206.
      S23 REMOTE, popup extinguished → H208/I208.
      S24 OFF, S23 LOCAL.

    S25 (STBY PWR / DS12,DS13): S25 ON → F207/F209 CONNECTED.
      Popup illuminated (LOCAL) → H207/I207.
      S23 REMOTE, popup extinguished → H209/I209.
      S25 OFF, S23 LOCAL.
    """
    screen.log_signal.emit("==========VISUAL CHECK OF RELAY K101 STARTED==========", False)
    overall_pass = True

    _psu_channel_on(screen, 1, 28.0, 1.0)
    time.sleep(0.5)

    # ── S24 (NORM PWR / DS10,DS11) ───────────────────────────────────────
    STM32RelayController.send_with_retry(STM32RelayController.set_s23_local)
    time.sleep(0.3)
    s24_ok = STM32RelayController.send_with_retry(STM32RelayController.set_s24_on)
    write_self_test_excel("F206", "CONNECTED" if s24_ok else "FAILED")
    write_self_test_excel("F208", "CONNECTED" if s24_ok else "FAILED")
    if s24_ok:
        screen.log_signal.emit("S24 (NORM PWR) successfully set to UP position (PASS)", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S24 to UP position (FAIL)", True)
    time.sleep(0.5)

    p1 = _visual_inspection_check(
        screen,
        "NORM PWR: DS10 (+VN) & DS11 (-VN) LEDs should illuminate.",
        "ds_10_11.jpeg", 206, 206
    )
    overall_pass &= (s24_ok and p1)

    s23_rem_ok1 = STM32RelayController.send_with_retry(STM32RelayController.set_s23_remote)
    if s23_rem_ok1:
        screen.log_signal.emit("S23 successfully set to REMOTE (PASS)", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S23 to REMOTE (FAIL)", True)
    time.sleep(0.5)

    p2 = _visual_inspection_check(
        screen,
        "NORM PWR: DS10 (+VN) & DS11 (-VN) LEDs should extinguish.",
        "ds_10_11.jpeg", 208, 208
    )
    overall_pass &= (s23_rem_ok1 and p2)

    time.sleep(0.3)
    STM32RelayController.send_with_retry(STM32RelayController.set_s24_off)
    STM32RelayController.send_with_retry(STM32RelayController.set_s23_local)
    time.sleep(0.3)

    # ── S25 (STBY PWR / DS12,DS13) ───────────────────────────────────────
    s25_ok = STM32RelayController.send_with_retry(STM32RelayController.set_s25_on)
    write_self_test_excel("F207", "CONNECTED" if s25_ok else "FAILED")
    write_self_test_excel("F209", "CONNECTED" if s25_ok else "FAILED")
    if s25_ok:
        screen.log_signal.emit("S25 (STBY PWR) successfully set to UP position (PASS)", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S25 to UP position (FAIL)", True)
    time.sleep(0.5)

    p3 = _visual_inspection_check(
        screen,
        "STBY PWR: DS12 (+VN) & DS13 (-VN) LEDs should illuminate.",
        "ds_12_13.jpeg", 207, 207
    )
    overall_pass &= (s25_ok and p3)

    s23_rem_ok2 = STM32RelayController.send_with_retry(STM32RelayController.set_s23_remote)
    if s23_rem_ok2:
        screen.log_signal.emit("S23 switched to REMOTE (PASS)", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S23 to REMOTE (FAIL)", True)
    time.sleep(0.5)

    p4 = _visual_inspection_check(
        screen,
        "STBY PWR: DS12 (+VN) & DS13 (-VN) LEDs should extinguish.",
        "ds_12_13.jpeg", 209, 209
    )
    overall_pass &= (s23_rem_ok2 and p4)

    time.sleep(0.3)
    STM32RelayController.send_with_retry(STM32RelayController.set_s25_off)
    STM32RelayController.send_with_retry(STM32RelayController.set_s23_local)
    time.sleep(0.3)

    _psu_channel_off(screen, 1)

    if overall_pass:
        screen.log_signal.emit("==========VISUAL CHECK OF RELAY K101 COMPLETED SUCCESSFULLY==========", False)
    else:
        screen.log_signal.emit("==========VISUAL CHECK OF RELAY K101 COMPLETED WITH FAILURES==========", True)

    return overall_pass

def _run_pairing_test(screen):
    """
    Full S/J relay pairing test with PSU current-sense verification and
    APx THD+N/Frequency measurement.
    Rows F110..F143 (34 rows, 2 per pair — S row then J row).
    G/H/I110..G/H/I142 (17 rows, one per pair, on the S-relay row).
    """

    configure_apx(screen)
    time.sleep(2)
    generator_control(screen, level="5.0 Vrms", frequency=1000)

    overall_pass = True
    row_start = 110

    for idx, (label, s_on, s_off, j_on, j_off) in enumerate(_PAIRING_RELAYS):
        s_row = row_start + idx * 2
        j_row = s_row + 1
        gh_row = s_row

        pair_pass = _run_pairing_channel(
            screen, label, s_on, s_off, j_on, j_off, s_row, j_row, gh_row
        )
        overall_pass &= pair_pass
        
    # ── Extra triplet pairing tests: S31/S14/J29 and S28/S19/J26 ────────
    extra_pass = _run_extra_triplet_test(screen)
    overall_pass &= extra_pass

    # ── SB SEL (S35) sub-test — runs after all main relays are OFF ──────
    sbsel_pass = _run_sbsel_test(screen)
    overall_pass &= sbsel_pass
    


    if overall_pass:
        screen.log_signal.emit("==========RELAY PAIRING TEST COMPLETED SUCCESSFULLY==========", False)
    else:
        screen.log_signal.emit("==========RELAY PAIRING TEST COMPLETED WITH FAILURES==========", True)

    if hasattr(screen, "register_test_result"):
        screen.register_test_result("PASS" if overall_pass else "FAIL")

    return overall_pass


# ── Update run() to include the new pairing test ────────────────────────────
def run(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("Self ISTJ Test")
    screen.log_signal.emit("==========COMMENCING ISTJ SELF TEST==========", False)

    screen.operator_signal.emit(
        "⚠ Operator Action Required",
        "• Please ensure that the ISTJ Self test board is properly connected.",
        str(RESOURCES_DIR / "self_test.jpeg")
    )
    screen._operator_event.wait()
    time.sleep(1.2)

    screen.log_signal.emit("==========COMMENCING SINGLE RELAY TEST WITH DMM==========", False)
    _run_resistance_test(screen)

    time.sleep(1.2)
    screen.log_signal.emit("==========COMMENCING RELAY PAIRING TEST WITH APX==========", False)
    _run_pairing_test(screen)
    
    time.sleep(1.2)
    screen.log_signal.emit("==========COMMENCING VISUAL INSPECTION==========", False)
    _run_visual_inspection_test(screen)   
    
    time.sleep(1.2)
    _run_norm_stby_remote_test(screen)
    
    time.sleep(1.2)
    screen.log_signal.emit("==========COMMENCING VOLTAGE RELAY TEST==========", False)
    _run_voltage_relay_test(screen) 
    


    time.sleep(1.2)
    screen.log_signal.emit("==========SUCCESSFULLY COMPLETED ISTJ SELF TEST==========", False)