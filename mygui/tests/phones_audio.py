from core.paths import RESOURCES_DIR
from core.stm32_commands import STM32RelayController
import time
from PyQt5.QtWidgets import (
    QApplication
)
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel


def run(screen):
    
    screen.log_signal.emit("==========COMMENCING PHONES AUDIO TEST==========", False)
    
    screen.log_signal.emit("Step 1: disconnecting HOT MIC Connector (J14)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j14_off():
        screen.log_signal.emit("HOT MIC Connector J14 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect HOT MIC Connector J14", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 2: disconnecting NORMS PHONES Connector (J15)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_off():
        screen.log_signal.emit("NORMS PHONES Connector J15 successfully disconnected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect NORMS PHONES Connector J15", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
     
    screen.log_signal.emit("Step 3: connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j29_on():
        screen.log_signal.emit("J29 successfully connected", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 4: connecting NORMS PHONES Connector (J15) and CONTROLLED MIC Connector (J13)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_on():
        screen.log_signal.emit("NORMS PHONES Connector J15 successfully connected", False)
        time.sleep(0.5)
        if STM32RelayController.set_j13_on():
            screen.log_signal.emit("CONTROLLED MIC Connector J13 successfully connected", False)
            time.sleep(0.5)
        else:
            screen.log_signal.emit("ERROR: Failed to connect CONTROLLED MIC Connector J13", True)
            return
        
    else:
        screen.log_signal.emit("ERROR: Failed to connect NORMS PHONES Connector J15", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Turn the MIC MODE knob fully COUNTERCLOCKWISE (CCW)\n",
        RESOURCES_DIR / "knob_ccw.png","ok",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    
    time.sleep(2)
    
    data = read_apx_meter(screen,min_v="10.5", max_v="11.5",max_thd=10)
    if data:
        # write_excel("E25", data["observation"])   # measured value
        write_excel("E25", data["value"])         # raw vrms
        write_excel("F25", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=200,state="on")  # Ensure generator is OFF after test
    time.sleep(0.9)
    data = read_apx_meter(screen, min_v="7.7",max_thd=10)
    if data:
        # write_excel("E26", data["observation"])   # measured value
        write_excel("E26", data["value"])         # raw vrms
        write_excel("F26", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=3500)  
    data = read_apx_meter(screen, min_v="7.7",max_thd=10)
    if data:
        # write_excel("E26", data["observation"])   # measured value
        write_excel("E27", data["value"])         # raw vrms
        write_excel("F27", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    
    
    screen.log_signal.emit("Step 5: disconnecting NORMS PHONES Connector (J15) and connecting STBY PHONES Connector (J16)", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j15_off():
        screen.log_signal.emit("NORMS PHONES Connector J15 successfully disconnected", False)
        time.sleep(0.5)
        if STM32RelayController.set_j16_on():
            screen.log_signal.emit("STBY PHONES Connector J16 successfully connected", False)
            time.sleep(0.5)
        else:
            screen.log_signal.emit("ERROR: Failed to connect STBY PHONES Connector J16", True)
            return
        
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect NORMS PHONES Connector J15 or STBY PHONES Connector J16", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 6: Turning Switch (S24) to OFF", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s24_off():
        screen.log_signal.emit("S24 successfully turned OFF", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn OFF S24", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    screen.log_signal.emit("Step 7: Turning Switch (S25) to ON", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s25_on():
        screen.log_signal.emit("S25 successfully turned ON", False)
        time.sleep(0.5)
        
    else:
        screen.log_signal.emit("ERROR: Failed to turn ON S25", True)
        return

    QApplication.processEvents()
    time.sleep(2)
    
    data = read_apx_meter(screen,min_v="10.5", max_v="11.5",max_thd=10)
    if data:
        # write_excel("E25", data["observation"])   # measured value
        write_excel("E28", data["value"])         # raw vrms
        write_excel("F28", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=200,state="on")  # Ensure generator is OFF after test
    time.sleep(0.9)
    data = read_apx_meter(screen, min_v="7.7",max_thd=10)
    if data:
        # write_excel("E26", data["observation"])   # measured value
        write_excel("E29", data["value"])         # raw vrms
        write_excel("F29", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=3500)  
    data = read_apx_meter(screen, min_v="7.7",max_thd=10)
    if data:
        # write_excel("E26", data["observation"])   # measured value
        write_excel("E30", data["value"])         # raw vrms
        write_excel("F30", data["result"])        # PASS / FAIL
        
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    
    screen.log_signal.emit("✓ PHONES AUDIO TEST COMPLETED", False)
    time.sleep(0.5)