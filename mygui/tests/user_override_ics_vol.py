import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication

def run_norm(screen):
    screen.log_signal.emit("==========Commencing ICS VOLUME Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1kHz
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release the O/R button.\n",
        RESOURCES_DIR /"or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #Audio analyser should read 5.5+-0.55 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @200 Hz
    #Audio analyser should read >3.9 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #Audio analyser should read >3.9 Vrms with <10% THD + N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release the O/R button.\n",
        RESOURCES_DIR /"or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("==========Successfully Completed ICS VOLUME Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing ICS VOLUME Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1kHz
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release the O/R button.\n",
        RESOURCES_DIR /"or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #Audio analyser should read 5.5+-0.55 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @200 Hz
    #Audio analyser should read >3.9 Vrms with <10% THD + N
    #set audio analyser gen output to 750 uVrms @3500 Hz
    #Audio analyser should read >3.9 Vrms with <10% THD + N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release the O/R button.\n",
        RESOURCES_DIR /"or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("==========Successfully Completed ICS VOLUME Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)