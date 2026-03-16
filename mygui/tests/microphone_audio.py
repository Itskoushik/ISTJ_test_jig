from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from core.excel_logger import write_excel
from devices.apx_analyzer import read_apx_meter,generator_control,audible_tone_check,audible_reduce_until_silent,audible_increase_until_audible,reduce_monitor_gain_to_x1
def run_stby(screen):
    screen.log_signal.emit("==========COMMENCING MICROPHONE AUDIO TEST==========", False)
    
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E11", data["observation"])   # measured value
        write_excel("E11", data["value"])         # raw vrms
        write_excel("F11", data["result"])        # PASS / FAIL
        
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully CLOCKWISE (CW)\n",
        RESOURCES_DIR / "knob_fcw.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    data = read_apx_meter(screen, max_v="2", unit="mvrms")
    if data:
        # write_excel("E13", data["observation"])   # measured value
        write_excel("E13", data["value"])         # raw vrms
        write_excel("F13", data["result"])        # PASS / FAIL
    screen.log_signal.emit("Step 1: Turning ICS(S32) to ON.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s32_on():
        screen.log_signal.emit("S32 successfully set to ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to ON", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E15", data["observation"])   # measured value
        write_excel("E15", data["value"])         # raw vrms
        write_excel("F15", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Step 2: Turning ICS(S32) to OFF.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s32_off():
        screen.log_signal.emit("S32 successfully set to OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to OFF", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Step 3: Turning TX SWITCH (S30) to ON.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("TX SWITCH (S30) successfully set to ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to ON", True)
        
    
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E17", data["observation"])   # measured value
        write_excel("E17", data["value"])         # raw vrms
        write_excel("F17", data["result"])        # PASS / FAIL
        
    screen.log_signal.emit("Step 4: Turning TX SWITCH (S30) to OFF.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("TX SWITCH (S30) successfully set to OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to OFF", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen,state="off")
    screen.log_signal.emit("Step 5: Turning LOAD Switch (S31) to NEUTRAL.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s31_neutral():
        screen.log_signal.emit("S31 successfully set to NEUTRAL", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to NEUTRAL", True)
        

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
    
    
    screen.log_signal.emit("Step 6: Disconnecting J28 Headset jack.", False)
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

    
    screen.log_signal.emit("Step 7: Turning LOAD Switch (S31) to 600 ohms.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s31_600ohm():
        screen.log_signal.emit("S31 successfully set to 600 ohms", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to 600 ohms", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen,state="on")
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Step 8: Increasing audio analyser MONITOR volume until tone is audible.", False)
    time.sleep(2)
    data = audible_tone_check(screen)

    operator = data["operator"]
    result = data["result"]
    gain_used=data["gain"]

    
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
    screen.log_signal.emit("Step 9: Decreasing audio analyser Generator Output until tone is not audible.", False)
    
    audible_reduce_until_silent(screen)
    time.sleep(2)

    audible_increase_until_audible(screen)
    data=read_apx_meter(screen,min_v="100", max_v="500", unit="uVrms")
    if data:
        write_excel("E21", data["value"])         # raw vrms at audible threshold
        write_excel("F21", data["result"])        # PASS / FAIL
    time.sleep(2)
    screen.log_signal.emit("Step 10: Increasing audio analyser Generator Output until tone is audible.", False)

    screen.log_signal.emit("Step 11: decreasing audio analyser Monitor volume.", False)

    time.sleep(2)
    reduce_monitor_gain_to_x1(screen, gain_used)
    time.sleep(1)
    
    screen.log_signal.emit("Step 12: Disconnecting MIC Connector (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j13_off():
        screen.log_signal.emit("J13 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J13", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 13: Connecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j14_on():
        screen.log_signal.emit("J14 successfully connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect J14", True)
        

    QApplication.processEvents()
    time.sleep(2)
    generator_control(screen,level="750.0 uVrms",state="on")
    time.sleep(1)
    data=read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        write_excel("E23", data["value"])         # raw vrms at 750 uVrms gen level
        write_excel("F23", data["result"])        # PASS / FAIL
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
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E10", data["observation"])   # measured value
        write_excel("E10", data["value"])         # raw vrms
        write_excel("F10", data["result"])        # PASS / FAIL 
    time.sleep(1)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully CLOCKWISE (CW)\n",
        RESOURCES_DIR / "knob_fcw.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    data = read_apx_meter(screen, max_v="2", unit="mvrms")
    if data:
        # write_excel("E12", data["observation"])   # measured value
        write_excel("E12", data["value"])         # raw vrms
        write_excel("F12", data["result"])        # PASS / FAIL
    time.sleep(1)
    screen.log_signal.emit("Step 1: Turning ICS(S32) to ON.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s32_on():
        screen.log_signal.emit("S32 successfully set to ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to ON", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E14", data["observation"])   # measured value
        write_excel("E14", data["value"])         # raw vrms
        write_excel("F14", data["result"])        # PASS / FAIL
    
    time.sleep(1)
    screen.log_signal.emit("Step 2: Turning ICS(S32) to OFF.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s32_off():
        screen.log_signal.emit("S32 successfully set to OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to OFF", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Step 3: Turning TX SWITCH (S30) to ON.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("TX SWITCH (S30) successfully set to ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to ON", True)
        
    
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E16", data["observation"])   # measured value
        write_excel("E16", data["value"])         # raw vrms
        write_excel("F16", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Step 4: Turning TX SWITCH (S30) to OFF.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("TX SWITCH (S30) successfully set to OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to OFF", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    generator_control(screen,state="off")
    
    screen.log_signal.emit("Step 5: Turning LOAD Switch (S31) to NEUTRAL.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s31_neutral():
        screen.log_signal.emit("S31 successfully set to NEUTRAL", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to NEUTRAL", True)
        

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
    
    time.sleep(1)
    screen.log_signal.emit("Step 6: Disconnecting J28 Headset jack.", False)
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
    
    screen.log_signal.emit("Step 7: Turning LOAD Switch (S31) to 600 ohms.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s31_600ohm():
        screen.log_signal.emit("S31 successfully set to 600 ohms", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to 600 ohms", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen,state="on")
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Step 8: Increasing audio analyser MONITOR volume until tone is audible.", False)
    
    time.sleep(2)

    data = audible_tone_check(screen)

    operator = data["operator"]
    result = data["result"]
    gain_used=data["gain"]

    print("Operator:", operator)
    print("Result:", result)
    
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
    
    time.sleep(2)
    screen.log_signal.emit("Step 9: Decreasing audio analyser Generator Output until tone is not audible.", False)
    
    audible_reduce_until_silent(screen)

    time.sleep(2)

    audible_increase_until_audible(screen)
    
    time.sleep(2)
    data=read_apx_meter(screen,min_v="100", max_v="500", unit="uVrms")
    if data:
        write_excel("E20", data["value"])         # raw vrms at audible threshold
        write_excel("F20", data["result"])        # PASS / FAIL
    time.sleep(2)
    screen.log_signal.emit("Step 11: decreasing audio analyser Monitor volume.", False)

    time.sleep(2)
    reduce_monitor_gain_to_x1(screen, gain_used)
    # ⏸ WAIT until operator clicks OK
   
    time.sleep(0.5)
    
    
    screen.log_signal.emit("Step 12: Disconnecting MIC Connector (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j13_off():
        screen.log_signal.emit("J13 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J13", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 13: Connecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j14_on():
        screen.log_signal.emit("J14 successfully connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect J14", True)
        

    QApplication.processEvents()
    time.sleep(2)
    generator_control(screen,level="750.0 uVrms",state="on")
    time.sleep(1)
    data=read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        write_excel("E22", data["value"])         # raw vrms at 750 uVrms gen level
        write_excel("F22", data["result"])        # PASS / FAIL
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