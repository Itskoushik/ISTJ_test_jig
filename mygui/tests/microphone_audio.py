from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
import core.dmm_reader as dmm_reader
from core.excel_logger import write_excel
from devices.apx_analyzer import read_apx_meter,generator_control,audible_tone_check,audible_reduce_until_silent,audible_increase_until_audible,reduce_monitor_gain_to_x1
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v,autoset_oscilloscope
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("MICROPHONE AUDIO TEST (STBY)")
    screen.log_signal.emit("==========COMMENCING MICROPHONE AUDIO TEST==========", False)
    
    
    #audio analyser output set to 750uvrms at 1khz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    time.sleep(2)
    screen.check_abort()
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Disconnecting NORM PHONES Connector (J15)  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_j15_off):
        screen.log_signal.emit("NORM PHONES Connector J15 successfully Disconnected", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NORM PHONES Connector J15.", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Connecting STBY PHONES Connector (J16)  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j16_on):
        screen.log_signal.emit("STBY PHONES Connector J16 successfully Connected", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect STBY PHONES Connector J16.", True)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s35_on):
        screen.log_signal.emit("S35/SB sel successfully set to Up position", False)
        time.sleep(0.5)   
        screen.check_abort()                      
    else:
        screen.log_signal.emit("ERROR: Failed to set S35/SB sel to Up position", True)
        

    time.sleep(0.5)
    screen.check_abort()
    
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E11", data["observation"])   # measured observation
        write_excel("E11", data["observation"])         # raw vrms
        write_excel("F11", data["result"])        # PASS / FAIL
        
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob CW\n",
        RESOURCES_DIR / "knob_fcw.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.check_abort()
    screen.log_signal.emit("MIC MODE knob set to CW", False)
    time.sleep(1)
    data = read_apx_meter(screen, max_v="2", unit="mvrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel("E13", data["observation"])         # raw vrms
        write_excel("F13", data["result"])        # PASS / FAIL
    screen.log_signal.emit("Turning ICS(S32) to ON.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s32_on):
        screen.log_signal.emit("S32 successfully set to Up position", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to Up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E15", data["observation"])   # measured observation
        write_excel("E15", data["observation"])         # raw vrms
        write_excel("F15", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Turning ICS(S32) to Down Position.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s32_off):
        screen.log_signal.emit("S32 successfully set to Down Position", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to Down Position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Turning TX SWITCH (S30) to ON.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("TX SWITCH (S30) successfully set to Up position", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to Up position", True)
        
    
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E17", data["observation"])   # measured observation
        write_excel("E17", data["observation"])         # raw vrms
        write_excel("F17", data["result"])        # PASS / FAIL
        
    screen.log_signal.emit("Turning TX SWITCH (S30) to Down position.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("TX SWITCH (S30) successfully set to Down Position", False)
        time.sleep(0.5)
        screen.check_abort()
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to Down Position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    # generator_control(screen,state="off")
    screen.log_signal.emit("Turning LOAD Switch (S31) to NEUTRAL.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s31_neutral):
        screen.log_signal.emit("S31 successfully set to NEUTRAL", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to NEUTRAL", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("J27 BENCH MIC successfully Disconnected", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J27 BENCH MIC", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    autoset_oscilloscope(screen)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect the headset jack J28 using headset adapter\n"
        "• Turn the MIC MODE knob CCW\n",
        RESOURCES_DIR / "knob_headset.jpg","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Headset jack J28 connected using headset adapter", False)
    screen.log_signal.emit("Turned MIC MODE knob CCW", False)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
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
    screen.check_abort()
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E19",operator)   # YES
    write_excel("F19",result)     # PASS
    
    
    screen.log_signal.emit("Disconnecting J28 Headset jack.", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect the headset jack J28 using headset adapter\n",
        RESOURCES_DIR / "headset_rem.jpg","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.check_abort()
    screen.log_signal.emit("J28 headset jack successfully disconnected", False)
    time.sleep(2)
    set_ch1_ch2_scale_10v(screen)

    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_on):
        screen.log_signal.emit("J27 BENCH MIC successfully Connected", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J27 BENCH MIC.", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Turning LOAD Switch (S31) to 600 ohms.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s31_600ohm):
        screen.log_signal.emit("S31 successfully set to 600 ohms", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to 600 ohms", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    # generator_control(screen,state="on")
    
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Increasing audio analyser MONITOR volume until tone is audible.", False)
    time.sleep(2)
    data = audible_tone_check(screen)

    operator = data["operator"]
    result = data["result"]
    gain_used=data["gain"]

    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.check_abort()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set MIC MODE to 12'o clock position.\n",
        RESOURCES_DIR / "knob_12oclock.png",
        "ok",None
    )


    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.check_abort()
    screen.log_signal.emit("MIC MODE knob set to 12'o clock position", False)
    time.sleep(5)
    screen.log_signal.emit("Decreasing audio analyser Generator Output until tone is not audible.", False)
    
    audible_reduce_until_silent(screen)
    time.sleep(2)
    screen.check_abort()
    screen.log_signal.emit("Increasing audio analyser Generator Output until tone is audible.", False)

    data=audible_increase_until_audible(screen)
    if data:
        write_excel("E21", data["threshold"])         # raw vrms at audible threshold
        write_excel("F21", data["result"])        # PASS / FAIL
    
    time.sleep(2)
    screen.check_abort()

    screen.log_signal.emit("decreasing audio analyser Monitor volume.", False)

    time.sleep(2)
    reduce_monitor_gain_to_x1(screen, gain_used)
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("Disconnecting MIC Connector (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j13_off):
        screen.log_signal.emit("MIC Connector J13 successfully disconnected", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect MIC Connector J13", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j14_on):
        screen.log_signal.emit("HOT MIC Connector J14 successfully connected", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect HOT MIC Connector J14", True)
        

    QApplication.processEvents()
    time.sleep(2)
    screen.check_abort()
    generator_control(screen,level="750.0 uVrms",frequency=1000)
    time.sleep(1)
    data=read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        write_excel("E23", data["observation"])         # raw vrms at 750 uVrms gen level
        write_excel("F23", data["result"])        # PASS / FAIL
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully CCW.\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("MIC MODE knob set to CCW", False)
    screen.check_abort()
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s35_off):
        screen.log_signal.emit("S35/SB sel successfully set to Down Position", False)
        time.sleep(0.5)                         
    else:
        screen.log_signal.emit("ERROR: Failed to set S35/SB sel to Down Position", True)
        

    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("============ MICROPHONE AUDIO TEST COMPLETED =============", False)
    
    


def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("MICROPHONE AUDIO TEST (NORM)")
    
    screen.log_signal.emit("==========COMMENCING MICROPHONE AUDIO TEST==========", False)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s35_on):
        screen.log_signal.emit("S35/SB sel successfully set to Up position", False)
        time.sleep(0.5)    
        screen.check_abort()                     
    else:
        screen.log_signal.emit("ERROR: Failed to set S35/SB sel to Up position", True)
        

    time.sleep(0.5)
    screen.check_abort()
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E10", data["observation"])   # measured observation
        write_excel("E10", data["observation"])         # raw vrms
        write_excel("F10", data["result"])        # PASS / FAIL 
    time.sleep(1)
    screen.check_abort()
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob CW\n",
        RESOURCES_DIR / "knob_fcw.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.check_abort()
    screen.log_signal.emit("MIC MODE knob set to CW", False)
    time.sleep(1)
    data = read_apx_meter(screen, max_v="2", unit="mvrms")
    if data:
        # write_excel("E12", data["observation"])   # measured observation
        write_excel("E12", data["observation"])         # raw vrms
        write_excel("F12", data["result"])        # PASS / FAIL
    time.sleep(1)
    screen.log_signal.emit("Turning ICS(S32) to Up position.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s32_on):
        screen.log_signal.emit("S32 successfully set to Up position", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to Up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E14", data["observation"])   # measured observation
        write_excel("E14", data["observation"])         # raw vrms
        write_excel("F14", data["result"])        # PASS / FAIL
    
    time.sleep(1)
    screen.log_signal.emit("Turning ICS(S32) to Down position.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s32_off):
        screen.log_signal.emit("S32 successfully set to Down position", False)
        time.sleep(0.5)
        screen.check_abort()
    else:
        screen.log_signal.emit("ERROR: Failed to  S32 to Down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Turning TX SWITCH (S30) to Up position.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("TX SWITCH (S30) successfully set to Up position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to Up position", True)
        
    
    data = read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        # write_excel("E16", data["observation"])   # measured observation
        write_excel("E16", data["observation"])         # raw vrms
        write_excel("F16", data["result"])        # PASS / FAIL
    screen.check_abort()
    screen.log_signal.emit("Turning TX SWITCH (S30) to Down position.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("TX SWITCH (S30) successfully set to Down position", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S30 to Down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    # generator_control(screen,state="off")
    
    screen.log_signal.emit("Turning LOAD Switch (S31) to NEUTRAL.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_s31_neutral):
        screen.log_signal.emit("S31 successfully set to NEUTRAL", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to NEUTRAL", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("J27 BENCH MIC successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J27 BENCH MIC", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    autoset_oscilloscope(screen)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect the headset jack J28 using headset adapter\n"
        "• Turn the MIC MODE knob CCW\n",
        RESOURCES_DIR / "knob_headset.jpg","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.check_abort()
    time.sleep(2)
    screen.log_signal.emit("Headset jack J28 connected using headset adapter", False)
    screen.log_signal.emit("Turned MIC MODE knob CCW", False)
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
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
    screen.check_abort()
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E18",operator)   # YES
    write_excel("F18",result)     # PASS
    
    time.sleep(1)
    screen.log_signal.emit("Disconnecting J28 Headset jack.", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    screen.check_abort()
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect the headset jack J28 using headset adapter\n",
        RESOURCES_DIR / "headset_rem.jpg","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.check_abort()
    screen.log_signal.emit("J28 headset jack successfully disconnected", False)
    time.sleep(2)
    set_ch1_ch2_scale_10v(screen)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_on):
        screen.log_signal.emit("J27 BENCH MIC successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J27 BENCH MIC.", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    screen.log_signal.emit("Turning LOAD Switch (S31) to 600 ohms.  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_s31_600ohm):
        screen.log_signal.emit("S31 successfully set to 600 ohms", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to  S31 to 600 ohms", True)
        
    screen.check_abort()
    QApplication.processEvents()
    time.sleep(0.5)
    # generator_control(screen,state="on")
    screen.check_abort()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Increasing audio analyser MONITOR volume until tone is audible.", False)
    
    time.sleep(2)

    data = audible_tone_check(screen)

    operator = data["operator"]
    result = data["result"]
    gain_used=data["gain"]

    print("Operator:", operator)
    print("Result:", result)
    screen.check_abort()
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set MIC MODE to 12'o clock position.\n",
        RESOURCES_DIR / "knob_12oclock.png",
        "ok",None
    )


    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.check_abort()
    screen.log_signal.emit("MIC MODE knob set to 12'o clock position", False)
    time.sleep(2)
    screen.log_signal.emit("Decreasing audio analyser Generator Output until tone is not audible.", False)
    
    audible_reduce_until_silent(screen)
    screen.check_abort()

    time.sleep(2)
    screen.check_abort()
    data=audible_increase_until_audible(screen)
    if data:
        write_excel("E20", data["threshold"])         # raw vrms at audible threshold
        write_excel("F20", data["result"])        # PASS / FAIL
    time.sleep(2)
    screen.log_signal.emit("decreasing audio analyser Monitor volume.", False)

    time.sleep(2)
    screen.check_abort()
    reduce_monitor_gain_to_x1(screen, gain_used)
    # ⏸ WAIT until operator clicks OK
   
    time.sleep(0.5)
    screen.check_abort()
    
    
    screen.log_signal.emit("Disconnecting MIC Connector (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_j13_off):
        screen.log_signal.emit("MIC Connector J13 successfully disconnected", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect MIC Connector J13", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    time.sleep(2)
    
    screen.log_signal.emit("Connecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_j14_on):
        screen.log_signal.emit("HOT MIC Connector J14 successfully Connected", False)
        time.sleep(0.5)
        screen.check_abort()
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect HOT MIC Connector J14", True)
        

    QApplication.processEvents()
    time.sleep(2)
    screen.check_abort()
    generator_control(screen,level="750.0 uVrms",frequency=1000)
    time.sleep(1)
    screen.check_abort()
    data=read_apx_meter(screen,min_v="1.8", max_v="2.2")
    if data:
        write_excel("E22", data["observation"])         # raw vrms at 750 uVrms gen level
        write_excel("F22", data["result"])              # PASS / FAIL
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully CCW.\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.check_abort()
    screen.log_signal.emit("MIC MODE knob set to CCW", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("J27 MIC Connector successfully Disconnected", False)
        time.sleep(0.5) 
        screen.check_abort()                        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J27 MIC Connector", True)
        
    time.sleep(0.5)
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_s36_on):
        screen.log_signal.emit("GEN LOAD S36 successfully set to Up position", False)
        time.sleep(0.5) 
        screen.check_abort()                        
    else:
        screen.log_signal.emit("ERROR: Failed to set GEN LOAD S36 to Up position", True)
        
    time.sleep(0.5)
    screen.check_abort()
    result = dmm_reader.read_resistance(screen, "GEN LOAD reading: ", min_val=68, max_val=82)
    if result:
        write_excel("E24", result["observation"])  
        write_excel("F24", result["result"])  
    screen.check_abort()    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s36_off):
        screen.log_signal.emit("GEN LOAD S36 successfully set to Down position", False)
        time.sleep(0.5)                         
    else:
        screen.log_signal.emit("ERROR: Failed to set GEN LOAD S36 to Down position", True)
        
    time.sleep(0.5) 
    screen.check_abort()
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_on):
        screen.log_signal.emit("J27 MIC Connector successfully Connected", False)
        time.sleep(0.5)                         
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J27 MIC Connector.", True)
        
    time.sleep(0.5)
    screen.check_abort()
   
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_s35_off):
        screen.log_signal.emit("S35/SB sel successfully set to Down position", False)
        time.sleep(0.5)                         
    else:
        screen.log_signal.emit("ERROR: Failed to set S35/SB sel to Down position", True)
        

    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("============ MICROPHONE AUDIO TEST COMPLETED =============", False)