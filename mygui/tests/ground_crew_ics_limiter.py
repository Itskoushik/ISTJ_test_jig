import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from devices.apx_analyzer import read_apx_meter,generator_control
from core.excel_logger import write_excel_dynamic  
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import autoset_oscilloscope,set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW ICS LIMITER TEST (NORM)")
    screen.log_signal.emit("==========Commencing GROUND CREW ICS LIMITER test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)

    screen.log_signal.emit("Disconnecting the Audio analyser Gen output to the MIC Connector J27", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("MIC Connector J27 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC Connector J27", True)

    QApplication.processEvents()
    time.sleep(0.5)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Disconnecting the Audio analyser Gen output to the PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("PH Connector J29 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PH Connector J29", True)

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Connecting the Audio analyser Gen output to the MIC Connector J24", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j24_on):
        screen.log_signal.emit("MIC OUT Connector J24 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT Connector J24", True)

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    
    screen.log_signal.emit("Connecting the Audio analyser input to the GND CREW PH connector J26", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_on):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="1.0 mVrms", frequency=1000,gen_scale=9.3)
    time.sleep(0.9)
    data=read_apx_meter(screen,min_v=11.2,max_v=11.8)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F407", data["observation"])         # raw vrms
        write_excel_dynamic("K407", data["result"])        # PASS / FAIL
    time.sleep(0.5)
    screen.log_signal.emit("==========Commencing Headset check test===========", False)
    #turn the audio analyser gen output off.
    generator_control(screen,state="off")
    
    screen.log_signal.emit("Setting LOAD Switch S28 to the Center position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s28_neutral):
        screen.log_signal.emit("LOAD Switch S28 successfully set to Center position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set LOAD Switch S28 to Center position", True)

    QApplication.processEvents()
    time.sleep(0.5)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j24_off):
        screen.log_signal.emit("MIC OUT Connector J24 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT Connector J24", True)

    QApplication.processEvents()
    time.sleep(0.5)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_off):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Connecting Headset Adapter to HEADSET J25", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    time.sleep(0.5)
    autoset_oscilloscope(screen)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect Headset Adapter to HEADSET J25\n",
        RESOURCES_DIR / "headsetjb.jpeg",
        "ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("headset adapter connected to HEADSET J25", False)

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Speak into the microphone\n"
        "• Audio with no unusual noises or disruptions should be heard in the headset\n",
        RESOURCES_DIR / "microphone.png",
        "yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F409",operator)   # YES
    write_excel_dynamic("K409",result)     # PASS 
    
    screen.log_signal.emit("headset audio check completed", False)

    screen.log_signal.emit("Disconnecting Headset Adapter from HEADSET J25", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect Headset Adapter from HEADSET J25\n",
        RESOURCES_DIR / "headsetjb1.jpeg",
        "ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    set_ch1_ch2_scale_10v(screen)
    screen.log_signal.emit("headset adapter disconnected from HEADSET J25", False)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j24_on):
        screen.log_signal.emit("MIC OUT Connector J24 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT Connector J24", True)

    QApplication.processEvents()
    time.sleep(0.5)
    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_on):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Setting LOAD Switch S28 to the 600 ohms", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s28_600ohms):
        screen.log_signal.emit("LOAD Switch S28 successfully set to 600 ohms", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set LOAD Switch S28 to 600 ohms", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("==========Successfully completed Headset check test===========", False)
    
    
    screen.log_signal.emit("==========Successfully completed GROUND CREW ICS LIMITER test===========", False)
    

    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW ICS LIMITER TEST (STBY)")
    screen.log_signal.emit("==========Commencing GROUND CREW ICS LIMITER test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)

    screen.log_signal.emit("Disconnecting the Audio analyser Gen output to the MIC Connector J27", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("MIC Connector J27 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC Connector J27", True)

    QApplication.processEvents()
    time.sleep(0.5)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Disconnecting the Audio analyser Gen output to the PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("PH Connector J29 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PH Connector J29", True)

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Connecting the Audio analyser Gen output to the MIC Connector J24", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j24_on):
        screen.log_signal.emit("MIC OUT Connector J24 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT Connector J24", True)

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    screen.log_signal.emit("Connecting the Audio analyser input to the GND CREW PH connector J26", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_on):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="1.0 mVrms", frequency=1000,gen_scale=9.3)
    time.sleep(0.9)
    data=read_apx_meter(screen,min_v=11.2,max_v=11.8)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F408", data["observation"])         # raw vrms
        write_excel_dynamic("K408", data["result"])        # PASS / FAIL
    time.sleep(0.5)
    screen.log_signal.emit("==========Commencing Headset check test===========", False)
    #turn the audio analyser gen output off.
    generator_control(screen,state="off")
    
    screen.log_signal.emit("Setting LOAD Switch S28 to the Center position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s28_neutral):
        screen.log_signal.emit("LOAD Switch S28 successfully set to Center position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set LOAD Switch S28 to Center position", True)

    QApplication.processEvents()
    time.sleep(0.5)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j24_off):
        screen.log_signal.emit("MIC OUT Connector J24 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT Connector J24", True)

    QApplication.processEvents()
    time.sleep(0.5)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_off):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    autoset_oscilloscope(screen)
    screen.log_signal.emit("Connecting Headset Adapter to HEADSET J25", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect Headset Adapter to HEADSET J25\n",
        RESOURCES_DIR / "headsetjb.jpeg",
        "ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("headset adapter connected to HEADSET J25", False)  

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Speak into the microphone\n"
        "• Audio with no unusual noises or disruptions should be heard in the headset\n",
        RESOURCES_DIR / "microphone.png",
        "yes_no",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F410",operator)   # YES
    write_excel_dynamic("K410",result)     # PASS 
    screen.log_signal.emit("headset audio check completed", False)
    screen.log_signal.emit("Disconnecting Headset Adapter from HEADSET J25", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect Headset Adapter from HEADSET J25\n",
        RESOURCES_DIR / "headsetjb1.jpeg",
        "ok",None
    )
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    set_ch1_ch2_scale_10v(screen)
    screen.log_signal.emit("headset adapter disconnected from HEADSET J25", False)
    if STM32RelayController.send_with_retry(STM32RelayController.set_j24_on):
        screen.log_signal.emit("MIC OUT Connector J24 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect MIC OUT Connector J24", True)

    QApplication.processEvents()
    time.sleep(0.5)
    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_on):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Setting LOAD Switch S28 to the 600 ohms", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s28_600ohms):
        screen.log_signal.emit("LOAD Switch S28 successfully set to 600 ohms", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set LOAD Switch S28 to 600 ohms", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    screen.log_signal.emit("==========Successfully completed Headset check test===========", False)
    
    
    screen.log_signal.emit("==========Successfully completed GROUND CREW ICS LIMITER test===========", False)