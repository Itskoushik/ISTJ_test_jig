"""
PSUAutomation
=============

Lightweight PSU control used exclusively by SelfTestWorker
(equipment_self_check_screen.py). No voltage monitoring — self-tests
drive the PSU directly via raw SCPI and don't need live readings.
"""

import time
import threading
from threading import Event, Lock

import pyvisa

from core.stm32_commands import STM32RelayController
from psu.psu_commands import PSUCommands
from psu.psu_helpers import find_psu


class PSUAutomationHost:
    """
    Callback interface PSUAutomation needs from whatever owns it.
    """

    def log(self, message: str, is_error: bool = False):
        raise NotImplementedError

    def is_aborted(self) -> bool:
        raise NotImplementedError

    def notify_disconnect_toast(self):
        pass  # optional — default no-op

    def request_operator_ack(self, title: str, message: str):
        raise NotImplementedError

    def on_reconnect_failed(self):
        raise NotImplementedError

    def pause_device_listeners(self):
        pass  # optional — default no-op

    def restore_device_listener(self, listener):
        pass  # optional — default no-op


class PSUAutomation:
    """
    Owns the PSU VISA connection and channel workers.
    No voltage monitoring — self-tests don't need live readings.
    """

    def __init__(self, host: PSUAutomationHost):
        self.host = host

        self.psu_lock = Lock()
        self.rm = pyvisa.ResourceManager()
        self.psu_inst = None

        self.current_channel = None

        # Reconnect state
        self._psu_ready_event = Event()
        self._psu_ready_event.set()
        self._psu_error_handled = False
        self._disconnect_in_progress = False
        self._reconnect_in_progress = False
        self._reconnect_lock = Lock()

    # ------------------------------------------------------------------
    # Low level SCPI
    # ------------------------------------------------------------------

    def psu_send_command(self, command: str, _retries: int = 3) -> str:
        if not self._psu_ready_event.is_set():
            self._psu_ready_event.wait(timeout=300)
            if not self._psu_ready_event.is_set() or self.host.is_aborted():
                return ""
        if self._psu_error_handled:
            return ""
        if self._disconnect_in_progress:
            return ""
        if self.host.is_aborted():
            return ""
        if not self.psu_inst:
            return ""

        for attempt in range(1, _retries + 1):
            try:
                with self.psu_lock:
                    if "?" in command:
                        return self.psu_inst.query(command).strip()
                    else:
                        self.psu_inst.write(command)
                        return ""
            except Exception as exc:
                exc_str = str(exc).lower()
                print(f"[PSU] I/O error (attempt {attempt}/{_retries}): {exc}")

                _soft_errors = (
                    "incorrect", "invalid", "undefined header",
                    "syntax error", "query interrupted", "query unterminated",
                    "command error", "execution error", "otp", "ocp", "ovp",
                    "vi_error_io",
                )
                if any(token in exc_str for token in _soft_errors):
                    print(f"[PSU] Soft SCPI error — skipping reconnect: {exc}")
                    return ""

                if attempt < _retries:
                    time.sleep(0.3)
                    continue

                _hard_errors = (
                    "visaioerror", "resource not found", "timeout",
                    "not connected", "unable to connect", "no listeners",
                    "vi_error", "access denied", "object reference",
                )
                if not any(token in exc_str for token in _hard_errors):
                    print(f"[PSU] Non-transport error after retries — skipping reconnect: {exc}")
                    return ""

                if self._reconnect_in_progress:
                    return ""
                self._psu_error_handled = True
                threading.Thread(
                    target=self._background_reconnect,
                    daemon=True,
                    name="PSU-reconnect"
                ).start()
                return ""
        return ""

    def _safe_set_remote(self):
        try:
            with self.psu_lock:
                if self.psu_inst:
                    self.psu_inst.write("SYST:REM")
        except Exception as e:
            print(f"[PSU] SYST:REM suppressed (already remote or benign): {e}")

    def freeze_psu_front_panel(self):
        self.psu_send_command(PSUCommands.SYSTEM_LOCK_ON)
        self.host.log("PSU front panel LOCKED (SYST:LOCK ON)", False)

    def unfreeze_psu_front_panel(self):
        self.psu_send_command(PSUCommands.SYSTEM_LOCK_OFF)
        self.host.log("PSU front panel UNLOCKED (SYST:LOCK OFF)", False)

    def find_psu(self):
        return find_psu(self)

    # ------------------------------------------------------------------
    # Channel workers — no voltage monitoring
    # ------------------------------------------------------------------

    def worker_channel_1(self):
        """CH1: 28V / 2.6A, output ON."""
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 1")
        time.sleep(0.1)
        self.psu_send_command("SOUR1:VOLT 28.0")
        self.psu_send_command("SOUR1:CURR 2.6")
        self.psu_send_command("OUTP ON")
        time.sleep(0.5)
        self.current_channel = 1
        self.host.log("Ch1 OUTPUT ON (28V, 2.6A)", False)
        time.sleep(2)

    def worker_ch2_28v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)
        self.psu_send_command("SOUR2:VOLT 28.0")
        self.psu_send_command("SOUR2:CURR 2.0")
        self.psu_send_command("OUTP ON")
        time.sleep(0.5)
        self.current_channel = 2
        self.host.log("Ch2 OUTPUT ON (28V, 2.0A)", False)

    def worker_ch3_5v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 3")
        time.sleep(0.1)
        self.psu_send_command("SOUR3:VOLT 5.0")
        self.psu_send_command("SOUR3:CURR 1.0")
        self.psu_send_command("OUTP ON")
        time.sleep(0.5)
        self.current_channel = 3
        self.host.log("Ch3 OUTPUT ON (5V, 1.0A)", False)

    def worker_ch2_12v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)
        self.psu_send_command("SOUR2:VOLT 12.0")
        self.psu_send_command("SOUR2:CURR 2.0")
        self.psu_send_command("OUTP ON")
        time.sleep(0.5)
        self.current_channel = 2
        self.host.log("Ch2 OUTPUT ON (12V, 2.0A)", False)

    def worker_ch2_5v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)
        self.psu_send_command("SOUR2:VOLT 5.0")
        self.psu_send_command("SOUR2:CURR 2.0")
        self.psu_send_command("OUTP ON")
        time.sleep(0.5)
        self.current_channel = 2
        self.host.log("Ch2 OUTPUT ON (5V, 2.0A)", False)

    def turn_off_psu_output(self, channel: int) -> bool:
        try:
            time.sleep(0.1)
            with self.psu_lock:
                self.psu_inst.write("*CLS")
                time.sleep(0.05)
                self.psu_inst.write(f"INST:NSEL {channel}")
                time.sleep(0.05)
                self.psu_inst.write("OUTP OFF")
            self.host.log(f"Ch{channel} output turned OFF (OUTP OFF)", False)
            return True
        except Exception as e:
            self.host.log(f"ERROR: Failed to turn off output - {str(e)}", True)
            return False

    # ------------------------------------------------------------------
    # Disconnect / reconnect recovery
    # ------------------------------------------------------------------

    def _background_reconnect(self, max_attempts: int = 5, delay: float = 3.0):
        lock = self._reconnect_lock
        acquired = lock.acquire(blocking=False)
        if not acquired:
            print("[PSU RECONNECT] Already in progress — skipping")
            return
        self._reconnect_in_progress = True
        self._psu_ready_event.clear()
        try:
            self.host.pause_device_listeners()

            try:
                if self.psu_inst:
                    self.psu_inst.close()
            except Exception:
                pass
            self.psu_inst = None

            try:
                if self.rm:
                    self.rm.close()
            except Exception:
                pass
            finally:
                self.rm = None

            saved_channel = self.current_channel or 1
            self.host.notify_disconnect_toast()

            self.host.log("⚠ PSU connection lost — waiting for operator to reconnect cable...", True)
            self.host.request_operator_ack(
                "⚠ PSU Disconnected",
                "The PSU connection has been lost.\n\n"
                "Please ensure:\n"
                "  • PSU USB cable is firmly connected\n"
                "  • PSU power switch is ON\n"
                "  • All power cables are seated properly\n\n"
                "Click OK when PSU is connected and ready — "
                "the system will then attempt to reconnect automatically.",
            )
            self.host.log("🔌 Operator confirmed PSU ready — attempting reconnect...", False)

            for attempt in range(1, max_attempts + 1):
                if self.host.is_aborted():
                    return
                print(f"[PSU RECONNECT] Attempt {attempt}/{max_attempts}...")
                time.sleep(delay)
                try:
                    self.rm = pyvisa.ResourceManager()
                    new_inst = self.find_psu()
                    if not new_inst:
                        continue
                    self.psu_inst = new_inst
                    self._safe_set_remote()
                    time.sleep(0.2)

                    # Restore CH3 (5V / 1A) — the only channel used in self-tests
                    self.psu_inst.write("INST:NSEL 3")
                    time.sleep(0.05)
                    self.psu_inst.write("SOUR3:VOLT 5.0")
                    self.psu_inst.write("SOUR3:CURR 1.0")
                    self.psu_inst.write("OUTP ON")
                    time.sleep(0.1)

                    self.psu_inst.write(f"INST:NSEL {saved_channel}")
                    time.sleep(0.1)

                    try:
                        sync_ok = STM32RelayController.send_with_retry(STM32RelayController.sync)
                        if sync_ok:
                            self.host.log("✅ STM32 sync confirmed after PSU restore", False)
                        else:
                            self.host.log("⚠ STM32 sync failed after PSU restore — relays may be unreliable", True)
                    except Exception as sync_err:
                        self.host.log(f"⚠ STM32 sync error: {sync_err}", True)

                    self._psu_error_handled = False

                    self.host.request_operator_ack(
                        "✅ PSU Reconnected Successfully",
                        "PSU has been reconnected.\n\n"
                        "The self-test will resume from where it paused.\n\n"
                        "Click OK to continue.",
                    )

                    self._psu_ready_event.set()
                    self.host.log("▶ PSU reconnected — self-test resuming.", False)
                    return

                except Exception as exc:
                    print(f"[PSU RECONNECT] Attempt {attempt} failed: {exc}")

            print("[PSU RECONNECT] ✗ All attempts failed — aborting")
            self.host.log("❌ PSU reconnect failed — self-test aborted.", True)
            self._disconnect_in_progress = True
            self.host.on_reconnect_failed()

        finally:
            self._reconnect_in_progress = False
            lock.release()

    def check_abort(self):
        if self.host.is_aborted():
            raise Exception("TEST_ABORTED_BY_USER")
        if not self._psu_ready_event.is_set():
            self.host.log("⏸ Paused — waiting for PSU to reconnect...", False)
            self._psu_ready_event.wait(timeout=300)
            if self.host.is_aborted():
                raise Exception("TEST_ABORTED_BY_USER")
            self.host.log("▶ PSU ready — resuming.", False)