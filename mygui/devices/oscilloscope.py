import pyvisa
from typing import Optional, Dict, List


class OscilloscopeIdentification:
    """Data class to store parsed oscilloscope identification information."""
    
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
    Minimal logging output; emits signals via caller for GUI integration.
    """
    
    SCPI_IDN_QUERY = "*IDN?"
    SCPI_OPC_QUERY = "*OPC?"
    DEFAULT_TIMEOUT_MS = 5000
    DISCOVERY_TIMEOUT_MS = 2000
    DEFAULT_READ_TERMINATION = '\n'
    DEFAULT_WRITE_TERMINATION = '\n'
    
    def __init__(self):
        """Initialize the oscilloscope connection manager."""
        self.rm: Optional[pyvisa.ResourceManager] = None
        self.instrument: Optional[pyvisa.Resource] = None
        self.identification: Optional[OscilloscopeIdentification] = None
        self.resource_string: Optional[str] = None
        self.claimed_visa_resources = set()

    
    def discover_resources(self) -> List[str]:
        """
        Discover all VISA resources available on the system.
        
        Returns:
            List[str]: List of VISA resource strings
        
        Raises:
            RuntimeError: If ResourceManager cannot be instantiated
        """
        try:
            self.rm = pyvisa.ResourceManager()
        except Exception as e:
            raise RuntimeError(f"Cannot initialize VISA ResourceManager: {e}")
        
        resources = self.rm.list_resources()
        return list(resources)
    
    def _parse_idn_response(self, idn_response: str) -> Optional[OscilloscopeIdentification]:
        """Parse SCPI *IDN? response: <Mfg>,<Model>,<SN>,<FW>"""
        try:
            parts = [p.strip() for p in idn_response.strip().split(',')]
            
            if len(parts) < 4:
                return None
            
            manufacturer = parts[0]
            model = parts[1]
            serial_number = parts[2]
            firmware_version = parts[3]
            
            if not all([manufacturer, model, serial_number, firmware_version]):
                return None
            
            identification = OscilloscopeIdentification(
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                firmware_version=firmware_version
            )
            
            return identification
            
        except Exception:
            return None
    
    def _is_oscilloscope(self, idn_response: str) -> bool:
        """Heuristic check for oscilloscope manufacturer identifiers."""
        oscilloscope_manufacturers = [
            'Tektronix', 'Agilent', 'Keysight', 'Rigol', 'Siglent',
            'LeCroy', 'Teledyne', 'Rohde & Schwarz', 'HP'
        ]
        
        idn_upper = idn_response.upper()
        return any(mfg.upper() in idn_upper for mfg in oscilloscope_manufacturers)
    
    def _configure_resource(self, resource: pyvisa.Resource) -> None:
        """Configure communication settings for a VISA resource."""
        try:
            resource.read_termination = self.DEFAULT_READ_TERMINATION
            resource.write_termination = self.DEFAULT_WRITE_TERMINATION
            resource.timeout = self.DEFAULT_TIMEOUT_MS
            resource.encoding = 'utf-8'
        except Exception:
            pass
    
    def _attempt_connection(self, resource_string: str) -> Optional[pyvisa.Resource]:
        """Safely attempt to open a VISA resource."""
        if not self.rm:
            return None
        
        try:
            resource = self.rm.open_resource(
                resource_string,
                timeout=self.DISCOVERY_TIMEOUT_MS
            )
            return resource
        except (pyvisa.VisaIOError, pyvisa.InvalidSession, Exception):
            return None
    
    def _query_identification(self, resource: pyvisa.Resource) -> Optional[str]:
        """Query device identification using SCPI *IDN? command."""
        try:
            idn_response = resource.query(self.SCPI_IDN_QUERY)
            return idn_response
        except (pyvisa.VisaIOError, Exception):
            return None
    
    def _validate_communication(self) -> bool:
        """Validate communication with the connected oscilloscope."""
        if not self.instrument:
            return False
        
        try:
            self.instrument.query(self.SCPI_OPC_QUERY)
            return True
        except Exception:
            return False
    
    def discover_and_connect(self) -> bool:
        """
        Discover all VISA resources and connect to the first valid oscilloscope.
        
        Returns:
            bool: True if successful connection and identification, False otherwise
        """
        try:
            resources = self.discover_resources()
        except RuntimeError:
            return False
        
        if not resources:
            return False
        
        # Attempt connection and identification for each resource
        for resource_string in resources:
            if resource_string in self.claimed_visa_resources:
                continue

            
            try:
                resource = self._attempt_connection(resource_string)
                if not resource:
                    continue
                
                self._configure_resource(resource)
                
                idn_response = self._query_identification(resource)
                if not idn_response:
                    resource.close()
                    continue
                
                if not self._is_oscilloscope(idn_response):
                    resource.close()
                    continue
                
                identification = self._parse_idn_response(idn_response)
                if not identification:
                    resource.close()
                    continue
                
                # Connection successful
                self.instrument = resource
                self.identification = identification
                self.resource_string = resource_string
                self.claimed_visa_resources.add(resource_string)

                
                if self._validate_communication():
                    return True
                else:
                    # ❌ Validation failed → release claim
                    self.claimed_visa_resources.discard(resource_string)
                    resource.close()
                    self.instrument = None
                    continue

            except Exception:
                try:
                    resource.close()
                except:
                    pass
                continue
        
        return False
    
    def close(self) -> None:
        """Close the oscilloscope connection and cleanup resources."""
        if self.instrument:
            try:
                self.instrument.close()
            except Exception:
                pass
            finally:
                self.instrument = None
        
        if self.rm:
            try:
                self.rm.close()
            except Exception:
                pass
            finally:
                self.rm = None
    
    def get_identification(self) -> Optional[OscilloscopeIdentification]:
        """Get the identification information of the connected oscilloscope."""
        return self.identification
    
    def is_connected(self) -> bool:
        """Check if an oscilloscope is currently connected."""
        return self.instrument is not None