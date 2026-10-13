import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController 
from devices.apx_analyzer import generator_control,read_apx_meter
from core.excel_logger import write_excel_dynamic,write_excel_dynamic
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
from core.tuning_workflow import set_popup_title
def run_norm(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER TRANSMIT AUDIO TX OUTPUT LEVEL Test (NORM)")
    screen.log_signal.emit("==========Commencing USER TRANSMIT AUDIO TX OUTPUT LEVEL test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("J29 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J29", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    #j07
    screen.log_signal.emit("Setting the switch S33 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_off):
        screen.log_signal.emit("S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to Down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to IN position .\n",
        RESOURCES_DIR /"vhf1alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set V/UHF 1 to IN position", False)
    

    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT Connector J7", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j07_on):
        screen.log_signal.emit("MIC OUT Connector J7 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT Connector J7", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000,gen_scale=9.066)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE
    
    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS1 Should illuminate red .\n",
        RESOURCES_DIR /"ds1.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F89", data["observation"])         # raw vrms
        write_excel_dynamic("K89", data["result"])        # PASS / FAIL

    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F91", data["observation"])         # raw vrms
        write_excel_dynamic("K91", data["result"])        # PASS / FAIL

    #set audio analyser gen output to 750 uVrms @3500 Hz
    time.sleep(0.5)
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F93", data["observation"])         # raw vrms 
        write_excel_dynamic("K93", data["result"])        # PASS / FAIL
    time.sleep(0.5)
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to OUT position .\n",
        RESOURCES_DIR /"vhf1alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set V/UHF 1 to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT Connector J7", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j07_off):
        screen.log_signal.emit("MIC OUT Connector J7 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT Connector J7", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J8 test
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to IN position .\n",
        RESOURCES_DIR /"VUHF-2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set V/UHF 2 to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT COM 2 Connector J8", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j08_on):
        screen.log_signal.emit("MIC OUT COM 2 Connector J8 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT COM 2 Connector J8", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000,gen_scale=9.066)
    time.sleep(0.5)

    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS2 Should illuminate red .\n",
        RESOURCES_DIR /"ds2.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("G87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G89", data["observation"])         # raw vrms
        write_excel_dynamic("K89", data["result"])        # PASS / FAIL
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)

    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G91", data["observation"])         # raw vrms
        write_excel_dynamic("K91", data["result"])        # PASS / FAIL 
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G93", data["observation"])         # raw vrms
        write_excel_dynamic("K93", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to OUT position .\n",
        RESOURCES_DIR /"VUHF-2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set V/UHF 2 to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 2 Connector J8", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j08_off):
        screen.log_signal.emit("MIC OUT COM 2 Connector J8 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 2 Connector J8", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J9 test
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to IN position .\n",
        RESOURCES_DIR /"hfalh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set HF to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT COM 3 Connector J9", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j09_on):
        screen.log_signal.emit("MIC OUT COM 3 Connector J9 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT COM 3 Connector J9", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000,gen_scale=9.066)
    time.sleep(0.5)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS3 Should illuminate red .\n",
        RESOURCES_DIR /"ds3.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("H87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H89", data["observation"])         # raw vrms
        write_excel_dynamic("K89", data["result"])        # PASS / FAIL

    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H91", data["observation"])         # raw vrms
        write_excel_dynamic("K91", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H93", data["observation"])         # raw vrms
        write_excel_dynamic("K93", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to OUT position .\n",
        RESOURCES_DIR /"hfalh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set HF to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 3 Connector J9", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j09_off):
        screen.log_signal.emit("MIC OUT COM 3 Connector J9 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 3 Connector J9", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J10 test 
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE to IN position .\n",
        RESOURCES_DIR /"sparealh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set SPARE to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT COM 4 Connector J10", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j10_on):
        screen.log_signal.emit("MIC OUT COM 4 Connector J10 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT COM 4 Connector J10", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000, gen_scale=9.066)
    time.sleep(0.5)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS4 Should illuminate red .\n",
        RESOURCES_DIR /"ds4.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("I87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I89", data["observation"])         # raw vrms
        write_excel_dynamic("K89", data["result"])        # PASS / FAIL
    
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I91", data["observation"])         # raw vrms
        write_excel_dynamic("K91", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I93", data["observation"])         # raw vrms
        write_excel_dynamic("K93", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE to OUT position .\n",
        RESOURCES_DIR /"sparealh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set SPARE to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 4 Connector J10", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j10_off):
        screen.log_signal.emit("MIC OUT COM 4 Connector J10 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 4 Connector J10", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #j11 test
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set LD HLR to IN position .\n",
        RESOURCES_DIR /"LD HLR.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set LD HLR to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT COM 5 Connector J11", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j11_on):
        screen.log_signal.emit("MIC OUT COM 5 Connector J11 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT COM 5 Connector J11", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000, gen_scale=9.066)
    time.sleep(0.5)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS5 Should illuminate red .\n",
        RESOURCES_DIR /"ds5.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("J87",operator)   # YES
    write_excel_dynamic("K87",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J89", data["observation"])         # raw vrms
        write_excel_dynamic("K89", data["result"])        # PASS / FAIL
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J91", data["observation"])         # raw vrms
        write_excel_dynamic("K91", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J93", data["observation"])         # raw vrms
        write_excel_dynamic("K93", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set LD HLR to OUT position .\n",
        RESOURCES_DIR /"LD HLR.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set LD HLR to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 5 Connector J11", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j11_off):
        screen.log_signal.emit("MIC OUT COM 5 Connector J11 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 5 Connector J11", True)
        

    time.sleep(0.5)

    screen.log_signal.emit("==========Successfully Completed  USER TRANSMIT AUDIO TX OUTPUT LEVEL test===========", False)
    time.sleep(0.5)

    
def run_stby(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("USER TRANSMIT AUDIO TX OUTPUT LEVEL Test (STBY)")
    screen.log_signal.emit("==========Commencing USER TRANSMIT AUDIO TX OUTPUT LEVEL test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    if STM32RelayController.send_with_retry(STM32RelayController.set_j29_off):
        screen.log_signal.emit("J29 successfully Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J29", True)

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    screen.log_signal.emit("Setting the switch S33 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s33_off):
        screen.log_signal.emit("S33 successfully set to Down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Set S33 to Down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #j07
    
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to IN position .\n",
        RESOURCES_DIR /"vhf1alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set V/UHF 1 to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT Connector J7", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j07_on):
        screen.log_signal.emit("MIC OUT Connector J7 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT Connector J7", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000, gen_scale=9.066)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS1 Should illuminate red .\n",
        RESOURCES_DIR /"ds1.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("F88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F90", data["observation"])         # raw vrms
        write_excel_dynamic("K90", data["result"])        # PASS / FAIL


    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F92", data["observation"])         # raw vrms
        write_excel_dynamic("K92", data["result"])        # PASS / FAIL

    #set audio analyser gen output to 750 uVrms @3500 Hz
    time.sleep(0.5)
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("F94", data["observation"])         # raw vrms 
        write_excel_dynamic("K94", data["result"])        # PASS / FAIL
    time.sleep(0.5)
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    
    time.sleep(0.5)
        # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 1 to OUT position .\n",
        RESOURCES_DIR /"vhf1alh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set V/UHF 1 to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT Connector J7", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j07_off):
        screen.log_signal.emit("MIC OUT Connector J7 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT Connector J7", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J8 test
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to IN position .\n",
        RESOURCES_DIR /"VUHF-2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set V/UHF 2 to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT COM 2 Connector J8", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j08_on):
        screen.log_signal.emit("MIC OUT COM 2 Connector J8 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT COM 2 Connector J8", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000, gen_scale=9.066)
    time.sleep(0.5)

    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS2 Should illuminate red .\n",
        RESOURCES_DIR /"ds2.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("G88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G90", data["observation"])         # raw vrms
        write_excel_dynamic("K90", data["result"])        # PASS / FAIL

    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)

    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G92", data["observation"])         # raw vrms
        write_excel_dynamic("K92", data["result"])        # PASS / FAIL 
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("G94", data["observation"])         # raw vrms
        write_excel_dynamic("K94", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set V/UHF 2 to OUT position .\n",
        RESOURCES_DIR /"VUHF-2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set V/UHF 2 to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 2 Connector J8", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j08_off):
        screen.log_signal.emit("MIC OUT COM 2 Connector J8 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 2 Connector J8", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J9 test
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to IN position .\n",
        RESOURCES_DIR /"hfalh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set HF to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT COM 3 Connector J9", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j09_on):
        screen.log_signal.emit("MIC OUT COM 3 Connector J9 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT COM 3 Connector J9", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000, gen_scale=9.066)
    time.sleep(0.5)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS3 Should illuminate red .\n",
        RESOURCES_DIR /"ds3.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("H88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H90", data["observation"])         # raw vrms
        write_excel_dynamic("K90", data["result"])        # PASS / FAIL
    

    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H92", data["observation"])         # raw vrms
        write_excel_dynamic("K92", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("H94", data["observation"])         # raw vrms
        write_excel_dynamic("K94", data["result"])        # PASS / FAIL

    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set HF to OUT position .\n",
        RESOURCES_DIR /"hfalh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set HF to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 3 Connector J9", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j09_off):
        screen.log_signal.emit("MIC OUT COM 3 Connector J9 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 3 Connector J9", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #J10 test 
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE to IN position .\n",
        RESOURCES_DIR /"sparealh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set SPARE to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT COM 4 Connector J10", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j10_on):
        screen.log_signal.emit("MIC OUT COM 4 Connector J10 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT COM 4 Connector J10", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000, gen_scale=9.066)
    time.sleep(0.5)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s30_on():
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS4 Should illuminate red .\n",
        RESOURCES_DIR /"ds4.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("I88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I90", data["observation"])         # raw vrms
        write_excel_dynamic("K90", data["result"])        # PASS / FAIL
    
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I92", data["observation"])         # raw vrms
        write_excel_dynamic("K92", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("I94", data["observation"])         # raw vrms
        write_excel_dynamic("K94", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set SPARE to OUT position .\n",
        RESOURCES_DIR /"sparealh2.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set SPARE to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 4 Connector J10", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j10_off):
        screen.log_signal.emit("MIC OUT COM 4 Connector J10 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 4 Connector J10", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    #j11 test
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set LD HLR to IN position .\n",
        RESOURCES_DIR /"LD HLR.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set LD HLR to IN position", False)
    screen.log_signal.emit("connected the Audio analyser input and oscilloscope to the MIC OUT COM 5 Connector J11", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j11_on):
        screen.log_signal.emit("MIC OUT COM 5 Connector J11 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to connected MIC OUT COM 5 Connector J11", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    #set audio analyser gen output to 750 uVrms @1 KHz
    generator_control(screen, level="750.0 uVrms", frequency=1000, gen_scale=9.066)
    time.sleep(0.5)
    screen.log_signal.emit("Setting TX Switch S30 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_on):
        screen.log_signal.emit("S30 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to up position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• DS5 Should illuminate red .\n",
        RESOURCES_DIR /"ds5.jpeg","yes_no",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    result = getattr(screen, "last_test_result", "")
    operator = getattr(screen, "last_operator_response", "")
    print("Operator:", operator)   # YES / NO
    print("Result:", result)       # PASS / FAIL

    write_excel_dynamic("J88",operator)   # YES
    write_excel_dynamic("K88",result)     # PASS 
    
    #Audio analyser should read 500 +-50m Vrms with <10% THD+N
    data=read_apx_meter(screen,min_v=450,max_v=550,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J90", data["observation"])         # raw vrms
        write_excel_dynamic("K90", data["result"])        # PASS / FAIL
    
    #set audio analyser gen output to 750 uVrms @200 Hz
    generator_control(screen, level="750.0 uVrms", frequency=200)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J92", data["observation"])         # raw vrms
        write_excel_dynamic("K92", data["result"])        # PASS / FAIL
    #set audio analyser gen output to 750 uVrms @3500 Hz
    generator_control(screen, level="750.0 uVrms", frequency=3500)
    time.sleep(0.5)
    #audio analyser should read >350 mVrms with <10% THD+N
    data=read_apx_meter(screen,min_v=350,max_thd=10.0,unit="mvrms")
    if data:
        # write_excel_dynamic("E13", data["observation"])   # measured observation
        write_excel_dynamic("J94", data["observation"])         # raw vrms
        write_excel_dynamic("K94", data["result"])        # PASS / FAIL
    
    screen.log_signal.emit("Setting TX Switch S30 to Down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_s30_off):
        screen.log_signal.emit("S30 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set S30 to down position", True)
        

    QApplication.processEvents()
    time.sleep(0.5)
    # 🛑 PAUSE POINT
    screen.check_abort()
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Set LD HLR to OUT position .\n",
        RESOURCES_DIR /"LD HLR.png","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    screen.log_signal.emit("successfully Set LD HLR to OUT position", False)
    screen.log_signal.emit("Disconnect the Audio analyser input and oscilloscope to the MIC OUT COM 5 Connector J11", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.send_with_retry(STM32RelayController.set_j11_off):
        screen.log_signal.emit("MIC OUT COM 5 Connector J11 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect MIC OUT COM 5 Connector J11", True)

    screen.log_signal.emit("==========Successfully Completed USER TRANSMIT AUDIO TX OUTPUT LEVEL test===========", False)
    time.sleep(0.5)