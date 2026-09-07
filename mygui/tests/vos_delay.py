from core.paths import RESOURCES_DIR
import time
from core.stm32_commands import STM32RelayController
from PyQt5.QtWidgets import (
    QApplication
)
from core.excel_logger import write_excel
from devices.apx_analyzer import generator_control,read_apx_meter,audible_tone_check,audible_monitor_check
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("VOS Delay Test (STBY)")
    screen.log_signal.emit("==========COMMENCING VOS DELAY TEST==========", False)
    set_popup_title("VOS Delay Test (STBY)")
    if STM32RelayController.send_with_retry(STM32RelayController.set_j13_on):
            screen.log_signal.emit("MIC Connector J13 successfully Connected", False)
            time.sleep(0.5)
            
    else:
        screen.log_signal.emit("ERROR: Failed to connect MIC Connector J13", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
        
    screen.log_signal.emit("Disconnecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j14_off):
        screen.log_signal.emit("HOT MIC Connector J14 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect HOT MIC Connector J14", True)
            

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
            
    #audio analyser output set to 750uvrms at 1khz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    time.sleep(2)
    # 🛑 PAUSE POINT
    screen.log_signal.emit("Disconnecting NORM PHONES Connector (J15)  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j15_off):
        screen.log_signal.emit("NORM PHONES Connector J15 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NORM PHONES Connector J15.", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Connecting STBY PHONES Connector (J16)  ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j16_on):
        screen.log_signal.emit("STBY PHONES Connector J16 successfully Connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Connect STBY PHONES Connector J16.", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    time.sleep(2)
    audible_tone_check(screen)
    time.sleep(1)
    audible_monitor_check(screen)
    time.sleep(1)
    # 🛑 PAUSE POINT
    
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ OPERATOR ACTION REQUIRED",
        "• Did Audio Analyser MONITOR audio get mute Between 0.5 - 1.5 seconds?\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Operator response received.", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E34",operator)   # YES
    write_excel("F34",result)     # PASS
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob CCW\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("MIC MODE knob set to fully CCW.", False)
    time.sleep(2)
    
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j13_off):
        screen.log_signal.emit("CONTROLLED MIC Connector J13 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect CONTROLLED MIC Connector J13.", True)
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j14_off):
        screen.log_signal.emit("HOT MIC Connector J14 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect HOT MIC Connector J14.", True)
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j15_off):
        screen.log_signal.emit("NORM PHONES Connector J15 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NORM PHONES Connector J15.", True)
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j16_off):
        screen.log_signal.emit("STBY PHONES Connector J16 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect STBY PHONES Connector J16.", True)
        
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("PHONES Connector J29 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PHONES Connector J29.", True)
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("MIC Connector J27 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC Connector J27.", True)

    screen.log_signal.emit("============ VOS DELAY TEST COMPLETED =============", False)






def run_norm(screen):
    set_popup_title("VOS Delay Test (NORM)")
    set_ch1_ch2_scale_10v(screen)
    screen.log_signal.emit("==========COMMENCING VOS DELAY TEST==========", False)
            
    #audio analyser output set to 750uvrms at 1khz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    time.sleep(2)

    audible_tone_check(screen)
    time.sleep(1)
    audible_monitor_check(screen)
    time.sleep(1)
    # 🛑 PAUSE POINT
    
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ OPERATOR ACTION REQUIRED",
        "• Did Audio Analyser MONITOR audio get mute Between 0.5 - 1.5 seconds?\n",
        RESOURCES_DIR / "hear.png",
        "yes_no",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("Operator response received.", False)
    time.sleep(2)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel("E33",operator)   # YES
    write_excel("F33",result)     # PASS
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully CCW.\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    screen.log_signal.emit("MIC MODE knob set to fully CCW.", False)
    time.sleep(2)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j13_off):
        screen.log_signal.emit("CONTROLLED MIC Connector J13 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect CONTROLLED MIC Connector J13.", True)
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j14_off):
        screen.log_signal.emit("HOT MIC Connector J14 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect HOT MIC Connector J14.", True)
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j15_off):
        screen.log_signal.emit("NORM PHONES Connector J15 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect NORM PHONES Connector J15.", True)
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j16_off):
        screen.log_signal.emit("STBY PHONES Connector J16 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect STBY PHONES Connector J16.", True)
        
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("PHONES Connector J29 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PHONES Connector J29.", True)
        
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("MIC Connector J27 successfully Disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC Connector J27.", True)
    
    screen.log_signal.emit("============ VOS DELAY TEST COMPLETED =============", False)