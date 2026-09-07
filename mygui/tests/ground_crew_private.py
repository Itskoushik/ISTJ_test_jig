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
    set_popup_title("GROUND CREW PRIVATE INTERCOM CHANNEL Test (NORM)")
    screen.log_signal.emit("==========Commencing GROUND CREW PRIVATE INTERCOM CHANNEL test===========", False)
    screen.log_signal.emit("Disconnecting the Audio analyser Gen output to the MIC Connector J27", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("MIC Connector J27 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC Connector J27", True)

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
    screen.log_signal.emit("Setting PRIVATE Switch S33 to the Up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_on):
        screen.log_signal.emit("PRIVATE Switch S33 successfully set to Up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE Switch S33 to Up position", True)

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F414", data["observation"])         # raw vrms
        write_excel_dynamic("K414", data["result"])        # PASS / FAIL
        
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F416", data["observation"])         # raw vrms
        write_excel_dynamic("K416", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F418", data["observation"])         # raw vrms
        write_excel_dynamic("K418", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting PRIVATE Switch S33 to the Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_off):
        screen.log_signal.emit("PRIVATE Switch S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE Switch S33 to Down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("==========Successfully completed GROUND CREW PRIVATE INTERCOM CHANNEL test===========", False)

def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW PRIVATE INTERCOM CHANNEL Test (STBY)")
    screen.log_signal.emit("==========Commencing GROUND CREW PRIVATE INTERCOM CHANNEL test===========", False)
    screen.log_signal.emit("Disconnecting the Audio analyser Gen output to the MIC Connector J27", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("MIC Connector J27 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC Connector J27", True)

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
    screen.log_signal.emit("Setting PRIVATE Switch S33 to the Up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_on):
        screen.log_signal.emit("PRIVATE Switch S33 successfully set to Up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE Switch S33 to Up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    #Audio analyser should read >9.9 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=9.9,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F415", data["observation"])         # raw vrms
        write_excel_dynamic("K415", data["result"])        # PASS / FAIL

    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F417", data["observation"])         # raw vrms
        write_excel_dynamic("K417", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #Audio analyser should read >7.7 Vrms with <10% THD + N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F419", data["observation"])         # raw vrms
        write_excel_dynamic("K419", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting PRIVATE Switch S33 to the Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_off):
        screen.log_signal.emit("PRIVATE Switch S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set PRIVATE Switch S33 to Down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("==========Successfully completed GROUND CREW PRIVATE INTERCOM CHANNEL test===========", False)