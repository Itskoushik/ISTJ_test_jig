import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from devices.apx_analyzer import read_apx_meter,generator_control
from core.excel_logger import write_excel_dynamic  
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW PRIMARY INTERCOM CHANNEL ICS VOLUME test (NORM)")
    screen.log_signal.emit("==========Commencing GROUND CREW PRIMARY INTERCOM CHANNEL ICS VOLUME test===========", False)
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
    
    #the audio analyser should read <35 mVrms 
    data=read_apx_meter(screen,max_v=35,unit="mVrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G399", data["observation"])         # raw vrms
        write_excel_dynamic("K399", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting the GND CREW ICS switch S29 to the up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s29_on):
        screen.log_signal.emit("GND CREW ICS switch S29 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set GND CREW ICS switch S29 to up position", True)

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    
    
    screen.log_signal.emit("Setting the GND CREW LOAD switch S28 to the up 600 ohm", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s28_600ohms):
        screen.log_signal.emit("GND CREW LOAD switch S28 successfully set to 600ohms position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set GND CREW LOAD switch S28 to 600ohms position", True)

    QApplication.processEvents()
    time.sleep(0.5)

    #the audio analyser should read 11.0+-1.1 Vrms with <10% THD+N 
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G400", data["observation"])         # raw vrms
        write_excel_dynamic("K400", data["result"])        # PASS / FAIL
     
    #set the audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #the audio analyser should read >7.7 Vrms <10% THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G402", data["observation"])         # raw vrms
        write_excel_dynamic("K402", data["result"])        # PASS / FAIL 
    #set the audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #the audio analyser should read >7.7 Vrms <10% THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G404", data["observation"])         # raw vrms
        write_excel_dynamic("K404", data["result"])        # PASS / FAIL 
    
    screen.log_signal.emit("==========Successfully completed GROUND CREW PRIMARY INTERCOM CHANNEL ICS VOLUME test===========", False)
    

    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW PRIMARY INTERCOM CHANNEL ICS VOLUME test (STBY)")
    screen.log_signal.emit("==========Commencing GROUND CREW PRIMARY INTERCOM CHANNEL ICS VOLUME test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)

    screen.log_signal.emit("Connecting the Audio analyser Gen output to the MIC Connector J24", False)
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
    
    
    screen.log_signal.emit("Setting the GND CREW ICS switch S29 to the up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s29_on):
        screen.log_signal.emit("GND CREW ICS switch S29 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set GND CREW ICS switch S29 to up position", True)

    QApplication.processEvents()
    time.sleep(0.5)
     
    
    screen.log_signal.emit("Setting the GND CREW LOAD switch S28 to the up 600 ohm", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s28_600ohms):
        screen.log_signal.emit("GND CREW LOAD switch S28 successfully set to 600ohms position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set GND CREW LOAD switch S28 to 600ohms position", True)

    QApplication.processEvents()
    time.sleep(0.5)
    #the audio analyser should read 11.0+-1.1 Vrms with <10% THD+N 
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G401", data["observation"])         # raw vrms
        write_excel_dynamic("K401", data["result"])        # PASS / FAIL
     
    #set the audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #the audio analyser should read >7.7 Vrms <10% THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G403", data["observation"])         # raw vrms
        write_excel_dynamic("K403", data["result"])        # PASS / FAIL 
    #set the audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #the audio analyser should read >7.7 Vrms <10% THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G405", data["observation"])         # raw vrms
        write_excel_dynamic("K405", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("==========Successfully completed GROUND CREW PRIMARY INTERCOM CHANNEL ICS VOLUME test===========", False)