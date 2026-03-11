import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication

def run_norm(screen):
    screen.log_signal.emit("==========Commencing ICS Volume Control test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 kHz
    #on the audio analyser press INPUT A and AMPL.
    #Set audio analyser to read dBr ZERO
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS knob to Fully CCW while monitoring the oscilloscope.\n"
        "• There should be no noise or disruptions observed .\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #Audio analyser should read <-40dBr(>40dB of range)
   
    
    screen.log_signal.emit("==========Successfully Completed ICS Volume Control test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing ICS Volume Control test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 kHz
    #on the audio analyser press INPUT A and AMPL.
    #Set audio analyser to read dBr ZERO
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS knob to Fully CCW while monitoring the oscilloscope.\n"
        "• There should be no noise or disruptions observed .\n",
        RESOURCES_DIR / "ics_fully_ccw.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #Audio analyser should read <-40dBr(>40dB of range)
    
    screen.log_signal.emit("==========Successfully Completed ICS Volume Control test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)