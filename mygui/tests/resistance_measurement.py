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
def alh1_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)
    set_popup_title("RESISTANCE MEASUREMENTS TEST (STBY)")
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Connected DMM +ve lead to PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j54_on):
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect PRIVATE KEY connector (J54)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")
    
    if result:
        write_excel("E88", result["observation"])  
        write_excel("F88", result["result"])  
    
    screen.log_signal.emit("Switching PRIVATE KEY Switch (S33) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_on):
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully set to UP position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE KEY Switch (S33) to UP position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E89", result["observation"])  
        write_excel("F89", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
           # stop test if DMM not connected
    
    screen.log_signal.emit("Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_off):
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully set to DOWN position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE KEY Switch (S33) to DOWN position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Disconnecting PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j54_off):
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PRIVATE KEY connector (J54)", True)
        

    QApplication.processEvents()
    time.sleep(2)
        
    screen.log_signal.emit("===========RESISTANCE MEASUREMENTS TEST COMPLETED============", False)
    time.sleep(0.5)
    
    
def alh3_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)
    set_popup_title("RESISTANCE MEASUREMENTS TEST (STBY)")
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Connected DMM +ve lead to OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j52_on):
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect OVERRIDE KEY connector (J52)", True)

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E78", result["observation"])  
        write_excel("F78", result["result"])  
            

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press CALL Switch.\n"
        "• ON indicator should light up green.\n",
        RESOURCES_DIR / "call.jpg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Pressed CALL Switch and ON indicator lit up green", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")

    if result:
        write_excel("E80", result["observation"])  
        write_excel("F80", result["result"])        
    

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press CALL Switch.\n"
        "• ON indicator should get extinguished.\n",
        RESOURCES_DIR / "call.jpg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Pressed CALL Switch and ON indicator got extinguished", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E81",operator)   # YES
    write_excel("F81",result)     # PASS  
    
    screen.log_signal.emit("Disconnecting OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j52_off):
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect OVERRIDE KEY connector (J52)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("===========RESISTANCE MEASUREMENTS TEST COMPLETED============", False)
    time.sleep(0.5)
    
def alh2_stby(screen):   
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)          
    set_popup_title("RESISTANCE MEASUREMENTS TEST (STBY)")
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Connected DMM +ve lead to OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j52_on):
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect OVERRIDE KEY connector (J52)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E78", result["observation"])
        write_excel("F78", result["result"])     
    
    # 🛑 PAUSE POINT
    screen.check_abort()
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
    screen.log_signal.emit("Pressed O/R Switch and ON indicator lit up green", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")

    if result:
        write_excel("E80", result["observation"])  
        write_excel("F80", result["result"])     
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
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
    screen.log_signal.emit("Pressed O/R Switch and ON indicator got extinguished", False)
    screen.log_signal.emit("Disconnecting OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j52_off):
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect OVERRIDE KEY connector (J52)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
       
    
    screen.log_signal.emit("Connected DMM +ve lead to SONIC KEY connector (J53)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j53_on):
        screen.log_signal.emit("SONIC KEY connector (J53) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect SONIC KEY connector (J53)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E83", result["observation"])  
        write_excel("F83", result["result"])  
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press SONIC Switch.\n"
        "• ISO indicator should light up green.\n",
        RESOURCES_DIR / "sonic.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    
    screen.log_signal.emit("Pressed SONIC Switch and ISO indicator lit up green", False)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E85", result["observation"])  
        write_excel("F85", result["result"])  
    time.sleep(2) 
    
    # 🛑 PAUSE POINT
    screen.check_abort()
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
    screen.log_signal.emit("Pressed SONIC Switch and ISO indicator got extinguished", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E87",operator)   # YES
    write_excel("F87",result)     # PASS
    
    screen.log_signal.emit("Disconnecting SONIC KEY connector (J53)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j53_off):
        screen.log_signal.emit("SONIC KEY connector (J53) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect SONIC KEY connector (J53)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("===========RESISTANCE MEASUREMENTS TEST COMPLETED============", False)
    time.sleep(0.5)







def alh1_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)             
    set_popup_title("RESISTANCE MEASUREMENTS TEST (NORM)")
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2)
    write_excel("E77","N/A")
    write_excel("F77","N/A")
    write_excel("E78","N/A")
    write_excel("F78","N/A")
    write_excel("E79","N/A")
    write_excel("F79","N/A")
    write_excel("E80","N/A")
    write_excel("F80","N/A")
    write_excel("E81","N/A")
    write_excel("F81","N/A")
    write_excel("E82","N/A")
    write_excel("F82","N/A")
    write_excel("E83","N/A")
    write_excel("F83","N/A")
    write_excel("E84","N/A")
    write_excel("F84","N/A")
    write_excel("E85","N/A")
    write_excel("F85","N/A")
    write_excel("E86","N/A")
    write_excel("F86","N/A")
    write_excel("E87","N/A")
    write_excel("F87","N/A")
    write_excel("E95","N/A")
    write_excel("F95","N/A")
    write_excel("E96","N/A")
    write_excel("F96","N/A")
    write_excel("E97","N/A")
    write_excel("F97","N/A")
    write_excel("E98","N/A")
    write_excel("F98","N/A") 
    
    screen.log_signal.emit("Connected DMM +ve lead to MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j51_on):
        screen.log_signal.emit("MUTE KEY connector (J51) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MUTE KEY connector (J51)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E75", result["observation"])
        write_excel("F75", result["result"])        

    
    screen.log_signal.emit("Switching MUTE KEY Switch (S34) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully set to UP position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE KEY Switch (S34) to UP position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")

    if result:
        write_excel("E76", result["observation"])  
        write_excel("F76", result["result"])        

    screen.log_signal.emit("Switching MUTE KEY Switch (S34) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully set to DOWN position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE KEY Switch (S34) to DOWN position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Disconnecting MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j51_off):
        screen.log_signal.emit("MUTE KEY connector (J51) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MUTE KEY connector (J51)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connected DMM +ve lead to PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j54_on):
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect PRIVATE KEY connector (J54)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")
    
    if result:
        write_excel("E88", result["observation"])  
        write_excel("F88", result["result"])  
    
    screen.log_signal.emit("Switching PRIVATE KEY Switch (S33) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_on):
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully set to UP position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE KEY Switch (S33) to UP position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E89", result["observation"])  
        write_excel("F89", result["result"])  
 # stop test if DMM not connected
    
    screen.log_signal.emit("Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_off):
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully set to DOWN position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE KEY Switch (S33) to DOWN position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Disconnecting PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j54_off):
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PRIVATE KEY connector (J54)", True)
    

    QApplication.processEvents()
    time.sleep(2)
        
    screen.log_signal.emit("Connected DMM +ve lead to ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j43_on):
        screen.log_signal.emit("ICS VOL connector (J43) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect ICS VOL connector (J43)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    
    if result:
        write_excel("E90", result["observation"])  
        write_excel("F90", result["result"])  

    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to 12 o'clock position.\n",
        RESOURCES_DIR / "ics_12.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to 12 o'clock position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "0.5k", "1.5k")
    
    if result:
        write_excel("E91", result["observation"])  
        write_excel("F91", result["result"])  
       # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully CCW position.\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to Fully CCW position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "8k", "12k")
    if result:
        write_excel("E92", result["observation"])  
        write_excel("F92", result["result"])  
    
    
    screen.log_signal.emit("Disconnecting ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j43_off):
        screen.log_signal.emit("ICS VOL connector (J43) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect ICS VOL connector (J43)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully CW position.\n",
        RESOURCES_DIR / "ics_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to Fully CW position", False)
    screen.log_signal.emit("Connected DMM +ve lead to NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j36_on):
        screen.log_signal.emit("NORM SEL connector (J36) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NORM SEL connector (J36)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")
    if result:
        write_excel("E93", result["observation"])  
        write_excel("F93", result["result"])  

    
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to STBY.\n",
        RESOURCES_DIR / "stby.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Set STBY/NORMAL Switch to STBY position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E94", result["observation"])  
        write_excel("F94", result["result"])  

    screen.log_signal.emit("Disconnecting NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j36_off):
        screen.log_signal.emit("NORM SEL connector (J36) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NORM SEL connector (J36)", True)
     

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to NORMAL.\n",
        RESOURCES_DIR / "normal.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Set STBY/NORMAL Switch to NORMAL position", False)
    screen.log_signal.emit("===========RESISTANCE MEASUREMENTS TEST COMPLETED============", False)
    time.sleep(0.5)
    
def alh3_norm(screen):  
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)           
    set_popup_title("RESISTANCE MEASUREMENTS TEST (NORM)")    
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    write_excel("E82","N/A")
    write_excel("F82","N/A")
    write_excel("E83","N/A")
    write_excel("F83","N/A")
    write_excel("E84","N/A")
    write_excel("F84","N/A")
    write_excel("E85","N/A")
    write_excel("F85","N/A")
    write_excel("E86","N/A")
    write_excel("F86","N/A")
    write_excel("E87","N/A")
    write_excel("F87","N/A")
    screen.log_signal.emit("Connected DMM +ve lead to MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j51_on):
        screen.log_signal.emit("MUTE KEY connector (J51) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MUTE KEY connector (J51)", True)
  

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E75", result["observation"])
        write_excel("F75", result["result"])        

    
    screen.log_signal.emit("Switching MUTE KEY Switch (S34) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully set to UP position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE KEY Switch (S34) to UP position", True)
       

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")

    if result:
        write_excel("E76", result["observation"])  
        write_excel("F76", result["result"])        

    
    screen.log_signal.emit("Switching MUTE KEY Switch (S34) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully set to DOWN position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE KEY Switch (S34) to DOWN position", True)
      

    QApplication.processEvents()
    time.sleep(2)

    
    screen.log_signal.emit("Disconnecting MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j51_off):
        screen.log_signal.emit("MUTE KEY connector (J51) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MUTE KEY connector (J51)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connected DMM +ve lead to OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j52_on):
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect OVERRIDE KEY connector (J52)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E77", result["observation"])  
        write_excel("F77", result["result"])  
            

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press CALL Switch.\n"
        "• ON indicator should light up green.\n",
        RESOURCES_DIR / "call.jpg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Pressed CALL Switch and ON indicator lit up green", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")

    if result:
        write_excel("E79", result["observation"])  
        write_excel("F79", result["result"])        
    

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press CALL Switch.\n"
        "• ON indicator should get extinguished.\n",
        RESOURCES_DIR / "call.jpg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Pressed CALL Switch and ON indicator got extinguished", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E81",operator)   # YES
    write_excel("F81",result)     # PASS  
    
    screen.log_signal.emit("Disconnecting OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j52_off):
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect OVERRIDE KEY connector (J52)", True)
   

    QApplication.processEvents()
    time.sleep(2)
    

    screen.log_signal.emit("Connected DMM +ve lead to PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j54_on):
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect PRIVATE KEY connector (J54)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")
    
    if result:
        write_excel("E88", result["observation"])  
        write_excel("F88", result["result"])  
    
    screen.log_signal.emit("Switching PRIVATE KEY Switch (S33) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_on):
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully set to UP position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE KEY Switch (S33) to UP position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E89", result["observation"])  
        write_excel("F89", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
           # stop test if DMM not connected
    
    screen.log_signal.emit("Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_off):
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully set to DOWN position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE KEY Switch (S33) to DOWN position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Disconnecting PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j54_off):
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PRIVATE KEY connector (J54)", True)
        

    QApplication.processEvents()
    time.sleep(2)
        
    screen.log_signal.emit("Connected DMM +ve lead to ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j43_on):
        screen.log_signal.emit("ICS VOL connector (J43) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect ICS VOL connector (J43)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    
    if result:
        write_excel("E90", result["observation"])  
        write_excel("F90", result["result"])  

           # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to 12 o'clock position.\n",
        RESOURCES_DIR / "ics_12.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to 12 o'clock position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading","0.5k", "1.5k")
    
    if result:
        write_excel("E91", result["observation"])  
        write_excel("F91", result["result"])  
       # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully CCW position.\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to Fully CCW position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading","8k", "12k")
    if result:
        write_excel("E92", result["observation"])  
        write_excel("F92", result["result"])  
    
    
    screen.log_signal.emit("Disconnecting ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j43_off):
        screen.log_signal.emit("ICS VOL connector (J43) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect ICS VOL connector (J43)", True)
       

    QApplication.processEvents()
    time.sleep(2)
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully CW position.\n",
        RESOURCES_DIR / "ics_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to Fully CW position", False)
    screen.log_signal.emit("Connected DMM +ve lead to NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j36_on):
        screen.log_signal.emit("NORM SEL connector (J36) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NORM SEL connector (J36)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")
    if result:
        write_excel("E93", result["observation"])  
        write_excel("F93", result["result"])  

    

    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to STBY.\n",
        RESOURCES_DIR / "stby.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Set STBY/NORMAL Switch to STBY position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E94", result["observation"])  
        write_excel("F94", result["result"])  

    screen.log_signal.emit("Disconnecting NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j36_off):
        screen.log_signal.emit("NORM SEL connector (J36) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NORM SEL connector (J36)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to NORMAL.\n",
        RESOURCES_DIR / "normal.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Set STBY/NORMAL Switch to NORMAL position", False)
    screen.log_signal.emit("===========RESISTANCE MEASUREMENTS TEST COMPLETED============", False)
    time.sleep(0.5)
    
def alh2_norm(screen):   
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)          
    set_popup_title("RESISTANCE MEASUREMENTS TEST (NORM)")
    screen.log_signal.emit("==========COMMENCING RESISTANCE MEASUREMENTS TEST==========", False)
    time.sleep(2) 
    
    screen.log_signal.emit("Connected DMM +ve lead to MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j51_on):
        screen.log_signal.emit("MUTE KEY connector (J51) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MUTE KEY connector (J51)", True)
       

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E75", result["observation"])
        write_excel("F75", result["result"])        

    
    screen.log_signal.emit("Switching MUTE KEY Switch (S34) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully set to UP position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE KEY Switch (S34) to UP position", True)
       

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")

    if result:
        write_excel("E76", result["observation"])  
        write_excel("F76", result["result"])        

    
    screen.log_signal.emit("Switching MUTE KEY Switch (S34) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE KEY Switch (S34) successfully set to DOWN position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE KEY Switch (S34) to DOWN position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Disconnecting MUTE KEY connector (J51)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j51_off):
        screen.log_signal.emit("MUTE KEY connector (J51) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MUTE KEY connector (J51)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connected DMM +ve lead to OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j52_on):
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect OVERRIDE KEY connector (J52)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E77", result["observation"])  
        write_excel("F77", result["result"])  
            

    # 🛑 PAUSE POINT
    screen.check_abort()
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
    screen.log_signal.emit("Pressed O/R Switch and ON indicator lit up green", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")

    if result:
        write_excel("E79", result["observation"])  
        write_excel("F79", result["result"])        
    

    # 🛑 PAUSE POINT
    screen.check_abort()
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
    screen.log_signal.emit("Pressed O/R Switch and ON indicator got extinguished", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E81",operator)   # YES
    write_excel("F81",result)     # PASS  
    
    screen.log_signal.emit("Disconnecting OVERRIDE KEY connector (J52)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j52_off):
        screen.log_signal.emit("OVERRIDE KEY connector (J52) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect OVERRIDE KEY connector (J52)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Connected DMM +ve lead to SONIC KEY connector (J53)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j53_on):
        screen.log_signal.emit("SONIC KEY connector (J53) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect SONIC KEY connector (J53)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")

    if result:
        write_excel("E82", result["observation"])  
        write_excel("F82", result["result"])  
            

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press SONIC Switch.\n"
        "• ISO indicator should light up green.\n",
        RESOURCES_DIR / "sonic.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    screen.log_signal.emit("Pressed SONIC Switch and ISO indicator lit up green", False)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E84", result["observation"])  
        write_excel("F84", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
        
    
    # 🛑 PAUSE POINT
    screen.check_abort()
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
    screen.log_signal.emit("Pressed SONIC Switch and ISO indicator got extinguished", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E86",operator)   # YES
    write_excel("F86",result)     # PASS
    
    
    screen.log_signal.emit("Disconnecting SONIC KEY connector (J53)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j53_off):
        screen.log_signal.emit("SONIC KEY connector (J53) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect SONIC KEY connector (J53)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Connected DMM +ve lead to PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j54_on):
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect PRIVATE KEY connector (J54)", True)
       

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")
    
    if result:
        write_excel("E88", result["observation"])  
        write_excel("F88", result["result"])  
    
    screen.log_signal.emit("Switching PRIVATE KEY Switch (S33) to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_on):
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully set to UP position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE KEY Switch (S33) to UP position", True)
       

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E89", result["observation"])  
        write_excel("F89", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
           # stop test if DMM not connected
    
    screen.log_signal.emit("Switching PRIVATE KEY Switch (S33) to DOWN position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_off):
        screen.log_signal.emit("PRIVATE KEY Switch (S33) successfully set to DOWN position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE KEY Switch (S33) to DOWN position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Disconnecting PRIVATE KEY connector (J54)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j54_off):
        screen.log_signal.emit("PRIVATE KEY connector (J54) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PRIVATE KEY connector (J54)", True)
        

    QApplication.processEvents()
    time.sleep(2)
        
    screen.log_signal.emit("Connected DMM +ve lead to ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j43_on):
        screen.log_signal.emit("ICS VOL connector (J43) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect ICS VOL connector (J43)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    
    if result:
        write_excel("E90", result["observation"])  
        write_excel("F90", result["result"])  
    else:
        screen.log_signal.emit("ERROR: DMM not connected or no reading obtained", True)
           # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to 12 o'clock position.\n",
        RESOURCES_DIR / "ics_12.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to 12 o'clock position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading","0.5k", "1.5k")
    
    if result:
        write_excel("E91", result["observation"])  
        write_excel("F91", result["result"])  
       # stop test if DMM not connected
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully CCW position.\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to Fully CCW position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading","8k", "12k")
    if result:
        write_excel("E92", result["observation"])  
        write_excel("F92", result["result"])  
    
    
    screen.log_signal.emit("Disconnecting ICS VOL connector (J43)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j43_off):
        screen.log_signal.emit("ICS VOL connector (J43) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect ICS VOL connector (J43)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS VOL to Fully CW position.\n",
        RESOURCES_DIR / "ics_cw.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Rotated ICS VOL to Fully CW position", False)
    
    screen.log_signal.emit("Connected DMM +ve lead to NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j36_on):
        screen.log_signal.emit("NORM SEL connector (J36) successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect NORM SEL connector (J36)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    result = dmm_reader.read_resistance(screen, "Multimeter Reading", "1M")
    if result:
        write_excel("E93", result["observation"])  
        write_excel("F93", result["result"])   
    
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to STBY.\n",
        RESOURCES_DIR / "stby.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Set STBY/NORMAL Switch to STBY position", False)
    result = dmm_reader.read_resistance(screen, "Multimeter Reading",None, "50")
    if result:
        write_excel("E94", result["observation"])  
        write_excel("F94", result["result"])  

    screen.log_signal.emit("Disconnecting NORM SEL connector (J36)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j36_off):
        screen.log_signal.emit("NORM SEL connector (J36) successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NORM SEL connector (J36)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set STBY/NORMAL Switch to NORMAL.\n",
        RESOURCES_DIR / "normal.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("Set STBY/NORMAL Switch to NORMAL position", False)
    screen.log_signal.emit("===========RESISTANCE MEASUREMENTS TEST COMPLETED============", False)
    time.sleep(0.5)
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
    
    
def run_stby(screen):
    model = screen.alhx_combo.currentText().strip()
    jmodel=screen.jbox_combo.currentText().strip()

    if model == "N200 - ALH1" and jmodel=="No Junction Box":
        alh1_stby(screen)

    elif model == "N200 - ALH2" and jmodel=="No Junction Box":
        alh2_stby(screen)

    elif model == "N200 - ALH3" and jmodel=="No Junction Box":
        alh3_stby(screen)

    else:
        screen.log_signal.emit(f"ERROR: Invalid ALHx model selected: {model}", True)
        return