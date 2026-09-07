from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("MIC LIMITER TEST")
    screen.log_signal.emit("==========COMMENCING MIC LIMITER TEST==========", False)
    
    generator_control(screen, level="1 mVrms", frequency=1000)
    data = read_apx_meter(screen,min_v="10.8", max_v="12.2")
    if data:
        # write_excel("E26", data["observation"])   # measured observation
        write_excel("E32", data["observation"])         # raw vrms
        write_excel("F32", data["result"])        # PASS / FAIL
    
    
    screen.log_signal.emit("disconnecting STBY PHONES Connector (J16)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j16_off):
        screen.log_signal.emit("STBY PHONES Connector J16 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect STBY PHONES Connector J16", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    
    screen.log_signal.emit("Connecting NORMS PHONES Connector (J15)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j15_on):
        screen.log_signal.emit("NORMS PHONES Connector J15 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect NORMS PHONES Connector J15", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Turning STBY PWR Switch (S25) to OFF", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s25_off):
        screen.log_signal.emit("STBY PWR Switch S25 successfully set to Down position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set STBY PWR Switch S25 to Down position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Turning NORMS PWR Switch (S24) to ON", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s24_on):
        screen.log_signal.emit("NORMS PWR Switch S24 successfully set to Up position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to set NORMS PWR Switch S24 to Up position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    generator_control(screen, level="1 mVrms", frequency=1000)
    data = read_apx_meter(screen,min_v="10.8", max_v="12.2")
    if data:
        # write_excel("E26", data["observation"])   # measured observation
        write_excel("E31", data["observation"])         # raw vrms
        write_excel("F31", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("============ MIC LIMITER TEST COMPLETED =============", False)