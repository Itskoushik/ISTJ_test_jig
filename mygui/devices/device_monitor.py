from PyQt5.QtCore import *
from devices.device_types import DeviceType
from devices.device_listeners import (
    PSUListener, STM32Listener,
    OscilloscopeListener, DMMListener, AudioAnalyzerListener
)
import threading
from core.stm32_commands import STM32RelayController

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
        self._tracked_instance_ids = {}     # device UI name -> id(instance), set by _handback_oscilloscope()

        # Reconnect polling — fires on main thread every 3 s, safe for GUI
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(3000)
        self._reconnect_timer.timeout.connect(self._poll_reconnect)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
        for lst in self._listeners:
            lst.stop()
            lst.wait(2000)
        self._listeners.clear()
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
        """
        survivors = []
        for lst in self._listeners:
            if lst.device_type == device_type:
                lst.stop()
                lst.wait(1000)
                # stop() only flags the thread to exit — it never closes the
                # underlying serial handle, so a paused/stopped MCU listener
                # keeps the COM port locked for anyone trying to reopen it.
                if device_type == DeviceType.MCU:
                    try:
                        ser = getattr(lst, "ser", None)
                        if ser is not None and ser.is_open:
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
            self._worker.device_status[ui_name] = False   # ← keep worker.device_status truthful
        if ui_name not in self._disconnected_devices:
            self._disconnected_devices.add(ui_name)
            self.device_disconnected.emit(ui_name, message)

    # ------------------------------------------------------------------
    # Reconnect polling (runs on main thread via QTimer — GUI-safe)
    # ------------------------------------------------------------------

    def _poll_reconnect(self):
        if not self._disconnected_devices:
            return

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
            BOOT_GRACE_SECONDS = 8.0
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

            ser.close()               # release before handshake controller uses it

            # ── Step 5: UNSYNC → SYNC handshake ──────────────────────────────
            STM32RelayController.unsync()
            time.sleep(0.3)

            if not STM32RelayController.sync():
                print("[MCU Reconnect] SYNC failed — board not ready yet")
                return False

            print("[MCU Reconnect] SYNC confirmed ✓")

            # ── Step 6: Reopen handle for listener heartbeat ──────────────────
            ser = self._open_stm32_serial()
            if ser is None:
                print("[MCU Reconnect] Could not reopen COM port for listener")
                return False

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
        Reconnect Audio Analyzer: use the same connect_apx helper as
        initial discovery. AudioAnalyzerListener reads the global APx
        object internally, so no handle needs to be passed.
        """
        try:
            from devices.apx_analyzer import connect_apx
            found, connection = connect_apx(lambda msg, err: None)
            if found:
                self._remove_dead_listener(DeviceType.AUDIO)
                self._worker.apx_connection = connection
                self._worker.device_status["Audio Analyzer"] = True
                self._start(AudioAnalyzerListener())
                return True
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _open_stm32_serial(self):
        """
        Scan all COM ports and return a serial handle for the MCU.
        Match by VID (integer) or description keywords — no port hard-bind.
        """
        import serial
        import serial.tools.list_ports

        cfg = self.DEVICE_IDENTIFIERS["MCU"]

        for p in serial.tools.list_ports.comports():
            desc = p.description or ""

            # Hard skip — noise ports
            if any(k in desc for k in cfg["skip_keywords"]):
                continue

            # VID match (most reliable) or description keyword match
            vid_match  = (p.vid == cfg["vid"])
            desc_match = any(k in desc for k in cfg["description_keywords"])

            if not (vid_match or desc_match):
                continue

            try:
                ser = serial.Serial(p.device, cfg["baud"], timeout=1)
                if ser.isOpen():
                    return ser
            except Exception:
                continue

        return None