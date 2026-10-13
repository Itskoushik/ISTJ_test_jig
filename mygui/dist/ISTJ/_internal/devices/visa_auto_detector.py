import pyvisa





DMM_PREFIXES = (
"DM3", "DM6", "DM9",           # Rigol DMMs
"34460", "34461", "34465",      # Keysight
"8846", "8845", "2110",         # Fluke / Keithley
)

DMM_KEYWORDS = (
    "MULTIMETER", "DMM",
    "KEITHLEY", "FLUKE",
)

PSU_PREFIXES = (
    "DP8", "DP7", "DP3",           # Rigol PSUs  ← DP832 starts with DP8
    "E3631", "E3632", "E3633",     # Keysight
    "N5700", "N6700",
)

PSU_KEYWORDS = (
    "POWER SUPPLY", "PSU",
)

# Oscilloscope prefixes — be SPECIFIC, no short 2-char matches
SCOPE_PREFIXES = (
    "DS1", "DS2", "DS4", "DS6", "DS7",
    "DHO",
    "MSO5", "MSO7", "MSO1",
    "DSO-X", "DSOX", "MSOX",
    "SDS",
    "TDS", "DPO", "MDO", "MSO", "TBS",  # ← added TBS
    "HDO", "MXO", "WXO",
)

SCOPE_KEYWORDS = (
    "OSCILLOSCOPE",
)

def classify_device(idn: str):
    """
    Classifies a VISA instrument by its IDN string.
    Uses model-prefix matching first (specific), then keyword fallback.
    PSU check runs before oscilloscope to avoid Rigol cross-match.
    """
    idn_u = idn.upper()

    # Extract model field (second CSV field)
    parts = [p.strip() for p in idn.split(",")]
    model = parts[1].upper() if len(parts) > 1 else ""

    # ── 1. DMM (check first — least ambiguous prefixes) ──────────────
    if any(model.startswith(p) for p in DMM_PREFIXES):
        return "dmm"
    if any(k in idn_u for k in DMM_KEYWORDS):
        return "dmm"

    # ── 2. PSU (must come BEFORE oscilloscope — Rigol shared brand) ──
    if any(model.startswith(p) for p in PSU_PREFIXES):
        return "power"
    if any(k in idn_u for k in PSU_KEYWORDS):
        return "power"

    # ── 3. OSCILLOSCOPE ───────────────────────────────────────────────
    if any(model.startswith(p) for p in SCOPE_PREFIXES):
        return "oscilloscope"
    if any(k in idn_u for k in SCOPE_KEYWORDS):
        return "oscilloscope"

    return "unknown"


def scan_all_instruments(log, skip_resources: set = None):
    """
    Scans all USB and TCPIP VISA resources and classifies each instrument.
    Pass skip_resources to exclude already-claimed addresses (e.g. PSU).
    """
    rm = pyvisa.ResourceManager()
    all_resources = rm.list_resources()

    resources = [
        r for r in all_resources
        if (r.startswith("USB") or r.startswith("TCPIP"))
        and r not in (skip_resources or set())   # ← skip already-claimed
    ]

    devices = {
        "dmm": None,
        "oscilloscope": None,
        "power": None,
    }

    log(f"Scanning VISA resources... ({len(resources)} found)", False)

    for res in resources:
        try:
            inst = rm.open_resource(res, timeout=3000)

            # Tektronix scopes reject '\n' termination — let VISA use defaults
            try:
                idn = inst.query("*IDN?").strip()
            except Exception:
                # Retry without any termination characters (Tektronix USB)
                inst.write_termination = ''
                inst.read_termination = ''
                idn = inst.query("*IDN?").strip()
            dtype = classify_device(idn)

            parts = [p.strip() for p in idn.split(",")]
            manufacturer = parts[0] if len(parts) > 0 else "Unknown"
            model        = parts[1] if len(parts) > 1 else "Unknown"
            serial       = parts[2] if len(parts) > 2 else "Unknown"
            firmware     = parts[3] if len(parts) > 3 else "Unknown"

            if dtype == "dmm" and not devices["dmm"]:
                devices["dmm"] = inst
                log("──────── DMM Details ────────", False)
                log(f"DMM detected at {res} ✓", False)
                log(f"  Manufacturer: {manufacturer}", False)
                log(f"  Model: {model}", False)
                log(f"  Serial: {serial}", False)
                log(f"  Firmware: {firmware}", False)
                log("─────────────────────────────", False)

            elif dtype == "oscilloscope" and not devices["oscilloscope"]:
                devices["oscilloscope"] = inst
                log("──────── Oscilloscope Details ────────", False)
                log(f"Oscilloscope detected at {res} ✓", False)
                log(f"  Manufacturer: {manufacturer}", False)
                log(f"  Model: {model}", False)
                log(f"  Serial: {serial}", False)
                log(f"  Firmware: {firmware}", False)
                log("──────────────────────────────────────", False)

            elif dtype == "power" and not devices["power"]:
                devices["power"] = inst
                log(f"Power Supply (secondary) detected at {res} ✓", False)

            else:
                log(f"  Unclassified: {res} → {idn[:60]}", False)
                inst.close()

        except Exception as e:
            log(f"  Could not query {res}: {e}", True)

    return devices
