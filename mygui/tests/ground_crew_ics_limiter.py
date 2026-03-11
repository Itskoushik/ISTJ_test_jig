import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from core.excel_logger import write_excel

def run_norm(screen):
    screen.log_signal.emit("==========Commencing GROUND CREW ICS LIMITER test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    #turn the audio analyser gen output off.
    
    screen.log_signal.emit("Setting LOAD Switch S28 to the Center position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s28_neutral():
        screen.log_signal.emit("LOAD Switch S28 successfully set to Center position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set LOAD Switch S28 to Center position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connecting Headset Adapter to HEADSET J25", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j25_on():
        screen.log_signal.emit("HEADSET J25 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect HEADSET J25", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Speak into the microphone\n"
        "• Audio with no unusual noises or disruptions should be heard in the headset\n",
        RESOURCES_DIR / "microphone.png",
        "yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("F400",operator)   # YES
    write_excel("K400",result)     # PASS 

    screen.log_signal.emit("Disconnecting Headset Adapter from HEADSET J25", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j25_off():
        screen.log_signal.emit("HEADSET J25 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect HEADSET J25", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting LOAD Switch S28 to the 600 ohms", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s28_600ohms():
        screen.log_signal.emit("LOAD Switch S28 successfully set to 600 ohms", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set LOAD Switch S28 to 600 ohms", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #Turn the Audio analyser generator Output ON
    
    
    screen.log_signal.emit("==========Successfully completed GROUND CREW ICS LIMITER test===========", False)
    

    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing GROUND CREW ICS LIMITER test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    #turn the audio analyser gen output off.
    
    screen.log_signal.emit("Setting LOAD Switch S28 to the Center position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s28_neutral():
        screen.log_signal.emit("LOAD Switch S28 successfully set to Center position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set LOAD Switch S28 to Center position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connecting Headset Adapter to HEADSET J25", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j25_on():
        screen.log_signal.emit("HEADSET J25 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect HEADSET J25", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Speak into the microphone\n"
        "• Audio with no unusual noises or disruptions should be heard in the headset\n",
        RESOURCES_DIR / "microphone.png",
        "yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("F401",operator)   # YES
    write_excel("K401",result)     # PASS 

    screen.log_signal.emit("Disconnecting Headset Adapter from HEADSET J25", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j25_off():
        screen.log_signal.emit("HEADSET J25 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect HEADSET J25", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting LOAD Switch S28 to the 600 ohms", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s28_600ohms():
        screen.log_signal.emit("LOAD Switch S28 successfully set to 600 ohms", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set LOAD Switch S28 to 600 ohms", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #Turn the Audio analyser generator Output ON
    
    
    screen.log_signal.emit("==========Successfully completed GROUND CREW ICS LIMITER test===========", False)