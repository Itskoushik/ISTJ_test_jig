import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController

def run_norm(screen):
    screen.log_signal.emit("==========Commencing ICS Volume test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Setting the PRIVATE switch S33 to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_on():
        screen.log_signal.emit("S33 successfully set to UP position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to UP position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @1 KHz
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @200 Hz
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    
    screen.log_signal.emit("Setting the PRIVATE switch S33 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to Down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("==========Successfully Completed ICS Volume test===========", False)
    time.sleep(0.5)
    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing ICS Volume test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Setting the PRIVATE switch S33 to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_on():
        screen.log_signal.emit("S33 successfully set to UP position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to UP position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @1 KHz
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @200 Hz
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    
        
    screen.log_signal.emit("==========Successfully Completed ICS Volume test===========", False)
    QApplication.processEvents()    
    time.sleep(0.5) 