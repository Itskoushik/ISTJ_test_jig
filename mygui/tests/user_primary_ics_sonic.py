import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication

def run_norm(screen):
    screen.log_signal.emit("==========Commencing ICS SONIC MUTE Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS knob to Fully CCW .\n"
        "• Press and Release SONIC button .\n",
        RESOURCES_DIR / "ics_sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #Audio analyser should read <11 mVrms 
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC button .\n",
        RESOURCES_DIR / "sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #Audio analyser should read <9.9Vrms with <10% THD+N
   
    
    screen.log_signal.emit("==========Successfully Completed ICS SONIC MUTE Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing ICS SONIC MUTE Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS knob to Fully CCW .\n"
        "• Press and Release SONIC button .\n",
        RESOURCES_DIR / "ics_sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #Audio analyser should read <11 mVrms 
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC button .\n",
        RESOURCES_DIR / "sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #Audio analyser should read <9.9Vrms with <10% THD+N
   
    
    screen.log_signal.emit("==========Successfully Completed ICS SONIC MUTE Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)