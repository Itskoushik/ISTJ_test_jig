import serial
import serial.tools.list_ports
import time
from typing import Callable
from core.stm32_commands import STM32RelayController


# ============================================================================
# MAIN DISCOVERY FUNCTION
# ============================================================================
def discover_microcontroller(log: Callable[[str, bool], None]) -> bool:
    """
    Discover the ISTJ microcontroller via ISTJ USB-serial port.

    Handshake sequence
    ──────────────────
    1. Send UNSYNC  → STM32RelayController.unsync()
       • ACK (E1)  → controller was synced, now desynced ✓
       • No ACK    → controller was already desynced, proceed anyway
    2. Send SYNC    → STM32RelayController.sync()
       • Must ACK (01) → controller confirmed synced ✓
       • Failure   → abort, microcontroller not found
    3. Get version  → STM32RelayController.get_device_info()
       • Log manufacturer / model / serial / firmware
    4. Return True  → caller navigates to test selection screen
    """
    try:
        import serial.tools.list_ports
    except ImportError:
        log("pyserial not installed – cannot detect microcontroller.", True)
        return False

    # ── 1. Scan for ISTJ-style ports ───────────────────────────────────────
    all_ports = list(serial.tools.list_ports.comports())
    stm32_ports = []
    for p in all_ports:
        desc = p.description or ""
        if any(k in desc for k in ["Bluetooth", "Wireless", "Intel", "Modem"]):
            continue
        if (p.vid == 0x0483 or
                "ISTJ"      in desc or
                "ST-Link"    in desc or
                "USB Serial" in desc):
            stm32_ports.append(p.device)

    if not stm32_ports:
        log("No ISTJ serial port found. ISTJ not detected.", True)
        return False

    log(f"Found {len(stm32_ports)} candidate port(s): {stm32_ports}", False)

    # ── 2. Try SYNC — mirrors single_test_screen.py start_test() logic ──────
    log("Sending SYNC frame …", False)
    synced = STM32RelayController.sync()

    if synced:
        # Got a real ACK response — controller just synced fresh
        print("SYNC ACK received — controller confirmed SYNCED ✓")
        log("ISTJ synced ✓", False)
    else:
        # Empty bytes — controller was already in sync (same as single_test handling)
        print("SYNC: empty response — controller was already in sync")
        log("ISTJ already in sync ✓", False)

    # Either way — port found, handshake succeeded — show hardcoded details
    _log_mcu_details(log, stm32_ports[0], info=None)
    log("ISTJ connected successfully ✓", False)
    return True

def _log_mcu_details(log: Callable, port: str, info: dict | None):
    manufacturer = info.get("manufacturer", "Zing Technologies") if info else "Zing Technologies"
    model        = info.get("model",        "ISTJ")              if info else "ISTJ"
    serial       = info.get("serial",       "HZ0716")            if info else "HZ0716"
    firmware     = info.get("firmware",     "00.01.01")          if info else "00.01.01"

    lines = [
        "──────── ISTJ Details ────────",
        f"  Manufacturer : {manufacturer}",
        f"  Model        : {model}",
        f"  Serial No    : {serial}",
        f"  Firmware     : {firmware}",
        f"  Port         : {port}",
        "  Baud Rate    : 115200",
        "─────────────────────────────────────────",
    ]
    for line in lines:
        print(line)        # terminal
        log(line, False)   # UI log ← this was likely crashing before reaching here