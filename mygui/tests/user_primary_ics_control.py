import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from devices.apx_analyzer import generator_control,set_dbra_reference,monitor_dbra_until_ok
from core.excel_logger import write_excel,write_excel_dynamic
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
from core.tuning_workflow import set_popup_title

def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL ICS Volume Control Test (NORM)")
    screen.log_signal.emit("==========Commencing USER PRIMARY INTERCOM CHANNEL ICS Volume Control Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 kHz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    
    time.sleep(0.5)
    
    time.sleep(0.5)
    #on the audio analyser press INPUT A and AMPL.
    #Set audio analyser to read dBr ZERO
    set_dbra_reference(screen)
    
    #Audio analyser should read <-40dBr(>40dB of range)
    data=monitor_dbra_until_ok(screen)
    if data:
        write_excel_dynamic("F34", data["value"])         # raw dBrA
        write_excel("K34", data["result"])        # PASS / FAIL
    screen.log_signal.emit(
            f"ICS Volume Control: {data['value']:.2f} dBrA  {data['result']}",
            data["result"] == "FAIL"
        )
    
    screen.log_signal.emit("==========Successfully Completed USER PRIMARY INTERCOM CHANNEL ICS Volume Control Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL ICS Volume Control Test (STBY)")
    screen.log_signal.emit("==========Commencing USER PRIMARY INTERCOM CHANNEL ICS Volume Control Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 kHz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    time.sleep(0.5)
    
    time.sleep(0.5)
    #on the audio analyser press INPUT A and AMPL.
    #Set audio analyser to read dBr ZERO
    set_dbra_reference(screen)
    
    #Audio analyser should read <-40dBr(>40dB of range)
    data=monitor_dbra_until_ok(screen)
    if data:
        write_excel_dynamic("F35", data["value"])         # raw dBrA
        write_excel("K35", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit(
            f"ICS Volume Control: {data['value']:.2f} dBrA  {data['result']}",
            data["result"] == "FAIL"
        )
    screen.log_signal.emit("==========Successfully Completed USER PRIMARY INTERCOM CHANNEL ICS Volume Control Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)