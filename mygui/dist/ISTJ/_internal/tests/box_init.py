
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from core.paths import RESOURCES_DIR
from PyQt5.QtCore import QTimer
from devices.apx_analyzer import configure_apx_jb,generator_control,configure_apx
from core.oscilloscope_helper import set_ch1_ch2_scale_10v

def run_init_jbox(screen):
    """
    Connect the audio analyser generator output to MIC Connector J27.
    Connect the audio analyser input and oscilloscope to PH Connector J29.
    
    """
            
    screen.log_signal.emit("========== INITIALIZATION START ==========", False)
    time.sleep(0.1)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J61 Connector to J101 Connector using test cable.\n"
        "• Connect J62 Connector to J102 Connector using test cable.\n"
        "• Connect J64 Connector to J108 Connector using test cable.\n",
        RESOURCES_DIR / "j101.png","ok",None
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
        RESOURCES_DIR / "sbj101.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    if not screen.psu_inst:
        screen.psu_inst = screen.find_psu()

    if not screen.psu_inst:
        screen.log_signal.emit("ERROR: PSU not found", True)
        return
    screen.test_running = True



    # ▶ CHANNEL 3 SEQUENCE
    
    time.sleep(2)

    screen.check_abort()

    
    
    screen.log_signal.emit("COMMENCING TESTS UNDER NORMAL MODE", False)
    
    screen.log_signal.emit("audio analyser gen output set to 600ohm impedance balanced", False)
    configure_apx_jb(screen)
    # screen.check_abort()
    screen.log_signal.emit("Connecting the audio analyser generator output to MIC Connector J27", False)

    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_on):
        screen.log_signal.emit("J27 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J27", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s23_remote):
        screen.log_signal.emit("S23 Remote successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect S23 Remote", True)

    QApplication.processEvents()
    time.sleep(1)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s31_600ohm):
        screen.log_signal.emit("S31 successfully set to 600 OHM", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S31 to 600 OHM", True)
    QApplication.processEvents()
    time.sleep(1)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s28_600ohms):
        screen.log_signal.emit("S28 successfully set to 600 OHM", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S28 to 600 OHM", True)
    QApplication.processEvents()
    time.sleep(1)
    
        
    screen.log_signal.emit("switching S22 STBY to Up Position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s22_on):
        screen.log_signal.emit("S22 STBY successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S22 STBY to Up Position", True)
    screen.log_signal.emit("Switching S21 STBY to Up Position", False)    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s21_on):
        screen.log_signal.emit("S21 NORM successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S21 NORM to Up Position", True)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    

    
    
    
    screen.log_signal.emit("Connecting the audio analyser input and oscilloscope to PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
        screen.log_signal.emit("J29 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J29", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    screen.log_signal.emit("Power Supply set to 28V (SOUR:VOLT 28.0)", False)
    time.sleep(1)
    screen.check_abort()
    
    screen.log_signal.emit("Live voltage monitoring enabled", False)
    screen.log_signal.emit("========== PSU AUTOMATION STARTING ==========", False)



    # ▶ CHANNEL 1 SEQUENCE
    screen.worker_channel_1()
    time.sleep(2)
    if screen.psu_inst and screen.rm:
        screen.start_device_monitoring()
    screen.check_abort()
    
    screen.log_signal.emit("Connecting the power supply output to Connector J58", False)
    screen.log_signal.emit("J58 successfully Connected to power supply output", False)

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
        RESOURCES_DIR / "alh2.png","acknowledge",None
    )

    # ⏸ WAIT until operator clicks yes or no
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.check_abort()
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL switch to NORMAL.\n",
        RESOURCES_DIR / "normal.jpeg","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Switching S24 to UP position.", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s24_on):
        screen.log_signal.emit("S24 successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S24 to Up Position", True)
    #audio analyser gen output impedance to 600ohm bal input read AMPL ,set audio analyser gen output to 750 uvrms at 1kHz 
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    time.sleep(0.5)
    screen.log_signal.emit("Junction Box initialization complete", False)
    set_ch1_ch2_scale_10v(screen)

def run_init_jbox_stby(screen):
    """
    Connect the audio analyser generator output to MIC Connector J27.
    Connect the audio analyser input and oscilloscope to PH Connector J29.
    
    """
            
    screen.log_signal.emit("========== INITIALIZATION START ==========", False)
    time.sleep(0.1)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J61 Connector to J101 Connector using test cable.\n"
        "• Connect J62 Connector to J102 Connector using test cable.\n"
        "• Connect J64 Connector to J108 Connector using test cable.\n",
        RESOURCES_DIR / "j101.png","ok",None
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
        RESOURCES_DIR / "sbj101.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    if not screen.psu_inst:
        screen.psu_inst = screen.find_psu()

    if not screen.psu_inst:
        screen.log_signal.emit("ERROR: PSU not found", True)
        return
    screen.test_running = True



    # ▶ CHANNEL 3 SEQUENCE
    
    time.sleep(2)
    # if screen.psu_inst and screen.rm:
    #     screen.start_device_monitoring()
    screen.check_abort()
    
    
    # screen.log_signal.emit("COMMENCING TESTS UNDER NORMAL MODE", False)
    
    screen.log_signal.emit("audio analyser gen output set to 600ohm impedance balanced", False)
    configure_apx_jb(screen)
    # screen.check_abort()
    screen.log_signal.emit("Connecting the audio analyser generator output to MIC Connector J27", False)

    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_on):
        screen.log_signal.emit("J27 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J27", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s23_remote):
        screen.log_signal.emit("S23 Remote successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect S23 Remote", True)

    QApplication.processEvents()
    time.sleep(1)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s31_600ohm):
        screen.log_signal.emit("S31 successfully set to 600 OHM", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S31 to 600 OHM", True)
    QApplication.processEvents()
    time.sleep(1)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s28_600ohms):
        screen.log_signal.emit("S28 successfully set to 600 OHM", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S28 to 600 OHM", True)
    QApplication.processEvents()
    time.sleep(1)
    
        
    screen.log_signal.emit("switching S22 STBY to Up Position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s22_on):
        screen.log_signal.emit("S22 STBY successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S22 STBY to Up Position", True)
    screen.log_signal.emit("Switching S21 STBY to Up Position", False)    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s21_on):
        screen.log_signal.emit("S21 NORM successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S21 NORM to Up Position", True)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()

    screen.log_signal.emit("Connecting the audio analyser input and oscilloscope to PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
        screen.log_signal.emit("J29 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J29", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    screen.log_signal.emit("Power Supply set to 28V (SOUR:VOLT 28.0)", False)
    time.sleep(1)
    screen.check_abort()
    
    screen.log_signal.emit("Live voltage monitoring enabled", False)
    screen.log_signal.emit("========== PSU AUTOMATION STARTING ==========", False)
    set_ch1_ch2_scale_10v(screen)





    # ▶ CHANNEL 1 SEQUENCE
    screen.worker_channel_1()
    time.sleep(2)
    if screen.psu_inst and screen.rm:
        screen.start_device_monitoring()
    screen.check_abort()
    
    screen.log_signal.emit("Connecting the power supply output to Connector J58", False)
    screen.log_signal.emit("J58 successfully Connected to power supply output", False)

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
        "• STBY/NORMAL switch to STBY.\n"
        "• RAD PTT,SONIC and O/R are not illuminated .\n",
        RESOURCES_DIR / "alh2.png","acknowledge",None
    )

    # ⏸ WAIT until operator clicks yes or no
    screen.operator_event.wait()
    
    screen.log_signal.emit("Connecting the JACK J67 to Multimeter +ve lead ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j67_on):
        screen.log_signal.emit("J67 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J67 to Multimeter +ve lead", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL switch to STBY.\n",
        RESOURCES_DIR / "stby.jpeg","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Switching the S25 STBY PWR to UP position ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s25_on):
        screen.log_signal.emit("S25 successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S25 to Up Position", True)

    QApplication.processEvents()
    time.sleep(1)
    
    #audio analyser gen output impedance to 600ohm bal input read AMPL ,set audio analyser gen output to 750 uvrms at 1kHz 
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    time.sleep(0.5)
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

        screen.log_signal.emit("========== INITIALIZATION START ==========", False)
        time.sleep(0.1)
        # 🛑 PAUSE POINT
        screen.operator_event.clear()
        screen.show_popup_signal.emit(
            "⚠ Operator Action Required",
            "• Connect J65 Connector to J101 Connector using test cable.\n"
            "• Connect J66 Connector to J102 Connector using test cable.\n"
            "• Connect TJ-160 connector to J101 Connector.\n",
            RESOURCES_DIR / "sbj101.png","ok",None
        )

        # ⏸ WAIT until operator clicks OK
        screen.operator_event.wait()
        if not screen.psu_inst:
            screen.psu_inst = screen.find_psu()

        if not screen.psu_inst:
            screen.log_signal.emit("ERROR: PSU not found", True)
            return
        screen.test_running = True
        
        time.sleep(2)
        screen.check_abort()

        screen.log_signal.emit("Switching all Relays to Default state", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
            screen.log_signal.emit("All relays successfully set to default states", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set all relays to default states", True)

        screen.log_signal.emit("COMMENCING TESTS UNDER NORMAL MODE", False)
        
        screen.log_signal.emit("audio analyser gen output set to 50ohm impedance balanced", False)
        configure_apx(screen)

        screen.check_abort()
        screen.log_signal.emit("LOCAL/REMOTE (S23) → LOCAL", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_s23_local):
            screen.log_signal.emit("S23 successfully set to LOCAL", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set S23 to LOCAL", True)

        QApplication.processEvents()
        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("LOAD (S31) → 600 OHM", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_s31_600ohm):
            screen.log_signal.emit("S31 successfully set to 600 OHM", False)
        else:
            screen.log_signal.emit("ERROR: Failed to set S31 to 600 OHM", True)

        QApplication.processEvents()
        time.sleep(1)

        screen.check_abort()
        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("Connecting the power supply connector (J58)", False)
        screen.log_signal.emit("J58 successfully Connected", False)
        

        QApplication.processEvents()
        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("Connecting the power supply connector (J60)", False)
        screen.log_signal.emit("J60 successfully Connected", False)

        time.sleep(1)
        screen.check_abort()
        screen.log_signal.emit("Live voltage monitoring enabled", False)

        screen.log_signal.emit("========== PSU AUTOMATION STARTING ==========", False)
        time.sleep(1)
        screen.worker_channel_1()
        time.sleep(2)
        if screen.psu_inst and screen.rm:
            screen.start_device_monitoring()
        screen.check_abort()
        set_ch1_ch2_scale_10v(screen)