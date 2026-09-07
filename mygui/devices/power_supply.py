import pyvisa
from typing import Callable, Optional, Tuple

TARGET_ID_KEYWORDS = ["RIGOL", "DP832"]


# Make rm a module-level or class-level variable
_rm = None

def get_resource_manager():
    global _rm
    if _rm is None:
        _rm = pyvisa.ResourceManager()
    return _rm
def discover_power_supply(log, claimed_resources):
    try:
        rm = get_resource_manager()
        resources = rm.list_resources()

        if not resources:
            log("No VISA resources found. Check PSU connection.", True)
            return False, None, None

        log("Scanning VISA resources for Power Supply...", False)

        for res in resources:
            if res in claimed_resources:
                continue

            try:
                inst = rm.open_resource(res, timeout=3000)

                idn = inst.query("*IDN?").strip()

                if all(k in idn for k in TARGET_ID_KEYWORDS):
                    parts = [p.strip() for p in idn.split(",")]

                    manufacturer = parts[0] if len(parts) > 0 else "Unknown"
                    model = parts[1] if len(parts) > 1 else "Unknown"
                    serial = parts[2] if len(parts) > 2 else "Unknown"
                    firmware = parts[3] if len(parts) > 3 else "Unknown"

                    log("──────── Power Supply Details ────────", False)
                    log(f"Power Supply found at {res} ✓", False)
                    log(f"  Manufacturer: {manufacturer}", False)
                    log(f"  Model: {model}", False)
                    log(f"  Serial Number: {serial}", False)
                    log(f"  Firmware Version: {firmware}", False)
                    log("──────────────────────────────────────", False)

                    claimed_resources.add(res)

                    # ✅ RETURN LIVE INSTANCE (DO NOT CLOSE)
                    return True, res, inst

                # ❌ Only close if NOT matched
                inst.close()

            except Exception:
                continue

        log("No RIGOL DP832 Power Supply detected.", True)
        return False, None, None

    except Exception as e:
        log(f"Power Supply discovery error: {str(e)}", True)
        return False, None, None



def force_other_channels_off(inst):
    for ch in [2, 3]:
        inst.write(f"INST:NSEL {ch}")
        inst.write("OUTP OFF")
    print("⛔ CH2 & CH3 forced OFF and frozen")
    
def check_current_ch1(inst, min_val=1.3, max_val=2.0):
    try:
        inst.write("INST:NSEL 1")
        current = float(inst.query("MEAS:CURR?").strip())

        observation = f"CH1 Current = {current:.2f} A"

        if min_val <= current <= max_val:
            return {
                "observation": observation + " (Within Range)",
                "result": "PASS",
                "value": f"{current:.2f} A"
            }
        else:
            return {
                "observation": observation + " (Out of Range)",
                "result": "FAIL",
                "value": f"{current:.2f} A"
            }

    except Exception as e:
        return {
            "observation": f"Error: {str(e)}",
            "result": "FAIL",
            "value": None
        }

def check_current_ch3(inst):
    try:
        inst.write("INST:NSEL 3")
        current = float(inst.query("MEAS:CURR?").strip())

        return {
            "observation": f"CH3 Current = {current:.2f} A",
            "result": "PASS",
            "value": f"{current:.2f} A"
        }

    except Exception as e:
        return {
            "observation": f"Error: {str(e)}",
            "result": "FAIL",
            "value": None
        }


def connect_power_supply(resource: str):
    rm = get_resource_manager()
    return rm.open_resource(resource, timeout=3000)

def disconnect_power_supply(inst):
    try:
        if inst:
            inst.close()
    except:
        pass

    
def reset_resource_manager():
    global _rm
    if _rm is not None:
        try:
            _rm.close()
        except Exception:
            pass
        _rm = None