from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from core.excel_logger import write_excel
def run_stby(screen):
    screen.log_signal.emit("==========COMMENCING MICROPHONE AUDIO TEST==========", False)

    screen.log_signal.emit(
        "OPERATOR ACTION: Turn the MIC MODE knob fully clockwise (CW).",
        False
    )

    screen.log_signal.emit(
        "AUDIO ANALYSER NOTE: MIC MODE set to maximum (Fully CW) before test start.",
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
    screen.log_signal.emit("Step 1: Turning ICS(S32) to ON.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s32_on():
        screen.log_signal.emit("S32 successfully set to ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to ON", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    screen.log_signal.emit("Step 2: Turning ICS(S32) to OFF.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s32_off():
        screen.log_signal.emit("S32 successfully set to OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to OFF", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    screen.log_signal.emit("Step 3: Turning TX SWITCH (S30) to OFF.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("TX SWITCH (S30) successfully set to OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to OFF", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Step 4: Turning LOAD Switch (S31) to NEUTRAL.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s31_neutral():
        screen.log_signal.emit("S31 successfully set to NEUTRAL", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to NEUTRAL", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect the headset jack J28 using headset adapter\n"
        "• Turn the MIC MODE knob fully COUNTERCLOCKWISE (CCW)\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Headset jack J28 connected using headset adapter", False)
    
    time.sleep(2)
    
    
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
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E19",operator)   # YES
    write_excel("F19",result)     # PASS
    
    
    screen.log_signal.emit("Step 5: Disconnecting J28 Headset jack.", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect the headset jack J28 using headset adapter\n",
        None,"ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("J28 successfully disconnected", False)
    time.sleep(2)

    
    screen.log_signal.emit("Step 6: Turning LOAD Switch (S31) to 600 ohms.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s31_600ohm():
        screen.log_signal.emit("S31 successfully set to 600 ohms", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to 600 ohms", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Step 7: Increasing audio analyser MONITOR volume until tone is audible.", False)
    
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ IS THE TONE AUDIBLE?",
        "• Increasing audio analyser MONITOR volume until tone is audible.\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",
        10
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set MIC MODE to 12'o clock position.\n",
        RESOURCES_DIR / "knob_12oclock.png",
        "ok",None
    )


    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(5)
    screen.log_signal.emit("Step 8: Decreasing audio analyser Generator Output until tone is not audible.", False)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ IS THE TONE NOT AUDIBLE?",
        "• Decreasing audio analyser Generator Output until tone is not audible.\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",
        10
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(5)
    screen.log_signal.emit("Step 9: Increasing audio analyser Generator Output until tone is audible.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ IS THE TONE AUDIBLE?",
        "• Increasing audio analyser Generator Output until tone is audible.\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",
        10
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Step 10: decreasing audio analyser Monitor volume.", False)

    time.sleep(2)
    
    screen.log_signal.emit("Step 11: Disconnecting MIC Connector (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j13_off():
        screen.log_signal.emit("J13 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J13", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 12: Connecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j14_on():
        screen.log_signal.emit("J14 successfully connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect J14", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
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
    
    screen.log_signal.emit("✓ MICROPHONE AUDIO TEST COMPLETED", False)


def run_norm(screen):
    
    screen.log_signal.emit("==========COMMENCING MICROPHONE AUDIO TEST==========", False)

    screen.log_signal.emit(
        "OPERATOR ACTION: Turn the MIC MODE knob fully clockwise (CW).",
        False
    )

    screen.log_signal.emit(
        "AUDIO ANALYSER NOTE: MIC MODE set to maximum (Fully CW) before test start.",
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
    screen.log_signal.emit("Step 1: Turning ICS(S32) to ON.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s32_on():
        screen.log_signal.emit("S32 successfully set to ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to ON", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    screen.log_signal.emit("Step 2: Turning ICS(S32) to OFF.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s32_off():
        screen.log_signal.emit("S32 successfully set to OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to OFF", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    screen.log_signal.emit("Step 3: Turning TX SWITCH (S30) to OFF.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("TX SWITCH (S30) successfully set to OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to OFF", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Step 4: Turning LOAD Switch (S31) to NEUTRAL.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s31_neutral():
        screen.log_signal.emit("S31 successfully set to NEUTRAL", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to NEUTRAL", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect the headset jack J28 using headset adapter\n"
        "• Turn the MIC MODE knob fully COUNTERCLOCKWISE (CCW)\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    
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
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E18",operator)   # YES
    write_excel("F18",result)     # PASS
    
    
    screen.log_signal.emit("Step 5: Disconnecting J28 Headset jack.", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect the headset jack J28 using headset adapter\n",
        None,"ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("J28 successfully disconnected", False)
    time.sleep(2)
    
    screen.log_signal.emit("Step 6: Turning LOAD Switch (S31) to 600 ohms.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s31_600ohm():
        screen.log_signal.emit("S31 successfully set to 600 ohms", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to 600 ohms", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Step 7: Increasing audio analyser MONITOR volume until tone is audible.", False)
    
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ IS THE TONE AUDIBLE?",
        "• Increasing audio analyser MONITOR volume until tone is audible.\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",
        10
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set MIC MODE to 12'o clock position.\n",
        RESOURCES_DIR / "knob_12oclock.png",
        "ok",None
    )


    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(5)
    screen.log_signal.emit("Step 8: Decreasing audio analyser Generator Output until tone is not audible.", False)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ IS THE TONE NOT AUDIBLE?",
        "• Decreasing audio analyser Generator Output until tone is not audible.\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",
        10
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(5)
    screen.log_signal.emit("Step 9: Increasing audio analyser Generator Output until audible.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ IS THE TONE AUDIBLE?",
        "• Increasing audio analyser Generator Output until tone is audible.\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",
        10
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Step 10: decreasing audio analyser Monitor volume.", False)

    time.sleep(2)
    
    screen.log_signal.emit("Step 11: Disconnecting MIC Connector (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j13_off():
        screen.log_signal.emit("J13 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J13", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 12: Connecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j14_on():
        screen.log_signal.emit("J14 successfully connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect J14", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
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
    
    #press audio analyser gen load
    
    screen.log_signal.emit("✓ MICROPHONE AUDIO TEST COMPLETED", False)