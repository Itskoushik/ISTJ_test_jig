from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)




def run(screen):
    
    screen.log_signal.emit("==========COMMENCING PHONES AUDIO TEST==========", False)
    
    screen.log_signal.emit("Step 1: disconnecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j14_off():
        screen.log_signal.emit("J14 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J14", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 2: disconnecting PHONES Connector (J15)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_off():
        screen.log_signal.emit("J15 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J15", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    #disable audio analyser input.
    
    screen.log_signal.emit("Step 3: connecting Connector (J29)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j29_on():
        screen.log_signal.emit("J29 successfully connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect J29", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: connecting JACKS (J15) and (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_on():
        screen.log_signal.emit("J15 successfully connected", False)
        time.sleep(0.5)
        if STM32RelayController.set_j13_on():
            screen.log_signal.emit("J13 successfully connected", False)
            time.sleep(0.5)
        else:
            screen.log_signal.emit("ERROR: Failed to connect J13", True)
            return
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect J15 or J13", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
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
    
    #audio analyser tests
    
    screen.log_signal.emit("Step 5: disconnecting Connector (J15) and connecting Connector (J16)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_off():
        screen.log_signal.emit("J15 successfully disconnected", False)
        time.sleep(0.5)
        if STM32RelayController.set_j16_on():
            screen.log_signal.emit("J16 successfully connected", False)
            time.sleep(0.5)
        else:
            screen.log_signal.emit("ERROR: Failed to connect J16", True)
            return
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect J15 or J16", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 6: Turning Switch (S24) to OFF", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s24_off():
        screen.log_signal.emit("S24 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S24", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 7: Turning Switch (S25) to ON", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s25_on():
        screen.log_signal.emit("S25 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S25", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    #audio analyser tests
    
    screen.log_signal.emit("✓ PHONES AUDIO TEST COMPLETED", False)
    time.sleep(0.5)