import time
from core.paths import RESOURCES_DIR
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel,write_excel_dynamic
from core.stm32_commands import STM32RelayController
from PyQt5.QtWidgets import QApplication
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER OVERRIDE INTERCOM CHANNEL CVR Output level test (NORM)")
    screen.log_signal.emit("==========Commencing USER OVERRIDE INTERCOM CHANNEL CVR Output level test===========", False)
    time.sleep(0.5) 
    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("J29 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J29", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    #set audio analyser gen output to 750 uVrms @1kHz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    #Audio analyser should read 1.0+-0.1 V with <10% THD + N
    data=read_apx_meter(screen,min_v=0.9,max_v=1.1,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F75", data["observation"])         # raw vrms
        write_excel("K75", data["result"])        # PASS / FAIL
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)

    #Audio analyser should read >700 mVrms with <10% THD + N
    data=read_apx_meter(screen,min_v=700,max_thd=10.0,unit="mVrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F77", data["observation"])         # raw vrms
        write_excel("K77", data["result"])        # PASS / FAIL

    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >700 mVrms with <10% THD + N
    data=read_apx_meter(screen,min_v=700,max_thd=10.0,unit="mVrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F79", data["observation"])         # raw vrms
        write_excel("K79", data["result"])  
    
    
    screen.log_signal.emit("==========Successfully Completed USER OVERRIDE INTERCOM CHANNEL CVR Output level test===========", False)
    time.sleep(0.5) 

    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER OVERRIDE INTERCOM CHANNEL CVR Output level test (STBY)")
    screen.log_signal.emit("==========Commencing USER OVERRIDE INTERCOM CHANNEL CVR Output level test===========", False)
    time.sleep(0.5) 
    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("J29 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J29", True)

    QApplication.processEvents()
    time.sleep(1)
    #set audio analyser gen output to 750 uVrms @1kHz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    #Audio analyser should read 1.0+-0.1 V with <10% THD + N
    data=read_apx_meter(screen,min_v=0.9,max_v=1.1,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F76", data["observation"])         # raw vrms
        write_excel("K76", data["result"])        # PASS / FAIL
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)

    #Audio analyser should read >700 mVrms with <10% THD + N
    data=read_apx_meter(screen,min_v=700,max_thd=10.0,unit="mVrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F78", data["observation"])         # raw vrms
        write_excel("K78", data["result"])        # PASS / FAIL

    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >700 mVrms with <10% THD + N
    data=read_apx_meter(screen,min_v=700,max_thd=10.0,unit="mVrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F80", data["observation"])         # raw vrms
        write_excel("K80", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("==========Successfully Completed USER OVERRIDE INTERCOM CHANNEL CVR Output level test===========", False)
    time.sleep(0.5) 