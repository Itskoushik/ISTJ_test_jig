import sys
import time
from datetime import datetime
from pathlib import Path
from PyQt5.QtGui import QFont, QPixmap, QColor, QIcon, QDesktopServices
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize, QUrl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QDialog,
    QMessageBox, QScrollArea, QSizePolicy, QGridLayout, QFrame, QListWidget, QListWidgetItem
)
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrinter
import pyvisa
from typing import Optional, Dict, List
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import sqlite3

import traceback
from PyQt5.QtWidgets import QMessageBox



def global_exception_handler(exctype, value, tb):
    msg = ''.join(traceback.format_exception(exctype, value, tb))
    QMessageBox.critical(
        None,
        "Critical Error",
        "An unexpected error occurred.\n\n"
        "The application will remain open.\n"
        "Please contact the system administrator."
    )
    print(msg)

sys.excepthook = global_exception_handler

# ============================================================================
# DIRECTORY SETUP
# ============================================================================


BASE_DIR = Path(__file__).parent
from db_paths import ADMIN_DB_PATH
RESOURCES_DIR = BASE_DIR / "resourses"
LOGS_DIR = Path(
    r"D:\workkkkkk\\harvel systems\\codes\\gui\\mygui\\logs\\connection logs"
)

LOGS_PDF_DIR = Path(
    r"D:\workkkkkk\\harvel systems\\codes\\gui\\mygui\\logs\\logs_pdf"
)

REPORTS_DIR = BASE_DIR / "test_reports"
PDF_TEST_REPORTS_DIR = Path(
    r"D:\\workkkkkk\\harvel systems\\codes\\gui\\mygui\\test_reports\\pdfs"
)


for directory in [RESOURCES_DIR, LOGS_DIR, REPORTS_DIR, LOGS_PDF_DIR]:
    directory.mkdir(exist_ok=True)

# ============================================================================
# LOGGER UTILITY
# ============================================================================
class Logger:
    def __init__(self, log_file=None):
        self.log_file = log_file
        self.logs = []

    def log(self, message, error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append({"text": log_entry, "error": error})
        
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry + "\n")
            except Exception:
                pass


    def get_logs(self):
        return self.logs

    def clear(self):
        self.logs = []
        


def export_logs_to_pdf(log_entries, pdf_path: Path):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    story = []

    story.append(Paragraph("<b>HAL Connection Logs</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    
    if not log_entries:
        story.append(Paragraph("No logs available.", styles["Normal"]))

    

    for entry in log_entries:
        color = "red" if entry["error"] else "black"
        story.append(
            Paragraph(
                f"<font color='{color}'>{entry['text']}</font>",
                styles["Normal"]
            )
        )
        story.append(Spacer(1, 6))

    doc.build(story)


# ============================================================================
# OSCILLOSCOPE VISA DISCOVERY (from main.py - Integration Layer)
# ============================================================================
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


def init_admin_auth_db():
    """Initialize admin authentication database in the specified directory."""
    # Ensure the database directory exists
    from db_paths import ADMIN_DB_PATH

    ADMIN_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(ADMIN_DB_PATH))

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_name TEXT,
            designation TEXT,
            password TEXT,
            PRIMARY KEY (admin_name, designation)
        )
    """)

    # Default designation passwords (first run only)
    import hashlib

    def hash_pwd(p):
        return hashlib.sha256(p.encode("utf-8")).hexdigest()

    defaults = [
        ("_default", "Senior Test Engineer", hash_pwd("admin10")),
        ("_default", "Manager", hash_pwd("admin11")),
        ("_default", "General Manager", hash_pwd("admin12")),
    ]


    for row in defaults:
        cur.execute(
            "INSERT OR IGNORE INTO admins VALUES (?, ?, ?)", row
        )

    conn.commit()
    conn.close()


# ============================================================================
# SCREEN 1: LOGIN SCREEN
# ============================================================================

class LoginScreen(QMainWindow):
    login_success = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HAL - Login")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "wave.png")))
        self.setGeometry(100, 100, 550, 650)
        self.setFixedSize(550, 600)  # Fixed window size, non-resizable
        self.setStyleSheet("background: linear-gradient(to bottom, #e0f7fa, #ffffff);")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Logos Section
        logos_layout = QHBoxLayout()
        logos_layout.setContentsMargins(0, 0, 0, 0)
        logos_layout.addStretch()

        # HAL Logo
        hal_logo_label = QLabel()
        hal_pixmap = QPixmap(str(RESOURCES_DIR / "hal_logo.png"))
        hal_pixmap = hal_pixmap.scaled(120, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        hal_logo_label.setPixmap(hal_pixmap)
        hal_logo_label.setAlignment(Qt.AlignCenter)
        logos_layout.addWidget(hal_logo_label)

        # Vertical Separator Line
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setLineWidth(1)
        separator.setStyleSheet("color: #b0c4d4;")
        separator.setFixedWidth(1)
        separator.setMinimumHeight(60)
        logos_layout.addWidget(separator)

        # Zing Logo
        zing_logo_label = QLabel()
        zing_pixmap = QPixmap(str(RESOURCES_DIR / "zing.png"))
        zing_pixmap = zing_pixmap.scaled(120, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        zing_logo_label.setPixmap(zing_pixmap)
        zing_logo_label.setAlignment(Qt.AlignCenter)
        logos_layout.addWidget(zing_logo_label)

        logos_layout.addStretch()
        layout.addLayout(logos_layout)

        # Tab Widget for Employee and Admin Login
        self.tab_widget = QWidget()
        tab_layout = QVBoxLayout(self.tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        # Tab buttons (Employee and Admin)
        tab_buttons_layout = QHBoxLayout()
        tab_buttons_layout.setContentsMargins(0, 0, 0, 0)
        tab_buttons_layout.setSpacing(0)

        self.employee_tab_btn = QPushButton("Employee Login")
        self.employee_tab_btn.setMinimumHeight(40)
        self.employee_tab_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.employee_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f4f8;
                color: #1a5da8;
                border: 1px solid #1a5da8;
                border-radius: 0px;
                padding: 10px;
                border-right: none;
            }
            QPushButton:hover {
                background-color: #d0e8f2;
            }
        """)
        self.employee_tab_btn.clicked.connect(self.show_employee_login)
        tab_buttons_layout.addWidget(self.employee_tab_btn)

        self.admin_tab_btn = QPushButton("Admin Login")
        self.admin_tab_btn.setMinimumHeight(40)
        self.admin_tab_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.admin_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #666666;
                border: 1px solid #d0d0d0;
                border-radius: 0px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #eeeeee;
            }
        """)
        self.admin_tab_btn.clicked.connect(self.show_admin_login)
        tab_buttons_layout.addWidget(self.admin_tab_btn)

        tab_layout.addLayout(tab_buttons_layout)

        # Stacked widget to hold both login forms
        self.stacked_widget = QWidget()
        stacked_layout = QVBoxLayout(self.stacked_widget)
        stacked_layout.setContentsMargins(0, 0, 0, 0)
        stacked_layout.setSpacing(0)

        # ===== EMPLOYEE LOGIN FORM =====
        self.employee_form = QWidget()
        employee_form_layout = QVBoxLayout(self.employee_form)
        employee_form_layout.setContentsMargins(0, 20, 0, 0)
        employee_form_layout.setSpacing(20)

        # Title
        employee_title_label = QLabel("Employee Login")
        employee_title_label.setFont(QFont("Arial", 24, QFont.Bold))
        employee_title_label.setAlignment(Qt.AlignCenter)
        employee_title_label.setStyleSheet("color: #1a5da8; background-color: transparent;")
        employee_form_layout.addWidget(employee_title_label)

        # Employee Name Field
        name_container = QHBoxLayout()
        name_icon = QLabel("👤")
        name_icon.setFont(QFont("Arial", 14))
        name_container.addWidget(name_icon)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Employee Name")
        self.name_input.setStyleSheet(self.input_style())
        name_container.addWidget(self.name_input)
        employee_form_layout.addLayout(name_container)

        # Employee ID Field
        id_container = QHBoxLayout()
        id_icon = QLabel("🪪")
        id_icon.setFont(QFont("Arial", 14))
        id_container.addWidget(id_icon)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Employee ID")
        self.id_input.setStyleSheet(self.input_style())
        id_container.addWidget(self.id_input)
        employee_form_layout.addLayout(id_container)

        # Login Button
        self.employee_login_btn = QPushButton("LOGIN")
        self.employee_login_btn.setStyleSheet(self.button_style())
        self.employee_login_btn.clicked.connect(self.validate_employee_login)
        employee_form_layout.addWidget(self.employee_login_btn)

        employee_form_layout.addStretch()
        stacked_layout.addWidget(self.employee_form)

        # ===== ADMIN LOGIN FORM (FIXED LAYOUT) =====
        self.admin_form = QWidget()
        admin_form_layout = QVBoxLayout(self.admin_form)
        admin_form_layout.setContentsMargins(0, 20, 0, 0)
        admin_form_layout.setSpacing(18)  # Consistent vertical spacing

        # Title
        admin_title_label = QLabel("Admin Login")
        admin_title_label.setFont(QFont("Arial", 24, QFont.Bold))
        admin_title_label.setAlignment(Qt.AlignCenter)
        admin_title_label.setStyleSheet("color: #1a5da8; background-color: transparent;")
        admin_form_layout.addWidget(admin_title_label)

        # ========== ADMIN NAME FIELD ROW ==========
        admin_name_row = QHBoxLayout()
        admin_name_row.setContentsMargins(0, 0, 0, 0)
        admin_name_row.setSpacing(12)
        
        # Icon container with fixed width
        admin_name_icon_container = QWidget()
        admin_name_icon_container.setFixedWidth(36)
        admin_name_icon_layout = QHBoxLayout(admin_name_icon_container)
        admin_name_icon_layout.setContentsMargins(0, 0, 0, 0)
        admin_name_icon_layout.setSpacing(0)
        
        admin_name_icon = QLabel("👤")
        admin_name_icon.setFont(QFont("Arial", 14))
        admin_name_icon.setAlignment(Qt.AlignCenter)
        admin_name_icon_layout.addWidget(admin_name_icon)
        
        admin_name_row.addWidget(admin_name_icon_container, 0, Qt.AlignVCenter)

        self.admin_name_input = QLineEdit()
        self.admin_name_input.setPlaceholderText("Enter Admin Name")
        self.admin_name_input.setStyleSheet(self.input_style())
        self.admin_name_input.setMinimumHeight(40)
        self.admin_name_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        admin_name_row.addWidget(self.admin_name_input, 1)
        
        admin_form_layout.addLayout(admin_name_row)

        # ========== DESIGNATION DROPDOWN ROW ==========
        designation_row = QHBoxLayout()
        designation_row.setContentsMargins(0, 0, 0, 0)
        designation_row.setSpacing(12)
        
        # Icon container with fixed width
        designation_icon_container = QWidget()
        designation_icon_container.setFixedWidth(36)
        designation_icon_layout = QHBoxLayout(designation_icon_container)
        designation_icon_layout.setContentsMargins(0, 0, 0, 0)
        designation_icon_layout.setSpacing(0)
        
        designation_icon = QLabel("💼")
        designation_icon.setFont(QFont("Arial", 14))
        designation_icon.setAlignment(Qt.AlignCenter)
        designation_icon_layout.addWidget(designation_icon)
        
        designation_row.addWidget(designation_icon_container, 0, Qt.AlignVCenter)

        self.designation_combo = QComboBox()
        self.designation_combo.addItem("Select Designation")  # Placeholder
        self.designation_combo.addItems([
            "Senior Test Engineer",
            "Manager",
            "General Manager",
            "Meta Admin"
        ])
        self.designation_combo.setMinimumHeight(40)
        self.designation_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.designation_combo.setStyleSheet(self.combo_style())
        designation_row.addWidget(self.designation_combo, 1)
        
        admin_form_layout.addLayout(designation_row)

        # ========== PASSWORD FIELD ROW ==========
        password_row = QHBoxLayout()
        password_row.setContentsMargins(0, 0, 0, 0)
        password_row.setSpacing(12)
        
        # Icon container with fixed width
        password_icon_container = QWidget()
        password_icon_container.setFixedWidth(36)
        password_icon_layout = QHBoxLayout(password_icon_container)
        password_icon_layout.setContentsMargins(0, 0, 0, 0)
        password_icon_layout.setSpacing(0)
        
        password_icon = QLabel("🔒")
        password_icon.setFont(QFont("Arial", 14))
        password_icon.setAlignment(Qt.AlignCenter)
        password_icon_layout.addWidget(password_icon)
        
        password_row.addWidget(password_icon_container, 0, Qt.AlignVCenter)

        self.admin_password_input = QLineEdit()
        self.admin_password_input.setPlaceholderText("Enter Password")
        self.admin_password_input.setEchoMode(QLineEdit.Password)
        self.admin_password_input.setStyleSheet(self.input_style())
        self.admin_password_input.setMinimumHeight(40)
        self.admin_password_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        password_row.addWidget(self.admin_password_input, 1)
        
        admin_form_layout.addLayout(password_row)

        # ========== LOGIN BUTTON (ISOLATED) ==========
        admin_form_layout.addSpacing(8)  # Extra spacing before button
        
        self.admin_login_btn = QPushButton("LOGIN")
        self.admin_login_btn.setStyleSheet(self.button_style())
        self.admin_login_btn.clicked.connect(self.validate_admin_login)
        admin_form_layout.addWidget(self.admin_login_btn)

        admin_form_layout.addStretch()
        stacked_layout.addWidget(self.admin_form)

        tab_layout.addWidget(self.stacked_widget, 1)
        layout.addWidget(self.tab_widget, 1)

        # Footer
        footer_label = QLabel("© 2025 Zing Technologies. All rights reserved.")
        footer_label.setFont(QFont("Arial", 8))
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #999999; background-color: transparent;")
        layout.addWidget(footer_label)

        # Show employee login by default
        self.show_employee_login()

    def show_employee_login(self):
        """Show employee login form"""
        self.employee_form.show()
        self.admin_form.hide()
        self.employee_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f4f8;
                color: #1a5da8;
                border: 1px solid #1a5da8;
                border-radius: 0px;
                padding: 10px;
                border-right: none;
            }
            QPushButton:hover {
                background-color: #d0e8f2;
            }
        """)
        self.admin_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #666666;
                border: 1px solid #d0d0d0;
                border-radius: 0px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #eeeeee;
            }
        """)
        self.name_input.setFocus()

    def show_admin_login(self):
        """Show admin login form"""
        self.employee_form.hide()
        self.admin_form.show()
        self.admin_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8f4f8;
                color: #1a5da8;
                border: 1px solid #1a5da8;
                border-radius: 0px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #d0e8f2;
            }
        """)
        self.employee_tab_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #666666;
                border: 1px solid #d0d0d0;
                border-radius: 0px;
                padding: 10px;
                border-right: none;
            }
            QPushButton:hover {
                background-color: #eeeeee;
            }
        """)
        self.admin_name_input.setFocus()

    def input_style(self):
        return """
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 10px;
                background-color: #f8f9fa;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #1a5da8;
                background-color: #ffffff;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
        """

    def combo_style(self):
        return """
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 10px;
                background-color: #f8f9fa;
                color: #333;
                min-height: 18px;
            }
            QComboBox:focus {
                border: 2px solid #1a5da8;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
                selection-background-color: #1a5da8;
                color: #333;
            }
        """

    def button_style(self):
        return """
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
            QPushButton:pressed {
                background-color: #0f3860;
            }
        """

    def validate_employee_login(self):
        name = self.name_input.text().strip()
        emp_id = self.id_input.text().strip()

        if not name or not emp_id:
            self.show_error_popup("Please enter the Username or ID correctly!")
            return

        self.login_success.emit(name, emp_id, "Employee")


    def validate_admin_login(self):
        name = self.admin_name_input.text().strip()
        designation = self.designation_combo.currentText()
        password = self.admin_password_input.text().strip()

        # Validation: Check all fields are filled
        if not name:
            self.show_error_popup("Please enter the Admin Name!")
            return

        if designation == "Select Designation":
            self.show_error_popup("Please select a Designation!")
            return

        if not password:
            self.show_error_popup("Please enter the Password!")
            return

        
        # ===== META ADMIN LOGIN =====
        if designation == "Meta Admin":

            # MASTER META ADMIN
            if name.lower() == "master" and password == "admin560017":
                self.login_success.emit("MASTER_META", "META_ADMIN_MASTER", "Meta Admin")
                return

            # NORMAL META ADMIN (self-reset)
            if password == "admin123":

                # 🔑 Fetch real designation from DB
                conn = sqlite3.connect(ADMIN_DB_PATH)
                conn.execute("PRAGMA foreign_keys = ON")
                cur = conn.cursor()
                cur.execute(
                    "SELECT designation FROM admins WHERE admin_name=? AND designation!='_default'",
                    (name,)
                )
                row = cur.fetchone()
                conn.close()

                if not row:
                    self.show_error_popup(
                        "Admin designation not found. Login once as normal admin first."
                    )
                    return

                real_designation = row[0]

                self.login_success.emit(name, "META_ADMIN_SELF", real_designation)
                return


            self.show_error_popup("Invalid Meta Admin credentials!")
            return


        # ===== OTHER ADMINS (DB-BASED PASSWORD CHECK) =====
        conn = sqlite3.connect(ADMIN_DB_PATH)
        cur = conn.cursor()

        # 1️⃣ Check admin-specific password
        cur.execute(
            "SELECT password FROM admins WHERE admin_name=? AND designation=?",
            (name, designation)
        )
        row = cur.fetchone()

        # 2️⃣ Fallback to designation default password
        if not row:
            cur.execute(
                "SELECT password FROM admins WHERE admin_name=? AND designation=?",
                ("_default", designation)
            )
            row = cur.fetchone()

        conn.close()

        import hashlib
        hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()

        if row and hashed == row[0]:

            # ✅ ENSURE ADMIN EXISTS IN DB (CRITICAL FIX)
            conn = sqlite3.connect(ADMIN_DB_PATH)
            cur = conn.cursor()

            if designation != "Meta Admin":
                cur.execute(
                    "INSERT OR IGNORE INTO admins (admin_name, designation, password) VALUES (?, ?, ?)",
                    (name, designation, row[0])
                )


            conn.commit()
            conn.close()

            self.login_success.emit(name, designation, designation)
            return




        self.show_error_popup("Invalid Admin credentials!")



    def show_error_popup(self, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Login Error")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.exec_()

    def show_feature_coming_soon(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Admin Login")
        msg_box.setText("Admin Login - Feature Coming Soon")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()
        # Clear the admin form after showing the message
        self.admin_name_input.clear()
        self.designation_combo.setCurrentIndex(0)
        self.admin_password_input.clear()

# ============================================================================
# SCREEN 2: CONNECTION SCREEN (MODIFIED WITH OSCILLOSCOPE DISCOVERY)
# ============================================================================
class ConnectionWorker(QThread):
    """
    Worker thread for device discovery.
    Integrates real oscilloscope VISA discovery into existing placeholder flow.
    """
    log_signal = pyqtSignal(str, bool)
    connection_complete = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.oscilloscope_connection = None
        self.oscilloscope_found = False
        self.microcontroller_found = False
        self.claimed_visa_resources = set()

        self.device_status = {
            "PSU (Power Supply)": False,
            "Audio Precision Analyzer": False,
            "Microcontroller": False,
            "DMM (Digital Multimeter)": False,
            "Oscilloscope": False,
        }

    def run(self):
        """
        Execute device discovery sequence.
        Real VISA discovery for oscilloscope, placeholders for other devices.
        """
        time.sleep(0.5)
        
        # ===== POWER SUPPLY (REAL VISA DISCOVERY) =====
        self.log_signal.emit("Searching for power supply…", False)
        self.discover_power_supply()
        
        # ===== DMM =====
        self.log_signal.emit("Searching for DMM…", False)
        time.sleep(1.5)
        self.log_signal.emit("DMM found at 192.168.1.11 ✓", False)
        self.device_status["DMM (Digital Multimeter)"] = True

        
        # ===== OSCILLOSCOPE (REAL VISA DISCOVERY) =====
        self.log_signal.emit("Searching for oscilloscope…", False)
        self.discover_oscilloscope()
        
        # ===== APX 525 =====
        self.log_signal.emit("Searching for APX 525…", False)
        time.sleep(1.5)
        self.log_signal.emit("APX 525 found at 192.168.1.13 ✓", False)
        self.device_status["Audio Precision Analyzer"] = True

        
        # ===== MICROCONTROLLER =====
        self.log_signal.emit("Searching for Microcontroller…", False)
        self.discover_microcontroller()
        
        # All devices connected
        all_connected = all(self.device_status.values())
        self.connection_complete.emit(all_connected)

    def discover_power_supply(self):
        """
        Discover and connect to power supply (RIGOL DP832) via VISA.
        Searches for the PSU on available VISA resources and logs connection details.
        Emits log updates via signal.
        """
        try:
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            
            if not resources:
                self.log_signal.emit("No VISA resources found. Check PSU connection.", True)
                return
            
            # Target keywords for RIGOL DP832
            TARGET_ID_KEYWORDS = ["RIGOL", "DP832"]
            
            self.log_signal.emit("Scanning VISA resources for Power Supply...", False)
            
            for res in resources:
                try:
                    inst = rm.open_resource(res, timeout=3000)
                    try:
                        idn = inst.query("*IDN?").strip()
                    finally:
                        inst.close()
                    
                    # Check if this is a RIGOL DP832
                    if all(k in idn for k in TARGET_ID_KEYWORDS):
                        # Parse identification
                        parts = [p.strip() for p in idn.split(',')]
                        if len(parts) >= 4:
                            manufacturer = parts[0]
                            model = parts[1]
                            serial_number = parts[2]
                            firmware_version = parts[3]
                            
                            # Log detailed PSU information
                            self.log_signal.emit(
                                f"Power Supply found at {res} ✓",
                                False
                            )
                            self.device_status["PSU (Power Supply)"] = True
                            self.claimed_visa_resources.add(res)


                            self.log_signal.emit(
                                f"  Manufacturer: {manufacturer}",
                                False
                            )
                            self.log_signal.emit(
                                f"  Model: {model}",
                                False
                            )
                            self.log_signal.emit(
                                f"  Serial Number: {serial_number}",
                                False
                            )
                            self.log_signal.emit(
                                f"  Firmware Version: {firmware_version}",
                                False
                            )
                            
                            inst.close()
                            return
                    
                    inst.close()
                    
                except Exception:
                    pass
            
            # No PSU found
            self.log_signal.emit(
                "No RIGOL DP832 Power Supply detected. Check USB/LAN connection.",
                True
            )
            
        except Exception as e:
            self.log_signal.emit(
                f"Power Supply discovery error: {str(e)}",
                True
            )
                             
                             
                             
    def discover_oscilloscope(self):
        """
        Discover and connect to oscilloscope via VISA.
        Executes in worker thread (non-blocking UI).
        Emits log updates via signal.
        """
        try:
            self.oscilloscope_connection = OscilloscopeConnection()
            self.oscilloscope_connection.claimed_visa_resources = self.claimed_visa_resources

            
            # Attempt discovery and connection
            if self.oscilloscope_connection.discover_and_connect():
                # SUCCESS: Extract identification
                ident = self.oscilloscope_connection.get_identification()
                
                if ident:
                    # Log detailed identification
                    self.log_signal.emit(
                        f"Oscilloscope found at {self.oscilloscope_connection.resource_string} ✓",
                        False
                    )
                    self.log_signal.emit(
                        f"  Manufacturer: {ident.manufacturer}",
                        False
                    )
                    self.log_signal.emit(
                        f"  Model: {ident.model}",
                        False
                    )
                    self.log_signal.emit(
                        f"  Serial Number: {ident.serial_number}",
                        False
                    )
                    self.log_signal.emit(
                        f"  Firmware Version: {ident.firmware_version}",
                        False
                    )
                    self.oscilloscope_found = True
                    self.device_status["Oscilloscope"] = True

                else:
                    self.log_signal.emit(
                        "Oscilloscope connected but identification parsing failed",
                        True
                    )
            else:
                # FAILURE: Log error but continue flow
                self.log_signal.emit(
                    "No oscilloscope found on VISA resources. Check connections.",
                    True
                )
                self.oscilloscope_found = False
        
        except Exception as e:
            # Catch any unexpected errors and log gracefully
            self.log_signal.emit(
                f"Oscilloscope discovery error: {str(e)}",
                True
            )
            self.oscilloscope_found = False

    def discover_microcontroller(self):
        """
        Discover and verify microcontroller connection via serial/UART.
        Uses CRC-8 validation from hellllo.py.
        Executes in worker thread (non-blocking UI).
        Emits log updates via signal.
        """
        try:
            import serial
            import serial.tools.list_ports
            
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
                self.log_signal.emit(
                    "No serial ports found. Microcontroller not detected.",
                    True
                )
                self.microcontroller_found = False
                return
            
            # Filter for STM32 devices
            stm32_ports = []
            for port in ports:
                if any(k in port.description for k in ["Bluetooth", "Wireless", "Intel", "Modem"]):
                    continue
                
                if (port.vid == 0x0483 or "STM32" in port.description or 
                    "ST-Link" in port.description or "USB Serial" in port.description):
                    stm32_ports.append(port.device)
            
            if not stm32_ports:
                self.log_signal.emit(
                    "No STM32 device detected on serial ports.",
                    True
                )
                self.microcontroller_found = False
                return
            
            # Attempt connection to each STM32 port
            for port in stm32_ports:
                try:
                    ser = serial.Serial(port, 115200, timeout=2)
                    self.log_signal.emit(f"Attempting connection to {port}...", False)
                    # ===== FORCE DESYNC BEFORE SYNC (CRITICAL FIX) =====
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()

                    self.log_signal.emit(
                        f"Port {port}: Sending forced desync before sync...",
                        False
                    )

                    desync_frame = bytearray([0x02, 0x35, 0x02, 0xFF, 0xE0, 0x56, 0x03, 0x0D])
                    ser.write(desync_frame)
                    time.sleep(0.3)

                    # Read & ignore desync response (MCU may or may not reply)
                    _ = ser.read(8)

                    
                    # Send Ready command (from hellllo.py)
                    frame = bytearray([0x02, 0x35, 0x02, 0xFF, 0x00, 0x98, 0x03, 0x0D])
                    ser.write(frame)
                    time.sleep(0.5)
                    
                    # Read response
                    response = ser.read(8)
                    
                    if len(response) == 8:
                        start, slave, length, command, state, recv_crc, end, eof = response
                        
                        # Validate frame format
                        if (start == 0x02 and slave == 0x35 and length == 0x02 and 
                            end == 0x03 and eof == 0x0D):
                            
                            # Validate CRC
                            crc_data = [start, slave, length, command, state, end, eof]
                            calc_crc = crc8(crc_data)
                            
                            if calc_crc == recv_crc:
                                # Check handshake response
                                if command == 0xFF and state == 0x01:
                                    self.log_signal.emit(
                                        f"Microcontroller found at {port} ✓",
                                        False
                                    )
                                    self.log_signal.emit(
                                        f"  Protocol: STM32 UART (115200 baud)",
                                        False
                                    )
                                    self.log_signal.emit(
                                        f"  Handshake: Successful",
                                        False
                                    )
                                    ser.close()
                                    self.microcontroller_found = True
                                    self.device_status["Microcontroller"] = True

                                    return
                                elif command == 0xFF and state == 0xFF:
                                    self.log_signal.emit(
                                        f"Port {port}: MCU already synced. Performing desync → resync...",
                                        True
                                    )

                                    # ---------------- DESYNC ----------------
                                    desync_frame = bytearray([0x02, 0x35, 0x02, 0xFF, 0xE0, 0x56, 0x03, 0x0D])
                                    ser.write(desync_frame)
                                    time.sleep(0.4)

                                    desync_resp = ser.read(8)
                                    if len(desync_resp) != 8:
                                        self.log_signal.emit(
                                            f"Port {port}: Desync response invalid",
                                            True
                                        )
                                        continue

                                    ds, dsl, dl, dc, dst, dcrc, de, deof = desync_resp
                                    if not (ds == 0x02 and dsl == 0x35 and dl == 0x02 and
                                            dc == 0xFF and dst == 0xE1 and de == 0x03 and deof == 0x0D):
                                        self.log_signal.emit(
                                            f"Port {port}: Desync failed",
                                            True
                                        )
                                        continue

                                    self.log_signal.emit(
                                        f"Port {port}: Desync successful. Re-attempting sync...",
                                        False
                                    )

                                    # ---------------- RESYNC ----------------
                                    sync_frame = bytearray([0x02, 0x35, 0x02, 0xFF, 0x00, 0x98, 0x03, 0x0D])
                                    ser.write(sync_frame)
                                    time.sleep(0.4)

                                    response = ser.read(8)
                                    if len(response) != 8:
                                        self.log_signal.emit(
                                            f"Port {port}: No response after resync",
                                            True
                                        )
                                        continue

                                    s, sl, l, c, st, crc_r, e, eof = response
                                    crc_calc = crc8([s, sl, l, c, st, e, eof])

                                    if (s == 0x02 and sl == 0x35 and l == 0x02 and
                                        c == 0xFF and st == 0x01 and crc_calc == crc_r):

                                        self.log_signal.emit(
                                            f"Microcontroller re-synced successfully at {port} ✓",
                                            False
                                        )
                                        ser.close()
                                        self.microcontroller_found = True
                                        self.device_status["Microcontroller"] = True
                                        return

                                elif command == 0xFF and state == 0xFE:
                                    self.log_signal.emit(
                                        f"Port {port}: Data Error from controller",
                                        True
                                    )
                            else:
                                self.log_signal.emit(
                                    f"Port {port}: CRC validation failed",
                                    True
                                )
                        else:
                            self.log_signal.emit(
                                f"Port {port}: Invalid frame format",
                                True
                            )
                    
                    ser.close()
                    
                except (serial.SerialException, serial.PortNotOpenError):
                    continue
                except Exception as e:
                    try:
                        ser.close()
                    except:
                        pass
                    continue
            
            # No valid microcontroller found
            self.log_signal.emit(
                "Microcontroller not found or handshake failed on available ports.",
                True
            )
            self.microcontroller_found = False
            
        except ImportError:
            self.log_signal.emit(
                "pyserial library not installed. Cannot detect microcontroller.",
                True
            )
            self.microcontroller_found = False
        except Exception as e:
            self.log_signal.emit(
                f"Microcontroller discovery error: {str(e)}",
                True
            )
            self.microcontroller_found = False

class ConnectionScreen(QMainWindow):
    connection_success = pyqtSignal()
    test_selection_requested = pyqtSignal()

    def __init__(self, user_name, user_id):
        super().__init__()
        self.user_name = user_name
        self.user_id = user_id
        self.logger = Logger(LOGS_DIR / f"connection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        # Stores logs only for the latest CONNECT click (not retries)
        self.detailed_logger = Logger()
        # Holds per-peripheral failure diagnostics (detailed logs only)
        self.failure_details = {}


        self.oscilloscope_connection = None
        
        self.setWindowTitle("HAL - Connection")
        self.setGeometry(100, 100, 700, 800)
        self.setStyleSheet("background-color: #ffffff;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(str(RESOURCES_DIR / "hal_logo.png"))
        if logo_pixmap.isNull():
            logo_pixmap = QPixmap(150, 75)
            logo_pixmap.fill(QColor("#1a5da8"))
        else:
            logo_pixmap = logo_pixmap.scaledToWidth(150, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Connect Button
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setMinimumHeight(45)
        self.connect_btn.setMaximumWidth(250)
        self.connect_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.connect_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
        """)
        self.connect_btn.clicked.connect(self.start_connection)
        
        button_container = QHBoxLayout()
        button_container.addStretch()
        button_container.addWidget(self.connect_btn)
        button_container.addStretch()
        layout.addLayout(button_container)

        # Log Panel
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(300)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                background-color: white;
                color: #333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.log_text)

        # View Logs Button
        self.view_logs_btn = QPushButton("VIEW LOGS")
        self.view_logs_btn.setMinimumHeight(40)
        self.view_logs_btn.setMaximumWidth(250)
        self.view_logs_btn.setVisible(False)
        self.view_logs_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.view_logs_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.view_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.view_logs_btn.clicked.connect(self.show_detailed_logs)
        
        
        self.print_logs_btn = QPushButton("PRINT LOG")
        self.print_logs_btn.setMinimumHeight(40)
        self.print_logs_btn.setMaximumWidth(250)
        self.print_logs_btn.setVisible(False)
        self.print_logs_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.print_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                padding: 8px;    
                text-align: center;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.print_logs_btn.clicked.connect(self.print_logs_pdf)
        logs_btn_container = QHBoxLayout()
        logs_btn_container.addStretch()
        logs_btn_container.addWidget(self.view_logs_btn)
        logs_btn_container.addWidget(self.print_logs_btn)
        logs_btn_container.addStretch()
        layout.addLayout(logs_btn_container)


        self.worker = None
        self.connection_successful = False
        self.retry_count = 0
        self.max_retries = 3
        self.retry_seconds = 10
        self.retry_timer = QTimer()
        self.retry_timer.timeout.connect(self.retry_countdown)
        
    def start_connection(self):
        self.log_text.clear()
        self.retry_count = 0

        # 🔄 Refresh detailed logs ONLY on CONNECT
        self.detailed_logger.clear()

        self.start_actual_connection()





    def start_retry_cycle(self):
        self.connect_btn.setEnabled(False)
        self.retry_seconds = 10
        self.connect_btn.setText("Retrying in 10s")
        self.retry_timer.start(1000)

    def retry_countdown(self):
        self.retry_seconds -= 1

        if self.retry_seconds > 0:
            self.connect_btn.setText(f"Retrying in {self.retry_seconds}s")
        else:
            self.retry_timer.stop()
            self.retry_count += 1

            if self.retry_count > self.max_retries:
                self.connect_btn.setText("CONNECT")
                self.connect_btn.setEnabled(True)
                self.log_text.append("Max retries reached.")
                return

            self.log_text.append(f"Retry attempt {self.retry_count}/{self.max_retries}")
            self.start_actual_connection()


    def start_actual_connection(self):
        self.worker = ConnectionWorker()
        self.worker.log_signal.connect(self.append_log)
        self.worker.connection_complete.connect(self.on_connection_complete)
        self.worker.start()

    def append_log(self, message, error):
        if error:
            self.log_text.setTextColor(QColor("#d32f2f"))
        else:
            self.log_text.setTextColor(QColor("#1b5e20"))
        
        self.log_text.append(message)
        self.logger.log(message, error)
        self.detailed_logger.log(message, error)

        # -------- CAPTURE FAILURE CONTEXT (DETAILED LOGS ONLY) --------
        if error:
            if "Power Supply" in message:
                self.failure_details["PSU (Power Supply)"] = {
                    "Reason": message,
                    "Checks": [
                        "Verify USB/LAN cable connection",
                        "Check VISA driver installation",
                        "Confirm DP832 is powered ON",
                        "Run *IDN? manually via VISA test tool"
                    ]
                }

            elif "oscilloscope" in message.lower():
                self.failure_details["Oscilloscope"] = {
                    "Reason": message,
                    "Checks": [
                        "Check VISA resource visibility",
                        "Ensure oscilloscope is not claimed by another process",
                        "Verify SCPI *IDN? response",
                        "Confirm supported manufacturer"
                    ]
                }

            elif "DMM" in message:
                self.failure_details["DMM (Digital Multimeter)"] = {
                    "Reason": message,
                    "Checks": [
                        "Verify network/IP configuration",
                        "Ping device IP",
                        "Check DMM LAN settings"
                    ]
                }

            elif "APX" in message:
                self.failure_details["Audio Precision Analyzer"] = {
                    "Reason": message,
                    "Checks": [
                        "Verify APx software running",
                        "Check Ethernet connection",
                        "Confirm analyzer IP address"
                    ]
                }

            elif "Microcontroller" in message or "STM32" in message:
                self.failure_details["Microcontroller"] = {
                    "Reason": message,
                    "Checks": [
                        "Verify COM port availability",
                        "Check baud rate (115200)",
                        "Ensure correct firmware loaded",
                        "Check CRC / handshake response"
                    ]
                }


        self.log_text.setTextColor(QColor("#333"))

    def on_connection_complete(self, success):
        self.connect_btn.setEnabled(True)
        
        # Store oscilloscope connection reference for future use
        if self.worker and self.worker.oscilloscope_connection:
            self.oscilloscope_connection = self.worker.oscilloscope_connection
            self.device_status = self.worker.device_status

        
        if success:
            self.log_text.setTextColor(QColor("#1b5e20"))
            self.log_text.append("All devices connected successfully")
            self.logger.log("All devices connected successfully", False)
            self.connection_successful = True
            QTimer.singleShot(1500, self.proceed_to_test_selection)
        else:
            self.view_logs_btn.setVisible(True)
            self.print_logs_btn.setVisible(True)
            self.log_text.setTextColor(QColor("#d32f2f"))
            self.log_text.append("Connection failed. Retrying…")
            self.start_retry_cycle()



    def proceed_to_test_selection(self):
        self.test_selection_requested.emit()
        self.hide()
        

    def show_detailed_logs(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Detailed Connection Logs")
        dlg.setMinimumSize(700, 500)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
        """)

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ===== TITLE =====
        title = QLabel("Connection Log Details")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #1a5da8;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        meta = QLabel(
            f"""
            <b>User:</b> {self.user_name}<br>
            <b>User ID:</b> {self.user_id}<br>
            <b>Connection Time:</b> {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}
            """
        )
        meta.setStyleSheet("color:#374151; font-size:10pt;")
        meta.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(meta)


        # ===== LOG VIEW (SCROLLABLE) =====
        log_view = QTextEdit()
        log_view.setReadOnly(True)
        log_view.setFont(QFont("Consolas", 10))
        log_view.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d7e2;
                border-radius: 6px;
                background-color: #f9fafb;
                padding: 10px;
                color: #111827;
            }
        """)

        # Populate logs
        logs = self.detailed_logger.get_logs()

        if logs:
            for idx, entry in enumerate(logs, start=1):
                color = "#d32f2f" if entry["error"] else "#1b5e20"

                log_view.append(
                    f"<span style='color:{color};'>"
                    f"<b>{idx:02d}.</b> {entry['text']}"
                    f"</span>"
                )

                # -------- EXPAND FAILURE DETAILS (DETAILED LOGS ONLY) --------
                if entry["error"]:
                    for device, info in self.failure_details.items():
                        if info["Reason"] in entry["text"]:
                            log_view.append(
                                f"<span style='color:#374151; margin-left:16px;'>"
                                f"&nbsp;&nbsp;➤ <b>{device} Failure Details</b>"
                                f"</span>"
                            )

                            log_view.append(
                                f"<span style='color:#6b7280; margin-left:32px;'>"
                                f"&nbsp;&nbsp;&nbsp;Reason: {info['Reason']}"
                                f"</span>"
                            )

                            for check in info["Checks"]:
                                log_view.append(
                                    f"<span style='color:#6b7280; margin-left:48px;'>"
                                    f"&nbsp;&nbsp;&nbsp;• {check}"
                                    f"</span>"
                                )

        else:
            log_view.setText("No logs available for this connection attempt.")

        log_view.setTextColor(QColor("#111827"))
        main_layout.addWidget(log_view, 1)

        # ===== BUTTON ROW =====
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 36)
        close_btn.setFont(QFont("Arial", 9, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
        """)
        close_btn.clicked.connect(dlg.accept)

        btn_row.addWidget(close_btn)
        main_layout.addLayout(btn_row)

        dlg.exec_()


    def print_logs_pdf(self):
        pdf_path = LOGS_PDF_DIR / f"connection_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        export_logs_to_pdf(self.logger.get_logs(), pdf_path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))


        QMessageBox.information(
            self,
            "Log Exported",
            f"Log PDF saved to:\n{pdf_path}"
        )



# ============================================================================
# SCREEN 3: TEST SELECTION SCREEN
# ============================================================================
class TestSelectionScreen(QMainWindow):
    full_test_requested = pyqtSignal()
    unit_test_requested = pyqtSignal()
    equipment_self_test_requested = pyqtSignal()
    test_reports_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HAL - Test Selection")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(900, 700)
        self.setStyleSheet("background-color: #f5f5f5;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(40)

        # Logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(str(RESOURCES_DIR / "hal_logo.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaledToWidth(150, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Title Section
        title_label = QLabel("Select Test Mode")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1a5da8; background-color: transparent; letter-spacing: 0.5px;")
        layout.addWidget(title_label)

        # Grid Layout Container for 2x2 buttons
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setHorizontalSpacing(24)
        grid_layout.setVerticalSpacing(24)

        # =========================
        # ROW 0, COL 0: RUN FULL TEST BUTTON (PRIMARY)
        # =========================
        full_test_btn = QPushButton()
        full_test_btn.setMinimumSize(280, 200)
        full_test_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        full_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
                border: none;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
            QPushButton:pressed {
                background-color: #0f3860;
            }
        """)

        full_layout = QVBoxLayout(full_test_btn)
        full_layout.setContentsMargins(0, 0, 0, 0)
        full_layout.setSpacing(16)
        full_layout.setAlignment(Qt.AlignCenter)

        full_icon = QLabel()
        full_icon.setPixmap(QPixmap(str(RESOURCES_DIR / "full_test.png")).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        full_icon.setAlignment(Qt.AlignCenter)
        full_icon.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        full_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        full_text = QLabel("RUN FULL TEST")
        full_text.setFont(QFont("Arial", 12, QFont.Bold))
        full_text.setStyleSheet("color: white; background-color: transparent; border: none; padding: 0px; margin: 0px; letter-spacing: 0.3px;")
        full_text.setAlignment(Qt.AlignCenter)
        full_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        full_layout.addStretch()
        full_layout.addWidget(full_icon, 0, Qt.AlignCenter)
        full_layout.addWidget(full_text, 0, Qt.AlignCenter)
        full_layout.addStretch()

        full_test_btn.clicked.connect(lambda: self.full_test_requested.emit())
        grid_layout.addWidget(full_test_btn, 0, 0)

        # =========================
        # ROW 0, COL 1: RUN SINGLE TEST BUTTON (SECONDARY)
        # =========================
        unit_test_btn = QPushButton()
        unit_test_btn.setMinimumSize(280, 200)
        unit_test_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        unit_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #d5d8dc;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #b0b8c1;
            }
            QPushButton:pressed {
                background-color: #f0f2f5;
                border: 2px solid #a0a8b1;
            }
        """)

        unit_layout = QVBoxLayout(unit_test_btn)
        unit_layout.setContentsMargins(0, 0, 0, 0)
        unit_layout.setSpacing(16)
        unit_layout.setAlignment(Qt.AlignCenter)

        unit_icon = QLabel()
        unit_icon.setPixmap(QPixmap(str(RESOURCES_DIR / "unit_test.png")).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        unit_icon.setAlignment(Qt.AlignCenter)
        unit_icon.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        unit_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        unit_text = QLabel("RUN SINGLE TEST")
        unit_text.setFont(QFont("Arial", 12, QFont.Bold))
        unit_text.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px; letter-spacing: 0.3px;")
        unit_text.setAlignment(Qt.AlignCenter)
        unit_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        unit_layout.addStretch()
        unit_layout.addWidget(unit_icon, 0, Qt.AlignCenter)
        unit_layout.addWidget(unit_text, 0, Qt.AlignCenter)
        unit_layout.addStretch()

        unit_test_btn.clicked.connect(lambda: self.unit_test_requested.emit())
        grid_layout.addWidget(unit_test_btn, 0, 1)

        # =========================
        # ROW 1, COL 0: CALIBRATIONS BUTTON (SECONDARY)
        # =========================
        calibrations_btn = QPushButton()
        calibrations_btn.setMinimumSize(280, 200)
        calibrations_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        calibrations_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #d5d8dc;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #b0b8c1;
            }
            QPushButton:pressed {
                background-color: #f0f2f5;
                border: 2px solid #a0a8b1;
            }
        """)

        calib_layout = QVBoxLayout(calibrations_btn)
        calib_layout.setContentsMargins(0, 0, 0, 0)
        calib_layout.setSpacing(16)
        calib_layout.setAlignment(Qt.AlignCenter)

        calib_icon = QLabel()
        calib_icon.setPixmap(QPixmap(str(RESOURCES_DIR / "calibrations.png")).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ) if QPixmap(str(RESOURCES_DIR / "calibrations.png")).isNull() == False else QPixmap(64, 64))
        calib_icon.setAlignment(Qt.AlignCenter)
        calib_icon.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        calib_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        calib_text = QLabel("EQUIPMENT SELF TEST")
        calib_text.setFont(QFont("Arial", 12, QFont.Bold))
        calib_text.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px; letter-spacing: 0.3px;")
        calib_text.setAlignment(Qt.AlignCenter)
        calib_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        calib_layout.addStretch()
        calib_layout.addWidget(calib_icon, 0, Qt.AlignCenter)
        calib_layout.addWidget(calib_text, 0, Qt.AlignCenter)
        calib_layout.addStretch()

        # Placeholder functionality for calibrations
        calibrations_btn.clicked.connect(self.on_calibrations_clicked)
        grid_layout.addWidget(calibrations_btn, 1, 0)

        # =========================
        # ROW 1, COL 1: TEST REPORTS BUTTON (SECONDARY)
        # =========================
        reports_btn = QPushButton()
        reports_btn.setMinimumSize(280, 200)
        reports_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        reports_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #d5d8dc;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border: 2px solid #b0b8c1;
            }
            QPushButton:pressed {
                background-color: #f0f2f5;
                border: 2px solid #a0a8b1;
            }
        """)

        reports_layout = QVBoxLayout(reports_btn)
        reports_layout.setContentsMargins(0, 0, 0, 0)
        reports_layout.setSpacing(16)
        reports_layout.setAlignment(Qt.AlignCenter)

        reports_icon = QLabel()
        reports_icon.setPixmap(QPixmap(str(RESOURCES_DIR / "test_reports.png")).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ) if QPixmap(str(RESOURCES_DIR / "test_reports.png")).isNull() == False else QPixmap(64, 64))
        reports_icon.setAlignment(Qt.AlignCenter)
        reports_icon.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        reports_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        reports_text = QLabel("PRINT REPORT")
        reports_text.setFont(QFont("Arial", 12, QFont.Bold))
        reports_text.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px; letter-spacing: 0.3px;")
        reports_text.setAlignment(Qt.AlignCenter)
        reports_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        reports_layout.addStretch()
        reports_layout.addWidget(reports_icon, 0, Qt.AlignCenter)
        reports_layout.addWidget(reports_text, 0, Qt.AlignCenter)
        reports_layout.addStretch()

        # Placeholder functionality for reports
        reports_btn.clicked.connect(self.on_reports_clicked)
        grid_layout.addWidget(reports_btn, 1, 1)

        # Set equal column and row stretches
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)

        layout.addWidget(grid_container, 1)
        layout.addStretch()

    def on_calibrations_clicked(self):
        self.equipment_self_test_requested.emit()

    def on_reports_clicked(self):
        pdf_files = list(PDF_TEST_REPORTS_DIR.glob("*.pdf"))

        if not pdf_files:
            # Improved "No Reports" dialog with better styling
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("No Test Reports")
            msg_box.setText("No test reports found")
            msg_box.setInformativeText(
                "There are currently no PDF reports available.\n\n"
                "Run tests and generate reports to see them here."
            )
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #ffffff;
                border: none;
            }

            QMessageBox QFrame {
                border: none;
                background-color: transparent;
            }

            QMessageBox QLabel {
                color: #374151;
                background-color: transparent;
            }

            QMessageBox QLabel#qt_msgbox_informativelabel {
                color: #666666;
                font-size: 9pt;
                background-color: transparent;
            }

            QMessageBox QPushButton {
                min-width: 80px;
                min-height: 32px;
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }

            QMessageBox QPushButton:hover {
                background-color: #154a8a;
            }
        """)
            msg_box.exec_()
            return

        # PDFs exist → ask application to open Test Reports
        self.test_reports_requested.emit()


# ============================================================================
class TestReportsScreen(QMainWindow):
    return_to_test_selection = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HAL - Test Reports")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet("background-color: #f5f5f5;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ===== HEADER BAR (MATCHING IMAGE UI) =====
        header_frame = QFrame()
        header_frame.setFixedHeight(64)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
            }
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(12)

        # Back Button (Left)
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(110, 36)
        back_btn.setFont(QFont("Arial", 9, QFont.Bold))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #fbc02d;
                color: #000000;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f9a825;
            }
        """)
        back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(back_btn, 0, Qt.AlignLeft)

        # Center Title
        title = QLabel("Test Reports (PDF)")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1a5da8;")
        header_layout.addWidget(title, 1)

        # Right spacer (keeps title perfectly centered)
        header_layout.addSpacing(110)

        layout.addWidget(header_frame)



        # ===== LIST =====
        self.report_list = QListWidget()
        self.report_list.setFont(QFont("Arial", 10))
        self.report_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #d0d7e2;
                border-radius: 6px;
            }
        """)


        layout.addWidget(self.report_list)
        self.load_reports()


    # -------------------------------------------------
    def load_reports(self):
        self.report_list.clear()

        if not PDF_TEST_REPORTS_DIR.exists():
            QMessageBox.warning(self, "Error", "PDF reports directory not found.")
            return

        pdf_files = sorted(PDF_TEST_REPORTS_DIR.glob("*.pdf"))

        if not pdf_files:
            QMessageBox.information(self, "No Test Reports", "No test reports found.")
            return

        for pdf in pdf_files:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 48))

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 6, 12, 6)
            row_layout.setSpacing(10)

            # 📄 File name (clickable)
            name_label = QLabel(pdf.name)
            name_label.setFont(QFont("Arial", 10))
            name_label.setStyleSheet("""
                QLabel {
                    color: #1a5da8;
                }
                QLabel:hover {
                    text-decoration: underline;
                }
            """)
            name_label.setCursor(Qt.PointingHandCursor)
            name_label.mousePressEvent = lambda _, p=pdf: self.open_pdf_path(p)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # 🖨 Print button
            print_btn = QPushButton("Print")
            print_btn.setFixedSize(90, 32)
            print_btn.setFont(QFont("Arial", 9, QFont.Bold))
            print_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a5da8;
                    color: white;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #154a8a;
                }
            """)
            print_btn.clicked.connect(lambda _, p=pdf: self.print_pdf(p))

            row_layout.addWidget(name_label)
            row_layout.addWidget(print_btn)

            self.report_list.addItem(item)
            self.report_list.setItemWidget(item, row_widget)
    # -------------------------------------------------
    def open_pdf_path(self, pdf_path: Path):
        """Open PDF in default system viewer"""
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))
    
    def print_pdf(self, pdf_path: Path):
        """Open print preview for a specific PDF"""
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(
            lambda _: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(pdf_path))
            )
        )
        preview.exec_()

    # -------------------------------------------------
    def on_back_clicked(self):
        self.return_to_test_selection.emit()
        self.close()

# ============================================================================
# SCREEN 3.5: EQUIPMENT SELF CHECK SCREEN (LAYOUT & STYLING FIXES)
# ============================================================================

class EquipmentSelfCheckScreen(QMainWindow):
    """
    Equipment Self Check Screen - displays device connectivity and self-test status.
    Opens as a separate page from TestSelectionScreen.
    Visually matches the provided reference image with HAL color palette.
    """
    return_to_test_selection = pyqtSignal()

    def __init__(self, device_status: dict):
        super().__init__()
        self.device_status = device_status
        self.setWindowTitle("HAL - Equipment Self Check")
        self.setGeometry(100, 100, 1200, 900)
        self.setMinimumSize(1000, 750)
        self.setStyleSheet("background-color: #f5f5f5;")

        self.logger = Logger(LOGS_DIR / f"equipment_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(20)

        # =====================================================================
        # HEADER BAR – Logo, Title, Status Badge, Back Button
        # =====================================================================
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 0px;
            }
        """)
        header_frame.setFixedHeight(70)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(20)
        header_layout.setAlignment(Qt.AlignVCenter)

        # Back Button (LEFT)
        back_btn = QPushButton("← Back")
        back_btn.setMinimumHeight(40)
        back_btn.setMinimumWidth(120)
        back_btn.setMaximumWidth(120)
        back_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        back_btn.setFont(QFont("Arial", 9, QFont.Bold))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #fbc02d;
                color: #000000;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f9a825;
            }
            QPushButton:pressed {
                background-color: #f57f17;
            }
        """)
        back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(back_btn, 0, Qt.AlignLeft | Qt.AlignVCenter)

        # Logo + Title (CENTER-LEFT)
        logo_label = QLabel()
        logo_pixmap = QPixmap(str(RESOURCES_DIR / "hal_logo.png"))
        if logo_pixmap.isNull():
            logo_pixmap = QPixmap(80, 40)
            logo_pixmap.fill(QColor("#1a5da8"))
        else:
            logo_pixmap = logo_pixmap.scaledToWidth(80, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header_layout.addWidget(logo_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        title_label = QLabel("Equipment Self Check")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setStyleSheet("color: #1a1a1a; background-color: transparent; border: none; padding: 0px;")
        header_layout.addWidget(title_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        header_layout.addStretch()

        # Status Badge (CENTER-RIGHT) – Green "All Devices Detected"
        status_badge = QFrame()
        status_badge.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border: 1px solid #4caf50;
                border-radius: 4px;
                padding: 0px;
            }
        """)
        status_badge.setFixedHeight(36)
        badge_layout = QHBoxLayout(status_badge)
        badge_layout.setContentsMargins(12, 0, 12, 0)
        badge_layout.setSpacing(8)

        status_dot = QLabel("●")
        status_dot.setFont(QFont("Arial", 12))
        status_dot.setStyleSheet("color: #4caf50; background-color: transparent; border: none;")
        status_dot.setAlignment(Qt.AlignCenter)
        badge_layout.addWidget(status_dot, 0, Qt.AlignVCenter)

        all_ok = all(self.device_status.values())
        status_text = QLabel(
            "All Devices Detected" if all_ok else "Some Devices Not Detected"
        )
        status_dot.setStyleSheet(
            "color: #4caf50;" if all_ok else "color: #d32f2f;"
        )

        status_text.setFont(QFont("Arial", 10, QFont.Bold))
        status_text.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        status_text.setStyleSheet("color: #2e7d32; background-color: transparent; border: none; letter-spacing: 0.2px;")
        badge_layout.addWidget(status_text, 1, Qt.AlignVCenter)

        header_layout.addWidget(status_badge, 0, Qt.AlignRight | Qt.AlignVCenter)

        main_layout.addWidget(header_frame, 0)

        # =====================================================================
        # SCROLLABLE CONTENT AREA
        # =====================================================================
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
            QScrollBar:vertical {
                width: 8px;
                background-color: #f5f5f5;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #f5f5f5;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

        # =====================================================================
        # DEVICE CARDS LAYOUT – Strict 3-column grid with centered second row
        # =====================================================================
        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(0)

        # Define device data
        devices = [
            {
                "name": "PSU (Power Supply)",
                "port": "USB",
                "connected": self.device_status.get("PSU (Power Supply)", False),
            },
            {
                "name": "Audio Precision Analyzer",
                "port": "APIX | USB",
                "connected": self.device_status.get("Audio Precision Analyzer", False),
            },
            {
                "name": "Microcontroller",
                "port": "COM",
                "connected": self.device_status.get("Microcontroller", False),
            },
            {
                "name": "DMM (Digital Multimeter)",
                "port": "USB",
                "connected": self.device_status.get("DMM (Digital Multimeter)", False),
            },
            {
                "name": "Oscilloscope",
                "port": "USB",
                "connected": self.device_status.get("Oscilloscope", False),
            },
        ]


        # ===== ROW 1: 3 Cards (PSU, Audio Precision, Microcontroller) =====
        row1_layout = QHBoxLayout()
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(20)  # Horizontal spacing between cards

        for idx in range(3):
            card = self._create_device_card(devices[idx])
            row1_layout.addWidget(card, 1)  # Equal stretch factor (1) for equal widths

        cards_layout.addLayout(row1_layout)
        cards_layout.addSpacing(20)  # Vertical spacing between rows

        # ===== ROW 2: 2 Cards (DMM, Oscilloscope) – Centered =====
        row2_layout = QHBoxLayout()
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(20)  # Horizontal spacing between cards

        # Left stretch to center the cards
        row2_layout.addStretch(1)

        for idx in range(2):
            card = self._create_device_card(devices[3 + idx])
            row2_layout.addWidget(card, 1)  # Equal stretch factor for equal widths

        # Right stretch to center the cards
        row2_layout.addStretch(1)

        cards_layout.addLayout(row2_layout)
        cards_layout.addStretch()

        scroll_layout.addWidget(cards_container)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area, 1)

        # =====================================================================
        # BOTTOM ACTION BUTTONS – 2 centered buttons with equal width
        # =====================================================================
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(12)
        bottom_layout.addStretch()

        run_all_btn = QPushButton("Run Full Test")
        run_all_btn.setMinimumHeight(44)
        run_all_btn.setMinimumWidth(260)
        run_all_btn.setMaximumWidth(260)
        run_all_btn.setFont(QFont("Arial", 10, QFont.Bold))
        run_all_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        run_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: bold;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
            QPushButton:pressed {
                background-color: #0d3f1f;
            }
        """)
        run_all_btn.clicked.connect(self.on_run_all_self_tests)
        bottom_layout.addWidget(run_all_btn)

        generate_report_btn = QPushButton("Generate Report")
        generate_report_btn.setMinimumHeight(44)
        generate_report_btn.setMinimumWidth(260)
        generate_report_btn.setMaximumWidth(260)
        generate_report_btn.setFont(QFont("Arial", 10, QFont.Bold))
        generate_report_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        generate_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: bold;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #1054b8;
            }
        """)
        generate_report_btn.clicked.connect(self.on_generate_report)
        bottom_layout.addWidget(generate_report_btn)

        bottom_layout.addStretch()

        main_layout.addLayout(bottom_layout, 0)

    def _create_device_card(self, device: dict) -> QFrame:
        """
        Create a professional device card with device icon, connected status, port info,
        self-test result, and Run/View buttons.
        
        All cards have consistent: height, padding, border radius, and spacing.
        Device name stays on a single line.
        """
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 0px;
            }
        """)
        card.setMinimumHeight(280)  # Fixed height for consistency
        card.setMaximumHeight(280)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)  # Consistent padding
        layout.setSpacing(12)

        # ===== Device Icon + Name Row =====
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Device Icon (48x48 px)
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        
        # Map device names to image files
        device_icon_map = {
            "PSU (Power Supply)": "power_supply.png",
            "Audio Precision Analyzer": "audio.png",
            "Microcontroller": "micro.png",
            "DMM (Digital Multimeter)": "dmm.png",
            "Oscilloscope": "oscope.png",
        }
        
        icon_filename = device_icon_map.get(device["name"], "")
        if icon_filename:
            icon_path = RESOURCES_DIR / icon_filename
            icon_pixmap = QPixmap(str(icon_path))
            if not icon_pixmap.isNull():
                icon_pixmap = icon_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(icon_pixmap)
        
        header_layout.addWidget(icon_label, 0, Qt.AlignTop | Qt.AlignLeft)

        # Device Name (Title) – Single line, no wrap
        name_label = QLabel(device["name"])
        name_label.setFont(QFont("Arial", 11, QFont.Bold))
        name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_label.setStyleSheet("color: #1a1a1a; background-color: transparent; border: none; padding: 0px;")
        name_label.setWordWrap(False)  # Prevent wrapping
        name_label.setFixedHeight(24)  # Fixed height for alignment
        header_layout.addWidget(name_label, 1, Qt.AlignLeft | Qt.AlignVCenter)

        layout.addLayout(header_layout)

        # ===== Connection Status (Green dot + text) =====
        status_container = QHBoxLayout()
        status_container.setContentsMargins(0, 0, 0, 0)
        status_container.setSpacing(6)

        status_dot = QLabel("●")
        status_dot.setFont(QFont("Arial", 10))
        status_dot.setAlignment(Qt.AlignCenter)
        status_dot.setFixedWidth(12)
        status_container.addWidget(status_dot, 0)

        if device["connected"]:
            status_text = QLabel("Connected")
            status_dot.setStyleSheet("color: #4caf50; background-color: transparent; border: none;")
            status_color = "#2e7d32"
        else:
            status_text = QLabel("Not Connected")
            status_dot.setStyleSheet("color: #d32f2f; background-color: transparent; border: none;")
            status_color = "#d32f2f"

        status_text.setFont(QFont("Arial", 9))
        status_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        status_text.setStyleSheet(f"color: {status_color}; background-color: transparent; border: none;")
        status_container.addWidget(status_text, 1)

        layout.addLayout(status_container)

        # ===== Port/VISA Information =====
        port_label = QLabel(device["port"])
        port_label.setFont(QFont("Arial", 9))
        port_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        port_label.setStyleSheet("color: #666666; background-color: transparent; border: none; padding: 0px; margin: 0px;")
        layout.addWidget(port_label)

        # ===== Self-Test Result Label =====
        test_result = QLabel("Self-Test Result: Pending")
        test_result.setFont(QFont("Arial", 9))
        test_result.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        test_result.setStyleSheet("color: #f57c00; background-color: transparent; border: none; padding: 0px; margin: 0px;")
        test_result.setObjectName(f"test_result_{device['name']}")  # For later updates
        layout.addWidget(test_result)

        layout.addSpacing(8)

        # ===== Action Buttons (Run Self Test + View Logs) =====
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        run_btn = QPushButton("Run Self Test")
        if not device["connected"]:
            run_btn.setEnabled(False)
            run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #b0bec5;
                    color: #ffffff;
                    border-radius: 3px;
                }
            """)

        run_btn.setMinimumHeight(36)
        run_btn.setFont(QFont("Arial", 9, QFont.Bold))
        run_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        run_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
            QPushButton:pressed {
                background-color: #0f3860;
            }
        """)
        run_btn.clicked.connect(lambda: self.on_run_device_self_test(device["name"]))
        button_layout.addWidget(run_btn)

        view_btn = QPushButton("View Logs")
        view_btn.setMinimumHeight(36)
        view_btn.setFont(QFont("Arial", 9, QFont.Bold))
        view_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        view_btn.clicked.connect(lambda: self.on_view_device_logs(device["name"]))
        button_layout.addWidget(view_btn)

        layout.addLayout(button_layout)

        return card

    def on_run_device_self_test(self, device_name: str):
        """Handle individual device self-test (placeholder)"""
        msg = f"Starting self-test for {device_name}..."
        self.logger.log(msg, False)
        
        # Placeholder: Log action and update UI label
        QMessageBox.information(
            self,
            "Self-Test Started",
            f"Self-test for {device_name} initiated.\n\n(Placeholder functionality - wire to hardware later)",
            QMessageBox.Ok
        )

    def on_view_device_logs(self, device_name: str):
        """Handle view logs for individual device (placeholder)"""
        msg = f"Viewing logs for {device_name}..."
        self.logger.log(msg, False)
        
        # Placeholder: Show logs dialog
        QMessageBox.information(
            self,
            f"Logs - {device_name}",
            f"Device logs for {device_name}:\n\n[Log entries would appear here]\n\n(Placeholder functionality)",
            QMessageBox.Ok
        )

    def on_run_all_self_tests(self):
        """Handle run self-test for all devices (placeholder)"""
        self.logger.log("Running self-tests for all devices...", False)
        
        QMessageBox.information(
            self,
            "Self-Test Suite Started",
            "Self-tests for all devices initiated.\n\n(Placeholder functionality - wire to hardware later)",
            QMessageBox.Ok
        )

    def on_generate_report(self):
        """Handle generate self-check report (placeholder)"""
        self.logger.log("Generating equipment self-check report...", False)
        
        QMessageBox.information(
            self,
            "Report Generated",
            "Equipment self-check report successfully generated.\n\n(Placeholder functionality - wire to report generation logic later)",
            QMessageBox.Ok
        )

    def on_back_clicked(self):
        """Return to Test Selection Screen"""
        self.logger.log("Returning to Test Selection from Equipment Self Check", False)
        self.return_to_test_selection.emit()
        self.close()

# ============================================================================
# CALIBRATION POPUP
# ============================================================================
class CalibrationPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Message")
        self.setGeometry(200, 200, 500, 450)
        self.setModal(True)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Please set the ICS and Radio Knobs")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Knob Image
        knob_label = QLabel()
        knob_pixmap = QPixmap(str(RESOURCES_DIR / "knob.png"))
        if knob_pixmap.isNull():
            knob_pixmap = QPixmap(150, 150)
            knob_pixmap.fill(QColor("#e0e0e0"))
        else:
            knob_pixmap = knob_pixmap.scaledToWidth(150, Qt.SmoothTransformation)
        knob_label.setPixmap(knob_pixmap)
        knob_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(knob_label)

        # Instructions
        instructions = QLabel(
            "• Turn the ICS knobs fully CW.\n"
            "• Set MIC Mode to HOT.\n"
            "• Turn TX SEL knobs fully CCW and to the OUT position.\n"
            "• Turn RX SEL knobs fully CCW."
        )
        instructions.setFont(QFont("Arial", 10))
        instructions.setAlignment(Qt.AlignLeft)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addStretch()

        # Acknowledge Button
        ack_btn = QPushButton("I Acknowledge")
        ack_btn.setMinimumHeight(40)
        ack_btn.setMaximumWidth(200)
        ack_btn.setFont(QFont("Arial", 11, QFont.Bold))
        ack_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        ack_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
        """)
        ack_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ack_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
# ============================================================================
# TEST COMPLETION MODAL
# ============================================================================
class TestCompletionModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Report")
        self.setGeometry(300, 300, 450, 250)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Success Icon/Title
        title = QLabel("✓ Test report successfully generated.")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1b5e20;")
        layout.addWidget(title)

        info_text = QLabel(
            "You can either click on 'Save' to store the report or 'Terminate'\nto close it."
        )
        info_text.setFont(QFont("Arial", 10))
        info_text.setAlignment(Qt.AlignCenter)
        info_text.setWordWrap(True)
        layout.addWidget(info_text)

        layout.addStretch()

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(36)
        save_btn.setMinimumWidth(100)
        save_btn.setFont(QFont("Arial", 10, QFont.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
        """)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        terminate_btn = QPushButton("Terminate")
        terminate_btn.setMinimumHeight(36)
        terminate_btn.setMinimumWidth(100)
        terminate_btn.setFont(QFont("Arial", 10, QFont.Bold))
        terminate_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        terminate_btn.clicked.connect(self.reject)
        button_layout.addWidget(terminate_btn)

        layout.addLayout(button_layout)

# ============================================================================
# ABORT TEST CONFIRMATION POPUP
# ============================================================================
class AbortTestConfirmationPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Abort Test?")
        self.setGeometry(400, 300, 450, 200)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Warning Title
        title = QLabel("Abort Test?")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #d32f2f;")
        layout.addWidget(title)

        # Message
        message = QLabel(
            "A test is currently running. Do you want to abort it and return to the Test Selection screen?"
        )
        message.setFont(QFont("Arial", 10))
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        layout.addWidget(message)

        layout.addStretch()

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        abort_go_back_btn = QPushButton("Yes, Abort & Go Back")
        abort_go_back_btn.setMinimumHeight(36)
        abort_go_back_btn.setMinimumWidth(140)
        abort_go_back_btn.setFont(QFont("Arial", 10, QFont.Bold))
        abort_go_back_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        abort_go_back_btn.clicked.connect(self.accept)
        button_layout.addWidget(abort_go_back_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setFont(QFont("Arial", 10, QFont.Bold))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

# ============================================================================
# NEW: DISCONNECT RESULT POPUP
# ============================================================================
class DisconnectResultDialog(QDialog):
    def __init__(self, success: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Disconnect" if success else "Disconnect Failed")
        self.setModal(True)
        self.setFixedSize(360, 220)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border: none;
            }
            QLabel {
                color: #374151;
                background-color: transparent;
            }
            QPushButton {
                min-height: 34px;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton#primary {
                background-color: #1a5da8;
                color: white;
                border: none;
            }
            QPushButton#primary:hover {
                background-color: #154a8a;
            }
            QPushButton#danger {
                background-color: #d32f2f;
                color: white;
                border: none;
            }
            QPushButton#danger:hover {
                background-color: #b71c1c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        icon_label = QLabel("✓" if success else "⚠")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Arial", 28, QFont.Bold))
        icon_label.setStyleSheet("color: #1b5e20; background-color: transparent;" if success else "color: #d32f2f; background-color: transparent;")
        layout.addWidget(icon_label)

        title = QLabel("Disconnected successfully." if success else "Disconnect failed.")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("background-color: transparent;")
        layout.addWidget(title)

        desc = QLabel(
            "You can now return to the Connection screen."
            if success else
            "Please check the cable or device and try disconnecting again."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("background-color: transparent;")
        layout.addWidget(desc)

        layout.addStretch()

        btn = QPushButton("OK" if success else "Retry")
        btn.setObjectName("primary" if success else "danger")
        btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)


# ============================================================================
# SCREEN 4: FULL TEST SCREEN (MODIFIED HEADER WITH BACK BUTTON)
# ============================================================================
class FullTestScreen(QMainWindow):
    test_completed = pyqtSignal()
    return_to_test_selection = pyqtSignal()
    return_to_connection = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HAL - Full Test")
        self.setGeometry(50, 50, 1400, 950)
        self.setMinimumSize(QSize(1000, 750))
        self.setStyleSheet("background-color: #f5f5f5;")

        self.logger = Logger(LOGS_DIR / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.test_running = False
        self.voltage_value = 28.0
        self.config_locked = False
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)
        

        # =====================================================================
        # TOP HEADER BAR – Clean gradient-like appearance
        # =====================================================================
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 0px;
            }
        """)
        top_bar.setFixedHeight(60)
        
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)
        top_layout.setSpacing(16)
        
        # Logo + Title on the left
        logo_label = QLabel()
        logo_pixmap = QPixmap(str(RESOURCES_DIR / "hal_logo.png"))
        if logo_pixmap.isNull():
            logo_pixmap = QPixmap(100, 50)
            logo_pixmap.fill(QColor("#1a5da8"))
        else:
            logo_pixmap = logo_pixmap.scaledToWidth(100, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_layout.addWidget(logo_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        title_label = QLabel("HAL – Full Test")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setStyleSheet("color: #1a1a1a; background-color: transparent; border: none; padding: 0px;")
        top_layout.addWidget(title_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        top_layout.addStretch()

        # Back button (NEW) – positioned before Power Supply label
        self.back_btn = QPushButton("Back")
        self.back_btn.setMinimumHeight(40)
        self.back_btn.setMinimumWidth(120)
        self.back_btn.setMaximumWidth(120)
        self.back_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.back_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.back_btn.setIconSize(QSize(18, 18))
        back_icon = QPixmap(str(RESOURCES_DIR / "backarr.png"))
        self.back_btn.setIcon(QIcon(back_icon))
        self.back_btn.setText("Back ")  # Added space after the text
        if not back_icon.isNull():
            self.back_btn.setIcon(QIcon(back_icon))
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #fbc02d;
                color: #000000;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f9a825;
            }
            QPushButton:pressed {
                background-color: #f57f17;
            }
        """)
        self.back_btn.clicked.connect(self.on_back_clicked)
        top_layout.addWidget(self.back_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Power Supply info in center-right (after Back button)
        self.voltage_label = QLabel("Power Supply: 28.0 V")
        self.voltage_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.voltage_label.setAlignment(Qt.AlignCenter)
        self.voltage_label.setStyleSheet("""
            QLabel {
                color: #1a5da8;
                padding: 6px 12px;
                background-color: #f0f4f8;
                border-radius: 4px;
            }
        """)
        self.voltage_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_layout.addWidget(self.voltage_label, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Disconnect button on the right
        disconnect_btn = QPushButton()
        disconnect_btn.setMinimumHeight(40)
        disconnect_btn.setMinimumWidth(165)
        disconnect_btn.setMaximumWidth(160)
        disconnect_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        disconnect_btn.setFont(QFont("Arial", 9, QFont.Bold))
        disconnect_btn.setIconSize(QSize(18, 18))
        disconnect_icon = QPixmap(str(RESOURCES_DIR / "disconnect.png"))
        if not disconnect_icon.isNull():
            disconnect_btn.setIcon(QIcon(disconnect_icon))
        disconnect_btn.setText("DISCONNECT")
        disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:pressed {
                background-color: #a71a1a;
            }
        """)
        disconnect_btn.clicked.connect(self.disconnect_and_return)
        top_layout.addWidget(disconnect_btn, 0, Qt.AlignRight | Qt.AlignVCenter)
        
        main_layout.addWidget(top_bar, 0)

        # =====================================================================
        # MAIN SCROLLABLE CONTENT AREA
        # =====================================================================
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
            QScrollBar:vertical {
                width: 8px;
                background-color: #f5f5f5;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background-color: #f5f5f5;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(16)

        # ==========================================================
        # CONTROL PANEL CONTAINER – Professional styled frame
        # ==========================================================
        control_panel_frame = QFrame()
        control_panel_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        control_panel_frame.setFrameShape(QFrame.StyledPanel)
        control_panel_layout = QVBoxLayout(control_panel_frame)
        control_panel_layout.setContentsMargins(0, 0, 0, 0)
        control_panel_layout.setSpacing(0)

        # Control Panel Header Bar (Blue strip)
        header_bar = QFrame()
        header_bar.setStyleSheet("""
            QFrame {
                background-color: #1a5da8;
                border-radius: 6px 6px 0px 0px;
            }
        """)
        header_bar.setFixedHeight(44)
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(0)

        header_label = QLabel("Control Panel")
        header_label.setFont(QFont("Arial", 11, QFont.Bold))
        header_label.setStyleSheet("color: #ffffff; letter-spacing: 0.3px; background-color: transparent; border: none; padding: 0px;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        control_panel_layout.addWidget(header_bar)

        # Configuration grid inside the frame
        config_container = QWidget()
        config_container.setStyleSheet("background-color: #ffffff;")
        config_grid = QGridLayout(config_container)
        config_grid.setContentsMargins(24, 20, 24, 20)
        config_grid.setHorizontalSpacing(48)
        config_grid.setVerticalSpacing(16)

        # ==========================================
        # LEFT SECTION: ALHx Configuration
        # ==========================================
        
        # ALHx Model Label (plain text, no background)
        alhx_model_label = QLabel("ALHx Model:")
        alhx_model_label.setFont(QFont("Arial", 9, QFont.Bold))
        alhx_model_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        alhx_model_label.setMinimumWidth(120)
        alhx_model_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.alhx_combo = QComboBox()
        self.alhx_combo.addItems(["ALH1", "ALH2", "ALH3"])
        self.alhx_combo.setMinimumHeight(32)
        self.alhx_combo.setFont(QFont("Arial", 9))
        self.alhx_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 5px 8px;
                background-color: #ffffff;
                color: #333;
            }
            QComboBox:focus {
                border: 1px solid #1a5da8;
                background-color: #fafbfc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox:disabled {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                color: #999999;
            }
        """)

        config_grid.addWidget(alhx_model_label, 0, 0, Qt.AlignRight | Qt.AlignVCenter)
        config_grid.addWidget(self.alhx_combo, 0, 1, Qt.AlignLeft | Qt.AlignVCenter)

        # ALHx Serial Number Label (plain text, no background)
        alhx_sn_label = QLabel("ALHx Serial Number:")
        alhx_sn_label.setFont(QFont("Arial", 9, QFont.Bold))
        alhx_sn_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        alhx_sn_label.setMinimumWidth(120)
        alhx_sn_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.alhx_serial = QLineEdit()
        self.alhx_serial.setPlaceholderText("SN-XXXXXXX")
        self.alhx_serial.setMinimumHeight(32)
        self.alhx_serial.setFont(QFont("Arial", 9))
        self.alhx_serial.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 5px 8px;
                background-color: #ffffff;
                color: #333;
            }
            QLineEdit:focus {
                border: 1px solid #1a5da8;
                background-color: #fafbfc;
            }
            QLineEdit:disabled {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                color: #999999;
            }
        """)

        config_grid.addWidget(alhx_sn_label, 1, 0, Qt.AlignRight | Qt.AlignVCenter)
        config_grid.addWidget(self.alhx_serial, 1, 1, Qt.AlignLeft | Qt.AlignVCenter)

        # Select Module (ALHx) Label (plain text, no background)
        mod_alhx_label = QLabel("Select MOD:")
        mod_alhx_label.setFont(QFont("Arial", 9, QFont.Bold))
        mod_alhx_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mod_alhx_label.setMinimumWidth(120)
        mod_alhx_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.mod_combo = QComboBox()
        self.mod_combo.addItems(["02", "03", "04", "05"])
        self.mod_combo.setMinimumHeight(32)
        self.mod_combo.setFont(QFont("Arial", 9))
        self.mod_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 5px 8px;
                background-color: #ffffff;
                color: #333;
            }
            QComboBox:focus {
                border: 1px solid #1a5da8;
                background-color: #fafbfc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox:disabled {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                color: #999999;
            }
        """)

        config_grid.addWidget(mod_alhx_label, 2, 0, Qt.AlignRight | Qt.AlignVCenter)
        config_grid.addWidget(self.mod_combo, 2, 1, Qt.AlignLeft | Qt.AlignVCenter)

        # ==========================================
        # RIGHT SECTION: Junction Box Configuration
        # ==========================================

        # Junction Box Label (plain text, no background)
        jbox_label = QLabel("Junction Box:")
        jbox_label.setFont(QFont("Arial", 9, QFont.Bold))
        jbox_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        jbox_label.setMinimumWidth(120)
        jbox_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.jbox_combo = QComboBox()
        self.jbox_combo.addItems(["No Junction Box", "ALH4"])
        self.jbox_combo.setMinimumHeight(32)
        self.jbox_combo.setFont(QFont("Arial", 9))
        self.jbox_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 5px 8px;
                background-color: #ffffff;
                color: #333;
            }
            QComboBox:focus {
                border: 1px solid #1a5da8;
                background-color: #fafbfc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox:disabled {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                color: #999999;
            }
        """)
        self.jbox_combo.currentTextChanged.connect(self.on_jbox_selection_changed)

        config_grid.addWidget(jbox_label, 0, 2, Qt.AlignRight | Qt.AlignVCenter)
        config_grid.addWidget(self.jbox_combo, 0, 3, Qt.AlignLeft | Qt.AlignVCenter)

        # Junction Box Serial Number Label (plain text, no background)
        jbox_sn_label = QLabel("Serial Number:")
        jbox_sn_label.setFont(QFont("Arial", 9, QFont.Bold))
        jbox_sn_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        jbox_sn_label.setMinimumWidth(120)
        jbox_sn_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.jbox_serial = QLineEdit()
        self.jbox_serial.setPlaceholderText("SN-XXXXXXX")
        self.jbox_serial.setMinimumHeight(32)
        self.jbox_serial.setFont(QFont("Arial", 9))
        self.jbox_serial.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 5px 8px;
                background-color: #ffffff;
                color: #333;
            }
            QLineEdit:focus {
                border: 1px solid #1a5da8;
                background-color: #fafbfc;
            }
            QLineEdit:disabled {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                color: #999999;
            }
        """)

        config_grid.addWidget(jbox_sn_label, 1, 2, Qt.AlignRight | Qt.AlignVCenter)
        config_grid.addWidget(self.jbox_serial, 1, 3, Qt.AlignLeft | Qt.AlignVCenter)

        # Select Module (Junction Box) Label (plain text, no background)
        mod_jbox_label = QLabel("Select MOD:")
        mod_jbox_label.setFont(QFont("Arial", 9, QFont.Bold))
        mod_jbox_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mod_jbox_label.setMinimumWidth(120)
        mod_jbox_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.mod_jbox_combo = QComboBox()
        self.mod_jbox_combo.addItems(["00", "01"])
        self.mod_jbox_combo.setMinimumHeight(32)
        self.mod_jbox_combo.setFont(QFont("Arial", 9))
        self.mod_jbox_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                padding: 5px 8px;
                background-color: #ffffff;
                color: #333;
            }
            QComboBox:focus {
                border: 1px solid #1a5da8;
                background-color: #fafbfc;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox:disabled {
                background-color: #e8e8e8;
                border: 1px solid #d0d0d0;
                color: #999999;
            }
        """)

        config_grid.addWidget(mod_jbox_label, 2, 2, Qt.AlignRight | Qt.AlignVCenter)
        config_grid.addWidget(self.mod_jbox_combo, 2, 3, Qt.AlignLeft | Qt.AlignVCenter)

        # Set column stretches for balanced layout
        config_grid.setColumnStretch(0, 0)
        config_grid.setColumnStretch(1, 0)
        config_grid.setColumnStretch(2, 0)
        config_grid.setColumnStretch(3, 0)

        control_panel_layout.addWidget(config_container)

        scroll_layout.addWidget(control_panel_frame)

        # ==========================================================
        # LOCK BUTTON – Centered below Control Panel
        # ==========================================================
        lock_btn_layout = QHBoxLayout()
        lock_btn_layout.setContentsMargins(0, 0, 0, 0)
        lock_btn_layout.addStretch()

        self.lock_btn = QPushButton("Lock On")
        self.lock_btn.setFixedSize(200, 40)
        self.lock_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.lock_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
            QPushButton:pressed {
                background-color: #0f3860;
            }
        """)
        self.lock_btn.clicked.connect(self.toggle_lock_configuration)

        lock_btn_layout.addWidget(self.lock_btn)
        lock_btn_layout.addStretch()

        scroll_layout.addLayout(lock_btn_layout)

        # ==========================================================
        # ACTION BUTTONS ROW – Four equal buttons with icons
        # ==========================================================
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(12)

        self.start_btn = QPushButton("▶ Start Test")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
            QPushButton:pressed {
                background-color: #0d3f1f;
            }
        """)
        self.start_btn.clicked.connect(self.start_test)
        action_layout.addWidget(self.start_btn)

        abort_btn = QPushButton("◯ Abort Test")
        abort_btn.setMinimumHeight(44)
        abort_btn.setFont(QFont("Arial", 10, QFont.Bold))
        abort_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        abort_btn.setIconSize(QSize(18, 18))
        abort_icon = QPixmap(str(RESOURCES_DIR / "abort.png"))
        if not abort_icon.isNull():
            abort_btn.setIcon(QIcon(abort_icon))
        abort_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:pressed {
                background-color: #a71a1a;
            }
        """)
        abort_btn.clicked.connect(self.abort_test)
        action_layout.addWidget(abort_btn)

        graphs_btn = QPushButton("📊 Graphs")
        graphs_btn.setMinimumHeight(44)
        graphs_btn.setFont(QFont("Arial", 10, QFont.Bold))
        graphs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        graphs_btn.setIconSize(QSize(18, 18))
        graphs_btn.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e65100;
            }
            QPushButton:pressed {
                background-color: #d44d00;
            }
        """)
        action_layout.addWidget(graphs_btn)

        view_logs_btn = QPushButton("📋 View Logs")
        view_logs_btn.setMinimumHeight(44)
        view_logs_btn.setFont(QFont("Arial", 10, QFont.Bold))
        view_logs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        view_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #1054b8;
            }
        """)
        action_layout.addWidget(view_logs_btn)

        scroll_layout.addLayout(action_layout)

        # ==========================================================
        # TESTING CONTROLS / RUNNING LOGS SECTION
        # ==========================================================
        logs_container_frame = QFrame()
        logs_container_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
        """)
        logs_container_layout = QVBoxLayout(logs_container_frame)
        logs_container_layout.setContentsMargins(20, 16, 20, 16)
        logs_container_layout.setSpacing(12)

        logs_title = QLabel("Running Logs:")
        logs_title.setFont(QFont("Arial", 10, QFont.Bold))
        logs_title.setStyleSheet("""
            QLabel {
                color: #374151;
                font-weight: 600;
                letter-spacing: 0.2px;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
        """)
        logs_container_layout.addWidget(logs_title, 0)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(240)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                background-color: #fafbfc;
                color: #333;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        logs_container_layout.addWidget(self.log_text, 1)

        scroll_layout.addWidget(logs_container_frame)

        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area, 1)

        # Voltage Monitor Timer
        self.voltage_timer = QTimer()
        self.voltage_timer.timeout.connect(self.update_voltage)

        # Initialize junction box dependent state
        self.on_jbox_selection_changed(self.jbox_combo.currentText())

    def on_back_clicked(self):
        """Handle Back button click – check if test is running."""
        if self.test_running:
            # Show abort confirmation dialog
            confirmation = AbortTestConfirmationPopup(self)
            if confirmation.exec_() == QDialog.Accepted:
                # User confirmed abort
                self.abort_test_internal()
                self.return_to_test_selection.emit()
            # else: User clicked Cancel, stay on screen
        else:
            # No test running – immediately return
            self.return_to_test_selection.emit()

    def on_jbox_selection_changed(self, text):
        """Handle Junction Box selection change to enable/disable dependent fields."""
        is_no_junction_box = (text == "No Junction Box")
        self.jbox_serial.setEnabled(not is_no_junction_box)
        self.mod_jbox_combo.setEnabled(not is_no_junction_box)

    def toggle_lock_configuration(self):
        """Toggle lock/unlock configuration"""
        if self.config_locked:
            self.unlock_configuration()
        else:
            self.lock_configuration()

    def lock_configuration(self):
        self.config_locked = True
        self.mod_combo.setEnabled(False)
        self.alhx_combo.setEnabled(False)
        self.alhx_serial.setEnabled(False)
        self.jbox_combo.setEnabled(False)
        self.jbox_serial.setEnabled(False)
        self.mod_jbox_combo.setEnabled(False)
        self.lock_btn.setText("Unlock")
        self.logger.log("Configuration locked", False)

    def unlock_configuration(self):
        self.config_locked = False
        self.mod_combo.setEnabled(True)
        self.alhx_combo.setEnabled(True)
        self.alhx_serial.setEnabled(True)
        self.jbox_combo.setEnabled(True)
        # Re-apply junction box dependent state
        self.on_jbox_selection_changed(self.jbox_combo.currentText())
        self.lock_btn.setText("Lock On")
        self.logger.log("Configuration unlocked", False)

    def start_test(self):
        calibration = CalibrationPopup(self)
        if calibration.exec_() == QDialog.Accepted:
            self.test_running = True
            self.logger.log("Calibration acknowledged - Starting test initialization", False)
            self.log_text.clear()
            self.run_initialization()
            self.voltage_timer.start(10000)

    def run_initialization(self):
        self.append_log("AUTOMATION INITIALIZATION", False)
        self.append_log("1. LOCAL/REMOTE (S23) → LOCAL", False)
        self.logger.log("# WRITE RELAY LOGIC HERE", False)
        time.sleep(0.5)
        
        self.append_log("2. LOAD (S31) → 600 OHM", False)
        self.logger.log("# WRITE AUTOMATION LOGIC HERE", False)
        time.sleep(0.5)
        
        self.append_log("3. All switches DOWN", False)
        self.logger.log("# WRITE SWITCH CONTROL LOGIC HERE", False)
        time.sleep(0.5)
        
        self.append_log("4. Power Supply set to 28V", False)
        self.append_log("   SCPI: VOLT 28.0", False)
        self.append_log("   Voltage readback: 28.0V ✓", False)
        self.logger.log("# WRITE SCPI LOGIC HERE", False)
        time.sleep(0.5)
        
        self.append_log("5. Live voltage monitoring enabled", False)
        self.append_log("INITIALIZATION COMPLETE - Test execution starting", False)
        self.append_log("# WRITE TEST LOGIC HERE", False)
        
        # Show completion modal after simulated test
        QTimer.singleShot(2000, self.show_test_completion)

    def append_log(self, message, error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if error:
            self.log_text.setTextColor(QColor("#d32f2f"))
        else:
            self.log_text.setTextColor(QColor("#1b5e20"))
        
        self.log_text.append(f"[{timestamp}] {message}")
        self.logger.log(message, error)
        self.log_text.setTextColor(QColor("#333"))

    def show_test_completion(self):
        completion = TestCompletionModal(self)
        completion.exec_()

    def update_voltage(self):
        self.voltage_label.setText(f"Power Supply: {self.voltage_value} V")
        
    def disconnect_and_return(self):
        """
        DISCONNECT button handler with handshake
        """
        success = self.perform_disconnect_handshake()

        self.voltage_timer.stop()

        # Improved popup UI
        dialog = DisconnectResultDialog(success, self)
        dialog.exec_()

        if success:
            self.close()
            self.return_to_connection.emit()
        # on failure, user can close dialog and stay on screen to retry

    def abort_test(self):
        """Abort test button handler"""
        self.abort_test_internal()

    def abort_test_internal(self):
        """Internal abort logic – reused by both abort button and back confirmation"""
        self.test_running = False
        self.voltage_timer.stop()
        self.unlock_configuration()
        self.append_log("Test aborted by user", False)

    def perform_disconnect_handshake(self) -> bool:
        """
        Perform disconnect handshake with microcontroller via serial.
        Reuses exact same serial scanning, CRC-8, and frame validation logic
        from ConnectionWorker.discover_microcontroller.
        """
        try:
            import serial
            import serial.tools.list_ports

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

            ports = list(serial.tools.list_ports.comports())
            stm32_ports = []

            for port in ports:
                if any(k in port.description for k in ["Bluetooth", "Wireless", "Intel", "Modem"]):
                    continue
                if (port.vid == 0x0483 or "STM32" in port.description or
                    "ST-Link" in port.description or "USB Serial" in port.description):
                    stm32_ports.append(port.device)

            for port in stm32_ports:
                try:
                    ser = serial.Serial(port, 115200, timeout=2)

                    start, slave, length = 0x02, 0x35, 0x02
                    command, state = 0xFF, 0xE0
                    end, eof = 0x03, 0x0D

                    crc_val = crc8([start, slave, length, command, state, end, eof])
                    frame = bytearray([start, slave, length, command, state, crc_val, end, eof])

                    ser.write(frame)
                    time.sleep(0.5)

                    response = ser.read(8)
                    ser.close()

                    if len(response) != 8:
                        continue

                    rs, rsl, rl, rc, rst, rcrc, re, reof = response
                    if (rs == 0x02 and rsl == 0x35 and rl == 0x02 and re == 0x03 and reof == 0x0D):
                        if crc8([rs, rsl, rl, rc, rst, re, reof]) == rcrc:
                            if rc == 0xFF and rst == 0xE1:
                                return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def closeEvent(self, event):
        try:
            if self.worker and self.worker.isRunning():
                self.worker.quit()
                self.worker.wait()
        except Exception:
            pass
        event.accept()


# ============================================================================
# MODIFIED MAIN APPLICATION WITH WINDOW REUSE
# ============================================================================
class HALApplication(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.main_window = None
        self.current_screen = None
        self.device_status = {}


    def show_login(self):
        """Show login screen"""
        if self.main_window is None:
            self.main_window = QMainWindow()
            self.main_window.setGeometry(100, 100, 550, 550)
            self.main_window.setWindowTitle("HAL")
            self.main_window.setWindowIcon(QIcon(str(RESOURCES_DIR / "wave.png")))
            self.main_window.setFixedSize(550, 550)
            self.main_window.setStyleSheet("background: linear-gradient(to bottom, #e0f7fa, #ffffff);")
        
        login_screen = LoginScreen()
        login_screen.login_success.connect(self.on_login_success)
        login_screen.show()
        self.current_screen = login_screen

    def on_login_success(self, name, emp_id, real_designation):
        # 🔒 NEVER close current screen during navigation
        if self.current_screen:
            self.current_screen.hide()

        if emp_id in ["META_ADMIN_SELF", "META_ADMIN_MASTER"]:
            from meta_admin_dashboard import MetaAdminDashboard
            self.current_screen = MetaAdminDashboard(
                name,
                emp_id,
                real_designation
            )

            # 🔑 ADD THIS LINE (CRITICAL)
            self.current_screen.restart_login.connect(self.show_login)

            self.current_screen.show()
            return


        if emp_id in ["Senior Test Engineer", "Manager", "General Manager"]:
            try:
                self.current_screen = self.show_admin_dashboard(name, emp_id)
            except Exception as e:
                QMessageBox.critical(self, "Critical Error", str(e))
            return

        try:
            self.current_screen = self.show_connection(name, emp_id)
        except Exception as e:
            QMessageBox.critical(self, "Critical Error", str(e))



            
    def show_admin_dashboard(self, admin_name, designation):
        from admin_dashboard import AdminDashboard
        dashboard = AdminDashboard(admin_name, designation)
        dashboard.logout_requested.connect(self.show_login)
        dashboard.show()
        return dashboard



    def show_connection(self, name, emp_id):
        """Show connection screen"""
        connection_screen = ConnectionScreen(name, emp_id)
        connection_screen.test_selection_requested.connect(self.on_connection_complete)
        connection_screen.show()
        return connection_screen

        

    def on_connection_complete(self):
        """Handle connection completion"""
        if self.current_screen:
            # SAVE DEVICE STATUS FROM CONNECTION SCREEN
            self.device_status = getattr(self.current_screen, "device_status", {})
            self.current_screen.close()

        self.show_test_selection()


    def show_test_selection(self):
        test_selection_screen = TestSelectionScreen()
        test_selection_screen.full_test_requested.connect(self.show_full_test)
        test_selection_screen.unit_test_requested.connect(self.show_unit_test)
        test_selection_screen.equipment_self_test_requested.connect(
            self.show_equipment_self_check
        )

        test_selection_screen.test_reports_requested.connect(
            self.show_test_reports
        )

        test_selection_screen.show()
        self.current_screen = test_selection_screen


    def show_full_test(self):
        """Show full test screen"""
        if self.current_screen:
            self.current_screen.close()
        full_test_screen = FullTestScreen()
        full_test_screen.return_to_test_selection.connect(self.on_full_test_return)
        full_test_screen.return_to_connection.connect(self.on_disconnect_return)
        full_test_screen.show()
        self.current_screen = full_test_screen
    def on_disconnect_return(self):
        if self.current_screen:
            self.current_screen.close()
        self.show_connection("", "")

    def on_full_test_return(self):
        """Handle return from full test screen"""
        if self.current_screen:
            self.current_screen.close()
        self.show_test_selection()
    def show_equipment_self_check(self):
        """Show Equipment Self Check screen"""
        if self.current_screen:
            self.current_screen.close()

        equipment_screen = EquipmentSelfCheckScreen(device_status=self.device_status)
        equipment_screen.return_to_test_selection.connect(self.show_test_selection)
        equipment_screen.show()

        self.current_screen = equipment_screen
    def show_test_reports(self):
        if self.current_screen:
            self.current_screen.close()

        reports_screen = TestReportsScreen()
        reports_screen.return_to_test_selection.connect(self.show_test_selection)
        reports_screen.show()

        self.current_screen = reports_screen

    def show_unit_test(self):
        """Show unit test screen (placeholder)"""
        pass

if __name__ == "__main__":
    init_admin_auth_db()
    app = HALApplication()
    app.show_login()
    sys.exit(app.exec_())

