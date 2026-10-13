import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from core.paths import RESOURCES_DIR
import core.dmm_reader as _dmm_module
from core.excel_logger import write_excel_dynamic,write_excel
from devices.power_supply import check_current_ch1
from core.oscilloscope_helper import set_ch1_ch2_scale_10v


def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    screen.log_signal.emit("==========Commencing power supply test===========", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_s25_off):
        screen.log_signal.emit("S25 successfully switched to Down Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S25 to Down Position", True)
    time.sleep(1)
    if STM32RelayController.send_with_retry(STM32RelayController.set_s24_on):
        screen.log_signal.emit("S24 successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S24 to Up Position", True)
    time.sleep(1)
    if STM32RelayController.send_with_retry(STM32RelayController.set_j67_on):
        screen.log_signal.emit("J67 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J67 to Multimeter +ve lead", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()

    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS10 and DS11 indicators should illuminate red.\n",
        RESOURCES_DIR / "ds_10_11.jpeg","yes_no",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F12",operator)   # YES
    write_excel("K12",result)     # PASS 
    screen.check_abort()
    
    #power supply current meter should read between 1.3A to 2.0A
    data=check_current_ch1(screen.psu_inst)
    if data:
        write_excel_dynamic("F13",data["value"])
        write_excel("K13",data["result"])
    
    screen.log_signal.emit(
        f"Power Supply Current: {data['value']}  {data['result']}",
        data["result"] == "FAIL"
    )
        
    #multimeter should read 11+-1.1 Vdc
    result=_dmm_module.read_voltage(screen,"Power Supply Voltage Check", "9.9V","12.1V")
    if result:
        write_excel_dynamic("F14",result["observation"])
        write_excel("K14",result["result"])
    screen.log_signal.emit("Disconnecting the JACK J67 from Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j67_off):
        screen.log_signal.emit("J67 successfully Disconnected from Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J67 from Multimeter +ve lead", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Connecting the JACK J68 to Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j68_on):
        screen.log_signal.emit("J68 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J68 to Multimeter +ve lead", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    #multimeter should read -11 Vdc +-1.1V
    result=_dmm_module.read_voltage(screen,"J68 Multimeter Voltage Check", "-12.1","-9.9V")
    if result:
        write_excel_dynamic("F15",result["observation"])
        write_excel("K15",result["result"])
    
    screen.log_signal.emit("Disconnecting the JACK J68 from Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j68_off):
        screen.log_signal.emit("J68 successfully Disconnected from Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J68 from Multimeter +ve lead", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
        
    screen.log_signal.emit("==========Successfully Completed power supply test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    
    
    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    screen.log_signal.emit("==========Commencing power supply test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    if STM32RelayController.send_with_retry(STM32RelayController.set_s24_off):
        screen.log_signal.emit("S24 successfully switched to Down Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S24 to Down Position", True)
    time.sleep(0.6)    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s25_on):
        screen.log_signal.emit("S25 successfully switched to Up Position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to switch S25 to Up Position", True)

    QApplication.processEvents()
    time.sleep(1)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS12 and DS13 indicators should illuminate red.\n",
        RESOURCES_DIR / "ds_12_13.jpeg","yes_no",None
    )

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F16",operator)   # YES
    write_excel("K16",result)     # PASS 
    
    screen.check_abort()

    #power supply current meter should read between 1.3A to 2.0A
    data=check_current_ch1(screen.psu_inst)
    if data:
        write_excel_dynamic("F17",data["value"])
        write_excel("K17",data["result"])
        
    screen.log_signal.emit(
        f"Power Supply Current: {data['value']}  {data['result']}",
        data["result"] == "FAIL"
    )
    # screen.operator_event.clear()
    # # 🛑 PAUSE POINT
    # screen.operator_event.clear()
    # screen.show_popup_signal.emit(
    #     "⚠ Operator Action Required",
    #     "• Set STBY/NORMAL Switch to STBY.\n",
    #     RESOURCES_DIR / "stby.jpeg","ok",None
    # )
    # # ⏸ WAIT until operator clicks OK
    # screen.operator_event.wait()
    
    # time.sleep(2)

    
    screen.log_signal.emit("Connecting the JACK J70 to Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j70_on):
        screen.log_signal.emit("J70 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J70 to Multimeter +ve lead", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    #multimeter should read +11 Vdc +-1.1V
    result=_dmm_module.read_voltage(screen,"J70 Multimeter Voltage Check", "9.9V","12.1V")
    if result:
        write_excel_dynamic("F18",result["observation"])
        write_excel("K18",result["result"])
    screen.log_signal.emit("Disconnecting the JACK J70 from Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j70_off):
        screen.log_signal.emit("J70 successfully Disconnected from Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J70 from Multimeter +ve lead", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("Connecting the JACK J71 to Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j71_on):
        screen.log_signal.emit("J71 successfully Connected to Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J71 to Multimeter +ve lead", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    #multimeter should read -11 Vdc +-1.1V
    result=_dmm_module.read_voltage(screen,"J71 Multimeter Voltage Check", "-12.1V","-9.9V")
    if result:
        write_excel_dynamic("F19",result["observation"])
        write_excel("K19",result["result"])
    screen.log_signal.emit("Disconnecting the JACK J71 from Multimeter +ve lead .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j71_off):
        screen.log_signal.emit("J71 successfully Disconnected from Multimeter +ve lead", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J71 from Multimeter +ve lead", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.check_abort()
    
    screen.log_signal.emit("==========Successfully Completed power supply test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
    
    
    
    
    
    