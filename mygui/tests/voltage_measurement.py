from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
import core.dmm_reader as dmm_reader
from core.excel_logger import write_excel
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
_IMAGES = {
    "N200 - ALH1": {
        "com1": "uvhf1alh1.jpeg",
        "com2": "vhf2.jpeg",
        "com3": "hfalh1.png",
        "com4": "spare1alh1.jpeg",
        "com5": "pa.jpeg",
        "txselout": "txselalh1.jpeg",
        "txrxsel": "txrxalh1.png",
        "tx_stby_on": "tx_stby_alh1.jpeg",
    },
    "N200 - ALH2": {
        "com1": "vhf1alh2.png",
        "com2": "VUHF-2.png",
        "com3": "hfalh2.png",
        "com4": "sparealh2.png",
        "com5": "LD HLR.png",
        "txselout": "txselalh2.jpeg",
        "txrxsel": "txrxalh2.png",
        "tx_stby_on": "tx_stby_alh2.jpeg",
    },
    "N200 - ALH3": {
        "com1": "VUHFalh3.png",
        "com2": "VUHF-2alh3.png",
        "com3": "VHF FMalh3.png",
        "com4": "HFalh3.png",
        "com5": "SPARE 1alh3.png",
        "txselout": "txselalh3.jpeg",
        "txrxsel": "txrxalh3.png",
        "tx_stby_on": "tx_stby_alh3.jpeg",
    },
}
_NAMES = {
    "N200 - ALH1": {
        "com1": "VHF 1",    "com2": "VHF 2",    "com3": "HF",
        "com4": "SPARE 1",  "com5": "PA",
        "nav1": "ADF",      "nav2": "VOR 1",    "nav3": "VOR 2",
        "nav4": "DME",      "nav5": "MKR",      "nav6": "SPARE 2",
    },
    "N200 - ALH2": {
        "com1": "V/UHF 1",  "com2": "V/UHF 2",  "com3": "HF",
        "com4": "SPARE",    "com5": "LD HLR",
        "nav1": "IFF",      "nav2": "VOR",      "nav3": "MKB",
        "nav4": "DME",      "nav5": "HOMR",     "nav6": "SONIC",
    },
    "N200 - ALH3": {
        "com1": "V/UHF 1",  "com2": "V/UHF 2",  "com3": "VHF FM",
        "com4": "HF",       "com5": "SPARE 1",
        "nav1": "ADF",      "nav2": "SPARE 2",  "nav3": "SPARE 3",
        "nav4": "SPARE 4",  "nav5": "SPARE 5",  "nav6": "SPARE 6",
    },
}

def _run_stby_impl(screen, names, images):
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)
    
    screen.log_signal.emit("==========COMMENCING VOLTAGE MEASUREMENTS TEST==========", False)
    time.sleep(2)
    set_popup_title("VOLTAGE MEASUREMENTS TEST (STBY)")
    screen.log_signal.emit("Connecting COM 1 KEY Connector (J30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j30_on):
        screen.log_signal.emit("J30 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J30", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("E40", result["observation"])   # -14.3 mV
        write_excel("J40", result["result"])        # PASS
    
    #multimeter should read <0.2Vdc
    screen.log_signal.emit(f"{names['com1']} set to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com1']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com1"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()    
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("E42", result["observation"])   # -14.3 mV
        write_excel("J42", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM 1 KEY Connector (J30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j30_off):
        screen.log_signal.emit("J30 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J30", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Connecting COM 2 KEY Connector (J31)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j31_on):
        screen.log_signal.emit("J31 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J31", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("F40", result["observation"])   # -14.3 mV
        write_excel("J40", result["result"])        # PASS
    
    
    screen.log_signal.emit(f"Setting {names['com2']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com2']} to in position.(ON position)\n"
        f"• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com2"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()   
    time.sleep(2)
    screen.log_signal.emit(f"{names['com2']} set to in position.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("F42", result["observation"])   # -14.3 mV
        write_excel("J42", result["result"])        # PASS
    screen.log_signal.emit("Disconnecting COM 2 KEY Connector (J31)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j31_off):
        screen.log_signal.emit("J31 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J31", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting COM 3 KEY Connector (J32)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j32_on):
        screen.log_signal.emit("J32 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J32", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("G40", result["observation"])   # -14.3 mV
        write_excel("J40", result["result"])        # PASS
    screen.log_signal.emit(f"Setting {names['com3']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com3']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com3"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    screen.log_signal.emit(f"{names['com3']} set to in position.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("G42", result["observation"])   # -14.3 mV
        write_excel("J42", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM 3 KEY Connector (J32)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j32_off):
        screen.log_signal.emit("J32 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J32", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting COM 4 KEY Connector (J33)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j33_on):
        screen.log_signal.emit("J33 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J33", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("H40", result["observation"])   # -14.3 mV
        write_excel("J40", result["result"])        # PASS
    
    screen.log_signal.emit(f"Setting {names['com4']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com4']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com4"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    screen.log_signal.emit(f"{names['com4']} set to in position.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("H42", result["observation"])   # -14.3 mV
        write_excel("J42", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM 4 KEY Connector (J33)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j33_off):
        screen.log_signal.emit("J33 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J33", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting COM 5 KEY Connector (J34)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j34_on):
        screen.log_signal.emit("J34 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J34", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("I40", result["observation"])   # -14.3 mV
        write_excel("J40", result["result"])        # PASS

    screen.log_signal.emit(f"Setting {names['com5']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com5']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com5"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()

    time.sleep(2)
    screen.log_signal.emit(f"{names['com5']} set to in position.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("I42", result["observation"])   # -14.3 mV
        write_excel("J42", result["result"])        # PASS
 

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and hold RAD PTT Switch\n"
        "• TX Indicator should illuminate light.\n",
        RESOURCES_DIR / "rad_ptt_on.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E47",operator)   # YES
    write_excel("F47",result)     # PASS 
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Release RAD PTT Switch\n"
        "• TX Indicator should extinguish the light.\n",
        RESOURCES_DIR / "rad_ptt_off.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    

    screen.log_signal.emit("Switching TX Switch (S30) to UP position (ON)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect S30", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result=dmm_reader.read_voltage(screen," Multimeter Reading",None,"0.7V")
    if result:
        write_excel("E51", result["observation"])   # -14.3 mV
        write_excel("F51", result["result"])        # PASS   

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to Down Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to Down Position", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Disconnecting COM 5 KEY Connector (J34)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j34_off):
        screen.log_signal.emit("J34 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J34", True)
        

    QApplication.processEvents()
    time.sleep(2)  
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• TX SEL knobs fully ccw and put to OUT position.\n",
        RESOURCES_DIR / images["txselout"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM1 VOL (J37)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j37_on):
        screen.log_signal.emit("COM1 VOL (J37) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM1 VOL (J37)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("E59", result["observation"])   # -14.3 mV
        write_excel("K59", result["result"])        # PASS
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com1']} knob Clockwise till Lower Voltage \n"
        f"• {names['com1']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit(f"{names['com1']} rotated 1/4th clockwise.", False)
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("E61", result["observation"])   # -14.3 mV
        write_excel("K61", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com1']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['com1']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("E63", result["observation"])   # -14.3 mV
        write_excel("K63", result["result"])        # PASS
    screen.log_signal.emit("Disconnecting COM1 VOL (J37)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j37_off):
        screen.log_signal.emit("COM1 VOL (J37) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM1 VOL (J37)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM2 VOL (J38)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j38_on):
        screen.log_signal.emit("COM2 VOL (J38) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM2 VOL (J38)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("F59", result["observation"])   # -14.3 mV
        write_excel("K59", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com2']} knob Clockwise till Lower Voltage \n"
        f"• {names['com2']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com2']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("F61", result["observation"])   # -14.3 mV
        write_excel("K61", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com2']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com2']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("F63", result["observation"])   # -14.3 mV
        write_excel("K63", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM2 VOL (J38)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j38_off):
        screen.log_signal.emit("COM2 VOL (J38) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM2 VOL (J38)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM3 VOL (J39)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j39_on):
        screen.log_signal.emit("COM3 VOL (J39) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM3 VOL (J39)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("G59", result["observation"])   # -14.3 mV
        write_excel("K59", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com3']} knob Clockwise till Lower Voltage \n"
        f"• {names['com3']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com3']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("G61", result["observation"])   # -14.3 mV
        write_excel("K61", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com3']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com3']} rotated fully clockwise.", False) 
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("G63", result["observation"])   # -14.3 mV
        write_excel("K63", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM3 VOL (J39)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j39_off):
        screen.log_signal.emit("COM3 VOL (J39) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM3 VOL (J39)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM4 VOL (J40)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j40_on):
        screen.log_signal.emit("COM4 VOL (J40) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM4 VOL (J40)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("H59", result["observation"])   # -14.3 mV
        write_excel("K59", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com4']} knob Clockwise till Lower Voltage \n"
        f"• {names['com4']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['com4']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("H61", result["observation"])   # -14.3 mV
        write_excel("K61", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com4']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com4']} rotated fully clockwise.", False)
    
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V") 
    if result:
        write_excel("H63", result["observation"])   # -14.3 mV
        write_excel("K63", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM4 VOL (J40)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j40_off):
        screen.log_signal.emit("COM4 VOL (J40) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM4 VOL (J40)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM5 VOL (J41)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j41_on):
        screen.log_signal.emit("COM5 VOL (J41) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM5 VOL (J41)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("I59", result["observation"])   # -14.3 mV
        write_excel("K59", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com5']} knob Clockwise till Lower Voltage \n"
        f"• {names['com5']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['com5']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("I61", result["observation"])   # -14.3 mV
        write_excel("K61", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com5']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['com5']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("I63", result["observation"])   # -14.3 mV
        write_excel("K63", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM5 VOL (J41)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j41_off):
        screen.log_signal.emit("COM5 VOL (J41) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM5 VOL (J41)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV1 VOL (J44)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j44_on):
        screen.log_signal.emit("NAV1 VOL (J44) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV1 VOL (J44)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")  
    if result:
        write_excel("E68", result["observation"])   # -14.3 mV
        write_excel("K68", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav1']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav1']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav1']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("E70", result["observation"])   # -14.3 mV
        write_excel("K70", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav1']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav1']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V") 
    if result:
        write_excel("E72", result["observation"])   # -14.3 mV
        write_excel("K72", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV1 VOL (J44)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j44_off):
        screen.log_signal.emit("NAV1 VOL (J44) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV1 VOL (J44)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV2 VOL (J45)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j45_on):
        screen.log_signal.emit("NAV2 VOL (J45) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV2 VOL (J45)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("F68", result["observation"])   # -14.3 mV
        write_excel("K68", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav2']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav2']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav2']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("F70", result["observation"])   # -14.3 mV
        write_excel("K70", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav2']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav2']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V") 
    if result:
        write_excel("F72", result["observation"])   # -14.3 mV
        write_excel("K72", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV2 VOL (J45)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j45_off):
        screen.log_signal.emit("NAV2 VOL (J45) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV2 VOL (J45)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV3 VOL (J46)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j46_on):
        screen.log_signal.emit("NAV3 VOL (J46) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV3 VOL (J46)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("G68", result["observation"])   # -14.3 mV
        write_excel("K68", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav3']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav3']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav3']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("G70", result["observation"])   # -14.3 mV
        write_excel("K70", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav3']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav3']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V") 
    if result:
        write_excel("G72", result["observation"])   # -14.3 mV
        write_excel("K72", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV3 VOL (J46)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j46_off):
        screen.log_signal.emit("NAV3 VOL (J46) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV3 VOL (J46)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV4 VOL (J47)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j47_on):
        screen.log_signal.emit("NAV4 VOL (J47) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV4 VOL (J47)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("H68", result["observation"])   # -14.3 mV
        write_excel("K68", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav4']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav4']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav4']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("H70", result["observation"])   # -14.3 mV
        write_excel("K70", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav4']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav4']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V") 
    if result:
        write_excel("H72", result["observation"])   # -14.3 mV
        write_excel("K72", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV4 VOL (J47)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j47_off):
        screen.log_signal.emit("NAV4 VOL (J47) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV4 VOL (J47)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV5 VOL (J48)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j48_on):
        screen.log_signal.emit("NAV5 VOL (J48) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV5 VOL (J48)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("I68", result["observation"])   # -14.3 mV
        write_excel("K68", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav5']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav5']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav5']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("I70", result["observation"])   # -14.3 mV
        write_excel("K70", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav5']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['nav5']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("I72", result["observation"])   # -14.3 mV
        write_excel("K72", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV5 VOL (J48)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j48_off):
        screen.log_signal.emit("NAV5 VOL (J48) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV5 VOL (J48)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV6 VOL (J49)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j49_on):
        screen.log_signal.emit("NAV6 VOL (J49) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV6 VOL (J49)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("J68", result["observation"])   # -14.3 mV
        write_excel("K68", result["result"])   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav6']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav6']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav6']} rotated 1/4th clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("J70", result["observation"])   # -14.3 mV
        write_excel("K70", result["result"])        # PASS
        
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav6']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav6']} rotated fully clockwise.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V") 
    if result:
        write_excel("J72", result["observation"])   # -14.3 mV
        write_excel("K72", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV6 VOL (J49)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j49_off):
        screen.log_signal.emit("NAV6 VOL (J49) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV6 VOL (J49)", True)
        

    QApplication.processEvents()
    time.sleep(2)   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• TX SEL knobs fully ccw and put to OUT position.\n"
        "• RX SEL knobs fully ccw.\n",
        RESOURCES_DIR / images["txrxsel"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    
    screen.log_signal.emit("============ VOLTAGE MEASUREMENTS TEST COMPLETED =============", False)

def _run_norm_impl(screen, names, images):
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)
    set_popup_title("VOLTAGE MEASUREMENTS TEST (NORM)")
    screen.log_signal.emit("==========COMMENCING VOLTAGE MEASUREMENTS TEST==========", False)
    time.sleep(2)
    
    screen.log_signal.emit("Connecting COM 1 KEY Connector (J30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j30_on):
        screen.log_signal.emit("J30 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J30", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("E39", result["observation"])   # -14.3 mV
        write_excel("J39", result["result"])        # PASS
    
    screen.log_signal.emit(f"Setting {names['com1']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com1']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com1"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit(f"{names['com1']} set to in position.", False)
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("E41", result["observation"])   # 8.95 V
        write_excel("J41", result["result"])        # PASS
    screen.log_signal.emit("Disconnecting COM 1 KEY Connector (J30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j30_off):
        screen.log_signal.emit("J30 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J30", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Connecting COM 2 KEY Connector (J31)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j31_on):
        screen.log_signal.emit("J31 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J31", True)
    

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("F39", result["observation"])   
        write_excel("J39", result["result"])
    
    screen.log_signal.emit(f"Setting {names['com2']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com2']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com2"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit(f"{names['com2']} set to in position.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("F41", result["observation"])   
        write_excel("J41", result["result"])
    
    time.sleep(2)
    screen.log_signal.emit("Disconnecting COM 2 KEY Connector (J31)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j31_off):
        screen.log_signal.emit("J31 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J31", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting COM 3 KEY Connector (J32)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j32_on):
        screen.log_signal.emit("J32 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J32", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("G39", result["observation"])   
        write_excel("J39", result["result"])
    
    screen.log_signal.emit(f"Setting {names['com3']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com3']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com3"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit(f"{names['com3']} set to in position.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("G41", result["observation"])   
        write_excel("J41", result["result"])
    
    time.sleep(2)
    screen.log_signal.emit("Disconnecting COM 3 KEY Connector (J32)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j32_off):
        screen.log_signal.emit("J32 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J32", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting COM 4 KEY Connector (J33)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j33_on):
        screen.log_signal.emit("J33 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J33", True)

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("H39", result["observation"])   
        write_excel("J39", result["result"])
    
    screen.log_signal.emit(f"Setting {names['com4']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com4']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com4"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit(f"{names['com4']} set to in position.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("H41", result["observation"])   
        write_excel("J41", result["result"])
    time.sleep(2)
    screen.log_signal.emit("Disconnecting COM 4 KEY Connector (J33)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j33_off):
        screen.log_signal.emit("J33 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J33", True)

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting COM 5 KEY Connector (J34)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j34_on):
        screen.log_signal.emit("J34 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J34", True)

    QApplication.processEvents()
    time.sleep(2)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("I39", result["observation"])   
        write_excel("J39", result["result"])
    
    screen.log_signal.emit(f"Setting {names['com5']} to in position.", False)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Set {names['com5']} to in position.(ON position)\n"
        "• Indicator should illuminate green light.\n",
        RESOURCES_DIR / images["com5"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit(f"{names['com5']} set to in position.", False)
    result = dmm_reader.read_voltage(screen,"Multimeter Reading","8.5V","9.5V")
    if result:
        write_excel("I41", result["observation"])   
        write_excel("J41", result["result"])
    
    time.sleep(2)
   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and hold RAD PTT Switch\n"
        "• TX Indicator should illuminate light.\n",
        RESOURCES_DIR / "rad_ptt_on.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E46",operator)   # YES
    write_excel("F46",result)     # PASS
    
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.7V")
    if result:
        write_excel("E48", result["observation"])   # 0.68 V
        write_excel("F48", result["result"])        # PASS  
    
    
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Release RAD PTT Switch\n"
        "• TX Indicator should extinguish the light.\n",
        RESOURCES_DIR / "rad_ptt_off.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E49",operator)   # YES
    write_excel("F49",result)     # PASS

    time.sleep(2) 
    
    screen.log_signal.emit("Switching TX Switch (S30) to UP position (ON)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully Set to UP Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Set S30 to UP Position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.7V")
    if result:
        write_excel("E50", result["observation"])   # 0.68 V
        write_excel("F50", result["result"])        # PASS
    
    screen.log_signal.emit("Switching TX Switch (S30) to Down position (OFF)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully Set to Down Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Set S30 to Down Position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Disconnecting COM 5 KEY Connector (J34)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j34_off):
        screen.log_signal.emit("J34 successfully Set to Off Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Set J34 to Off Position", True)
        

    QApplication.processEvents()
    time.sleep(2)          


    screen.log_signal.emit("Switching STBY PWR Switch (S25) to UP position (ON)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s25_on):
        screen.log_signal.emit("S25 successfully Set to UP Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Set S25 to UP Position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Switching NORM PWR Switch (S24) to Down position (OFF)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s24_off):
        screen.log_signal.emit("S24 successfully Set to Down Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Set S24 to Down Position", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• TX SEL knobs fully ccw and put to OUT position.\n"
        "• STBY Indicator should get illuminated.\n",
        RESOURCES_DIR / images["tx_stby_on"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E52",operator)   # YES
    write_excel("F52",result)     # PASS

    time.sleep(2)  
    
    screen.log_signal.emit("Switching STBY PWR Switch (S25) to Down position (OFF)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s25_off):
        screen.log_signal.emit("S25 successfully Set to Down Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Set S25 to Down Position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Switching NORM PWR Switch (S24) to UP position (ON)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s24_on):
        screen.log_signal.emit("S24 successfully Set to UP Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Set S24 to UP Position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• STBY Indicator should get extinguished.\n",
        RESOURCES_DIR / "stby_off.jpeg","yes_no",None
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
    
    #===============================================================================
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM1 VOL (J37)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j37_on):
        screen.log_signal.emit("COM1 VOL (J37) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM1 VOL (J37)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("E58", result["observation"])   # 11.95 V
        write_excel("K58", result["result"])        # PASS
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com1']} knob Clockwise till Lower Voltage \n"
        f"• {names['com1']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit(f"{names['com1']} knob rotated less than 1/4th rotation.", False)
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("E60", result["observation"])   # 11.95 V
        write_excel("K60", result["result"])        # PASS
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com1']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['com1']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("E62", result["observation"])   # 11.95 V
        write_excel("K62", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM1 VOL (J37)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j37_off):
        screen.log_signal.emit("COM1 VOL (J37) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM1 VOL (J37)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM2 VOL (J38)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j38_on):
        screen.log_signal.emit("COM2 VOL (J38) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM2 VOL (J38)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("F58", result["observation"])   # 11.95 V
        write_excel("K58", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com2']} knob Clockwise till Lower Voltage \n"
        f"• {names['com2']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['com2']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("F60", result["observation"])   # 11.95 V
        write_excel("K60", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com2']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com2']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("F62", result["observation"])   # 11.95 V
        write_excel("K62", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM2 VOL (J38)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j38_off):
        screen.log_signal.emit("COM2 VOL (J38) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM2 VOL (J38)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM3 VOL (J39)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j39_on):
        screen.log_signal.emit("COM3 VOL (J39) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM3 VOL (J39)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("G58", result["observation"])   # 11.95 V
        write_excel("K58", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com3']} knob Clockwise till Lower Voltage \n"
        f"• {names['com3']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com3']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("G60", result["observation"])   # 11.95 V
        write_excel("K60", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com3']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['com3']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("G62", result["observation"])   # 11.95 V
        write_excel("K62", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM3 VOL (J39)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j39_off):
        screen.log_signal.emit("COM3 VOL (J39) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM3 VOL (J39)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM4 VOL (J40)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j40_on):
        screen.log_signal.emit("COM4 VOL (J40) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM4 VOL (J40)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("H58", result["observation"])   # 11.95 V
        write_excel("K58", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com4']} knob Clockwise till Lower Voltage \n"
        f"• {names['com4']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com4']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None)
    if result:
        write_excel("H60", result["observation"])   # 11.95 V
        write_excel("K60", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com4']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    screen.log_signal.emit(f"{names['com4']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("H62", result["observation"])   # 11.95 V
        write_excel("K62", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM4 VOL (J40)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j40_off):
        screen.log_signal.emit("COM4 VOL (J40) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM4 VOL (J40)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Connecting DMM +ve lead to COM5 VOL (J41)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j41_on):
        screen.log_signal.emit("COM5 VOL (J41) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect COM5 VOL (J41)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("I58", result["observation"])   # 11.95 V
        write_excel("K58", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['com5']} knob Clockwise till Lower Voltage \n"
        f"• {names['com5']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com5']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("I60", result["observation"])   # 11.95 V
        write_excel("K60", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['com5']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['com5']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("I62", result["observation"])   # 11.95 V
        write_excel("K62", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting COM5 VOL (J41)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j41_off):
        screen.log_signal.emit("COM5 VOL (J41) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect COM5 VOL (J41)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV1 VOL (J44)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j44_on):
        screen.log_signal.emit("NAV1 VOL (J44) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV1 VOL (J44)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("E67", result["observation"])   # 11.95 V
        write_excel("K67", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav1']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav1']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav1']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("E69", result["observation"])   # 11.95 V
        write_excel("K69", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav1']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav1']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("E71", result["observation"])   # 11.95 V
        write_excel("K71", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV1 VOL (J44)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j44_off):
        screen.log_signal.emit("NAV1 VOL (J44) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV1 VOL (J44)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV2 VOL (J45)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j45_on):
        screen.log_signal.emit("NAV2 VOL (J45) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV2 VOL (J45)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("F67", result["observation"])   # 11.95 V
        write_excel("K67", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav2']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav2']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav2']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("F69", result["observation"])   # 11.95 V
        write_excel("K69", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav2']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav2']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("F71", result["observation"])   # 11.95 V
        write_excel("K71", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV2 VOL (J45)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j45_off):
        screen.log_signal.emit("NAV2 VOL (J45) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV2 VOL (J45)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV3 VOL (J46)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j46_on):
        screen.log_signal.emit("NAV3 VOL (J46) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV3 VOL (J46)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("G67", result["observation"])   # 11.95 V
        write_excel("K67", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav3']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav3']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav3']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("G69", result["observation"])   # 11.95 V
        write_excel("K69", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav3']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav3']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("G71", result["observation"])   # 11.95 V
        write_excel("K71", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV3 VOL (J46)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j46_off):
        screen.log_signal.emit("NAV3 VOL (J46) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV3 VOL (J46)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV4 VOL (J47)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j47_on):
        screen.log_signal.emit("NAV4 VOL (J47) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV4 VOL (J47)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("H67", result["observation"])   # 11.95 V
        write_excel("K67", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav4']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav4']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav4']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("H69", result["observation"])   # 11.95 V
        write_excel("K69", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav4']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav4']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("H71", result["observation"])   # 11.95 V
        write_excel("K71", result["result"])        # PASS  
    
    screen.log_signal.emit("Disconnecting NAV4 VOL (J47)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j47_off):
        screen.log_signal.emit("NAV4 VOL (J47) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV4 VOL (J47)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV5 VOL (J48)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j48_on):
        screen.log_signal.emit("NAV5 VOL (J48) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV5 VOL (J48)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("I67", result["observation"])   # 11.95 V
        write_excel("K67", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav5']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav5']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav5']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("I69", result["observation"])   # 11.95 V
        write_excel("K69", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav5']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav5']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("I71", result["observation"])   # 11.95 V
        write_excel("K71", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV5 VOL (J48)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j48_off):
        screen.log_signal.emit("NAV5 VOL (J48) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV5 VOL (J48)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connecting DMM +ve lead to NAV6 VOL (J49)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j49_on):
        screen.log_signal.emit("NAV6 VOL (J49) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NAV6 VOL (J49)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading","10V","12V")
    if result:
        write_excel("J67", result["observation"])   # 11.95 V
        write_excel("K67", result["result"])        # PASS
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Slowly Rotate {names['nav6']} knob Clockwise till Lower Voltage \n"
        f"• {names['nav6']} knob should be rotated less than 1/4th rotation\n",
        RESOURCES_DIR / "knob14.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav6']} knob rotated less than 1/4th rotation.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,None) 
    if result:
        write_excel("J69", result["observation"])   # 11.95 V
        write_excel("K69", result["result"])        # PASS
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        f"• Rotate {names['nav6']} knob fully Clockwise \n",
        RESOURCES_DIR / "knob_fc.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit(f"{names['nav6']} knob rotated fully clockwise.", False)
    result=dmm_reader.read_voltage(screen,"Multimeter Reading",None,"0.2V")
    if result:
        write_excel("J71", result["observation"])   # 11.95 V
        write_excel("K71", result["result"])        # PASS
    
    screen.log_signal.emit("Disconnecting NAV6 VOL (J49)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j49_off):
        screen.log_signal.emit("NAV6 VOL (J49) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NAV6 VOL (J49)", True)
        

    QApplication.processEvents()
    
    time.sleep(2)   
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• TX SEL knobs fully ccw and put to OUT position.\n"
        "• RX SEL knobs fully ccw.\n",
        RESOURCES_DIR / images["txrxsel"],"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    screen.log_signal.emit("============ VOLTAGE MEASUREMENTS TEST COMPLETED =============", False)
    
def alh1_norm(screen):   _run_norm_impl(screen, _NAMES["N200 - ALH1"], _IMAGES["N200 - ALH1"])
def alh2_norm(screen):   _run_norm_impl(screen, _NAMES["N200 - ALH2"], _IMAGES["N200 - ALH2"])
def alh3_norm(screen):   _run_norm_impl(screen, _NAMES["N200 - ALH3"], _IMAGES["N200 - ALH3"])

def run_stby_1(screen):  _run_stby_impl(screen, _NAMES["N200 - ALH1"], _IMAGES["N200 - ALH1"])
def run_stby_2(screen):  _run_stby_impl(screen, _NAMES["N200 - ALH2"], _IMAGES["N200 - ALH2"])
def run_stby_3(screen):  _run_stby_impl(screen, _NAMES["N200 - ALH3"], _IMAGES["N200 - ALH3"])  
  
def run_stby(screen):
    model = screen.alhx_combo.currentText().strip()
    jmodel=screen.jbox_combo.currentText().strip()

    if model == "N200 - ALH1" and jmodel=="No Junction Box":
        run_stby_1(screen)

    elif model == "N200 - ALH2" and jmodel=="No Junction Box":
        run_stby_2(screen)

    elif model == "N200 - ALH3" and jmodel=="No Junction Box":
        run_stby_3(screen)

    else:
        screen.log_signal.emit(f"ERROR: Invalid ALHx model selected: {model}", True)
        return
    
def run_norm(screen):
    model = screen.alhx_combo.currentText().strip()
    jmodel=screen.jbox_combo.currentText().strip()

    if model == "N200 - ALH1" and jmodel=="No Junction Box":
        alh1_norm(screen)

    elif model == "N200 - ALH2" and jmodel=="No Junction Box":
        alh2_norm(screen)

    elif model == "N200 - ALH3" and jmodel=="No Junction Box":
        alh3_norm(screen)

    else:
        screen.log_signal.emit(f"ERROR: Invalid ALHx model selected: {model}", True)
        return