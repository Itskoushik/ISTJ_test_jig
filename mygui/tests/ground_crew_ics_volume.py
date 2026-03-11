import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController

def run_norm(screen):
    screen.log_signal.emit("==========Commencing ICS VOLUME test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connecting the Audio analyser Gen output to the MIC Connector J24", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j24_on():
        screen.log_signal.emit("MIC OUT Connector J24 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT Connector J24", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set the audio analyser gen output to 750 uVrms @1 KHz
    
    screen.log_signal.emit("Connecting the Audio analyser input to the GND CREW PH connector J26", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j26_on():
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect GND CREW PH Connector J26", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <35 mVrms 
    
    screen.log_signal.emit("Setting the GND CREW ICS switch S29 to the up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s29_on():
        screen.log_signal.emit("GND CREW ICS switch S29 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set GND CREW ICS switch S29 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read 11.0+-1.1 Vrms with <10% THD+N 
    
    screen.log_signal.emit("Setting the GND CREW LOAD switch S28 to the up 600 ohm", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s28_600ohms():
        screen.log_signal.emit("GND CREW LOAD switch S28 successfully set to 600ohms position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set GND CREW LOAD switch S28 to 600ohms position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set the audio analyser gen output to 750 uVrms @1 KHz
    #the audio analyser should read >9.9 Vrms <10% THD+N 
    #set the audio analyser gen output to 750 uVrms @200 Hz
    #the audio analyser should read >7.7 Vrms <10% THD+N 
    #set the audio analyser gen output to 750 uVrms @3500 Hz
    #the audio analyser should read >7.7 Vrms <10% THD+N 
    
    screen.log_signal.emit("==========Successfully completed ICS VOLUME test===========", False)
    

    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing ICS VOLUME test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connecting the Audio analyser Gen output to the MIC Connector J24", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j24_on():
        screen.log_signal.emit("MIC OUT Connector J24 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT Connector J24", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set the audio analyser gen output to 750 uVrms @1 KHz
    
    screen.log_signal.emit("Connecting the Audio analyser input to the GND CREW PH connector J26", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j26_on():
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect GND CREW PH Connector J26", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <35 mVrms 
    
    screen.log_signal.emit("Setting the GND CREW ICS switch S29 to the up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s29_on():
        screen.log_signal.emit("GND CREW ICS switch S29 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set GND CREW ICS switch S29 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read 11.0+-1.1 Vrms with <10% THD+N 
    
    screen.log_signal.emit("Setting the GND CREW LOAD switch S28 to the up 600 ohm", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s28_600ohms():
        screen.log_signal.emit("GND CREW LOAD switch S28 successfully set to 600ohms position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set GND CREW LOAD switch S28 to 600ohms position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #set the audio analyser gen output to 750 uVrms @1 KHz
    #the audio analyser should read >9.9 Vrms <10% THD+N 
    #set the audio analyser gen output to 750 uVrms @200 Hz
    #the audio analyser should read >7.7 Vrms <10% THD+N 
    #set the audio analyser gen output to 750 uVrms @3500 Hz
    #the audio analyser should read >7.7 Vrms <10% THD+N 
    
    screen.log_signal.emit("==========Successfully completed ICS VOLUME test===========", False)