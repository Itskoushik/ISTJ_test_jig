import sys
from pathlib import Path
import time
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QEvent,QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QWidget
)
from psu.psu_helpers import turn_on_psu_channel
from devices.apx_analyzer import close_apx
from screens.login_screen import LoginScreen
from screens.connection_screen import ConnectionScreen
from screens.test_selection_screen import TestSelectionScreen
from screens.test_reports_screen import TestReportsScreen
from screens.equipment_self_check_screen import EquipmentSelfCheckScreen
from screens.full_test_screen import FullTestScreen
from core.paths import *
from dialogs.prereq_check import run_prereq_check, PrereqCheckDialog
import traceback
import pyvisa
import traceback
class _SelfTestRefreshThread(QThread):
    """
    Runs DeviceMonitor.refresh_for_self_test() plus the CH3-ON / ISTJ
    boot-grace / sync chain OFF the main thread, so the operator sees
    the Equipment Self Check screen immediately instead of a frozen app
    for ~8-10s. Emits the final worker.device_status dict when done.

    Cancellable via cancel() — checked before every hardware-affecting
    step and in 0.1s slices during the boot-grace wait, so leaving the
    screen mid-refresh doesn't let CH3/ISTJ actions land after the
    operator has already navigated away and turned things off.
    Any exception during the scan emits `failed` instead of hanging
    silently with finished_ok never firing.
    """
    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, monitor, worker):
        super().__init__()
        self.monitor = monitor
        self.worker = worker
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.monitor.refresh_for_self_test(self.worker)

            if self._cancelled:
                return

            psu_inst = getattr(self.worker, "psu_inst", None)
            mcu_ok = False
            if psu_inst is not None:
                # refresh_for_self_test() already resumed all listeners
                # (incl. the live STM32 heartbeat listener) before returning.
                # Re-pause everything before touching CH3 / the ISTJ COM port,
                # otherwise this thread's unsync()/sync()/serial-open races
                # the live listener for the same port and makes ISTJ flash
                # "Not Connected" a few seconds after CH3 comes on.
                for lst in self.monitor._listeners:
                    try:
                        lst.pause()
                    except Exception:
                        pass

                # Force a genuine power cycle: turn CH3 OFF first, then wait 1.5s
                # before turning it back on.
                try:
                    with self.monitor._psu_lock:
                        psu_inst.write("INST:NSEL 3")
                        time.sleep(0.1)
                        psu_inst.write("OUTP OFF")
                except Exception:
                    pass
                for _ in range(15):          # 1.5s de-power wait, cancellable
                    if self._cancelled:
                        for lst in self.monitor._listeners:
                            try:
                                lst.resume()
                            except Exception:
                                pass
                        return
                    time.sleep(0.1)

                turn_on_psu_channel(
                    psu_inst, channel=3, voltage=5.0, current=1.0,
                    psu_lock=self.monitor._psu_lock,
                )
                for _ in range(80):          # 8.0s in 0.1s slices — cancellable
                    if self._cancelled:
                        for lst in self.monitor._listeners:
                            try:
                                lst.resume()
                            except Exception:
                                pass
                        return
                    time.sleep(0.1)

                from core.stm32_commands import STM32RelayController
                from devices.device_types import DeviceType
                self.monitor._remove_dead_listener(DeviceType.MCU)   # release the port before reopening it
                ser = self.monitor._open_stm32_serial()
                if ser is not None and not self._cancelled:
                    ser.close()
                    STM32RelayController.unsync()
                    time.sleep(0.3)
                    if not self._cancelled and STM32RelayController.sync():
                        ser = self.monitor._open_stm32_serial()
                        if ser is not None and not self._cancelled:
                            from devices.device_types import DeviceType
                            from devices.device_listeners import STM32Listener
                            self.monitor._remove_dead_listener(DeviceType.MCU)
                            self.monitor._start(
                                STM32Listener(ser, psu_inst=psu_inst, psu_lock=self.monitor._psu_lock)
                            )
                            mcu_ok = True

                # Resume everything else. If sync failed, the old MCU listener
                # (never removed above) resumes too instead of being left
                # paused forever.
                for lst in self.monitor._listeners:
                    try:
                        lst.resume()
                    except Exception:
                        pass

            if self._cancelled:
                return

            self.worker.device_status["Microcontroller"] = mcu_ok
            self.finished_ok.emit(dict(self.worker.device_status))
        except Exception as e:
            if not self._cancelled:
                self.failed.emit(str(e))
        
def except_hook(exctype, value, tb):
    print("\n REAL ERROR TRACEBACK ")
    traceback.print_exception(exctype, value, tb)

sys.excepthook = except_hook


def shutdown_psu_ch3(existing_psu=None):
    #dynamic detection of PSU resource
    PSU_RESOURCE = "USB::0x1AB1::0x0E11"  # Rigol DP800 series identifier

    psu = existing_psu
    rm = None
    opened_here = False

    if psu is None:
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            print(f"[PSU] Scanning {len(resources)} resources: {resources}")

            for resource in resources:
                if resource.startswith("ASRL"):
                    print(f"[PSU] Skipping {resource} (serial/COM port — reserved for STM32)")
                    continue
                if PSU_RESOURCE not in resource:
                    print(f"[PSU] Skipping {resource} (not PSU)")
                    continue
                try:
                    inst = rm.open_resource(resource)
                    inst.timeout = 3000
                    idn = inst.query("*IDN?").strip()
                    print(f"[PSU] {resource} -> {idn}")
                    if "DP8" in idn or "RIGOL" in idn.upper():
                        psu = inst
                        opened_here = True
                        print(f"[PSU] Matched PSU at {resource}")
                        break
                    else:
                        print(f"[PSU] IDN mismatch, skipping")
                        inst.close()
                except Exception as e:
                    print(f"[PSU] Failed to open {resource}: {e}")
                    traceback.print_exc()
                    continue

        except Exception as e:
            print(f"[PSU] Resource scan failed: {e}")
            traceback.print_exc()

    if psu is None:
        print("[PSU] No PSU found — PSU not shut down.")
        if rm:
            try: rm.close()
            except: pass
        return

    # Turn off ALL channels (1, 2, 3) on shutdown
    for ch in [1, 2, 3]:
        try:
            print(f"[PSU] Turning off CH{ch}...")
            psu.write(f"INST:NSEL {ch}")
            time.sleep(0.5)
            psu.write("OUTP OFF")
            time.sleep(0.5)
            state = psu.query("OUTP?").strip()
            print(f"[PSU] CH{ch} state after OFF: '{state}'")
        except Exception as e:
            print(f"[PSU] CH{ch} shutdown command failed: {e}")

    if opened_here:
        try: psu.close()
        except: pass
        if rm:
            try: rm.close()
            except: pass


# ============================================================================
# APPLICATION
# ============================================================================

class HALApplication(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.main_window = None
        self.current_screen = None
        self.device_status = {}
        self._psu_shutdown_done = False
        self._visited_test_mode = False   # set True by Single/Full Test; consumed once by show_equipment_self_check()

        # ✅ Screen cache — reuse instead of recreate
        self._test_selection_screen = None
        self._connection_screen = None
        self._active_monitor = None   # ← persistent DeviceMonitor, survives navigation

        self.aboutToQuit.connect(self._on_quit)

    def _trigger_psu_shutdown(self, existing_psu=None):
        if self._psu_shutdown_done:
            return
        self._psu_shutdown_done = True
        shutdown_psu_ch3(existing_psu=existing_psu)
        close_apx()

    def _on_quit(self):
        self._trigger_psu_shutdown()

    def _reset_psu_shutdown_guard(self):
        self._psu_shutdown_done = False

    def _reset_visited_test_mode(self):
        self._visited_test_mode = False

    def _hide_current(self):
        """Hide current screen without destroying it."""
        if self.current_screen:
            self.current_screen.hide()

    # ── Login ─────────────────────────────────────────────────────────────────
    def show_login(self):
        self.logged_in_name = None
        self.logged_in_emp_id = None
        self.device_status = {}
        self._reset_psu_shutdown_guard()
        self._reset_visited_test_mode()

        # ✅ Clear cached screens on logout — fresh session
        self._test_selection_screen = None
        self._connection_screen = None
        self._active_monitor = None

        if self.main_window is None:
            self.main_window = QMainWindow()
            self.main_window.setGeometry(100, 100, 550, 550)
            self.main_window.setWindowTitle("HAL")
            self.main_window.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
            self.main_window.setFixedSize(550, 550)
            self.main_window.setStyleSheet("background: linear-gradient(to bottom, #e0f7fa, #ffffff);")

        self._hide_current()
        QApplication.processEvents()
        login_screen = LoginScreen()
        login_screen.login_success.connect(self.on_login_success)
        login_screen.show()
        self.current_screen = login_screen

    # ── Login success ─────────────────────────────────────────────────────────
    def on_login_success(self, name, emp_id): #, real_designation
        self.logged_in_name = name
        self.logged_in_emp_id = emp_id

        self._hide_current()
        QApplication.processEvents()
        try:
            self.show_connection(name, emp_id)
        except Exception as e:
            QMessageBox.critical(None, "Critical Error", str(e))

    # ── Connection screen ─────────────────────────────────────────────────────
    def show_connection(self, name, emp_id):
        self._hide_current()
        QApplication.processEvents()
        # ✅ Reuse cached connection screen if it exists
        if self._connection_screen is None:
            self._connection_screen = ConnectionScreen(name, emp_id)
            self._connection_screen.test_selection_requested.connect(self.on_connection_complete)
            self._connection_screen.logout_requested.connect(self.show_login)

        self._connection_screen.show()
        self._connection_screen.raise_()
        self.current_screen = self._connection_screen

    # ── Connection complete ───────────────────────────────────────────────────
    def on_connection_complete(self):
        if self.current_screen:
            self.device_status = getattr(self.current_screen, "device_status", {})

        self._reset_psu_shutdown_guard()
        self._reset_visited_test_mode()
        self.show_test_selection()

    # ── Test selection ────────────────────────────────────────────────────────
    def show_test_selection(self):
        self._hide_current()
        QApplication.processEvents()
        # ✅ Reuse cached test selection screen if it exists
        if self._test_selection_screen is None:
            self._test_selection_screen = TestSelectionScreen()
            self._test_selection_screen.full_test_requested.connect(self.show_full_test)
            self._test_selection_screen.unit_test_requested.connect(self.show_unit_test)
            self._test_selection_screen.equipment_self_test_requested.connect(self.show_equipment_self_check)
            self._test_selection_screen.test_reports_requested.connect(self.show_test_reports)
            self._test_selection_screen.return_to_connection.connect(self.on_disconnect_return)

        self._test_selection_screen.show()
        self._test_selection_screen.raise_()
        QApplication.processEvents()
        self.current_screen = self._test_selection_screen

    # ── Full test ─────────────────────────────────────────────────────────────
    def show_full_test(self):
        self._hide_current()
        self._visited_test_mode = True
        # Full test screen is heavy/stateful — always create fresh
        full_test_screen = FullTestScreen()
        full_test_screen.return_to_test_selection.connect(self.on_full_test_return)
        full_test_screen.return_to_connection.connect(self.on_disconnect_return)
        full_test_screen.show()
        self.current_screen = full_test_screen

    def on_full_test_return(self):
        # Don't close full_test_screen — let it clean itself up
        self.show_test_selection()

    # ── Disconnect / return ───────────────────────────────────────────────────
    def on_disconnect_return(self):
        self._hide_current()
        QApplication.processEvents()
        # ✅ Invalidate cached connection screen — need fresh one after disconnect
        self._connection_screen = None
        self._test_selection_screen = None
        self.show_connection(self.logged_in_name, self.logged_in_emp_id)

    # ── Equipment self check ──────────────────────────────────────────────────

    def show_equipment_self_check(self):
        self._hide_current()
        QApplication.processEvents()
        worker = getattr(self._connection_screen, "worker", None)
        monitor = self._active_monitor

        if monitor is None and worker is not None:
            from devices.device_monitor import DeviceMonitor
            monitor = DeviceMonitor()
            monitor.start_all(worker)
            self._active_monitor = monitor

        # ── Capture BEFORE resetting. True means Single/Full Test just ran
        #    and already power-cycled CH3, resynced ISTJ, and re-validated
        #    PSU/DMM/Oscilloscope as part of its own pre-step. Redoing that
        #    full CH3 OFF→ON + 8s boot-wait + ISTJ unsync/sync here is
        #    pointless hardware churn — it's what makes the just-finished
        #    test look like it's silently re-running.
        came_from_test_screen = self._visited_test_mode
        self._visited_test_mode = False

        # ── Show the screen NOW with the last-known status (may be stale) —
        #    the background thread below corrects each card in place within
        #    a few seconds, instead of freezing the app while it scans.
        initial_status = dict(worker.device_status) if worker is not None else dict(self.device_status)
        self.device_status = initial_status

        equipment_screen = EquipmentSelfCheckScreen(
            device_status=initial_status,
            monitor=monitor,
        )
        equipment_screen.return_to_test_selection.connect(self.show_test_selection)

        if monitor is not None:
            try:
                monitor.device_disconnected.disconnect()
                monitor.device_reconnected.disconnect()
            except TypeError:
                pass
            monitor.device_disconnected.connect(equipment_screen.on_device_disconnected)
            monitor.device_reconnected.connect(equipment_screen.on_device_reconnected)
            for lst in monitor._listeners:
                try:
                    lst.resume()
                except Exception:
                    pass
            monitor._reconnect_timer.start()
            equipment_screen._monitor = monitor

        equipment_screen.show()
        self.current_screen = equipment_screen

        # ── Coming back from Single/Full Test: just rebind listeners to
        #    whatever instances worker currently holds — no CH3/ISTJ
        #    power-cycle, no scanning-lock popup, no _SelfTestRefreshThread.
        if came_from_test_screen:
            if monitor is not None and worker is not None:
                monitor.refresh_from_worker(worker)
                self.device_status = dict(worker.device_status)
            return

        # ── Otherwise this is a genuine fresh entry (e.g. straight from
        #    Connection or Test Selection with no test just run) — kick off
        #    the real fresh-scan + CH3 + ISTJ boot/sync in the background.
        #    When it finishes, reconcile each card against what changed,
        #    via the screen's existing device-status handlers.
        if monitor is not None and worker is not None:
            # Lock every Run Self Test button until the scan finishes —
            # prevents a self-test from launching against a PSU/DMM/OSC
            # handle this background thread is concurrently replacing.
            try:
                equipment_screen.set_scanning_lock(True)
            except RuntimeError:
                pass

            # Stop the reconnect-poll timer BEFORE the background thread
            # touches CH3/ISTJ. _poll_reconnect() -> _try_reconnect_stm32()
            # runs on this (main) thread every 3s and does its own
            # independent CH3-ON + boot-wait + unsync/sync + serial-open —
            # the exact same job _SelfTestRefreshThread is about to do.
            # Left running, the two race: both write INST:NSEL 3/OUTP ON
            # and both try to open the ISTJ COM port concurrently, which is
            # what makes ISTJ CONTROLLER's connection state unreliable.
            # Restarted in _on_self_test_refresh_done/_failed once the
            # thread's own CH3/ISTJ sequence has fully finished.
            monitor._reconnect_timer.stop()

            self._self_test_refresh_thread = _SelfTestRefreshThread(monitor, worker)
            self._self_test_refresh_thread.finished_ok.connect(
                lambda status: self._on_self_test_refresh_done(equipment_screen, initial_status, status)
            )
            self._self_test_refresh_thread.failed.connect(
                lambda err: self._on_self_test_refresh_failed(equipment_screen, err)
            )
            self._self_test_refresh_thread.start()

    def _on_self_test_refresh_done(self, screen, old_status, new_status):
        self.device_status = dict(new_status)

        # Operator may have already clicked Back — screen could be a dead
        # PyQt wrapper for a destroyed C++ object at this point.
        if self.current_screen is not screen:
            return

        for ui_name, is_connected in new_status.items():
            was_connected = old_status.get(ui_name, False)
            try:
                if is_connected and not was_connected:
                    screen.on_device_reconnected(ui_name)
                elif not is_connected and was_connected:
                    screen.on_device_disconnected(ui_name, f"{ui_name} not detected during refresh")
            except RuntimeError:
                # screen was closed/deleted mid-refresh — nothing left to update
                return

        # ── Scan is done — unlock Run Self Test buttons, respecting the
        #    just-updated per-device connected state (not unconditionally).
        try:
            screen.set_scanning_lock(False)
        except RuntimeError:
            pass

        # ── Resume normal reconnect polling now that _SelfTestRefreshThread's
        #    own CH3/ISTJ sequence is fully done — safe to let _poll_reconnect
        #    take over disconnect recovery again without racing anything.
        if self._active_monitor is not None:
            self._active_monitor._reconnect_timer.start()

        self._self_test_refresh_thread = None

    def _on_self_test_refresh_failed(self, screen, error_message: str):
        """
        The background scan raised — surfaces the failure instead of
        leaving the screen stuck showing pre-scan status with no
        indication anything went wrong.
        """
        self._self_test_refresh_thread = None
        if self.current_screen is not screen:
            return

        # ── Unlock buttons even on failure — otherwise a scan exception
        #    leaves every Run Self Test button permanently disabled with
        #    no way to recover short of leaving and re-entering the screen.
        #    Fall back to the last-known device_status (pre-scan) since the
        #    scan itself didn't produce a trustworthy new one.
        try:
            screen.set_scanning_lock(False)
        except RuntimeError:
            pass

        # ── Resume normal reconnect polling even on failure — otherwise a
        #    scan exception leaves the timer stopped forever, and ISTJ/PSU/
        #    DMM/Oscilloscope disconnects would never be auto-recovered
        #    until the operator leaves and re-enters the screen.
        if self._active_monitor is not None:
            self._active_monitor._reconnect_timer.start()

        try:
            QMessageBox.warning(
                screen,
                "Equipment Refresh Failed",
                f"Fresh device validation failed:\n\n{error_message}\n\n"
                "Device status on screen may be stale. You can try leaving "
                "and re-entering Equipment Self Test to retry.",
            )
        except RuntimeError:
            pass

    # ── Test reports ──────────────────────────────────────────────────────────
    def show_test_reports(self):
        self._hide_current()
        QApplication.processEvents()
        reports_screen = TestReportsScreen()
        reports_screen.return_to_test_selection.connect(self.show_test_selection)
        reports_screen.show()
        self.current_screen = reports_screen

    def show_unit_test(self):
        self._visited_test_mode = True


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    
    app = HALApplication()

    results = run_prereq_check()
    dialog = PrereqCheckDialog(results)
    if dialog.exec_() == QDialog.Rejected:
        sys.exit(0)

    app.show_login()
    sys.exit(app.exec_())