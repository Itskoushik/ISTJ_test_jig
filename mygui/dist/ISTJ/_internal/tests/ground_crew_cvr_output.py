import time
from core.paths import RESOURCES_DIR
import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel_dynamic
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import autoset_oscilloscope,set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW CVR OUTPUT LEVEL TEST (NORM)")
    screen.log_signal.emit("==========Commencing GROUND CREW CVR OUTPUT LEVEL test===========", False)

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

    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_off):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Connecting the Audio analyser input to CVR Connector J23 .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j23_on):
        screen.log_signal.emit("CVR Connector J23 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect CVR Connector J23", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    #the audio analyser should read 1.0+-0.1 Vrms with <10% THD +N
    data=read_apx_meter(screen,min_v=0.9,max_v=1.1,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F434", data["observation"])         # raw vrms
        write_excel_dynamic("K434", data["result"])        # PASS / FAIL

    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #the audio analyser should read >700 mVrms with <10% THD +N
    data=read_apx_meter(screen,min_v=700,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F436", data["observation"])         # raw vrms
        write_excel_dynamic("K436", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #the audio analyser should read >700 mVrms with <10% THD +N
    data=read_apx_meter(screen,min_v=700,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F438", data["observation"])         # raw vrms
        write_excel_dynamic("K438", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Disconnecting the Audio analyser input to CVR Connector J23 .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j23_off):
        screen.log_signal.emit("CVR Connector J23 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect CVR Connector J23", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("==========Successfully completed GROUND CREW CVR OUTPUT LEVEL test===========", False)
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("GROUND CREW CVR OUTPUT LEVEL TEST (STBY)")
    screen.log_signal.emit("==========Commencing GROUND CREW CVR OUTPUT LEVEL test===========", False)

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

    if STM32RelayController.send_with_retry(STM32RelayController.set_j26_off):
        screen.log_signal.emit("GND CREW PH Connector J26 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect GND CREW PH Connector J26", True)

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Connecting the Audio analyser input to CVR Connector J23 .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j23_on):
        screen.log_signal.emit("CVR Connector J23 successfully Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect CVR Connector J23", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    generator_control(screen, level="750.0 uVrms", frequency=1000)
    #the audio analyser should read 1.0+-0.1 Vrms with <10% THD +N
    data=read_apx_meter(screen,min_v=0.9,max_v=1.1,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F435", data["observation"])         # raw vrms
        write_excel_dynamic("K435", data["result"])        # PASS / FAIL
        
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    #the audio analyser should read >700 mVrms with <10% THD +N
    data=read_apx_meter(screen,min_v=700,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F437", data["observation"])         # raw vrms
        write_excel_dynamic("K437", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    #the audio analyser should read >700 mVrms with <10% THD +N
    data=read_apx_meter(screen,min_v=700,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F439", data["observation"])         # raw vrms
        write_excel_dynamic("K439", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Disconnecting the Audio analyser input to CVR Connector J23 .", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j23_off):
        screen.log_signal.emit("CVR Connector J23 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect CVR Connector J23", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("==========Successfully completed GROUND CREW CVR OUTPUT LEVEL test===========", False)