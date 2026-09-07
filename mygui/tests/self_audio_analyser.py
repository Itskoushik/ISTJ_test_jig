import time
from core.paths import RESOURCES_DIR
from devices.apx_analyzer import generator_control,read_apx_meter,configure_apx
from core.excel_logger import write_self_test_excel
from core.stm32_commands import STM32RelayController
from core.tuning_workflow import set_popup_title
from core.oscilloscope_helper import set_ch1_ch2_scale_10v
def run(screen):
    set_ch1_ch2_scale_10v(screen)
    set_popup_title("Self Audio Analyser Test")
    screen.log_signal.emit("==========COMMENCING AUDIO ANALYSER SELF TEST==========", False)
    
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
    write_self_test_excel("F12", "CONNECTED" if j23_ok else "FAIL")

    screen.log_signal.emit("Connecting Audio analyser Output to S12", False)
    s12_ok = STM32RelayController.send_with_retry(STM32RelayController.set_s12_on)
    if s12_ok:
        screen.log_signal.emit("S12 successfully set to UP position", False)
        time.sleep(0.5)
    else:
        screen.log_signal.emit("ERROR: Failed to set S12 to UP position", True)
    write_self_test_excel("F9", "CONNECTED" if s12_ok else "FAIL")
    write_self_test_excel("G9", "750.00 µVrms")          # value set (uVrms)
    time.sleep(0.5)
    generator_control(screen, level="750.00 uVrms", frequency=1000, gen_scale=1.0)
    data = read_apx_meter(screen, min_v=745, max_v=755, max_thd=10.0, unit="uvrms")
    if data:
        write_self_test_excel("H9", data["observation"])
        write_self_test_excel("I9", data["result"])
    write_self_test_excel("G11", "100.00 mVrms")          # value set (uVrms) 
    time.sleep(0.5)   
    generator_control(screen, level="100.00 mVrms", frequency=200, gen_scale=1.0)
    data = read_apx_meter(screen, min_v=95, max_v=105, max_thd=10.0, unit="mvrms")
    if data:
        write_self_test_excel("H11", data["observation"])
        write_self_test_excel("I11", data["result"])
    write_self_test_excel("G13", "1.0 Vrms")  
    time.sleep(0.5)  
    generator_control(screen, level="1.0 Vrms", frequency=3500, gen_scale=1.0)
    data = read_apx_meter(screen, min_v=0.95, max_v=1.05, max_thd=10.0, unit="vrms")
    if data:
        write_self_test_excel("H13", data["observation"])
        write_self_test_excel("I13", data["result"])

    time.sleep(0.5)
    screen.log_signal.emit("==========SUCCESSFULLY COMPLETED AUDIO ANALYSER SELF TEST==========", False)