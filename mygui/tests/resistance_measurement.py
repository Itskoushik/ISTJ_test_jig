from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from core.dmm_reader import read_resistance
from core.excel_logger import write_excel   

def alh1_stby(screen):
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Step 1: Connecting DMM +ve lead to PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j54_on():
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY connector (J54)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "PRIVATE KEY connector (J54)", "1M")
    
    if result:
        write_excel("E88", result["observation"])  
        write_excel("F88", result["result"])  
    
    screen.log_signal.emit("Step 2: Switching PRIVATE KEY Switch (S33) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_on():
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY Switch (S33)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "PRIVATE KEY switch (S33)",None, "50")
    if result:
        write_excel("E89", result["observation"])  
        write_excel("F89", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 3: Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY Switch (S33)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: Disconnecting PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j54_off():
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY connector (J54)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
        
    screen.log_signal.emit("Step 5: Connecting DMM +ve lead to ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j43_on():
        screen.log_signal.emit("ICS VOL connector (J43) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON ICS VOL connector (J43)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43)",None, "50")
    
    if result:
        write_excel("E90", result["observation"])  
        write_excel("F90", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to 12 o'clock position.\n",
        RESOURCES_DIR / "ics_12.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43) at 12 o'clock position","0.5k", "1.5k")
    
    if result:
        write_excel("E91", result["observation"])  
        write_excel("F91", result["result"])  
       # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully counter clockwise position.\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43) after rotating fully counter clockwise","8k", "12k")
    if result:
        write_excel("E92", result["observation"])  
        write_excel("F92", result["result"])  
    
    
    screen.log_signal.emit("Step 6: Disconnecting ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j43_off():
        screen.log_signal.emit("ICS VOL connector (J43) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF ICS VOL connector (J43)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 7: Connecting DMM +ve lead to NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j36_on():
        screen.log_signal.emit("NORM SEL connector (J36) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NORM SEL connector (J36)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "NORM SEL connector (J36)", "1M")
    if result:
        write_excel("E93", result["observation"])  
        write_excel("F93", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 8: Disconnecting NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j36_off():
        screen.log_signal.emit("NORM SEL connector (J36) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NORM SEL connector (J36)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to STBY.\n",
        RESOURCES_DIR / "stby.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "NORM SEL connector (J36) at STBY position",None, "50")
    if result:
        write_excel("E94", result["observation"])  
        write_excel("F94", result["result"])  

    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to NORMAL.\n",
        RESOURCES_DIR / "normal.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("✓ RESISTANCE MEASUREMENTS TEST COMPLETED", False)
    time.sleep(0.5)
    
    
def alh3_stby(screen):
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Step 5: Connecting DMM +ve lead to OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j52_on():
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON OVERRIDE KEY connector (J52)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "OVERRIDE KEY connector (J52)", "1M")

    if result:
        write_excel("E77", result["observation"])  
        write_excel("F77", result["result"])  
            

    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press O/R Switch.\n"
        "• ON indicator should light up green.\n",
        RESOURCES_DIR / "or_switch.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_resistance(screen, "O/R switch",None, "50")

    if result:
        write_excel("E79", result["observation"])  
        write_excel("F79", result["result"])        
    

    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press O/R Switch.\n"
        "• ON indicator should get extinguished.\n",
        RESOURCES_DIR / "or_switch.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E81",operator)   # YES
    write_excel("F81",result)     # PASS  
    
    screen.log_signal.emit("Step 6: Disconnecting OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j52_off():
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF OVERRIDE KEY connector (J52)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    
    
    # screen.log_signal.emit("Step 7: Connecting DMM +ve lead to PRIVATE KEY connector (J54)", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.set_j54_on():
    #     screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned ON", False)
    #     time.sleep(0.5)
        
    # else:
    #     screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY connector (J54)", True)
    #     return

    # QApplication.processEvents()
    # time.sleep(2)
    
    # result = read_resistance(screen, "PRIVATE KEY connector (J54)", "1M")
    
    # if result:
    #     write_excel("E88", result["observation"])  
    #     write_excel("F88", result["result"])  
    
    # screen.log_signal.emit("Step 8: Switching PRIVATE KEY Switch (S33) to UP position", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.set_s33_on():
    #     screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned ON", False)
    #     time.sleep(0.5)
        
    # else:
    #     screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY Switch (S33)", True)
    #     return

    # QApplication.processEvents()
    # time.sleep(2)
    
    # result = read_resistance(screen, "PRIVATE KEY switch (S33)",None, "50")
    # if result:
    #     write_excel("E89", result["observation"])  
    #     write_excel("F89", result["result"])  
    # else:
    #     screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
    #     return   # stop test if DMM not connected
    
    # screen.log_signal.emit("Step 9: Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.set_s33_off():
    #     screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned OFF", False)
    #     time.sleep(0.5)
        
    # else:
    #     screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY Switch (S33)", True)
    #     return

    # QApplication.processEvents()
    # time.sleep(2)
    
    # screen.log_signal.emit("Step 10: Disconnecting PRIVATE KEY connector (J54)", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.set_j54_off():
    #     screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned OFF", False)
    #     time.sleep(0.5)
        
    # else:
    #     screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY connector (J54)", True)
    #     return

    # QApplication.processEvents()
    # time.sleep(2)
        
    # screen.log_signal.emit("Step 11: Connecting DMM +ve lead to ICS VOL connector (J43)", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.set_j43_on():
    #     screen.log_signal.emit("ICS VOL connector (J43) successfully turned ON", False)
    #     time.sleep(0.5)
        
    # else:
    #     screen.log_signal.emit("ERROR: Failed to turn ON ICS VOL connector (J43)", True)
    #     return

    # QApplication.processEvents()
    # time.sleep(2)
    
    # result = read_resistance(screen, "ICS VOL connector (J43)",None, "50")
    
    # if result:
    #     write_excel("E90", result["observation"])  
    #     write_excel("F90", result["result"])  
    # else:
    #     screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
    #     return   # stop test if DMM not connected
    
    # # 🛑 PAUSE POINT
    # screen.operator_event.clear()
    # screen.show_popup_signal.emit(
    #     "⚠ Operator Action Required",
    #     "• Rotate ICS VOL to 12 o'clock position.\n",
    #     RESOURCES_DIR / "ics_12.jpeg","ok",None
    # )
    # # ⏸ WAIT until operator clicks OK
    # screen.operator_event.wait()
    
    # time.sleep(2)
    
    # result = read_resistance(screen, "ICS VOL connector (J43) at 12 o'clock position","0.5k", "1.5k")
    
    # if result:
    #     write_excel("E91", result["observation"])  
    #     write_excel("F91", result["result"])  
    #    # stop test if DMM not connected
    
    # # 🛑 PAUSE POINT
    # screen.operator_event.clear()
    # screen.show_popup_signal.emit(
    #     "⚠ Operator Action Required",
    #     "• Rotate ICS VOL to Fully counter clockwise position.\n",
    #     RESOURCES_DIR / "ics_fully_ccw.jpeg","ok",None
    # )
    # # ⏸ WAIT until operator clicks OK
    # screen.operator_event.wait()
    
    # time.sleep(2)
    
    # result = read_resistance(screen, "ICS VOL connector (J43) after rotating fully counter clockwise","8k", "12k")
    # if result:
    #     write_excel("E92", result["observation"])  
    #     write_excel("F92", result["result"])  
    
    
    # screen.log_signal.emit("Step 12: Disconnecting ICS VOL connector (J43)", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.set_j43_off():
    #     screen.log_signal.emit("ICS VOL connector (J43) successfully turned OFF", False)
    #     time.sleep(0.5)
        
    # else:
    #     screen.log_signal.emit("ERROR: Failed to turn OFF ICS VOL connector (J43)", True)
    #     return

    # QApplication.processEvents()
    # time.sleep(2)
    
    # screen.log_signal.emit("Step 13: Connecting DMM +ve lead to NORM SEL connector (J36)", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.set_j36_on():
    #     screen.log_signal.emit("NORM SEL connector (J36) successfully turned ON", False)
    #     time.sleep(0.5)
        
    # else:
    #     screen.log_signal.emit("ERROR: Failed to turn ON NORM SEL connector (J36)", True)
    #     return

    # QApplication.processEvents()
    # time.sleep(2)
    
    # result = read_resistance(screen, "NORM SEL connector (J36)", "1M")
    # if result:
    #     write_excel("E93", result["observation"])  
    #     write_excel("F93", result["result"])  
    # else:
    #     screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
    #     return   # stop test if DMM not connected
    
    # screen.log_signal.emit("Step 14: Disconnecting NORM SEL connector (J36)", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.set_j36_off():
    #     screen.log_signal.emit("NORM SEL connector (J36) successfully turned OFF", False)
    #     time.sleep(0.5)
        
    # else:
    #     screen.log_signal.emit("ERROR: Failed to turn OFF NORM SEL connector (J36)", True)
    #     return

    # QApplication.processEvents()
    # time.sleep(2)
    
    # # 🛑 PAUSE POINT
    # screen.operator_event.clear()
    # screen.show_popup_signal.emit(
    #     "⚠ Operator Action Required",
    #     "• Set STBY/NORMAL Switch to STBY.\n",
    #     RESOURCES_DIR / "stby.jpeg","ok",None
    # )
    # # ⏸ WAIT until operator clicks OK
    # screen.operator_event.wait()
    
    # time.sleep(2)
    
    # result = read_resistance(screen, "NORM SEL connector (J36) at STBY position",None, "50")
    # if result:
    #     write_excel("E94", result["observation"])  
    #     write_excel("F94", result["result"])  

    
    # # 🛑 PAUSE POINT
    # screen.operator_event.clear()
    # screen.show_popup_signal.emit(
    #     "⚠ Operator Action Required",
    #     "• Set STBY/NORMAL Switch to NORMAL.\n",
    #     RESOURCES_DIR / "normal.jpeg","ok",None
    # )
    # # ⏸ WAIT until operator clicks OK
    # screen.operator_event.wait()
    
    # time.sleep(2)
    
    # screen.log_signal.emit("✓ RESISTANCE MEASUREMENTS TEST COMPLETED", False)
    # time.sleep(0.5)    
    
def alh2_stby(screen):             
        
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Step 1: Connecting DMM +ve lead to OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j52_on():
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON OVERRIDE KEY connector (J52)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    #multimeter measurement
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press O/R Switch.\n"
        "• ON indicator should light up green.\n",
        RESOURCES_DIR / "or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2) 
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press O/R Switch.\n"
        "• ON indicator should get extinguished.\n",
        RESOURCES_DIR / "or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 2: Disconnecting OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j52_off():
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF OVERRIDE KEY connector (J52)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    #multimeter measurement
    
    screen.log_signal.emit("Step 3: Connecting DMM +ve lead to SONIC KEY connector (J53)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j53_on():
        screen.log_signal.emit("SONIC KEY connector (J53) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON SONIC KEY connector (J53)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    #multimeter measurement
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press SONIC Switch.\n"
        "• ON indicator should light up green.\n",
        RESOURCES_DIR / "sonic.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    
    #multimeter measurement
    time.sleep(2) 
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press SONIC Switch.\n"
        "• ISO indicator should get extinguished.\n",
        RESOURCES_DIR / "sonic.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: Disconnecting SONIC KEY connector (J53)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j53_off():
        screen.log_signal.emit("SONIC KEY connector (J53) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF SONIC KEY connector (J53)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    #multimeter measurement
    
    screen.log_signal.emit("✓ RESISTANCE MEASUREMENTS TEST COMPLETED", False)
    time.sleep(0.5)







def alh1_norm(screen):             
        
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Step 1: Connecting DMM +ve lead to MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j51_on():
        screen.log_signal.emit("MUTE KEY connector (J51) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON MUTE KEY connector (J51)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "MUTE KEY connector (J51)", "1M")

    if result:
        write_excel("E75", result["observation"])
        write_excel("F75", result["result"])        

    
    screen.log_signal.emit("Step 2: Switching MUTE KEY Switch (S34) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON MUTE KEY Switch (S34)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "MUTE KEY switch (S34)",None, "50")

    if result:
        write_excel("E76", result["observation"])  
        write_excel("F76", result["result"])        
    else:
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 3: Switching MUTE KEY Switch (S34) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF MUTE KEY Switch (S34)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: Disconnecting MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j51_off():
        screen.log_signal.emit("MUTE KEY connector (J51) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF MUTE KEY connector (J51)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 5: Connecting DMM +ve lead to PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j54_on():
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY connector (J54)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "PRIVATE KEY connector (J54)", "1M")
    
    if result:
        write_excel("E88", result["observation"])  
        write_excel("F88", result["result"])  
    
    screen.log_signal.emit("Step 6: Switching PRIVATE KEY Switch (S33) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_on():
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY Switch (S33)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "PRIVATE KEY switch (S33)",None, "50")
    if result:
        write_excel("E89", result["observation"])  
        write_excel("F89", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 7: Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY Switch (S33)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 8: Disconnecting PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j54_off():
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY connector (J54)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
        
    screen.log_signal.emit("Step 9: Connecting DMM +ve lead to ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j43_on():
        screen.log_signal.emit("ICS VOL connector (J43) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON ICS VOL connector (J43)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43)",None, "50")
    
    if result:
        write_excel("E90", result["observation"])  
        write_excel("F90", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to 12 o'clock position.\n",
        RESOURCES_DIR / "ics_12.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43) at 12 o'clock position","0.5k", "1.5k")
    
    if result:
        write_excel("E91", result["observation"])  
        write_excel("F91", result["result"])  
       # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully counter clockwise position.\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43) after rotating fully counter clockwise","8k", "12k")
    if result:
        write_excel("E92", result["observation"])  
        write_excel("F92", result["result"])  
    
    
    screen.log_signal.emit("Step 10: Disconnecting ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j43_off():
        screen.log_signal.emit("ICS VOL connector (J43) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF ICS VOL connector (J43)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 11: Connecting DMM +ve lead to NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j36_on():
        screen.log_signal.emit("NORM SEL connector (J36) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NORM SEL connector (J36)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "NORM SEL connector (J36)", "1M")
    if result:
        write_excel("E93", result["observation"])  
        write_excel("F93", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 12: Disconnecting NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j36_off():
        screen.log_signal.emit("NORM SEL connector (J36) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NORM SEL connector (J36)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to STBY.\n",
        RESOURCES_DIR / "stby.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "NORM SEL connector (J36) at STBY position",None, "50")
    if result:
        write_excel("E94", result["observation"])  
        write_excel("F94", result["result"])  

    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to NORMAL.\n",
        RESOURCES_DIR / "normal.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("✓ RESISTANCE MEASUREMENTS TEST COMPLETED", False)
    time.sleep(0.5)
    
def alh3_norm(screen):             
        
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Step 1: Connecting DMM +ve lead to MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j51_on():
        screen.log_signal.emit("MUTE KEY connector (J51) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON MUTE KEY connector (J51)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "MUTE KEY connector (J51)", "1M")

    if result:
        write_excel("E75", result["observation"])
        write_excel("F75", result["result"])        

    
    screen.log_signal.emit("Step 2: Switching MUTE KEY Switch (S34) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON MUTE KEY Switch (S34)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "MUTE KEY switch (S34)",None, "50")

    if result:
        write_excel("E76", result["observation"])  
        write_excel("F76", result["result"])        
    else:
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 3: Switching MUTE KEY Switch (S34) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF MUTE KEY Switch (S34)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: Disconnecting MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j51_off():
        screen.log_signal.emit("MUTE KEY connector (J51) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF MUTE KEY connector (J51)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 5: Connecting DMM +ve lead to OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j52_on():
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON OVERRIDE KEY connector (J52)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "OVERRIDE KEY connector (J52)", "1M")

    if result:
        write_excel("E77", result["observation"])  
        write_excel("F77", result["result"])  
            

    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press O/R Switch.\n"
        "• ON indicator should light up green.\n",
        RESOURCES_DIR / "or_switch.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_resistance(screen, "O/R switch",None, "50")

    if result:
        write_excel("E79", result["observation"])  
        write_excel("F79", result["result"])        
    

    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press O/R Switch.\n"
        "• ON indicator should get extinguished.\n",
        RESOURCES_DIR / "or_switch.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E81",operator)   # YES
    write_excel("F81",result)     # PASS  
    
    screen.log_signal.emit("Step 6: Disconnecting OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j52_off():
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF OVERRIDE KEY connector (J52)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    
    
    screen.log_signal.emit("Step 7: Connecting DMM +ve lead to PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j54_on():
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY connector (J54)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "PRIVATE KEY connector (J54)", "1M")
    
    if result:
        write_excel("E88", result["observation"])  
        write_excel("F88", result["result"])  
    
    screen.log_signal.emit("Step 8: Switching PRIVATE KEY Switch (S33) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_on():
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY Switch (S33)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "PRIVATE KEY switch (S33)",None, "50")
    if result:
        write_excel("E89", result["observation"])  
        write_excel("F89", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 9: Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY Switch (S33)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 10: Disconnecting PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j54_off():
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY connector (J54)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
        
    screen.log_signal.emit("Step 11: Connecting DMM +ve lead to ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j43_on():
        screen.log_signal.emit("ICS VOL connector (J43) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON ICS VOL connector (J43)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43)",None, "50")
    
    if result:
        write_excel("E90", result["observation"])  
        write_excel("F90", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to 12 o'clock position.\n",
        RESOURCES_DIR / "ics_12.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43) at 12 o'clock position","0.5k", "1.5k")
    
    if result:
        write_excel("E91", result["observation"])  
        write_excel("F91", result["result"])  
       # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully counter clockwise position.\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43) after rotating fully counter clockwise","8k", "12k")
    if result:
        write_excel("E92", result["observation"])  
        write_excel("F92", result["result"])  
    
    
    screen.log_signal.emit("Step 12: Disconnecting ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j43_off():
        screen.log_signal.emit("ICS VOL connector (J43) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF ICS VOL connector (J43)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 13: Connecting DMM +ve lead to NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j36_on():
        screen.log_signal.emit("NORM SEL connector (J36) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NORM SEL connector (J36)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "NORM SEL connector (J36)", "1M")
    if result:
        write_excel("E93", result["observation"])  
        write_excel("F93", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 14: Disconnecting NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j36_off():
        screen.log_signal.emit("NORM SEL connector (J36) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NORM SEL connector (J36)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to STBY.\n",
        RESOURCES_DIR / "stby.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "NORM SEL connector (J36) at STBY position",None, "50")
    if result:
        write_excel("E94", result["observation"])  
        write_excel("F94", result["result"])  

    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to NORMAL.\n",
        RESOURCES_DIR / "normal.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("✓ RESISTANCE MEASUREMENTS TEST COMPLETED", False)
    time.sleep(0.5)
    
def alh2_norm(screen):             
        
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Step 1: Connecting DMM +ve lead to MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j51_on():
        screen.log_signal.emit("MUTE KEY connector (J51) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON MUTE KEY connector (J51)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "MUTE KEY connector (J51)", "1M")

    if result:
        write_excel("E75", result["observation"])
        write_excel("F75", result["result"])        

    
    screen.log_signal.emit("Step 2: Switching MUTE KEY Switch (S34) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON MUTE KEY Switch (S34)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "MUTE KEY switch (S34)",None, "50")

    if result:
        write_excel("E76", result["observation"])  
        write_excel("F76", result["result"])        
    else:
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 3: Switching MUTE KEY Switch (S34) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF MUTE KEY Switch (S34)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: Disconnecting MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j51_off():
        screen.log_signal.emit("MUTE KEY connector (J51) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF MUTE KEY connector (J51)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 5: Connecting DMM +ve lead to OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j52_on():
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON OVERRIDE KEY connector (J52)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "OVERRIDE KEY connector (J52)", "1M")

    if result:
        write_excel("E77", result["observation"])  
        write_excel("F77", result["result"])  
            

    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press O/R Switch.\n"
        "• ON indicator should light up green.\n",
        RESOURCES_DIR / "or_switch.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = read_resistance(screen, "O/R switch",None, "50")

    if result:
        write_excel("E79", result["observation"])  
        write_excel("F79", result["result"])        
    

    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press O/R Switch.\n"
        "• ON indicator should get extinguished.\n",
        RESOURCES_DIR / "or_switch.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E81",operator)   # YES
    write_excel("F81",result)     # PASS  
    
    screen.log_signal.emit("Step 6: Disconnecting OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j52_off():
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF OVERRIDE KEY connector (J52)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 7: Connecting DMM +ve lead to SONIC KEY connector (J53)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j53_on():
        screen.log_signal.emit("SONIC KEY connector (J53) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON SONIC KEY connector (J53)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "SONIC KEY connector (J53)", "1M")

    if result:
        write_excel("E82", result["observation"])  
        write_excel("F82", result["result"])  
            

    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press SONIC Switch.\n"
        "• ISO indicator should light up green.\n",
        RESOURCES_DIR / "sonic.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    
    result = read_resistance(screen, "SONIC KEY connector (J53) after pressing SONIC Switch",None, "50")
    if result:
        write_excel("E84", result["observation"])  
        write_excel("F84", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press SONIC Switch.\n"
        "• ISO indicator should get extinguished.\n",
        RESOURCES_DIR / "sonic.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E86",operator)   # YES
    write_excel("F86",result)     # PASS
    
    
    screen.log_signal.emit("Step 8: Disconnecting SONIC KEY connector (J53)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j53_off():
        screen.log_signal.emit("SONIC KEY connector (J53) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF SONIC KEY connector (J53)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 9: Connecting DMM +ve lead to PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j54_on():
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY connector (J54)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "PRIVATE KEY connector (J54)", "1M")
    
    if result:
        write_excel("E88", result["observation"])  
        write_excel("F88", result["result"])  
    
    screen.log_signal.emit("Step 10: Switching PRIVATE KEY Switch (S33) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_on():
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON PRIVATE KEY Switch (S33)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "PRIVATE KEY switch (S33)",None, "50")
    if result:
        write_excel("E89", result["observation"])  
        write_excel("F89", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 11: Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY Switch (S33)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 12: Disconnecting PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j54_off():
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF PRIVATE KEY connector (J54)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
        
    screen.log_signal.emit("Step 13: Connecting DMM +ve lead to ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j43_on():
        screen.log_signal.emit("ICS VOL connector (J43) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON ICS VOL connector (J43)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43)",None, "50")
    
    if result:
        write_excel("E90", result["observation"])  
        write_excel("F90", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to 12 o'clock position.\n",
        RESOURCES_DIR / "ics_12.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43) at 12 o'clock position","0.5k", "1.5k")
    
    if result:
        write_excel("E91", result["observation"])  
        write_excel("F91", result["result"])  
       # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully counter clockwise position.\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "ICS VOL connector (J43) after rotating fully counter clockwise","8k", "12k")
    if result:
        write_excel("E92", result["observation"])  
        write_excel("F92", result["result"])  
    
    
    screen.log_signal.emit("Step 14: Disconnecting ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j43_off():
        screen.log_signal.emit("ICS VOL connector (J43) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF ICS VOL connector (J43)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 15: Connecting DMM +ve lead to NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j36_on():
        screen.log_signal.emit("NORM SEL connector (J36) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NORM SEL connector (J36)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    result = read_resistance(screen, "NORM SEL connector (J36)", "1M")
    if result:
        write_excel("E93", result["observation"])  
        write_excel("F93", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        return   # stop test if DMM not connected
    
    screen.log_signal.emit("Step 16: Disconnecting NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j36_off():
        screen.log_signal.emit("NORM SEL connector (J36) successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF NORM SEL connector (J36)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to STBY.\n",
        RESOURCES_DIR / "stby.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    result = read_resistance(screen, "NORM SEL connector (J36) at STBY position",None, "50")
    if result:
        write_excel("E94", result["observation"])  
        write_excel("F94", result["result"])  

    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to NORMAL.\n",
        RESOURCES_DIR / "normal.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("✓ RESISTANCE MEASUREMENTS TEST COMPLETED", False)
    time.sleep(0.5)
def run_norm(screen):
    model = screen.alhx_combo.currentText().strip()
    jmodel=screen.jbox_combo.currentText().strip()

    if model == "ALH1" and jmodel=="No Junction Box":
        alh1_norm(screen)

    elif model == "ALH2" and jmodel=="No Junction Box":
        alh2_norm(screen)

    elif model == "ALH3" and jmodel=="No Junction Box":
        alh3_norm(screen)

    else:
        screen.log_signal.emit(f"ERROR: Invalid ALHx model selected: {model}", True)
        return
    
    
def run_stby(screen):
    model = screen.alhx_combo.currentText().strip()
    jmodel=screen.jbox_combo.currentText().strip()

    if model == "ALH1" and jmodel=="No Junction Box":
        alh1_stby(screen)

    elif model == "ALH2" and jmodel=="No Junction Box":
        alh2_stby(screen)

    elif model == "ALH3" and jmodel=="No Junction Box":
        alh3_stby(screen)

    else:
        screen.log_signal.emit(f"ERROR: Invalid ALHx model selected: {model}", True)
        return