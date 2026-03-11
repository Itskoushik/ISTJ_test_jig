from core.paths import RESOURCES_DIR
import time
from core.stm32_commands import STM32RelayController
from PyQt5.QtWidgets import (
    QApplication
)
from core.excel_logger import write_excel

def run_stby(screen):
    screen.log_signal.emit("==========COMMENCING VOS DELAY TEST==========", False)
            
    #audio analyser output set to 750uvrms at 1khz
    
    screen.log_signal.emit("Step 1: Disconnecting NORM PHONES Connector (J15)  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_off():
        screen.log_signal.emit("J15 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J15.", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Step 2: Connecting STBY PHONES Connector (J16)  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j16_on():
        screen.log_signal.emit("J16 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J16.", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Step 3: Increasing audio analyser MONITOR volume until audible.", False)
    
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ IS THE TONE AUDIBLE?",
        "• Increasing audio analyser MONITOR volume until audible.\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",
        10
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit(
        "OPERATOR ACTION: Turn the MIC MODE knob fully clockwise (CW).",
        False
    )
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully CLOCKWISE (CW)\n"
        "• Ensure microphone is connected properly\n",
        RESOURCES_DIR / "knob_fcw.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ OPERATOR ACTION REQUIRED",
        "• Did Audio Analyser MONITOR audio get mute Between 0.5 - 1.5 seconds?\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E34",operator)   # YES
    write_excel("F34",result)     # PASS
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully COUNTERCLOCKWISE (CCW)\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("✓ VOS DELAY TEST COMPLETED", False)






def run_norm(screen):


    screen.log_signal.emit("==========COMMENCING VOS DELAY TEST==========", False)
            
    #audio analyser output set to 750uvrms at 1khz
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Step 1: Increasing audio analyser MONITOR volume until audible.", False)
    
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ IS THE TONE AUDIBLE?",
        "• Increasing audio analyser MONITOR volume until audible.\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",
        10
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit(
        "OPERATOR ACTION: Turn the MIC MODE knob fully clockwise (CW).",
        False
    )
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully CLOCKWISE (CW)\n",
        RESOURCES_DIR / "knob_fcw.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ OPERATOR ACTION REQUIRED",
        "• Did Audio Analyser MONITOR audio get mute Between 0.5 - 1.5 seconds?\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E33",operator)   # YES
    write_excel("F33",result)     # PASS
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully COUNTERCLOCKWISE (CCW)\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("✓ VOS DELAY TEST COMPLETED", False)