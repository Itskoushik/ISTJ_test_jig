import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController    

def run_norm(screen):
    screen.log_signal.emit("==========Commencing TX PTT Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to in position .\n",
        RESOURCES_DIR /"vuhf1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #Audio analyser should read <11 mVrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to OUT position .\n",
        RESOURCES_DIR /"vuhf1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
   
    
    screen.log_signal.emit("==========Successfully Completed TX PTT Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing TX PTT Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to in position .\n",
        RESOURCES_DIR /"vuhf1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #Audio analyser should read <11 mVrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to OUT position .\n",
        RESOURCES_DIR /"vuhf1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting TX Switch S30 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_off():
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
   
    
    screen.log_signal.emit("==========Successfully Completed TX PTT Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)