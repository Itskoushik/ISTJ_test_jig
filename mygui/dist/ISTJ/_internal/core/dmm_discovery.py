import pyvisa


def _validate_rigol_dmm(inst, res_name):
    """
    Validates an already-open VISA resource is a genuine, stable Rigol DMM.
    Does not close inst. Returns (True, info_message) or (False, reason).
    """
    try:
        idn = inst.query("*IDN?").strip()
    except Exception as e:
        return False, f"IDN query failed: {e}"

    idn_upper = idn.upper()
    if "RIGOL" not in idn_upper or "DM" not in idn_upper:
        return False, f"Not a Rigol DMM (IDN={idn})"

    try:
        inst.query("*IDN?")
    except Exception as e:
        return False, f"IDN re-query failed (unstable session): {e}"

    parts = idn.split(",")
    manufacturer = parts[0] if len(parts) > 0 else "Unknown"
    model = parts[1] if len(parts) > 1 else "Unknown"
    serial = parts[2] if len(parts) > 2 else "Unknown"
    firmware = parts[3] if len(parts) > 3 else "Unknown"
    message = (
        f"Rigol DMM detected at {res_name} ✓\n"
        f"  Manufacturer: {manufacturer}\n"
        f"  Model: {model}\n"
        f"  Serial Number: {serial}\n"
        f"  Firmware Version: {firmware}"
    )
    return True, message


def discover_dmm(exclude_resources=None, log_fn=None):
    """
    Detect a Rigol DMM and return (ok, message, inst).

    USB-only: ASRL/GPIB/TCPIP/SOCKET resources are filtered out BEFORE
    rm.open_resource() is ever called on them — they are never opened,
    never queried, and can never produce a VI_ERROR_TMO from discovery.

    exclude_resources: VISA resource strings already claimed by other
    subsystems (PSU, oscilloscope) to skip.

    log_fn: optional callable(str), never raises. Intended for terminal
    (print) diagnostics only — callers should not route this to the GUI.
    """
    def _log(msg):
        if log_fn:
            try:
                log_fn(msg)
            except Exception:
                pass

    exclude = set(exclude_resources or [])

    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()
    except Exception as e:
        return False, f"DMM VISA error: {str(e)}", None

    if not resources:
        _log("[DMM] No VISA resources detected during discovery.")
        return False, "No VISA resources detected", None

    _log(f"[DMM] VISA resources found: {list(resources)}")

    for res in resources:
        # ── USB-only transport policy — filtered BEFORE open_resource() ──
        # ASRL is explicitly forbidden (Rigol DMM here is USB-only); no
        # other non-USB transport (GPIB/TCPIP/SOCKET) is attempted either.
        if not res.upper().startswith("USB"):
            _log(f"[DMM] Skipping non-USB resource: {res}")
            continue

        if res in exclude:
            _log(f"[DMM] Skipping claimed resource: {res}")
            continue

        inst = None
        try:
            _log(f"[DMM] Checking resource: {res}")
            inst = rm.open_resource(res)
            inst.timeout = 3000

            ok, info = _validate_rigol_dmm(inst, res)
            if ok:
                _log(f"[DMM] Valid Rigol DMM found: {res}")
                return True, info, inst

            _log(f"[DMM] Candidate rejected ({res}): {info}")
            inst.close()
            inst = None

        except Exception as e:
            _log(f"[DMM] Candidate error ({res}): {e}")
            if inst is not None:
                try:
                    inst.close()
                except Exception:
                    pass
            continue

    _log("[DMM] No Rigol DMM detected during recovery.")
    return False, "No Rigol DMM detected", None