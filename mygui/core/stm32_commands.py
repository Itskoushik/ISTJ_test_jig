import time
import serial
import serial.tools.list_ports
import threading
# AFTER
class RelayStateTracker:
    """
    Tracks the last commanded state of every relay — binary (on/off) AND
    multi-state (S23 local/remote, S28/S31 8ohm/neutral/600ohm) — so it
    can be restored after a PSU reconnect + default-state reset.

    Keyed by relay group name (e.g. "s31", "j13"), not by the exact
    command name, so switching a multi-state relay between two non-default
    states overwrites the same slot instead of leaving stale duplicates.
    """
    _relay_states: dict = {}    # group_name -> (fname, cmd_func)  (last commanded non-default state)
    _order: list = []           # group_name, in first-seen order
    _lock = __import__("threading").Lock()

    # Suffixes that represent a relay's DEFAULT state (i.e. what
    # set_default_states() already puts it in) — no need to replay these.
    _DEFAULT_SUFFIXES = ("_off", "_neutral", "_local")
    # All recognized state suffixes, used only to derive the group name.
    _STATE_SUFFIXES = ("_on", "_off", "_local", "_remote",
                        "_8ohm", "_8ohms", "_neutral", "_600ohm", "_600ohms")

    @classmethod
    def _group_name(cls, fname: str) -> str:
        """set_j13_on -> j13, set_s31_600ohm -> s31, set_s23_remote -> s23"""
        base = fname[len("set_"):] if fname.startswith("set_") else fname
        for suffix in cls._STATE_SUFFIXES:
            if base.endswith(suffix):
                return base[: -len(suffix)]
        return base

    @classmethod
    def record_state(cls, fname: str, cmd_func):
        group = cls._group_name(fname)
        with cls._lock:
            if fname.endswith(cls._DEFAULT_SUFFIXES):
                # Relay is back at its default state — set_default_states()
                # already covers this, nothing to replay.
                cls._relay_states.pop(group, None)
                if group in cls._order:
                    cls._order.remove(group)
                return
            cls._relay_states[group] = (fname, cmd_func)
            if group not in cls._order:
                cls._order.append(group)

    @classmethod
    def clear(cls):
        with cls._lock:
            cls._relay_states.clear()
            cls._order.clear()

    @classmethod
    def restore_all(cls) -> bool:
        """
        Send set_default_states first, then re-send every relay's last
        commanded non-default state. Returns True only if every command
        succeeds.
        """
        with cls._lock:
            snapshot = [(group, *cls._relay_states[group]) for group in cls._order]

        # Step 1 — default state
        if not STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
            return False

        import time
        time.sleep(0.5)

        # Step 2 — re-apply last known state for every relay that had one
        for group, fname, cmd_func in snapshot:
            ok = STM32RelayController.send_with_retry(cmd_func)
            if not ok:
                print(f"[RELAY RESTORE] Failed to restore {group} ({fname})")
                return False
            time.sleep(0.2)

        return True
    
class STM32RelayController:
    """
    Handles STM32 relay commands (S23, S31, Jxx, etc.)
    Uses CRC-8 (poly 0x07) – SAME logic as disconnect handshake
    """

    BAUDRATE = 115200
    TIMEOUT = 2
    RECEIVE_DEADLINE = 0.5             # extra time to assemble a full 8-byte frame
    DEFAULT_RELAY_SETTLE_DELAY = 0.25   # pause after each successful default-state relay
    _bus_lock = threading.Lock()       # serializes ALL STM32 serial transactions

    # ── Relay-failure escalation state (Problems 1 & 4) ──
    _active_screen = None
    _relay_error_active = False

    @classmethod
    def register_screen(cls, screen):
        cls._active_screen = screen

    @classmethod
    def reset_relay_error_state(cls):
        cls._relay_error_active = False

    # ─── CRC-8 ────────────────────────────────────────────────────────────────
    @staticmethod
    def crc8(data) -> int:
        crc = 0x00
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = ((crc << 1) ^ 0x07) & 0xFF if (crc & 0x80) else (crc << 1) & 0xFF
        return crc

    # ─── Port scanner ─────────────────────────────────────────────────────────
    @classmethod
    def _get_stm32_ports(cls):
        ports = []
        for p in serial.tools.list_ports.comports():
            desc = p.description or ""
            if any(k in desc for k in ["Bluetooth", "Wireless", "Intel", "Modem"]):
                continue
            if (p.vid == 0x0483 or
                    "STM32"      in desc or
                    "ST-Link"    in desc or
                    "USB Serial" in desc):
                ports.append(p)
        return ports

    # ─── Robust frame receiver ──────────────────────────────────────────────
    @classmethod
    def _read_exact_frame(cls, ser, expected_length: int = 8) -> bytes:
        """
        Accumulate bytes from `ser` until exactly `expected_length` bytes have
        been received or the receive deadline expires.

        Tolerates an initial empty read and multi-chunk (partial) reads.
        Returns whatever was collected — 0, partial, or `expected_length`
        bytes — never raises on timeout. b'' is never treated as success by
        any caller.
        """
        buffer = bytearray()
        deadline = time.monotonic() + cls.RECEIVE_DEADLINE

        while len(buffer) < expected_length and time.monotonic() < deadline:
            chunk = ser.read(expected_length - len(buffer))
            if chunk:
                buffer.extend(chunk)
            else:
                time.sleep(0.02)

        return bytes(buffer)

    # ─── Core send + validate ─────────────────────────────────────────────────
    @classmethod
    def send_and_validate(cls, cmd_byte: int, tx_state: int,
                          expected_rx_state: int | None = None,
                          _conn=None) -> bool:
        """
        Build and send an 8-byte command frame, then validate the 8-byte reply.

        TX frame : 02 35 02 CMD TX_STATE CRC 03 0D
        RX frame : 02 07 02 CMD RX_STATE CRC 03 0D   (slave=0x07 in response)

        `_conn` is internal-use only: when set_default_states() passes an
        already-open serial.Serial, it's reused instead of opening/closing a
        fresh connection for this one command. Do not pass this from
        outside the class — every set_jXX_on/off()-style call keeps calling
        this with only (cmd_byte, tx_state), unaffected.
        """
        if expected_rx_state is None:
            expected_rx_state = tx_state

        body = [0x02, 0x35, 0x02, cmd_byte, tx_state, 0x03, 0x0D]
        body.insert(5, cls.crc8(body))
        tx = bytearray(body)

        def _validate(rx: bytes) -> bool:
            start, slave, length, rc, rst, rcrc, end, eof = rx
            if (start != 0x02 or slave != 0x07 or length != 0x02 or
                    rc != cmd_byte or rst != expected_rx_state or
                    end != 0x03 or eof != 0x0D):
                print(f"[RELAY RX] Invalid frame for CMD=0x{cmd_byte:02X}: {rx.hex(' ')}")
                return False
            if cls.crc8([start, slave, length, rc, rst, end, eof]) != rcrc:
                print(f"[RELAY RX] CRC failure for CMD=0x{cmd_byte:02X}: {rx.hex(' ')}")
                return False
            return True

        with cls._bus_lock:
            # ── Persistent-connection path (used by set_default_states) ──
            if _conn is not None:
                try:
                    _conn.reset_input_buffer()
                    _conn.write(tx)
                    time.sleep(0.2)
                    rx = cls._read_exact_frame(_conn, 8)
                except Exception as e:
                    print(f"[RELAY RX] Shared connection error for CMD=0x{cmd_byte:02X}: {e}")
                    return False

                if len(rx) == 0:
                    print(f"[RELAY RX] Empty response for CMD=0x{cmd_byte:02X} STATE=0x{tx_state:02X}")
                    return False
                if len(rx) != 8:
                    print(f"[RELAY RX] Partial response for CMD=0x{cmd_byte:02X}: "
                          f"received {len(rx)}/8 bytes: {rx.hex(' ')}")
                    return False
                return _validate(rx)

            # ── Legacy path: open/close per command (unchanged externally) ──
            for port in cls._get_stm32_ports():
                try:
                    ser = serial.Serial(port.device, cls.BAUDRATE, timeout=cls.TIMEOUT)
                    try:
                        ser.reset_input_buffer()
                        ser.write(tx)
                        time.sleep(0.3)
                        rx = cls._read_exact_frame(ser, 8)
                    finally:
                        ser.close()

                    if len(rx) == 0:
                        print(f"[RELAY RX] Empty response for CMD=0x{cmd_byte:02X} STATE=0x{tx_state:02X}")
                        continue
                    if len(rx) != 8:
                        print(f"[RELAY RX] Partial response for CMD=0x{cmd_byte:02X}: "
                              f"received {len(rx)}/8 bytes: {rx.hex(' ')}")
                        continue

                    if _validate(rx):
                        return True
                    continue

                except Exception:
                    continue

            return False

    # ─── Retry helper ─────────────────────────────────────────────────────────
    # (unchanged — send_with_retry, _psu_seems_down, _prompt_psu_recovery_or_abort,
    #  _handle_relay_command_failure, _prompt_retry_or_abort, _escalate all stay
    #  exactly as in the original file)

    @classmethod
    def set_default_states(cls) -> bool:

        relay_off_commands = [
        # ── Priority group: turn these off FIRST ──
        ("J29", 0x2D), ("J26", 0x2A), ("J23", 0x27),
        ("J18", 0x22), ("J19", 0x23), ("J20", 0x24), ("J21", 0x25), ("J22", 0x26),
        ("J07", 0x17), ("J08", 0x18), ("J09", 0x19), ("J10", 0x1A), ("J11", 0x1B),
        ("J27", 0x2B), ("J24", 0x28),
        ("S01", 0x60), ("S02", 0x61), ("S03", 0x62), ("S04", 0x63),
        ("S05", 0x64), ("S06", 0x65), ("S07", 0x66), ("S08", 0x67),
        ("S09", 0x68), ("S10", 0x69), ("S11", 0x6A), ("S12", 0x6B),
        ("S13", 0x6C), ("S14", 0x6D), ("S15", 0x6E), ("S16", 0x6F),
        ("S17", 0x70), ("S18", 0x71), ("S19", 0x72),

        # ── Remaining relays ──
        ("S21", 0x74), ("S22", 0x75), ("S23", 0x76), ("S24", 0x77), ("S25", 0x78),
        ("S26", 0x79), ("S27", 0x7A), ("S28", 0x7B), ("S29", 0x7C),
        ("S30", 0x7D), ("S31", 0x7E), ("S32", 0x7F), ("S33", 0x80),
        ("S34", 0x81), ("S35", 0x82), ("S36", 0x83),
        ("J12", 0x1C), ("J13", 0x1D), ("J14", 0x1E), ("J15", 0x1F),
        ("J16", 0x20), ("J30", 0x2E), ("J31", 0x2F), ("J32", 0x30),
        ("J33", 0x31), ("J34", 0x32), ("J35", 0x33), ("J36", 0x34),
        ("J37", 0x35), ("J38", 0x36), ("J39", 0x37), ("J40", 0x38),
        ("J41", 0x39), ("J42", 0x3A), ("J43", 0x3B), ("J44", 0x3C),
        ("J45", 0x3D), ("J46", 0x3E), ("J47", 0x3F), ("J48", 0x40),
        ("J49", 0x41), ("J50", 0x42), ("J51", 0x43), ("J52", 0x44),
        ("J53", 0x45), ("J54", 0x46),
        ("J67", 0x53), ("J68", 0x54),
        ("J70", 0x56), ("J71", 0x57),
    ]

        ports = cls._get_stm32_ports()
        if not ports:
            print("[DEFAULT STATE] No STM32 port found for relay reset")
            return False

        # NOTE: Reverted the "persistent shared connection + pause listeners"
        # approach. That pattern held one COM-port handle open continuously
        # for the whole ~90-command sweep and paused the PSU/oscilloscope
        # listeners around it. On this system's USB chipset (shared internal
        # hub, fewer independent controllers than a normal desktop), holding
        # the port open that long while suspending sibling VISA polling was
        # destabilizing the PSU/scope connections — they came back as
        # "disconnected" right after every relay reset. Reverting to
        # per-command open/close (each relay command opens the COM port,
        # writes, reads, and closes immediately) matches the version that
        # was proven stable on this hardware, and the PSU/scope listeners
        # are left running throughout instead of being paused.
        failed = []
        consecutive_fail_count = 0
        RELAY_RETRIES = 3   # per-relay retries — one flaky send shouldn't count as a failure

        for name, cmd in relay_off_commands:
            relay_ok = False
            for attempt in range(1, RELAY_RETRIES + 1):
                if cls.send_and_validate(cmd, 0x00):   # no _conn — opens/closes per call
                    relay_ok = True
                    break
                if attempt < RELAY_RETRIES:
                    time.sleep(0.25)

            if relay_ok:
                if consecutive_fail_count:
                    print(f"[DEFAULT STATE] {name} → OFF ✓ (recovered after {consecutive_fail_count} prior failures)")
                else:
                    print(f"[DEFAULT STATE] {name} → OFF ✓")
                consecutive_fail_count = 0
                time.sleep(cls.DEFAULT_RELAY_SETTLE_DELAY)  # let the bus settle
            else:
                failed.append(name)
                consecutive_fail_count += 1
                print(
                    f"[DEFAULT STATE] {name} failed after {RELAY_RETRIES} attempts "
                    f"({consecutive_fail_count} consecutive real failures)"
                )

                if consecutive_fail_count >= 5:
                    print(
                        "[DEFAULT STATE] 5 relays failed consecutively even after "
                        "individual retries — this is USB/comms corruption, not a "
                        "one-off blip. Stopping sweep and escalating."
                    )
                    cls._escalate(
                        title="⚠ Relay Communication Failure",
                        message=(
                            "Relay communication has repeatedly failed.\n\n"
                            "Possible causes:\n"
                            "• ISTJ entered Bad Authentication mode.\n"
                            "• USB communication corruption.\n\n"
                            "Recommended Action:\n"
                            "Abort the current test.\n"
                            "Reconnect the ISTJ.\n"
                            "Reconnect the USB cable.\n"
                            "Restart the application."
                        ),
                    )
                    return False

        if failed:
            print(f"[DEFAULT STATE] Completed with failures: {failed}")
            return False

        print("[DEFAULT STATE] All relays OFF ✓")
        return True
    # ─── Retry helper ─────────────────────────────────────────────────────────
    @classmethod
    def send_with_retry(cls, cmd_func, retries: int = 3) -> bool:
        while True:
            success = False
            for _ in range(retries):
                if cmd_func():
                    success = True
                    break
                time.sleep(0.3)

            fname = getattr(cmd_func, "__name__", "") if callable(cmd_func) else ""
            # AFTER
            # ── Auto-track relay state for PSU-reconnect restore ──
            # (covers binary on/off relays AND multi-state relays like
            # S23 local/remote, S28/S31 8ohm/neutral/600ohm)
            try:
                if fname.startswith("set_") and fname != "set_default_states" and success:
                    RelayStateTracker.record_state(fname, cmd_func)
            except Exception:
                pass

            # ── PROBLEM 1: handled inline inside set_default_states() itself —
            # it retries each relay individually, counts CONSECUTIVE relays that
            # still fail after exhausting their own retries, and escalates
            # immediately at 5. Nothing to do here for that case — this branch
            # would otherwise wait for 5 separate send_with_retry(set_default_states)
            # calls to fail, which never happens in practice (one call already
            # does the full sweep).

            # ── PROBLEM 4: every other relay command (1 failure is enough) ──
            if fname.startswith("set_") and fname != "set_default_states" and not success:
                screen = cls._active_screen

                if cls._psu_seems_down(screen):
                    # Relay failed AND PSU looks unreachable — most likely
                    # cause is the PSU being off/power-cycled, not a relay
                    # bus fault. Offer PSU recovery instead of the generic
                    # relay-failure popup.
                    choice = cls._prompt_psu_recovery_or_abort(fname)
                else:
                    # PSU confirmed alive — genuine relay-comms issue.
                    choice = cls._handle_relay_command_failure()

                if choice == "retry":
                    if screen is not None:
                        screen.log_signal.emit(f"🔁 Retrying {fname}…", False)
                    continue  # re-attempt cmd_func from scratch, same as a fresh call

                if screen is not None:
                    screen._skip_relay_reset_on_abort = True
                    screen.abort_event.set()
                raise Exception("TEST_ABORTED_BY_USER")

            return success

    @classmethod
    def _psu_seems_down(cls, screen) -> bool:
        """
        Best-effort check for whether the PSU looks unreachable right now.
        Does NOT trigger a reconnect itself — just answers the question so
        send_with_retry can pick the right popup. Treats "PSU already known
        to be down/recovering" as down without re-querying it.
        """
        if screen is None:
            return False
        if getattr(screen, "_psu_error_handled", False) or not screen._psu_ready_event.is_set():
            return True  # already flagged down or a recovery is already in progress
        if not getattr(screen, "psu_inst", None):
            return True  # no PSU handle at all
        try:
            with screen.psu_lock:
                screen.psu_inst.query("*IDN?")
            return False  # PSU answered — it's alive
        except Exception:
            return True

    @classmethod
    def _prompt_psu_recovery_or_abort(cls, fname: str) -> str:
        """
        Relay command failed AND the PSU appears unreachable. Pause the test
        and ask the operator to either continue with PSU recovery or abort.
        Recovery does not start a second reconnect thread — the PSU listener
        already detects the disconnect independently and drives
        _background_reconnect() on its own; we just wait on the same event
        it clears/sets, with a defensive fallback only if recovery somehow
        hasn't started yet.
        """
        screen = cls._active_screen
        if screen is None:
            print("[RELAY WRAPPER] ❌ PSU-related relay failure but no screen registered — defaulting to abort.")
            return "abort"

        if getattr(screen, "_relay_error_active", False):
            print("[RELAY WRAPPER] Escalation already active — suppressing duplicate popup.")
            return "abort"

        screen._relay_error_active = True
        screen._skip_relay_reset_on_abort = True
        screen._psu_ready_event.clear()  # pause test immediately, same gate as PSU-listener recovery

        ack_event = threading.Event()
        choice = {"value": "abort"}

        from PyQt5.QtWidgets import QDialog

        def _on_result(result, popup):
            choice["value"] = "recover" if result == QDialog.Accepted else "abort"
            ack_event.set()

        try:
            screen._queue_popup(
                "⚠ Relay Failed — PSU Unreachable",
                f"The relay command ({fname}) failed, and the PSU could not be reached.\n\n"
                "This usually means:\n"
                "  • The PSU has been turned OFF\n"
                "  • A power fluctuation or cable disconnect occurred\n\n"
                "Click YES to recover the PSU and resume the test automatically,\n"
                "or NO to abort the test.",
                None, "yes_no", None,
                callback=_on_result,
            )
        except Exception as e:
            print(f"[RELAY WRAPPER] Failed to queue popup: {e}")
            ack_event.set()

        # after
        deadline = time.time() + 600
        while time.time() < deadline:
            if ack_event.wait(timeout=0.5):
                break
            if screen.abort_event.is_set():
                print("[RELAY WRAPPER] Abort already in progress — skipping popup wait.")
                break
        screen._relay_error_active = False

        if choice["value"] != "recover":
            return "abort"

        # Defensive-only fallback: nudge recovery ourselves only if the PSU
        # listener hasn't already started it (event still set = nothing has
        # paused the test yet).
        if not getattr(screen, "_reconnect_in_progress", False) and screen._psu_ready_event.is_set():
            screen._psu_error_handled = True
            threading.Thread(
                target=screen._background_reconnect,
                daemon=True,
                name="PSU-reconnect-from-relay",
            ).start()

        screen.log_signal.emit("⏸ Waiting for PSU recovery to complete before retrying relay…", True)
        screen._psu_ready_event.wait(timeout=300)

        if screen.abort_event.is_set():
            return "abort"

        screen.log_signal.emit(f"▶ PSU recovered — retrying {fname}", False)
        screen._skip_relay_reset_on_abort = False
        return "retry"

    @classmethod
    def _handle_relay_command_failure(cls) -> str:
        """Returns 'retry' or 'abort' — does not raise itself."""
        return cls._prompt_retry_or_abort(
            title="⚠ Relay Communication Failure",
            message=(
                "Relay communication failed.\n\n"
                "Possible causes:\n"
                "USB communication issue.\n"
                "Bad relay connection.\n"
                "STM32 communication failure."
            ),
        )

    @classmethod
    def _prompt_retry_or_abort(cls, title: str, message: str) -> str:
        """
        Pure relay-comms failure (PSU confirmed alive). Pause the test on the
        same event check_abort() waits on, ask the operator to retry the
        failed relay command or abort. Returns 'retry' / 'abort' and never
        raises — the caller decides what to do with the answer.
        """
        screen = cls._active_screen
        if screen is None:
            print(
                "[RELAY WRAPPER] ❌ Escalation triggered but no screen is "
                "registered — cannot pause/prompt. Defaulting to abort."
            )
            return "abort"

        if getattr(screen, "_relay_error_active", False):
            print("[RELAY WRAPPER] Escalation already active — suppressing duplicate popup.")
            return "abort"

        screen._relay_error_active = True
        screen._skip_relay_reset_on_abort = True
        screen._psu_ready_event.clear()  # pause: check_abort() will block here

        ack_event = threading.Event()
        choice = {"value": "abort"}

        from PyQt5.QtWidgets import QDialog

        def _on_result(result, popup):
            choice["value"] = "retry" if result == QDialog.Accepted else "abort"
            ack_event.set()

        try:
            screen._queue_popup(
                title,
                message + "\n\nClick YES to retry this relay command, NO to abort the test.",
                None, "yes_no", None,
                callback=_on_result,
            )
        except Exception as e:
            print(f"[RELAY WRAPPER] Failed to queue popup: {e}")
            ack_event.set()

        # after
        deadline = time.time() + 600
        while time.time() < deadline:
            if ack_event.wait(timeout=0.5):
                break
            if screen.abort_event.is_set():
                print("[RELAY WRAPPER] Abort already in progress — skipping popup wait.")
                break
        screen._relay_error_active = False
        if choice["value"] == "retry":
            screen._skip_relay_reset_on_abort = False  # comms just proved to work again

        screen._psu_ready_event.set()  # always unblock check_abort() before returning
        return choice["value"]

    @classmethod
    def _escalate(cls, title: str, message: str):
        """
        Shared escalation path for Problems 1 & 4:
        pause the test, show the existing OperatorInfoPopup (via the screen's
        existing thread-safe popup queue), then stop test progression.
        Since relay comms are already failing, cleanup on abort must skip
        set_default_states() — flagged via _skip_relay_reset_on_abort.
        """
        screen = cls._active_screen
        if screen is None:
            # Loud on purpose — a silent return here means an operator never
            # sees a real hardware failure. If you see this in the console,
            # register_screen() was never called for the screen that's
            # actually running this test (check that start_test() on that
            # specific screen calls STM32RelayController.register_screen(self)).
            print(
                "[RELAY WRAPPER] ❌ Escalation triggered but no screen is "
                "registered — popup CANNOT be shown. Call "
                "STM32RelayController.register_screen(self) from this "
                "screen's start_test()."
            )
            return
        if getattr(screen, "_relay_error_active", False):
            print("[RELAY WRAPPER] Escalation already active — suppressing duplicate popup.")
            return  # already paused / already showing a popup for this failure

        screen._relay_error_active = True
        screen._skip_relay_reset_on_abort = True

        # after
        ack_event = threading.Event()

        def _on_ok(result, popup):
            ack_event.set()

        try:
            screen._queue_popup(title, message, None, "ok", None, callback=_on_ok)
        except Exception as e:
            print(f"[RELAY WRAPPER] Failed to queue popup: {e}")
            ack_event.set()

        # Poll instead of a flat 600s wait — bail immediately if the screen is
        # already aborting (e.g. Force Close), so we never block the shutdown
        # path waiting for a popup click that will never come.
        deadline = time.time() + 600
        while time.time() < deadline:
            if ack_event.wait(timeout=0.5):
                break
            if screen.abort_event.is_set():
                print("[RELAY WRAPPER] Abort already in progress — skipping popup wait.")
                break

        raise Exception("TEST_ABORTED_BY_USER")

    # ======================
    # S23 (LOCAL / REMOTE)
    # CMD = 0x76
    # ======================
    @classmethod
    def set_s23_local(cls):
        return cls.send_and_validate(0x76, 0x00)

    @classmethod
    def set_s23_remote(cls):
        return cls.send_and_validate(0x76, 0x01)

    # ======================
    # S31 (LOAD)
    # CMD = 0x7E
    # ======================
    @classmethod
    def set_s31_8ohm(cls):
        return cls.send_and_validate(0x7E, 0x01)

    @classmethod
    def set_s31_neutral(cls):
        return cls.send_and_validate(0x7E, 0x00)

    @classmethod
    def set_s31_600ohm(cls):
        return cls.send_and_validate(0x7E, 0x02)
    
        # ======================
    # J13
    # CMD = 0x1D
    # ======================
    @classmethod
    def set_j13_off(cls):
        return cls.send_and_validate(0x1D, 0x00)

    @classmethod
    def set_j13_on(cls):
        return cls.send_and_validate(0x1D, 0x01)

    # ======================
    # J14
    # CMD = 0x1E
    # ======================
    @classmethod
    def set_j14_off(cls):
        return cls.send_and_validate(0x1E, 0x00)

    @classmethod
    def set_j14_on(cls):
        return cls.send_and_validate(0x1E, 0x01)

    # ======================
    # J15
    # CMD = 0x1F
    # ======================
    @classmethod
    def set_j15_off(cls):
        return cls.send_and_validate(0x1F, 0x00)

    @classmethod
    def set_j15_on(cls):
        return cls.send_and_validate(0x1F, 0x01)

    # ======================
    # J16
    # CMD = 0x20
    # ======================
    @classmethod
    def set_j16_off(cls):
        return cls.send_and_validate(0x20, 0x00)

    @classmethod
    def set_j16_on(cls):
        return cls.send_and_validate(0x20, 0x01)

    # # ======================
    # # J28
    # # CMD = 0x2C
    # # ======================
    # @classmethod
    # def set_j28_off(cls):
    #     return cls.send_and_validate(0x2C, 0x00)

    # @classmethod
    # def set_j28_on(cls):
    #     return cls.send_and_validate(0x2C, 0x01)

    # ======================
    # J29
    # CMD = 0x2D
    # ======================
    @classmethod
    def set_j29_off(cls):
        return cls.send_and_validate(0x2D, 0x00)

    @classmethod
    def set_j29_on(cls):
        return cls.send_and_validate(0x2D, 0x01)

    # ======================
    # S25
    # CMD = 0x78
    # ======================
    @classmethod
    def set_s25_off(cls):
        return cls.send_and_validate(0x78, 0x00)

    @classmethod
    def set_s25_on(cls):
        return cls.send_and_validate(0x78, 0x01)

    # ======================
    # S30
    # CMD = 0x7D
    # ======================
    @classmethod
    def set_s30_off(cls):
        return cls.send_and_validate(0x7D, 0x00)

    @classmethod
    def set_s30_on(cls):
        return cls.send_and_validate(0x7D, 0x01)

    # ======================
    # S32
    # CMD = 0x7F
    # ======================
    @classmethod
    def set_s32_off(cls):
        return cls.send_and_validate(0x7F, 0x00)

    @classmethod
    def set_s32_on(cls):
        return cls.send_and_validate(0x7F, 0x01)

    # ======================
    # J27
    # CMD = 0x2B
    # ======================
    @classmethod
    def set_j27_off(cls):
        return cls.send_and_validate(0x2B, 0x00)

    @classmethod
    def set_j27_on(cls):
        return cls.send_and_validate(0x2B, 0x01)

    # ======================
    # S24
    # CMD = 0x77
    # ======================
    @classmethod
    def set_s24_off(cls):
        return cls.send_and_validate(0x77, 0x00)

    @classmethod
    def set_s24_on(cls):
        return cls.send_and_validate(0x77, 0x01)
    
    # ======================
    # J30
    # CMD = 0x2E
    # ======================
    @classmethod
    def set_j30_off(cls):
        return cls.send_and_validate(0x2E, 0x00)
    @classmethod
    def set_j30_on(cls):
        return cls.send_and_validate(0x2E, 0x01)


    # ======================
    # J31
    # CMD = 0x2F
    # ======================
    @classmethod
    def set_j31_off(cls):
        return cls.send_and_validate(0x2F, 0x00)

    @classmethod
    def set_j31_on(cls):
        return cls.send_and_validate(0x2F, 0x01)

    # ======================
    # J32
    # CMD = 0x30
    # ======================
    @classmethod
    def set_j32_off(cls):
        return cls.send_and_validate(0x30, 0x00)
    @classmethod
    def set_j32_on(cls):
        return cls.send_and_validate(0x30, 0x01)


    # ======================
    # J33
    # CMD = 0x31
    # ======================
    @classmethod
    def set_j33_off(cls):
        return cls.send_and_validate(0x31, 0x00)

    @classmethod
    def set_j33_on(cls):
        return cls.send_and_validate(0x31, 0x01)

    # ======================
    # J34
    # CMD = 0x32
    # ======================
    @classmethod
    def set_j34_off(cls):
        return cls.send_and_validate(0x32, 0x00)
    @classmethod
    def set_j34_on(cls):
        return cls.send_and_validate(0x32, 0x01)


    # ======================
    # J36
    # CMD = 0x34
    # ======================
    @classmethod
    def set_j36_off(cls):
        return cls.send_and_validate(0x34, 0x00)
    @classmethod
    def set_j36_on(cls):
        return cls.send_and_validate(0x34, 0x01)
    
    # ======================
    # J37
    # CMD = 0x35
    # ======================
    @classmethod
    def set_j37_off(cls):
        return cls.send_and_validate(0x35, 0x00)
    @classmethod
    def set_j37_on(cls):
        return cls.send_and_validate(0x35, 0x01)


    # ======================
    # J38
    # CMD = 0x36
    # ======================
    @classmethod
    def set_j38_off(cls):
        return cls.send_and_validate(0x36, 0x00)

    @classmethod
    def set_j38_on(cls):
        return cls.send_and_validate(0x36, 0x01)

    # ======================
    # J39
    # CMD = 0x37
    # ======================
    @classmethod
    def set_j39_off(cls):
        return cls.send_and_validate(0x37, 0x00)
    @classmethod
    def set_j39_on(cls):
        return cls.send_and_validate(0x37, 0x01)


    # ======================
    # J40
    # CMD = 0x38
    # ======================
    @classmethod
    def set_j40_off(cls):
        return cls.send_and_validate(0x38, 0x00)
    @classmethod
    def set_j40_on(cls):
        return cls.send_and_validate(0x38, 0x01)


    # ======================
    # J41
    # CMD = 0x39
    # ======================
    @classmethod
    def set_j41_off(cls):
        return cls.send_and_validate(0x39, 0x00)
    @classmethod
    def set_j41_on(cls):
        return cls.send_and_validate(0x39, 0x01)


    # ======================
    # J42
    # CMD = 0x3A
    # ======================
    @classmethod
    def set_j42_off(cls):
        return cls.send_and_validate(0x3A, 0x00)
    @classmethod
    def set_j42_on(cls):
        return cls.send_and_validate(0x3A, 0x01)
    
    # ======================
    # J43
    # CMD = 0x3B
    # ======================
    @classmethod
    def set_j43_off(cls):
        return cls.send_and_validate(0x3B, 0x00)
    @classmethod
    def set_j43_on(cls):
        return cls.send_and_validate(0x3B, 0x01)
    
    # ======================
    # J44
    # CMD = 0x3C
    # ======================
    @classmethod
    def set_j44_off(cls):
        return cls.send_and_validate(0x3C, 0x00)
    @classmethod
    def set_j44_on(cls):
        return cls.send_and_validate(0x3C, 0x01)
    
    # ======================
    # J45
    # CMD = 0x3D
    # ======================
    @classmethod
    def set_j45_off(cls):
        return cls.send_and_validate(0x3D, 0x00)
    @classmethod
    def set_j45_on(cls):
        return cls.send_and_validate(0x3D, 0x01)
    
    # ======================
    # J46
    # CMD = 0x3E
    # ======================
    @classmethod
    def set_j46_off(cls):
        return cls.send_and_validate(0x3E, 0x00)
    @classmethod
    def set_j46_on(cls):
        return cls.send_and_validate(0x3E, 0x01)
    
    # ======================
    # J47
    # CMD = 0x3F
    # ======================
    @classmethod
    def set_j47_off(cls):
        return cls.send_and_validate(0x3F, 0x00)
    @classmethod
    def set_j47_on(cls):
        return cls.send_and_validate(0x3F, 0x01)
    
    # ======================
    # J48
    # CMD = 0x40
    # ======================
    @classmethod
    def set_j48_off(cls):
        return cls.send_and_validate(0x40, 0x00)
    @classmethod
    def set_j48_on(cls):
        return cls.send_and_validate(0x40, 0x01)
    
    
    
    
    # ======================
    # J49
    # CMD = 0x41
    # ======================
    @classmethod
    def set_j49_off(cls):
        return cls.send_and_validate(0x41, 0x00)

    @classmethod
    def set_j49_on(cls):
        return cls.send_and_validate(0x41, 0x01)

    # ======================
    # J51
    # CMD = 0x43
    # ======================
    @classmethod
    def set_j51_off(cls):
        return cls.send_and_validate(0x43, 0x00)

    @classmethod
    def set_j51_on(cls):
        return cls.send_and_validate(0x43, 0x01)

    # ======================
    # J52
    # CMD = 0x44
    # ======================
    @classmethod
    def set_j52_off(cls):
        return cls.send_and_validate(0x44, 0x00)
    @classmethod
    def set_j52_on(cls):
        return cls.send_and_validate(0x44, 0x01)


    # ======================
    # J53
    # CMD = 0x45
    # ======================
    @classmethod
    def set_j53_off(cls):
        return cls.send_and_validate(0x45, 0x00)
    @classmethod
    def set_j53_on(cls):
        return cls.send_and_validate(0x45, 0x01)


    # ======================
    # J54
    # CMD = 0x46
    # ======================
    @classmethod
    def set_j54_off(cls):
        return cls.send_and_validate(0x46, 0x00)
    @classmethod
    def set_j54_on(cls):
        return cls.send_and_validate(0x46, 0x01)
    
    # ======================
    # S26
    # CMD = 0x79
    # ======================
    @classmethod
    def set_s26_off(cls):
        return cls.send_and_validate(0x79, 0x00)

    @classmethod
    def set_s26_on(cls):
        return cls.send_and_validate(0x79, 0x01)


    # ======================
    # S33
    # CMD = 0x80
    # ======================
    @classmethod
    def set_s33_off(cls):
        return cls.send_and_validate(0x80, 0x00)

    @classmethod
    def set_s33_on(cls):
        return cls.send_and_validate(0x80, 0x01)


    # ======================
    # S34
    # CMD = 0x81
    # ======================
    @classmethod
    def set_s34_off(cls):
        return cls.send_and_validate(0x81, 0x00)

    @classmethod
    def set_s34_on(cls):
        return cls.send_and_validate(0x81, 0x01)
    
    # =========================================================================
    # HANDSHAKE / SYSTEM
    # =========================================================================
 
    # Sync   TX: 02 35 02 FF 00 98 03 0D   RX: 02 35 02 FF 01 F3 03 0D
    @classmethod
    def sync(cls) -> bool:
        tx = bytearray([0x02, 0x35, 0x02, 0xFF, 0x00, 0x98, 0x03, 0x0D])
        return cls._send_raw_and_check(tx, expected_cmd=0xFF, expected_state=0x01)
 
    # Unsync TX: 02 35 02 FF E0 56 03 0D   RX: 02 35 02 FF E1 3D 03 0D
    @classmethod
    def unsync(cls) -> bool:
        tx = bytearray([0x02, 0x35, 0x02, 0xFF, 0xE0, 0x56, 0x03, 0x0D])
        return cls._send_raw_and_check(tx, expected_cmd=0xFF, expected_state=0xE1)
 
    # @classmethod
    # def set_default_states(cls) -> bool:

    #     relay_off_commands = [
    #     # ── Priority group: turn these off FIRST ──
    #     ("J29", 0x2D), ("J26", 0x2A), ("J23", 0x27),
    #     ("J18", 0x22), ("J19", 0x23), ("J20", 0x24), ("J21", 0x25), ("J22", 0x26),
    #     ("J07", 0x17), ("J08", 0x18), ("J09", 0x19), ("J10", 0x1A), ("J11", 0x1B),
    #     ("J27", 0x2B), ("J24", 0x28),
    #     ("S01", 0x60), ("S02", 0x61), ("S03", 0x62), ("S04", 0x63),
    #     ("S05", 0x64), ("S06", 0x65), ("S07", 0x66), ("S08", 0x67),
    #     ("S09", 0x68), ("S10", 0x69), ("S11", 0x6A), ("S12", 0x6B),
    #     ("S13", 0x6C), ("S14", 0x6D), ("S15", 0x6E), ("S16", 0x6F),
    #     ("S17", 0x70), ("S18", 0x71), ("S19", 0x72),

    #     # ── Remaining relays ──
    #     ("S21", 0x74), ("S22", 0x75), ("S23", 0x76), ("S24", 0x77), ("S25", 0x78),
    #     ("S26", 0x79), ("S27", 0x7A), ("S28", 0x7B), ("S29", 0x7C),
    #     ("S30", 0x7D), ("S31", 0x7E), ("S32", 0x7F), ("S33", 0x80),
    #     ("S34", 0x81), ("S35", 0x82), ("S36", 0x83),
    #     ("J12", 0x1C), ("J13", 0x1D), ("J14", 0x1E), ("J15", 0x1F),
    #     ("J16", 0x20), ("J30", 0x2E), ("J31", 0x2F), ("J32", 0x30),
    #     ("J33", 0x31), ("J34", 0x32), ("J35", 0x33), ("J36", 0x34),
    #     ("J37", 0x35), ("J38", 0x36), ("J39", 0x37), ("J40", 0x38),
    #     ("J41", 0x39), ("J42", 0x3A), ("J43", 0x3B), ("J44", 0x3C),
    #     ("J45", 0x3D), ("J46", 0x3E), ("J47", 0x3F), ("J48", 0x40),
    #     ("J49", 0x41), ("J50", 0x42), ("J51", 0x43), ("J52", 0x44),
    #     ("J53", 0x45), ("J54", 0x46),
    #     ("J67", 0x53), ("J68", 0x54),
    #     ("J70", 0x56), ("J71", 0x57),
    # ]
 
    #     if not cls._get_stm32_ports():
    #         print("[DEFAULT STATE] No STM32 port found for relay reset")
    #         return False

    #     failed = []
    #     consecutive_fail_count = 0
    #     RELAY_RETRIES = 3   # per-relay retries — one flaky send shouldn't count as a failure

    #     for name, cmd in relay_off_commands:
    #         relay_ok = False
    #         for attempt in range(1, RELAY_RETRIES + 1):
    #             if cls.send_and_validate(cmd, 0x00):
    #                 relay_ok = True
    #                 break
    #             if attempt < RELAY_RETRIES:
    #                 time.sleep(0.15)

    #         if relay_ok:
    #             if consecutive_fail_count:
    #                 print(f"[DEFAULT STATE] {name} → OFF ✓ (recovered after {consecutive_fail_count} prior failures)")
    #             else:
    #                 print(f"[DEFAULT STATE] {name} → OFF ✓")
    #             consecutive_fail_count = 0
    #         else:
    #             # Only counts as a real failure once its own retries are exhausted
    #             failed.append(name)
    #             consecutive_fail_count += 1
    #             print(
    #                 f"[DEFAULT STATE] {name} failed after {RELAY_RETRIES} attempts "
    #                 f"({consecutive_fail_count} consecutive real failures)"
    #             )

    #             if consecutive_fail_count >= 5:
    #                 print(
    #                     "[DEFAULT STATE] 5 relays failed consecutively even after "
    #                     "individual retries — this is USB/comms corruption, not a "
    #                     "one-off blip. Stopping sweep and escalating."
    #                 )
    #                 cls._escalate(
    #                     title="⚠ Relay Communication Failure",
    #                     message=(
    #                         "Relay communication has repeatedly failed.\n\n"
    #                         "Possible causes:\n"
    #                         "• ISTJ entered Bad Authentication mode.\n"
    #                         "• USB communication corruption.\n\n"
    #                         "Recommended Action:\n"
    #                         "Abort the current test.\n"
    #                         "Reconnect the ISTJ.\n"
    #                         "Reconnect the USB cable.\n"
    #                         "Restart the application."
    #                     ),
    #                 )
    #                 # _escalate() raises TEST_ABORTED_BY_USER — this return
    #                 # is only reached if that call somehow returns normally.
    #                 return False

    #     if failed:
    #         print(f"[DEFAULT STATE] Completed with failures: {failed}")
    #         return False

    #     print("[DEFAULT STATE] All relays OFF ✓")
    #     return True
    #=======================
    #Junction Box ALH4
    #=======================
    
    #=======================
    # J07
    # CMD = 0x17
    #=======================

    @classmethod
    def set_j07_off(cls):
        return cls.send_and_validate(0x17,0x00)

    @classmethod
    def set_j07_on(cls):
        return cls.send_and_validate(0x17,0x01)
    
    #=======================
    # J08
    # CMD = 0x18
    #=======================

    @classmethod
    def set_j08_off(cls):
        return cls.send_and_validate(0x18,0x00)

    @classmethod
    def set_j08_on(cls):
        return cls.send_and_validate(0x18,0x01)
    
    #=======================
    # J09
    # CMD = 0x19
    #=======================

    @classmethod
    def set_j09_off(cls):
        return cls.send_and_validate(0x19,0x00)

    @classmethod
    def set_j09_on(cls):
        return cls.send_and_validate(0x19,0x01)
    
    #=======================
    # J10
    # CMD = 0x1A
    #=======================

    @classmethod
    def set_j10_off(cls):
        return cls.send_and_validate(0x1A,0x00)

    @classmethod
    def set_j10_on(cls):
        return cls.send_and_validate(0x1A,0x01)
    
    #=======================
    # J11
    # CMD = 0x1B
    #=======================

    @classmethod
    def set_j11_off(cls):
        return cls.send_and_validate(0x1B,0x00)

    @classmethod
    def set_j11_on(cls):
        return cls.send_and_validate(0x1B,0x01)
    
    
    #=======================
    # J18
    # CMD = 0x22
    #=======================

    @classmethod
    def set_j18_off(cls):
        return cls.send_and_validate(0x22,0x00)

    @classmethod
    def set_j18_on(cls):
        return cls.send_and_validate(0x22,0x01)
    
    #=======================
    # J19
    # CMD = 0x23
    #=======================

    @classmethod
    def set_j19_off(cls):
        return cls.send_and_validate(0x23,0x00)

    @classmethod
    def set_j19_on(cls):
        return cls.send_and_validate(0x23,0x01)
    
    #=======================
    # J20
    # CMD = 0x24
    #=======================

    @classmethod
    def set_j20_off(cls):
        return cls.send_and_validate(0x24,0x00)

    @classmethod
    def set_j20_on(cls):
        return cls.send_and_validate(0x24,0x01)
    
    
    #=======================
    # J21
    # CMD = 0x25
    #=======================

    @classmethod
    def set_j21_off(cls):
        return cls.send_and_validate(0x25,0x00)

    @classmethod
    def set_j21_on(cls):
        return cls.send_and_validate(0x25,0x01)
    
    #=======================
    # J22
    # CMD = 0x26
    #=======================

    @classmethod
    def set_j22_off(cls):
        return cls.send_and_validate(0x26,0x00)

    @classmethod
    def set_j22_on(cls):
        return cls.send_and_validate(0x26,0x01)
    
    #=======================
    # J23
    # CMD = 0x27
    #=======================

    @classmethod
    def set_j23_off(cls):
        return cls.send_and_validate(0x27,0x00)

    @classmethod
    def set_j23_on(cls):
        return cls.send_and_validate(0x27,0x01)
    
    #=======================
    # J24
    # CMD = 0x28
    #=======================

    @classmethod
    def set_j24_off(cls):
        return cls.send_and_validate(0x28,0x00)

    @classmethod
    def set_j24_on(cls):
        return cls.send_and_validate(0x28,0x01)
    
    
    #=======================
    # J26
    # CMD = 0x2A
    #=======================

    @classmethod
    def set_j26_off(cls):
        return cls.send_and_validate(0x2A,0x00)

    @classmethod
    def set_j26_on(cls):
        return cls.send_and_validate(0x2A,0x01)
    
    
    # ─── Raw frame sender (SYNC / UNSYNC / DEFAULT — slave=0x35 in response) ──
    @classmethod
    def _send_raw_and_check(cls, tx: bytearray,
                             expected_cmd: int, expected_state: int) -> bool:
        for port in cls._get_stm32_ports():
            try:
                with cls._bus_lock:
                    print(f"[STM32 SERIAL] {port.device} OPEN (sync/unsync)")
                    ser = serial.Serial(port.device, cls.BAUDRATE, timeout=cls.TIMEOUT)
                    ser.reset_input_buffer()
                    ser.write(tx)
                    time.sleep(0.4)
                    rx = ser.read(8)
                    ser.close()
                    print(f"[STM32 SERIAL] {port.device} CLOSED (sync/unsync)")
 
                if len(rx) != 8:
                    continue
 
                start, slave, length, rc, rst, rcrc, end, eof = rx
 
                # Handshake/system responses use slave = 0x35
                if (start  != 0x02 or
                        slave  != 0x35 or    # ← CORRECT for SYNC/UNSYNC/DEFAULT
                        length != 0x02 or
                        rc     != expected_cmd or
                        rst    != expected_state or
                        end    != 0x03 or
                        eof    != 0x0D):
                    continue
 
                if cls.crc8([start, slave, length, rc, rst, end, eof]) == rcrc:
                    return True
 
            except Exception:
                continue
 
        return False
    
    
    @classmethod
    def get_device_info(cls) -> dict | None:
        """
        Version TX: 02 35 02 BB B0 B1 03 0D
        Response  : 02 07 02 BB B1 2D 03 0D   (8-byte ACK, slave=0x07)
        Returns a dict with 'ack': True if the frame was received,
        None if no response at all (so caller can log the difference).
        """
        tx = bytearray([0x02, 0x35, 0x02, 0xBB, 0xB0, 0xB1, 0x03, 0x0D])
        for port in cls._get_stm32_ports():
            try:
                with cls._bus_lock:
                    ser = serial.Serial(port.device, cls.BAUDRATE, timeout=cls.TIMEOUT)
                    ser.reset_input_buffer()
                    ser.write(tx)
                    time.sleep(0.4)
                    rx = ser.read(8)
                    ser.close()

                if len(rx) != 8:
                    continue

                start, slave, length, rc, rst, rcrc, end, eof = rx

                if (start  != 0x02 or
                        slave  != 0x07 or
                        length != 0x02 or
                        rc     != 0xBB or
                        rst    != 0xB1 or
                        end    != 0x03 or
                        eof    != 0x0D):
                    continue

                if cls.crc8([start, slave, length, rc, rst, end, eof]) == rcrc:
                    return {"ack": True}   # ← ACK confirmed, use hardcoded details

            except Exception:
                continue
        return None   # ← no response at all


    
    #=======================
    # J67
    # CMD = 0x53
    #=======================
    @classmethod
    def set_j67_off(cls):
        return cls.send_and_validate(0x53, 0x00)

    @classmethod
    def set_j67_on(cls):
        return cls.send_and_validate(0x53, 0x01)


    #=======================
    # J68
    # CMD = 0x54
    #=======================
    @classmethod
    def set_j68_off(cls):
        return cls.send_and_validate(0x54, 0x00)

    @classmethod
    def set_j68_on(cls):
        return cls.send_and_validate(0x54, 0x01)

    # ======================
    # J12
    # CMD = 0x1C
    # ======================
    @classmethod
    def set_j12_off(cls):
        return cls.send_and_validate(0x1C, 0x00)

    @classmethod
    def set_j12_on(cls):
        return cls.send_and_validate(0x1C, 0x01)

    # ======================
    # J35
    # CMD = 0x33
    # ======================
    @classmethod
    def set_j35_off(cls):
        return cls.send_and_validate(0x33, 0x00)

    @classmethod
    def set_j35_on(cls):
        return cls.send_and_validate(0x33, 0x01)

    # ======================
    # J50
    # CMD = 0x42
    # ======================
    @classmethod
    def set_j50_off(cls):
        return cls.send_and_validate(0x42, 0x00)

    @classmethod
    def set_j50_on(cls):
        return cls.send_and_validate(0x42, 0x01)

    # ======================
    # S27
    # CMD = 0x7A
    # ======================
    @classmethod
    def set_s27_off(cls):
        return cls.send_and_validate(0x7A, 0x00)

    @classmethod
    def set_s27_on(cls):
        return cls.send_and_validate(0x7A, 0x01)

    # ======================
    # S35 / SB-SEL
    # CMD = 0x82
    # ======================
    @classmethod
    def set_s35_off(cls):
        return cls.send_and_validate(0x82, 0x00)

    @classmethod
    def set_s35_on(cls):
        return cls.send_and_validate(0x82, 0x01)
    
    
    # ======================
    # S36 / GEN-LOAD
    # CMD = 0x83
    # ======================
    @classmethod
    def set_s36_off(cls):
        return cls.send_and_validate(0x83, 0x00)

    @classmethod
    def set_s36_on(cls):
        return cls.send_and_validate(0x83, 0x01)


    #=======================
    # J70
    # CMD = 0x56
    #=======================
    @classmethod
    def set_j70_off(cls):
        return cls.send_and_validate(0x56, 0x00)

    @classmethod
    def set_j70_on(cls):
        return cls.send_and_validate(0x56, 0x01)


    #=======================
    # J71
    # CMD = 0x57
    #=======================
    @classmethod
    def set_j71_off(cls):
        return cls.send_and_validate(0x57, 0x00)

    @classmethod
    def set_j71_on(cls):
        return cls.send_and_validate(0x57, 0x01)


    #=======================
    # S01
    # CMD = 0x60
    #=======================
    @classmethod
    def set_s01_off(cls):
        return cls.send_and_validate(0x60, 0x00)

    @classmethod
    def set_s01_on(cls):
        return cls.send_and_validate(0x60, 0x01)


    #=======================
    # S02
    # CMD = 0x61
    #=======================
    @classmethod
    def set_s02_off(cls):
        return cls.send_and_validate(0x61, 0x00)

    @classmethod
    def set_s02_on(cls):
        return cls.send_and_validate(0x61, 0x01)


    #=======================
    # S03
    # CMD = 0x62
    #=======================
    @classmethod
    def set_s03_off(cls):
        return cls.send_and_validate(0x62, 0x00)

    @classmethod
    def set_s03_on(cls):
        return cls.send_and_validate(0x62, 0x01)


    #=======================
    # S04
    # CMD = 0x63
    #=======================
    @classmethod
    def set_s04_off(cls):
        return cls.send_and_validate(0x63, 0x00)

    @classmethod
    def set_s04_on(cls):
        return cls.send_and_validate(0x63, 0x01)


    #=======================
    # S05
    # CMD = 0x64
    #=======================
    @classmethod
    def set_s05_off(cls):
        return cls.send_and_validate(0x64, 0x00)

    @classmethod
    def set_s05_on(cls):
        return cls.send_and_validate(0x64, 0x01)


    #=======================
    # S06
    # CMD = 0x65
    #=======================
    @classmethod
    def set_s06_off(cls):
        return cls.send_and_validate(0x65, 0x00)

    @classmethod
    def set_s06_on(cls):
        return cls.send_and_validate(0x65, 0x01)


    #=======================
    # S07
    # CMD = 0x66
    #=======================
    @classmethod
    def set_s07_off(cls):
        return cls.send_and_validate(0x66, 0x00)

    @classmethod
    def set_s07_on(cls):
        return cls.send_and_validate(0x66, 0x01)


    #=======================
    # S08
    # CMD = 0x67
    #=======================
    @classmethod
    def set_s08_off(cls):
        return cls.send_and_validate(0x67, 0x00)

    @classmethod
    def set_s08_on(cls):
        return cls.send_and_validate(0x67, 0x01)


    #=======================
    # S09
    # CMD = 0x68
    #=======================
    @classmethod
    def set_s09_off(cls):
        return cls.send_and_validate(0x68, 0x00)

    @classmethod
    def set_s09_on(cls):
        return cls.send_and_validate(0x68, 0x01)


    #=======================
    # S10
    # CMD = 0x69
    #=======================
    @classmethod
    def set_s10_off(cls):
        return cls.send_and_validate(0x69, 0x00)

    @classmethod
    def set_s10_on(cls):
        return cls.send_and_validate(0x69, 0x01)


    #=======================
    # S11
    # CMD = 0x6A
    #=======================
    @classmethod
    def set_s11_off(cls):
        return cls.send_and_validate(0x6A, 0x00)

    @classmethod
    def set_s11_on(cls):
        return cls.send_and_validate(0x6A, 0x01)


    #=======================
    # S12
    # CMD = 0x6B
    #=======================
    @classmethod
    def set_s12_off(cls):
        return cls.send_and_validate(0x6B, 0x00)

    @classmethod
    def set_s12_on(cls):
        return cls.send_and_validate(0x6B, 0x01)


    #=======================
    # S13
    # CMD = 0x6C
    #=======================
    @classmethod
    def set_s13_off(cls):
        return cls.send_and_validate(0x6C, 0x00)

    @classmethod
    def set_s13_on(cls):
        return cls.send_and_validate(0x6C, 0x01)


    #=======================
    # S14
    # CMD = 0x6D
    #=======================
    @classmethod
    def set_s14_off(cls):
        return cls.send_and_validate(0x6D, 0x00)

    @classmethod
    def set_s14_on(cls):
        return cls.send_and_validate(0x6D, 0x01)


    #=======================
    # S15
    # CMD = 0x6E
    #=======================
    @classmethod
    def set_s15_off(cls):
        return cls.send_and_validate(0x6E, 0x00)

    @classmethod
    def set_s15_on(cls):
        return cls.send_and_validate(0x6E, 0x01)


    #=======================
    # S16
    # CMD = 0x6F
    #=======================
    @classmethod
    def set_s16_off(cls):
        return cls.send_and_validate(0x6F, 0x00)

    @classmethod
    def set_s16_on(cls):
        return cls.send_and_validate(0x6F, 0x01)


    #=======================
    # S17
    # CMD = 0x70
    #=======================
    @classmethod
    def set_s17_off(cls):
        return cls.send_and_validate(0x70, 0x00)

    @classmethod
    def set_s17_on(cls):
        return cls.send_and_validate(0x70, 0x01)


    #=======================
    # S18
    # CMD = 0x71
    #=======================
    @classmethod
    def set_s18_off(cls):
        return cls.send_and_validate(0x71, 0x00)

    @classmethod
    def set_s18_on(cls):
        return cls.send_and_validate(0x71, 0x01)


    #=======================
    # S19
    # CMD = 0x72
    #=======================
    @classmethod
    def set_s19_off(cls):
        return cls.send_and_validate(0x72, 0x00)

    @classmethod
    def set_s19_on(cls):
        return cls.send_and_validate(0x72, 0x01)


    #=======================
    # S21
    # CMD = 0x74
    #=======================
    @classmethod
    def set_s21_off(cls):
        return cls.send_and_validate(0x74, 0x00)

    @classmethod
    def set_s21_on(cls):
        return cls.send_and_validate(0x74, 0x01)


    #=======================
    # S22
    # CMD = 0x75
    #=======================
    @classmethod
    def set_s22_off(cls):
        return cls.send_and_validate(0x75, 0x00)

    @classmethod
    def set_s22_on(cls):
        return cls.send_and_validate(0x75, 0x01)

    
    #=======================
    # S28
    # CMD = 0x7B
    # STATES:
    #   0x00 -> 8 ohms
    #   0x01 -> Neutral
    #   0x02 -> 600 ohms
    #=======================
    @classmethod
    def set_s28_8ohms(cls):
        return cls.send_and_validate(0x7B, 0x01)

    @classmethod
    def set_s28_neutral(cls):
        return cls.send_and_validate(0x7B, 0x00)

    @classmethod
    def set_s28_600ohms(cls):
        return cls.send_and_validate(0x7B, 0x02)


    #=======================
    # S29
    # CMD = 0x7C
    #=======================
    @classmethod
    def set_s29_off(cls):
        return cls.send_and_validate(0x7C, 0x00)

    @classmethod
    def set_s29_on(cls):
        return cls.send_and_validate(0x7C, 0x01)

    
    
    
    