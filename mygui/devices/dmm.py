import pyvisa

def discover_dmm():
    """
    Detect ANY Rigol DMM and return details + connection
    """

    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()

        if not resources:
            return False, "No VISA resources detected", None

        for res in resources:
            try:
                inst = rm.open_resource(res)
                inst.timeout = 3000

                idn = inst.query("*IDN?").strip()
                idn_upper = idn.upper()

                if "RIGOL" in idn_upper and "DM" in idn_upper:

                    parts = idn.split(",")

                    manufacturer = parts[0] if len(parts) > 0 else "Unknown"
                    model = parts[1] if len(parts) > 1 else "Unknown"
                    serial = parts[2] if len(parts) > 2 else "Unknown"
                    firmware = parts[3] if len(parts) > 3 else "Unknown"

                    message = (
                        f"Rigol DMM detected at {res} ✓\n"
                        f"  Manufacturer: {manufacturer}\n"
                        f"  Model: {model}\n"
                        f"  Serial Number: {serial}\n"
                        f"  Firmware Version: {firmware}"
                    )

                    return True, message, inst

                inst.close()

            except Exception:
                continue

        return False, "No Rigol DMM detected", None

    except Exception as e:
        return False, f"DMM VISA error: {str(e)}", None

    


