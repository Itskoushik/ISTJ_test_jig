import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController

def run_norm(screen):
    screen.log_signal.emit("Connecting the Audio analyser input to CVR Connector J23 .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j23_on():
        screen.log_signal.emit("CVR Connector J23 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect CVR Connector J23", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set the audio analyser gen output to 750 uVrms @1KHz 
    #the audio analyser should read 1.0+- Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @200 Hz 
    #the audio analyser should read >700 mVrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @3500 Hz 
    #the audio analyser should read >700 mVrms with <10% THD +N
    
    screen.log_signal.emit("Disconnecting the Audio analyser input to CVR Connector J23 .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j23_off():
        screen.log_signal.emit("CVR Connector J23 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect CVR Connector J23", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    
    screen.log_signal.emit("Connecting the Audio analyser input to CVR Connector J23 .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j23_on():
        screen.log_signal.emit("CVR Connector J23 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect CVR Connector J23", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set the audio analyser gen output to 750 uVrms @1KHz 
    #the audio analyser should read 1.0+- Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @200 Hz 
    #the audio analyser should read >700 mVrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @3500 Hz 
    #the audio analyser should read >700 mVrms with <10% THD +N
    
    screen.log_signal.emit("Disconnecting the Audio analyser input to CVR Connector J23 .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j23_off():
        screen.log_signal.emit("CVR Connector J23 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect CVR Connector J23", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)