import time
from core.paths import RESOURCES_DIR
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController    

def run_norm(screen):
    screen.log_signal.emit("==========Commencing RX SELECTION AND MUTING Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Connect the Audio analyser gen output to the RX AUD Connector J57", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j57_on():
        screen.log_signal.emit("RX AUD Connector J57 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect RX AUD Connector J57", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set the audio analyser gen output to 5.5 Vrms @1 KHz
    
    screen.log_signal.emit("Connect the Audio analyser input and the oscilloscope to the PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j29_on():
        screen.log_signal.emit("PH Connector J29 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect PH Connector J29", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting COM 1 switch S1 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s01_on():
        screen.log_signal.emit("COM 1 switch S1 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 1 switch S1 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 1 fully cw .\n",
        RESOURCES_DIR /"vuhf1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 1 switch S1 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s01_off():
        screen.log_signal.emit("COM 1 switch S1 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 1 switch S1 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com2
    screen.log_signal.emit("Setting COM 2 switch S2 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s02_on():
        screen.log_signal.emit("COM 2 switch S2 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 2 switch S2 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 2 fully cw .\n",
        RESOURCES_DIR /"vuhf2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 2 switch S2 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s02_off():
        screen.log_signal.emit("COM 2 switch S2 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 2 switch S2 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com3
    
    screen.log_signal.emit("Setting COM 3 switch S3 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s03_on():
        screen.log_signal.emit("COM 3 switch S3 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 3 switch S3 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate HF fully cw .\n",
        RESOURCES_DIR /"hf.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 3 switch S3 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s03_off():
        screen.log_signal.emit("COM 3 switch S3 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 3 switch S3 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com4
    
    screen.log_signal.emit("Setting COM 4 switch S4 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s04_on():
        screen.log_signal.emit("COM 4 switch S4 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 4 switch S4 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 1 fully cw .\n",
        RESOURCES_DIR /"spare1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 4 switch S4 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s04_off():
        screen.log_signal.emit("COM 4 switch S4 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 4 switch S4 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com5 s05
    
    screen.log_signal.emit("Setting COM 5 switch S5 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s05_on():
        screen.log_signal.emit("COM 5 switch S5 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 5 switch S5 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 2 fully cw .\n",
        RESOURCES_DIR /"spare2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 5 switch S5 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s05_off():
        screen.log_signal.emit("COM 5 switch S5 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 5 switch S5 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #NAV 1 S7
    
    screen.log_signal.emit("Setting NAV 1 switch S7 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s07_on():
        screen.log_signal.emit("NAV 1 switch S7 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 1 switch S7 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ADF fully cw .\n",
        RESOURCES_DIR /"adf.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 1 switch S7 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s07_off():
        screen.log_signal.emit("NAV 1 switch S7 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 1 switch S7 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #nav 2 s8
    
    screen.log_signal.emit("Setting NAV 2 switch S8 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s08_on():
        screen.log_signal.emit("NAV 2 switch S8 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 2 switch S8 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SONIC fully cw .\n",
        RESOURCES_DIR /"sonic_knob.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 2 switch S8 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s08_off():
        screen.log_signal.emit("NAV 2 switch S8 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 2 switch S8 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #NAV 3 s9
    
    screen.log_signal.emit("Setting NAV 3 switch S9 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s09_on():
        screen.log_signal.emit("NAV 3 switch S9 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 3 switch S9 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ESM fully cw .\n",
        RESOURCES_DIR /"esm.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 3 switch S9 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s09_off():
        screen.log_signal.emit("NAV 3 switch S9 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 3 switch S9 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #Nav 4 s10
    
    
    screen.log_signal.emit("Setting NAV 4 switch S10 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s10_on():
        screen.log_signal.emit("NAV 4 switch S10 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 4 switch S10 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 3 fully cw .\n",
        RESOURCES_DIR /"spare3.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 4 switch S10 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s10_off():
        screen.log_signal.emit("NAV 4 switch S10 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 4 switch S10 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #nav 5 s11
    
    screen.log_signal.emit("Setting NAV 5 switch S11 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s11_on():
        screen.log_signal.emit("NAV 5 switch S11 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 5 switch S11 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 4 fully cw .\n",
        RESOURCES_DIR /"spare4.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 5 switch S11 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s11_off():
        screen.log_signal.emit("NAV 5 switch S11 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 5 switch S11 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #nav6 s12
    
    screen.log_signal.emit("Setting NAV 6 switch S12 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s12_on():
        screen.log_signal.emit("NAV 6 switch S12 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 6 switch S12 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 5 fully cw .\n",
        RESOURCES_DIR /"spare5.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 6 switch S12 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s12_off():
        screen.log_signal.emit("NAV 6 switch S12 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 6 switch S12 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser gen output from the RX AUD Connector J57 ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j57_off():
        screen.log_signal.emit("RX AUD Connector J57 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect RX AUD Connector J57", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and the oscilloscope from the PH Connector J29 ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j29_off():
        screen.log_signal.emit("PH Connector J29 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PH Connector J29", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    
    screen.log_signal.emit("==========Successfully Completed RX SELECTION AND MUTING Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    
def run_stby(screen):
    screen.log_signal.emit("==========Commencing RX SELECTION AND MUTING Test==========", False)
    QApplication.processEvents()
    time.sleep(0.5)
    screen.log_signal.emit("Connect the Audio analyser gen output to the RX AUD Connector J57", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j57_on():
        screen.log_signal.emit("RX AUD Connector J57 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect RX AUD Connector J57", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set the audio analyser gen output to 5.5 Vrms @1 KHz
    
    screen.log_signal.emit("Connect the Audio analyser input and the oscilloscope to the PH Connector J29", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j29_on():
        screen.log_signal.emit("PH Connector J29 successfully  Connected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect PH Connector J29", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting COM 1 switch S1 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s01_on():
        screen.log_signal.emit("COM 1 switch S1 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 1 switch S1 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 1 fully cw .\n",
        RESOURCES_DIR /"vuhf1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 1 switch S1 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s01_off():
        screen.log_signal.emit("COM 1 switch S1 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 1 switch S1 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com2
    screen.log_signal.emit("Setting COM 2 switch S2 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s02_on():
        screen.log_signal.emit("COM 2 switch S2 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 2 switch S2 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate V/UHF 2 fully cw .\n",
        RESOURCES_DIR /"vuhf2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 2 switch S2 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s02_off():
        screen.log_signal.emit("COM 2 switch S2 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 2 switch S2 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com3
    
    screen.log_signal.emit("Setting COM 3 switch S3 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s03_on():
        screen.log_signal.emit("COM 3 switch S3 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 3 switch S3 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate HF fully cw .\n",
        RESOURCES_DIR /"hf.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 3 switch S3 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s03_off():
        screen.log_signal.emit("COM 3 switch S3 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 3 switch S3 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com4
    
    screen.log_signal.emit("Setting COM 4 switch S4 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s04_on():
        screen.log_signal.emit("COM 4 switch S4 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 4 switch S4 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 1 fully cw .\n",
        RESOURCES_DIR /"spare1.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 4 switch S4 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s04_off():
        screen.log_signal.emit("COM 4 switch S4 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 4 switch S4 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #com5 s05
    
    screen.log_signal.emit("Setting COM 5 switch S5 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s05_on():
        screen.log_signal.emit("COM 5 switch S5 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 5 switch S5 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 2 fully cw .\n",
        RESOURCES_DIR /"spare2.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting COM 5 switch S5 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s05_off():
        screen.log_signal.emit("COM 5 switch S5 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set COM 5 switch S5 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #NAV 1 S7
    
    screen.log_signal.emit("Setting NAV 1 switch S7 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s07_on():
        screen.log_signal.emit("NAV 1 switch S7 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 1 switch S7 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ADF fully cw .\n",
        RESOURCES_DIR /"adf.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 1 switch S7 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s07_off():
        screen.log_signal.emit("NAV 1 switch S7 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 1 switch S7 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    #nav 2 s8
    
    screen.log_signal.emit("Setting NAV 2 switch S8 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s08_on():
        screen.log_signal.emit("NAV 2 switch S8 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 2 switch S8 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SONIC fully cw .\n",
        RESOURCES_DIR /"sonic_knob.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 2 switch S8 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s08_off():
        screen.log_signal.emit("NAV 2 switch S8 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 2 switch S8 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #NAV 3 s9
    
    screen.log_signal.emit("Setting NAV 3 switch S9 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s09_on():
        screen.log_signal.emit("NAV 3 switch S9 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 3 switch S9 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate ESM fully cw .\n",
        RESOURCES_DIR /"esm.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 3 switch S9 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s09_off():
        screen.log_signal.emit("NAV 3 switch S9 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 3 switch S9 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #Nav 4 s10
    
    
    screen.log_signal.emit("Setting NAV 4 switch S10 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s10_on():
        screen.log_signal.emit("NAV 4 switch S10 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 4 switch S10 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 3 fully cw .\n",
        RESOURCES_DIR /"spare3.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 4 switch S10 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s10_off():
        screen.log_signal.emit("NAV 4 switch S10 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 4 switch S10 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #nav 5 s11
    
    screen.log_signal.emit("Setting NAV 5 switch S11 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s11_on():
        screen.log_signal.emit("NAV 5 switch S11 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 5 switch S11 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 4 fully cw .\n",
        RESOURCES_DIR /"spare4.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 5 switch S11 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s11_off():
        screen.log_signal.emit("NAV 5 switch S11 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 5 switch S11 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #nav6 s12
    
    screen.log_signal.emit("Setting NAV 6 switch S12 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s12_on():
        screen.log_signal.emit("NAV 6 switch S12 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 6 switch S12 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Rotate SPARE 5 fully cw .\n",
        RESOURCES_DIR /"spare5.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    
    #the audio analyser should read 11 +- 1.1 Vrms with <10% THD+N
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Press and Release SONIC  .\n",
        RESOURCES_DIR /"sonic.jpeg","ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(0.5)
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to up position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_on():
        screen.log_signal.emit("MUTE switch S34 successfully set to up position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to up position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #the audio analyser should read <11 mVrms.
    
    screen.log_signal.emit("Setting MUTE switch switch S34 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s34_off():
        screen.log_signal.emit("MUTE switch S34 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set MUTE switch S34 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    #set audio analyser gen output to 5.5Vrms @200 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    #set audio analyser gen output to 5.5Vrms @3500 Hz
    #the audio analyser should read >7.7 Vrms with <10%THD+N
    
    screen.log_signal.emit("Setting NAV 6 switch S12 to down position", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_s12_off():
        screen.log_signal.emit("NAV 6 switch S12 successfully set to down position", False)
    else:
        screen.log_signal.emit("ERROR: Failed to set NAV 6 switch S12 to down position", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser gen output from the RX AUD Connector J57 ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j57_off():
        screen.log_signal.emit("RX AUD Connector J57 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect RX AUD Connector J57", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    screen.log_signal.emit("Disconnect the Audio analyser input and the oscilloscope from the PH Connector J29 ", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j29_off():
        screen.log_signal.emit("PH Connector J29 successfully  Disconnected", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect PH Connector J29", True)
        return

    QApplication.processEvents()
    time.sleep(0.5)
    
    
    
    screen.log_signal.emit("==========Successfully Completed RX SELECTION AND MUTING Test===========", False)
    QApplication.processEvents()
    time.sleep(0.5)