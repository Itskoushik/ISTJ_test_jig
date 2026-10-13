import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController  
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel_dynamic,write_excel_dynamic
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER RECIEVE AUDIO RX SELECTION AND MUTING Test (NORM)")
    screen.log_signal.emit("==========Commencing USER RECIEVE AUDIO RX SELECTION AND MUTING Test==========", False)
    time.sleep(0.5)

    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("MIC Connector J27 successfully  disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect MIC Connector J27", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Connect the Audio analyser input and the oscilloscope to the PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
        screen.log_signal.emit("PH Connector J29 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect PH Connector J29", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting COM 1 switch S1 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s01_on):
        screen.log_signal.emit("COM 1 switch S1 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 1 switch S1 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 1 fully cw .\n",
        RESOURCES_DIR /"VUHF-1.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Rotated V/UHF 1 fully cw", False)
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F148", data["observation"])         # raw vrms
        write_excel_dynamic("K148", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F150", data["observation"])         # raw vrms
        write_excel_dynamic("K150", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F152", data["observation"])         # raw vrms
        write_excel_dynamic("K152", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F154", data["observation"])         # raw vrms
        write_excel_dynamic("K154", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F156", data["observation"])         # raw vrms
        write_excel_dynamic("K156", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting COM 1 switch S1 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s01_off):
        screen.log_signal.emit("COM 1 switch S1 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 1 switch S1 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    #com2
    screen.log_signal.emit("Setting COM 2 switch S2 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s02_on):
        screen.log_signal.emit("COM 2 switch S2 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 2 switch S2 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.7)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 2 fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"VUHF2alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.7)
    screen.log_signal.emit("Rotated V/UHF 2 fully cw", False)
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G148", data["observation"])         # raw vrms
        write_excel_dynamic("K148", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.7)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G150", data["observation"])         # raw vrms
        write_excel_dynamic("K150", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G152", data["observation"])         # raw vrms
        write_excel_dynamic("K152", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G154", data["observation"])         # raw vrms
        write_excel_dynamic("K154", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G156", data["observation"])         # raw vrms
        write_excel_dynamic("K156", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting COM 2 switch S2 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s02_off):
        screen.log_signal.emit("COM 2 switch S2 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 2 switch S2 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com3
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting COM 3 switch S3 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s03_on):
        screen.log_signal.emit("COM 3 switch S3 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 3 switch S3 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate HF fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"HF.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.9)
    
    screen.log_signal.emit("Rotated HF fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H148", data["observation"])         # raw vrms
        write_excel_dynamic("K148", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H150", data["observation"])         # raw vrms
        write_excel_dynamic("K150", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.8)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H152", data["observation"])         # raw vrms
        write_excel_dynamic("K152", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H154", data["observation"])         # raw vrms
        write_excel_dynamic("K154", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H156", data["observation"])         # raw vrms
        write_excel_dynamic("K156", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting COM 3 switch S3 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s03_off):
        screen.log_signal.emit("COM 3 switch S3 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 3 switch S3 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com4
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting COM 4 switch S4 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s04_on):
        screen.log_signal.emit("COM 4 switch S4 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 4 switch S4 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"SPARE.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated SPARE fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I148", data["observation"])         # raw vrms
        write_excel_dynamic("K148", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I150", data["observation"])         # raw vrms
        write_excel_dynamic("K150", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I152", data["observation"])         # raw vrms
        write_excel_dynamic("K152", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I154", data["observation"])         # raw vrms
        write_excel_dynamic("K154", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I156", data["observation"])         # raw vrms
        write_excel_dynamic("K156", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting COM 4 switch S4 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s04_off):
        screen.log_signal.emit("COM 4 switch S4 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 4 switch S4 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com5 s05
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting COM 5 switch S5 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s05_on):
        screen.log_signal.emit("COM 5 switch S5 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 5 switch S5 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate LD HLR fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"LD HLRalh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated LD HLR fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J148", data["observation"])         # raw vrms
        write_excel_dynamic("K148", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J150", data["observation"])         # raw vrms
        write_excel_dynamic("K150", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J152", data["observation"])         # raw vrms
        write_excel_dynamic("K152", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J154", data["observation"])         # raw vrms
        write_excel_dynamic("K154", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J156", data["observation"])         # raw vrms
        write_excel_dynamic("K156", data["result"])        # PASS / FAIL
    screen.log_signal.emit("Setting COM 5 switch S5 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s05_off):
        screen.log_signal.emit("COM 5 switch S5 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 5 switch S5 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #NAV 1 S7
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 1 switch S7 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s07_on):
        screen.log_signal.emit("NAV 1 switch S7 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 1 switch S7 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate IFF fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"IFF.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated IFF fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F160", data["observation"])         # raw vrms
        write_excel_dynamic("K160", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F162", data["observation"])         # raw vrms
        write_excel_dynamic("K162", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F164", data["observation"])         # raw vrms
        write_excel_dynamic("K164", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F166", data["observation"])         # raw vrms
        write_excel_dynamic("K166", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F168", data["observation"])         # raw vrms
        write_excel_dynamic("K168", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 1 switch S7 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s07_off):
        screen.log_signal.emit("NAV 1 switch S7 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 1 switch S7 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #nav 2 s8
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 2 switch S8 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s08_on):
        screen.log_signal.emit("NAV 2 switch S8 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 2 switch S8 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate VOR fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"VOR.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated VOR fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F184", data["observation"])         # raw vrms
        write_excel_dynamic("K184", data["result"])        # PASS / FAIL
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F186", data["observation"])         # raw vrms
        write_excel_dynamic("K186", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F188", data["observation"])         # raw vrms
        write_excel_dynamic("K188", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F190", data["observation"])         # raw vrms
        write_excel_dynamic("K190", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F192", data["observation"])         # raw vrms
        write_excel_dynamic("K192", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 2 switch S8 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s08_off):
        screen.log_signal.emit("NAV 2 switch S8 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 2 switch S8 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #NAV 3 s9
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 3 switch S9 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s09_on):
        screen.log_signal.emit("NAV 3 switch S9 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 3 switch S9 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate MKB fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"MKB.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated MKB fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H184", data["observation"])         # raw vrms
        write_excel_dynamic("K184", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H186", data["observation"])         # raw vrms
        write_excel_dynamic("K186", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H188", data["observation"])         # raw vrms
        write_excel_dynamic("K188", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H190", data["observation"])         # raw vrms
        write_excel_dynamic("K190", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H192", data["observation"])         # raw vrms
        write_excel_dynamic("K192", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting NAV 3 switch S9 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s09_off):
        screen.log_signal.emit("NAV 3 switch S9 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 3 switch S9 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #Nav 4 s10
    
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 4 switch S10 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s10_on):
        screen.log_signal.emit("NAV 4 switch S10 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 4 switch S10 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate DME fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"DME.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated DME fully cw", False)
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G160", data["observation"])         # raw vrms
        write_excel_dynamic("K160", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G162", data["observation"])         # raw vrms
        write_excel_dynamic("K162", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G164", data["observation"])         # raw vrms
        write_excel_dynamic("K164", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G166", data["observation"])         # raw vrms
        write_excel_dynamic("K166", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G168", data["observation"])         # raw vrms
        write_excel_dynamic("K168", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting NAV 4 switch S10 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s10_off):
        screen.log_signal.emit("NAV 4 switch S10 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 4 switch S10 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #nav 5 s11
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 5 switch S11 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s11_on):
        screen.log_signal.emit("NAV 5 switch S11 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 5 switch S11 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate HOMR fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"HOMR.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated HOMR fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H160", data["observation"])         # raw vrms
        write_excel_dynamic("K160", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H162", data["observation"])         # raw vrms
        write_excel_dynamic("K162", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H164", data["observation"])         # raw vrms
        write_excel_dynamic("K164", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H166", data["observation"])         # raw vrms
        write_excel_dynamic("K166", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H168", data["observation"])         # raw vrms
        write_excel_dynamic("K168", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 5 switch S11 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s11_off):
        screen.log_signal.emit("NAV 5 switch S11 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 5 switch S11 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #nav6 s12
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 6 switch S12 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s12_on):
        screen.log_signal.emit("NAV 6 switch S12 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 6 switch S12 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SONIC fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"SONIC.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Rotated SONIC fully cw", False)
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I160", data["observation"])         # raw vrms
        write_excel_dynamic("K160", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I162", data["observation"])         # raw vrms
        write_excel_dynamic("K162", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I164", data["observation"])         # raw vrms
        write_excel_dynamic("K164", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I166", data["observation"])         # raw vrms
        write_excel_dynamic("K166", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I168", data["observation"])         # raw vrms
        write_excel_dynamic("K168", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 6 switch S12 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s12_off):
        screen.log_signal.emit("NAV 6 switch S12 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 6 switch S12 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 1 switch S14 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s14_on):
        screen.log_signal.emit("DIR 1 switch S14 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 1 switch S14 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J160", data["observation"])         # raw vrms
        write_excel_dynamic("K160", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"sonic_plus.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J162", data["observation"])         # raw vrms
        write_excel_dynamic("K162", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J164", data["observation"])         # raw vrms
        write_excel_dynamic("K164", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J166", data["observation"])         # raw vrms
        write_excel_dynamic("K166", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J168", data["observation"])         # raw vrms
        write_excel_dynamic("K168", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 1 switch S14 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s14_off):
        screen.log_signal.emit("DIR 1 switch S14 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 1 switch S14 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    
    screen.log_signal.emit("Setting DIR 2 switch S15 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s15_on):
        screen.log_signal.emit("DIR 2 switch S15 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 2 switch S15 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F172", data["observation"])         # raw vrms
        write_excel_dynamic("K172", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F174", data["observation"])         # raw vrms
        write_excel_dynamic("K174", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F176", data["observation"])         # raw vrms
        write_excel_dynamic("K176", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F178", data["observation"])         # raw vrms
        write_excel_dynamic("K178", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F180", data["observation"])         # raw vrms
        write_excel_dynamic("K180", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 2 switch S15 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s15_off):
        screen.log_signal.emit("DIR 2 switch S15 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 2 switch S15 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 3 switch S16 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s16_on):
        screen.log_signal.emit("DIR 3 switch S16 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 3 switch S16 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G172", data["observation"])         # raw vrms
        write_excel_dynamic("K172", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G174", data["observation"])         # raw vrms
        write_excel_dynamic("K174", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G176", data["observation"])         # raw vrms
        write_excel_dynamic("K176", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G178", data["observation"])         # raw vrms
        write_excel_dynamic("K178", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G180", data["observation"])         # raw vrms
        write_excel_dynamic("K180", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 3 switch S16 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s16_off):
        screen.log_signal.emit("DIR 3 switch S16 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 3 switch S16 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 4 switch S17 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s17_on):
        screen.log_signal.emit("DIR 4 switch S17 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 4 switch S17 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H172", data["observation"])         # raw vrms
        write_excel_dynamic("K172", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H174", data["observation"])         # raw vrms
        write_excel_dynamic("K174", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H176", data["observation"])         # raw vrms
        write_excel_dynamic("K176", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H178", data["observation"])         # raw vrms
        write_excel_dynamic("K178", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H180", data["observation"])         # raw vrms
        write_excel_dynamic("K180", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 4 switch S17 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s17_off):
        screen.log_signal.emit("DIR 4 switch S17 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 4 switch S17 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting DIR 5 switch S18 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    if STM32RelayController.send_with_retry(STM32RelayController.set_s18_on):
        screen.log_signal.emit("DIR 5 switch S18 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 5 switch S18 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I172", data["observation"])         # raw vrms
        write_excel_dynamic("K172", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I174", data["observation"])         # raw vrms
        write_excel_dynamic("K174", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I176", data["observation"])         # raw vrms
        write_excel_dynamic("K176", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I178", data["observation"])         # raw vrms
        write_excel_dynamic("K178", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I180", data["observation"])         # raw vrms
        write_excel_dynamic("K180", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 5 switch S18 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s18_off):
        screen.log_signal.emit("DIR 5 switch S18 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 5 switch S18 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 6 switch S19 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s19_on):
        screen.log_signal.emit("DIR 6 switch S19 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 6 switch S19 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J172", data["observation"])         # raw vrms
        write_excel_dynamic("K172", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J174", data["observation"])         # raw vrms
        write_excel_dynamic("K174", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J176", data["observation"])         # raw vrms
        write_excel_dynamic("K176", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J178", data["observation"])         # raw vrms
        write_excel_dynamic("K178", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J180", data["observation"])         # raw vrms
        write_excel_dynamic("K180", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 6 switch S19 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s19_off):
        screen.log_signal.emit("DIR 6 switch S19 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 6 switch S19 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # screen.log_signal.emit("Disconnect the Audio analyser gen output from the RX AUD Connector J57 ", False)
    # QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    # if STM32RelayController.send_with_retry(STM32RelayController.set_j57_off):
    #     screen.log_signal.emit("RX AUD Connector J57 successfully  Disconnected", False)
    # else:
    #     screen.log_signal.emit("ERROR: Failed to Disconnect RX AUD Connector J57", True)
        

    # QApplication.processEvents()
    # time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and the oscilloscope from the PH Connector J29 ", False)  # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("PH Connector J29 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PH Connector J29", True)
        

    time.sleep(0.5)

    screen.log_signal.emit("==========Successfully Completed  USER RECIEVE AUDIO RX SELECTION AND MUTING Test===========", False)
    time.sleep(0.5)
    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER RECIEVE AUDIO RX SELECTION AND MUTING Test (STBY)")
    screen.log_signal.emit("==========Commencing USER RECIEVE AUDIO RX SELECTION AND MUTING Test==========", False)
    time.sleep(0.5)
    
    #set the audio analyser gen output to 5.5 Vrms @1 KHz
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_j27_off):
        screen.log_signal.emit("MIC Connector J27 successfully  disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to disconnect MIC Connector J27", True)
        
    screen.log_signal.emit("Connect the Audio analyser input and the oscilloscope to the PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
        screen.log_signal.emit("PH Connector J29 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect PH Connector J29", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting COM 1 switch S1 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s01_on):
        screen.log_signal.emit("COM 1 switch S1 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 1 switch S1 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 1 fully cw .\n",
        RESOURCES_DIR /"VUHF-1.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated V/UHF 1 fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F149", data["observation"])         # raw vrms
        write_excel_dynamic("K149", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F151", data["observation"])         # raw vrms
        write_excel_dynamic("K151", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F153", data["observation"])         # raw vrms
        write_excel_dynamic("K153", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F155", data["observation"])         # raw vrms
        write_excel_dynamic("K155", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F157", data["observation"])         # raw vrms
        write_excel_dynamic("K157", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting COM 1 switch S1 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s01_off):
        screen.log_signal.emit("COM 1 switch S1 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 1 switch S1 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    #com2
    screen.log_signal.emit("Setting COM 2 switch S2 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s02_on):
        screen.log_signal.emit("COM 2 switch S2 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 2 switch S2 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 2 fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"VUHF2alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated V/UHF 2 fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G149", data["observation"])         # raw vrms
        write_excel_dynamic("K149", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G151", data["observation"])         # raw vrms
        write_excel_dynamic("K151", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G153", data["observation"])         # raw vrms
        write_excel_dynamic("K153", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G155", data["observation"])         # raw vrms
        write_excel_dynamic("K155", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G157", data["observation"])         # raw vrms
        write_excel_dynamic("K157", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting COM 2 switch S2 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s02_off):
        screen.log_signal.emit("COM 2 switch S2 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 2 switch S2 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com3
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting COM 3 switch S3 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s03_on):
        screen.log_signal.emit("COM 3 switch S3 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 3 switch S3 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate HF fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"HF.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated HF fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H149", data["observation"])         # raw vrms
        write_excel_dynamic("K149", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H151", data["observation"])         # raw vrms
        write_excel_dynamic("K151", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H153", data["observation"])         # raw vrms
        write_excel_dynamic("K153", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H155", data["observation"])         # raw vrms
        write_excel_dynamic("K155", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H157", data["observation"])         # raw vrms
        write_excel_dynamic("K157", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting COM 3 switch S3 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s03_off):
        screen.log_signal.emit("COM 3 switch S3 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 3 switch S3 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com4
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting COM 4 switch S4 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s04_on):
        screen.log_signal.emit("COM 4 switch S4 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 4 switch S4 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"SPARE.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated SPARE fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I149", data["observation"])         # raw vrms
        write_excel_dynamic("K149", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I151", data["observation"])         # raw vrms
        write_excel_dynamic("K151", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I153", data["observation"])         # raw vrms
        write_excel_dynamic("K153", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I155", data["observation"])         # raw vrms
        write_excel_dynamic("K155", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I157", data["observation"])         # raw vrms
        write_excel_dynamic("K157", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting COM 4 switch S4 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s04_off):
        screen.log_signal.emit("COM 4 switch S4 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 4 switch S4 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com5 s05
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting COM 5 switch S5 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s05_on):
        screen.log_signal.emit("COM 5 switch S5 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 5 switch S5 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate LD HLR fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"LD HLRalh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated LD HLR fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J149", data["observation"])         # raw vrms
        write_excel_dynamic("K149", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J151", data["observation"])         # raw vrms
        write_excel_dynamic("K151", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J153", data["observation"])         # raw vrms
        write_excel_dynamic("K153", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J155", data["observation"])         # raw vrms
        write_excel_dynamic("K155", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J157", data["observation"])         # raw vrms
        write_excel_dynamic("K157", data["result"])        # PASS / FAIL
    screen.log_signal.emit("Setting COM 5 switch S5 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s05_off):
        screen.log_signal.emit("COM 5 switch S5 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 5 switch S5 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #NAV 1 S7
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 1 switch S7 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s07_on):
        screen.log_signal.emit("NAV 1 switch S7 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 1 switch S7 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate IFF fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"IFF.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated IFF fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F161", data["observation"])         # raw vrms
        write_excel_dynamic("K161", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F163", data["observation"])         # raw vrms
        write_excel_dynamic("K163", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F165", data["observation"])         # raw vrms
        write_excel_dynamic("K165", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F167", data["observation"])         # raw vrms
        write_excel_dynamic("K167", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F169", data["observation"])         # raw vrms
        write_excel_dynamic("K169", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting NAV 1 switch S7 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s07_off):
        screen.log_signal.emit("NAV 1 switch S7 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 1 switch S7 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #nav 2 s8
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 2 switch S8 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s08_on):
        screen.log_signal.emit("NAV 2 switch S8 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 2 switch S8 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate VOR fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"VOR.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated VOR fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F185", data["observation"])         # raw vrms
        write_excel_dynamic("K185", data["result"])        # PASS / FAIL
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F187", data["observation"])         # raw vrms
        write_excel_dynamic("K187", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F189", data["observation"])         # raw vrms
        write_excel_dynamic("K189", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F191", data["observation"])         # raw vrms
        write_excel_dynamic("K191", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F193", data["observation"])         # raw vrms
        write_excel_dynamic("K193", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 2 switch S8 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s08_off):
        screen.log_signal.emit("NAV 2 switch S8 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 2 switch S8 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #NAV 3 s9
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 3 switch S9 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s09_on):
        screen.log_signal.emit("NAV 3 switch S9 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 3 switch S9 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate MKB fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"MKB.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated MKB fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H185", data["observation"])         # raw vrms
        write_excel_dynamic("K185", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H187", data["observation"])         # raw vrms
        write_excel_dynamic("K187", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H189", data["observation"])         # raw vrms
        write_excel_dynamic("K189", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H191", data["observation"])         # raw vrms
        write_excel_dynamic("K191", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H193", data["observation"])         # raw vrms
        write_excel_dynamic("K193", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 3 switch S9 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s09_off):
        screen.log_signal.emit("NAV 3 switch S9 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 3 switch S9 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #Nav 4 s10
    
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 4 switch S10 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s10_on):
        screen.log_signal.emit("NAV 4 switch S10 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 4 switch S10 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate DME fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"DME.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    screen.log_signal.emit("Rotated DME fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G161", data["observation"])         # raw vrms
        write_excel_dynamic("K161", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G163", data["observation"])         # raw vrms
        write_excel_dynamic("K163", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G165", data["observation"])         # raw vrms
        write_excel_dynamic("K165", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G167", data["observation"])         # raw vrms
        write_excel_dynamic("K167", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G169", data["observation"])         # raw vrms
        write_excel_dynamic("K169", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 4 switch S10 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s10_off):
        screen.log_signal.emit("NAV 4 switch S10 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 4 switch S10 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #nav 5 s11
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 5 switch S11 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s11_on):
        screen.log_signal.emit("NAV 5 switch S11 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 5 switch S11 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate HOMR fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"HOMR.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated HOMR fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H161", data["observation"])         # raw vrms
        write_excel_dynamic("K161", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H163", data["observation"])         # raw vrms
        write_excel_dynamic("K163", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H165", data["observation"])         # raw vrms
        write_excel_dynamic("K165", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H167", data["observation"])         # raw vrms
        write_excel_dynamic("K167", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H169", data["observation"])         # raw vrms
        write_excel_dynamic("K169", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 5 switch S11 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s11_off):
        screen.log_signal.emit("NAV 5 switch S11 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 5 switch S11 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #nav6 s12
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting NAV 6 switch S12 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s12_on):
        screen.log_signal.emit("NAV 6 switch S12 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 6 switch S12 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SONIC fully cw .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"SONIC.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Rotated SONIC fully cw", False)
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I161", data["observation"])         # raw vrms
        write_excel_dynamic("K161", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I163", data["observation"])         # raw vrms
        write_excel_dynamic("K163", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,max_v=11,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I165", data["observation"])         # raw vrms
        write_excel_dynamic("K165", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I167", data["observation"])         # raw vrms
        write_excel_dynamic("K167", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I169", data["observation"])         # raw vrms
        write_excel_dynamic("K169", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting NAV 6 switch S12 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s12_off):
        screen.log_signal.emit("NAV 6 switch S12 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 6 switch S12 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 1 switch S14 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s14_on):
        screen.log_signal.emit("DIR 1 switch S14 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 1 switch S14 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J161", data["observation"])         # raw vrms
        write_excel_dynamic("K161", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n"
        "• Note: if other TX and RX knobs are fully cw, rotate it fully ccw. \n",
        RESOURCES_DIR /"sonic_plus.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J163", data["observation"])         # raw vrms
        write_excel_dynamic("K163", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J165", data["observation"])         # raw vrms
        write_excel_dynamic("K165", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J167", data["observation"])         # raw vrms
        write_excel_dynamic("K167", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J169", data["observation"])         # raw vrms
        write_excel_dynamic("K169", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 1 switch S14 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s14_off):
        screen.log_signal.emit("DIR 1 switch S14 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 1 switch S14 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 2 switch S15 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s15_on):
        screen.log_signal.emit("DIR 2 switch S15 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 2 switch S15 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F173", data["observation"])         # raw vrms
        write_excel_dynamic("K173", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F175", data["observation"])         # raw vrms
        write_excel_dynamic("K175", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F177", data["observation"])         # raw vrms
        write_excel_dynamic("K177", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F179", data["observation"])         # raw vrms
        write_excel_dynamic("K179", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F181", data["observation"])         # raw vrms
        write_excel_dynamic("K181", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 2 switch S15 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s15_off):
        screen.log_signal.emit("DIR 2 switch S15 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 2 switch S15 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 3 switch S16 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s16_on):
        screen.log_signal.emit("DIR 3 switch S16 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 3 switch S16 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G173", data["observation"])         # raw vrms
        write_excel_dynamic("K173", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G175", data["observation"])         # raw vrms
        write_excel_dynamic("K175", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G177", data["observation"])         # raw vrms
        write_excel_dynamic("K177", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G179", data["observation"])         # raw vrms
        write_excel_dynamic("K179", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G181", data["observation"])         # raw vrms
        write_excel_dynamic("K181", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 3 switch S16 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s16_off):
        screen.log_signal.emit("DIR 3 switch S16 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 3 switch S16 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 4 switch S17 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s17_on):
        screen.log_signal.emit("DIR 4 switch S17 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 4 switch S17 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H173", data["observation"])         # raw vrms
        write_excel_dynamic("K173", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H175", data["observation"])         # raw vrms
        write_excel_dynamic("K175", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_on):
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H177", data["observation"])         # raw vrms
        write_excel_dynamic("K177", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H179", data["observation"])         # raw vrms
        write_excel_dynamic("K179", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H181", data["observation"])         # raw vrms
        write_excel_dynamic("K181", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 4 switch S17 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s17_off):
        screen.log_signal.emit("DIR 4 switch S17 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 4 switch S17 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 5 switch S18 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s18_on):
        screen.log_signal.emit("DIR 5 switch S18 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 5 switch S18 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I173", data["observation"])         # raw vrms
        write_excel_dynamic("K173", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I175", data["observation"])         # raw vrms
        write_excel_dynamic("K175", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I177", data["observation"])         # raw vrms
        write_excel_dynamic("K177", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I179", data["observation"])         # raw vrms
        write_excel_dynamic("K179", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I181", data["observation"])         # raw vrms
        write_excel_dynamic("K181", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 5 switch S18 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s18_off):
        screen.log_signal.emit("DIR 5 switch S18 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 5 switch S18 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    generator_control(screen, level="5.50 Vrms", frequency=1000,gen_scale=2.0)
    screen.log_signal.emit("Setting DIR 6 switch S19 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s19_on):
        screen.log_signal.emit("DIR 6 switch S19 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 6 switch S19 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J173 ", data["observation"])         # raw vrms
        write_excel_dynamic("K164", data["result"])        # PASS / FAIL

    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to IN position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to IN position", False)
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J175", data["observation"])         # raw vrms
        write_excel_dynamic("K175", data["result"])        # PASS / FAIL
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC to OUT position .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("Press and Released SONIC to OUT position", False)
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    data=read_apx_meter(screen,min_v=9.9,max_v=12.1,max_thd=10)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J177", data["observation"])         # raw vrms
        write_excel_dynamic("K177", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s34_off):
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    generator_control(screen, level="5.50 Vrms", frequency=200,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J179", data["observation"])         # raw vrms
        write_excel_dynamic("K179", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    generator_control(screen, level="5.50 Vrms", frequency=3500,gen_scale=2.0)
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    data=read_apx_meter(screen,min_v=7.7,max_thd=10.0)
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J181", data["observation"])         # raw vrms
        write_excel_dynamic("K181", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting DIR 6 switch S19 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s19_off):
        screen.log_signal.emit("DIR 6 switch S19 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set DIR 6 switch S19 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and the oscilloscope from the PH Connector J29 ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("PH Connector J29 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PH Connector J29", True)

    
    screen.log_signal.emit("==========Successfully Completed USER RECIEVE AUDIO RX SELECTION AND MUTING Test===========", False)
    time.sleep(0.5)