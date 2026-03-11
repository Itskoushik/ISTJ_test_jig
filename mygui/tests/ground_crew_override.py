import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController

def run_norm(screen):
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch .\n",
        RESOURCES_DIR / "or_switch.jpeg",
        "ok",None
    )


    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    
    #set the audio analyser gen output to 750 uVrms @1KHz 
    #the audio analyser should read >9.9 Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @200 Hz 
    #the audio analyser should read >7.7 Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @3500 Hz 
    #the audio analyser should read >7.7 Vrms with <10% THD +N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch .\n",
        RESOURCES_DIR / "or_switch.jpeg",
        "ok",None
    )


    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    
def run_stby(screen):
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch .\n",
        RESOURCES_DIR / "or_switch.jpeg",
        "ok",None
    )


    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    
    #set the audio analyser gen output to 750 uVrms @1KHz 
    #the audio analyser should read >9.9 Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @200 Hz 
    #the audio analyser should read >7.7 Vrms with <10% THD +N
    #set the audio analyser gen output to 750 uVrms @3500 Hz 
    #the audio analyser should read >7.7 Vrms with <10% THD +N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch .\n",
        RESOURCES_DIR / "or_switch.jpeg",
        "ok",None
    )


    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)