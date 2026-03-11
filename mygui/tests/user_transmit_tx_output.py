import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from core.excel_logger import write_excel_dynamic   
def run_norm(screen):
    screen.log_signal.emit("==========Commencing TX OUTPUT LEVEL test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    #j07
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to in position .\n",
        RESOURCES_DIR /"vuhf1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT Connector J7", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j07_on():
        screen.log_signal.emit("MIC OUT Connector J7 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT Connector J7", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS1 Should illuminate red .\n",
        RESOURCES_DIR /"ds1.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to OUT position .\n",
        RESOURCES_DIR /"vuhf1.jpg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT Connector J7", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j07_off():
        screen.log_signal.emit("MIC OUT Connector J7 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT Connector J7", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J8 test
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to in position .\n",
        RESOURCES_DIR /"vuhf2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT COM 2 Connector J8", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j08_on():
        screen.log_signal.emit("MIC OUT COM 2 Connector J8 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT COM 2 Connector J8", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS2 Should illuminate red .\n",
        RESOURCES_DIR /"ds2.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("G87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to OUT position .\n",
        RESOURCES_DIR /"vuhf2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 2 Connector J8", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j08_off():
        screen.log_signal.emit("MIC OUT COM 2 Connector J8 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 2 Connector J8", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J9 test
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to in position .\n",
        RESOURCES_DIR /"hf.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT COM 3 Connector J9", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j09_on():
        screen.log_signal.emit("MIC OUT COM 3 Connector J9 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT COM 3 Connector J9", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS3 Should illuminate red .\n",
        RESOURCES_DIR /"ds3.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("H87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to OUT position .\n",
        RESOURCES_DIR /"hf.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 3 Connector J9", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j09_off():
        screen.log_signal.emit("MIC OUT COM 3 Connector J9 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 3 Connector J9", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J10 test 
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 1 to in position .\n",
        RESOURCES_DIR /"spare1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT COM 4 Connector J10", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j10_on():
        screen.log_signal.emit("MIC OUT COM 4 Connector J10 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT COM 4 Connector J10", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS4 Should illuminate red .\n",
        RESOURCES_DIR /"ds4.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("I87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 1 to OUT position .\n",
        RESOURCES_DIR /"spare1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 4 Connector J10", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j10_off():
        screen.log_signal.emit("MIC OUT COM 4 Connector J10 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 4 Connector J10", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #j11 test
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 2 to in position .\n",
        RESOURCES_DIR /"spare2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT COM 5 Connector J11", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j11_on():
        screen.log_signal.emit("MIC OUT COM 5 Connector J11 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT COM 5 Connector J11", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS5 Should illuminate red .\n",
        RESOURCES_DIR /"ds5.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("J87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 2 to OUT position .\n",
        RESOURCES_DIR /"spare2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 5 Connector J11", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j11_off():
        screen.log_signal.emit("MIC OUT COM 5 Connector J11 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 5 Connector J11", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting the switch S33 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to Down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)

    screen.log_signal.emit("==========Successfully Completed TX OUTPUT LEVEL test===========", False)
    time.sleep(0.5)

    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing TX OUTPUT LEVEL test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    #j07
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to in position .\n",
        RESOURCES_DIR /"vuhf1.jpg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT Connector J7", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j07_on():
        screen.log_signal.emit("MIC OUT Connector J7 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT Connector J7", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS1 Should illuminate red .\n",
        RESOURCES_DIR /"ds1.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to OUT position .\n",
        RESOURCES_DIR /"vuhf1.jpg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT Connector J7", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j07_off():
        screen.log_signal.emit("MIC OUT Connector J7 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT Connector J7", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J8 test
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to in position .\n",
        RESOURCES_DIR /"vuhf2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT COM 2 Connector J8", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j08_on():
        screen.log_signal.emit("MIC OUT COM 2 Connector J8 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT COM 2 Connector J8", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS2 Should illuminate red .\n",
        RESOURCES_DIR /"ds2.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("G88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to OUT position .\n",
        RESOURCES_DIR /"vuhf2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 2 Connector J8", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j08_off():
        screen.log_signal.emit("MIC OUT COM 2 Connector J8 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 2 Connector J8", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J9 test
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to in position .\n",
        RESOURCES_DIR /"hf.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT COM 3 Connector J9", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j09_on():
        screen.log_signal.emit("MIC OUT COM 3 Connector J9 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT COM 3 Connector J9", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS3 Should illuminate red .\n",
        RESOURCES_DIR /"ds3.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("H88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to OUT position .\n",
        RESOURCES_DIR /"hf.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 3 Connector J9", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j09_off():
        screen.log_signal.emit("MIC OUT COM 3 Connector J9 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 3 Connector J9", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J10 test 
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 1 to in position .\n",
        RESOURCES_DIR /"spare1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT COM 4 Connector J10", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j10_on():
        screen.log_signal.emit("MIC OUT COM 4 Connector J10 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT COM 4 Connector J10", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS4 Should illuminate red .\n",
        RESOURCES_DIR /"ds4.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("I88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 1 to OUT position .\n",
        RESOURCES_DIR /"spare1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 4 Connector J10", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j10_off():
        screen.log_signal.emit("MIC OUT COM 4 Connector J10 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 4 Connector J10", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #j11 test
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 2 to in position .\n",
        RESOURCES_DIR /"spare2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connect the Audio analyser input and oscilloscope to the MIC OUT COM 5 Connector J11", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j11_on():
        screen.log_signal.emit("MIC OUT COM 5 Connector J11 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT COM 5 Connector J11", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS5 Should illuminate red .\n",
        RESOURCES_DIR /"ds5.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("J88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 2 to OUT position .\n",
        RESOURCES_DIR /"spare2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #audio analyser should read >350 mVrms with <10% THD+N
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 5 Connector J11", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j11_off():
        screen.log_signal.emit("MIC OUT COM 5 Connector J11 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 5 Connector J11", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting the switch S33 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to Down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)

    screen.log_signal.emit("==========Successfully Completed TX OUTPUT LEVEL test===========", False)
    time.sleep(0.5)