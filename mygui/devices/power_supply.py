import pyvisa
from typing import Callable, Optional, Tuple

TARGET_ID_KEYWORDS = ["RIGOL", "DP832"]


def discover_power_supply(
    log: Callable[[str, bool], None],
    claimed_resources: set
) -> Tuple[bool, Optional[str]]:
    """
    Discover and connect to RIGOL DP832 power supply via VISA.
    Pure device logic (NO PyQt, NO UI).
    """

    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()

        if not resources:
            log("No VISA resources found. Check PSU connection.", True)
            return False, None

        log("Scanning VISA resources for Power Supply...", False)

        for res in resources:
            if res in claimed_resources:
                continue

            try:
                inst = rm.open_resource(res, timeout=3000)
                try:
                    idn = inst.query("*IDN?").strip()
                finally:
                    inst.close()

                if all(k in idn for k in TARGET_ID_KEYWORDS):
                    parts = [p.strip() for p in idn.split(",")]

                    manufacturer = parts[0] if len(parts) > 0 else "Unknown"
                    model = parts[1] if len(parts) > 1 else "Unknown"
                    serial = parts[2] if len(parts) > 2 else "Unknown"
                    firmware = parts[3] if len(parts) > 3 else "Unknown"

                    log(f"Power Supply found at {res} ✓", False)
                    log(f"  Manufacturer: {manufacturer}", False)
                    log(f"  Model: {model}", False)
                    log(f"  Serial Number: {serial}", False)
                    log(f"  Firmware Version: {firmware}", False)

                    claimed_resources.add(res)
                    return True, res

            except Exception:
                continue

        log("No RIGOL DP832 Power Supply detected. Check USB/LAN connection.", True)
        return False, None

    except Exception as e:
        log(f"Power Supply discovery error: {str(e)}", True)
        return False, None
TARGET_ID_KEYWORDS = ["RIGOL", "DP832"]

def find_dp832():
    rm = pyvisa.ResourceManager()
    for res in rm.list_resources():
        try:
            inst = rm.open_resource(res, timeout=3000)
            idn = inst.query("*IDN?").strip()
            if all(k in idn for k in TARGET_ID_KEYWORDS):
                print(f"Connected to: {idn}")
                return inst
            inst.close()
        except Exception:
            pass
    return None


def force_other_channels_off(inst):
    for ch in [2, 3]:
        inst.write(f"INST:NSEL {ch}")
        inst.write("OUTP OFF")
    print("⛔ CH2 & CH3 forced OFF and frozen")