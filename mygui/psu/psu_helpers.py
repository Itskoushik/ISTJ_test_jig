# psu/psu_helpers.py
import time
import pyvisa

# Same identifiers DeviceMonitor already uses for PSU — keep these two
# in sync if the PSU model ever changes.
_PSU_VID_KEYWORDS = ["0x1AB1"]      # RIGOL VID
_PSU_PID_KEYWORDS = ["0x0E11"]      # DP800 series PID
_PSU_IDN_KEYWORDS = ["DP8", "RIGOL"]


def find_psu(rm=None, exclude_resources=None):
    """
    Scan VISA resources for a Rigol DP8xx-series PSU.
    Standalone — creates its own ResourceManager if none is given.
    Also accepts a PSUAutomation instance (its .rm is unwrapped),
    so PSUAutomation.find_psu(self) still works unchanged.

    Filters by VID/PID BEFORE opening any resource. This is required —
    opening a resource string that's already claimed by another live
    instrument (e.g. the oscilloscope, mid-command) can interrupt that
    instrument's transaction and knock it offline. Never widen this to
    a blind "try every resource" scan again.

    exclude_resources: optional set of VISA resource strings to skip
    outright (e.g. resources already known to belong to the scope/DMM).
    """
    if rm is not None and hasattr(rm, "rm"):
        rm = rm.rm  # unwrap PSUAutomation -> its ResourceManager

    own_rm = rm is None
    if own_rm:
        rm = pyvisa.ResourceManager()

    exclude_resources = exclude_resources or set()

    try:
        for res in rm.list_resources():
            if res.startswith("ASRL"):
                continue  # PSU is never on a COM port
            if res in exclude_resources:
                continue

            # ── VID/PID filter BEFORE opening — do not touch resources
            # that can't possibly be the PSU. ──
            if not any(v in res for v in _PSU_VID_KEYWORDS):
                continue
            if not any(p in res for p in _PSU_PID_KEYWORDS):
                continue

            try:
                inst = rm.open_resource(res, timeout=3000)
                time.sleep(0.3)  # let USB enumeration settle, mirrors DeviceMonitor
                idn = inst.query("*IDN?").strip()
                if any(kw in idn.upper() for kw in _PSU_IDN_KEYWORDS):
                    print(f"[PSU] Connected: {idn}")
                    return inst
                inst.close()
            except Exception:
                continue
    except Exception as e:
        print(f"[PSU HELPER] find_psu scan failed: {e}")
    return None


def find_psu_specific(resource_string: str, rm=None):
    """
    Fast-path reconnect to a PREVIOUSLY KNOWN PSU resource, without calling
    rm.list_resources(). A full bus enumeration touches every USB-TMC
    device and can transiently disrupt other live USB VISA sessions (e.g.
    the oscilloscope) — this avoids that entirely when the PSU's resource
    string from before the disconnect is already known.

    Returns the open instrument on success, None on failure (caller should
    fall back to find_psu() for a full rescan).
    """
    if not resource_string:
        return None

    if rm is not None and hasattr(rm, "rm"):
        rm = rm.rm

    own_rm = rm is None
    if own_rm:
        rm = pyvisa.ResourceManager()

    try:
        inst = rm.open_resource(resource_string, timeout=3000)
        time.sleep(0.3)
        idn = inst.query("*IDN?").strip()
        if any(kw in idn.upper() for kw in _PSU_IDN_KEYWORDS):
            print(f"[PSU] Reconnected directly to known resource: {idn}")
            return inst
        inst.close()
    except Exception as e:
        print(f"[PSU HELPER] find_psu_specific({resource_string}) failed: {e}")
    return None

import time

def turn_off_psu_channel(psu_inst, channel: int, psu_lock=None) -> bool:
    """Turn off a single PSU channel using the EXISTING psu_inst/lock. Never opens a new connection."""
    if psu_inst is None:
        return False
    try:
        def _do():
            psu_inst.write(f"INST:NSEL {channel}")
            time.sleep(0.05)
            psu_inst.write("OUTP OFF")
            time.sleep(0.05)
        if psu_lock is not None:
            with psu_lock:
                _do()
        else:
            _do()
        return True
    except Exception as e:
        print(f"[PSU HELPER] turn_off_psu_channel(Ch{channel}) failed: {e}")
        return False


def turn_off_all_psu_channels(psu_inst, psu_lock=None) -> bool:
    """Turn OFF CH1, CH2, CH3 in sequence using the EXISTING psu_inst/lock."""
    if psu_inst is None:
        return False
    all_ok = True
    for ch in (1, 2, 3):
        if not turn_off_psu_channel(psu_inst, ch, psu_lock=psu_lock):
            all_ok = False
    return all_ok


def turn_on_psu_channel(psu_inst, channel: int, voltage: float, current: float, psu_lock=None) -> bool:
    """Configure and enable a single PSU channel using the EXISTING psu_inst/lock."""
    if psu_inst is None:
        return False
    try:
        def _do():
            psu_inst.write(f"INST:NSEL {channel}")
            time.sleep(0.05)
            psu_inst.write(f"SOUR{channel}:VOLT {voltage}")
            time.sleep(0.05)
            psu_inst.write(f"SOUR{channel}:CURR {current}")
            time.sleep(0.05)
            psu_inst.write("OUTP ON")
            time.sleep(0.05)
        if psu_lock is not None:
            with psu_lock:
                _do()
        else:
            _do()
        return True
    except Exception as e:
        print(f"[PSU HELPER] turn_on_psu_channel(Ch{channel}) failed: {e}")
        return False