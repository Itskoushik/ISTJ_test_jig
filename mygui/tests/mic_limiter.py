from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel


def run(screen):
    
    screen.log_signal.emit("==========COMMENCING MIC LIMITER TEST==========", False)
    
    generator_control(screen, level="1 mVrms", frequency=1000)
    data = read_apx_meter(screen,min_v="10.8", max_v="12.2")
    if data:
        # write_excel("E26", data["observation"])   # measured value
        write_excel("E32", data["value"])         # raw vrms
        write_excel("F32", data["result"])        # PASS / FAIL
    
    
    screen.log_signal.emit("Step 1: disconnecting STBY PHONES Connector (J16)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j16_off():
        screen.log_signal.emit("STBY PHONES Connector J16 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF STBY PHONES Connector J16", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Step 2: Connecting NORMS PHONES Connector (J15)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_on():
        screen.log_signal.emit("NORMS PHONES Connector J15 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON J15", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 3: Turning STBY PWR Switch (S25) to OFF", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s25_off():
        screen.log_signal.emit("STBY PWR Switch S25 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF STBY PWR Switch S25", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: Turning NORMS PWR Switch (S24) to ON", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s24_on():
        screen.log_signal.emit("NORMS PWR Switch S24 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON NORMS PWR Switch S24", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    generator_control(screen, level="1 mVrms", frequency=1000)
    data = read_apx_meter(screen,min_v="10.8", max_v="12.2")
    if data:
        # write_excel("E26", data["observation"])   # measured value
        write_excel("E31", data["value"])         # raw vrms
        write_excel("F31", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("✓ MIC LIMITER TEST COMPLETED", False)