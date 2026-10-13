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
    searching = pyqtSignal()   # NEW — fired right before ISTJ CH3/COM initialization begins

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

            from devices.device_types import DeviceType
            from devices.device_listeners import STM32Listener

            psu_inst = getattr(self.worker, "psu_inst", None)
            # refresh_for_self_test() already did the authoritative CH3 +
            # COM check and set this correctly — if it's already True, CH3
            # was already ON and the port was already found, so there is
            # nothing left to do (Case 1: don't touch CH3 at all).
            mcu_ok = self.worker.device_status.get("Microcontroller", False)

            if psu_inst is not None and not mcu_ok:
                self.searching.emit()   # NEW — screen shows "Searching..." before any hardware touch
                for lst in self.monitor._listeners:
                    try:
                        lst.pause()
                    except Exception:
                        pass

                try:
                    with self.monitor._psu_lock:
                        ch3_state = psu_inst.query("OUTP? CH3").strip().upper()
                except Exception:
                    ch3_state = "0"

                # Only power CH3 on if it's genuinely off. If it's already
                # ON but the COM port just hasn't been found yet, leave it
                # alone — do NOT turn it off and back on.
                if ch3_state not in ("1", "ON"):
                    if self._cancelled:
                        for lst in self.monitor._listeners:
                            try:
                                lst.resume()
                            except Exception:
                                pass
                        return
                    turn_on_psu_channel(
                        psu_inst, channel=3, voltage=5.0, current=1.0,
                        psu_lock=self.monitor._psu_lock,
                    )

                self.monitor._remove_dead_listener(DeviceType.MCU)   # release the port before polling

                # Poll for the COM port instead of blocking a fixed 8s —
                # same 8.0s upper bound as before, but returns as soon as
                # the port actually appears.
                ser = None
                for _ in range(80):
                    if self._cancelled:
                        for lst in self.monitor._listeners:
                            try:
                                lst.resume()
                            except Exception:
                                pass
                        return
                    ser = self.monitor._open_stm32_serial()
                    if ser is not None:
                        break
                    time.sleep(0.1)

                if ser is not None and not self._cancelled:
                    # COM visibility is sufficient for "Connected" — mirrors
                    # DeviceMonitor._try_reconnect_stm32(), which intentionally
                    # skips SYNC for this same reason.
                    from core.stm32_commands import STM32RelayController
                    if ser is not STM32RelayController._default_state_conn:
                        # Only close+reopen a handle we independently
                        # opened. If _open_stm32_serial() gave us
                        # STM32RelayController's shared persistent
                        # connection instead, closing it here would break
                        # relay commands out from under it.
                        ser.close()
                        self.monitor._remove_dead_listener(DeviceType.MCU)
                        ser = self.monitor._open_stm32_serial()
                    if ser is not None and not self._cancelled:
                        self.monitor._start(
                            STM32Listener(ser, psu_inst=psu_inst, psu_lock=self.monitor._psu_lock)
                        )
                        mcu_ok = True

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

import faulthandler
from PyQt5.QtCore import qInstallMessageHandler
_crash_log = open(Path.home() / "hal_crash.log", "a", buffering=1)
faulthandler.enable(file=_crash_log, all_threads=True)

def _qt_msg(mode, ctx, msg):
    _crash_log.write(f"[Qt:{int(mode)}] {msg}\n")
    _crash_log.flush()
qInstallMessageHandler(_qt_msg)


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
        # Back/Abort shut PSU CH3 off, so Equipment Self Check must run the
        # scan (CH3 on + ISTJ discovery) instead of the fast path.
        self._visited_test_mode = False
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
        # BEFORE: _hide_current() + processEvents() ran FIRST, so the previous
        #         screen disappeared while Equipment Self Check was still
        #         being built/blocking, exposing a blank window.
        # AFTER:  remember the previous screen and keep it VISIBLE until the
        #         new screen is fully constructed and painted.
        prev_screen = self.current_screen

        worker = getattr(self._connection_screen, "worker", None)
        monitor = self._active_monitor

        if monitor is None and worker is not None:
            from devices.device_monitor import DeviceMonitor
            monitor = DeviceMonitor()
            monitor.start_all(worker)
            self._active_monitor = monitor

        came_from_test_screen = self._visited_test_mode
        self._visited_test_mode = False

        # BEFORE: handles_alive()/refresh_from_worker() (blocking VISA queries
        #         and listener waits) ran AFTER the window was already shown,
        #         freezing it while blank.
        # AFTER:  run them now, while the previous screen is still on display,
        #         so the status snapshot below is already accurate.
        fast_path = False
        if (came_from_test_screen and monitor is not None and worker is not None
                and monitor.handles_alive(worker)):
            monitor.refresh_from_worker(worker)
            fast_path = True

        initial_status = dict(worker.device_status) if worker is not None else dict(self.device_status)
        self.device_status = initial_status

        # AFTER: build the screen without showing it. If construction fails,
        #        keep the working previous screen visible and report it.
        try:
            equipment_screen = EquipmentSelfCheckScreen(
                device_status=initial_status,
                monitor=monitor,
            )
        except Exception as e:
            traceback.print_exc()
            print(f"[NAV] Equipment Self Check construction failed: {e}")
            try:
                QMessageBox.warning(
                    prev_screen, "Equipment Self Check",
                    f"Could not open Equipment Self Check:\n\n{e}",
                )
            except Exception:
                pass
            return   # prev_screen was never hidden

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

        # AFTER: the screen is fully built -> show it, let Qt run one
        #        layout/paint pass, and only THEN hide the previous screen.
        equipment_screen.showMaximized()
        equipment_screen.raise_()
        equipment_screen.activateWindow()
        QApplication.processEvents()
        if prev_screen is not None and prev_screen is not equipment_screen:
            prev_screen.hide()
        self.current_screen = equipment_screen

        if fast_path:
            self.device_status = dict(worker.device_status)
            return
        # otherwise fall through to the background scan below

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

            thread = _SelfTestRefreshThread(monitor, worker)
            self._self_test_refresh_thread = thread
            print("[THREAD] SelfTestRefresh CREATED")
            thread.finished_ok.connect(
                lambda status: self._on_self_test_refresh_done(equipment_screen, initial_status, status)
            )
            thread.failed.connect(
                lambda err: self._on_self_test_refresh_failed(equipment_screen, err)
            )
            thread.searching.connect(
                lambda: equipment_screen.set_istj_searching()
                
            )
            # Qt's own `finished` signal is the ONLY thing allowed to
            # clear self._self_test_refresh_thread — never a bounded
            # wait() timeout. Guarded by identity so a stale/replaced
            # thread's finished signal can't null out a newer one.
            thread.finished.connect(lambda: self._on_refresh_thread_finished(thread))
            thread.start()
            print("[THREAD] SelfTestRefresh STARTED")
            
    def _on_refresh_thread_finished(self, thread):
        print("[THREAD] SelfTestRefresh FINISHED")
        if thread is not self._self_test_refresh_thread:
            return   # a newer thread has already replaced this one
        if thread.isRunning():
            return   # finished signal fired but isRunning() still true — shouldn't
                      # happen, but never null a possibly-live reference
        self._self_test_refresh_thread = None

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
        # self._self_test_refresh_thread clearing is now owned exclusively
        # by _on_refresh_thread_finished (Qt's `finished` signal) — do not
        # duplicate it here to avoid racing/clearing a thread object that
        # technically hasn't emitted `finished` yet at this exact instant.

    def _on_self_test_refresh_failed(self, screen, error_message: str):
        """
        The background scan raised — surfaces the failure instead of
        leaving the screen stuck showing pre-scan status with no
        indication anything went wrong.
        """
        # Reference clearing owned by _on_refresh_thread_finished, not here.
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