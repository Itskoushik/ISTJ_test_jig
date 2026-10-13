import time
import serial
import serial.tools.list_ports
from core.excel_logger import write_self_test_excel

SERIAL_CONFIG = {
    "baudrate": 9600,
    "bytesize": serial.EIGHTBITS,
    "stopbits": serial.STOPBITS_ONE,
    "parity":   serial.PARITY_NONE,
    "xonxoff":  False,
    "rtscts":   False,
    "dsrdtr":   False,
    "timeout":  1,
}

MAX_TX_LEN = 8
CELL_MAP = {"tx": "D14", "rx": "F14", "result": "H14"}
SHEET_NAME = "Sheet1"

def available_ports():
    return [p.device for p in serial.tools.list_ports.comports()]


def open_connection(port: str) -> serial.Serial:
    return serial.Serial(port=port, **SERIAL_CONFIG)


def send_and_receive(ser: serial.Serial, tx_text: str, read_bytes: int = 256, read_delay: float = 0.2):
    if len(tx_text) > MAX_TX_LEN:
        raise ValueError(f"TX data exceeds {MAX_TX_LEN} characters (got {len(tx_text)}).")

    ser.write(tx_text.encode("ascii", errors="ignore"))
    time.sleep(read_delay)
    rx_bytes = ser.read(read_bytes)
    rx_text = rx_bytes.decode("ascii", errors="replace") if rx_bytes else ""

    result = "PASS" if rx_text == tx_text else "FAIL"

    write_self_test_excel(CELL_MAP["tx"], tx_text, sheet_name=SHEET_NAME)
    write_self_test_excel(CELL_MAP["rx"], rx_text if rx_text else "(no response)", sheet_name=SHEET_NAME)
    write_self_test_excel(CELL_MAP["result"], result, sheet_name=SHEET_NAME)

    return tx_text, rx_text, result


def close_connection(ser: serial.Serial):
    try:
        if ser and ser.is_open:
            ser.close()
    except Exception:
        pass