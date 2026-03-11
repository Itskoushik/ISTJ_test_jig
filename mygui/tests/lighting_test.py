from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from core.excel_logger import write_excel

def alh1_norm(screen):
    
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    
    screen.log_signal.emit("Step 1: Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "vuhf.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 3: Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Step 4: Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s26_on():
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get dim\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n",
        RESOURCES_DIR / "backlit.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E99",operator)   # YES
    write_excel("F99",result)     # PASS 
    
    screen.log_signal.emit("Step 5: Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Step 6: Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    # screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "backlit_on.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E101",operator)   # YES
    write_excel("F101",result)     # PASS 
    screen.log_signal.emit("Step 7: ON, TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Step 8: Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    # screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "backlit_dim.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 9: ON, TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    
    screen.log_signal.emit("✓ LIGHTING TEST COMPLETED", False)
    
def alh3_norm(screen):
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    
    screen.log_signal.emit("Step 1: Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch.\n",
        RESOURCES_DIR / "or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)

    
    screen.log_signal.emit("Step 2: Pressed and released O/R switch", False)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "vuhf.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 3: Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Step 4: Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s26_on():
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get dim\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n",
        RESOURCES_DIR / "backlit.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E99",operator)   # YES
    write_excel("F99",result)     # PASS 
    
    screen.log_signal.emit("Step 5: Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Step 6: Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    # screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "backlit_on.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E101",operator)   # YES
    write_excel("F101",result)     # PASS 
    screen.log_signal.emit("Step 7: ON, TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Step 8: Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    # screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "backlit_dim.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 9: ON, TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    
    screen.log_signal.emit("✓ LIGHTING TEST COMPLETED", False)
    


def alh2_norm(screen):    
    
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    
    screen.log_signal.emit("Step 1: Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch.\n",
        RESOURCES_DIR / "or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)

    
    screen.log_signal.emit("Step 2: Pressed and released O/R switch", False)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "vuhf.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Step 3: Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Step 4: Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s26_on():
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get dim\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n",
        RESOURCES_DIR / "backlit.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E99",operator)   # YES
    write_excel("F99",result)     # PASS 
    
    screen.log_signal.emit("Step 5: Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Step 6: Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    # screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "backlit_on.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E101",operator)   # YES
    write_excel("F101",result)     # PASS 
    screen.log_signal.emit("Step 7: ON, TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Step 8: Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    # screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "backlit_dim.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 9: ON, TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    
    screen.log_signal.emit("✓ LIGHTING TEST COMPLETED", False)
    
def run_stby(screen):
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    
    screen.log_signal.emit("Step 1: Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s26_on():
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get dim\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n",
        RESOURCES_DIR / "backlit.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E99",operator)   # YES
    write_excel("F99",result)     # PASS 
    
    screen.log_signal.emit("Step 2: Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Step 3: Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    # screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "backlit_on.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E101",operator)   # YES
    write_excel("F101",result)     # PASS 
    screen.log_signal.emit("Step 4: ON, TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Step 5: Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    # screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "backlit_dim.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Step 6: ON, TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    
    screen.log_signal.emit("✓ LIGHTING TEST COMPLETED", False)
    


def run_stby(screen):
    model = screen.alhx_combo.currentText().strip()
    jmodel=screen.jbox_combo.currentText().strip()

    if model == "ALH1" and jmodel=="No Junction Box":
        run_stby(screen)

    elif model == "ALH2" and jmodel=="No Junction Box":
        run_stby(screen)

    elif model == "ALH3" and jmodel=="No Junction Box":
        run_stby(screen)

    else:
        screen.log_signal.emit(f"ERROR: Invalid ALHx model selected: {model}", True)
        return
    
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
