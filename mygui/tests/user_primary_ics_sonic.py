import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from devices.apx_analyzer import read_apx_meter
from core.excel_logger import write_excel,write_excel_dynamic
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL ICS SONIC MUTE Test (NORM)")
    screen.log_signal.emit("==========Commencing USER PRIMARY INTERCOM CHANNEL ICS SONIC MUTE Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS knob to Fully CW .\n"
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR / "ics_sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Rotated ICS knob to Fully CW", False)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #Audio analyser should read <11 mVrms
    data=read_apx_meter(screen,max_v=11,unit="mVrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F39", data["observation"])         # raw vrms
        write_excel("K39", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR / "sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    #Audio analyser should read <9.9Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F41", data["observation"])         # raw vrms
        write_excel("K41", data["result"])
   
    
    screen.log_signal.emit("==========Successfully Completed USER PRIMARY INTERCOM CHANNEL ICS SONIC MUTE Test===========", False)

    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER PRIMARY INTERCOM CHANNEL ICS SONIC MUTE Test (STBY)")
    screen.log_signal.emit("==========Commencing USER PRIMARY INTERCOM CHANNEL ICS SONIC MUTE Test==========", False)
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ICS knob to Fully CW .\n"
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR / "ics_sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Rotated ICS knob to Fully CW", False)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    
    #Audio analyser should read <11 mVrms
    data=read_apx_meter(screen,max_v=11,unit="mVrms")
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F40", data["observation"])         # raw vrms
        write_excel("K40", data["result"])        # PASS / FAIL 
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR / "sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)

    #Audio analyser should read <9.9Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F42", data["observation"])         # raw vrms
        write_excel("K42", data["result"]) 
   
    
    screen.log_signal.emit("==========Successfully Completed USER PRIMARY INTERCOM CHANNEL ICS SONIC MUTE Test===========", False)
