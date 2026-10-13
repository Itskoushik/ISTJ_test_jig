import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel,write_excel_dynamic
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER OVERRIDE INTERCOM CHANNEL ICS VOLUME test (NORM)")
    screen.log_signal.emit("==========Commencing USER OVERRIDE INTERCOM CHANNEL ICS VOLUME Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1kHz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release the O/R button to IN position.\n",
        RESOURCES_DIR /"or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released O/R switch to IN position", False)
    #Audio analyser should read 5.5+-0.55 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=4.95,max_v=6.05,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F64", data["observation"])         # raw vrms
        write_excel("K64", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >3.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=3.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F66", data["observation"])         # raw vrms
        write_excel("K66", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >3.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=3.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F68", data["observation"])         # raw vrms
        write_excel("K68", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release the O/R button to OUT position.\n",
        RESOURCES_DIR /"or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released O/R switch to OUT position", False)
    screen.log_signal.emit("==========Successfully Completed USER OVERRIDE INTERCOM CHANNEL ICS VOLUME Test===========", False)

    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER OVERRIDE INTERCOM CHANNEL ICS VOLUME test (STBY)")
    screen.log_signal.emit("==========Commencing USER OVERRIDE INTERCOM CHANNEL ICS VOLUME Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1kHz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release the O/R button to IN position.\n",
        RESOURCES_DIR /"or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released O/R switch to IN position", False)
    #Audio analyser should read 5.5+-0.55 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=4.95,max_v=6.05,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F65", data["observation"])         # raw vrms
        write_excel("K65", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >3.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=3.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F67", data["observation"])         # raw vrms
        write_excel("K67", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >3.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=3.9,max_thd=10.0)
    if data:
        # write_excel("E13", data["observation"])   # measured observation
        write_excel_dynamic("F69", data["observation"])         # raw vrms
        write_excel("K69", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort() 
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release the O/R button to OUT position.\n",
        RESOURCES_DIR /"or_switch.jpeg","ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released O/R switch to OUT position", False)
    screen.log_signal.emit("==========Successfully Completed USER OVERRIDE INTERCOM CHANNEL ICS VOLUME Test===========", False)
