import pyvisa

def classify_device(idn: str):
    """
    Universal device classifier using IDN string.
    Works for ANY brand.
    """

    idn_u = idn.upper()

    # ===== DMM =====
    dmm_keywords = [
        "DMM", "MULTIMETER",
        "344", "345", "346",      # Keysight series
        "DM3", "DM30",            # Rigol
        "KEITHLEY",
        "FLUKE",
        "8846", "8845", "2110"
    ]

    # ===== OSCILLOSCOPE =====
    scope_keywords = [
        "DSO", "MSO", "DS", "DHO",
        "SDS", "TDS", "DPO",
        "OSCILLOSCOPE"
    ]

    # ===== POWER SUPPLY =====
    psu_keywords = [
        "DP", "E36", "POWER SUPPLY",
        "PSU", "N670"
    ]

    # classify
    if any(k in idn_u for k in dmm_keywords):
        return "dmm"

    if any(k in idn_u for k in scope_keywords):
        return "oscilloscope"

    if any(k in idn_u for k in psu_keywords):
        return "power"

    return "unknown"


def scan_all_instruments(log):
    rm = pyvisa.ResourceManager()
    all_resources = rm.list_resources()

    # keep only real instrument buses
    resources = [
        r for r in all_resources
        if r.startswith("USB") or r.startswith("TCPIP")
    ]


    used = set()

    devices = {
        "dmm": None,
        "oscilloscope": None,
        "power": None
    }

    log(f"Scanning VISA resources... ({len(resources)} found)", False)

    for res in resources:
        if res in used:
            continue

        try:
            inst = rm.open_resource(res, timeout=2000)
            inst.write_termination = '\n'
            inst.read_termination = '\n'

            idn = inst.query("*IDN?").strip()
            dtype = classify_device(idn)

            parts = idn.split(",")
            manufacturer = parts[0] if len(parts)>0 else "Unknown"
            model = parts[1] if len(parts)>1 else "Unknown"
            serial = parts[2] if len(parts)>2 else "Unknown"
            firmware = parts[3] if len(parts)>3 else "Unknown"

            # ===== DMM =====
            if dtype == "dmm" and not devices["dmm"]:
                devices["dmm"] = inst
                used.add(res)

                log(f"DMM detected at {res} ✓", False)
                log(f"  Manufacturer: {manufacturer}", False)
                log(f"  Model: {model}", False)
                log(f"  Serial: {serial}", False)
                log(f"  Firmware: {firmware}", False)
                continue

            # ===== OSCILLOSCOPE =====
            if dtype == "oscilloscope" and not devices["oscilloscope"]:
                if res in used:
                    inst.close()
                    continue

                devices["oscilloscope"] = inst
                used.add(res)

                log(f"Oscilloscope detected at {res} ✓", False)
                log(f"  Manufacturer: {manufacturer}", False)
                log(f"  Model: {model}", False)
                log(f"  Serial: {serial}", False)
                log(f"  Firmware: {firmware}", False)
                continue

            # ===== PSU =====
            if dtype == "power" and not devices["power"]:
                devices["power"] = inst
                used.add(res)

                log(f"Power Supply detected at {res} ✓", False)
                log(f"  Manufacturer: {manufacturer}", False)
                log(f"  Model: {model}", False)
                log(f"  Serial: {serial}", False)
                continue

            inst.close()

        except Exception:
            pass

    return devices
