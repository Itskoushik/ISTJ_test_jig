import time
from core.paths import RESOURCES_DIR
from devices.apx_analyzer import generator_control,configure_apx
from core.excel_logger import write_self_test_excel
from core.stm32_commands import STM32RelayController
from core.tuning_workflow import set_popup_title
from devices.oscilloscope_connection import OscilloscopeConnection
from core.oscilloscope_helper import read_osc_meter,autoset_oscilloscope,set_ch1_ch2_scale_10v
def run(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("Self Oscilloscope Test")
    if not getattr(screen, "osc_conn", None) or not screen.osc_conn.is_connected():
        screen.log_signal.emit("OSC: Connecting to oscilloscope...", False)
        conn = OscilloscopeConnection()
        if conn.discover_and_connect():
            screen.osc_conn = conn
            screen.log_signal.emit(
                f"OSC: Connected to {conn.identification.manufacturer} "
                f"{conn.identification.model} ✓", False
            )
        else:
            screen.log_signal.emit("⚠ OSC: Could not connect — test will be incomplete", True)
    # ↑ END OF ADD
    
    screen.log_signal.emit("==========COMMENCING OSCILLOSCOPE SELF TEST==========", False)
    
    screen.operator_signal.emit(
        "⚠ Operator Action Required",
        "• Please ensure that the ISTJ Self test board is properly connected.",
        str(RESOURCES_DIR / "self_test.jpeg")   # empty string "" if no image
    )
    screen._operator_event.wait()   # blocks screen thread until operator clicks OK
    time.sleep(0.5)
    screen.log_signal.emit("Configuring APX analyzer for Self test...", False)
    configure_apx(screen)
    time.sleep(0.5)
    screen.log_signal.emit("Connecting Audio analyser input to J23 ", False)
    j23_ok = STM32RelayController.send_with_retry(STM32RelayController.set_j23_on)
    if j23_ok:
        screen.log_signal.emit("J23 successfully connected", False)
        time.sleep(0.5)
    else:
        screen.log_signal.emit("ERROR: Failed to connect J23", True)
    write_self_test_excel("F22", "CONNECTED" if j23_ok else "FAILED")

    screen.log_signal.emit("Connecting Audio analyser Output to S12 ", False)
    s12_ok = STM32RelayController.send_with_retry(STM32RelayController.set_s12_on)
    if s12_ok:
        screen.log_signal.emit("S12 successfully set to UP position", False)
        time.sleep(0.5)
    else:
        screen.log_signal.emit("ERROR: Failed to set S12 to UP position", True)
    write_self_test_excel("F19", "CONNECTED" if s12_ok else "FAILED")
    write_self_test_excel("G19", "5.00 Vrms")          # value set (uVrms)
    time.sleep(0.5)
    generator_control(screen, level="5.00 Vrms", frequency=1000, gen_scale=1.0,state="ON")
    time.sleep(1)
    autoset_oscilloscope(screen)
    time.sleep(5)
    osc_data = read_osc_meter(screen, min_v=4.50, max_v=5.50)   
    if osc_data:
        write_self_test_excel("H19", osc_data["observation"])
        write_self_test_excel("I19", osc_data["result"])
    else:
        write_self_test_excel("H19", "ERROR")
        write_self_test_excel("I19", "FAIL")
    write_self_test_excel("G21", "10.00 Vrms")  
    time.sleep(0.5)  
    generator_control(screen, level="10.00 Vrms", frequency=200, gen_scale=1.0,state="ON")
    time.sleep(1)
    autoset_oscilloscope(screen)
    time.sleep(5)
    osc_data = read_osc_meter(screen, min_v=9.50, max_v=10.50)   
    if osc_data:
        write_self_test_excel("H21", osc_data["observation"])
        write_self_test_excel("I21", osc_data["result"])
    else:
        write_self_test_excel("H21", "ERROR")
        write_self_test_excel("I21", "FAIL")
    write_self_test_excel("G23", "12.00 Vrms")
    time.sleep(0.5)    
    generator_control(screen, level="12.00 Vrms", frequency=3500, gen_scale=1.0,state="ON")
    time.sleep(1)
    autoset_oscilloscope(screen)
    time.sleep(5)
    osc_data = read_osc_meter(screen, min_v=11.50, max_v=12.50)   
    if osc_data:
        write_self_test_excel("H23", osc_data["observation"])
        write_self_test_excel("I23", osc_data["result"])
    else:
        write_self_test_excel("H23", "ERROR")
        write_self_test_excel("I23", "FAIL")
    
    generator_control(screen,state="OFF")    

    screen.log_signal.emit("==========SUCCESSFULLY COMPLETED OSCILLOSCOPE SELF TEST==========", False)
