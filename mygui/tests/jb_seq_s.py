from tests import (
    power_supply,
    user_override_cvr_output,
    user_override_ics_vol,
    user_primary_ics_sonic,
    user_primary_ics_vol,
    user_primary_ics_control,
    user_primary_tx_ptt,
    user_private_ics_vol,
    user_transmit_tx_output,
    user_recieve_rx_select,
    ground_crew_ics_volume,
    ground_crew_ics_limiter,
    ground_crew_private,
    ground_crew_override,
    ground_crew_cvr_output
)

import time
from PyQt5.QtWidgets import QApplication
from core.stm32_commands import STM32RelayController
from core.paths import RESOURCES_DIR

from core.excel_logger import reset_column_offset,next_column,reset_row_offset,next_row
def should_run(screen, parent, sub=None):

    for t in screen.selected_tests:

        if "::" in t:
            p, s = t.split("::")
        else:
            p = t
            s = None

        if p.strip() == parent and (sub is None or s == sub):
            return True

    return False
def run_norm(screen):
    reset_column_offset()
    reset_row_offset()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J103 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "POWER SUPPLY TEST",None):
        power_supply.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    time.sleep(1) 
    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
       
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
         
    #changes for each J104,105,106,107 
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J18", False)
      # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j18_on():
        screen.log_signal.emit("J18 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J18 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_norm(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J18", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j18_off():
        screen.log_signal.emit("J18 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J18 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
   
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
   
    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
   
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect J63 Connector from J103 Connector using test cable.\n",
        None,"ok",None
    )
    
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    next_column()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J104 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()   
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
         
    #changes for each 105,106,107 
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J19", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j19_on():
        screen.log_signal.emit("J19 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J19 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_norm(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J19", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j19_off():
        screen.log_signal.emit("J19 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J19 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    reset_column_offset() 
    next_row(10)
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    

    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect J63 Connector from J104 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    next_column()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J105 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()   
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
         
    #changes for each 106,107 
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J20", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j20_on():
        screen.log_signal.emit("J20 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J20 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_norm(screen)
        
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J20", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j20_off():
        screen.log_signal.emit("J20 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J20 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()

    reset_column_offset() 
    next_row(10) 
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect J63 Connector from J105 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    next_column()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J106 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()   
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
         
    #changes for each 107 
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J21", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j21_on():
        screen.log_signal.emit("J21 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J21 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_norm(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J21", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j21_off():
        screen.log_signal.emit("J21 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J21 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    reset_column_offset() 
    next_row(10) 
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

        # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect J63 Connector from J106 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    next_column()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J107 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()   
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
 
    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
         
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J22", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j22_on():
        screen.log_signal.emit("J22 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J22 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_norm(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J22", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j22_off():
        screen.log_signal.emit("J22 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J22 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    reset_column_offset() 
    next_row(10) 
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "GROUND CREW PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        ground_crew_ics_volume.run_norm(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "GROUND CREW PRIMARY INTERCOM CHANNEL TEST", "ICS LIMITER TEST"):
        ground_crew_ics_limiter.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "GROUND CREW PRIVATE INTERCOM CHANNEL TEST", None):
        ground_crew_private.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "GROUND CREW OVERRIDE INTERCOM CHANNEL TEST", None):
        ground_crew_override.run_norm(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "GROUND CREW CVR OUTPUT LEVEL TEST", None):
        ground_crew_cvr_output.run_norm(screen)
    time.sleep(1)

    
    
    
    
def run_stby(screen):
    # 🛑 PAUSE POINT
    
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J103 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
 
    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
         
    #changes for each J104,105,106,107 
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J18", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j18_on():
        screen.log_signal.emit("J18 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J18 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_stby(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J18", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j18_off():
        screen.log_signal.emit("J18 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J18 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    reset_column_offset() 
    next_row(10) 
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect J63 Connector from J103 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    next_column()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J104 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()   
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
 
    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
         
    #changes for each 105,106,107 
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J19", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j19_on():
        screen.log_signal.emit("J19 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J19 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_stby(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J19", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j19_off():
        screen.log_signal.emit("J19 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J19 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    
    reset_column_offset() 
    next_row(10)
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
        
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect J63 Connector from J104 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    next_column()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J105 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()   
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_stby(screen)
    time.sleep(1)
    screen.check_abort()

    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
         
    #changes for each 106,107 
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J20", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j20_on():
        screen.log_signal.emit("J20 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J20 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_stby(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J20", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j20_off():
        screen.log_signal.emit("J20 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J20 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    
    reset_column_offset() 
    next_row(10) 
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
   
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect J63 Connector from J105 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    next_column()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J106 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()   
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
   
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
         
    #changes for each 107 
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J21", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j21_on():
        screen.log_signal.emit("J21 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J21 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_stby(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J21", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j21_off():
        screen.log_signal.emit("J21 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J21 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    
    reset_column_offset() 
    next_row(10) 
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
        # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Disconnect J63 Connector from J106 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()
    next_column()
    # 🛑 PAUSE POINT
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "⚠ Operator Action Required",
        "• Connect J63 Connector to J107 Connector using test cable.\n",
        None,"ok",None
    )
    
    # ⏸ WAIT until operator clicks OK
    screen.operator_event.wait()
    time.sleep(1)
    screen.check_abort()   
    
    if should_run(screen, "POWER SUPPLY TEST", None):
        power_supply.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_primary_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME CONTROL TEST"):
        user_primary_ics_control.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "SONIC MUTE TEST"):
        user_primary_ics_sonic.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    if should_run(screen, "USER PRIMARY INTERCOM CHANNEL TEST", "TX PTT TEST"):
        user_primary_tx_ptt.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER PRIVATE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_private_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
     
    
    if should_run(screen, "USER OVERRIDE INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        user_override_ics_vol.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
         
    screen.log_signal.emit("Connecting the audio analyser input to CVR Connector J22", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j22_on():
        screen.log_signal.emit("J22 successfully Connected to CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Connect J22 to CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER CVR AUDIO TEST", "CVR OUTPUT LEVEL TEST"):
        user_override_cvr_output.run_stby(screen)
    screen.log_signal.emit("Disconnecting the audio analyser input to CVR Connector J22", False)
    QApplication.processEvents()   # 🔑 FORCE UI UPDATE

    if STM32RelayController.set_j22_off():
        screen.log_signal.emit("J22 successfully Disconnected from CVR Connector", False)
    else:
        screen.log_signal.emit("ERROR: Failed to Disconnect J22 from CVR Connector", True)
        return

    QApplication.processEvents()
    time.sleep(1)
    screen.check_abort()
    
    
    reset_column_offset() 
    next_row(10) 
    if should_run(screen, "USER TRANSMIT AUDIO TEST", "TX OUTPUT LEVEL TEST"):
        user_transmit_tx_output.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "USER RECEIVE AUDIO TEST", "RX SELECTION AND MUTING TEST"):
        user_recieve_rx_select.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "GROUND CREW PRIMARY INTERCOM CHANNEL TEST", "ICS VOLUME TEST"):
        ground_crew_ics_volume.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    ground_crew_ics_limiter.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
   
    if should_run(screen, "GROUND CREW PRIVATE INTERCOM CHANNEL TEST", None):
        ground_crew_private.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "GROUND CREW OVERRIDE INTERCOM CHANNEL TEST", None):
        ground_crew_override.run_stby(screen)
    time.sleep(1)
    screen.check_abort()
    
    if should_run(screen, "GROUND CREW CVR OUTPUT LEVEL TEST", None):
        ground_crew_cvr_output.run_stby(screen)
    time.sleep(1)
    
