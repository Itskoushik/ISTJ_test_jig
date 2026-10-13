from PyQt5.QtCore import *
from devices.device_types import DeviceType
from devices.device_listeners import (
    PSUListener, STM32Listener,
    OscilloscopeListener, DMMListener, AudioAnalyzerListener
)
import threading
from core.stm32_commands import STM32RelayController
class _ApxReconnectThread(QThread):
    """
    Runs the EXISTING devices.apx_analyzer.connect_apx() off the GUI thread.
    connect_apx() may launch APx500, sleep ~3s and do COM init, so it must
    never be called from the QTimer/_poll_reconnect path directly.
    Emits result(ok, reason) exactly once. Owns no UI objects.
    """
    result = pyqtSignal(bool, str)

    def run(self):
        import devices.apx_analyzer as _apx_mod
        try:
            ok, apx = _apx_mod.connect_apx(None)    # existing official path
            if not ok or apx is None:
                # connect_apx returns False for demo mode, but leaves the
                # demo instance in the module global — shut it down.
                try:
                    _apx_mod.close_apx()
                except Exception:
                    pass
                _apx_mod.apx = None
                self.result.emit(False, "connect_apx failed or APx is in DEMO mode")
                return
            # Validate it is a live, real-hardware connection.
            _ = apx.Version
            if apx.IsDemoMode:
                try:
                    _apx_mod.close_apx()
                except Exception:
                    pass
                _apx_mod.apx = None
                self.result.emit(False, "APx500 is in DEMO mode (no hardware)")
                return
            self.result.emit(True, "")
        except Exception as e:
            try:
                _apx_mod.apx = None
            except Exception:
                pass
            self.result.emit(False, str(e))
            
class DeviceMonitor(QObject):
    """
    Owns all device listener threads.
    Emits a single unified signal when any device disconnects.
    Safe to connect to GUI slots — signal crosses thread boundary automatically.
    """
    device_disconnected = pyqtSignal(str, str)   # (device_ui_name, message)
    device_reconnected  = pyqtSignal(str)         # (device_ui_name)

    # Maps DeviceType → display name used in EquipmentSelfCheckScreen cards
    DEVICE_UI_NAMES = {
        DeviceType.PSU:   "PSU (Power Supply)",
        DeviceType.OSC:   "Oscilloscope",
        DeviceType.DMM:   "DMM (Digital Multimeter)",
        DeviceType.AUDIO: "Audio Analyzer",
        DeviceType.MCU:   "Microcontroller",   # ← was "ISTJ" — must match the card's device key
    }
    # Hard-bound device identifiers from initial discovery
    DEVICE_IDENTIFIERS = {
        "PSU": {
            "vid_keywords": ["0x1AB1"],           # RIGOL VID in VISA resource string
            "pid_keywords": ["0x0E11"],           # DP800 series PID
            "idn_keywords": ["DP8", "RIGOL"],     # *IDN? response keywords
            "skip_asrl": True,                    # never on serial/COM ports
        },
        "DMM": {
            "vid_keywords": ["0x1AB1"],           # RIGOL VID
            "pid_keywords": ["0x0C94"],           # DM3000 series PID
            "idn_keywords": ["DM3", "RIGOL"],     # *IDN? response keywords
            "skip_asrl": True,
        },
        "OSC": {
            "vid_keywords": ["0x0699"],           # Tektronix VID
            "pid_keywords": ["0x03C4"],           # TBS1000 series PID
            "idn_keywords": ["TEKTRONIX", "TBS", "TEK"],  # *IDN? response keywords
            "skip_asrl": True,
        },
        "MCU": {
            "vid": 0x0483,                        # STM32 USB VID (integer for pyserial)
            "description_keywords": ["STM32", "ST-Link", "ISTJ", "USB Serial"],
            "skip_keywords": ["Bluetooth", "Wireless", "Intel", "Modem"],
            "baud": 115200,
        },
        "AUDIO": {
            "model_keywords": ["APx", "APx500", "APx525"],  # from connect_apx response
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listeners: list = []
        self._psu_lock = threading.Lock()
        self._worker = None
        self._monitor = None   # set externally by main.py — not used internally                          # ref to ConnectionWorker
        self._disconnected_devices: set = set()     # tracks what is currently down
        self._mcu_off_logged = False   # avoids re-printing "CH3 OFF, leaving it off" every 3s poll
        self._mcu_ch3_turned_on_at = None   # monotonic timestamp of the last genuine CH3 OFF→ON transition
        self._mcu_last_ch3_state = None     # last observed CH3 state, to detect the transition

        # While a self-test PRE-STEP owns CH3/ISTJ (_set_mcu_status is
        # called directly, bypassing the paused listener), suppress the
        # UI signal so the main Equipment Self Test dashboard doesn't
        # flicker Disconnected/Connected mid-test. Exactly one pending
        # transition is remembered and replayed once suppression lifts —
        # via resume_mcu_ui_signals() below — covering both a normal
        # test finish and an aborted/terminate()'d one.
        self._suppress_mcu_ui_signals = False
        self._mcu_ui_signal_pending = None   # None, or ("reconnected", None) / ("disconnected", reason)
        self._tracked_instance_ids = {}     # device UI name -> id(instance), set by _handback_oscilloscope()

        # APx reconnect guard: only ONE background reconnect may exist at a time.
        self._apx_reconnect_in_progress = False
        self._apx_reconnect_thread = None

        # Reconnect polling — fires on main thread every 3 s, safe for GUI
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(3000)
        self._reconnect_timer.timeout.connect(self._poll_reconnect)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    
    def handles_alive(self, worker) -> bool:
        def _ok(inst, lock=None):
            if inst is None:
                return False
            try:
                if lock is not None:
                    with lock:
                        return bool(inst.query("*IDN?"))
                return bool(inst.query("*IDN?"))
            except Exception:
                return False
        return (_ok(getattr(worker, "psu_inst", None), self._psu_lock)
                and _ok(getattr(worker, "dmm_connection", None))
                and _ok(getattr(worker, "oscilloscope_connection", None)))

    def start_all(self, worker):
        """
        Pass the ConnectionWorker after discovery completes.
        Only starts a listener if the device was actually found.
        """
        self._worker = worker
        status = worker.device_status

        if status.get("PSU (Power Supply)") and worker.psu_inst:
            self._start(PSUListener(worker.psu_inst, self._psu_lock))

        if status.get("Oscilloscope") and worker.oscilloscope_connection:
            self._start(OscilloscopeListener(worker.oscilloscope_connection))

        if status.get("DMM (Digital Multimeter)") and worker.dmm_connection:
            self._start(DMMListener(worker.dmm_connection))

        if status.get("Audio Analyzer"):
            self._start(AudioAnalyzerListener())

        # STM32 / ISTJ — open a fresh read-only serial handle for heartbeat
        if status.get("Microcontroller"):
            ser = self._open_stm32_serial()
            if ser:
                self._start(STM32Listener(ser, psu_inst=worker.psu_inst, psu_lock=self._psu_lock))

        self._reconnect_timer.start()

    def stop_all(self):
        self._reconnect_timer.stop()
        survivors = []
        for lst in self._listeners:
            print(f"[LISTENER] {lst.device_type} STOP REQUEST")
            lst.stop()
            lst.wait(2000)
            if lst.isRunning():
                # Never drop the reference to a still-running QThread —
                # doing so risks "QThread: Destroyed while thread is
                # still running" the moment GC collects it.
                print(f"[LISTENER] {lst.device_type} did NOT stop within 2s — keeping reference, will not be destroyed")
                survivors.append(lst)
            else:
                print(f"[LISTENER] {lst.device_type} FINISHED")
        self._listeners = survivors
        self._disconnected_devices.clear()

    def refresh_from_worker(self, worker) -> None:
        """
        Rebind PSU/DMM/Oscilloscope listeners to whatever device instances
        `worker` currently holds. Call this once, only when Single Test or
        Full Test may have replaced those instances since this monitor's
        listeners were started (see HALApplication._visited_test_mode).

        Mirrors the existing _try_reconnect_psu/_try_reconnect_dmm/
        _try_reconnect_oscilloscope pattern: stop the current listener for
        that device type via _remove_dead_listener() before starting the
        replacement, so this can never produce a duplicate listener. A
        device the worker has no instance for is left untouched — this
        only rebinds already-live instances, it never discovers or opens
        anything new.
        """
        if worker is None:
            return

        self._worker = worker  # in case Single/Full Test replaced the worker object itself

        psu_inst = getattr(worker, "psu_inst", None)
        if psu_inst is not None:
            self._remove_dead_listener(DeviceType.PSU)
            self._start(PSUListener(psu_inst, self._psu_lock))
            self._disconnected_devices.discard("PSU (Power Supply)")
            worker.device_status["PSU (Power Supply)"] = True

        dmm_conn = getattr(worker, "dmm_connection", None)
        if dmm_conn is not None:
            self._remove_dead_listener(DeviceType.DMM)
            self._start(DMMListener(dmm_conn))
            self._disconnected_devices.discard("DMM (Digital Multimeter)")
            worker.device_status["DMM (Digital Multimeter)"] = True

        osc_conn = getattr(worker, "oscilloscope_connection", None)
        if osc_conn is not None:
            self._remove_dead_listener(DeviceType.OSC)
            self._start(OscilloscopeListener(osc_conn))
            self._disconnected_devices.discard("Oscilloscope")
            worker.device_status["Oscilloscope"] = True

        # Microcontroller (ISTJ) — this method previously left MCU
        # completely untouched, unlike PSU/DMM/Oscilloscope above. That
        # meant arriving here via the "came from Single/Full Test" path
        # could leave NO STM32Listener running at all: whatever the card
        # showed was just leftover status, with nothing actually polling
        # OUTP? CH3. Manually turning CH3 off was then invisible — there
        # was no thread watching it. Mirror the same
        # existing-listener-first pattern refresh_for_self_test() already
        # uses, so this path also guarantees a live listener (or an
        # honest "Not Connected") instead of a silently unmonitored card.
        psu_inst = getattr(worker, "psu_inst", None)
        if psu_inst is not None:
            existing_mcu = next(
                (lst for lst in self._listeners
                 if lst.device_type == DeviceType.MCU and lst.isRunning()),
                None,
            )
            if existing_mcu is None:
                self._restart_mcu_listener(worker)

    def refresh_for_self_test(self, worker) -> None:
        """
        ALWAYS called on Equipment Self Test entry (never gated by
        _visited_test_mode). Performs a genuine validate-or-discover pass
        for PSU/DMM/Oscilloscope, and a liveness check (no reconnect) for
        the global APx, then rebinds every listener to the resulting
        instances. Leaves worker.device_status fully truthful before
        EquipmentSelfCheckScreen is constructed.
        """
        if worker is None:
            return
        self._worker = worker

        for lst in self._listeners:
            try:
                lst.pause()
            except Exception:
                pass

        psu_resource = None
        dmm_resource = None

        # ---------------- PSU ----------------
        psu_ok = False
        inst = getattr(worker, "psu_inst", None)
        if inst is not None:
            try:
                with self._psu_lock:
                    resp = inst.query("*IDN?")
                psu_ok = bool(resp)
            except Exception:
                psu_ok = False
        if not psu_ok:
            from psu.psu_helpers import find_psu
            inst = find_psu()
            psu_ok = inst is not None
        if psu_ok:
            worker.psu_inst = inst
            psu_resource = getattr(inst, "resource_name", None)
            self._remove_dead_listener(DeviceType.PSU)
            self._start(PSUListener(inst, self._psu_lock))
            self._disconnected_devices.discard("PSU (Power Supply)")
        else:
            worker.psu_inst = None
            self._remove_dead_listener(DeviceType.PSU)
            self._disconnected_devices.add("PSU (Power Supply)")
        worker.device_status["PSU (Power Supply)"] = psu_ok

        # ---------------- DMM ----------------
        dmm_ok = False
        inst = getattr(worker, "dmm_connection", None)
        if inst is not None:
            try:
                resp = inst.query("*IDN?")
                dmm_ok = bool(resp)
            except Exception:
                dmm_ok = False
        if not dmm_ok:
            from core.dmm_discovery import discover_dmm  
            exclude = {psu_resource} if psu_resource else set()
            dmm_ok, _msg, inst = discover_dmm(exclude_resources=exclude, log_fn=print)
        if dmm_ok:
            worker.dmm_connection = inst
            dmm_resource = getattr(inst, "resource_name", None)
            self._remove_dead_listener(DeviceType.DMM)
            self._start(DMMListener(inst))
            self._disconnected_devices.discard("DMM (Digital Multimeter)")
        else:
            worker.dmm_connection = None
            self._remove_dead_listener(DeviceType.DMM)
            self._disconnected_devices.add("DMM (Digital Multimeter)")
        worker.device_status["DMM (Digital Multimeter)"] = dmm_ok

        # ---------------- Oscilloscope ----------------
        osc_ok = False
        inst = getattr(worker, "oscilloscope_connection", None)
        if inst is not None:
            try:
                resp = inst.query("*IDN?")
                osc_ok = bool(resp)
            except Exception:
                osc_ok = False
        if not osc_ok:
            from devices.oscilloscope_connection import OscilloscopeConnection
            conn = OscilloscopeConnection()
            claimed = set()
            if psu_resource:
                claimed.add(psu_resource)
            if dmm_resource:
                claimed.add(dmm_resource)
            conn.claimed_visa_resources = claimed
            osc_ok = conn.discover_and_connect()
            inst = conn.instrument if osc_ok else None
        if osc_ok:
            worker.oscilloscope_connection = inst
            self._remove_dead_listener(DeviceType.OSC)
            self._start(OscilloscopeListener(inst))
            self._disconnected_devices.discard("Oscilloscope")
        else:
            worker.oscilloscope_connection = None
            self._remove_dead_listener(DeviceType.OSC)
            self._disconnected_devices.add("Oscilloscope")
        worker.device_status["Oscilloscope"] = osc_ok

        # ---------------- Microcontroller (ISTJ) ----------------
        # CH3 is the MCU's only power source, and its listener may have
        # been explicitly stopped without ever getting to notice CH3's
        # real state (e.g. PSU shutdown on the last time this screen was
        # left). Re-derive status from CH3 itself rather than trusting
        # whatever device_status was carried over.
        mcu_ok = False
        if psu_ok:
            try:
                with self._psu_lock:
                    ch3_state = worker.psu_inst.query("OUTP? CH3").strip().upper()
                if ch3_state in ("1", "ON"):
                    # If a live STM32Listener already exists and is running,
                    # trust it instead of tearing it down and reopening the
                    # COM port. _restart_mcu_listener() closes then reopens
                    # the serial handle — on some OSes the port isn't
                    # immediately reusable right after close(), so an
                    # already-healthy connection can transiently fail that
                    # reopen and flip Connected -> Disconnected a moment
                    # after this screen showed it as Connected.
                    existing_mcu = next(
                        (lst for lst in self._listeners
                         if lst.device_type == DeviceType.MCU and lst.isRunning()),
                        None,
                    )
                    if existing_mcu is not None:
                        mcu_ok = True
                        worker.device_status["Microcontroller"] = True
                    else:
                        mcu_ok = self._restart_mcu_listener(worker)  # sets status True + emits on success
            except Exception:
                mcu_ok = False
        if not mcu_ok:
            self._set_mcu_status(worker, False, "CH3 not ON or ISTJ COM port unavailable")

        # ---------------- Audio Analyzer (liveness only, no reconnect) ----
        from devices.apx_analyzer import get_apx
        apx_ok = False
        apx = get_apx()
        if apx is not None:
            try:
                _ = apx.Version
                apx_ok = True
            except Exception:
                apx_ok = False
        self._remove_dead_listener(DeviceType.AUDIO)
        if apx_ok:
            self._start(AudioAnalyzerListener())
            self._disconnected_devices.discard("Audio Analyzer")
        else:
            self._disconnected_devices.add("Audio Analyzer")
        worker.device_status["Audio Analyzer"] = apx_ok

        for lst in self._listeners:
            try:
                lst.resume()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _start(self, listener):
        listener.disconnected.connect(self._on_disconnected)
        listener.start()
        self._listeners.append(listener)

    def _remove_dead_listener(self, device_type: DeviceType):
        """
        Stop and remove any listener whose device_type matches.
        Called before spawning a replacement so we never run duplicates.
        A listener that fails to stop within the wait is kept in the
        survivors list (never dropped) so its QThread reference stays
        alive until it genuinely finishes — this does mean a caller
        could theoretically end up with two listeners of the same type
        briefly; that's preferable to a fatal Qt abort from destroying
        a running QThread.
        """
        survivors = []
        for lst in self._listeners:
            if lst.device_type == device_type:
                lst.stop()
                lst.wait(1000)
                if lst.isRunning():
                    print(f"[LISTENER] {device_type} did not stop within 1s during replace — keeping reference")
                    survivors.append(lst)
                    continue
                # stop() only flags the thread to exit — it never closes the
                # underlying serial handle, so a paused/stopped MCU listener
                # keeps the COM port locked for anyone trying to reopen it.
                if device_type == DeviceType.MCU:
                    try:
                        ser = getattr(lst, "ser", None)
                        # Never close STM32RelayController's shared
                        # persistent connection here — this listener may
                        # only be borrowing it (see _open_stm32_serial()).
                        # Closing someone else's handle breaks relay
                        # commands; only close a handle we independently
                        # opened ourselves.
                        if (ser is not None and ser.is_open
                                and ser is not STM32RelayController._default_state_conn):
                            ser.close()
                    except Exception:
                        pass
            else:
                survivors.append(lst)
        self._listeners = survivors

    # ------------------------------------------------------------------
    # Disconnect handling
    # ------------------------------------------------------------------

    def _on_disconnected(self, device_type: DeviceType, message: str):
        ui_name = self.DEVICE_UI_NAMES.get(device_type, str(device_type))
        if self._worker is not None:
            self._worker.device_status[ui_name] = False

        if device_type == DeviceType.MCU and self._suppress_mcu_ui_signals:
            self._disconnected_devices.add(ui_name)
            self._mcu_ui_signal_pending = ("disconnected", message)
            return

        if ui_name not in self._disconnected_devices:
            self._disconnected_devices.add(ui_name)
            self.device_disconnected.emit(ui_name, message)

    # ------------------------------------------------------------------
    # Reconnect polling (runs on main thread via QTimer — GUI-safe)
    # ------------------------------------------------------------------

    def _poll_reconnect(self):
        if not self._disconnected_devices:
            return
        # A self-test pre-step may have requested the timer stop via a
        # QueuedConnection invokeMethod, which is asynchronous and does
        # not guarantee this callback won't still fire once more before
        # the stop is processed. _suppress_mcu_ui_signals is a plain
        # attribute, set synchronously by the self-test worker BEFORE it
        # requests the timer stop, so checking it here closes that race
        # window for the device the suppression cares about.
        if self._suppress_mcu_ui_signals and "Microcontroller" in self._disconnected_devices:
            return   # a self test owns PSU/DMM/scope/APx/COM: reconnect nothing now

        # Snapshot BEFORE this cycle's recoveries mutate the set — this tells
        # us whether the PSU itself was down at the start of this poll, even
        # if PSU recovers earlier in this same loop than the MCU does.
        psu_was_down_this_cycle = "PSU (Power Supply)" in self._disconnected_devices

        for ui_name in list(self._disconnected_devices):
            recovered = False

            if ui_name == "PSU (Power Supply)":
                recovered = self._try_reconnect_psu()
            elif ui_name == "Oscilloscope":
                recovered = self._try_reconnect_oscilloscope()
            elif ui_name == "DMM (Digital Multimeter)":
                recovered = self._try_reconnect_dmm()
            elif ui_name == "Microcontroller":
                # If PSU itself dropped (cable pull / power-cycle), CH3's
                # output resets on the instrument — auto re-power it as part
                # of recovering the whole rig. If PSU never left, an operator
                # deliberately flipped CH3 off — leave it alone.
                recovered = self._try_reconnect_stm32(
                    force_power_on=psu_was_down_this_cycle
                )
            elif ui_name == "Audio Analyzer":
                recovered = self._try_reconnect_apx()

            if recovered:
                # _set_mcu_status() computes was_down from
                # _disconnected_devices itself and does its own discard —
                # discarding it here FIRST makes was_down always False,
                # so the reconnected signal (and thus the UI card update)
                # silently never fires even though the MCU is genuinely
                # back. Let _set_mcu_status() own the discard for MCU.
                if ui_name == "Microcontroller":
                    self._set_mcu_status(self._worker, True, "reconnect poll recovered")
                else:
                    self._disconnected_devices.discard(ui_name)
                    self.device_reconnected.emit(ui_name)

    # ------------------------------------------------------------------
    # Per-device reconnect strategies
    # ------------------------------------------------------------------

    def _try_reconnect_psu(self) -> bool:
        """
        Reconnect PSU — matched by VID/PID keywords in VISA resource string,
        then confirmed by *IDN? keywords. No serial number or resource hard-bind.
        """
        cfg = self.DEVICE_IDENTIFIERS["PSU"]
        try:
            import pyvisa, time
            rm = pyvisa.ResourceManager()

            for res in rm.list_resources():
                if res.startswith("ASRL"):
                    continue          # PSU is never on a COM port

                # VID + PID must both appear in the resource string
                if not any(v in res for v in cfg["vid_keywords"]):
                    continue
                if not any(p in res for p in cfg["pid_keywords"]):
                    continue

                try:
                    inst = rm.open_resource(res)
                    inst.timeout = 3000
                    time.sleep(0.5)   # let USB enumeration settle
                    idn = inst.query("*IDN?").strip().upper()

                    if not any(kw in idn for kw in cfg["idn_keywords"]):
                        inst.close()
                        continue      # VID/PID matched but wrong device — skip

                    self._remove_dead_listener(DeviceType.PSU)
                    self._worker.psu_inst = inst
                    self._worker.device_status["PSU (Power Supply)"] = True
                    self._start(PSUListener(inst, self._psu_lock))
                    return True

                except Exception:
                    continue

        except Exception:
            pass
        return False

    def _try_reconnect_oscilloscope(self) -> bool:
        """
        Reconnect Oscilloscope — matched by VID/PID keywords in VISA resource
        string, confirmed by *IDN? keywords. No serial or resource hard-bind.
        """
        cfg = self.DEVICE_IDENTIFIERS["OSC"]
        try:
            import pyvisa, time
            rm = pyvisa.ResourceManager()

            for res in rm.list_resources():
                if res.startswith("ASRL"):
                    continue

                if not any(v in res for v in cfg["vid_keywords"]):
                    continue
                if not any(p in res for p in cfg["pid_keywords"]):
                    continue

                try:
                    inst = rm.open_resource(res)
                    inst.timeout = 3000
                    time.sleep(0.5)
                    idn = inst.query("*IDN?").strip().upper()

                    if not any(kw in idn for kw in cfg["idn_keywords"]):
                        inst.close()
                        continue

                    self._remove_dead_listener(DeviceType.OSC)
                    self._worker.oscilloscope_connection = inst
                    self._worker.device_status["Oscilloscope"] = True
                    self._start(OscilloscopeListener(inst))
                    return True

                except Exception:
                    continue

        except Exception:
            pass
        return False

    def _try_reconnect_dmm(self) -> bool:
        """
        Reconnect DMM — matched by VID/PID keywords in VISA resource string,
        confirmed by *IDN? keywords. No serial or resource hard-bind.
        """
        cfg = self.DEVICE_IDENTIFIERS["DMM"]
        try:
            import pyvisa, time
            rm = pyvisa.ResourceManager()

            for res in rm.list_resources():
                if res.startswith("ASRL"):
                    continue

                if not any(v in res for v in cfg["vid_keywords"]):
                    continue
                if not any(p in res for p in cfg["pid_keywords"]):
                    continue

                try:
                    inst = rm.open_resource(res)
                    inst.timeout = 3000
                    time.sleep(0.5)
                    idn = inst.query("*IDN?").strip().upper()

                    if not any(kw in idn for kw in cfg["idn_keywords"]):
                        inst.close()
                        continue

                    self._remove_dead_listener(DeviceType.DMM)
                    self._worker.dmm_connection = inst
                    self._worker.device_status["DMM (Digital Multimeter)"] = True
                    self._start(DMMListener(inst))
                    return True

                except Exception:
                    continue

        except Exception:
            pass
        return False

    def _try_reconnect_stm32(self, force_power_on: bool = False) -> bool:
        import time
        try:
            # ── Step 1: PSU must be connected ────────────────────────────────
            psu = getattr(self._worker, "psu_inst", None)
            if psu is None:
                print("[MCU Reconnect] PSU not available — cannot power ISTJ")
                return False

            # ── Step 1.5: Check CH3's CURRENT state ──────────────────────────
            try:
                with self._psu_lock:
                    current_state = psu.query("OUTP? CH3").strip().upper()
            except Exception as e:
                print(f"[MCU Reconnect] Could not query CH3 state: {e}")
                return False

            if current_state not in ("1", "ON") and not force_power_on:
                # CH3 is off and the PSU itself never dropped — this was a
                # deliberate CH3 toggle. Don't override the operator.
                # Reset the last-known-state tracker so the next OFF→ON
                # transition is always detected as fresh, even if a PRIOR
                # reconnect cycle already left this at "ON" — otherwise the
                # CH3-write/boot-grace block below gets skipped on every
                # toggle after the first, letting sync race the board's
                # real boot/USB re-enumeration time instead of waiting for it.
                self._mcu_last_ch3_state = "OFF"
                self._mcu_ch3_turned_on_at = None
                if not self._mcu_off_logged:
                    print("[MCU Reconnect] CH3 is OFF (PSU still present) — leaving it off, not recovering MCU")
                    self._mcu_off_logged = True
                return False   # stays "Not Connected" until CH3 is turned back on manually

            self._mcu_off_logged = False   # state changed — allow the message to print again next time

            if current_state not in ("1", "ON") and force_power_on:
                print("[MCU Reconnect] CH3 is OFF following PSU recovery — re-powering it now")

            # ── Step 2: Only WRITE to CH3 on a genuine OFF→ON transition — never
            # re-affirm an already-ON channel on every 3s poll. Re-writing gives
            # no new boot signal to wait on and is why the old code reset nothing
            # to actually wait for, letting Step 3's fixed 2s sleep race the board.
            was_off = current_state not in ("1", "ON")
            if was_off or self._mcu_last_ch3_state != "ON":
                try:
                    with self._psu_lock:
                        psu.write("INST:NSEL 3")
                        time.sleep(0.4)
                        psu.write("VOLT 5.0")
                        time.sleep(0.3)
                        psu.write("CURR 1.0")
                        time.sleep(0.3)
                        psu.write("OUTP ON")
                        time.sleep(0.4)
                        state = psu.query("OUTP?").strip()

                    if state not in ("1", "ON"):
                        print(f"[MCU Reconnect] PSU CH3 did not turn ON (state={state})")
                        return False

                    print("[MCU Reconnect] PSU CH3 ON: 5V / 1A ✓")

                except Exception as e:
                    print(f"[MCU Reconnect] PSU CH3 setup failed: {e}")
                    return False

                self._mcu_ch3_turned_on_at = time.monotonic()

            self._mcu_last_ch3_state = "ON"

            # ── Step 3: Non-blocking boot-grace check — matches SelfTestWorker's
            # own calibrated ~8s wait instead of a flat 2s that never lines up
            # with real USB enumeration time. Skip this poll cycle (no sleep on
            # the GUI thread) until the grace period has elapsed.
            BOOT_GRACE_SECONDS = 5.0
            if self._mcu_ch3_turned_on_at is not None:
                elapsed = time.monotonic() - self._mcu_ch3_turned_on_at
                if elapsed < BOOT_GRACE_SECONDS:
                    print(f"[MCU Reconnect] Waiting for ISTJ to boot... ({elapsed:.1f}s/{BOOT_GRACE_SECONDS:.0f}s)")
                    return False

            # ── Step 4: Check COM port is visible ────────────────────────────
            ser = self._open_stm32_serial()
            if ser is None:
                print("[MCU Reconnect] COM port not visible yet — will retry")
                return False

            # If _open_stm32_serial() handed back STM32RelayController's
            # shared persistent connection, do NOT close it — that would
            # tear down relay command connectivity out from under
            # STM32RelayController. Only close+reopen when this really is
            # our own independently-opened handle.
            if ser is not STM32RelayController._default_state_conn:
                ser.close()           # release before reopening for the listener

                # ── Step 5: SYNC handshake skipped intentionally — COM port
                # visibility (Step 4) is treated as sufficient to mark the card
                # "Connected". Avoids waiting on/failing over the UNSYNC→SYNC
                # round-trip just to update UI status.
                print("[MCU Reconnect] COM port visible — marking connected (SYNC skipped)")

                # ── Step 6: Reopen handle for listener heartbeat ──────────────────
                ser = self._open_stm32_serial()
                if ser is None:
                    print("[MCU Reconnect] Could not reopen COM port for listener")
                    return False
            else:
                print("[MCU Reconnect] COM port visible — marking connected (SYNC skipped)")

            self._remove_dead_listener(DeviceType.MCU)
            self._worker.device_status["Microcontroller"] = True
            self._start(STM32Listener(ser, psu_inst=psu, psu_lock=self._psu_lock))
            self._mcu_ch3_turned_on_at = None
            print("[MCU Reconnect] ISTJ listener restarted ✓")
            return True

        except Exception as e:
            print(f"[MCU Reconnect] Unexpected error: {e}")
            return False
    def borrow_oscilloscope_handle(self, screen) -> bool:
        """
        Move the live oscilloscope VISA session from DeviceMonitor's
        ownership to screen.osc_conn, without closing/reopening it —
        mirrors the PSU handle borrow. Call once at pre-step, before any
        test code touches the oscilloscope.
        """
        from devices.oscilloscope_connection import OscilloscopeConnection

        raw_inst = getattr(self._worker, "oscilloscope_connection", None)
        if raw_inst is None:
            screen.osc_conn = None
            return False

        self._remove_dead_listener(DeviceType.OSC)
        self._disconnected_devices.discard("Oscilloscope")

        conn = OscilloscopeConnection()
        conn.instrument = raw_inst
        conn.resource_string = getattr(raw_inst, "resource_name", None)

        try:
            idn = raw_inst.query("*IDN?").strip()
            conn.identification = conn._parse_idn_response(idn)
        except Exception:
            conn.identification = None

        screen.osc_conn = conn
        screen.log_signal.emit(
            "[PRE-STEP] Oscilloscope handle borrowed from DeviceMonitor ✓ (listener paused)",
            False,
        )
        return True

    def _try_reconnect_apx(self) -> bool:
        """
        Returns True only for the passive case (APx object is already alive).
        A real relaunch is asynchronous: it is started here and completed in
        _on_apx_reconnect_result(), which does its own status/signal work.
        """
        import time as _t

        # AFTER: reconnect guard — never start a second worker.
        if self._apx_reconnect_in_progress:
            return False
        # A running self test owns APx (its pre-step closes/relaunches it).
        if self._suppress_mcu_ui_signals:
            return False

        # Existing 30 s throttle preserved: don't relaunch APx500 every tick.
        now = _t.monotonic()
        if now - getattr(self, "_last_apx_try", 0.0) < 30.0:
            return False
        self._last_apx_try = now

        try:
            from devices.apx_analyzer import get_apx
            apx = get_apx()
            if apx is not None:
                try:
                    _ = apx.Version             # passive liveness check
                    self._remove_dead_listener(DeviceType.AUDIO)
                    self._worker.device_status["Audio Analyzer"] = True
                    self._start(AudioAnalyzerListener())
                    return True
                except Exception:
                    pass                        # object is dead -> relaunch below

            # BEFORE: get_apx() is None (APx500 closed) -> return False forever.
            # AFTER:  APx500 may have been completely closed, so reconnect with
            #         the existing connect_apx() lifecycle in a BACKGROUND
            #         worker instead of only inspecting the old object.
            self._apx_reconnect_in_progress = True
            th = _ApxReconnectThread()
            self._apx_reconnect_thread = th
            th.result.connect(self._on_apx_reconnect_result)
            th.finished.connect(lambda t=th: self._on_apx_thread_finished(t))
            th.start()
            print("[APX Reconnect] background reconnect started")
        except Exception as e:
            self._apx_reconnect_in_progress = False
            print(f"[APX Reconnect] could not start worker: {e}")
        return False

    @pyqtSlot(bool, str)
    def _on_apx_reconnect_result(self, ok: bool, reason: str):
        """Main-thread handler. DeviceMonitor owns the state; the UI only
        receives device_reconnected, so a destroyed screen is harmless."""
        self._apx_reconnect_in_progress = False   # failure -> later poll retries
        if not ok:
            print(f"[APX Reconnect] failed: {reason} — will retry on a later poll")
            return
        if self._suppress_mcu_ui_signals:
            # A self test started meanwhile; it relaunches APx itself and
            # _resume_monitor_listeners() restores the listener afterwards.
            print("[APX Reconnect] self test active — deferring listener start")
            return
        # Exactly ONE fresh listener: remove any dead/stale one first.
        self._remove_dead_listener(DeviceType.AUDIO)
        self._start(AudioAnalyzerListener())
        if self._worker is not None:
            self._worker.device_status["Audio Analyzer"] = True
        was_down = "Audio Analyzer" in self._disconnected_devices
        self._disconnected_devices.discard("Audio Analyzer")
        if was_down:
            self.device_reconnected.emit("Audio Analyzer")
        print("[APX Reconnect] Audio Analyzer reconnected ✓")

    def _on_apx_thread_finished(self, thread):
        # Defensive: clear the guard even if the thread died without emitting.
        # The thread reference is dropped only after Qt says it has finished.
        if thread is self._apx_reconnect_thread:
            self._apx_reconnect_thread = None
            self._apx_reconnect_in_progress = False

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _open_stm32_serial(self):
        """
        Open a serial handle for the MCU via the ONE authoritative port
        resolver, STM32RelayController.get_cached_or_discover_port() —
        no independent comports() scan here anymore. This makes the
        screen's notion of "the ISTJ port" and the relay controller's
        _cached_port the SAME cache (Req #3/#8/#9): a full USB enumeration
        only happens when that cache is actually invalid, and it benefits
        every caller of this method identically — start_all(),
        refresh_for_self_test(), _restart_mcu_listener(),
        _try_reconnect_stm32() — with zero changes to any of them.
        """
        import serial

        cfg = self.DEVICE_IDENTIFIERS["MCU"]
        port = STM32RelayController.get_cached_or_discover_port()
        if port is None:
            return None

        # ── Reuse STM32RelayController's own persistent connection if
        # it's already open on this exact port, instead of opening a
        # SECOND independent serial.Serial handle. A COM port is
        # exclusive-access at the OS level — a second concurrent open on
        # the same port from this same process fails every time with a
        # busy/access-denied error, and the old code below mistook that
        # failure for "device not present", invalidating _cached_port on
        # an already-healthy, already-connected controller. This is the
        # actual cause of "COM port not visible yet — will retry" firing
        # forever even while ISTJ is genuinely connected.
        shared = STM32RelayController._default_state_conn
        if (shared is not None and getattr(shared, "is_open", False)
                and getattr(shared, "port", None) == port):
            return shared

        try:
            ser = serial.Serial(port, cfg["baud"], timeout=1)
            if ser.isOpen():
                return ser
        except Exception:
            # Re-check the shared connection once more before giving up —
            # a race where sync() opened _default_state_conn a moment
            # after get_cached_or_discover_port() ran above would land
            # here. Only invalidate the cache if there's truly no live
            # connection to fall back on.
            shared = STM32RelayController._default_state_conn
            if (shared is not None and getattr(shared, "is_open", False)
                    and getattr(shared, "port", None) == port):
                return shared
            # Cached port existed but couldn't actually be opened (claimed
            # elsewhere, or genuinely gone) — invalidate so the NEXT call
            # re-discovers instead of retrying the same dead port forever.
            STM32RelayController._cached_port = None

        return None
    
    def _restart_mcu_listener(self, worker=None) -> bool:
        """
        Remove any existing MCU listener and start a brand-new STM32Listener
        on a freshly opened serial handle. This is the ONLY place besides
        _try_reconnect_stm32() that is allowed to create an STM32Listener —
        used by SelfTestWorker's pre-step after it power-cycles CH3 and does
        its own raw ISTJ sync, so DeviceMonitor regains ownership of MCU
        connectivity monitoring afterward instead of being left with none.

        Never call this while an MCU listener you still want is running —
        it always removes-then-recreates.
        """
        worker = worker or self._worker
        if worker is None:
            return False

        self._remove_dead_listener(DeviceType.MCU)

        ser = self._open_stm32_serial()
        if ser is None:
            return False

        self._start(STM32Listener(ser, psu_inst=getattr(worker, "psu_inst", None), psu_lock=self._psu_lock))
        # _set_mcu_status also fires device_reconnected — without it the
        # screen's card never learns the sync succeeded.
        self._set_mcu_status(worker, True, "ISTJ listener restarted")
        return True
    
    def _set_mcu_status(self, worker, connected: bool, reason: str = "") -> None:
        """
        ...
        While a self-test PRE-STEP owns CH3/ISTJ (_suppress_mcu_ui_signals
        is True), the transition is still tracked in device_status/
        _disconnected_devices as before — callers that read those directly
        keep working — but the signal itself is deferred to
        resume_mcu_ui_signals() instead of firing immediately, so the
        equipment screen doesn't flicker mid-test.
        """
        if worker is not None:
            worker.device_status["Microcontroller"] = connected
        if connected:
            was_down = "Microcontroller" in self._disconnected_devices
            self._disconnected_devices.discard("Microcontroller")
            if was_down:
                if self._suppress_mcu_ui_signals:
                    self._mcu_ui_signal_pending = ("reconnected", None)
                else:
                    self.device_reconnected.emit("Microcontroller")
        else:
            was_up = "Microcontroller" not in self._disconnected_devices
            self._disconnected_devices.add("Microcontroller")
            if was_up:
                final_reason = reason or "PSU Channel 3 is OFF"
                if self._suppress_mcu_ui_signals:
                    self._mcu_ui_signal_pending = ("disconnected", final_reason)
                else:
                    self.device_disconnected.emit("Microcontroller", final_reason)

    def resume_mcu_ui_signals(self):
        """
        Stop suppressing Microcontroller status signals and replay the
        single most recent transition recorded while suppressed, if any.
        Call this whenever a self-test that owned CH3/ISTJ finishes —
        normally (SelfTestWorker's own finally) or aborted (SelfTestDialog's
        _resume_listeners_after_abort(), which is the only place that can
        still run after a hard terminate() skipped the worker's own
        cleanup). Idempotent — a second call with nothing pending is a
        no-op, so it's always safe to call defensively.
        """
        self._suppress_mcu_ui_signals = False
        pending = self._mcu_ui_signal_pending
        self._mcu_ui_signal_pending = None
        if pending is None:
            return
        kind, reason = pending
        if kind == "reconnected":
            self.device_reconnected.emit("Microcontroller")
        else:
            self.device_disconnected.emit("Microcontroller", reason)