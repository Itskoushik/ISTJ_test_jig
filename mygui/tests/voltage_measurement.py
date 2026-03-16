from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from core.dmm_reader import read_voltage
from core.excel_logger import write_excel

def run_stby(screen):
    
    screen.log_signal.emit("==========COMMENCING VOLTAGE MEASUREMENTS TEST==========", False)
    time.sleep(2)
    
    screen.log_signal.emit("Step 1: Connecting COM 1 KEY Connector (J30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j30_on():
        screen.log_signal.emit("J30 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J30", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen,"COM 1 KEY Connector (J30)",None,"0.2V")
    if result:
        write_excel("E44", result["observation"])   # -14.3 mV
        write_excel("J44", result["result"])        # PASS
    
    #multimeter should read <0.2Vdc
    screen.log_signal.emit("Step 2: Setting V/UHF 1 to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()    
    time.sleep(2)
    result=read_voltage(screen," V/UHF 1 to in position","8.5V","9.5V")
    if result:
        write_excel("E46", result["observation"])   # -14.3 mV
        write_excel("J46", result["result"])        # PASS
    
    screen.log_signal.emit("Step 3: Disconnecting COM 1 KEY Connector (J30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j30_off():
        screen.log_signal.emit("J30 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J30", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 4: Connecting COM 2 KEY Connector (J31)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j31_on():
        screen.log_signal.emit("J31 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J31", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen,"COM 2 KEY Connector (J31)",None,"0.2V")
    if result:
        write_excel("F44", result["observation"])   # -14.3 mV
        write_excel("J44", result["result"])        # PASS
    
    
    screen.log_signal.emit("Step 5: Setting V/UHF 2 to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()   
    time.sleep(2)
    result = read_voltage(screen," V/UHF 2 to in position","8.5V","9.5V")
    if result:
        write_excel("F46", result["observation"])   # -14.3 mV
        write_excel("J46", result["result"])        # PASS
    screen.log_signal.emit("Step 6: Disconnecting COM 2 KEY Connector (J31)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j31_off():
        screen.log_signal.emit("J31 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J31", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 7: Connecting COM 3 KEY Connector (J32)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j32_on():
        screen.log_signal.emit("J32 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J32", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen,"COM 3 KEY Connector (J32)",None,"0.2V")
    if result:
        write_excel("G44", result["observation"])   # -14.3 mV
        write_excel("J44", result["result"])        # PASS
    screen.log_signal.emit("Step 8: Setting HF to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    
    result = read_voltage(screen," HF to in position","8.5V","9.5V")
    if result:
        write_excel("G46", result["observation"])   # -14.3 mV
        write_excel("J46", result["result"])        # PASS
    
    screen.log_signal.emit("Step 9: Disconnecting COM 3 KEY Connector (J32)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j32_off():
        screen.log_signal.emit("J32 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J32", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 10: Connecting COM 4 KEY Connector (J33)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j33_on():
        screen.log_signal.emit("J33 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J33", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen,"COM 4 KEY Connector (J33)",None,"0.2V")
    if result:
        write_excel("H44", result["observation"])   # -14.3 mV
        write_excel("J44", result["result"])        # PASS
    
    screen.log_signal.emit("Step 11: Setting SPARE 1 to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 1 to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    result = read_voltage(screen," SPARE 1 to in position","8.5V","9.5V")
    if result:
        write_excel("H46", result["observation"])   # -14.3 mV
        write_excel("J46", result["result"])        # PASS
    
    screen.log_signal.emit("Step 12: Disconnecting COM 4 KEY Connector (J33)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j33_off():
        screen.log_signal.emit("J33 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J33", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 13: Connecting COM 5 KEY Connector (J34)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j34_on():
        screen.log_signal.emit("J34 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J34", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen,"COM 5 KEY Connector (J34)",None,"0.2V")
    if result:
        write_excel("I44", result["observation"])   # -14.3 mV
        write_excel("J44", result["result"])        # PASS

    screen.log_signal.emit("Step 14: Setting SPARE 2 to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 2 to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()

    time.sleep(2)
    result = read_voltage(screen," SPARE 2 to in position","8.5V","9.5V")
    if result:
        write_excel("I46", result["observation"])   # -14.3 mV
        write_excel("J46", result["result"])        # PASS
    
    screen.log_signal.emit("Step 15: Disconnecting COM 5 KEY Connector (J34)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j34_off():
        screen.log_signal.emit("J34 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J34", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and hold RAD PTT Switch\n"
        "• TX Indicator should illuminate light.\n",
        RESOURCES_DIR / "rad_ptt.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E51",operator)   # YES
    write_excel("F51",result)     # PASS      

    screen.log_signal.emit("Step 16: Switching TX Switch (S30) to UP position (ON)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result=read_voltage(screen," RAD ptt switch",None,"0.7V")
    if result:
        write_excel("E55", result["observation"])   # -14.3 mV
        write_excel("F55", result["result"])        # PASS

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 18: Connecting DMM +ve lead to COM1 VOL (J37)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j37_on():
        screen.log_signal.emit("COM1 VOL (J37) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM1 VOL (J37)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen," COM 1 VOL(J37)","10V","12V")
    if result:
        write_excel("E63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])        # PASS
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate V/UHF 1 knob Clockwise till Lower Voltage \n"
        "• V/UHF 1 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_voltage(screen," COM 1 VOL(J37) after 1/4th rotation",None,None) 
    if result:
        write_excel("E65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 1 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," COM 1 VOL(J37) after full rotation",None,"0.2V")
    if result:
        write_excel("E67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    screen.log_signal.emit("Step 19: Disconnecting COM1 VOL (J37)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j37_off():
        screen.log_signal.emit("COM1 VOL (J37) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM1 VOL (J37)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 20: Connecting DMM +ve lead to COM2 VOL (J38)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j38_on():
        screen.log_signal.emit("COM2 VOL (J38) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM2 VOL (J38)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen," COM 2 VOL(J38)","10V","12V")
    if result:
        write_excel("F63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate V/UHF 2 knob Clockwise till Lower Voltage \n"
        "• V/UHF 2 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_voltage(screen," COM 2 VOL(J38) after 1/4th rotation",None,None) 
    if result:
        write_excel("F65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 2 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_voltage(screen," COM 2 VOL(J38) after full rotation",None,"0.2V")
    if result:
        write_excel("F67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 21: Disconnecting COM2 VOL (J38)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j38_off():
        screen.log_signal.emit("COM2 VOL (J38) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM2 VOL (J38)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 22: Connecting DMM +ve lead to COM3 VOL (J39)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j39_on():
        screen.log_signal.emit("COM3 VOL (J39) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM3 VOL (J39)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen," COM 3 VOL(J39)","10V","12V")
    if result:
        write_excel("G63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate HF knob Clockwise till Lower Voltage \n"
        "• HF knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_voltage(screen," COM 3 VOL(J39) after 1/4th rotation",None,None) 
    if result:
        write_excel("G65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate HF knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," COM 3 VOL(J39) after full rotation",None,"0.2V")
    if result:
        write_excel("G67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 23: Disconnecting COM3 VOL (J39)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j39_off():
        screen.log_signal.emit("COM3 VOL (J39) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM3 VOL (J39)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 24: Connecting DMM +ve lead to COM4 VOL (J40)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j40_on():
        screen.log_signal.emit("COM4 VOL (J40) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM4 VOL (J40)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen," COM 4 VOL(J40)","10V","12V")
    if result:
        write_excel("H63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 1 knob Clockwise till Lower Voltage \n"
        "• SPARE 1 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," COM 4 VOL(J40) after 1/4th rotation",None,None)
    if result:
        write_excel("H65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 1 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," COM 4 VOL(J40) after full rotation",None,"0.2V") 
    if result:
        write_excel("H67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 25: Disconnecting COM4 VOL (J40)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j40_off():
        screen.log_signal.emit("COM4 VOL (J40) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM4 VOL (J40)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 26: Connecting DMM +ve lead to COM5 VOL (J41)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j41_on():
        screen.log_signal.emit("COM5 VOL (J41) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM5 VOL (J41)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen," COM 5 VOL(J41)","10V","12V")
    if result:
        write_excel("I63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 2 knob Clockwise till Lower Voltage \n"
        "• SPARE 2 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," COM 5 VOL(J41) after 1/4th rotation",None,None) 
    if result:
        write_excel("I65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 2 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," COM 5 VOL(J41) after full rotation",None,"0.2V")
    if result:
        write_excel("I67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 27: Disconnecting COM5 VOL (J41)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j41_off():
        screen.log_signal.emit("COM5 VOL (J41) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM5 VOL (J41)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 28: Connecting DMM +ve lead to NAV1 VOL (J44)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j44_on():
        screen.log_signal.emit("NAV1 VOL (J44) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV1 VOL (J44)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen," NAV1 VOL(J44)","10V","12V")  
    if result:
        write_excel("J63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate ADF knob Clockwise till Lower Voltage \n"
        "• ADF knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV1 VOL(J44) after 1/4th rotation",None,None)
    if result:
        write_excel("J65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ADF knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV1 VOL(J44) after full rotation",None,"0.2V") 
    if result:
        write_excel("J67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 29: Disconnecting NAV1 VOL (J44)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j44_off():
        screen.log_signal.emit("NAV1 VOL (J44) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV1 VOL (J44)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 30: Connecting DMM +ve lead to NAV2 VOL (J45)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j45_on():
        screen.log_signal.emit("NAV2 VOL (J45) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV2 VOL (J45)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen," NAV2 VOL(J45)","10V","12V")
    if result:
        write_excel("K63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SONIC knob Clockwise till Lower Voltage \n"
        "• SONIC knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV2 VOL(J45) after 1/4th rotation",None,None)
    if result:
        write_excel("K65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SONIC knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV2 VOL(J45) after full rotation",None,"0.2V") 
    if result:
        write_excel("K67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 31: Disconnecting NAV2 VOL (J45)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j45_off():
        screen.log_signal.emit("NAV2 VOL (J45) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV2 VOL (J45)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 32: Connecting DMM +ve lead to NAV3 VOL (J46)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j46_on():
        screen.log_signal.emit("NAV3 VOL (J46) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV3 VOL (J46)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen," NAV3 VOL(J46)","10V","12V")
    if result:
        write_excel("L63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate ESM knob Clockwise till Lower Voltage \n"
        "• ESM knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_voltage(screen," NAV3 VOL(J46) after 1/4th rotation",None,None)
    if result:
        write_excel("L65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ESM knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV3 VOL(J46) after full rotation",None,"0.2V") 
    if result:
        write_excel("L67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 33: Disconnecting NAV3 VOL (J46)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j46_off():
        screen.log_signal.emit("NAV3 VOL (J46) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV3 VOL (J46)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 34: Connecting DMM +ve lead to NAV4 VOL (J47)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j47_on():
        screen.log_signal.emit("NAV4 VOL (J47) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV4 VOL (J47)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen," NAV4 VOL(J47)","10V","12V")
    if result:
        write_excel("M63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 3 knob Clockwise till Lower Voltage \n"
        "• SPARE 3 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV4 VOL(J47) after 1/4th rotation",None,None) 
    if result:
        write_excel("M65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 3 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV4 VOL(J47) after full rotation",None,"0.2V") 
    if result:
        write_excel("M67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 35: Disconnecting NAV4 VOL (J47)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j47_off():
        screen.log_signal.emit("NAV4 VOL (J47) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV4 VOL (J47)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 36: Connecting DMM +ve lead to NAV5 VOL (J48)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j48_on():
        screen.log_signal.emit("NAV5 VOL (J48) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV5 VOL (J48)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    result = read_voltage(screen," NAV5 VOL(J48)","10V","12V")
    if result:
        write_excel("N63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 4 knob Clockwise till Lower Voltage \n"
        "• SPARE 4 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV5 VOL(J48) after 1/4th rotation",None,None)
    if result:
        write_excel("N65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 4 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV5 VOL(J48) after full rotation",None,"0.2V")
    if result:
        write_excel("N67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 37: Disconnecting NAV5 VOL (J48)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j48_off():
        screen.log_signal.emit("NAV5 VOL (J48) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV5 VOL (J48)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 38: Connecting DMM +ve lead to NAV6 VOL (J49)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j49_on():
        screen.log_signal.emit("NAV6 VOL (J49) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV6 VOL (J49)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_voltage(screen," NAV6 VOL(J49)","10V","12V")
    if result:
        write_excel("O63", result["observation"])   # -14.3 mV
        write_excel("P63", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 5 knob Clockwise till Lower Voltage \n"
        "• SPARE 5 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = read_voltage(screen," NAV6 VOL(J49) after 1/4th rotation",None,None) 
    if result:
        write_excel("O65", result["observation"])   # -14.3 mV
        write_excel("P65", result["result"])        # PASS
        
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 5 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_voltage(screen," NAV6 VOL(J49) after full rotation",None,"0.2V") 
    if result:
        write_excel("O67", result["observation"])   # -14.3 mV
        write_excel("P67", result["result"])        # PASS
    
    screen.log_signal.emit("Step 39: Disconnecting NAV6 VOL (J49)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j49_off():
        screen.log_signal.emit("NAV6 VOL (J49) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV6 VOL (J49)", True)
        return

    QApplication.processEvents()
    time.sleep(2)   
    
    screen.log_signal.emit("✓ VOLTAGE MEASUREMENTS TEST COMPLETED", False)

def run_norm(screen):    
  
    screen.log_signal.emit("==========COMMENCING VOLTAGE MEASUREMENTS TEST==========", False)
    time.sleep(2)
    
    screen.log_signal.emit("Step 1: Connecting COM 1 KEY Connector (J30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j30_on():
        screen.log_signal.emit("J30 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J30", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result=read_voltage(screen,"COM 1 KEY Connector (J30)",None,"0.2V")
    if result:
        write_excel("E43", result["observation"])   # -14.3 mV
        write_excel("J43", result["result"])        # PASS
    
    screen.log_signal.emit("Step 2: Setting V/UHF 1 to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_voltage(screen," V/UHF 1 to in position","8.5V","9.5V")
    if result:
        write_excel("E45", result["observation"])   # 8.95 V
        write_excel("J45", result["result"])        # PASS
    screen.log_signal.emit("Step 3: Disconnecting COM 1 KEY Connector (J30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j30_off():
        screen.log_signal.emit("J30 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J30", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 4: Connecting COM 2 KEY Connector (J31)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j31_on():
        screen.log_signal.emit("J31 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J31", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen,"COM 2 KEY Connector (J31)",None,"0.2V")
    if result:
        write_excel("F43", result["observation"])   
        write_excel("J43", result["result"])
    
    screen.log_signal.emit("Step 5: Setting V/UHF 2 to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    result = read_voltage(screen," V/UHF 2 to in position","8.5V","9.5V")
    if result:
        write_excel("F45", result["observation"])   
        write_excel("J45", result["result"])
    
    time.sleep(2)
    screen.log_signal.emit("Step 6: Disconnecting COM 2 KEY Connector (J31)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j31_off():
        screen.log_signal.emit("J31 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J31", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 7: Connecting COM 3 KEY Connector (J32)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j32_on():
        screen.log_signal.emit("J32 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J32", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen,"COM 3 KEY Connector (J32)",None,"0.2V")
    if result:
        write_excel("G43", result["observation"])   
        write_excel("J43", result["result"])
    
    screen.log_signal.emit("Step 8: Setting HF to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    result = read_voltage(screen," HF to in position","8.5V","9.5V")
    if result:
        write_excel("G45", result["observation"])   
        write_excel("J45", result["result"])
    
    time.sleep(2)
    screen.log_signal.emit("Step 9: Disconnecting COM 3 KEY Connector (J32)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j32_off():
        screen.log_signal.emit("J32 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J32", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 10: Connecting COM 4 KEY Connector (J33)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j33_on():
        screen.log_signal.emit("J33 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J33", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen,"COM 4 KEY Connector (J33)",None,"0.2V")
    if result:
        write_excel("H43", result["observation"])   
        write_excel("J43", result["result"])
    
    screen.log_signal.emit("Step 11: Setting SPARE 1 to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 1 to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    result = read_voltage(screen," SPARE 1 to in position","8.5V","9.5V")
    if result:
        write_excel("H45", result["observation"])   
        write_excel("J45", result["result"])
    time.sleep(2)
    screen.log_signal.emit("Step 12: Disconnecting COM 4 KEY Connector (J33)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j33_off():
        screen.log_signal.emit("J33 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J33", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 13: Connecting COM 5 KEY Connector (J34)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j34_on():
        screen.log_signal.emit("J34 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J34", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result = read_voltage(screen,"COM 5 KEY Connector (J34)",None,"0.2V")
    if result:
        write_excel("I43", result["observation"])   
        write_excel("J43", result["result"])
    
    screen.log_signal.emit("Step 14: Setting SPARE 2 to in position.", False)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE 2 to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / "button_in.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    result = read_voltage(screen," SPARE 2 to in position","8.5V","9.5V")
    if result:
        write_excel("I45", result["observation"])   
        write_excel("J45", result["result"])
    
    time.sleep(2)
    screen.log_signal.emit("Step 15: Disconnecting COM 5 KEY Connector (J34)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j34_off():
        screen.log_signal.emit("J34 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J34", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and hold RAD PTT Switch\n"
        "• TX Indicator should illuminate light.\n",
        RESOURCES_DIR / "rad_ptt.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E50",operator)   # YES
    write_excel("F50",result)     # PASS
    
    result=read_voltage(screen," RAD ptt switch",None,"0.7V")
    if result:
        write_excel("E52", result["observation"])   # 0.68 V
        write_excel("F52", result["result"])        # PASS  
    
    
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Release RAD PTT Switch\n"
        "• TX Indicator should extinguish the light.\n",
        RESOURCES_DIR / "rad_ptt.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E53",operator)   # YES
    write_excel("F53",result)     # PASS

    time.sleep(2)           

    screen.log_signal.emit("Step 16: Switching TX Switch (S30) to UP position (ON)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result=read_voltage(screen," RAD ptt switch",None,"0.7V")
    if result:
        write_excel("E54", result["observation"])   # 0.68 V
        write_excel("F54", result["result"])        # PASS
    
    screen.log_signal.emit("Step 17: Switching TX Switch (S30) to Down position (OFF)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30", True)
        return

    QApplication.processEvents()
    time.sleep(2)

    screen.log_signal.emit("Step 18: Switching STBY PWR Switch (S25) to UP position (ON)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s25_on():
        screen.log_signal.emit("S25 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S25", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 19: Switching NORM PWR Switch (S24) to Down position (OFF)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s24_off():
        screen.log_signal.emit("S24 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S24", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• STBY Indicator should get illuminated.\n",
        None,"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E56",operator)   # YES
    write_excel("F56",result)     # PASS

    time.sleep(2)  
    
    screen.log_signal.emit("Step 20: Switching STBY PWR Switch (S25) to Down position (OFF)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s25_off():
        screen.log_signal.emit("S25 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S25", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 21: Switching NORM PWR Switch (S24) to UP position (ON)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s24_on():
        screen.log_signal.emit("S24 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S24", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• STBY Indicator should get extinguished.\n",
        None,"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E57",operator)   # YES
    write_excel("F57",result)     # PASS
    time.sleep(2)
    
    #===============================================================================
    
    screen.log_signal.emit("Step 22: Connecting DMM +ve lead to COM1 VOL (J37)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j37_on():
        screen.log_signal.emit("COM1 VOL (J37) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM1 VOL (J37)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result=read_voltage(screen," COM 1 VOL(J37)","10V","12V")
    if result:
        write_excel("E62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate V/UHF 1 knob Clockwise till Lower Voltage \n"
        "• V/UHF 1 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," COM 1 VOL(J37) after 1/4th rotation",None,None)
    if result:
        write_excel("E64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 1 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result=read_voltage(screen," COM 1 VOL(J37) after full rotation",None,"0.2V")
    if result:
        write_excel("E66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 23: Disconnecting COM1 VOL (J37)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j37_off():
        screen.log_signal.emit("COM1 VOL (J37) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM1 VOL (J37)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 24: Connecting DMM +ve lead to COM2 VOL (J38)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j38_on():
        screen.log_signal.emit("COM2 VOL (J38) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM2 VOL (J38)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result=read_voltage(screen," COM 2 VOL(J38)","10V","12V")
    if result:
        write_excel("F62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate V/UHF 2 knob Clockwise till Lower Voltage \n"
        "• V/UHF 2 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result=read_voltage(screen," COM 2 VOL(J38) after 1/4th rotation",None,None)
    if result:
        write_excel("F64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 2 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," COM 2 VOL(J38) after full rotation",None,"0.2V")
    if result:
        write_excel("F66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 25: Disconnecting COM2 VOL (J38)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j38_off():
        screen.log_signal.emit("COM2 VOL (J38) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM2 VOL (J38)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 26: Connecting DMM +ve lead to COM3 VOL (J39)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j39_on():
        screen.log_signal.emit("COM3 VOL (J39) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM3 VOL (J39)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result=read_voltage(screen," COM 3 VOL(J39)","10V","12V")
    if result:
        write_excel("G62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate HF knob Clockwise till Lower Voltage \n"
        "• HF knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," COM 3 VOL(J39) after 1/4th rotation",None,None)
    if result:
        write_excel("G64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate HF knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result=read_voltage(screen," COM 3 VOL(J39) after full rotation",None,"0.2V")
    if result:
        write_excel("G66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 27: Disconnecting COM3 VOL (J39)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j39_off():
        screen.log_signal.emit("COM3 VOL (J39) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM3 VOL (J39)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 28: Connecting DMM +ve lead to COM4 VOL (J40)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j40_on():
        screen.log_signal.emit("COM4 VOL (J40) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM4 VOL (J40)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result=read_voltage(screen," COM 4 VOL(J40)","10V","12V")
    if result:
        write_excel("H62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 1 knob Clockwise till Lower Voltage \n"
        "• SPARE 1 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," COM 4 VOL(J40) after 1/4th rotation",None,None)
    if result:
        write_excel("H64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 1 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result=read_voltage(screen," COM 4 VOL(J40) after full rotation",None,"0.2V")
    if result:
        write_excel("H66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 29: Disconnecting COM4 VOL (J40)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j40_off():
        screen.log_signal.emit("COM4 VOL (J40) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM4 VOL (J40)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 30: Connecting DMM +ve lead to COM5 VOL (J41)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j41_on():
        screen.log_signal.emit("COM5 VOL (J41) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON COM5 VOL (J41)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result=read_voltage(screen," COM 5 VOL(J41)","10V","12V")
    if result:
        write_excel("I62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 2 knob Clockwise till Lower Voltage \n"
        "• SPARE 2 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," COM 5 VOL(J41) after 1/4th rotation",None,None) 
    if result:
        write_excel("I64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 2 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," COM 5 VOL(J41) after full rotation",None,"0.2V")
    if result:
        write_excel("I66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 31: Disconnecting COM5 VOL (J41)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j41_off():
        screen.log_signal.emit("COM5 VOL (J41) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF COM5 VOL (J41)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 32: Connecting DMM +ve lead to NAV1 VOL (J44)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j44_on():
        screen.log_signal.emit("NAV1 VOL (J44) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV1 VOL (J44)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result=read_voltage(screen," NAV 1 VOL(J44)","10V","12V")
    if result:
        write_excel("J62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate ADF knob Clockwise till Lower Voltage \n"
        "• ADF knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV1 VOL(J44) after 1/4th rotation",None,None) 
    if result:
        write_excel("J64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ADF knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV1 VOL(J44) after full rotation",None,"0.2V")
    if result:
        write_excel("J66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 33: Disconnecting NAV1 VOL (J44)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j44_off():
        screen.log_signal.emit("NAV1 VOL (J44) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV1 VOL (J44)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 34: Connecting DMM +ve lead to NAV2 VOL (J45)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j45_on():
        screen.log_signal.emit("NAV2 VOL (J45) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV2 VOL (J45)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result=read_voltage(screen," NAV 2 VOL(J45)","10V","12V")
    if result:
        write_excel("K62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SONIC knob Clockwise till Lower Voltage \n"
        "• SONIC knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV2 VOL(J45) after 1/4th rotation",None,None) 
    if result:
        write_excel("K64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SONIC knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV2 VOL(J45) after full rotation",None,"0.2V")
    if result:
        write_excel("K66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 35: Disconnecting NAV2 VOL (J45)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j45_off():
        screen.log_signal.emit("NAV2 VOL (J45) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV2 VOL (J45)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 36: Connecting DMM +ve lead to NAV3 VOL (J46)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j46_on():
        screen.log_signal.emit("NAV3 VOL (J46) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV3 VOL (J46)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result=read_voltage(screen," NAV 3 VOL(J46)","10V","12V")
    if result:
        write_excel("L62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate ESM knob Clockwise till Lower Voltage \n"
        "• ESM knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV3 VOL(J46) after 1/4th rotation",None,None) 
    if result:
        write_excel("L64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ESM knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV3 VOL(J46) after full rotation",None,"0.2V")
    if result:
        write_excel("L66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 37: Disconnecting NAV3 VOL (J46)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j46_off():
        screen.log_signal.emit("NAV3 VOL (J46) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV3 VOL (J46)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 38: Connecting DMM +ve lead to NAV4 VOL (J47)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j47_on():
        screen.log_signal.emit("NAV4 VOL (J47) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV4 VOL (J47)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result=read_voltage(screen," NAV4 VOL(J47)","10V","12V")
    if result:
        write_excel("M62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 3 knob Clockwise till Lower Voltage \n"
        "• SPARE 3 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV4 VOL(J47) after 1/4th rotation",None,None) 
    if result:
        write_excel("M64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 3 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV4 VOL(J47) after full rotation",None,"0.2V")
    if result:
        write_excel("M66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS  
    
    screen.log_signal.emit("Step 39: Disconnecting NAV4 VOL (J47)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j47_off():
        screen.log_signal.emit("NAV4 VOL (J47) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV4 VOL (J47)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 40: Connecting DMM +ve lead to NAV5 VOL (J48)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j48_on():
        screen.log_signal.emit("NAV5 VOL (J48) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV5 VOL (J48)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result=read_voltage(screen," NAV 5 VOL(J48)","10V","12V")
    if result:
        write_excel("N62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 4 knob Clockwise till Lower Voltage \n"
        "• SPARE 4 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV5 VOL(J48) after 1/4th rotation",None,None) 
    if result:
        write_excel("N64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 4 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV5 VOL(J48) after full rotation",None,"0.2V")
    if result:
        write_excel("N66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 41: Disconnecting NAV5 VOL (J48)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j48_off():
        screen.log_signal.emit("NAV5 VOL (J48) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV5 VOL (J48)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 42: Connecting DMM +ve lead to NAV6 VOL (J49)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j49_on():
        screen.log_signal.emit("NAV6 VOL (J49) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NAV6 VOL (J49)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    result=read_voltage(screen," NAV 6 VOL(J49)","10V","12V")
    if result:
        write_excel("O62", result["observation"])   # 11.95 V
        write_excel("P62", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Slowly Rotate SPARE 5 knob Clockwise till Lower Voltage \n"
        "• SPARE 5 knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV6 VOL(J49) after 1/4th rotation",None,None) 
    if result:
        write_excel("O64", result["observation"])   # 11.95 V
        write_excel("P64", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 5 knob fully Clockwise \n",
        RESOURCES_DIR / "knob_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result=read_voltage(screen," NAV6 VOL(J49) after full rotation",None,"0.2V")
    if result:
        write_excel("O66", result["observation"])   # 11.95 V
        write_excel("P66", result["result"])        # PASS
    
    screen.log_signal.emit("Step 41: Disconnecting NAV6 VOL (J49)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j49_off():
        screen.log_signal.emit("NAV6 VOL (J49) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NAV6 VOL (J49)", True)
        return

    QApplication.processEvents()
    time.sleep(2)   
    
    screen.log_signal.emit("✓ VOLTAGE MEASUREMENTS TEST COMPLETED", False)