
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from core.paths import RESOURCES_DIR
from core.excel_logger import create_model_report
from PyQt5.QtCore import QTimer

def run_init_jbox(screen):
    """
    Connect the audio analyser generator output to MIC Connector J27.
    Connect the audio analyser input and oscilloscope to PH Connector J29.
    
    """
            
    screen.log_signal.emit("========== INITIALIZATION START ==========", False)
    time.sleep(0.1)

    screen.log_signal.emit("Switching all Relays to Default state", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_default_states():
        screen.log_signal.emit("All relays successfully set to default states", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
        return

    # ✅ Do not freeze GUI during settle delay
    screen.log_signal.emit("Waiting 20 seconds for relays to settle...", False)

    screen.abortable_sleep(20)
    
    
    # screen.log_signal.emit("COMMENCING TESTS UNDER NORMAL MODE", False)
    
    # screen.check_abort()
    screen.log_signal.emit("Step 1: Connecting the audio analyser generator output to MIC Connector J27", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j27_on():
        screen.log_signal.emit("J27 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J27", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    screen.log_signal.emit("Step 2: Connecting the audio analyser input and oscilloscope to PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j29_on():
        screen.log_signal.emit("J29 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J29", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J61 Connector to J101 Connector using test cable.\n"
        "• Connect J62 Connector to J102 Connector using test cable.\n"
        "• Connect J64 Connector to J108 Connector using test cable.\n",
        RESOURCES_DIR / "junction_box.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J65 Connector to J101 Connector using test cable.\n"
        "• Connect J66 Connector to J102 Connector using test cable.\n",
        None,"ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    screen.log_signal.emit("Step 3: Power Supply set to 28V (SOUR:VOLT 28.0)", False)
    time.sleep(1)
    screen.check_abort()
    
    screen.log_signal.emit("Step 4: Connecting the power supply output to Connector J58", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j58_on():
        screen.log_signal.emit("J58 successfully Connected to power supply output", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J58 to power supply output", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• V/UHF 1 to SPARE 2 Rotate all knobs fully CCW (Counter Clockwise) and to OUT position .\n"
        "• ADF1 to SPARE 5 Rotate all knobs fully CCW (Counter Clockwise) .\n"
        "• ICS Volume Control fully CW (Clockwise) .\n"
        "• VOS control CCW (Counter Clockwise) to HOT position .\n"
        "• STBY/NORMAL switch to NORMAL.\n"
        "• RAD PTT,SONIC and O/R are not illuminated .\n",
        RESOURCES_DIR / "jb.jpg","yes_no",None
    )

    # ⏸ WAIT until operator clicks yes or no
    screen.operator_event.wait()
    
    screen.log_signal.emit("Step 6: Connecting the JACK J67 to Multimeter +ve lead ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j67_on():
        screen.log_signal.emit("J67 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J67 to Multimeter +ve lead", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    #audio analyser gen output impedance to 600ohm bal input read AMPL ,set audio analyser gen output to 750 uvrms at 1kHz 
    
    screen.log_signal.emit("Junction Box initialization complete", False)
    
    

def run_init_sb(screen):
        """
        Run test initialization sequence with PSU automation.
        
        Steps:
        1. LOCAL/REMOTE switch configuration
        2. Load resistance configuration
        3. Switch configuration
        4. PSU setup
        5. PSU automation sequence
        """
        model = screen.alhx_combo.currentText().strip()
        # # Create new report
        # QTimer.singleShot(50, lambda: create_model_report(model))
        screen.log_signal.emit("========== INITIALIZATION START ==========", False)
        time.sleep(0.1)

        screen.log_signal.emit("Switching all Relays to Default state", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.set_default_states():
            screen.log_signal.emit("All relays successfully set to default states", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)
            return

        # ✅ Do not freeze GUI during settle delay
        screen.log_signal.emit("Waiting 20 seconds for relays to settle...", False)

        screen.abortable_sleep(20)
        
        
        
        screen.log_signal.emit("COMMENCING TESTS UNDER NORMAL MODE", False)
        # # 🔴 FORCE PSU BIND FIRST
        # if not screen.psu_inst:
        #     screen.psu_inst = screen.find_psu()

        # # ❌ PSU NOT PRESENT → IMMEDIATE ABORT
        # if not screen.psu_inst:
        #     QTimer.singleShot(
        #         0,
        #         lambda: screen.on_device_disconnected(
        #             DeviceType.PSU,
        #             "Power Supply not detected.\nCheck USB connection."
        #         )
        #     )
        #     return

        # # ✅ START PSU MONITORING *BEFORE* ANY STEPS
        # screen.start_device_monitoring()

        screen.check_abort()
        screen.log_signal.emit("Step 1: LOCAL/REMOTE (S23) → LOCAL", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.set_s23_local():
            screen.log_signal.emit("S23 successfully set to LOCAL", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set S23 to LOCAL", True)
            return

        QApplication.processEvents()
        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("Step 2: LOAD (S31) → 600 OHM", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.set_s31_600ohm():
            screen.log_signal.emit("S31 successfully set to 600 OHM", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set S31 to 600 OHM", True)
            return

        QApplication.processEvents()
        time.sleep(1)

        screen.check_abort()
        screen.log_signal.emit("Step 3: All switches DOWN", False)
        screen.logger.log("# WRITE SWITCH CONTROL LOGIC HERE", False)
        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("Step 4: Connecting the power supply connector (J58)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.set_j58_on():
            screen.log_signal.emit("J58 successfully set to ON", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set J58 to ON", True)
            return

        QApplication.processEvents()
        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("Step 5: Connecting the power supply connector (J60)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.set_j60_on():
            screen.log_signal.emit("J60 successfully set to ON", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set J60 to ON", True)
            return

        QApplication.processEvents()
        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("Step 6: Power Supply set to 28V (SOUR:VOLT 28.0)", False)
        screen.logger.log("# WRITE SCPI LOGIC HERE", False)
        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("Step 7: Live voltage monitoring enabled", False)
        screen.log_signal.emit("========== PSU AUTOMATION STARTING ==========", False)
        time.sleep(1)
        screen.start_device_monitoring()
        screen.check_abort()