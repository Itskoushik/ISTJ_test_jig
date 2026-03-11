from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)



def run(screen):
    
    screen.log_signal.emit("==========COMMENCING MIC LIMITER TEST==========", False)
    
    
    screen.log_signal.emit("Step 1: disconnecting Connector (J16)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j16_off():
        screen.log_signal.emit("J16 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF J16", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 2: Connecting Connector (J15)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_on():
        screen.log_signal.emit("J15 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J15", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 3: Turning Switch (S25) to OFF", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s25_off():
        screen.log_signal.emit("S25 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S25", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: Turning Switch (S24) to ON", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s24_on():
        screen.log_signal.emit("S24 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S24", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("✓ MIC LIMITER TEST COMPLETED", False)