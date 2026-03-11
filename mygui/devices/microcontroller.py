import serial
import serial.tools.list_ports
import time
from typing import Callable


def discover_microcontroller(log: Callable[[str, bool], None]) -> bool:
    """
    Discover and verify microcontroller connection via serial/UART.
    Uses CRC-8 validation from hellllo.py.
    Executes in worker thread (non-blocking UI).
    Pure device logic (NO PyQt, NO worker state).
    """

    try:
        # CRC-8 implementation (from hellllo.py)
        def crc8(data):
            crc = 0x00
            poly = 0x07
            for byte in data:
                crc ^= byte
                for _ in range(8):
                    if crc & 0x80:
                        crc = ((crc << 1) ^ poly) & 0xFF
                    else:
                        crc = (crc << 1) & 0xFF
            return crc

        # Scan for STM32 ports
        ports = list(serial.tools.list_ports.comports())

        if not ports:
            log("No serial ports found. Microcontroller not detected.", True)
            return False

        # Filter for STM32 devices
        stm32_ports = []
        for port in ports:
            if any(k in port.description for k in ["Bluetooth", "Wireless", "Intel", "Modem"]):
                continue

            if (
                port.vid == 0x0483
                or "STM32" in port.description
                or "ST-Link" in port.description
                or "USB Serial" in port.description
            ):
                stm32_ports.append(port.device)

        if not stm32_ports:
            log("No STM32 device detected on serial ports.", True)
            return False

        # Attempt connection to each STM32 port
        for port in stm32_ports:
            try:
                ser = serial.Serial(port, 115200, timeout=2)
                log(f"Attempting connection to {port}...", False)

                # ===== FORCE DESYNC BEFORE SYNC (CRITICAL FIX) =====
                ser.reset_input_buffer()
                ser.reset_output_buffer()

                log(f"Port {port}: Sending forced desync before sync...", False)

                desync_frame = bytearray([0x02, 0x35, 0x02, 0xFF, 0xE0, 0x56, 0x03, 0x0D])
                ser.write(desync_frame)
                time.sleep(0.3)

                # Read & ignore desync response
                _ = ser.read(8)

                # Send Ready command
                frame = bytearray([0x02, 0x35, 0x02, 0xFF, 0x00, 0x98, 0x03, 0x0D])
                ser.write(frame)
                time.sleep(0.5)

                # Read response
                response = ser.read(8)

                if len(response) == 8:
                    start, slave, length, command, state, recv_crc, end, eof = response

                    # Validate frame format
                    if (
                        start == 0x02
                        and slave == 0x35
                        and length == 0x02
                        and end == 0x03
                        and eof == 0x0D
                    ):
                        # Validate CRC
                        crc_data = [start, slave, length, command, state, end, eof]
                        calc_crc = crc8(crc_data)

                        if calc_crc == recv_crc:
                            # Check handshake response
                            if command == 0xFF and state == 0x01:
                                log(f"Microcontroller found at {port} ✓", False)
                                log("  Protocol: STM32 UART (115200 baud)", False)
                                log("  Handshake: Successful", False)
                                ser.close()
                                return True

                            elif command == 0xFF and state == 0xFF:
                                log(
                                    f"Port {port}: MCU already synced. Performing desync → resync...",
                                    True
                                )

                                # ---------------- DESYNC ----------------
                                ser.write(desync_frame)
                                time.sleep(0.4)

                                desync_resp = ser.read(8)
                                if len(desync_resp) != 8:
                                    log(f"Port {port}: Desync response invalid", True)
                                    continue

                                ds, dsl, dl, dc, dst, dcrc, de, deof = desync_resp
                                if not (
                                    ds == 0x02
                                    and dsl == 0x35
                                    and dl == 0x02
                                    and dc == 0xFF
                                    and dst == 0xE1
                                    and de == 0x03
                                    and deof == 0x0D
                                ):
                                    log(f"Port {port}: Desync failed", True)
                                    continue

                                log(
                                    f"Port {port}: Desync successful. Re-attempting sync...",
                                    False
                                )

                                # ---------------- RESYNC ----------------
                                ser.write(frame)
                                time.sleep(0.4)

                                response = ser.read(8)
                                if len(response) != 8:
                                    log(f"Port {port}: No response after resync", True)
                                    continue

                                s, sl, l, c, st, crc_r, e, eof = response
                                crc_calc = crc8([s, sl, l, c, st, e, eof])

                                if (
                                    s == 0x02
                                    and sl == 0x35
                                    and l == 0x02
                                    and c == 0xFF
                                    and st == 0x01
                                    and crc_calc == crc_r
                                ):
                                    log(
                                        f"Microcontroller re-synced successfully at {port} ✓",
                                        False
                                    )
                                    ser.close()
                                    return True

                            elif command == 0xFF and state == 0xFE:
                                log(f"Port {port}: Data Error from controller", True)

                        else:
                            log(f"Port {port}: CRC validation failed", True)
                    else:
                        log(f"Port {port}: Invalid frame format", True)

                ser.close()

            except (serial.SerialException, serial.PortNotOpenError):
                continue
            except Exception:
                try:
                    ser.close()
                except:
                    pass
                continue

        # No valid microcontroller found
        log("Microcontroller not found or handshake failed on available ports.", True)
        return False

    except ImportError:
        log("pyserial library not installed. Cannot detect microcontroller.", True)
        return False

    except Exception as e:
        log(f"Microcontroller discovery error: {str(e)}", True)
        return False
