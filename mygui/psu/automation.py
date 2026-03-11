import time
def worker_channel_1(screen):
    """
    CHANNEL 1
    Voltage: 28V
    Current: 1.3A
    Output ON until task completes
    """

    screen.psu_send_command("*CLS")
    screen.psu_send_command("INST:NSEL 1")
    time.sleep(0.1)

    screen.psu_send_command("SOUR1:VOLT 28.0")
    screen.psu_send_command("SOUR1:CURR 1.3")

    screen.psu_send_command("OUTP ON")
    time.sleep(0.5)   # ⏳ let PSU settle
    screen.start_voltage_monitoring()
    
    screen.current_channel = 1
    screen.log_signal.emit("Ch1 OUTPUT ON (28V, 1.3A)", False)
    screen.operator_event.clear()
    screen.show_popup_signal.emit(
        "Channel 1 Active",
        "Channel 1 is ON at 28V.\nClick OK to proceed.",
        None,"ok",None
    )
    screen.operator_event.wait()
    screen.log_signal.emit("Operator confirmed Channel 1", False)
    time.sleep(15)

    


    # -------------------------------------------------
    # ADD YOUR LOGIC HERE
    # Output remains ON until this logic completes
    

    screen.psu_send_command("OUTP OFF")
    screen.stop_voltage_monitoring()

    screen.log_signal.emit("Ch1 OUTPUT OFF", False)


def worker_ch2_28v(screen):
    screen.psu_send_command("*CLS")
    screen.psu_send_command("INST:NSEL 2")
    time.sleep(0.1)

    screen.psu_send_command("SOUR2:VOLT 28.0")
    screen.psu_send_command("SOUR2:CURR 1.3")

    screen.psu_send_command("OUTP ON")
    time.sleep(0.5)   # ⏳ let PSU settle
    screen.start_voltage_monitoring()
    screen.current_channel = 2
    screen.log_signal.emit("Ch2 OUTPUT ON (28V, 1.3A)", False)
    
    # ADD YOUR LOGIC HERE
    time.sleep(15)
    screen.psu_send_command("OUTP OFF")
    screen.stop_voltage_monitoring()
    screen.log_signal.emit("Ch2 OUTPUT OFF (28V step complete)", False)

def worker_ch2_12v(screen):
    screen.psu_send_command("*CLS")
    screen.psu_send_command("INST:NSEL 2")
    time.sleep(0.1)

    screen.psu_send_command("SOUR2:VOLT 12.0")
    screen.psu_send_command("SOUR2:CURR 1.3")

    screen.psu_send_command("OUTP ON")
    time.sleep(0.5)   # ⏳ let PSU settle
    screen.start_voltage_monitoring()
    screen.current_channel = 2
    screen.log_signal.emit("Ch2 OUTPUT ON (12V, 1.3A)", False)

    # ADD YOUR LOGIC HERE

    screen.psu_send_command("OUTP OFF")
    screen.stop_voltage_monitoring()
    screen.log_signal.emit("Ch2 OUTPUT OFF (16V step complete)", False)

def worker_ch2_5v(screen):
    screen.psu_send_command("*CLS")
    screen.psu_send_command("INST:NSEL 2")
    time.sleep(0.1)

    screen.psu_send_command("SOUR2:VOLT 5.0")
    screen.psu_send_command("SOUR2:CURR 1.3")

    screen.psu_send_command("OUTP ON")
    time.sleep(0.5)   # ⏳ let PSU settle
    screen.start_voltage_monitoring()
    screen.current_channel = 2
    screen.log_signal.emit("Ch2 OUTPUT ON (5V, 1.3A)", False)

    # ADD YOUR LOGIC HERE

    screen.psu_send_command("OUTP OFF")
    screen.stop_voltage_monitoring()
    screen.log_signal.emit("Ch2 OUTPUT OFF (8V step complete)", False)
    



def run_channel_sequence(screen, channel: int):
    print("\n==============================")
    print(f"ENTER run_channel_sequence(channel={channel})")
    print("==============================")

    screen.debug_active_channel("START")

    screen.psu_send_command("*CLS")
    screen.psu_send_command(f"INST:NSEL {channel}")
    time.sleep(0.1)

    screen.debug_active_channel("AFTER INST:NSEL")

    # 🔴 SET VOLTAGE / CURRENT
    screen.psu_send_command(f"SOUR{channel}:VOLT 28.0")
    screen.psu_send_command(f"SOUR{channel}:CURR 1.35")


    screen.debug_active_channel("AFTER SET V/I")

    # 🔴 OUTPUT ON
    screen.psu_send_command("OUTP ON")
    time.sleep(0.5)   # ⏳ let PSU settle
    screen.start_voltage_monitoring()
    time.sleep(0.2)

    screen.debug_active_channel("AFTER OUTP ON")

    out_state = screen.psu_send_command("OUTP?")
    print(f"CHANNEL {channel} OUTPUT STATE AFTER ON:", out_state)

    screen.current_channel = channel
    screen.log_signal.emit(f"Ch{channel} OUTPUT ON", False)


    screen.debug_active_channel("BEFORE OUTP OFF")

    screen.psu_send_command("*CLS")
    screen.psu_send_command(f"INST:NSEL {channel}")
    screen.psu_send_command("OUTP OFF")
    screen.stop_voltage_monitoring()

    screen.debug_active_channel("AFTER OUTP OFF")

    screen.log_signal.emit(f"Ch{channel} OUTPUT OFF", False)