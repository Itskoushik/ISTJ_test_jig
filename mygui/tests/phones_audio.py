from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("PHONES AUDIO TEST")
    screen.log_signal.emit("==========COMMENCING PHONES AUDIO TEST==========", False)
    
    screen.log_signal.emit("disconnecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j14_off):
        screen.log_signal.emit("HOT MIC Connector J14 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect HOT MIC Connector J14", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("disconnecting NORMS PHONES Connector (J15)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j15_off):
        screen.log_signal.emit("NORMS PHONES Connector J15 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect NORMS PHONES Connector J15", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
     
    screen.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
        screen.log_signal.emit("STATION BOX PH Connector J29 successfully connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("connecting NORMS PHONES Connector (J15) and CONTROLLED MIC Connector (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j15_on):
        screen.log_signal.emit("NORMS PHONES Connector J15 successfully connected", False)
        time.sleep(0.5)
        if STM32RelayController.send_with_retry(STM32RelayController.set_j13_on):
            screen.log_signal.emit("CONTROLLED MIC Connector J13 successfully connected", False)
            time.sleep(0.5)
        else:
            screen.log_signal.emit("ERROR: Failed to connect CONTROLLED MIC Connector J13", True)
            
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect NORMS PHONES Connector J15", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
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
    
    time.sleep(2)
    screen.log_signal.emit("MIC MODE knob set to fully CCW.", False)
    data = read_apx_meter(screen,min_v="10.5", max_v="11.5",max_thd=10)
    if data:
        # write_excel("E25", data["observation"])   # measured observation
        write_excel("E25", data["observation"])         # raw vrms
        write_excel("F25", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=200,state="on")  # Ensure generator is OFF after test
    time.sleep(0.9)
    data = read_apx_meter(screen, min_v="7.7",max_thd=10)
    if data:
        # write_excel("E26", data["observation"])   # measured observation
        write_excel("E26", data["observation"])         # raw vrms
        write_excel("F26", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=3500)  
    data = read_apx_meter(screen, min_v="7.7",max_thd=10)
    if data:
        # write_excel("E26", data["observation"])   # measured observation
        write_excel("E27", data["observation"])         # raw vrms
        write_excel("F27", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    
    
    screen.log_signal.emit("disconnecting NORMS PHONES Connector (J15) and connecting STBY PHONES Connector (J16)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j15_off):
        screen.log_signal.emit("NORMS PHONES Connector J15 successfully disconnected", False)
        time.sleep(0.5)
        if STM32RelayController.send_with_retry(STM32RelayController.set_j16_on):
            screen.log_signal.emit("STBY PHONES Connector J16 successfully connected", False)
            time.sleep(0.5)
        else:
            screen.log_signal.emit("ERROR: Failed to connect STBY PHONES Connector J16", True)
            
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect NORMS PHONES Connector J15 or STBY PHONES Connector J16", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Turning Switch (S24) to Down Position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s24_off):
        screen.log_signal.emit("S24 successfully turned to Down Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn S24 to Down Position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Turning Switch (S25) to Up Position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s25_on):
        screen.log_signal.emit("S25 successfully turned to Up Position", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn S25 to Up Position", True)
        

    QApplication.processEvents()
    time.sleep(2)
    
    data = read_apx_meter(screen,min_v="10.5", max_v="11.5",max_thd=10)
    if data:
        # write_excel("E25", data["observation"])   # measured observation
        write_excel("E28", data["observation"])         # raw vrms
        write_excel("F28", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=200,state="on")  # Ensure generator is OFF after test
    time.sleep(0.9)
    data = read_apx_meter(screen, min_v="7.7",max_thd=10)
    if data:
        # write_excel("E26", data["observation"])   # measured observation
        write_excel("E29", data["observation"])         # raw vrms
        write_excel("F29", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=3500)  
    data = read_apx_meter(screen, min_v="7.7",max_thd=10)
    if data:
        # write_excel("E26", data["observation"])   # measured observation
        write_excel("E30", data["observation"])         # raw vrms
        write_excel("F30", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    
    screen.log_signal.emit("============ PHONES AUDIO TEST COMPLETED =============", False)
    time.sleep(0.5)