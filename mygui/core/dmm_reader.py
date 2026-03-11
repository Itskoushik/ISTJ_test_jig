import time
import pyvisa

_dmm = None   # global hidden connection


# ===============================
# CONNECT DMM ONCE
# ===============================
def _get_dmm():
    global _dmm

    if _dmm:
        return _dmm

    try:
        rm = pyvisa.ResourceManager()
        resources = rm.list_resources()

        for res in resources:
            try:
                inst = rm.open_resource(res, timeout=3000)
                idn = inst.query("*IDN?").strip().upper()

                if "RIGOL" in idn and "DM" in idn:
                    _dmm = inst
                    return _dmm

                inst.close()
            except:
                pass
    except:
        pass

    return None


# ===============================
# UNIT STRING → OHMS
# ===============================
def _to_ohms(value):
    """
    Converts:
    1M, 1.2K, 500, 2.2Mohm → ohms
    """

    if value is None:
        return None

    s = str(value).upper().replace("OHM", "").replace("Ω", "").strip()

    multiplier = 1

    if "G" in s:
        multiplier = 1e9
        s = s.replace("G", "")
    elif "M" in s:
        multiplier = 1e6
        s = s.replace("M", "")
    elif "K" in s:
        multiplier = 1e3
        s = s.replace("K", "")

    return float(s) * multiplier


# ===============================
# AUTO FORMAT LIKE REAL DMM
# ===============================
def _format_resistance(value_ohm):
    """
    Display in kΩ / MΩ like real DMM
    """

    if value_ohm >= 1e6:
        return f"{value_ohm/1e6:.3f} MΩ"
    elif value_ohm >= 1e3:
        return f"{value_ohm/1e3:.3f} kΩ"
    else:
        return f"{value_ohm:.3f} Ω"


# ===============================
# MAIN FUNCTION
# ===============================
def read_resistance(screen, label="Resistance", min_val=None, max_val=None):
    """
    Smart resistance reader with range check + auto unit display

    Examples:
    read_resistance(screen,"R1")
    read_resistance(screen,"R1","1M")
    read_resistance(screen,"R1",None,"500")
    read_resistance(screen,"R1","1K","10K")
    """

    dmm = _get_dmm()

    if not dmm:
        screen.log_signal.emit("❌ DMM not connected", True)
        return {
            "value": 0,
            "observation": "NO DMM",
            "result": "FAIL"
        }

    try:
        # set resistance mode
        dmm.write(":FUNCtion:RESistance")
        time.sleep(0.25)

        raw = dmm.query(":MEASure:RESistance?").strip()
        measured = float(raw)

        # convert limits
        min_ohm = _to_ohms(min_val)
        max_ohm = _to_ohms(max_val)

        display_val = _format_resistance(measured)

        # ================= ONLY READING =================
        if min_ohm is None and max_ohm is None:
            screen.log_signal.emit(f"{label}: {display_val}", False)
            return {
                "value": measured,
                "observation": display_val,
                "result": "OK"
            }

        # ================= RANGE CHECK =================
        status = True

        if min_ohm is not None and measured < min_ohm:
            status = False

        if max_ohm is not None and measured > max_ohm:
            status = False

        # range text
        range_txt = ""
        if min_val and max_val:
            range_txt = f"(Range {min_val} - {max_val})"
        elif min_val:
            range_txt = f"(>{min_val})"
        elif max_val:
            range_txt = f"(<{max_val})"

        # ================= RESULT =================
        result_text = "PASS" if status else "FAIL"
        # 🔴 Update overall flag
        if hasattr(screen, "register_test_result"):
            screen.register_test_result(result_text)

        # emit log
        if status:
            screen.log_signal.emit(
                f"{label}: {display_val} {range_txt}  PASS ✅",
                False
            )
        else:
            screen.log_signal.emit(
                f"{label}: {display_val} {range_txt}  FAIL ❌",
                True
            )

        # return structured data
        return {
            "value": measured,
            "observation": display_val,
            "result": result_text
        }

    except Exception as e:
        screen.log_signal.emit(f"DMM read error: {str(e)}", True)
        return None
    
# ===============================
# UNIT STRING → VOLTS
# ===============================
def _to_volts(value):
    """
    Converts:
    5, 5V, 500mV, 0.5V → volts
    """

    if value is None:
        return None

    s = str(value).upper().replace("V", "").strip()

    multiplier = 1

    if "MV" in str(value).upper():
        multiplier = 1e-3
        s = s.replace("MV", "")
    elif "KV" in str(value).upper():
        multiplier = 1e3
        s = s.replace("KV", "")

    return float(s) * multiplier


# ===============================
# AUTO FORMAT VOLTAGE LIKE DMM
# ===============================
def _format_voltage(v):
    if abs(v) >= 1:
        return f"{v:.3f} V"
    else:
        return f"{v*1000:.1f} mV"


# ===============================
# DC VOLTAGE READER
# ===============================
def read_voltage(screen, label="Voltage", min_val=None, max_val=None):
    """
    Smart DC voltage reader

    Examples:
    read_voltage(screen,"V1")
    read_voltage(screen,"V1","5")
    read_voltage(screen,"V1",None,"12V")
    read_voltage(screen,"V1","4.5","5.5")
    read_voltage(screen,"V1","500mV","1V")
    """

    dmm = _get_dmm()

    if not dmm:
        screen.log_signal.emit("❌ DMM not connected", True)
        return {
            "value": 0,
            "observation": "NO DMM",
            "result": "FAIL"
        }

    try:
        # set DC voltage mode
        dmm.write(":FUNCtion:VOLTage:DC")
        time.sleep(0.25)

        raw = dmm.query(":MEASure:VOLTage:DC?").strip()
        measured = float(raw)

        # convert limits
        min_v = _to_volts(min_val)
        max_v = _to_volts(max_val)

        display_val = _format_voltage(measured)

        # ===== ONLY READING =====
        if min_v is None and max_v is None:
            screen.log_signal.emit(f"{label}: {display_val}", False)

            return {
                "value": measured,
                "observation": display_val,
                "result": "PASS"
            }

        status = True

        if min_v is not None and measured < min_v:
            status = False

        if max_v is not None and measured > max_v:
            status = False

        # range text
        range_txt = ""
        if min_val and max_val:
            range_txt = f"(Range {min_val} - {max_val})"
        elif min_val:
            range_txt = f"(>{min_val})"
        elif max_val:
            range_txt = f"(<{max_val})"

        # result text
        result_text = "PASS" if status else "FAIL"
        # 🔴 Update overall flag
        if hasattr(screen, "register_test_result"):
            screen.register_test_result(result_text)

        # emit log
        if status:
            screen.log_signal.emit(
                f"{label}: {display_val} {range_txt}  PASS ✅",
                False
            )
        else:
            screen.log_signal.emit(
                f"{label}: {display_val} {range_txt}  FAIL ❌",
                True
            )

        # return structured data
        return {
            "value": measured,
            "observation": display_val,
            "result": result_text
        }

    except Exception as e:
        screen.log_signal.emit(f"Voltage read error: {str(e)}", True)
        return None

