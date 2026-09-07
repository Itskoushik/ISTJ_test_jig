import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController  
from devices.apx_analyzer import read_apx_meter
from core.excel_logger import write_excel,write_excel_dynamic  
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL TX PTT Test (NORM)")
    screen.log_signal.emit("==========Commencing USER PRIMARY INTERCOM CHANNEL TX PTT Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to IN position .\n",
        RESOURCES_DIR /"vhf1alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Successfully Set V/UHF 1 to IN position", False)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
        time.sleep(0.5)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.6)
    
    #Audio analyser should read <11 mVrms with <10% THD+N
    data=read_apx_meter(screen,max_v=11,unit="mVrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F46", data["observation"])         # raw vrms
        write_excel("K46", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to OUT position .\n",
        RESOURCES_DIR /"vhf1alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Successfully Set V/UHF 1 to OUT position", False)
    screen.log_signal.emit("Setting TX Switch S30 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
   
    
    screen.log_signal.emit("==========Successfully Completed USER PRIMARY INTERCOM CHANNEL TX PTT Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL TX PTT Test (STBY)")
    screen.log_signal.emit("==========Commencing USER PRIMARY INTERCOM CHANNEL TX PTT Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to IN position .\n",
        RESOURCES_DIR /"vhf1alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Successfully Set V/UHF 1 to IN position", False)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)

    QApplication.processEvents()
    time.sleep(0.5)
    
    #Audio analyser should read <11 mVrms with <10% THD+N
    data=read_apx_meter(screen,max_v=11,unit="mVrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F47", data["observation"])         # raw vrms
        write_excel("K47", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to OUT position .\n",
        RESOURCES_DIR /"vhf1alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Successfully Set V/UHF 1 to OUT position", False)
    screen.log_signal.emit("Setting TX Switch S30 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)

    QApplication.processEvents()
    time.sleep(0.5)
   
    
    screen.log_signal.emit("==========Successfully Completed USER PRIMARY INTERCOM CHANNEL TX PTT Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)