import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController

def run_norm(screen):
    
    screen.log_signal.emit("Setting PRIVATE Switch S33 to the Up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_on():
        screen.log_signal.emit("PRIVATE Switch S33 successfully set to Up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE Switch S33 to Up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set the audio analyser gen output to 750 uVrms @1KHz 
    #the audio analyser should read >9.9 Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @200 Hz 
    #the audio analyser should read >7.7 Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @3500 Hz 
    #the audio analyser should read >7.7 Vrms with <10% THD +N
    
    screen.log_signal.emit("Setting PRIVATE Switch S33 to the Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("PRIVATE Switch S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE Switch S33 to Down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    
    screen.log_signal.emit("Setting PRIVATE Switch S33 to the Up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_on():
        screen.log_signal.emit("PRIVATE Switch S33 successfully set to Up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE Switch S33 to Up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set the audio analyser gen output to 750 uVrms @1KHz 
    #the audio analyser should read >9.9 Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @200 Hz 
    #the audio analyser should read >7.7 Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @3500 Hz 
    #the audio analyser should read >7.7 Vrms with <10% THD +N
    
    screen.log_signal.emit("Setting PRIVATE Switch S33 to the Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s33_off():
        screen.log_signal.emit("PRIVATE Switch S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE Switch S33 to Down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)