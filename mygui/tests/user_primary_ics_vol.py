import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication

def run_norm(screen):
    screen.log_signal.emit("========== ICS Volume test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @200 Hz
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    
    screen.log_signal.emit("==========Successfully Completed ICS Volume test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    screen.log_signal.emit("========== ICS Volume test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @200 Hz
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    
    screen.log_signal.emit("==========Successfully Completed ICS Volume test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)