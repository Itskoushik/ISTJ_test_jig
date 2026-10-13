from core.paths import RESOURCES_DIR
import time
from core.excel_logger import write_excel
from core.stm32_commands import STM32RelayController
from PyQt5.QtWidgets import QApplication
from core.oscilloscope_helper import set_ch1_ch2_scale_10v

def alh3_mod2(screen):
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)
    screen.log_signal.emit("==========COMMENCING TRANSIENT TEST==========", False)
    time.sleep(2)
    
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX  SEL Knobs to in position.\n",
        RESOURCES_DIR / "txselalh3on.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully set all TX SEL Knobs to in position", False)
    time.sleep(2)
    
    
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  CALL switch.\n"
        "• ON indicators should illuminate green\n",
        RESOURCES_DIR / "callgreen.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully pressed CALL switch and ON indicators illuminated", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E95",operator)   # YES
    write_excel("F95",result)     # PASS  
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Repeated Press RAD PTT switch.\n"
        "• ON indicators should Extinguish\n",
        RESOURCES_DIR / "radptton.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E96",operator)   # YES
    write_excel("F96",result)     # PASS  
    write_excel("D96","'ON' indicators should Extinguish")
    
    # doubt must be clarified
    screen.log_signal.emit("successfully repeated press RAD PTT switch", False)
    
    screen.log_signal.emit("Switching S30 switch to ON (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 switch successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30 switch", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• ON indicators should not Illuminate green.\n",
        RESOURCES_DIR / "nogreen.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("successfully checked that ON indicators are not illuminating", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E97",operator)   # YES
    write_excel("F97",result)     # PASS 
    write_excel("D97","'ON' indicators should not Illuminate") 
    screen.log_signal.emit("Switching S30 switch to OFF (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 switch successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30 switch", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  CALL switch.\n"
        "• ON indicators should Illuminate green\n",
        RESOURCES_DIR / "callgreen.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("successfully pressed CALL switch and ON indicators illuminated", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E98",operator)   # YES
    write_excel("F98",result)     # PASS  
    write_excel("D98","'ON' indicators should Illuminate")

    screen.log_signal.emit("===========TRANSIENT TEST COMPLETED============", False)
    time.sleep(0.5)
    
def alh3_mod345(screen):
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)
    screen.log_signal.emit("==========COMMENCING TRANSIENT TEST==========", False)
    time.sleep(2)
    
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX  SEL Knobs to in position.\n",
        RESOURCES_DIR / "txselalh3on.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully set all TX SEL Knobs to in position", False)
    time.sleep(2)
    
    
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  CALL switch.\n"
        "• ON indicators should illuminate green\n",
        RESOURCES_DIR / "callgreen.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully pressed and released CALL switch", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E95",operator)   # YES
    write_excel("F95",result)     # PASS  
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Repeated Press RAD PTT switch.\n"
        "• ON indicators should not Extinguish\n",
        RESOURCES_DIR / "radpttonn.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E96",operator)   # YES
    write_excel("F96",result)     # PASS  
    
    # doubt must be clarified
    screen.log_signal.emit("successfully repeated press RAD PTT switch", False)
    
    screen.log_signal.emit("Switching S30 switch to ON (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 switch successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30 switch", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• ON indicators should not Extinguish\n",
        RESOURCES_DIR / "ongreen.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully checked that ON indicators are not illuminating", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E97",operator)   # YES
    write_excel("F97",result)     # PASS  
    screen.log_signal.emit("Switching S30 switch to OFF (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 switch successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30 switch", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  CALL switch.\n"
        "• ON indicators should Extinguish\n",
        RESOURCES_DIR / "callnogreen.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("successfully pressed CALL switch and ON indicators extinguished", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E98",operator)   # YES
    write_excel("F98",result)     # PASS  
    
    screen.log_signal.emit("===========TRANSIENT TEST COMPLETED============", False)
    time.sleep(0.5)

       
def alh2_mod2(screen):  
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)
    
    screen.log_signal.emit("==========COMMENCING TRANSIENT TEST==========", False)
    time.sleep(2)
    
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX  SEL Knobs to in position.\n",
        RESOURCES_DIR / "txselalh2on.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully set all TX SEL Knobs to in position", False)
    time.sleep(2)
    
    
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  O/R and SONIC switches.\n"
        "• ON and ISO indicators should illuminate green\n",
        RESOURCES_DIR / "or_sonicon.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully pressed and released O/R and SONIC switches", False)
    screen.log_signal.emit("successfully checked that ON and ISO indicators illuminated", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E95",operator)   # YES
    write_excel("F95",result)     # PASS  
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Repeated Press RAD PTT switch.\n"
        "• ON and ISO indicators should Extinguish\n",
        RESOURCES_DIR / "radpttoniso.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E96",operator)   # YES
    write_excel("F96",result)     # PASS 
    write_excel("D96","'ON' and 'ISO' indicators should Extinguish") 
    
    # doubt must be clarified
    screen.log_signal.emit("successfully repeated press RAD PTT switch", False)
    
    screen.log_signal.emit("Switching S30 switch to ON (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 switch successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30 switch", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• ON and ISO indicators should not Illuminate\n",
        RESOURCES_DIR / "onisooff.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("successfully checked that ON and ISO indicators are not illuminating", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E97",operator)   # YES
    write_excel("F97",result)     # PASS 
    write_excel("D97","'ON' and 'ISO' indicators should not Illuminate") 
    screen.log_signal.emit("Switching S30 switch to OFF (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 switch successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30 switch", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  O/R and SONIC switches.\n"
        "• ON and ISO indicators should Illuminate\n",
        RESOURCES_DIR / "or_sonicon.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("successfully pressed and released O/R and SONIC switches", False)
    screen.log_signal.emit("successfully checked that ON and ISO indicators illuminated", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E98",operator)   # YES
    write_excel("F98",result)     # PASS  
    write_excel("D98","'ON' and 'ISO' indicators should Illuminate") 

    screen.log_signal.emit("===========TRANSIENT TEST COMPLETED============", False)
    time.sleep(0.5)

def alh2_mod345(screen):  
    set_ch1_ch2_scale_10v(screen)
    time.sleep(0.5)
    
    screen.log_signal.emit("==========COMMENCING TRANSIENT TEST==========", False)
    time.sleep(2)
    
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX  SEL Knobs to in position.\n",
        RESOURCES_DIR / "txselalh2on.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully set all TX SEL Knobs to in position", False)
    time.sleep(2)
    
    
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  O/R and SONIC switches.\n"
        "• ON and ISO indicators should illuminate green\n",
        RESOURCES_DIR / "or_sonicon.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("successfully pressed and released O/R and SONIC switches", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E95",operator)   # YES
    write_excel("F95",result)     # PASS  
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Repeated Press RAD PTT switch.\n"
        "• ON and ISO indicators should not Extinguish\n",
        RESOURCES_DIR / "radpttoniso.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E96",operator)   # YES
    write_excel("F96",result)     # PASS  
    
    # doubt must be clarified
    screen.log_signal.emit("successfully repeated press RAD PTT switch", False)
    
    screen.log_signal.emit("Switching S30 switch to ON (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 switch successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30 switch", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• ON and ISO indicators should not Extinguish\n",
        RESOURCES_DIR / "onisoon.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("successfully checked that ON and ISO indicators are not illuminating", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E97",operator)   # YES
    write_excel("F97",result)     # PASS  
    screen.log_signal.emit("Switching S30 switch to OFF (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 switch successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30 switch", True)
        

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  O/R and SONIC switches.\n"
        "• ON and ISO indicators should Extinguish\n",
        RESOURCES_DIR / "orsonicoff.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    screen.log_signal.emit("successfully pressed and released O/R and SONIC switches", False)
    screen.log_signal.emit("successfully checked that ON and ISO indicators extinguished", False)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E98",operator)   # YES
    write_excel("F98",result)     # PASS  
    
    screen.log_signal.emit("===========TRANSIENT TEST COMPLETED============", False)
    time.sleep(0.5)

def run(screen):
    model = screen.alhx_combo.currentText().strip()
    jmodel = screen.jbox_combo.currentText().strip()
    mod = screen.mod_combo.text().strip()  # e.g. "02", "03", "04", "05"

    if model == "N200 - ALH1":
        return

    elif model == "N200 - ALH2" and jmodel == "No Junction Box":
        if mod == "02":
            alh2_mod2(screen)
        elif mod in ("03", "04", "05"):
            alh2_mod345(screen)
        else:
            screen.log_signal.emit(f"ERROR: Unknown MOD selected for ALH2: {mod}", True)

    elif model == "N200 - ALH3" and jmodel == "No Junction Box":
        if mod == "02":
            alh3_mod2(screen)
        elif mod in ("03", "04", "05"):
            alh3_mod345(screen)
        else:
            screen.log_signal.emit(f"ERROR: Unknown MOD selected for ALH3: {mod}", True)

    else:
        screen.log_signal.emit(f"ERROR: Invalid model/junction box combination: {model} / {jmodel}", True)
        return