
# ============================================================================
# SCPI COMMAND CONSTANTS (DP832 DATASHEET COMPLIANT)
# ============================================================================
class PSUCommands:
    """SCPI commands for DP832 Power Supply Unit (DP832 Manual Compliant)"""
    
    # Channel Selection
    CHANNEL_SELECT = "INST:NSEL {}"  # {} = channel number (1, 2, or 3)
    
    # Voltage Settings
    VOLTAGE_SET = "SOUR:VOLT {}"  # {} = voltage value (0-32V range)
    VOLTAGE_QUERY = "SOUR:VOLT?"
    VOLTAGE_READBACK = "MEAS:VOLT?"  # Live voltage measurement
    
    # Current Settings
    CURRENT_SET = "SOUR:CURR {}"  # {} = current value (0-5.1A range)
    CURRENT_QUERY = "SOUR:CURR?"
    CURRENT_READBACK = "MEAS:CURR?"  # Live current measurement
    
    # Output Control
    OUTPUT_ON = "OUTP ON"
    OUTPUT_OFF = "OUTP OFF"
    OUTPUT_QUERY = "OUTP?"
    
    # System Settings
    SYSTEM_LOCK_ON = "SYST:LOCK ON"  # Lock front panel
    SYSTEM_LOCK_OFF = "SYST:LOCK OFF"  # Unlock front panel
    
    # Over-voltage Protection
    OVP_SET = "SOUR:VOLT:PROT {}"  # {} = OVP threshold
    OVP_QUERY = "SOUR:VOLT:PROT?"
    OVP_ENABLE = "SOUR:VOLT:PROT:STAT ON"
    OVP_DISABLE = "SOUR:VOLT:PROT:STAT OFF"
    
    # Over-current Protection
    OCP_SET = "SOUR:CURR:PROT {}"  # {} = OCP threshold
    OCP_QUERY = "SOUR:CURR:PROT?"
    OCP_ENABLE = "SOUR:CURR:PROT:STAT ON"
    OCP_DISABLE = "SOUR:CURR:PROT:STAT OFF"
    
    # System Information
    DEVICE_CLEAR = "*CLS"
    RESET = "*RST"
    IDENTIFICATION_QUERY = "*IDN?"
    STATUS_QUERY = "STAT?"


