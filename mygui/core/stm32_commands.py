import time
import serial
import serial.tools.list_ports


class STM32RelayController:
    """
    Handles STM32 relay commands (S23, S31, Jxx, etc.)
    Uses CRC-8 (poly 0x07) – SAME logic as disconnect handshake
    """

    BAUDRATE = 115200
    TIMEOUT = 2

    # ======================
    # CRC-8
    # ======================
    @staticmethod
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

    # ======================
    # GENERIC SEND + VALIDATE
    # ======================
    @classmethod
    def send_and_validate(cls, cmd_byte, tx_state, expected_rx_state=None):
        if expected_rx_state is None:
            expected_rx_state = tx_state

        ports = list(serial.tools.list_ports.comports())

        # ✅ Filter only STM32 related ports (prevents freezing)
        stm32_ports = []
        for port in ports:
            desc = (port.description or "")
            if any(k in desc for k in ["Bluetooth", "Wireless", "Intel", "Modem"]):
                continue

            if (port.vid == 0x0483 or
                "STM32" in desc or
                "ST-Link" in desc or
                "USB Serial" in desc):
                stm32_ports.append(port)

        ports = stm32_ports

        tx = [0x02, 0x35, 0x02, cmd_byte, tx_state, 0x03, 0x0D]
        tx.insert(5, cls.crc8(tx))

        for port in ports:
            try:
                ser = serial.Serial(port.device, cls.BAUDRATE, timeout=cls.TIMEOUT)

                ser.reset_input_buffer()
                ser.write(bytearray(tx))
                time.sleep(0.3)

                rx = ser.read(8)
                ser.close()

                if len(rx) != 8:
                    continue

                rs, rsl, rl, rc, rst, rcrc, re, reof = rx

                if (
                    rs == 0x02 and
                    rsl == 0x07 and
                    rl == 0x02 and
                    rc == cmd_byte and
                    rst == expected_rx_state and
                    re == 0x03 and
                    reof == 0x0D and
                    cls.crc8([rs, rsl, rl, rc, rst, re, reof]) == rcrc
                ):
                    return True

            except Exception:
                continue
        return False


    # ======================
    # S23 (LOCAL / REMOTE)
    # CMD = 0x76
    # ======================
    @classmethod
    def set_s23_local(cls):
        return cls.send_and_validate(0x76, 0x00)

    @classmethod
    def set_s23_remote(cls):
        return cls.send_and_validate(0x76, 0x01)

    # ======================
    # S31 (LOAD)
    # CMD = 0x7E
    # ======================
    @classmethod
    def set_s31_8ohm(cls):
        return cls.send_and_validate(0x7E, 0x00)

    @classmethod
    def set_s31_neutral(cls):
        return cls.send_and_validate(0x7E, 0x01)

    @classmethod
    def set_s31_600ohm(cls):
        return cls.send_and_validate(0x7E, 0x02)
    #=======================
    # J58 (POWER SUPPLY)
    # CMD = 0x4A
    #=======================
    @classmethod
    def set_j58_off(cls):
        return cls.send_and_validate(0x4A, 0x00)

    @classmethod
    def set_j58_on(cls):
        return cls.send_and_validate(0x4A, 0x01)

    #=======================
    # J60 (POWER SUPPLY)
    # CMD = 0x4C
    #=======================

    @classmethod
    def set_j60_off(cls):
        return cls.send_and_validate(0x4C, 0x00)

    @classmethod
    def set_j60_on(cls):
        return cls.send_and_validate(0x4C, 0x01)
    
        # ======================
    # J13
    # CMD = 0x1D
    # ======================
    @classmethod
    def set_j13_off(cls):
        return cls.send_and_validate(0x1D, 0x00)

    @classmethod
    def set_j13_on(cls):
        return cls.send_and_validate(0x1D, 0x01)

    # ======================
    # J14
    # CMD = 0x1E
    # ======================
    @classmethod
    def set_j14_off(cls):
        return cls.send_and_validate(0x1E, 0x00)

    @classmethod
    def set_j14_on(cls):
        return cls.send_and_validate(0x1E, 0x01)

    # ======================
    # J15
    # CMD = 0x1F
    # ======================
    @classmethod
    def set_j15_off(cls):
        return cls.send_and_validate(0x1F, 0x00)

    @classmethod
    def set_j15_on(cls):
        return cls.send_and_validate(0x1F, 0x01)

    # ======================
    # J16
    # CMD = 0x20
    # ======================
    @classmethod
    def set_j16_off(cls):
        return cls.send_and_validate(0x20, 0x00)

    @classmethod
    def set_j16_on(cls):
        return cls.send_and_validate(0x20, 0x01)

    # ======================
    # J28
    # CMD = 0x2C
    # ======================
    @classmethod
    def set_j28_off(cls):
        return cls.send_and_validate(0x2C, 0x00)

    @classmethod
    def set_j28_on(cls):
        return cls.send_and_validate(0x2C, 0x01)

    # ======================
    # J29
    # CMD = 0x2D
    # ======================
    @classmethod
    def set_j29_off(cls):
        return cls.send_and_validate(0x2D, 0x00)

    @classmethod
    def set_j29_on(cls):
        return cls.send_and_validate(0x2D, 0x01)

    # ======================
    # S25
    # CMD = 0x78
    # ======================
    @classmethod
    def set_s25_off(cls):
        return cls.send_and_validate(0x78, 0x00)

    @classmethod
    def set_s25_on(cls):
        return cls.send_and_validate(0x78, 0x01)

    # ======================
    # S30
    # CMD = 0x7D
    # ======================
    @classmethod
    def set_s30_off(cls):
        return cls.send_and_validate(0x7D, 0x00)

    @classmethod
    def set_s30_on(cls):
        return cls.send_and_validate(0x7D, 0x01)

    # ======================
    # S32
    # CMD = 0x7F
    # ======================
    @classmethod
    def set_s32_off(cls):
        return cls.send_and_validate(0x7F, 0x00)

    @classmethod
    def set_s32_on(cls):
        return cls.send_and_validate(0x7F, 0x01)

    # ======================
    # J27
    # CMD = 0x2B
    # ======================
    @classmethod
    def set_j27_off(cls):
        return cls.send_and_validate(0x2B, 0x00)

    @classmethod
    def set_j27_on(cls):
        return cls.send_and_validate(0x2B, 0x01)

    # ======================
    # S24
    # CMD = 0x77
    # ======================
    @classmethod
    def set_s24_off(cls):
        return cls.send_and_validate(0x77, 0x00)

    @classmethod
    def set_s24_on(cls):
        return cls.send_and_validate(0x77, 0x01)
    
    # ======================
    # J30
    # CMD = 0x2E
    # ======================
    @classmethod
    def set_j30_off(cls):
        return cls.send_and_validate(0x2E, 0x00)
    @classmethod
    def set_j30_on(cls):
        return cls.send_and_validate(0x2E, 0x01)


    # ======================
    # J31
    # CMD = 0x2F
    # ======================
    @classmethod
    def set_j31_off(cls):
        return cls.send_and_validate(0x2F, 0x00)

    @classmethod
    def set_j31_on(cls):
        return cls.send_and_validate(0x2F, 0x01)

    # ======================
    # J32
    # CMD = 0x30
    # ======================
    @classmethod
    def set_j32_off(cls):
        return cls.send_and_validate(0x30, 0x00)
    @classmethod
    def set_j32_on(cls):
        return cls.send_and_validate(0x30, 0x01)


    # ======================
    # J33
    # CMD = 0x31
    # ======================
    @classmethod
    def set_j33_off(cls):
        return cls.send_and_validate(0x31, 0x00)

    @classmethod
    def set_j33_on(cls):
        return cls.send_and_validate(0x31, 0x01)

    # ======================
    # J34
    # CMD = 0x32
    # ======================
    @classmethod
    def set_j34_off(cls):
        return cls.send_and_validate(0x32, 0x00)
    @classmethod
    def set_j34_on(cls):
        return cls.send_and_validate(0x32, 0x01)


    # ======================
    # J36
    # CMD = 0x34
    # ======================
    @classmethod
    def set_j36_off(cls):
        return cls.send_and_validate(0x34, 0x00)
    @classmethod
    def set_j36_on(cls):
        return cls.send_and_validate(0x34, 0x01)
    
    # ======================
    # J37
    # CMD = 0x35
    # ======================
    @classmethod
    def set_j37_off(cls):
        return cls.send_and_validate(0x35, 0x00)
    @classmethod
    def set_j37_on(cls):
        return cls.send_and_validate(0x35, 0x01)


    # ======================
    # J38
    # CMD = 0x36
    # ======================
    @classmethod
    def set_j38_off(cls):
        return cls.send_and_validate(0x36, 0x00)

    @classmethod
    def set_j38_on(cls):
        return cls.send_and_validate(0x36, 0x01)

    # ======================
    # J39
    # CMD = 0x37
    # ======================
    @classmethod
    def set_j39_off(cls):
        return cls.send_and_validate(0x37, 0x00)
    @classmethod
    def set_j39_on(cls):
        return cls.send_and_validate(0x37, 0x01)


    # ======================
    # J40
    # CMD = 0x38
    # ======================
    @classmethod
    def set_j40_off(cls):
        return cls.send_and_validate(0x38, 0x00)
    @classmethod
    def set_j40_on(cls):
        return cls.send_and_validate(0x38, 0x01)


    # ======================
    # J41
    # CMD = 0x39
    # ======================
    @classmethod
    def set_j41_off(cls):
        return cls.send_and_validate(0x39, 0x00)
    @classmethod
    def set_j41_on(cls):
        return cls.send_and_validate(0x39, 0x01)


    # ======================
    # J42
    # CMD = 0x3A
    # ======================
    @classmethod
    def set_j42_off(cls):
        return cls.send_and_validate(0x3A, 0x00)
    @classmethod
    def set_j42_on(cls):
        return cls.send_and_validate(0x3A, 0x01)
    
    # ======================
    # J43
    # CMD = 0x3B
    # ======================
    @classmethod
    def set_j43_off(cls):
        return cls.send_and_validate(0x3B, 0x00)
    @classmethod
    def set_j43_on(cls):
        return cls.send_and_validate(0x3B, 0x01)
    
    # ======================
    # J44
    # CMD = 0x3C
    # ======================
    @classmethod
    def set_j44_off(cls):
        return cls.send_and_validate(0x3C, 0x00)
    @classmethod
    def set_j44_on(cls):
        return cls.send_and_validate(0x3C, 0x01)
    
    # ======================
    # J45
    # CMD = 0x3D
    # ======================
    @classmethod
    def set_j45_off(cls):
        return cls.send_and_validate(0x3D, 0x00)
    @classmethod
    def set_j45_on(cls):
        return cls.send_and_validate(0x3D, 0x01)
    
    # ======================
    # J46
    # CMD = 0x3E
    # ======================
    @classmethod
    def set_j46_off(cls):
        return cls.send_and_validate(0x3E, 0x00)
    @classmethod
    def set_j46_on(cls):
        return cls.send_and_validate(0x3E, 0x01)
    
    # ======================
    # J47
    # CMD = 0x3F
    # ======================
    @classmethod
    def set_j47_off(cls):
        return cls.send_and_validate(0x3F, 0x00)
    @classmethod
    def set_j47_on(cls):
        return cls.send_and_validate(0x3F, 0x01)
    
    # ======================
    # J48
    # CMD = 0x40
    # ======================
    @classmethod
    def set_j48_off(cls):
        return cls.send_and_validate(0x40, 0x00)
    @classmethod
    def set_j48_on(cls):
        return cls.send_and_validate(0x40, 0x01)
    
    
    
    
    # ======================
    # J49
    # CMD = 0x41
    # ======================
    @classmethod
    def set_j49_off(cls):
        return cls.send_and_validate(0x41, 0x00)

    @classmethod
    def set_j49_on(cls):
        return cls.send_and_validate(0x41, 0x01)

    # ======================
    # J51
    # CMD = 0x43
    # ======================
    @classmethod
    def set_j51_off(cls):
        return cls.send_and_validate(0x43, 0x00)

    @classmethod
    def set_j51_on(cls):
        return cls.send_and_validate(0x43, 0x01)

    # ======================
    # J52
    # CMD = 0x44
    # ======================
    @classmethod
    def set_j52_off(cls):
        return cls.send_and_validate(0x44, 0x00)
    @classmethod
    def set_j52_on(cls):
        return cls.send_and_validate(0x44, 0x01)


    # ======================
    # J53
    # CMD = 0x45
    # ======================
    @classmethod
    def set_j53_off(cls):
        return cls.send_and_validate(0x45, 0x00)
    @classmethod
    def set_j53_on(cls):
        return cls.send_and_validate(0x45, 0x01)


    # ======================
    # J54
    # CMD = 0x46
    # ======================
    @classmethod
    def set_j54_off(cls):
        return cls.send_and_validate(0x46, 0x00)
    @classmethod
    def set_j54_on(cls):
        return cls.send_and_validate(0x46, 0x01)
    
    # ======================
    # S26
    # CMD = 0x79
    # ======================
    @classmethod
    def set_s26_off(cls):
        return cls.send_and_validate(0x79, 0x00)

    @classmethod
    def set_s26_on(cls):
        return cls.send_and_validate(0x79, 0x01)


    # ======================
    # S33
    # CMD = 0x80
    # ======================
    @classmethod
    def set_s33_off(cls):
        return cls.send_and_validate(0x80, 0x00)

    @classmethod
    def set_s33_on(cls):
        return cls.send_and_validate(0x80, 0x01)


    # ======================
    # S34
    # CMD = 0x81
    # ======================
    @classmethod
    def set_s34_off(cls):
        return cls.send_and_validate(0x81, 0x00)

    @classmethod
    def set_s34_on(cls):
        return cls.send_and_validate(0x81, 0x01)
    
    # ======================
    # Default Relay States
    # ======================
    @classmethod
    def set_default_states(cls):
        return cls.send_and_validate(0xEE, 0xF0, expected_rx_state=0xF1)
    
    #=======================
    #Junction Box ALH4
    #=======================
    
    #=======================
    # J07
    # CMD = 0x17
    #=======================

    @classmethod
    def set_j07_off(cls):
        return cls.send_and_validate(0x17,0x00)

    @classmethod
    def set_j07_on(cls):
        return cls.send_and_validate(0x17,0x01)
    
    #=======================
    # J08
    # CMD = 0x18
    #=======================

    @classmethod
    def set_j08_off(cls):
        return cls.send_and_validate(0x18,0x00)

    @classmethod
    def set_j08_on(cls):
        return cls.send_and_validate(0x18,0x01)
    
    #=======================
    # J09
    # CMD = 0x19
    #=======================

    @classmethod
    def set_j09_off(cls):
        return cls.send_and_validate(0x19,0x00)

    @classmethod
    def set_j09_on(cls):
        return cls.send_and_validate(0x19,0x01)
    
    #=======================
    # J10
    # CMD = 0x1A
    #=======================

    @classmethod
    def set_j10_off(cls):
        return cls.send_and_validate(0x1A,0x00)

    @classmethod
    def set_j10_on(cls):
        return cls.send_and_validate(0x1A,0x01)
    
    #=======================
    # J11
    # CMD = 0x1B
    #=======================

    @classmethod
    def set_j11_off(cls):
        return cls.send_and_validate(0x1B,0x00)

    @classmethod
    def set_j11_on(cls):
        return cls.send_and_validate(0x1B,0x01)
    
    
    #=======================
    # J18
    # CMD = 0x22
    #=======================

    @classmethod
    def set_j18_off(cls):
        return cls.send_and_validate(0x22,0x00)

    @classmethod
    def set_j18_on(cls):
        return cls.send_and_validate(0x22,0x01)
    
    #=======================
    # J19
    # CMD = 0x23
    #=======================

    @classmethod
    def set_j19_off(cls):
        return cls.send_and_validate(0x23,0x00)

    @classmethod
    def set_j19_on(cls):
        return cls.send_and_validate(0x23,0x01)
    
    #=======================
    # J20
    # CMD = 0x24
    #=======================

    @classmethod
    def set_j20_off(cls):
        return cls.send_and_validate(0x24,0x00)

    @classmethod
    def set_j20_on(cls):
        return cls.send_and_validate(0x24,0x01)
    
    
    #=======================
    # J21
    # CMD = 0x25
    #=======================

    @classmethod
    def set_j21_off(cls):
        return cls.send_and_validate(0x25,0x00)

    @classmethod
    def set_j21_on(cls):
        return cls.send_and_validate(0x25,0x01)
    
    #=======================
    # J22
    # CMD = 0x26
    #=======================

    @classmethod
    def set_j22_off(cls):
        return cls.send_and_validate(0x26,0x00)

    @classmethod
    def set_j22_on(cls):
        return cls.send_and_validate(0x26,0x01)
    
    #=======================
    # J23
    # CMD = 0x27
    #=======================

    @classmethod
    def set_j23_off(cls):
        return cls.send_and_validate(0x27,0x00)

    @classmethod
    def set_j23_on(cls):
        return cls.send_and_validate(0x27,0x01)
    
    #=======================
    # J24
    # CMD = 0x28
    #=======================

    @classmethod
    def set_j24_off(cls):
        return cls.send_and_validate(0x28,0x00)

    @classmethod
    def set_j24_on(cls):
        return cls.send_and_validate(0x28,0x01)
    
    #=======================
    # J25
    # CMD = 0x29
    #=======================

    @classmethod
    def set_j25_off(cls):
        return cls.send_and_validate(0x29,0x00)

    @classmethod
    def set_j25_on(cls):
        return cls.send_and_validate(0x29,0x01)
    
    #=======================
    # J26
    # CMD = 0x2A
    #=======================

    @classmethod
    def set_j26_off(cls):
        return cls.send_and_validate(0x2A,0x00)

    @classmethod
    def set_j26_on(cls):
        return cls.send_and_validate(0x2A,0x01)
    
    #=======================
    # J28
    # CMD = 0x2C
    #=======================

    @classmethod
    def set_j28_off(cls):
        return cls.send_and_validate(0x2C,0x00)

    @classmethod
    def set_j28_on(cls):
        return cls.send_and_validate(0x2C,0x01)
    
    #=======================
    # J57
    # CMD = 0x49
    #=======================

    @classmethod
    def set_j57_off(cls):
        return cls.send_and_validate(0x49,0x00)

    @classmethod
    def set_j57_on(cls):
        return cls.send_and_validate(0x49,0x01)
    
    
    #=======================
    # J67
    # CMD = 0x53
    #=======================
    @classmethod
    def set_j67_off(cls):
        return cls.send_and_validate(0x53, 0x00)

    @classmethod
    def set_j67_on(cls):
        return cls.send_and_validate(0x53, 0x01)


    #=======================
    # J68
    # CMD = 0x54
    #=======================
    @classmethod
    def set_j68_off(cls):
        return cls.send_and_validate(0x54, 0x00)

    @classmethod
    def set_j68_on(cls):
        return cls.send_and_validate(0x54, 0x01)


    #=======================
    # J69
    # CMD = 0x55
    #=======================
    @classmethod
    def set_j69_off(cls):
        return cls.send_and_validate(0x55, 0x00)

    @classmethod
    def set_j69_on(cls):
        return cls.send_and_validate(0x55, 0x01)


    #=======================
    # J70
    # CMD = 0x56
    #=======================
    @classmethod
    def set_j70_off(cls):
        return cls.send_and_validate(0x56, 0x00)

    @classmethod
    def set_j70_on(cls):
        return cls.send_and_validate(0x56, 0x01)


    #=======================
    # J71
    # CMD = 0x57
    #=======================
    @classmethod
    def set_j71_off(cls):
        return cls.send_and_validate(0x57, 0x00)

    @classmethod
    def set_j71_on(cls):
        return cls.send_and_validate(0x57, 0x01)


    #=======================
    # S01
    # CMD = 0x60
    #=======================
    @classmethod
    def set_s01_off(cls):
        return cls.send_and_validate(0x60, 0x00)

    @classmethod
    def set_s01_on(cls):
        return cls.send_and_validate(0x60, 0x01)


    #=======================
    # S02
    # CMD = 0x61
    #=======================
    @classmethod
    def set_s02_off(cls):
        return cls.send_and_validate(0x61, 0x00)

    @classmethod
    def set_s02_on(cls):
        return cls.send_and_validate(0x61, 0x01)


    #=======================
    # S03
    # CMD = 0x62
    #=======================
    @classmethod
    def set_s03_off(cls):
        return cls.send_and_validate(0x62, 0x00)

    @classmethod
    def set_s03_on(cls):
        return cls.send_and_validate(0x62, 0x01)


    #=======================
    # S04
    # CMD = 0x63
    #=======================
    @classmethod
    def set_s04_off(cls):
        return cls.send_and_validate(0x63, 0x00)

    @classmethod
    def set_s04_on(cls):
        return cls.send_and_validate(0x63, 0x01)


    #=======================
    # S05
    # CMD = 0x64
    #=======================
    @classmethod
    def set_s05_off(cls):
        return cls.send_and_validate(0x64, 0x00)

    @classmethod
    def set_s05_on(cls):
        return cls.send_and_validate(0x64, 0x01)


    #=======================
    # S06
    # CMD = 0x65
    #=======================
    @classmethod
    def set_s06_off(cls):
        return cls.send_and_validate(0x65, 0x00)

    @classmethod
    def set_s06_on(cls):
        return cls.send_and_validate(0x65, 0x01)


    #=======================
    # S07
    # CMD = 0x66
    #=======================
    @classmethod
    def set_s07_off(cls):
        return cls.send_and_validate(0x66, 0x00)

    @classmethod
    def set_s07_on(cls):
        return cls.send_and_validate(0x66, 0x01)


    #=======================
    # S08
    # CMD = 0x67
    #=======================
    @classmethod
    def set_s08_off(cls):
        return cls.send_and_validate(0x67, 0x00)

    @classmethod
    def set_s08_on(cls):
        return cls.send_and_validate(0x67, 0x01)


    #=======================
    # S09
    # CMD = 0x68
    #=======================
    @classmethod
    def set_s09_off(cls):
        return cls.send_and_validate(0x68, 0x00)

    @classmethod
    def set_s09_on(cls):
        return cls.send_and_validate(0x68, 0x01)


    #=======================
    # S10
    # CMD = 0x69
    #=======================
    @classmethod
    def set_s10_off(cls):
        return cls.send_and_validate(0x69, 0x00)

    @classmethod
    def set_s10_on(cls):
        return cls.send_and_validate(0x69, 0x01)


    #=======================
    # S11
    # CMD = 0x6A
    #=======================
    @classmethod
    def set_s11_off(cls):
        return cls.send_and_validate(0x6A, 0x00)

    @classmethod
    def set_s11_on(cls):
        return cls.send_and_validate(0x6A, 0x01)


    #=======================
    # S12
    # CMD = 0x6B
    #=======================
    @classmethod
    def set_s12_off(cls):
        return cls.send_and_validate(0x6B, 0x00)

    @classmethod
    def set_s12_on(cls):
        return cls.send_and_validate(0x6B, 0x01)


    #=======================
    # S13
    # CMD = 0x6C
    #=======================
    @classmethod
    def set_s13_off(cls):
        return cls.send_and_validate(0x6C, 0x00)

    @classmethod
    def set_s13_on(cls):
        return cls.send_and_validate(0x6C, 0x01)


    #=======================
    # S14
    # CMD = 0x6D
    #=======================
    @classmethod
    def set_s14_off(cls):
        return cls.send_and_validate(0x6D, 0x00)

    @classmethod
    def set_s14_on(cls):
        return cls.send_and_validate(0x6D, 0x01)


    #=======================
    # S15
    # CMD = 0x6E
    #=======================
    @classmethod
    def set_s15_off(cls):
        return cls.send_and_validate(0x6E, 0x00)

    @classmethod
    def set_s15_on(cls):
        return cls.send_and_validate(0x6E, 0x01)


    #=======================
    # S16
    # CMD = 0x6F
    #=======================
    @classmethod
    def set_s16_off(cls):
        return cls.send_and_validate(0x6F, 0x00)

    @classmethod
    def set_s16_on(cls):
        return cls.send_and_validate(0x6F, 0x01)


    #=======================
    # S17
    # CMD = 0x70
    #=======================
    @classmethod
    def set_s17_off(cls):
        return cls.send_and_validate(0x70, 0x00)

    @classmethod
    def set_s17_on(cls):
        return cls.send_and_validate(0x70, 0x01)


    #=======================
    # S18
    # CMD = 0x71
    #=======================
    @classmethod
    def set_s18_off(cls):
        return cls.send_and_validate(0x71, 0x00)

    @classmethod
    def set_s18_on(cls):
        return cls.send_and_validate(0x71, 0x01)


    #=======================
    # S19
    # CMD = 0x72
    #=======================
    @classmethod
    def set_s19_off(cls):
        return cls.send_and_validate(0x72, 0x00)

    @classmethod
    def set_s19_on(cls):
        return cls.send_and_validate(0x72, 0x01)


    #=======================
    # S21
    # CMD = 0x74
    #=======================
    @classmethod
    def set_s21_off(cls):
        return cls.send_and_validate(0x74, 0x00)

    @classmethod
    def set_s21_on(cls):
        return cls.send_and_validate(0x74, 0x01)


    #=======================
    # S22
    # CMD = 0x75
    #=======================
    @classmethod
    def set_s22_off(cls):
        return cls.send_and_validate(0x75, 0x00)

    @classmethod
    def set_s22_on(cls):
        return cls.send_and_validate(0x75, 0x01)

    
    #=======================
    # S28
    # CMD = 0x7B
    # STATES:
    #   0x00 -> 8 ohms
    #   0x01 -> Neutral
    #   0x02 -> 600 ohms
    #=======================
    @classmethod
    def set_s28_8ohms(cls):
        return cls.send_and_validate(0x7B, 0x00)

    @classmethod
    def set_s28_neutral(cls):
        return cls.send_and_validate(0x7B, 0x01)

    @classmethod
    def set_s28_600ohms(cls):
        return cls.send_and_validate(0x7B, 0x02)


    #=======================
    # S29
    # CMD = 0x7C
    #=======================
    @classmethod
    def set_s29_off(cls):
        return cls.send_and_validate(0x7C, 0x00)

    @classmethod
    def set_s29_on(cls):
        return cls.send_and_validate(0x7C, 0x01)

    
    
    
    