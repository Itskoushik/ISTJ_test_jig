import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel,write_excel_dynamic
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL ICS Volume Test (NORM)")
    screen.log_signal.emit("==========Commencing USER PRIMARY INTERCOM CHANNEL ICS Volume Test===========", False)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL ICS Volume Test")
    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="750.0 uVrms", frequency=1000,state="on")
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F25", data["observation"])         # raw vrms
        write_excel("K25", data["result"])        # PASS / FAIL
        
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F27", data["observation"])         # raw vrms
        write_excel("K27", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F29", data["observation"])         # raw vrms
        write_excel("K29", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("==========Successfully Completed USER PRIMARY INTERCOM CHANNEL ICS Volume Test===========", False)


    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL ICS Volume Test (STBY)")
    screen.log_signal.emit("==========Commencing USER PRIMARY INTERCOM CHANNEL ICS Volume Test===========", False)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL ICS Volume Test")
    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="750.0 uVrms", frequency=1000,state="on")
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F26", data["observation"])         # raw vrms
        write_excel("K26", data["result"])        # PASS / FAIL
        
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F28", data["observation"])         # raw vrms
        write_excel("K28", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F30", data["observation"])         # raw vrms
        write_excel("K30", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("==========Successfully Completed USER PRIMARY INTERCOM CHANNEL ICS Volume Test===========", False)
    