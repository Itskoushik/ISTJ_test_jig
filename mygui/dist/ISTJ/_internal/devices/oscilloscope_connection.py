import logging
import pyvisa
from typing import Optional, Dict, List

"""
Robust Python-based oscilloscope communication module.

This module provides automatic discovery, identification, and connection to oscilloscopes
via VISA (Virtual Instrument Software Architecture) using PyVISA. It supports USB (USBTMC),
LAN (VXI-11), and TCPIP interfaces without hardcoding resource strings.

Key Features:
- Automatic oscilloscope discovery via VISA ResourceManager
- Safe resource enumeration with exception handling
- SCPI *IDN? identification query and response parsing 
- Persistent session management with configurable timeouts
- Communication validation via SCPI commands
- Comprehensive logging of discovery and connection steps
- Modular, extensible design for future SCPI command integration
"""


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OscilloscopeIdentification:
    """
    Data class to store parsed oscilloscope identification information.
    
    Attributes:
        manufacturer (str): Manufacturer name (e.g., 'Tektronix')
        model (str): Model number (e.g., 'MSO5054B')
        serial_number (str): Device serial number
        firmware_version (str): Firmware/software version
    """
    
    def __init__(self, manufacturer: str, model: str, 
                 serial_number: str, firmware_version: str):
        self.manufacturer = manufacturer
        self.model = model
        self.serial_number = serial_number
        self.firmware_version = firmware_version
    
    def __repr__(self) -> str:
        return (
            f"OscilloscopeIdentification("
            f"manufacturer='{self.manufacturer}', "
            f"model='{self.model}', "
            f"serial_number='{self.serial_number}', "
            f"firmware_version='{self.firmware_version}')"
        )
    
    def to_dict(self) -> Dict[str, str]:
        """Convert identification to dictionary."""
        return {
            'manufacturer': self.manufacturer,
            'model': self.model,
            'serial_number': self.serial_number,
            'firmware_version': self.firmware_version
        }


class OscilloscopeConnection:
    """
    Manages oscilloscope VISA connection, discovery, and identification.
    
    This class handles:
    - Discovery of all VISA resources
    - Safe opening of resources with timeout handling
    - SCPI *IDN? query execution and parsing
    - Persistent session management
    - Communication validation
    """
    
    # SCPI command constants
    SCPI_IDN_QUERY = "*IDN?"
    SCPI_OPC_QUERY = "*OPC?"
    SCPI_RESET = "*RST"
    
    # Default communication timeouts (milliseconds)
    DEFAULT_TIMEOUT_MS = 5000
    DISCOVERY_TIMEOUT_MS = 2000
    
    # Termination character settings
    DEFAULT_READ_TERMINATION = '\n'
    DEFAULT_WRITE_TERMINATION = '\n'
    
    def __init__(self):
        """Initialize the oscilloscope connection manager."""
        self.rm: Optional[pyvisa.ResourceManager] = None
        self.instrument: Optional[pyvisa.Resource] = None
        self.identification: Optional[OscilloscopeIdentification] = None
        self.resource_string: Optional[str] = None
        logger.info("OscilloscopeConnection initialized")
        self.claimed_visa_resources = set()

    
    def discover_resources(self) -> List[str]:
        if self.rm is None:
            try:
                self.rm = pyvisa.ResourceManager()
                logger.info("VISA ResourceManager created successfully")
            except Exception as e:
                logger.error(f"Failed to create ResourceManager: {e}")
                raise RuntimeError(f"Cannot initialize VISA ResourceManager: {e}")
        
        resources = self.rm.list_resources()
        logger.info(f"Discovered {len(resources)} VISA resource(s)")
        
        for i, resource in enumerate(resources, 1):
            logger.debug(f"  [{i}] {resource}")
        
        return list(resources)
    
    def _parse_idn_response(self, idn_response: str) -> Optional[OscilloscopeIdentification]:
        """
        Parse SCPI *IDN? response according to standard format.
        
        Standard format: <Manufacturer>,<Model>,<SerialNumber>,<FirmwareVersion>
        Example: Tektronix,MSO5054B,B123456,1.2.3.4567
        
        Args:
            idn_response (str): Response from *IDN? query
        
        Returns:
            OscilloscopeIdentification or None if parsing fails
        """
        try:
            # Remove whitespace and split by comma
            parts = [p.strip() for p in idn_response.strip().split(',')]
            
            if len(parts) < 4:
                logger.warning(
                    f"IDN response has fewer than 4 fields: {idn_response}"
                )
                return None
            
            manufacturer = parts[0]
            model = parts[1]
            serial_number = parts[2]
            firmware_version = parts[3]
            
            # Validate that we have reasonable values
            if not all([manufacturer, model, serial_number, firmware_version]):
                logger.warning("IDN response contains empty fields")
                return None
            
            identification = OscilloscopeIdentification(
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                firmware_version=firmware_version
            )
            
            logger.info(f"Successfully parsed IDN response: {identification}")
            return identification
            
        except Exception as e:
            logger.error(f"Failed to parse IDN response '{idn_response}': {e}")
            return None
    
    def _is_oscilloscope(self, idn_response: str) -> bool:
        idn = idn_response.upper()

        # 🚫 HARD BLOCK NON-SCOPE DEVICES
        reject_keywords = [
            "DM3058", "DM3068",   # Rigol DMM
            "DP832", "DP831",     # PSU
            "MULTIMETER",
            "POWER SUPPLY",
            "DG",                 # Generator
            "DMM"
        ]

        for r in reject_keywords:
            if r in idn:
                logger.info(f"[Reject] Not oscilloscope: {idn}")
                return False

        # ✅ Only allow real scope models
        scope_keywords = [
            "DS", "MSO", "DHO",       # Rigol scopes
            "TBS", "TDS", "DPO",      # Tektronix
            "SDS", "SIGLENT",         # Siglent
            "DSO", "KEYSIGHT",        # Keysight
            "RTO", "RTB"              # Rohde
        ]

        for k in scope_keywords:
            if k in idn:
                logger.info(f"[Accepted Scope] {idn}")
                return True

        logger.info(f"[Reject Unknown Device] {idn}")
        return False


    
    def _configure_resource(self, resource: pyvisa.Resource) -> None:
        """
        Configure communication settings for a VISA resource.
        
        Sets:
        - Read/write termination characters
        - Timeout values
        - Encoding
        
        Args:
            resource (pyvisa.Resource): The VISA resource to configure
        """
        try:
            resource.read_termination = self.DEFAULT_READ_TERMINATION
            resource.write_termination = self.DEFAULT_WRITE_TERMINATION
            resource.timeout = self.DEFAULT_TIMEOUT_MS
            resource.encoding = 'utf-8'
            
            logger.debug(
                f"Configured resource: "
                f"timeout={resource.timeout}ms, "
                f"termination='{self.DEFAULT_READ_TERMINATION}'"
            )
        except Exception as e:
            logger.warning(f"Failed to configure resource settings: {e}")
    
    def _attempt_connection(self, resource_string: str) -> Optional[pyvisa.Resource]:
        """
        Safely attempt to open a VISA resource.
        
        Args:
            resource_string (str): VISA resource identifier string
        
        Returns:
            pyvisa.Resource or None if connection fails
        """
        if not self.rm:
            logger.error("ResourceManager not initialized")
            return None
        
        try:
            logger.debug(f"Attempting to connect to: {resource_string}")
            resource = self.rm.open_resource(
                resource_string,
                timeout=self.DISCOVERY_TIMEOUT_MS
            )
            logger.info(f"Successfully opened resource: {resource_string}")
            return resource
            
        except pyvisa.VisaIOError as e:
            logger.debug(f"VISA I/O error for {resource_string}: {e}")
            return None
        except pyvisa.InvalidSession as e:
            logger.debug(f"Invalid session for {resource_string}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Failed to open {resource_string}: {type(e).__name__}: {e}")
            return None
    
    def _query_identification(self, resource: pyvisa.Resource) -> Optional[str]:
        """
        Query device identification using SCPI *IDN? command.
        
        Args:
            resource (pyvisa.Resource): The VISA resource
        
        Returns:
            str or None: IDN response or None if query fails
        """
        try:
            logger.debug(f"Sending query: {self.SCPI_IDN_QUERY}")
            idn_response = resource.query(self.SCPI_IDN_QUERY)
            logger.debug(f"Received IDN response: {idn_response}")
            return idn_response
            
        except pyvisa.VisaIOError as e:
            logger.debug(f"VISA I/O error during IDN query: {e}")
            return None
        except Exception as e:
            logger.debug(f"Failed to query IDN: {type(e).__name__}: {e}")
            return None
    
    def discover_and_connect(self) -> bool:
        """
        Discover all VISA resources and connect to the first valid oscilloscope.
        
        This is the main discovery and connection workflow:
        1. Enumerate all VISA resources
        2. Attempt to open each resource safely
        3. Query *IDN? for identification
        4. Parse and validate identification
        5. Configure successful connection
        6. Validate communication
        
        Returns:
            bool: True if successful connection and identification, False otherwise
        """
        logger.info("=" * 70)
        logger.info("Starting oscilloscope discovery and connection process")
        logger.info("=" * 70)
        
        # Step 1: Discover resources
        resources = self.discover_resources()
        
        if not resources:
            logger.warning("No VISA resources found on system")
            return False
        
        # Step 2-3: Attempt connection and identification for each resource
        for resource_string in resources:
            # 🚫 SKIP serial-port resources (ASRLn::INSTR) — the real
            # instruments on this bench are always USB VISA devices
            # (e.g. USB::0x0699::0x03C4::SGVJ016415::INSTR). ASRL ports
            # are leftover COM ports (Bluetooth/virtual modems etc.) that
            # never respond correctly to *IDN? and just burn ~5-6s each
            # on a query timeout.
            if resource_string.upper().startswith("ASRL"):
                logger.info(f"[Skip] Serial resource, not a USB instrument: {resource_string}")
                continue

            # 🚫 SKIP already claimed resources (DMM/PSU etc)
            if resource_string in self.claimed_visa_resources:
                logger.info(f"[Skip] Resource already claimed by another device: {resource_string}")
                continue

            logger.info(f"\n[Discovery] Attempting resource: {resource_string}")
            
            # Attempt to open resource
            resource = self._attempt_connection(resource_string)
            if not resource:
                logger.info(f"[Discovery] Resource unavailable or inaccessible")
                continue
            
            try:
                # Configure resource settings
                self._configure_resource(resource)
                
                # Query identification
                idn_response = self._query_identification(resource)
                if not idn_response:
                    logger.info(f"[Discovery] No IDN response from {resource_string}")
                    resource.close()
                    continue

                # Step 4: Parse and validate identification
                if not self._is_oscilloscope(idn_response):
                    logger.info(
                        f"[Discovery] Device is not an oscilloscope: {idn_response[:50]}"
                    )
                    resource.close()
                    continue
                
                # Parse identification
                identification = self._parse_idn_response(idn_response)
                if not identification:
                    logger.info(f"[Discovery] Failed to parse identification response")
                    resource.close()
                    continue
                
                # Step 5: Connection successful - save reference and configure
                logger.info(
                    f"[Success] Oscilloscope identified: "
                    f"{identification.manufacturer} {identification.model}"
                )
                logger.info(f"  Serial Number: {identification.serial_number}")
                logger.info(f"  Firmware Version: {identification.firmware_version}")
                logger.info(f"  Resource String: {resource_string}")
                
                self.instrument = resource
                self.identification = identification
                self.resource_string = resource_string
                
                # Step 6: Validate communication
                if self._validate_communication():

                    logger.info("=" * 70)
                    logger.info("Oscilloscope connection and identification successful!")
                    logger.info("=" * 70)
                    return True
                else:
                    logger.warning("Communication validation failed")
                    resource.close()
                    self.instrument = None
                    continue
                    
            except Exception as e:
                logger.error(f"Unexpected error during connection: {e}")
                try:
                    resource.close()
                except:
                    pass
                continue
        
        logger.error("=" * 70)
        logger.error("Failed to discover and connect to any oscilloscope")
        logger.error("=" * 70)
        return False
    
    def _validate_communication(self) -> bool:
        """
        Validate communication with the connected oscilloscope.
        
        Sends simple SCPI commands to verify responsiveness:
        - *OPC? (Operation Complete) query
        - Optionally *RST (Reset) command
        
        Returns:
            bool: True if communication is valid
        """
        if not self.instrument:
            logger.error("No instrument connected for validation")
            return False
        
        try:
            logger.debug("Validating communication with *OPC? query")
            opc_response = self.instrument.query(self.SCPI_OPC_QUERY)
            logger.debug(f"OPC response: {opc_response}")
            
            if opc_response.strip() != '1':
                logger.warning(f"Unexpected OPC response: {opc_response}")
                # Some instruments may not respond with '1', continue anyway
            
            logger.info("Communication validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Communication validation failed: {e}")
            return False
    
    def close(self) -> None:
        """Close the oscilloscope connection and cleanup resources."""
        if self.instrument:
            try:
                self.instrument.close()
                logger.info("Oscilloscope connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self.instrument = None
        
        if self.rm:
            try:
                self.rm.close()
                logger.info("VISA ResourceManager closed")
            except Exception as e:
                logger.error(f"Error closing ResourceManager: {e}")
            finally:
                self.rm = None
    
    def send_scpi_command(self, command: str) -> None:
        """
        Send a SCPI command to the connected oscilloscope.
        
        Extension point for future SCPI command execution.
        
        Args:
            command (str): SCPI command string (e.g., '*RST')
        
        Raises:
            RuntimeError: If no instrument is connected
        """
        if not self.instrument:
            raise RuntimeError("No oscilloscope connected")
        
        try:
            logger.debug(f"Sending SCPI command: {command}")
            self.instrument.write(command)
            logger.debug(f"Command sent successfully")
        except Exception as e:
            logger.error(f"Failed to send SCPI command '{command}': {e}")
            raise
    
    def query_scpi_command(self, command: str) -> str:
        """
        Send a SCPI query command and retrieve the response.
        
        Extension point for future SCPI command execution.
        
        Args:
            command (str): SCPI query command (e.g., '*IDN?')
        
        Returns:
            str: Response from the instrument
        
        Raises:
            RuntimeError: If no instrument is connected
        """
        if not self.instrument:
            raise RuntimeError("No oscilloscope connected")
        
        try:
            logger.debug(f"Sending SCPI query: {command}")
            response = self.instrument.query(command)
            logger.debug(f"Query response: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to query SCPI command '{command}': {e}")
            raise
    
    def get_identification(self) -> Optional[OscilloscopeIdentification]:
        """Get the identification information of the connected oscilloscope."""
        return self.identification
    
    def is_connected(self) -> bool:
        """Check if an oscilloscope is currently connected."""
        return self.instrument is not None

    def close_instrument_only(self) -> None:
        """
        Close only the instrument session — deliberately does NOT close
        self.rm (the VISA ResourceManager).

        On this system's VISA backend, separate pyvisa.ResourceManager()
        instances have been observed to share the same underlying default-RM
        session within one process: closing ANY ResourceManager (even one
        that only ever opened the oscilloscope) invalidates VISA sessions
        belonging to OTHER instruments (PSU/DMM) opened via a different
        ResourceManager() instance in the same process.

        To guarantee the oscilloscope layer can never take down PSU/DMM,
        this method — not close() — must be used whenever a stale
        oscilloscope connection is cleaned up while other instruments may
        still be active (i.e. everywhere except final application exit).
        """
        if self.instrument:
            try:
                self.instrument.close()
                logger.info("Oscilloscope instrument session closed (ResourceManager left open)")
            except Exception as e:
                logger.error(f"Error closing oscilloscope instrument: {e}")
            finally:
                self.instrument = None
        # Deliberately do NOT close self.rm here — see docstring.

    def reconnect_specific(self, resource_string: str,
                            expected_manufacturer: str = None,
                            expected_model: str = None,
                            expected_serial: str = None) -> bool:
        """
        Reconnect directly to a previously-known Oscilloscope VISA resource
        string. Opens EXACTLY that one resource — no bus scan.
        """
        logger.info(f"[Reconnect] Attempting direct reconnect to known resource: {resource_string}")
        try:
            self.rm = pyvisa.ResourceManager()
        except Exception as e:
            logger.error(f"[Reconnect] Failed to create ResourceManager: {e}")
            return False

        resource = self._attempt_connection(resource_string)
        if not resource:
            logger.info(f"[Reconnect] Resource unavailable: {resource_string}")
            return False

        try:
            self._configure_resource(resource)
            idn_response = self._query_identification(resource)
            if not idn_response:
                logger.info("[Reconnect] No IDN response from known resource")
                resource.close()
                return False

            if not self._is_oscilloscope(idn_response):
                logger.info(f"[Reconnect] Device at known resource is no longer an oscilloscope: {idn_response}")
                resource.close()
                return False

            identification = self._parse_idn_response(idn_response)
            if not identification:
                resource.close()
                return False

            if expected_manufacturer and identification.manufacturer != expected_manufacturer:
                logger.warning("[Reconnect] Manufacturer mismatch — refusing to bind")
                resource.close()
                return False
            if expected_model and identification.model != expected_model:
                logger.warning("[Reconnect] Model mismatch — refusing to bind")
                resource.close()
                return False
            if expected_serial and identification.serial_number != expected_serial:
                logger.warning("[Reconnect] Serial number mismatch — refusing to bind")
                resource.close()
                return False

            self.instrument = resource
            self.identification = identification
            self.resource_string = resource_string

            if self._validate_communication():
                logger.info(f"[Reconnect] Direct reconnect succeeded: {identification}")
                return True

            logger.warning("[Reconnect] Communication validation failed on known resource")
            resource.close()
            self.instrument = None
            return False

        except Exception as e:
            logger.error(f"[Reconnect] Unexpected error during direct reconnect: {e}")
            try:
                resource.close()
            except Exception:
                pass
            return False

    def autoset(self) -> bool:
        """
        If an oscilloscope is already connected, trigger its
        auto-setup/autoscale function (brand-specific SCPI command).
        """
        if not self.is_connected():
            logger.warning("[Autoset] No oscilloscope connected — cannot autoset")
            return False

        manuf = (self.identification.manufacturer or "").upper()
        model = (self.identification.model or "").upper()

        try:
            if "RIGOL" in manuf:
                cmd = ":AUToscale"
            elif "SIGLENT" in manuf:
                cmd = "AUTO_SETUP"
            elif "TEKTRONIX" in manuf or "KEYSIGHT" in manuf or "AGILENT" in manuf:
                cmd = "AUToset EXECute"
            else:
                # fallback — try the most common SCPI form
                cmd = ":AUToscale"

            logger.info(f"[Autoset] Sending '{cmd}' to {manuf} {model}")
            self.instrument.write(cmd)
            return True

        except Exception as e:
            logger.error(f"[Autoset] Failed to send autoset command: {e}")
            return False

def main():
    """
    Example usage of the OscilloscopeConnection module.
    
    Demonstrates:
    - Creating a connection manager
    - Discovering and connecting to an oscilloscope
    - Retrieving identification information
    - Sending SCPI commands
    - Closing the connection
    """
    connection = OscilloscopeConnection()
    
    try:
        if connection.discover_and_connect():
            identification = connection.get_identification()
            if identification:
                logger.info("\n[Application] Connected Oscilloscope Details:")
                logger.info(f"  Manufacturer: {identification.manufacturer}")
                logger.info(f"  Model: {identification.model}")
                logger.info(f"  Serial Number: {identification.serial_number}")
                logger.info(f"  Firmware Version: {identification.firmware_version}")

            logger.info("\n[Application] Oscilloscope is ready for SCPI commands")
            logger.info("Triggering AUTO-SETUP on the oscilloscope")
            connection.autoset()

        else:
            logger.error("[Application] Failed to connect to oscilloscope")
            
    finally:
        # Always close connection
        connection.close()


if __name__ == "__main__":
    main()