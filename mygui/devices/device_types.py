from enum import Enum


class DeviceType(Enum):
    PSU = "Power Supply"
    OSC = "Oscilloscope"
    DMM = "Digital Multimeter"
    AUDIO = "Audio Analyzer"
    MCU = "Microcontroller"