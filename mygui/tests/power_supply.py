import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from core.paths import RESOURCES_DIR
from core.dmm_reader import read_voltage
from core.excel_logger import write_excel_dynamic,write_excel




def run_norm(screen):
    screen.log_signal.emit("==========Commencing power supply test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)

    
    screen.log_signal.emit("Step 1: Turning the power supply output ON and switching S21 NORM to Up Position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s21_on():
        screen.log_signal.emit("S21 NORM successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S21 NORM to Up Position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS10 and DS11 indicators should illuminate red.\n",
        RESOURCES_DIR / "ds10_indi.jpg","yes_no",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F12",operator)   # YES
    write_excel("K12",result)     # PASS 
    screen.check_abort()
    
    #power supply current meter should read between 1.3A to 2.0A
    #multimeter should read 11+-1.1 Vdc
    result=read_voltage(screen,"Power Supply Voltage Check", "9.9V","12.1V")
    if result:
        write_excel_dynamic("F14",result["observation"])
        write_excel("K14",result["result"])
    screen.log_signal.emit("Step 2: Disconnecting the JACK J67 from Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j67_off():
        screen.log_signal.emit("J67 successfully Disconnected from Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J67 from Multimeter +ve lead", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Step 3: Connecting the JACK J68 to Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j68_on():
        screen.log_signal.emit("J68 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J68 to Multimeter +ve lead", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    #multimeter should read -11 Vdc +-1.1V
    result=read_voltage(screen,"J68 Multimeter Voltage Check", "-12.1","-9.9V")
    if result:
        write_excel_dynamic("F15",result["observation"])
        write_excel("K15",result["result"])
    
    screen.log_signal.emit("Step 4: Disconnecting the JACK J68 from Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j68_off():
        screen.log_signal.emit("J68 successfully Disconnected from Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J68 from Multimeter +ve lead", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("==========Successfully Completed power supply test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    
    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing power supply test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
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
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS12 and DS13 indicators should illuminate red.\n",
        RESOURCES_DIR / "ds12.png","yes_no",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F16",operator)   # YES
    write_excel("K16",result)     # PASS 
    
    screen.check_abort()
    
    screen.log_signal.emit("Step 4: Turning the power supply output ON and switching S21 NORM to Up Position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s21_on():
        screen.log_signal.emit("S21 NORM successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S21 NORM to Up Position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    #power supply current meter should read between 1.3A to 2.0A
    
    screen.log_signal.emit("Step 5: Connecting the JACK J70 to Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j70_on():
        screen.log_signal.emit("J70 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J70 to Multimeter +ve lead", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    #multimeter should read +11 Vdc +-1.1V
    result=read_voltage(screen,"J70 Multimeter Voltage Check", "9.9V","12.1V")
    if result:
        write_excel_dynamic("F18",result["observation"])
        write_excel("K18",result["result"])
    screen.log_signal.emit("Step 6: Disconnecting the JACK J70 from Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j70_off():
        screen.log_signal.emit("J70 successfully Disconnected from Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J70 from Multimeter +ve lead", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Step 5: Connecting the JACK J71 to Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j71_on():
        screen.log_signal.emit("J71 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J71 to Multimeter +ve lead", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    #multimeter should read -11 Vdc +-1.1V
    result=read_voltage(screen,"J71 Multimeter Voltage Check", "-12.1V","-9.9V")
    if result:
        write_excel_dynamic("F19",result["observation"])
        write_excel("K19",result["result"])
    screen.log_signal.emit("Step 6: Disconnecting the JACK J71 from Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j71_off():
        screen.log_signal.emit("J71 successfully Disconnected from Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J71 from Multimeter +ve lead", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("==========Successfully Completed power supply test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    
    
    
    
    
    