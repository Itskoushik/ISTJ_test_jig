import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel_dynamic
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW OVERRIDE INTERCOM CHANNEL Test (NORM)")
    screen.log_signal.emit("==========Commencing GROUND CREW OVERRIDE INTERCOM CHANNEL Test===========", False)
    
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
    
    #set the audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    
    
    screen.log_signal.emit("Connecting the Audio analyser input to the GND CREW PH connector J26", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_on):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch to IN position .\n",
        RESOURCES_DIR / "or_switch.jpeg",
        "ok",None
    )

    screen.log_signal.emit("pressed and released O/R switch to IN position", False)
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F424", data["observation"])         # raw vrms
        write_excel_dynamic("K424", data["result"])        # PASS / FAIL

    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F426", data["observation"])         # raw vrms
        write_excel_dynamic("K426", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F428", data["observation"])         # raw vrms
        write_excel_dynamic("K428", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch to OUT position .\n",
        RESOURCES_DIR / "or_switch.jpeg",
        "ok",None
    )
    screen.log_signal.emit("pressed and released O/R switch to OUT position", False)

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    screen.log_signal.emit("==========Successfully completed GROUND CREW OVERRIDE INTERCOM CHANNEL Test===========", False)
    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW OVERRIDE INTERCOM CHANNEL Test (STBY)")
    screen.log_signal.emit("==========Commencing GROUND CREW OVERRIDE INTERCOM CHANNEL Test===========", False)
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
    
    #set the audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    
    
    screen.log_signal.emit("Connecting the Audio analyser input to the GND CREW PH connector J26", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_on):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch to IN position .\n",
        RESOURCES_DIR / "or_switch.jpeg",
        "ok",None
    )
    screen.log_signal.emit("pressed and released O/R switch to IN position", False)

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    
    #set the audio analyser gen output to 750 uVrms @1KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000) 
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F425", data["observation"])         # raw vrms
        write_excel_dynamic("K425", data["result"])        # PASS / FAIL

    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F427", data["observation"])         # raw vrms
        write_excel_dynamic("K427", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F429", data["observation"])         # raw vrms
        write_excel_dynamic("K429", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release O/R switch to OUT position .\n",
        RESOURCES_DIR / "or_switch.jpeg",
        "ok",None
    )
    screen.log_signal.emit("pressed and released O/R switch to OUT position", False)

    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(2)
    screen.log_signal.emit("==========Successfully completed GROUND CREW OVERRIDE INTERCOM CHANNEL Test===========", False)