import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel,write_excel_dynamic
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIVATE INTERCOM CHANNEL ICS Volume Test (NORM)")
    screen.log_signal.emit("==========Commencing USER PRIVATE INTERCOM CHANNEL ICS Volume Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Setting the PRIVATE switch S33 to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_on):
        screen.log_signal.emit("S33 successfully set to UP position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to UP position", True)


    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000,state="on")
        #Audio analyser should read >9.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F53", data["observation"])         # raw vrms
        write_excel("K53", data["result"])        # PASS / FAIL
        
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F55", data["observation"])         # raw vrms
        write_excel("K55", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F57", data["observation"])         # raw vrms
        write_excel("K57", data["result"])        # PASS / FAIL
    
    
    
    
    screen.log_signal.emit("==========Successfully Completed USER PRIVATE INTERCOM CHANNEL ICS Volume Test===========", False)
    time.sleep(0.5)
    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIVATE INTERCOM CHANNEL ICS Volume Test (STBY)")
    screen.log_signal.emit("==========Commencing USER PRIVATE INTERCOM CHANNEL ICS Volume Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Setting the PRIVATE switch S33 to UP position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_on):
        screen.log_signal.emit("S33 successfully set to UP position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to UP position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000,state="on")
        #Audio analyser should read >9.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F54", data["observation"])         # raw vrms
        write_excel("K54", data["result"])        # PASS / FAIL
        
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F56", data["observation"])         # raw vrms
        write_excel("K56", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F58", data["observation"])         # raw vrms
        write_excel("K58", data["result"])        # PASS / FAIL
    
        
    screen.log_signal.emit("==========Successfully Completed USER PRIVATE INTERCOM CHANNEL ICS Volume Test===========", False)
    QApplication.processEvents()    
    time.sleep(0.5) 