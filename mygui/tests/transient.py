from core.paths import RESOURCES_DIR
import time
from core.excel_logger import write_excel
from core.stm32_commands import STM32RelayController
from PyQt5.QtWidgets import QApplication

def alh1(screen):
    screen.log_signal.emit("==========COMMENCING TRANSIENT TEST==========", False)
    time.sleep(2)
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX  SEL Knobs to in position.\n",
        RESOURCES_DIR / "txsel.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 1: successfully set all TX SEL Knobs to in position", False)
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Repeated Press RAD PTT switch.\n"
        "• ON and ISO indicators should not Extinguish\n",
        RESOURCES_DIR / "rad_ptt.jpeg","yes_no",None
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
    screen.log_signal.emit("Step 2: successfully repeated press RAD PTT switch", False)
    # doubt must be clarified
    screen.log_signal.emit("Step 3: Switching S30 switch to ON (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 switch successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30 switch", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• ON and ISO indicators should not Extinguish\n",
        None,"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E97",operator)   # YES
    write_excel("F97",result)     # PASS  
    screen.log_signal.emit("Step 4: Switching S30 switch to OFF (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 switch successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30 switch", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    screen.log_signal.emit("✓ TRANSIENT TEST COMPLETED", False)
    time.sleep(0.5)
    
def alh3(screen):
    screen.log_signal.emit("==========COMMENCING TRANSIENT TEST==========", False)
    time.sleep(2)
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX  SEL Knobs to in position.\n",
        RESOURCES_DIR / "txsel.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 1: successfully set all TX SEL Knobs to in position", False)
    time.sleep(2)
    
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  O/R switch.\n"
        "• ON and ISO indicators should illuminate green\n",
        RESOURCES_DIR / "or_switch.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 2: successfully pressed and released O/R switch", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E95",operator)   # YES
    write_excel("F95",result)     # PASS  
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Repeated Press RAD PTT switch.\n"
        "• ON and ISO indicators should not Extinguish\n",
        RESOURCES_DIR / "rad_ptt.jpeg","yes_no",None
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
    screen.log_signal.emit("Step 3: successfully repeated press RAD PTT switch", False)
    
    screen.log_signal.emit("Step 4: Switching S30 switch to ON (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 switch successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30 switch", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• ON and ISO indicators should not Extinguish\n",
        None,"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E97",operator)   # YES
    write_excel("F97",result)     # PASS  
    screen.log_signal.emit("Step 5: Switching S30 switch to OFF (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 switch successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30 switch", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  O/R switch.\n"
        "• ON and ISO indicators should not Extinguish\n",
        RESOURCES_DIR / "or_switch.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E98",operator)   # YES
    write_excel("F98",result)     # PASS  
    
    screen.log_signal.emit("✓ TRANSIENT TEST COMPLETED", False)
    time.sleep(0.5)

       
def alh2(screen):  
    
    screen.log_signal.emit("==========COMMENCING TRANSIENT TEST==========", False)
    time.sleep(2)
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX  SEL Knobs to in position.\n",
        RESOURCES_DIR / "txsel.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 1: successfully set all TX SEL Knobs to in position", False)
    time.sleep(2)
    
    
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  O/R and SONIC switches.\n"
        "• ON and ISO indicators should illuminate green\n",
        RESOURCES_DIR / "or_sonic.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 2: successfully pressed and released O/R and SONIC switches", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E95",operator)   # YES
    write_excel("F95",result)     # PASS  
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Repeated Press RAD PTT switch.\n"
        "• ON and ISO indicators should not Extinguish\n",
        RESOURCES_DIR / "rad_ptt.jpeg","yes_no",None
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
    screen.log_signal.emit("Step 3: successfully repeated press RAD PTT switch", False)
    
    screen.log_signal.emit("Step 4: Switching S30 switch to ON (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 switch successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S30 switch", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• ON and ISO indicators should not Extinguish\n",
        None,"yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E97",operator)   # YES
    write_excel("F97",result)     # PASS  
    screen.log_signal.emit("Step 5: Switching S30 switch to OFF (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 switch successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S30 switch", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release  O/R and SONIC switches.\n"
        "• ON and ISO indicators should not Extinguish\n",
        RESOURCES_DIR / "or_sonic.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E98",operator)   # YES
    write_excel("F98",result)     # PASS  
    
    screen.log_signal.emit("✓ TRANSIENT TEST COMPLETED", False)
    time.sleep(0.5)
    

def run(screen):
    model = screen.alhx_combo.currentText().strip()
    jmodel=screen.jbox_combo.currentText().strip()
    
    if model == "ALH1" and jmodel=="No Junction Box":
        alh1(screen)

    elif model == "ALH2" and jmodel=="No Junction Box":
        alh2(screen)

    elif model == "ALH3" and jmodel=="No Junction Box":
        alh3(screen)

    else:
        screen.log_signal.emit(f"ERROR: Invalid ALHx model selected: {model}", True)
        return
