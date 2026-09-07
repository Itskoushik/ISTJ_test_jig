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
    screen.worker_ch2_28v()
    screen.log_signal.emit("Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "light0.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s26_on):
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• TX and V/UHF1 TX SEL indicators should get brightly illuminated.\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n"
        "• ISTJ CONTROLLER DS14 Indicator should be illuminated.\n",
        RESOURCES_DIR / "light2.png","yes_no",None
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
    
    screen.log_signal.emit("Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "light3.png","yes_no",None
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
    screen.log_signal.emit("TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "light1.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E103",operator)   # YES
    write_excel("F103",result)     # PASS 
    screen.log_signal.emit("TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    screen.channel_2_off()
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• Set all TX SEL knobs to OUT position\n",
        RESOURCES_DIR / "txselalh1.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Successfully set all TX SEL Knobs to OUT position", False)
    screen.log_signal.emit("===========LIGHTING TEST COMPLETED============", False)
    
def alh3_norm(screen):
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    screen.worker_ch2_28v()
    screen.log_signal.emit("Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release CALL switch.\n",
        RESOURCES_DIR / "call.jpg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)

    
    screen.log_signal.emit("Pressed and released CALL switch", False)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "light0alh3.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s26_on):
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n"
        "• ISTJ CONTROLLER DS14 Indicator should be illuminated.\n",
        RESOURCES_DIR / "light2alh3.png","yes_no",None
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
    
    screen.log_signal.emit("Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "light1alh3.png","yes_no",None
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
    screen.log_signal.emit("ON, TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "light3alh3.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E103",operator)   # YES
    write_excel("F103",result)     # PASS 
    screen.log_signal.emit("ON, TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    screen.channel_2_off()
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• Set all TX SEL knobs to OUT position\n"
        "• Press and release CALL switch.\n",
        RESOURCES_DIR / "alh3last.jpg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Successfully set all TX SEL Knobs to OUT position and pressed CALL switch", False)
    screen.log_signal.emit("===========LIGHTING TEST COMPLETED============", False)
    


def alh2_norm(screen):    
    
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    screen.worker_ch2_28v()
    screen.log_signal.emit("Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch.\n",
        RESOURCES_DIR / "or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)

    
    screen.log_signal.emit("Pressed and released O/R switch", False)
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "light0alh2.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s26_on):
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get dim\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n"
        "• ISTJ CONTROLLER DS14 Indicator should be illuminated.\n",
        RESOURCES_DIR / "light2alh2.png","yes_no",None
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
    
    screen.log_signal.emit("Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "light1alh2.png","yes_no",None
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
    screen.log_signal.emit("ON, TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "light3alh2.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E103",operator)   # YES
    write_excel("F103",result)     # PASS 
    screen.log_signal.emit("ON, TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    screen.channel_2_off()
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• Set all TX SEL knobs to OUT position\n"
        "• Press and release O/R switch.\n",
        RESOURCES_DIR / "alh2last.jpg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Successfully set all TX SEL Knobs to OUT position and pressed O/R switch", False)
    screen.log_signal.emit("===========LIGHTING TEST COMPLETED============", False)

def run_stby_1(screen):
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    screen.worker_ch2_28v()
    screen.log_signal.emit("Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "light0.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s26_on):
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n"
        "• ISTJ CONTROLLER DS14 Indicator should be illuminated.\n",
        RESOURCES_DIR / "light2.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E100",operator)   # YES
    write_excel("F100",result)     # PASS 
    
    screen.log_signal.emit("Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "light1.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E102",operator)   # YES
    write_excel("F102",result)     # PASS 
    screen.log_signal.emit("TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "light3.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E104",operator)   # YES
    write_excel("F104",result)     # PASS 
    screen.log_signal.emit("TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    screen.channel_2_off()
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• Set all TX SEL knobs to OUT position\n",
        RESOURCES_DIR / "txselalh1.jpeg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Successfully set all TX SEL Knobs to OUT position", False)
    screen.log_signal.emit("===========LIGHTING TEST COMPLETED============", False)

def run_stby_2(screen):
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    screen.worker_ch2_28v()
    screen.log_signal.emit("Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch.\n",
        RESOURCES_DIR / "or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)

    
    screen.log_signal.emit("Pressed and released O/R switch", False)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "light0alh2.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s26_on):
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get dim\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n"
        "• ISTJ CONTROLLER DS14 Indicator should be illuminated.\n",
        RESOURCES_DIR / "light2alh2.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E100",operator)   # YES
    write_excel("F100",result)     # PASS 
    
    screen.log_signal.emit("Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "light1alh2.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E102",operator)   # YES
    write_excel("F102",result)     # PASS 
    screen.log_signal.emit("ON, TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "light3alh2.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E104",operator)   # YES
    write_excel("F104",result)     # PASS 
    screen.log_signal.emit("ON, TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    screen.channel_2_off()
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• Set all TX SEL knobs to OUT position\n"
        "• Press and release O/R switch.\n",
        RESOURCES_DIR / "alh2last.jpg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Successfully set all TX SEL Knobs to OUT position and pressed O/R switch", False)
    screen.log_signal.emit("===========LIGHTING TEST COMPLETED============", False)

def run_stby_3(screen):
    
    screen.log_signal.emit("==========COMMENCING LIGHTING TEST==========", False)
    time.sleep(2)
    screen.worker_ch2_28v()
    screen.log_signal.emit("Setting TX Switch to UP position (S30)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("TX switch (S30) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON TX switch (S30)", True)
    

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release CALL switch.\n",
        RESOURCES_DIR / "call.jpg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    
    screen.log_signal.emit("Pressed and released CALL switch", False)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set all TX SEL knobs except V/UHF1 to OUT position\n",
        RESOURCES_DIR / "light0alh3.png","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    screen.log_signal.emit("Successfully set TX SEL knobs except V/UHF1 to OUT position", False)
    screen.log_signal.emit("Setting LIGHTS Switch to UP position (S26)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s26_on):
        screen.log_signal.emit("LIGHTS switch (S26) successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON LIGHTS switch (S26)", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get Illuminated brightly.\n"
        "• Faceplate legends, knobs, and pushbuttons should be backlit.\n"
        "• ISTJ CONTROLLER DS14 Indicator should be illuminated.\n",
        RESOURCES_DIR / "light2alh3.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E100",operator)   # YES
    write_excel("F100",result)     # PASS 
    
    screen.log_signal.emit("Verified backlighting of faceplate legends, knobs, and pushbuttons", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 5 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_5v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated brightly.\n",
        RESOURCES_DIR / "light1alh3.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E102",operator)   # YES
    write_excel("F102",result)     # PASS 
    screen.log_signal.emit("ON, TX and V/UHF1 TX SEL indicators illuminated brightly", False)
    screen.log_signal.emit("Decreasing right power supply voltage to 12 Vdc ", False)
    # ▶ CHANNEL 2 SEQUENCE – STEP 2
    screen.worker_ch2_12v()
    time.sleep(1)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• ON, TX and V/UHF1 TX SEL indicators should get illuminated dimly.\n",
        RESOURCES_DIR / "light3alh3.png","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E104",operator)   # YES
    write_excel("F104",result)     # PASS 
    screen.log_signal.emit("ON, TX and V/UHF1 TX SEL indicators illuminated dimly", False)
    time.sleep(2)
    screen.channel_2_off()
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Verification Required",
        "• Set all TX SEL knobs to OUT position\n"
        "• Press and release CALL switch.\n",
        RESOURCES_DIR / "alh3last.jpg","yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Successfully set all TX SEL Knobs to OUT position and pressed CALL switch", False)
    screen.log_signal.emit("===========LIGHTING TEST COMPLETED============", False)


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
