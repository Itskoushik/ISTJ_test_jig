import re
from dialogs.calibration_popup import CalibrationPopup
from dialogs.test_completion_dialog import TestCompletionModal
from dialogs.abort_test_dialog import AbortTestConfirmationPopup
from dialogs.OperatorInfoPopup import OperatorInfoPopup
from dialogs.logs_viewer_dialog import LogsViewerDialog
from threading import Event
from core.logger import Logger
from core.paths import RESOURCES_DIR,TEST_LOGS_DIR,SESSION_FILE
from core.stm32_commands import STM32RelayController
from core.excel_logger import create_model_report,finalize_report,write_excel,has_any_fail_in_report,rename_report
import sys
from datetime import datetime as dt
from core.tuning_workflow import install_tuning_hooks, remove_tuning_hooks
import time
from datetime import datetime
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QDialog,
    QScrollArea, QSizePolicy, QGridLayout, QFrame, QMessageBox, QApplication
)
import pyvisa
from devices.apx_analyzer import generator_control,set_generator_scale_factor
from threading import Lock
from psu.psu_threads import VoltageMonitorThread
from devices.device_listeners import PSUListener, STM32Listener
from devices.device_types import DeviceType
from psu.psu_commands import PSUCommands
from tests import (
    microphone_audio,
    phones_audio,
    mic_limiter,
    vos_delay,
    voltage_measurement,
    resistance_measurement,
    transient,
    lighting_test,
    box_init,
    jb_seq_s
)
from core.stm32_commands import RelayStateTracker

class PSUAutomationThread(QThread):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen

    def run(self):
        self.screen.run_psu_automation()


class InitializationThread(QThread):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen

    def run(self):
        self.screen.run_initialization()

class AbortWorkerThread(QThread):
    finished = pyqtSignal()

    def __init__(self, screen, reset_relays: bool):
        super().__init__()
        self.screen = screen
        self.reset_relays = reset_relays

    def run(self):
        self.screen.abort_test_internal(self.reset_relays)
        self.finished.emit()
# ============================================================================
# SCREEN 4: Single TEST SCREEN (MODIFIED HEADER WITH BACK BUTTON)
# ============================================================================
class SingleTestScreen(QMainWindow):
    """
    Main test execution screen with PSU automation, configuration management,
    and live voltage/current monitoring.
    """
    test_completed = pyqtSignal()
    return_to_test_selection = pyqtSignal()
    return_to_connection = pyqtSignal()
    log_signal = pyqtSignal(str, bool) 
    show_popup_signal = pyqtSignal([str, str, object, str, object],
                               [str, str, object, str, object, bool],
                               [str, str, object, str, object, bool, int])
    update_popup_signal = pyqtSignal(str)
    completion_signal = pyqtSignal()
    _trigger_queue_signal = pyqtSignal()

    TEST_PRE_STEPS = {
    "microphone_audio": lambda self: None,
    "phones_audio": lambda self: None,
    "mic_limiter": lambda self: self.pre_step_mic_limiter_run(),
    "vos_delay": lambda self: self.pre_step_vos_delay_run_norm(),
    "voltage_measurement": lambda self: self.pre_step_voltage_measurement_run_norm(),
    "resistance_measurement": lambda self: self.pre_step_resistance_measurement_run_norm(),
    "transient": lambda self: self.pre_step_transient_run(),
    "lighting_test": lambda self: self.pre_step_lighting_test_run_norm(),
    }

    TEST_PRE_STEPS_stby = {
        "microphone_audio": lambda self: None,
        "phones_audio": lambda self: None,
        "mic_limiter": lambda self: None,
        "vos_delay": lambda self: self.pre_step_vos_delay_run_norm(),
        "voltage_measurement": lambda self: self.pre_step_voltage_measurement_run_stby(),
        "resistance_measurement": lambda self: self.pre_step_resistance_measurement_run_stby(),
        "transient": lambda self: None,
        "lighting_test": lambda self: self.pre_step_lighting_test_run_stby(),
    }
    TEST_MAP = {
    "microphone_audio": lambda self: microphone_audio.run_norm(self),
    "phones_audio": lambda self: phones_audio.run(self),
    "mic_limiter": lambda self: mic_limiter.run(self),
    "vos_delay": lambda self: vos_delay.run_norm(self),
    "voltage_measurement": lambda self: voltage_measurement.run_norm(self),
    "resistance_measurement": lambda self: resistance_measurement.run_norm(self),
    "transient": lambda self: transient.run(self),
    "lighting_test": lambda self: lighting_test.run_norm(self),
        }
    
    TEST_MAP_stby = {
    "microphone_audio": lambda self: microphone_audio.run_stby(self),
    "phones_audio": None,
    "mic_limiter": None,
    "vos_delay": lambda self: vos_delay.run_stby(self),
    "voltage_measurement": lambda self: voltage_measurement.run_stby(self),
    "resistance_measurement": lambda self: resistance_measurement.run_stby(self),
    "transient": None,
    "lighting_test": lambda self: lighting_test.run_stby(self),
}

    def pre_step_mic_limiter_run(self):
        self.log_signal.emit("disconnecting NORMS PHONES Connector (J15) and connecting STBY PHONES Connector (J16)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j15_off):
            self.log_signal.emit("NORMS PHONES Connector J15 successfully disconnected", False)
            time.sleep(0.5)
            if STM32RelayController.send_with_retry(STM32RelayController.set_j16_on):
                self.log_signal.emit("STBY PHONES Connector J16 successfully connected", False)
                time.sleep(0.5)
            else:
                self.log_signal.emit("ERROR: Failed to connect STBY PHONES Connector J16", True)
                
            
        else:
            self.log_signal.emit("ERROR: Failed to disconnect NORMS PHONES Connector J15 or STBY PHONES Connector J16", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
        self.log_signal.emit("Turning Switch (S24) to OFF", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_s24_off):
            self.log_signal.emit("S24 successfully turned OFF", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to turn OFF S24", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
        
        self.log_signal.emit("Turning Switch (S25) to ON", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_s25_on):
            self.log_signal.emit("S25 successfully turned ON", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to turn ON S25", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
        
    def pre_step_vos_delay_run_norm(self):
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            
        
    
        
    def pre_step_voltage_measurement_run_norm(self):
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
    def pre_step_voltage_measurement_run_stby(self):
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
            
    def pre_step_resistance_measurement_run_norm(self):
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
        
    def pre_step_resistance_measurement_run_stby(self):
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
                    
    def pre_step_transient_run(self):
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
        
    def pre_step_lighting_test_run_norm(self):
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()
                
    def pre_step_lighting_test_run_stby(self):
        
        self.log_signal.emit("connecting Audio analyser input to STATION BOX PH Connector (J29)", False)
        QApplication.processEvents()   # 🔑 FORCE UI UPDATE

        if STM32RelayController.send_with_retry(STM32RelayController.set_j29_on):
            self.log_signal.emit("J29 successfully connected", False)
            time.sleep(0.5)
            
        else:
            self.log_signal.emit("ERROR: Failed to connect Audio analyser input to STATION BOX PH Connector J29", True)
            

        QApplication.processEvents()
        time.sleep(2)
        self.check_abort()

    
    def __init__(self, selected_tests=None,previous_screen=None, entry_mode="station",selected_connectors=None):
        super().__init__()
        self.selected_tests = list(selected_tests) if selected_tests else []
        self.selected_connectors = selected_connectors or ["J103","J104","J105","J106","J107"]
        print("Selected tests:", self.selected_tests)
        self.previous_screen = previous_screen
        self.entry_mode = entry_mode
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
        
        self.show_popup_signal[str, str, object, str, object].connect(self.show_operator_popup)
        self.show_popup_signal[str, str, object, str, object, bool].connect(self.show_operator_popup_rich)
        self.show_popup_signal[str, str, object, str, object, bool, int].connect(self.show_operator_popup_rich_sized)
        self.update_popup_signal.connect(self.update_active_popup)
        self._trigger_queue_signal.connect(self._process_popup_queue)
        
        # ================= SESSION READ =================
        try:
            with open(SESSION_FILE, "r") as f:
                lines = f.readlines()

                self.session_name = lines[0].strip()
                self.session_id = lines[1].strip()
                self.session_role = lines[2].strip()

        except Exception:
            self.session_name = "Unknown"
            self.session_id = "Unknown"
            self.session_role = "Unknown"
        self.psu_lock = Lock()
        self.voltage_monitor_thread = None
        self.voltage_stop_event = Event()
        self._psu_shutdown_lock = Lock()
        self._psu_shutdown_in_progress = False
        self._reconnect_generation = 0

        self.operator_event = Event()
        self._reconnect_event = Event()
        self._psu_ready_event = Event()
        self._psu_ready_event.set()
        self._abort_pending_event = Event()     # NEW
        self._abort_pending_event.set()         # NEW — set = not paused
        self._awaiting_reconnect_ack = False
        self.device_listeners = []
        self.overall_test_passed = True
        self.logs_history = [] # To store (timestamp, message, is_error)
        self._disconnect_in_progress = False
        self._disconnect_done = False
        self._psu_error_handled = False
        self._reconnect_in_progress = False
        self._reconnect_lock = Lock()
        self.abort_event = Event()   # ✅ For immediate termination request
        self.psu_thread = None       # ✅ Track the running automation thread
        self.init_thread = None
        self._popup_queue = []
        self._popup_queue_lock = Lock()
        self._popup_busy = False
        

        self.setWindowTitle("HAL - Single Test")
        self.setMinimumSize(QSize(1000, 750))
        self.setStyleSheet("background-color: #f5f5f5;")
        self.showMaximized()
        self.log_signal.connect(self.append_log)
        self.completion_signal.connect(self.show_test_completion) 
        self.logger = Logger(TEST_LOGS_DIR / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.test_running = False
        self.voltage_value = 0.0
        self.current_value = 0.0
        self.config_locked = False
        
        # PSU automation state
        self.psu_port = None
        self.current_channel = None
        self.voltage_monitor_thread = None
        
        self.psu_inst = None
        self.rm = pyvisa.ResourceManager()
        self.osc_conn = None
        self.channel_ocp_limits = {}
        self._ocp_tripped_channels = set()

        
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

        title_label = QLabel("HAL – Single Test")
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
        self.back_btn.setFocusPolicy(Qt.NoFocus)
        back_icon = QPixmap(str(RESOURCES_DIR / "backarr.png"))
        self.back_btn.setIcon(QIcon(back_icon))
        self.back_btn.setText("Back ")
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
        self.voltage_label = QLabel("Power Supply: 0.0 V | 0.0 A")
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
        alhx_model_label = QLabel("Station Box:")
        alhx_model_label.setFont(QFont("Arial", 9, QFont.Bold))
        alhx_model_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        alhx_model_label.setMinimumWidth(120)
        alhx_model_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.alhx_combo = QComboBox()
        self.alhx_combo.addItems(["N200 - ALH1", "N200 - ALH2", "N200 - ALH3"])
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
        self.alhx_serial.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9]*")))
        self.alhx_serial.editingFinished.connect(
            lambda: self.alhx_serial.setText(self.alhx_serial.text().upper())
        )
        self.alhx_serial.returnPressed.connect(lambda: self.mod_combo.setFocus())
        config_grid.addWidget(alhx_sn_label, 1, 0, Qt.AlignRight | Qt.AlignVCenter)
        config_grid.addWidget(self.alhx_serial, 1, 1, Qt.AlignLeft | Qt.AlignVCenter)

        # Select Module (ALHx) Label (plain text, no background)
        mod_alhx_label = QLabel("Select MOD:")
        mod_alhx_label.setFont(QFont("Arial", 9, QFont.Bold))
        mod_alhx_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mod_alhx_label.setMinimumWidth(120)
        mod_alhx_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.mod_combo = QLineEdit()
        self.mod_combo.setPlaceholderText("e.g. 02")
        self.mod_combo.setMinimumHeight(32)
        self.mod_combo.setMaxLength(2)
        self.mod_combo.setFont(QFont("Arial", 9))
        self.mod_combo.setValidator(QRegExpValidator(QRegExp("[0-9]{0,2}")))
        self.mod_combo.editingFinished.connect(
            lambda: self.mod_combo.setText(self.mod_combo.text().strip().zfill(2))
        )
        self.mod_combo.returnPressed.connect(self._focus_after_mod_combo)
        self.mod_combo.setStyleSheet("""
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
        self.jbox_combo.addItems(["No Junction Box", "N200 - ALH4"])
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
        self.jbox_serial.setValidator(QRegExpValidator(QRegExp("[A-Za-z0-9]*")))
        self.jbox_serial.editingFinished.connect(
            lambda: self.jbox_serial.setText(self.jbox_serial.text().upper())
        )
        self.jbox_serial.returnPressed.connect(lambda: self.mod_jbox_combo.setFocus())
        config_grid.addWidget(jbox_sn_label, 1, 2, Qt.AlignRight | Qt.AlignVCenter)
        config_grid.addWidget(self.jbox_serial, 1, 3, Qt.AlignLeft | Qt.AlignVCenter)

        # Select Module (Junction Box) Label (plain text, no background)
        mod_jbox_label = QLabel("Select MOD:")
        mod_jbox_label.setFont(QFont("Arial", 9, QFont.Bold))
        mod_jbox_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mod_jbox_label.setMinimumWidth(120)
        mod_jbox_label.setStyleSheet("color: #374151; background-color: transparent; border: none; padding: 0px; margin: 0px;")

        self.mod_jbox_combo = QLineEdit()
        self.mod_jbox_combo.setPlaceholderText("e.g. 00")
        self.mod_jbox_combo.setMinimumHeight(32)
        self.mod_jbox_combo.setFont(QFont("Arial", 9))
        self.mod_jbox_combo.setMaxLength(2)
        self.mod_jbox_combo.setValidator(QRegExpValidator(QRegExp("[0-9]{0,2}")))
        self.mod_jbox_combo.editingFinished.connect(
            lambda: self.mod_jbox_combo.setText(self.mod_jbox_combo.text().strip().zfill(2))
        )
        self.mod_jbox_combo.returnPressed.connect(lambda: self.lock_btn.setFocus())
        self.mod_jbox_combo.setStyleSheet("""
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
        self.lock_btn.setFocusPolicy(Qt.NoFocus)
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
        self.start_btn.setFocusPolicy(Qt.NoFocus)
        self.start_btn.setStyleSheet("""
            QPushButton:disabled {
                background-color: #9e9e9e;
                color: #e0e0e0;
            }
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
        abort_btn.setFocusPolicy(Qt.NoFocus)
        abort_icon = QPixmap(str(RESOURCES_DIR / "abort.png"))
        if not abort_icon.isNull():
            abort_btn.setIcon(QIcon(abort_icon))
        abort_btn.setText("◯ Abort Test")
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
        graphs_btn.setFocusPolicy(Qt.NoFocus)
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
        graphs_btn.clicked.connect(self.open_graphs_window)
        action_layout.addWidget(graphs_btn)

        view_logs_btn = QPushButton("📋 View Logs")
        view_logs_btn.setMinimumHeight(44)
        view_logs_btn.setFont(QFont("Arial", 10, QFont.Bold))
        view_logs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        view_logs_btn.setFocusPolicy(Qt.NoFocus)
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
        view_logs_btn.clicked.connect(self.open_logs_window)
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
                border: 1px solid #2a2a2a;
                background-color: #1a1a1a;
                color: #cccccc;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        logs_container_layout.addWidget(self.log_text, 1)

        scroll_layout.addWidget(logs_container_frame)

        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area, 1)


        # Initialize junction box dependent state
        self.on_jbox_selection_changed(self.jbox_combo.currentText())
        self.apply_entry_mode()
        
    def open_graphs_window(self):
        """
        Show a non-blocking graph window that plots all numeric test readings
        from logs_history (voltage, resistance, APX).  The window auto-refreshes
        every 2 s so live results appear while the test is still running.
        """
        from dialogs.graphs_dialog import GraphsDialog
    
        # Keep a reference so it isn't garbage-collected immediately
        self._graphs_window = GraphsDialog(self, logs_history=self.logs_history)
        self._graphs_window.show()

    def is_junction_box_mode(self) -> bool:
        station = self.alhx_combo.currentText().strip().upper()
        jbox = self.jbox_combo.currentText().strip().upper()
        return station in ["N200 - ALH1", "N200 - ALH2", "N200 - ALH3"] and jbox == "N200 - ALH4"

    def _focus_after_mod_combo(self):
        """Enter in mod_combo → jump into Junction Box fields if enabled, else the lock button."""
        if self.jbox_serial.isEnabled():
            self.jbox_serial.setFocus()
        else:
            self.lock_btn.setFocus()

    def show_operator_popup_rich_sized(self, title, message, image_path=None,
                                    buttons="ok", timer_seconds=None,
                                    rich_html=False, image_size=420):
        self.show_operator_popup(
            title, message, image_path, buttons, timer_seconds,
            rich_html=rich_html, image_size=image_size
        )
    
    def show_operator_popup_rich(self, title, message, image_path=None, buttons="ok", timer_seconds=None, rich_html=False):
        """
        Variant of show_operator_popup that supports live HTML updates.
        Called by the 6-argument overload of show_popup_signal.
        rich_html=True tells the popup to use a QLabel with setTextFormat(Qt.RichText)
        so update_popup_signal can inject coloured HTML into it.
        """
        self.show_operator_popup(
            title, message, image_path, buttons, timer_seconds,
            rich_html=rich_html
        )

    def update_active_popup(self, html_text: str):
        popup = getattr(self, "active_popup", None)
        if popup is not None:
            try:
                popup.set_dynamic_text(html_text)
            except Exception:
                pass
    def open_logs_window(self):
        """
        Show detailed logs popup (exact red/green as running logs)
        + PDF export.
        """
        try:
            # ✅ pass structured logs (timestamp, message, error)
            logs_data = getattr(self, "logs_history", [])

            # fallback if empty
            if not logs_data:
                logs_data = [(datetime.now().strftime("%H:%M:%S"), self.log_text.toPlainText(), False)]

            dlg = LogsViewerDialog(self, logs_data=logs_data)
            dlg.exec_()

        except Exception as e:
            QMessageBox.warning(self, "Logs Error", f"Failed to open logs window:\n{e}")



    # ========================================================================
    # CONTROL PANEL VALIDATION
    # ========================================================================
    def validate_control_panel(self) -> bool:
        """
        Validate all required fields in the control panel before test start.
        
        Checks:
        - ALHx Model selected
        - ALHx Serial Number filled
        - ALHx Module selected
        - Junction Box fields filled (if applicable)
        - Configuration is locked
        
        Returns:
            True if validation passes, False otherwise.
        """
        # Check ALHx Model
        if not self.alhx_combo.currentText():
            self.show_validation_error("ALHx Model must be selected")
            return False
        
        # Check ALHx Serial Number
        if not self.alhx_serial.text().strip():
            self.show_validation_error("ALHx Serial Number must be filled")
            return False
        
        # Check ALHx MOD
        if not self.mod_combo.text().strip():
            self.show_validation_error("ALHx Module (MOD) must be Filled")
            return False
        
        # Check Junction Box dependent fields
        jbox_selection = self.jbox_combo.currentText()
        if jbox_selection != "No Junction Box":
            # Junction Box is selected - validate dependent fields
            if not self.jbox_serial.text().strip():
                self.show_validation_error("Junction Box Serial Number must be filled")
                return False
            
            if not self.mod_jbox_combo.text().strip():
                self.show_validation_error("Junction Box Module (MOD) must be Filled")
                return False
        
        # Check if configuration is locked
        if not self.config_locked:
            self.show_validation_error("Configuration must be LOCKED before starting the test")
            return False
        
        return True

    def start_voltage_monitoring(self):
        if self.voltage_monitor_thread is not None:
            if self.voltage_monitor_thread.isRunning():
                return                           # already running, don't double-start
            self.voltage_monitor_thread = None   # dead thread, clean up

        if self.voltage_stop_event.is_set():
            self.voltage_stop_event.clear()          # ← MUST clear BEFORE creating thread
        if self._disconnect_in_progress or self.abort_event.is_set():
            return
        self.voltage_monitor_thread = VoltageMonitorThread(
        psu_send_command=self.psu_send_command,
        stop_event=self.voltage_stop_event,
        channel=self.current_channel or 1      # ← add this
    )
        self.voltage_monitor_thread.voltage_signal.connect(self.on_voltage_update)
        self.voltage_monitor_thread.start()
        self.log_signal.emit("Live voltage monitoring STARTED", False)




    # AFTER (fixed — wait for thread to actually finish before releasing):
    def stop_voltage_monitoring(self):
        t = self.voltage_monitor_thread
        self.voltage_monitor_thread = None

        self.voltage_stop_event.set()

        if t is not None:
            t.stop()
            t.wait(2000)

        # Reset readings to zero once monitoring stops
        self.voltage_value = 0.0
        self.current_value = 0.0
        self.update_voltage_label()

        self.log_signal.emit("Live voltage monitoring STOPPED", False)
    
    
    def register_test_result(self, result: str):
        """
        Call this after every individual test.
        If any test FAILS → overall becomes FAIL permanently.
        """
        if result and result.upper() == "FAIL":
            self.overall_test_passed = False
    
    
    def show_validation_error(self, message: str):
        """
        Display validation error message in a custom-styled popup dialog.
        
        Args:
            message: Error message to display
        """
        dlg = QDialog(self)
        dlg.setWindowTitle("Validation Error")
        dlg.setModal(True)
        dlg.setFixedWidth(420)
        dlg.setStyleSheet("QDialog { background-color: #ffffff; }")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # ── Icon (info.png inside a soft red circle, matching the reference UI) ──
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(72, 72)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #fee2e2;
                border-radius: 36px;
            }
        """)
        icon_pixmap = QPixmap(str(RESOURCES_DIR / "info.png"))
        if not icon_pixmap.isNull():
            icon_label.setPixmap(
                icon_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        icon_row = QHBoxLayout()
        icon_row.addStretch()
        icon_row.addWidget(icon_label)
        icon_row.addStretch()
        layout.addLayout(icon_row)

        # ── Title ──
        title_label = QLabel("Validation Error")
        title_label.setFont(QFont("Arial", 15, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #d32f2f; background-color: transparent; border: none;")
        layout.addWidget(title_label)

        # ── Message ──
        body_label = QLabel(message)
        body_label.setWordWrap(True)
        body_label.setAlignment(Qt.AlignCenter)
        body_label.setFont(QFont("Arial", 10))
        body_label.setStyleSheet("color: #374151; background-color: transparent; border: none;")
        layout.addWidget(body_label)

        # ── OK button, centered ──
        ok_row = QHBoxLayout()
        ok_row.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(120, 40)
        ok_btn.setFont(QFont("Arial", 10, QFont.Bold))
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #154a8a; }
            QPushButton:pressed { background-color: #0f3860; }
        """)
        ok_btn.clicked.connect(dlg.accept)
        ok_row.addWidget(ok_btn)
        ok_row.addStretch()
        layout.addLayout(ok_row)

        dlg.exec_()


    # ========================================================================
    # PSU AUTOMATION METHODS (DP832 DATASHEET COMPLIANT)
    # ========================================================================
    from psu.psu_helpers import find_psu

  
    def psu_send_command(self, command: str, _retries: int = 3, critical: bool = True) -> str:
        # ── Block directly on the event (no race with _reconnect_in_progress flag) ──
        if not self._psu_ready_event.is_set():
            self._psu_ready_event.wait(timeout=300)
            if not self._psu_ready_event.is_set() or self.abort_event.is_set():
                return ""
        if getattr(self, "_psu_error_handled", False):
            return ""
        if getattr(self, "_disconnect_in_progress", False):
            return ""
        if self.abort_event.is_set():
            return ""
        if not self.psu_inst:
            return ""

        for attempt in range(1, _retries + 1):
            try:
                with self.psu_lock:
                    if "?" in command:
                        return self.psu_inst.query(command).strip()
                    else:
                        self.psu_inst.write(command)
                        return ""
            except Exception as exc:
                exc_str = str(exc).lower()
                print(f"[PSU] I/O error (attempt {attempt}/{_retries}): {exc}")

                # ── Soft SCPI / command errors: log and skip, do NOT reconnect ──
                _soft_errors = (
                    "incorrect", "invalid", "undefined header",
                    "syntax error", "query interrupted", "query unterminated",
                    "command error", "execution error", "otp", "ocp", "ovp",
                )
                if any(token in exc_str for token in _soft_errors):
                    print(f"[PSU] Soft SCPI error — skipping reconnect: {exc}")
                    return ""

                if attempt < _retries:
                    time.sleep(0.3)
                    continue

                # ── Non-critical callers (the voltage-monitor poll) never escalate —
                # a single slow/failed background reading is not proof the PSU is gone.
                if not critical:
                    print(f"[PSU] Non-critical command failed after retries — skipping reconnect: {exc}")
                    return ""

                # ── Only trigger reconnect for genuine transport-level failures ──
                _hard_errors = (
                    "visaioerror", "resource not found", "timeout",
                    "not connected", "unable to connect", "no listeners",
                    "vi_error", "access denied", "object reference",
                )
                if not any(token in exc_str for token in _hard_errors):
                    print(f"[PSU] Non-transport error after retries — skipping reconnect: {exc}")
                    return ""

                if getattr(self, "_reconnect_in_progress", False):
                    return ""
                self._psu_error_handled = True
                import threading
                threading.Thread(
                    target=self._background_reconnect,
                    daemon=True,
                    name="PSU-reconnect"
                ).start()
                return ""
        return ""
    
    def _background_reconnect(self, max_attempts: int = 10, delay: float = 5.0):
        lock = getattr(self, "_reconnect_lock", None)
        if lock is None:
            return
        acquired = lock.acquire(blocking=False)
        if not acquired:
            print("[PSU RECONNECT] Already in progress — skipping")
            return
        self._reconnect_in_progress = True
        self._psu_ready_event.clear()   # ← PAUSE test thread immediately
        my_generation = self._reconnect_generation
        try:
            self.voltage_stop_event.set()
            t = self.voltage_monitor_thread
            self.voltage_monitor_thread = None
            if t is not None:
                t.stop()
                from PyQt5.QtCore import QThread
                if t is not QThread.currentThread():
                    t.wait(3000)

            for listener in getattr(self, "device_listeners", []):
                try:
                    listener.stop()
                except Exception:
                    pass
            self.device_listeners = []

            saved_psu_resource = None
            try:
                if self.psu_inst:
                    saved_psu_resource = self.psu_inst.resource_name
            except Exception:
                pass
            try:
                if self.psu_inst:
                    self.psu_inst.close()
            except Exception:
                pass
            self.psu_inst = None
            # Do NOT close self.rm here — it may be the same underlying VISA
            # session the oscilloscope's ResourceManager shares on this backend.
            # Closing it here has been observed to silently kill osc_conn's live
            # session, causing a false oscilloscope disconnect right after a PSU
            # reconnect. self.rm stays open and gets reused for the reconnect.

            # AFTER (fixed - toast only, no log until after operator OK):
            saved_channel = getattr(self, "current_channel", 1) or 1
            QTimer.singleShot(0, lambda: self._show_psu_disconnect_toast())   # silent toast only

            # ── Queue "PSU disconnected - check cable" popup ──
            # Waits behind any currently showing APX popup automatically
            self._awaiting_reconnect_ack = True
            self._reconnect_event.clear()

            self._queue_popup(
                "⚠ PSU Disconnected",
                "The PSU connection has been lost.\n\n"
                "Please ensure:\n"
                "  • PSU USB cable is firmly connected\n"
                "  • PSU power switch is ON\n"
                "  • All power cables are seated properly\n\n"
                "Click OK when PSU is connected and ready — "
                "the system will then attempt to reconnect automatically.",
                None,
                "ok",
                None,
                callback=lambda result, popup: self._reconnect_event.set()
            )

            self._reconnect_event.wait()
            self._awaiting_reconnect_ack = False
            self.log_signal.emit("🔌 Operator confirmed PSU ready — attempting reconnect...", False)

            import pyvisa as _pyvisa
            if self.rm is None:
                self.rm = _pyvisa.ResourceManager()

            for attempt in range(1, max_attempts + 1):
                if self.abort_event.is_set():
                    return
                print(f"[PSU RECONNECT] Attempt {attempt}/{max_attempts}...")
                time.sleep(delay)
                try:
                    from psu.psu_helpers import find_psu_specific
                    new_inst = None
                    if saved_psu_resource:
                        new_inst = find_psu_specific(saved_psu_resource, rm=self)
                    if not new_inst:
                        new_inst = self.find_psu()   # fallback: full scan
                    if not new_inst:
                        continue
                    self.psu_inst = new_inst

                    # ── Shutdown/abort may have started while we were discovering the
                    #    PSU (find_psu + the 3s retry delay is a real window). Re-check
                    #    immediately before restoring anything — do not trust the check
                    #    at the top of the loop, it is stale by now.
                    if self._reconnect_should_abort(my_generation):
                        self.log_signal.emit(
                            "[PSU RECONNECT] Abort/close active - refusing to restore outputs", True
                        )
                        self._safe_shutdown_all_psu_channels(context="reconnect aborted")
                        return

                    self._safe_set_remote();                       time.sleep(0.2)
                    with self.psu_lock:
                        self.psu_inst.write("SYST:LOCK ON");       time.sleep(0.1)
                        # ── Restore CH1 (28V / 2.6A) — always on during any test ──
                        self.psu_inst.write("INST:NSEL 1");        time.sleep(0.05)
                        self.psu_inst.write("SOUR1:VOLT 28.0")
                        self.psu_inst.write("SOUR1:CURR 2.6")
                        self.psu_inst.write("OUTP ON");            time.sleep(0.1)

                    # ── Re-check again immediately before CH3 — the check above is not
                    #    a substitute, abort can land in the gap between CH1 and CH3.
                    if self._reconnect_should_abort(my_generation):
                        self.log_signal.emit(
                            "[PSU RECONNECT] Abort/close active - refusing to restore CH3", True
                        )
                        self._safe_shutdown_all_psu_channels(context="reconnect aborted mid-restore")
                        return

                    with self.psu_lock:
                        # ── Restore CH3 (5V / 1.0A) — configure AND turn on unconditionally ──
                        self.psu_inst.write("INST:NSEL 3");        time.sleep(0.05)
                        self.psu_inst.write("SOUR3:VOLT 5.0")
                        self.psu_inst.write("SOUR3:CURR 1.0")
                        self.psu_inst.write("OUTP ON");            time.sleep(0.1)

                        # ── Return SCPI context to whichever channel was active at disconnect ──
                        self.psu_inst.write(f"INST:NSEL {saved_channel}"); time.sleep(0.1)
                    
                    # ── Sync STM32 NOW — while PSU is stable and powered ──
                    try:
                        sync_ok = STM32RelayController.send_with_retry(STM32RelayController.sync)
                        if sync_ok:
                            self.log_signal.emit("✅ STM32 sync confirmed after PSU restore", False)
                        else:
                            self.log_signal.emit("⚠ STM32 sync failed after PSU restore — relays may be unreliable", True)
                    except Exception as sync_err:
                        self.log_signal.emit(f"⚠ STM32 sync error: {sync_err}", True)

                    # ── Allow logs through again before showing popup ──
                    self._psu_error_handled = False

                    # ── Queue "PSU reconnected - confirm stable" popup ──
                    self._awaiting_reconnect_ack = True
                    self._reconnect_event.clear()

                    self._queue_popup(
                        "⚠ PSU Reconnected",
                        "PSU was disconnected and has been reconnected.\n\n"
                        "Click OK to restore relay states and resume the test.",
                        None,
                        "ok",
                        None,
                        callback=lambda result, popup: self._reconnect_event.set()
                    )

                    self._reconnect_event.wait()
                    self._awaiting_reconnect_ack = False

                    # ── Restore relay states ──
                    self.log_signal.emit("🔁 Restoring relay states after PSU reconnect…", False)
                    relay_ok = RelayStateTracker.restore_all()
                    if relay_ok:
                        self.log_signal.emit("✅ Relay states restored successfully.", False)
                    else:
                        self.log_signal.emit("⚠ Some relays may not have restored — check manually.", True)

                    # ── Restart voltage monitoring ──
                    self.voltage_stop_event.clear()
                    self.start_voltage_monitoring()

                    try:
                        psu_listener = PSUListener(self.psu_inst, self.psu_lock)
                        psu_listener.disconnected.connect(self.on_device_disconnected)
                        self.device_listeners = [
                            l for l in self.device_listeners if not isinstance(l, PSUListener)
                        ] + [psu_listener]
                        psu_listener.start()
                    except Exception as le:
                        print(f"[PSU RECONNECT] Listener restart failed: {le}")

                    # ── Queue final "resume" confirmation popup ──
                    self._awaiting_reconnect_ack = True
                    self._reconnect_event.clear()

                    self._queue_popup(
                        "✅ PSU Reconnected Successfully",
                        "PSU has been reconnected and relay states have been restored.\n\n"
                        "The test will resume from where it paused.\n\n"
                        "Click OK to continue.",
                        None,
                        "ok",
                        None,
                        callback=lambda result, popup: self._reconnect_event.set()
                    )

                    self._reconnect_event.wait()
                    self._awaiting_reconnect_ack = False

                    self._psu_ready_event.set()        # ← UNBLOCK test thread
                    self.log_signal.emit("▶ PSU reconnected — test resuming.", False)
                    return

                except Exception as exc:
                    print(f"[PSU RECONNECT] Attempt {attempt} failed: {exc}")
                    self.log_signal.emit(
                        f"🔁 PSU reconnect attempt {attempt}/{max_attempts} failed: {exc}", True
                    )

            # All attempts failed
            print("[PSU RECONNECT] ✗ All attempts failed — aborting test")
            self.log_signal.emit(
                "❌ PSU reconnect: all rediscovery attempts failed — see attempt log above.", True
            )
            self.log_signal.emit("❌ PSU reconnect failed — test aborted.", True)
            self._disconnect_in_progress = True
            self.abort_event.set()
            self.voltage_stop_event.set()
            QTimer.singleShot(0, self._show_psu_failed_dialog)

        finally:
            self._reconnect_in_progress = False
            lock.release()
    def _show_psu_disconnect_toast(self):
        """Non-blocking top-right toast when PSU disconnects."""

        toast = QWidget(self, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        toast.setAttribute(Qt.WA_DeleteOnClose)
        toast.setAttribute(Qt.WA_ShowWithoutActivating)
        toast.setFixedWidth(320)
        toast.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                border: 1px solid #d32f2f;
                border-radius: 8px;
            }
            QLabel { border: none; background: transparent; }
        """)

        layout = QVBoxLayout(toast)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        title_row = QHBoxLayout()
        icon_lbl = QLabel("⚠")
        icon_lbl.setStyleSheet("color:#d32f2f; font-size:14px;")
        title_lbl = QLabel("PSU Disconnected")
        title_lbl.setFont(QFont("Arial", 9, QFont.Bold))
        title_lbl.setStyleSheet("color:#f38ba8;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton { background:transparent; color:#585b70; border:none; font-size:11px; }
            QPushButton:hover { color:#cdd6f4; }
        """)
        close_btn.clicked.connect(toast.close)
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl, 1)
        title_row.addWidget(close_btn)
        layout.addLayout(title_row)

        body_lbl = QLabel("PSU connection lost. Attempting to reconnect automatically…")
        body_lbl.setWordWrap(True)
        body_lbl.setStyleSheet("color:#cdd6f4; font-size:8pt;")
        layout.addWidget(body_lbl)

        toast.adjustSize()
        pr = self.geometry()
        toast.move(pr.right() - toast.width() - 16, pr.top() + 80)
        toast.show()

        self._psu_toast = toast          # keep reference alive
        QTimer.singleShot(8000, toast.close)


    def _show_psu_failed_dialog(self):
        from PyQt5.QtWidgets import QMessageBox
        from PyQt5.QtCore import QTimer
        self._force_close_all_dialogs()
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("PSU Disconnected")
        msg.setText(
            "PSU could not be reconnected after multiple attempts.\n"
            "Test aborted. Please check the PSU connection and restart."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(
            lambda _: (
                self.return_to_connection.emit(),
                QTimer.singleShot(100, self.close),
            )
        )
        msg.exec_()
    
    def safe_handle_disconnect(self):
        if getattr(self, "_disconnect_done", False):
            return
        if getattr(self, "_reconnect_in_progress", False):
            return
        self._disconnect_done = True
        self.abort_event.set()
        self.voltage_stop_event.set()
        print("[SAFE DISCONNECT] Test aborted due to unrecoverable PSU error")
        
    def _queue_popup(self, title, message, image_path, buttons, timer_seconds, callback=None):
        with self._popup_queue_lock:
            self._popup_queue.append((title, message, image_path, buttons, timer_seconds, callback))
        # Use signal to safely trigger from background threads
        self._trigger_queue_signal.emit()

    def _process_popup_queue(self):
        if self._popup_busy:
            return

        # Once an abort has started, no more test-flow popups should ever
        # appear — drop anything left queued instead of showing it.
        if self.abort_event.is_set():
            with self._popup_queue_lock:
                self._popup_queue.clear()
            return

        with self._popup_queue_lock:
            if not self._popup_queue:
                return
            title, message, image_path, buttons, timer_seconds, callback = self._popup_queue.pop(0)

        self._popup_busy = True

        try:
            popup = OperatorInfoPopup(
                title=title, message=message, image_path=image_path,
                buttons=buttons, timer_seconds=timer_seconds, parent=self
            )
        except RuntimeError:
            # Parent window itself is mid-teardown — nothing to show.
            self._popup_busy = False
            return

        self.active_popup = popup

        def handle_result(result):
            self._popup_busy = False
            if callback:
                try:
                    callback(result, popup)
                except RuntimeError:
                    pass   # popup's Qt widget was already destroyed
                except Exception:
                    pass
            self._trigger_queue_signal.emit()

        popup.finished.connect(handle_result)
        popup.setWindowModality(Qt.NonModal)
        popup.setWindowFlags(popup.windowFlags() | Qt.WindowStaysOnTopHint)
        try:
            popup.show()
        except RuntimeError:
            pass
        QApplication.processEvents()
        
    def apply_entry_mode(self):
        """
        Configure UI depending on where user came from.
        This is the ONLY place controlling Station/Junction logic.
        """

        # ===============================
        # STATION BOX ENTRY
        # ===============================
        if self.entry_mode == "station":

            self.jbox_combo.setCurrentText("No Junction Box")
            self.jbox_combo.setEnabled(False)

            self.jbox_serial.setEnabled(False)
            self.mod_jbox_combo.setEnabled(False)

            # Station box must stay editable
            self.alhx_combo.setEnabled(True)

        # ===============================
        # JUNCTION BOX ENTRY
        # ===============================
        elif self.entry_mode == "junction":

            self.jbox_combo.setCurrentText("N200 - ALH4")
            self.jbox_combo.setEnabled(False)

            self.jbox_serial.setEnabled(True)
            self.mod_jbox_combo.setEnabled(True)

            # Station forced to ALH2
            self.alhx_combo.setCurrentText("N200 - ALH2")
            self.alhx_combo.setEnabled(False)

    def freeze_psu_front_panel(self):
        """
        Lock PSU front panel to prevent manual changes during automation.
        
        SCPI Command: SYST:LOCK ON (DP832 Datasheet §5.2)
        """
        self.psu_send_command(PSUCommands.SYSTEM_LOCK_ON)
        self.log_signal.emit("PSU front panel LOCKED (SYST:LOCK ON)", False)
        
    def _safe_set_remote(self):
        """
        Send SYST:REM safely — suppresses errors if PSU is already in remote mode.
        Calling SYST:REM on an already-remote PSU can raise a SCPI error on DP832
        which would falsely trigger the disconnect/reconnect handler.
        """
        try:
            with self.psu_lock:
                if self.psu_inst:
                    self.psu_inst.write("SYST:REM")
        except Exception as e:
            # Already in remote mode or benign SCPI error — not a disconnect
            print(f"[PSU] SYST:REM suppressed (already remote or benign): {e}")

    def unfreeze_psu_front_panel(self):
        """
        Unlock PSU front panel to allow manual changes.
        
        SCPI Command: SYST:LOCK OFF (DP832 Datasheet §5.2)
        """
        self.psu_send_command(PSUCommands.SYSTEM_LOCK_OFF)
        self.log_signal.emit("PSU front panel UNLOCKED (SYST:LOCK OFF)", False)

    def _safe_shutdown_all_psu_channels(self, context: str = "") -> bool:
        """
        Single authoritative PSU emergency shutdown path.
        Used by abort_test_internal, closeEvent (all paths), and
        on_device_disconnected. Never trusts a stale psu_inst blindly,
        never claims success it didn't actually achieve, and sets
        _psu_shutdown_in_progress immediately so any in-flight reconnect
        thread refuses to restore outputs.
        """
        self._psu_shutdown_in_progress = True
        try:
            with self._psu_shutdown_lock:
                print(f"[PSU SHUTDOWN] Starting emergency shutdown ({context})")

                inst = self.psu_inst
                inst_is_valid = False
                if inst is not None:
                    try:
                        with self.psu_lock:
                            inst.write("*CLS")
                        inst_is_valid = True
                        print("[PSU SHUTDOWN] Using current PSU connection")
                    except Exception as e:
                        print(
                            f"[PSU SHUTDOWN] Existing PSU handle invalid - rediscovering PSU ({e})"
                        )

                if not inst_is_valid:
                    try:
                        if self.rm is None:
                            import pyvisa as _pyvisa
                            self.rm = _pyvisa.ResourceManager()
                        inst = self.find_psu()
                        if inst:
                            self.psu_inst = inst
                            print("[PSU SHUTDOWN] Fresh PSU handle acquired for shutdown")
                        else:
                            print(
                                "[PSU SHUTDOWN] CRITICAL: PSU unavailable; channel state could not be commanded OFF"
                            )
                            return False
                    except Exception as e:
                        print(f"[PSU SHUTDOWN] CRITICAL: PSU rediscovery failed - {e}")
                        return False

                all_ok = True
                for ch in (1, 2, 3):
                    try:
                        with self.psu_lock:
                            inst.write(f"INST:NSEL {ch}")
                            time.sleep(0.1)
                            inst.write("OUTP OFF")
                            time.sleep(0.1)
                        print(f"[PSU SHUTDOWN] Ch{ch} OFF")
                    except Exception as e:
                        all_ok = False
                        print(f"[PSU SHUTDOWN] FAILED: Ch{ch} OFF - {e}")

                if all_ok:
                    print(
                        f"[PSU SHUTDOWN] All PSU channels OFF successfully ({context})"
                    )
                else:
                    print(
                        f"[PSU SHUTDOWN] CRITICAL: one or more channels could not be confirmed OFF ({context})"
                    )
                return all_ok
        finally:
            self._psu_shutdown_in_progress = False

    def _reconnect_should_abort(self, my_generation: int) -> bool:
        """
        Checked immediately before every OUTP ON in _background_reconnect.
        True means: do not restore outputs, terminate the reconnect.
        """
        return (
            self.abort_event.is_set()
            or getattr(self, "_psu_shutdown_in_progress", False)
            or getattr(self, "_disconnect_in_progress", False)
            or not self.test_running
            or my_generation != self._reconnect_generation
        )

    def _turn_off_psu_channels(self, channels, context: str = ""):
        """
        Turn off the given PSU channels using the EXISTING self.psu_inst
        (the same handle opened in start_test / reconnect — never re-opened here).
        Logs per-channel failures instead of swallowing them.
        """
        if not self.psu_inst:
            self.log_signal.emit(
                f"⚠ PSU OFF skipped{f' ({context})' if context else ''}: no active PSU handle",
                True
            )
            return False

        all_ok = True
        with self.psu_lock:
            for ch in channels:
                try:
                    self.psu_inst.write(f"INST:NSEL {ch}")
                    time.sleep(0.1)
                    self.psu_inst.write("OUTP OFF")
                    time.sleep(0.1)
                except Exception as e:
                    all_ok = False
                    self.log_signal.emit(f"⚠ Failed to turn OFF Ch{ch}: {e}", True)

        if all_ok:
            self.log_signal.emit(f"PSU OUTPUT TURNED OFF{f' ({context})' if context else ''}", False)
        else:
            self.log_signal.emit(
                f"⚠ PSU OFF completed with errors{f' ({context})' if context else ''} — verify hardware manually",
                True
            )
        return all_ok
    
    # def set_channel_current_with_ocp(self, channel: int, current: float, margin: float = 0.2):
    #     ocp_level = round(current + margin, 3)
    #     self.psu_send_command(f"INST:NSEL {channel}")
    #     time.sleep(0.05)
    #     self.psu_send_command(f"SOUR{channel}:CURR {current}")
    #     self.psu_send_command(f"SOUR{channel}:CURR:PROT {ocp_level}")
    #     self.psu_send_command(f"SOUR{channel}:CURR:PROT:STAT ON")
    #     self.channel_ocp_limits[channel] = ocp_level
    #     self._ocp_tripped_channels.discard(channel)
    #     self.log_signal.emit(
    #         f"Ch{channel} OCP armed at {ocp_level}A (set {current}A + {margin}A margin)", False
    #     )
        
    def debug_active_channel(self, tag: str):
        try:
            ch = self.psu_send_command("INST:NSEL?")
            volt = self.psu_send_command("SOUR:VOLT?")
            meas = self.psu_send_command("MEAS:VOLT?")
            print(f"[{tag}] ACTIVE_CH={ch}, SET_VOLT={volt}, MEAS_VOLT={meas}")
        except Exception as e:
            print(f"[{tag}] DEBUG ERROR:", e)

    def worker_channel_1(self):
        """
        CHANNEL 1
        Voltage: 28V
        Current: 2.6A
        Output ON until task completes
        """

        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 1")
        time.sleep(0.1)

        self.psu_send_command("SOUR1:VOLT 28.0")
        # self.set_channel_current_with_ocp(1, 2.6)

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        
        self.current_channel = 1
        self.log_signal.emit("Ch1 OUTPUT ON (28V, 2.6A)", False)
        self.operator_event.clear()
        time.sleep(2)
        


    
    def worker_ch2_28v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)

        self.psu_send_command("SOUR2:VOLT 28.0")
        # self.set_channel_current_with_ocp(2, 2.0)

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        self.current_channel = 2
        self.log_signal.emit("Ch2 OUTPUT ON (28V, 2.0A)", False)
        

    def worker_ch3_5v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 3")
        time.sleep(0.1)

        self.psu_send_command("SOUR3:VOLT 5.0")
        # self.set_channel_current_with_ocp(3, 1.0)

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        self.current_channel = 3
        self.log_signal.emit("Ch3 OUTPUT ON (5V, 1.0A)", False)

    def worker_ch2_12v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)

        self.psu_send_command("SOUR2:VOLT 12.0")
        # self.set_channel_current_with_ocp(2, 2.0)

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        self.current_channel = 2
        self.log_signal.emit("Ch2 OUTPUT ON (12V, 2.0A)", False)


    def worker_ch2_5v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)

        self.psu_send_command("SOUR2:VOLT 5.0")
        # self.set_channel_current_with_ocp(2, 2.0)

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        self.current_channel = 2
        self.log_signal.emit("Ch2 OUTPUT ON (5V, 2.0A)", False)
  
    def select_psu_channel(self, channel: int) -> bool:
        if channel not in [1, 2]:
            self.log_signal.emit(
                f"ERROR: Invalid channel {channel}. Only Ch1 and Ch2 supported",
                True
            )
            return False

        self.current_channel = channel
        self.log_signal.emit(f"Channel {channel} selected (LOGICAL ONLY)", False)
        return True


    def set_psu_voltage(self, voltage: float, channel: int) -> bool:
        """
        Set output voltage for specified channel.
        
        SCPI Command: SOUR:VOLT {voltage} (DP832 Datasheet §4.4)
        
        Args:
            voltage: Voltage value in volts (0-32V range for DP832)
            channel: Channel number (1 or 2)
        
        Returns:
            True if successful, False otherwise
        """
        
        try:
            time.sleep(0.1)
            self.psu_send_command(f"INST:NSEL {channel}")
            command = PSUCommands.VOLTAGE_SET.format(voltage)
            self.psu_send_command(command)
            self.log_signal.emit(f"Ch{channel} voltage set to {voltage}V (SOUR:VOLT {voltage})", False)
            return True
        except Exception as e:
            self.log_signal.emit(f"ERROR: Failed to set voltage - {str(e)}", True)
            return False

    def set_psu_current(self, current: float, channel: int) -> bool:
        """
        Set current limit for specified channel.
        
        SCPI Command: SOUR:CURR {current} (DP832 Datasheet §4.4)
        
        Args:
            current: Current limit in amperes (0-5.1A range for DP832)
            channel: Channel number (1 or 2)
        
        Returns:
            True if successful, False otherwise
        """
        
        try:
            time.sleep(0.1)
            self.psu_send_command(f"INST:NSEL {channel}")
            command = PSUCommands.CURRENT_SET.format(current)
            self.psu_send_command(command)
            self.log_signal.emit(f"Ch{channel} current limit set to {current}A (SOUR:CURR {current})", False)
            return True
        except Exception as e:
            self.log_signal.emit(f"ERROR: Failed to set current - {str(e)}", True)
            return False

    def turn_on_psu_output(self, channel: int) -> bool:
        try:
            time.sleep(0.1)
            with self.psu_lock:
                self.psu_inst.write("*CLS")
                time.sleep(0.05)
                self.psu_inst.write(f"INST:NSEL {channel}")
                time.sleep(0.05)
                self.psu_inst.write("OUTP ON")


            # FORCE channel context ONCE
            # self.psu_send_command(f"INST:NSEL {channel}")

            # # Enable output
            # self.psu_send_command(PSUCommands.OUTPUT_ON)

            self.log_signal.emit(f"Ch{channel} output turned ON (OUTP ON)", False)
            return True
        except Exception as e:
            self.log_signal.emit(f"ERROR: Failed to turn on output - {str(e)}", True)
            return False


    def turn_off_psu_output(self, channel: int) -> bool:
        """
        Disable output for specified channel.
        
        SCPI Command: OUTP OFF (DP832 Datasheet §4.3)
        
        Args:
            channel: Channel number (1 or 2)
        
        Returns:
            True if successful, False otherwise
        """
        
        try:
            time.sleep(0.1)
            # self.psu_send_command(f"INST:NSEL {channel}")
            # self.psu_send_command(PSUCommands.OUTPUT_OFF)
            with self.psu_lock:
                self.psu_inst.write("*CLS")
                time.sleep(0.05)
                self.psu_inst.write(f"INST:NSEL {channel}")
                time.sleep(0.05)
                self.psu_inst.write("OUTP OFF")

            self.log_signal.emit(f"Ch{channel} output turned OFF (OUTP OFF)", False)
            self.voltage_value = 0.0
            self.current_value = 0.0
            self.update_voltage_label()
            return True
        except Exception as e:
            self.log_signal.emit(f"ERROR: Failed to turn off output - {str(e)}", True)
            return False

    def on_voltage_update(self, voltage: float, current: float):
        self.voltage_value = voltage
        self.current_value = current
        self.update_voltage_label()

        ch = self.current_channel
        if ch and ch in self.channel_ocp_limits:
            limit = self.channel_ocp_limits[ch]
            if current >= limit and ch not in self._ocp_tripped_channels:
                self._ocp_tripped_channels.add(ch)
                self._handle_ocp_trip(ch, current, limit)

    def _handle_ocp_trip(self, channel: int, measured: float, limit: float):
        self.log_signal.emit(
            f"❌ OCP TRIP on Ch{channel}: {measured:.2f}A ≥ limit {limit:.2f}A — turning output OFF",
            True
        )
        try:
            self.turn_off_psu_output(channel)
        except Exception as e:
            self.log_signal.emit(f"ERROR: Failed to turn off Ch{channel} after OCP trip - {e}", True)

        self.abort_event.set()

        self._queue_popup(
            "⚠ High Current Detected",
            f"Channel {channel} exceeded its safe current limit.\n\n"
            f"Measured: {measured:.2f} A\n"
            f"Limit: {limit:.2f} A\n\n"
            f"Output has been turned OFF automatically.\n"
            f"Please check wiring/load for a short circuit before continuing.",
            None,
            "ok",
            None,
        )

    def update_voltage_label(self):
        """Update top-right voltage/current label with live readings"""
        channel_str = f"CH{self.current_channel}" if self.current_channel else "PSU"
        self.voltage_label.setText(
            f"Power Supply: {channel_str} → {self.voltage_value:.2f} V | {self.current_value:.2f} A"
        )
        # Keep combo in sync when automation changes current_channel
        if self.current_channel and hasattr(self, "channel_select_combo"):
            combo_index = self.current_channel - 1
            if self.channel_select_combo.currentIndex() != combo_index:
                self.channel_select_combo.blockSignals(True)
                self.channel_select_combo.setCurrentIndex(combo_index)
                self.channel_select_combo.blockSignals(False)

    def _on_display_channel_changed(self, index: int):
        channel = index + 1
        self.current_channel = channel
        self.update_voltage_label()

        if not self.psu_inst:
            self.log_signal.emit(f"Display channel → CH{channel} (PSU not connected yet)", False)
            return

        if (self.voltage_monitor_thread is not None
                and self.voltage_monitor_thread.isRunning()):
            self.voltage_monitor_thread.set_channel(channel)   # ← live swap, no restart
            self.log_signal.emit(f"Display channel switched → CH{channel}", False)
            return

        # fallback: monitor wasn't running, start fresh
        self.stop_voltage_monitoring()
        time.sleep(0.1)
        self.start_voltage_monitoring()
        self.log_signal.emit(f"Display channel switched → CH{channel}", False)
    
    def show_operator_popup(self, title, message, image_path=None,
                        buttons="ok", timer_seconds=None,
                        rich_html=False, image_size=420):
        if getattr(self, "_disconnect_in_progress", False) or self.abort_event.is_set():
            return

        def _callback(result, popup):
            try:
                res, operator = popup.get_result()
            except RuntimeError:
                # Popup's underlying Qt widget was already destroyed
                # (e.g. force-closed by an Abort that landed mid-popup) —
                # nothing left to read from it. Just release whatever was
                # waiting on this popup and stop.
                self.operator_event.set()
                return

            self.last_test_result = res
            self.last_operator_response = operator

            if buttons == "yes_no":
                if result == QDialog.Accepted:
                    self.operator_event.set()
                else:
                    self.log_signal.emit("Operator clicked NO, continuing test...", True)
                    self.operator_event.set()
            else:
                # PSU-reconnect popups never arrive here — _background_reconnect
                # queues its popups directly via _queue_popup() with its own
                # dedicated callback that sets _reconnect_event. Any popup that
                # reaches this handler is therefore always a normal test-flow
                # "ok" popup and must always release operator_event. Routing it
                # to _reconnect_event based on the *global* _awaiting_reconnect_ack
                # flag stole the ack whenever a PSU reconnect happened to be
                # mid-cycle at the same moment, permanently blocking the test
                # thread's operator_event.wait() and letting the reconnect
                # thread advance as though its own popup had been acknowledged.
                self.operator_event.set()

        # rich_html popups bypass queue — they need live updates via update_popup_signal
        if rich_html:
            popup = OperatorInfoPopup(
                title=title, message=message, image_path=image_path,
                buttons=buttons, timer_seconds=timer_seconds,
                rich_html=True, image_size=image_size, parent=self   # ← add image_size
            )
            self.active_popup = popup
            popup.finished.connect(lambda result: _callback(result, popup))
            popup.setWindowModality(Qt.NonModal)
            popup.setWindowFlags(popup.windowFlags() | Qt.WindowStaysOnTopHint)
            popup.show()
            QApplication.processEvents()
            return

        self._queue_popup(title, message, image_path, buttons, timer_seconds,
                          callback=_callback)
        

    def check_abort(self):
        if self.abort_event.is_set():
            raise Exception("TEST_ABORTED_BY_USER")
        # ── Block ALL test code while the Abort confirmation popup is up ────
        if not self._abort_pending_event.is_set():
            self._abort_pending_event.wait(timeout=60)
            if self.abort_event.is_set():
                raise Exception("TEST_ABORTED_BY_USER")
        # ── Block ALL test code while PSU reconnect is in progress ──────────
        if not self._psu_ready_event.is_set():
            self.log_signal.emit("⏸ Test paused — waiting for PSU to reconnect...", False)
            self._psu_ready_event.wait(timeout=300)
            if self.abort_event.is_set():
                raise Exception("TEST_ABORTED_BY_USER")
            self.log_signal.emit("▶ PSU ready — test resuming.", False)


    # ========================================================================
    # RUN PSU AUTOMATION SEQUENCE
    # ========================================================================
    def run_psu_automation(self):
        """
        Router:
        - No Junction Box → existing flow
        - Junction Box (ALH4) → separate flow
        """
        if self.is_junction_box_mode():
            return self.run_psu_automation_with_jbox()
        return self.run_psu_automation_no_jbox()
    
    
    def run_psu_automation_with_jbox(self):
        try:
            self.check_abort()
            self.log_signal.emit("Live voltage monitoring enabled", False)
            self.log_signal.emit("========== PSU AUTOMATION STARTING ==========", False)
            time.sleep(1)
            self.start_device_monitoring()
            self.check_abort()
 
            # ── Single call handles NORM + STBY per connector + ground crew ──
            jb_seq_s.run(self)
 
            remove_tuning_hooks()
            time.sleep(0.5)
            # self.log_signal.emit("========== ALL JUNCTION BOX TESTS COMPLETED ==========", False)
            self.completion_signal.emit()
 
        except Exception as e:
            if "TEST_ABORTED_BY_USER" not in str(e) and "PSU communication" not in str(e):
                self.log_signal.emit(f"ERROR: Junction Box PSU automation failed - {str(e)}", True)

    # ─────────────────────────────────────────────────────────────────────────────
    # run_psu_automation_no_jbox — broken into focused stages
    # ─────────────────────────────────────────────────────────────────────────────

    def run_psu_automation_no_jbox(self):
        try:
            self._setup_psu_remote()
            self._power_on_norm()
            self._connect_norm_relays()
            self._run_norm_tests()

            if self._has_stby_tests():          # ← skip entire STBY block if nothing to run
                self._operator_gate_stby()
                self._setup_stby_switches()
                self._power_on_norm()
                self._connect_stby_relays()
                self._run_stby_tests()
            else:
                self.log_signal.emit(
                    "No STBY tests for selected test set — skipping STBY stage.", False
                )

            self._teardown_no_jb()
        except Exception as e:
            if "TEST_ABORTED_BY_USER" not in str(e) and "PSU communication" not in str(e):
                self.log_signal.emit(f"ERROR: PSU automation failed - {str(e)}", True)


    # ── Stage 1: PSU remote mode + front panel lock ───────────────────────────────

    def _setup_psu_remote(self):
        self.test_running = True
        self._safe_set_remote()
        time.sleep(0.2)
        self.psu_send_command("INST:NSEL 1")
        time.sleep(0.1)
        self.freeze_psu_front_panel()
        time.sleep(0.2)
        self.start_device_monitoring()


    # ── Stage 2: Power CH1 on (shared by NORM and STBY) ──────────────────────────

    def _power_on_norm(self):
        self.worker_channel_1()
        time.sleep(2)


    # ── Stage 3: Relay connections for NORM mode ─────────────────────────────────

    def _connect_norm_relays(self):
        self.check_abort()
        self.log_signal.emit(
            "Connecting audio analyser input mic controller (J13) and phones connector (J15)", False
        )
        QApplication.processEvents()

        if STM32RelayController.send_with_retry(STM32RelayController.set_j13_on):
            self.log_signal.emit("J13 MIC controller successfully connected", False);  time.sleep(0.5)
            if STM32RelayController.send_with_retry(STM32RelayController.set_j15_on):
                self.log_signal.emit("J15 phones connector successfully connected", False); time.sleep(0.5)
            else:
                self.log_signal.emit("ERROR: Failed to connect J15", True)
        else:
            self.log_signal.emit("ERROR: Failed to connect J13/J15", True)

        QApplication.processEvents(); time.sleep(0.5)
        self.check_abort()

        self.log_signal.emit("Connecting audio analyser generator output (J27)", False)
        QApplication.processEvents()

        if STM32RelayController.send_with_retry(STM32RelayController.set_j27_on):
            self.log_signal.emit("J27 successfully connected", False); time.sleep(0.5)
        else:
            self.log_signal.emit("ERROR: Failed to connect J27", True)

        QApplication.processEvents(); time.sleep(0.5)
        self.check_abort()

        generator_control(self, level="750.0 uVrms", frequency=1000)

        self.log_signal.emit("Setting Switch S24 (NORM) to UP position", False)
        QApplication.processEvents()

        if STM32RelayController.send_with_retry(STM32RelayController.set_s24_on):
            self.log_signal.emit("S24 NORM successfully set to UP position", False); time.sleep(0.5)
        else:
            self.log_signal.emit("ERROR: Failed to set S24 to UP position", True)

        QApplication.processEvents(); time.sleep(0.5)
        self.check_abort()
        
        # 🛑 PAUSE POINT
        self.check_abort()
        self.operator_event.clear()
        self.show_popup_signal.emit(
            "⚠ Operator Action Required",
            "• DS10 and DS11 indicators should illuminate red.\n",
            RESOURCES_DIR / "ds_10_11.jpeg","yes_no",None
        )

        # ⏸ WAIT until operator clicks OK
        self.operator_event.wait()
        time.sleep(0.5)
        self.log_signal.emit("INITIALIZATION COMPLETE", False)


    # ── Stage 4: Run all NORM-mode tests ─────────────────────────────────────────

    def _run_norm_tests(self):
        tests = self.selected_tests or list(self.TEST_MAP.keys())
        for test in tests:
            self.check_abort()
            pre = self.TEST_PRE_STEPS.get(test)
            if pre:
                pre(self)
            self.check_abort()
            func = self.TEST_MAP.get(test)
            if func:
                self.log_signal.emit(f"Running {test}", False)
                func(self)
                time.sleep(0.5)
            else:
                self.log_signal.emit(f"Unknown test: {test}", True)

        self.log_signal.emit("==========All TESTS COMPLETED IN NORMAL MODE==========", False)
        time.sleep(2)


    # ── Stage 5: Operator gate between NORM and STBY ─────────────────────────────
    def _has_stby_tests(self) -> bool:
        """Returns True if at least one selected test has a real STBY implementation."""
        tests = self.selected_tests or list(self.TEST_MAP_stby.keys())
        return any(
            self.TEST_MAP_stby.get(t) is not None
            for t in tests
        )
    def _operator_gate_stby(self):
        self.log_signal.emit("========== INITIALIZATION START ==========", False)
        time.sleep(1)
        self.operator_event.clear()

        # AFTER
        from dialogs.calibration_popup import MODEL_IMAGES  # already imported at top — add if missing

        _model_img = MODEL_IMAGES.get(self.alhx_combo.currentText().strip(), "sb.png")
        self.check_abort()
        self.show_popup_signal.emit(
            "⚠ Operator Setup Required",
            "• Turn the ICS knobs fully CW.\n"
            "• Set MIC Mode to HOT.\n"
            "• Turn TX SEL knobs fully CCW and to the OUT position.\n"
            "• Turn RX SEL knobs fully CCW.\n",
            RESOURCES_DIR / _model_img,
            "acknowledge",
            None,
        )
        self.operator_event.wait()
        time.sleep(2)
        self.check_abort()
        self.operator_event.clear()
        self.show_popup_signal.emit(
            "⚠ Operator Action Required",
            "• Set STBY/NORMAL switch to NORMAL.\n",
            RESOURCES_DIR / "normal.jpeg","ok",None
        )

        # ⏸ WAIT until operator clicks OK
        self.operator_event.wait()
        time.sleep(0.5)
        self.check_abort()
        self.log_signal.emit("Switching all relays to default state", False)
        QApplication.processEvents()
        if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
            self.log_signal.emit("Successfully set all relays to default states", False)
        else:
            self.log_signal.emit("ERROR: Failed to set relays to default states", True)

        self.log_signal.emit("COMMENCING TESTS UNDER STBY MODE", False)


    # ── Stage 6: Switch configuration for STBY mode ──────────────────────────────

    def _setup_stby_switches(self):
        steps = [
            ("LOCAL/REMOTE (S23) → LOCAL",
            STM32RelayController.set_s23_local,  "S23 set to LOCAL"),
            ("LOAD (S31) → 600 OHM",
            STM32RelayController.set_s31_600ohm, "S31 set to 600 OHM"),
        ]
        for msg, cmd, ok_msg in steps:
            self.log_signal.emit(msg, False)
            QApplication.processEvents()
            if STM32RelayController.send_with_retry(cmd):
                self.log_signal.emit(ok_msg, False)
            else:
                self.log_signal.emit(f"ERROR: Failed — {msg}", True)
            QApplication.processEvents(); time.sleep(0.5)
            self.check_abort()

        # Steps 3-6 kept as log placeholders (same as original)
        for placeholder in [
            "Connecting power supply connector (J58)",
            "Connecting power supply connector (J60)",
            "Power Supply set to 28V",
        ]:
            self.log_signal.emit(placeholder, False)
            time.sleep(0.5)
            self.check_abort()
        
        self.log_signal.emit("Live voltage monitoring enabled", False)
        self.log_signal.emit("========== PSU AUTOMATION STARTING ==========", False)
        time.sleep(1)
        self.check_abort()


    # ── Stage 7: Relay connections for STBY mode ─────────────────────────────────

    def _connect_stby_relays(self):
        self.check_abort()
        self.log_signal.emit(
            "Connecting audio analyser input mic controller (J13) and phones connector (J15)", False
        )
        QApplication.processEvents()

        if STM32RelayController.send_with_retry(STM32RelayController.set_j13_on):
            self.log_signal.emit("J13 successfully connected", False); time.sleep(0.5)
            if STM32RelayController.send_with_retry(STM32RelayController.set_j15_on):
                self.log_signal.emit("J15 successfully connected", False); time.sleep(0.5)
            else:
                self.log_signal.emit("ERROR: Failed to connect J15", True)
        else:
            self.log_signal.emit("ERROR: Failed to connect J13/J15", True)

        QApplication.processEvents(); time.sleep(0.5)
        self.check_abort()

        self.log_signal.emit("Connecting audio analyser generator output (J27)", False)
        QApplication.processEvents()

        if STM32RelayController.send_with_retry(STM32RelayController.set_j27_on):
            self.log_signal.emit("J27 successfully connected", False); time.sleep(0.5)
        else:
            self.log_signal.emit("ERROR: Failed to connect J27", True)

        QApplication.processEvents(); time.sleep(0.5)
        self.check_abort()

        generator_control(self, level="750.0 uVrms", frequency=1000, state="on")

        self.log_signal.emit("Setting Switch S24 (NORM) to Down position", False)
        QApplication.processEvents()
        if STM32RelayController.send_with_retry(STM32RelayController.set_s24_off):
            self.log_signal.emit("Successfully set S24 to Down position", False); time.sleep(0.5)
        else:
            self.log_signal.emit("ERROR: Failed to set S24 to Down position", True)

        QApplication.processEvents(); time.sleep(0.5)
        self.check_abort()

        self.log_signal.emit("Setting Switch S25 (STBY) to UP position", False)
        QApplication.processEvents()
        if STM32RelayController.send_with_retry(STM32RelayController.set_s25_on):
            self.log_signal.emit("Successfully set S25 to UP position", False); time.sleep(0.5)
        else:
            self.log_signal.emit("ERROR: Failed to set S25 to UP position", True)

        QApplication.processEvents(); time.sleep(0.5)
        self.check_abort()
        
        # 🛑 PAUSE POINT
        self.check_abort()
        self.operator_event.clear()
        self.show_popup_signal.emit(
            "⚠ Operator Action Required",
            "• DS12 and DS13 indicators should illuminate red.\n",
            RESOURCES_DIR / "ds_12_13.jpeg","yes_no",None
        )

        # ⏸ WAIT until operator clicks OK
        self.operator_event.wait()
        time.sleep(0.5)
        self.log_signal.emit("===========INITIALIZATION COMPLETE=============", False)


    # ── Stage 8: Run all STBY-mode tests ─────────────────────────────────────────

    def _run_stby_tests(self):
        tests = self.selected_tests or list(self.TEST_MAP_stby.keys())
        for test in tests:
            self.check_abort()
            pre = self.TEST_PRE_STEPS_stby.get(test)
            if pre:
                pre(self)
            self.check_abort()
            func = self.TEST_MAP_stby.get(test)
            if func is None:
                continue   # no STBY implementation for this test — silently skip
            self.log_signal.emit(f"Running {test}", False)
            func(self)
            time.sleep(0.5)

        remove_tuning_hooks()
        self.log_signal.emit("==========All TESTS COMPLETED IN STBY MODE==========", False)


    # ── Stage 9: Teardown ─────────────────────────────────────────────────────────

    def _teardown_no_jb(self):
        self.log_signal.emit("Switching all relays to default state", False)
        QApplication.processEvents()
        if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
            self.log_signal.emit("All relays set to default states", False)
        else:
            self.log_signal.emit("ERROR: Failed to set relays to default states", True)

        time.sleep(2)
        self.check_abort()

        self.log_signal.emit("Ch1 OUTPUT OFF", False)
        self.log_signal.emit("✓ PSU automation COMPLETED", False)
        self.unfreeze_psu_front_panel()
        time.sleep(0.3)
        self.completion_signal.emit()
                
    def abortable_sleep(self, seconds: float, step: float = 0.1):
        """
        Sleep in small chunks so Abort works instantly.
        """
        end_time = time.time() + seconds
        while time.time() < end_time:
            self.check_abort()
            time.sleep(step)

    # ========================================================================
    # EXISTING METHODS (REFINED)
    # ========================================================================
    def showEvent(self, event):
        super().showEvent(event)
        for listener in getattr(self, "device_listeners", []):
            try:
                listener.resume()
            except Exception:
                pass

    def _cleanup_session(self, reset_relays: bool = False):
        """
        Full, synchronous teardown of everything this screen's session owns.
        Call this instead of abort_test_internal() directly whenever the user
        is navigating away (Back button) — abort_test_internal() alone leaves
        psu_thread/init_thread running and never releases the VISA handles,
        which is what causes the next screen's PSU/DMM/scope discovery to
        hang on a resource this screen never let go of.
        """
        self.abort_event.set()
        self._psu_shutdown_in_progress = True
        self._reconnect_generation += 1
        self.operator_event.set()
        self._psu_ready_event.set()
        self._force_close_all_dialogs()

        self._stop_worker_thread(self.psu_thread, "Test thread")
        self._stop_worker_thread(self.init_thread, "Init thread")

        self.abort_test_internal(reset_relays=reset_relays)

        for listener in getattr(self, "device_listeners", []):
            try:
                listener.stop()
                listener.wait(1500)
            except Exception:
                pass
        self.device_listeners = []

        try:
            if self.psu_inst:
                with self.psu_lock:
                    self.psu_inst.close()
        except Exception:
            pass
        self.psu_inst = None

        try:
            if getattr(self, "osc_conn", None):
                self.osc_conn.close_instrument_only()
        except Exception:
            pass
        self.osc_conn = None

        try:
            if self.rm:
                self.rm.close()
        except Exception:
            pass
        self.rm = None

        try:
            self.stop_voltage_monitoring()
        except Exception:
            pass

    def on_back_clicked(self):
        if self.test_running:
            confirmation = AbortTestConfirmationPopup(self)
            if confirmation.exec_() != QDialog.Accepted:
                return
            self._cleanup_session(reset_relays=False)

        if self.previous_screen:
            self.previous_screen.show()
        self.hide()
        


    def on_jbox_selection_changed(self, text):
        """
        Handle Junction Box selection change.
        - Enable/disable jbox fields
        - If ALH4 selected → only ALH2 allowed in station box
        """

        is_no_junction_box = (text == "No Junction Box")
        self.jbox_serial.setEnabled(not is_no_junction_box)
        self.mod_jbox_combo.setEnabled(not is_no_junction_box)

        # =====================================================
        # 🔴 IF JUNCTION BOX = ALH4 → ONLY ALH2 SUPPORTED
        # =====================================================
        if text.strip().upper() == "N200 - ALH4":

            # disable all except ALH2
            for i in range(self.alhx_combo.count()):
                item_text = self.alhx_combo.itemText(i)

                if item_text == "N200 - ALH2":
                    self.alhx_combo.model().item(i).setEnabled(True)
                else:
                    self.alhx_combo.model().item(i).setEnabled(False)

            # auto-switch to ALH2 if something else selected
            if self.alhx_combo.currentText() != "N200 - ALH2":
                self.alhx_combo.setCurrentText("N200 - ALH2")

        else:
            # =====================================================
            # 🟢 NORMAL MODE → enable all station options
            # =====================================================
            for i in range(self.alhx_combo.count()):
                self.alhx_combo.model().item(i).setEnabled(True)


    def toggle_lock_configuration(self):
        """Toggle between lock and unlock configuration state"""
        if self.config_locked:
            self.unlock_configuration()
        else:
            self.lock_configuration()

    def lock_configuration(self):
        """
        Lock configuration to prevent changes.
        Disables all configuration controls.
        """
        self.config_locked = True
        self.mod_combo.setEnabled(False)
        self.alhx_combo.setEnabled(False)
        self.alhx_serial.setEnabled(False)
        self.jbox_combo.setEnabled(False)
        self.jbox_serial.setEnabled(False)
        self.mod_jbox_combo.setEnabled(False)
        self.lock_btn.setText("Unlock")
        self.logger.log("Configuration locked", False)
        self.log_signal.emit("Configuration LOCKED - Ready to start test", False)

    def unlock_configuration(self):
        """
        Unlock configuration to allow changes.
        Re-enables all configuration controls.
        """
        self.config_locked = False
        self.mod_combo.setEnabled(True)
        self.alhx_combo.setEnabled(True)
        self.alhx_serial.setEnabled(True)
        # Re-apply junction box dependent state
        self.on_jbox_selection_changed(self.jbox_combo.currentText())

        self.lock_btn.setText("Lock On")
        self.logger.log("Configuration unlocked", False)
        self.log_signal.emit("Configuration UNLOCKED - You can now modify settings", False)

        # reapply entry restrictions
        self.apply_entry_mode()

    def start_test(self):
        """
        Start test after validation.
        Shows calibration dialog ONLY when No Junction Box / normal mode.
        """
        # ── Guard: ignore duplicate clicks while a test is already running ──
        if self.test_running:
            return

        # ── Guard 2: configuration must be locked before anything else ──
        if not self.config_locked:
            self.check_abort()
            self.show_popup_signal.emit(
                "Configuration Not Locked",
                "Please fill in all fields and click  'Lock On'  before starting the test.",
                None,
                "ok",
                None,
            )
            return
        
        # Validate control panel
        if not self.validate_control_panel():
            return
        self.log_signal.emit("Connecting with peripheral devices...", False)
        QApplication.processEvents()
        # AFTER:
        self._disconnect_done = False
        self._psu_error_handled = False
        self._disconnect_in_progress = False
        self._reconnect_in_progress = False
        self._disconnect_in_progress_psu = False
        self._psu_shutdown_in_progress = False
        self._reconnect_generation += 1   # orphan any reconnect thread left over from the last run
        self.voltage_stop_event.clear()
        self.overall_test_passed = True
        self.abort_event.clear()
        self.operator_event.clear()
        self._psu_ready_event.set()
        self._reconnect_event.clear()
        self.channel_ocp_limits.clear()
        self._ocp_tripped_channels.clear()
        RelayStateTracker.clear()

        # ── Register this screen for the relay wrappers, clear stale state ──
        self._relay_error_active = False
        self._skip_relay_reset_on_abort = False
        STM32RelayController.register_screen(self)
        STM32RelayController.reset_relay_error_state()
        self._popup_busy = False
        with self._popup_queue_lock:
            self._popup_queue.clear()

        # ── Fully stop (not just pause) listeners before we close their handles —
        # pause() only sets a flag and doesn't wait for an in-flight query to
        # finish, so closing psu_inst right after pause() can race a query
        # still executing on the listener thread. That race is a native VISA
        # driver call from two threads at once, which can crash the whole
        # process rather than raise a catchable Python exception.
        for listener in getattr(self, "device_listeners", []):
            try:
                listener.stop()
                listener.wait(1500)
            except Exception:
                pass
        self.device_listeners = []

        # ── Stop voltage monitor from previous run ──────────────────────
        try:
            self.stop_voltage_monitoring()
        except Exception:
            pass

        # ── Always close stale PSU handle and re-open fresh each run ──
        try:
            if self.psu_inst:
                try:
                    with self.psu_lock:
                        self.psu_inst.close()
                except Exception:
                    pass
                self.psu_inst = None
            # Reuse the existing ResourceManager if we already have one — only
            # create a new one if this is truly the first run (self.rm is None).
            # Closing and recreating rm here was invalidating osc_conn's separate
            # session on this VISA backend.
            import pyvisa as _pyvisa
            if self.rm is None:
                self.rm = _pyvisa.ResourceManager()
            self.psu_inst = self.find_psu()
            if self.psu_inst:
                print("[PSU] Fresh PSU handle opened at test start")
            else:
                print("[PSU] PSU not found at test start — will retry in init")
        except Exception as _fe:
            print(f"[PSU] PSU re-open at test start failed: {_fe}")
        # ── Force DMM reconnect fresh each run ──────────────────────────
        try:
            from core import dmm_reader
            dmm_reader.reset_dmm()
            print("[DMM] DMM handle reset — will reconnect fresh on first use")
        except Exception as _de:
            print(f"[DMM] DMM reset skipped (non-fatal): {_de}")
        try:
            if not dmm_reader.ensure_dmm_connected(self):
                self.log_signal.emit("DMM connection aborted by user.", True)
                return
        except Exception as _de:
            print(f"[DMM] ensure_dmm_connected failed: {_de}")
            
        # ── Force oscilloscope reconnect fresh each run ──────────────────
        try:
            from devices.oscilloscope_connection import OscilloscopeConnection
            from core.oscilloscope_helper import _get_active_non_osc_resources 
            if getattr(self, "osc_conn", None):
                try:
                    # close_instrument_only(), not close(): PSU/DMM are
                    # already open by this point in start_test() — closing
                    # the old scope's ResourceManager can invalidate their
                    # sessions on this VISA backend.
                    self.osc_conn.close_instrument_only()
                except Exception:
                    pass
            self.osc_conn = OscilloscopeConnection()
            self.osc_conn.claimed_visa_resources = _get_active_non_osc_resources(self)
            if self.osc_conn.discover_and_connect():
                ident = self.osc_conn.get_identification()
                print(f"[SCOPE] Fresh oscilloscope handle opened: {ident.manufacturer} {ident.model}")
            else:
                print("[SCOPE] Oscilloscope not found at test start — autoset will skip later")
        except Exception as _oe:
            print(f"[SCOPE] Oscilloscope reconnect failed (non-fatal): {_oe}")
        if self.psu_inst:
            try:
                with self.psu_lock:
                    self.psu_inst.write("*CLS")
                    time.sleep(0.2)
                    self.psu_inst.write("SYST:REM")
                    time.sleep(0.2)
                    self.psu_inst.write("*CLS")
                    time.sleep(0.2)

                    # Turn OFF all channels once before enabling CH3
                    for ch in (1, 2, 3):
                        self.psu_inst.write(f"INST:NSEL {ch}")
                        time.sleep(0.05)
                        self.psu_inst.write("OUTP OFF")
                        time.sleep(0.1)

                    self.psu_inst.write("INST:NSEL 3")
                    time.sleep(0.05)
                    self.psu_inst.write("SOUR3:VOLT 5.0"); time.sleep(0.5)
                    self.psu_inst.write("SOUR3:CURR 1.0"); time.sleep(0.5)
                    self.psu_inst.write("OUTP ON"); time.sleep(0.5)
                    time.sleep(0.3)
            except Exception as _pe:
                print(f"[PSU] CH3 pre-power failed (non-fatal): {_pe}")

        # ── PSU handle is now stable — update listener reference and resume ──
        for listener in getattr(self, "device_listeners", []):
            try:
                if isinstance(listener, PSUListener):
                    listener.psu_inst = self.psu_inst   # point to fresh handle
                    listener.fail_count = 0             # reset stale fail counter
                listener.resume()
            except Exception:
                pass

        try:
            sync_ok = STM32RelayController.send_with_retry(STM32RelayController.sync)
            if sync_ok:
                print("[STM32] Sync confirmed at test start")
            else:
                print("[STM32] Sync sent — no response (already synced or benign)")
        except Exception as _se:
            print(f"[STM32] Sync skipped at test start: {_se}")

        # ── Rename log file to reflect mode, model, and time ──────────────
        _log_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        if self.is_junction_box_mode():
            _jbox_model = (
                self.jbox_combo.currentText().strip()
                    .replace("N200 - ", "N200-")
                    .replace(" ", "-")
            )
            _log_name = f"ST_JNBX_{_jbox_model}_{_log_time}.log"
        else:
            _stbx_model = (
                self.alhx_combo.currentText().strip()
                    .replace("N200 - ", "N200-")
                    .replace(" ", "-")
            )
            _log_name = f"ST_STBX_{_stbx_model}_{_log_time}.log"

        self.logger = Logger(TEST_LOGS_DIR / _log_name)
        # ───────────────────────────────────────────────────────────────────

        self.lock_btn.setEnabled(False)
        self.start_btn.setEnabled(False)

        self.log_signal.emit("Connected with peripheral devices...", False)
        QApplication.processEvents()
        
        model = self.alhx_combo.currentText().strip()
        now = datetime.now()
        # ==========================================================
        # 🔴 CASE 1: JUNCTION BOX MODE (ALH4)
        # ==========================================================
        if self.is_junction_box_mode():
            set_generator_scale_factor(9.00)
            # 🔥 Load separate Junction Box template
            create_model_report("N200 - ALH4")   # Your separate JB template name

            # Employee Details
            write_excel("E3", self.session_name)
            write_excel("E4", self.session_id)

            # Station Box (ALH2 forced)
            write_excel("E5", model)
            write_excel("E6", self.alhx_serial.text().strip())
            write_excel("E8", self.mod_combo.text().strip())

            # 🔥 Junction Box Fields (Different Layout Area)
            write_excel("H3", "N200 - ALH4")
            write_excel("H4", self.jbox_serial.text().strip())
            write_excel("H5", self.mod_jbox_combo.text().strip())

            write_excel("E7", "Single Test - With Junction Box")

            write_excel("L4", now.strftime("%d-%m-%Y"))
            write_excel("L5", now.strftime("%H-%M-%S"))
            install_tuning_hooks(self)
        else:
            set_generator_scale_factor(1.66)
            create_model_report(model)
            # ================= HEADER DATA WRITE =================

            # Employee Details
            write_excel("C3", self.session_name)          # Employee Name
            write_excel("C4", self.session_id)            # Employee ID

            # LRU / Model
            write_excel("C5", model)                      # LRU (ALH1/2/3)

            # Serial Number
            write_excel("C6", self.alhx_serial.text().strip())

            # Test Type
            write_excel("C7", "Single test run")
            # MOD (ALH Module)
            write_excel("F3", self.mod_combo.text().strip())

            # Date & Time
            write_excel("J4", now.strftime("%d-%m-%Y"))   # Date
            write_excel("J5", now.strftime("%H-%M-%S"))   # Time
            install_tuning_hooks(self)
        # ✅ If Junction box mode (ALH4) → skip calibration popup
        if self.is_junction_box_mode():
            self.abort_event.clear()
            self.test_running = True
            self.logger.log("Junction Box mode ", False)
            self.log_text.clear()

            # ✅ Run initialization in background thread
            self.init_thread = InitializationThread(self)
            self.init_thread.start()
            return

        # ✅ Normal mode → show calibration popup
        calibration = CalibrationPopup(self, model=self.alhx_combo.currentText().strip())
        if calibration.exec_() == QDialog.Accepted:
            self.abort_event.clear()
            self.test_running = True
            self.logger.log("Calibration acknowledged - Starting test initialization", False)
            self.log_text.clear()

            # ✅ Run initialization in background thread
            self.init_thread = InitializationThread(self)
            self.init_thread.start()



    def run_initialization(self):
        if not self.is_junction_box_mode():
            box_init.run_init_sb(self)

        self.psu_thread = PSUAutomationThread(self)
        self.psu_thread.start()


        

    def start_device_monitoring(self):
        """
        Start device listeners. Reuses existing healthy listeners across runs
        instead of destroying and recreating them — avoids false-disconnect
        on second test run.
        """
        # ── PSU listener: reuse if already running, else create fresh ──
        existing_psu = next(
            (l for l in self.device_listeners if isinstance(l, PSUListener)),
            None
        )
        if existing_psu is not None and existing_psu.isRunning():
            existing_psu.psu_inst = self.psu_inst
            existing_psu.fail_count = 0
            existing_psu.resume()
            print("[DEVICE MONITOR] PSU listener reused from previous run")
        else:
            if not self.psu_inst:
                try:
                    if self.rm:
                        self.psu_inst = self.find_psu()
                except Exception as e:
                    print(f"[DEVICE MONITOR] find_psu skipped — rm not ready: {e}")
                    return
            if self.psu_inst:
                psu_listener = PSUListener(self.psu_inst, self.psu_lock)
                psu_listener.disconnected.connect(self.on_device_disconnected)
                self.device_listeners = [
                    l for l in self.device_listeners
                    if not isinstance(l, PSUListener)
                ]
                self.device_listeners.append(psu_listener)
                psu_listener.start()
                print("[DEVICE MONITOR] PSU listener created fresh")

        # ── STM32 listener: reuse if already running, else create fresh ──
        existing_stm32 = next(
            (l for l in self.device_listeners if isinstance(l, STM32Listener)),
            None
        )
        if existing_stm32 is not None and existing_stm32.isRunning():
            existing_stm32.resume()
            print("[DEVICE MONITOR] STM32 listener reused from previous run")
        elif hasattr(self, "stm32_serial") and self.stm32_serial:
            mcu_listener = STM32Listener(self.stm32_serial)
            mcu_listener.disconnected.connect(self.on_device_disconnected)
            self.device_listeners = [
                l for l in self.device_listeners
                if not isinstance(l, STM32Listener)
            ]
            self.device_listeners.append(mcu_listener)
            mcu_listener.start()
            print("[DEVICE MONITOR] STM32 listener created fresh")
    

    def _parse_log_line(self, message: str):
        """
        Returns list of (text, color) tuples for rich colorization.

        Rules:
        - Base text color: off-black #cccccc
        - Values with units (numbers + unit): green if PASS context, red if FAIL context
        - ✓ PASS / FAIL flags appended in matching color
        - ERROR lines handled separately in append_log
        """
        OFF_BLACK  = "#cccccc"
        PASS_GREEN = "#4caf50"
        FAIL_RED   = "#ef5350"

        # Detect overall pass/fail for this line
        # Detect overall pass/fail for this line
        upper = message.upper()
        is_pass_line = "PASS" in upper or "✅" in upper or "✓" in upper or "SUCCESS" in upper or "SUCCESSFULLY" in upper
        is_fail_line = "FAIL" in upper or "❌" in upper or "✗" in upper

        # Unit pattern: number followed by a known unit (with optional space)
        # Unit pattern: number followed by a known unit (with optional space)
        UNIT_PATTERN = re.compile(
            r'(?<![a-zA-Z])'                          # not preceded by a letter
            r'(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*'
            r'(Vrms|mVrms|uVrms|µVrms|dBrA|dBu|dBm|dB|mVrms|mV|kΩ|GΩ|MΩ|Ω|ohm|kHz|MHz|Hz|ms|µs|us|mA|mW|rpm|°C|°F|%|V|A|s|W)'
            r'(?=\s|,|;|\.|$|\)|\]|%)',
            re.IGNORECASE
        )

        # Remove trailing PASS/FAIL text — we'll re-append as flag
        clean = re.sub(r'\s*(✓\s*PASS|✗\s*FAIL|PASS|FAIL)\s*$', '', message, flags=re.IGNORECASE).rstrip()

        value_color = PASS_GREEN if is_pass_line else (FAIL_RED if is_fail_line else OFF_BLACK)

        parts = []
        OL_PATTERN = re.compile(r'\bOL\b', re.IGNORECASE)

        # Merge both patterns and sort by position
        matches = sorted(
            [(m, "unit") for m in UNIT_PATTERN.finditer(clean)] +
            [(m, "ol")   for m in OL_PATTERN.finditer(clean)],
            key=lambda x: x[0].start()
        )

        last = 0
        for m, kind in matches:
            if m.start() > last:
                parts.append((clean[last:m.start()], OFF_BLACK))
            parts.append((m.group(0), value_color))
            last = m.end()

        # Remaining text
        if last < len(clean):
            parts.append((clean[last:], OFF_BLACK))

        # Append check flag only if not already present in the message
        already_has_pass = "✓ PASS" in message or "PASS ✅" in message or "✅" in message
        already_has_fail = "✗ FAIL" in message or "FAIL ❌" in message or "❌" in message

        if is_pass_line and not already_has_pass:
            parts.append((" ✓ PASS", PASS_GREEN))
        elif is_fail_line and not already_has_fail:
            parts.append((" ✗ FAIL", FAIL_RED))

        return parts if parts else [(message, OFF_BLACK)]

    def append_log(self, message: str, error: bool = False):
        if getattr(self, "_psu_error_handled", False):
            # Allow reconnect-related messages through even during PSU error handling
            reconnect_keywords = ("PSU", "🔁", "✅", "⚠", "❌", "Relay", "reconnect", "Restoring")
            if not any(kw in message for kw in reconnect_keywords):
                return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_history.append((timestamp, message, error))

        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)

        def insert(text, color):
            fmt = self.log_text.currentCharFormat()
            fmt.setForeground(QColor(color))
            cursor.insertText(text, fmt)

        # Timestamp in dim gray
        insert(f"[{timestamp}] ", "#666666")

        if error:
            # Full line in red for errors
            insert(message + "\n", "#ef5350")
        elif message.startswith("==========") and message.endswith("=========="):
            # Section separator lines in yellow
            insert(message + "\n", "#fbc02d")
        else:
            # Parse for PASS/FAIL flags and value+unit patterns
            html_parts = self._parse_log_line(message)
            for text, color in html_parts:
                insert(text, color)
            insert("\n", "#cccccc")

        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
        self.logger.log(message, error)

        
    def show_test_completion(self):
        # 🔴 STOP MONITORING FIRST — before touching PSU
        # This prevents the monitor thread from seeing a "disconnect"
        # when we turn off PSU output below
        self._psu_error_handled = True        # ← block any PSU error callbacks
        self._disconnect_in_progress = True   # ← block disconnect popup trigger
        try:
            self.stop_voltage_monitoring()
        except Exception:
            pass
        # AFTER:
        try:
            self.unfreeze_psu_front_panel()
            self.psu_send_command("*CLS")
            time.sleep(0.05)
            self.psu_send_command("SYST:LOC")
            time.sleep(0.1)
        except Exception:
            pass
        for listener in getattr(self, "device_listeners", []):
            try:
                listener.pause()
            except Exception:
                pass
            # 🔴 TURN OFF PSU OUTPUT IMMEDIATELY
            
        self._turn_off_psu_channels([1, 2, 3], context="test completion")
        
        # ✅ Set disconnect flag AFTER stopping threads so no false trigger
        self._disconnect_in_progress = True

        self.test_running = False

        self.start_btn.setEnabled(True)
        
        self.lock_btn.setEnabled(True)       # ← re-enable lock button
        # self.unlock_configuration()

        # ================= WRITE RESULT FIRST =================
        # if self.overall_test_passed:
        #     test_result = "PASS"
        # else:
        #     test_result = "FAIL"
        
        
        test_result = "FAIL" if has_any_fail_in_report() else "PASS"

        if self.is_junction_box_mode():
            write_excel("L6", test_result)
        else:
            write_excel("J6", test_result)
        finalize_report()
        try:
            generator_control(self, state="off")  # ensure generator is off at end of test
        except Exception:
            pass  # APx may have crashed at end of test — generator off is best-effort only

        model_short = self.alhx_combo.currentText().strip().replace("N200 - ", "N200-").replace(" ", "-")
        jbox_short = self.jbox_combo.currentText().strip().replace("N200 - ", "N200-").replace(" ", "-")
        date_str = dt.now().strftime("%d%m%Y")
        time_str = dt.now().strftime("%H%M")

        if self.is_junction_box_mode():
            serial = self.jbox_serial.text().strip().replace(" ", "_") or "UNKNOWN"
            final_name = f"ST_{jbox_short}_JNBX_{serial}_{test_result}_{date_str}_{time_str}"
        else:
            serial = self.alhx_serial.text().strip().replace(" ", "_") or "UNKNOWN"
            final_name = f"ST_{model_short}_STBX_{serial}_{test_result}_{date_str}_{time_str}"
        report_path = rename_report(final_name)

        # ================= SHOW POPUP ONCE AFTER RESULT WRITTEN =================
        # Single test → save as PDF
        completion = TestCompletionModal(self, report_path=report_path, save_as_pdf=True, result=test_result)
        dialog_result = completion.exec_()

        # ✅ Clear logs regardless of Save or Close
        self.log_text.clear()
        self.logs_history.clear()
        self._per_test_results = {}
        self.overall_test_passed = True  # reset for next run
        self.channel_ocp_limits.clear()
        self._ocp_tripped_channels.clear()
        self._disconnect_done = False
        self._psu_error_handled = False
        self._disconnect_in_progress = False
        self._reconnect_in_progress = False
        self.voltage_stop_event.clear()
        self.abort_event.clear()
        self.operator_event.clear()
        self._reconnect_event.clear()          
        self._awaiting_reconnect_ack = False
        self._psu_ready_event.set()
        if getattr(self, "osc_conn", None):
            try:
                # PSU handle is still open at this point — close_instrument_only()
                # avoids invalidating it via a shared ResourceManager session.
                self.osc_conn.close_instrument_only()
            except Exception:
                pass
            self.osc_conn = None   
        self.log_signal.emit("Logs cleared after test completion.", False)
        


    def abort_test(self):
        if not self.test_running:
            popup = OperatorInfoPopup(
                title="Abort Test",
                message="No test is currently running.",
                image_path=RESOURCES_DIR / "remove.png",
                buttons="ok",
                timer_seconds=None,
                image_size=96,
                parent=self,
            )
            popup.exec_()
            return

        # ── Pause the test IMMEDIATELY — before the confirmation popup even
        # shows — so no other popup can slip in between. Also freeze popup
        # delivery so nothing already queued pops up while we wait.
        self._abort_pending_event.clear()
        self._popup_busy = True

        confirm = AbortTestConfirmationPopup(self)
        if confirm.exec_() != QDialog.Accepted:
            # ── Operator cancelled — resume the test right where it was ──
            self._popup_busy = False
            self._abort_pending_event.set()
            self._trigger_queue_signal.emit()   # let any queued popup show now
            return

        # ── Operator confirmed — release the popup gate (abort_event now
        # takes over) and proceed with the real abort ──
        self._popup_busy = False
        self._abort_pending_event.set()

        # ── 1. Signal abort ──────────────────────────────────────────
        self.abort_event.set()
        self._psu_shutdown_in_progress = True   # bail any in-flight reconnect ASAP
        self._reconnect_generation += 1         # orphan any reconnect thread now running
        self.operator_event.set()          # unblock any operator_event.wait()

        # ── Cut PSU outputs immediately — do not wait for worker threads to
        # unwind or for the operator to click through the save/discard
        # dialog further down; that can take seconds to minutes.
        # abort_test_internal() re-confirms this later; this just closes
        # the gap. Silent — print() only, nothing to the on-screen logs.
        try:
            self._safe_shutdown_all_psu_channels(context="abort - immediate")
        except Exception as e:
            print(f"[ABORT] Immediate PSU shutdown check failed: {e}")

        # Drop any test-flow popup still waiting in the queue — once abort
        # begins none of them should appear. Left unclear, closing the
        # currently-shown dialog below can trigger the next queued one to
        # pop up mid-abort, and if its widget gets force-closed in the same
        # tick that raises RuntimeError on the deleted Qt object.
        with self._popup_queue_lock:
            self._popup_queue.clear()

        self._force_close_all_dialogs()    # close open operator popups

        # ── 2. Let worker threads exit cleanly first; terminate only as fallback ──
        self._stop_worker_thread(self.psu_thread, "Test thread")
        self._stop_worker_thread(self.init_thread, "Init thread")

        # ── 3. Ask operator: save partial report or discard? ─────────
        #    (runs on main thread — safe because threads are already dead)
        self._show_abort_save_dialog()

    def _show_abort_save_dialog(self):
        # --- build dialog ---
        dlg = QDialog(self)
        dlg.setWindowTitle("Test Aborted")
        dlg.setModal(True)
        dlg.setFixedWidth(420)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        icon_label = QLabel("⚠")
        icon_label.setFont(QFont("Arial", 28))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel("Test was aborted")
        title_label.setFont(QFont("Arial", 13, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #d32f2f;")
        layout.addWidget(title_label)

        body_label = QLabel(
            "Results collected so far have been recorded in the report.\n"
            "Would you like to save the partial report or discard it?"
        )
        body_label.setWordWrap(True)
        body_label.setAlignment(Qt.AlignCenter)
        body_label.setStyleSheet("color: #555555; font-size: 11px;")
        layout.addWidget(body_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        save_btn = QPushButton("💾  Save Partial Report")
        save_btn.setMinimumHeight(38)
        save_btn.setFont(QFont("Arial", 10, QFont.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
        """)

        discard_btn = QPushButton("🗑  Discard")
        discard_btn.setMinimumHeight(38)
        discard_btn.setFont(QFont("Arial", 10, QFont.Bold))
        discard_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #616161; }
            QPushButton:pressed { background-color: #424242; }
        """)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(discard_btn)
        layout.addLayout(btn_row)

        self._abort_save_choice = "discard"

        def on_save():
            self._abort_save_choice = "save"
            dlg.accept()

        def on_discard():
            self._abort_save_choice = "discard"
            dlg.accept()

        save_btn.clicked.connect(on_save)
        discard_btn.clicked.connect(on_discard)

        dlg.exec_()   # blocks until user clicks — main thread, no background threads running yet

        # ── Save report and show TestCompletionModal FIRST ──────────
        if self._abort_save_choice == "save":
            try:
                from datetime import datetime as _dt

                result = "FAIL" if has_any_fail_in_report() else "PASS"
                self._abort_report_result = result

                if self.is_junction_box_mode():
                    write_excel("L6", result + " (PARTIAL)")
                else:
                    write_excel("G4", result + " (PARTIAL)")

                finalize_report()

                model_short = (
                    self.alhx_combo.currentText().strip()
                        .replace("N200 - ", "N200-")
                        .replace(" ", "-")
                )
                date_str = _dt.now().strftime("%d%m%Y")
                time_str = _dt.now().strftime("%H%M")

                if self.is_junction_box_mode():
                    serial = self.jbox_serial.text().strip().replace(" ", "_") or "UNKNOWN"
                    final_name = f"ABORT_{model_short}_JNBX_{serial}_{result}_{date_str}_{time_str}"
                else:
                    serial = self.alhx_serial.text().strip().replace(" ", "_") or "UNKNOWN"
                    final_name = f"ABORT_{model_short}_STBX_{serial}_{result}_{date_str}_{time_str}"

                # ✅ rename ONCE only
                report_path = rename_report(final_name)
                self.log_signal.emit(f"Partial report saved as: {final_name}", False)

                # ✅ Show TestCompletionModal NOW — before relay reset popup
                # This runs on main thread, no background thread conflict
                completion = TestCompletionModal(
                    self,
                    report_path=report_path,
                    save_as_pdf=True,
                    result=result
                )
                completion.exec_()   # user clicks OK/Save here — blocks cleanly

            except Exception as e:
                self.log_signal.emit(f"Report save failed: {e}", True)
        else:
            self.log_signal.emit("Partial report discarded.", False)

        # ── NOW show 'Terminating Test' popup + start relay reset ───
        self.terminating_popup = OperatorInfoPopup(
            title="Terminating Test",
            message=(
                "Stopping test…\n"
                "Switching all relays to default state.\n\n"
                "Please wait — OK will become available\n"
                "once all relays have been reset."
            ),
            image_path=None,
            buttons="ok",
            timer_seconds=None,
            parent=self,
        )

        # Disable OK until relay reset completes
        QTimer.singleShot(0, self._disable_terminating_ok)
        self.terminating_popup.show()
        self.terminating_popup.finished.connect(lambda _: self._on_abort_popup_closed())
        QApplication.processEvents()

        # ── Start relay reset in background ──────────────────────────
        # If the abort was triggered by a relay-comms failure (Problems 1/4),
        # skip set_default_states() — the bus is already unreliable.
        self._abort_worker = AbortWorkerThread(
            self, reset_relays=False
        )
        self._abort_worker.finished.connect(self._on_abort_finished)
        self._abort_worker.start()


    def _on_abort_finished(self):
        """
        Called on main thread when AbortWorkerThread finishes.
        Relays are now in default state — re-enable OK button only.
        TestCompletionModal was already shown BEFORE this point.
        """
        try:
            if hasattr(self, "terminating_popup") and self.terminating_popup is not None:
                for btn in self.terminating_popup.findChildren(QPushButton):
                    btn.setEnabled(True)
                    btn.setToolTip("")
                self.log_signal.emit("✓ All relays reset — you may now close the popup.", False)
        except RuntimeError:
            pass

    def _disable_terminating_ok(self):
        """Disable every QPushButton inside the terminating popup."""
        if not hasattr(self, "terminating_popup") or self.terminating_popup is None:
            return
        for btn in self.terminating_popup.findChildren(QPushButton):
            btn.setEnabled(False)
            btn.setToolTip("Please wait until relay reset is complete.")


    def _on_abort_popup_closed(self):
        """
        Operator clicked OK on the terminating popup.
        Now safe to clear logs and reset state.
        """
        self.terminating_popup = None
        # ── Clear popup queue so stale PSU popups don't resurface after abort ──
        with self._popup_queue_lock:
            self._popup_queue.clear()
        self._popup_busy = False
        self.log_text.clear()
        self.logs_history.clear()
        self.log_signal.emit("Logs cleared after abort.", False)

    def channel_2_off(self):
        try:
            self.psu_send_command("INST:NSEL 2")
            time.sleep(0.5)
            self.psu_send_command("OUTP OFF")
            time.sleep(0.5)
            self.log_signal.emit("Channel 2 turned OFF", False)
        except Exception as e:
            self.log_signal.emit(f"Failed to turn off Channel 2: {e}", True)
            
            
    def abort_test_internal(self, reset_relays=True):
        """Forcefully abort running test + cleanup"""

        # ⚠️ DO NOT call _force_close_all_dialogs here — this runs on a background
        # thread during abort. Dialog closing must happen on the main thread only.
        # _force_close_all_dialogs() is called in abort_test() on the main thread.

        self._psu_shutdown_in_progress = True
        self._reconnect_generation += 1
        try:
            generator_control(self, state="off")
        except Exception:
            pass  # APx crash during abort cleanup — safe to ignore
        # 🔴 TURN OFF PSU OUTPUT IMMEDIATELY — authoritative path, rediscovers
        # the PSU if psu_inst is stale/None rather than silently skipping.
        self._safe_shutdown_all_psu_channels(context="abort")

        # ← ADD HERE
        try:
            self.unfreeze_psu_front_panel()
        except Exception:
            pass
        
        try:
            self.psu_send_command("*CLS")
            time.sleep(0.5)
            self.psu_send_command("SYST:LOC")
            time.sleep(0.1)
        except Exception:
            pass
        # 🔥 SAVE REPORT
        try:
            finalize_report()
            if getattr(self, "_abort_save_choice", "save") == "save":
                self.log_signal.emit("Report saved successfully", False)
        except Exception as e:
            self.log_signal.emit(f"Report save failed: {e}", True)

        # 🔴 RESET RELAYS
        if reset_relays:
            try:
                self.log_signal.emit("Switching all relays to default state...", True)
                if STM32RelayController.send_with_retry(STM32RelayController.set_default_states):
                    self.log_signal.emit("✓ All relays successfully set to default state", False)
                else:
                    self.log_signal.emit("WARNING: Some relays may not have reset to default", True)
            except Exception as e:
                self.log_signal.emit(f"Relay reset failed during abort: {e}", True)
                
        remove_tuning_hooks()
        RelayStateTracker.clear()
        self.channel_ocp_limits.clear()
        self._ocp_tripped_channels.clear()
        self.test_running = False
        self.start_btn.setEnabled(True)   # ⚠️ This emits to main thread via Qt — safe via signal

        try:
            self.operator_event.set()
        except Exception:
            pass
        self._psu_ready_event.set()
        try:
            self.stop_voltage_monitoring()
        except Exception:
            pass

        for listener in getattr(self, "device_listeners", []):
            try:
                listener.pause()
            except Exception:
                pass

        self.unlock_configuration()
        self.lock_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self._disconnect_done = False
        self._psu_error_handled = False
        self._disconnect_in_progress = False
        self._reconnect_in_progress = False
        self._reconnect_event.clear()          
        self._awaiting_reconnect_ack = False   

        self.log_signal.emit("✗ Test aborted by user", True)



    def _force_close_all_dialogs(self):
        """
        Force close ALL modal/non-modal dialogs when device disconnects.
        """
        for widget in QApplication.topLevelWidgets():
            if widget is self:
                continue

            # Close all dialogs
            if isinstance(widget, QDialog):
                widget.reject()

            # Close any message boxes
            if isinstance(widget, QMessageBox):
                widget.close()

    def _stop_worker_thread(self, thread, label: str, graceful_ms: int = 2500, force_ms: int = 2000):
        """
        abort_event/operator_event are already set by the time this is called,
        so the worker thread's check_abort() / relay-escalation wait() should
        already be raising TEST_ABORTED_BY_USER and unwinding on its own —
        which properly releases psu_lock via its `with` block.

        terminate() is a last resort: it's an OS-level kill that bypasses
        Python's exception unwinding entirely, so if the thread is killed
        mid `with self.psu_lock:` the lock never gets released and every
        subsequent PSU command (including our own abort cleanup) hangs forever.
        """
        if thread is None or not thread.isRunning():
            return
        if thread.wait(graceful_ms):
            print(f"[{label}] Test paused.")
            return
        self.log_signal.emit(f"{label} did not stop in time — forcing stop.", True)
        thread.terminate()
        thread.wait(force_ms)
        self._reset_psu_lock_if_stuck()

    def _reset_psu_lock_if_stuck(self):
        """
        A forcefully terminated worker thread may have been killed while
        holding self.psu_lock. Python's Lock can't be force-released from
        outside, so if it's still locked, swap in a fresh one rather than
        let every future PSU command hang forever.
        """
        try:
            if self.psu_lock.locked():
                self.log_signal.emit(
                    "⚠ PSU lock appeared stuck after forced stop — resetting it.", True
                )
                self.psu_lock = Lock()
        except Exception:
            pass

    def on_device_disconnected(self, device: DeviceType, message: str):
        if self._disconnect_in_progress:
            return
        if getattr(self, "_reconnect_in_progress", False):
            return
        if getattr(self, "_psu_error_handled", False):
            return

        lock = getattr(self, "_reconnect_lock", None)
        if lock is not None and not lock.acquire(blocking=False):
            print("[DISCONNECT HANDLER] Reconnect lock held — skipping")
            return
        if lock is not None:
            lock.release()

        if device == DeviceType.PSU:
            if getattr(self, "_disconnect_in_progress", False):
                return
            self._psu_error_handled = True
            import threading
            threading.Thread(
                target=self._background_reconnect,
                daemon=True,
                name="PSU-reconnect-listener"
            ).start()
            return

        # Non-PSU device (e.g. STM32) — hard abort
        self._disconnect_in_progress = True
        self._psu_shutdown_in_progress = True
        self._reconnect_generation += 1
        self.abort_test_internal(reset_relays=False)   # abort_test_internal now performs
                                                          # the authoritative PSU shutdown itself
        try:
            self.operator_event.set()
        except Exception:
            pass
        self.stop_voltage_monitoring()
        # Belt-and-suspenders: abort_test_internal already shut all channels off,
        # but confirm explicitly in case this handler races ahead of it.
        self._safe_shutdown_all_psu_channels(context="device disconnect")
        for listener in self.device_listeners:
            listener.stop()
            listener.wait()
        self._force_close_all_dialogs()
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(f"{device.value} Disconnected")
        msg.setText(f"{message}\nTest aborted.\nReturning to connection screen…")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.buttonClicked.connect(
            lambda _: (
                self.return_to_connection.emit(),
                QTimer.singleShot(100, self.close),
            )
        )
        msg.exec_()


    def closeEvent(self, event):
        # ─────────────────────────────────────────────────────────────────
        # If a test is running we must abort it cleanly BEFORE closing,
        # so relays get time to settle and the PSU is switched off.
        # ─────────────────────────────────────────────────────────────────
        
        if self.test_running:
            event.ignore()

            popup = OperatorInfoPopup(
                title="⚠ Test In Progress",
                message=(
                    "A test is currently running.\n\n"
                    "Please click  'Abort Test'  first and wait for it\n"
                    "to finish, then close the window.\n\n"
                    "Click  'Force Close'  only if absolutely necessary\n"
                    "(relays will NOT be reset)."
                ),
                image_path=None,
                buttons="yes_no",   # yes = Force Close, no = Cancel
                timer_seconds=None,
                parent=self,
            )
            # Relabel the buttons so intent is clear
            for btn in popup.findChildren(QPushButton):
                # after
                if btn.text().strip().upper() in ("YES", "Y"):
                    btn.setText("Force Close")
                    btn.setMinimumWidth(160)
                    btn.setMinimumHeight(36)
                    btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #d32f2f;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 8px 20px;
                            font-weight: bold;
                        }
                        QPushButton:hover { background-color: #b71c1c; }
                    """)
                elif btn.text().strip().upper() in ("NO", "N"):
                    btn.setText("Cancel")
                    btn.setMinimumWidth(100)
                    btn.setMinimumHeight(36)

            result = popup.exec_()

            if result == QDialog.Accepted:
                # Force Close — run cleanup on a background thread instead of
                # blocking the GUI. ...
                self.abort_event.set()
                self._psu_shutdown_in_progress = True   # stop any live reconnect NOW
                self._reconnect_generation += 1
                self.operator_event.set()

                # ── Same immediate cutoff as Abort — worker-thread stop and
                # the "cleaning up" popup below can still take a while.
                # Silent — print() only.
                try:
                    self._safe_shutdown_all_psu_channels(context="force close - immediate")
                except Exception as e:
                    print(f"[FORCE CLOSE] Immediate PSU shutdown check failed: {e}")

                self._force_close_all_dialogs()

                self._close_popup = OperatorInfoPopup(
                    title="Closing Application",
                    message=(
                        "Cleaning up and closing…\n\n"
                        "Please wait — this window will close automatically."
                    ),
                    image_path=None,
                    buttons="ok",
                    timer_seconds=None,
                    parent=self,
                )
                for btn in self._close_popup.findChildren(QPushButton):
                    btn.setEnabled(False)
                    btn.setToolTip("Please wait until cleanup is complete.")
                self._close_popup.show()
                QApplication.processEvents()

                self._stop_worker_thread(self.psu_thread, "Test thread")
                self._stop_worker_thread(self.init_thread, "Init thread")

                self._close_worker = AbortWorkerThread(
                    self, reset_relays=False
                )
                self._close_worker.finished.connect(self._on_close_abort_finished)
                self._close_worker.start()
            # else: Cancel — window stays open, user uses Abort Test button
            return
        # ── Normal close (no test running) ───────────────────────────────
        try:
            if self.voltage_monitor_thread:
                self.stop_voltage_monitoring()

            for listener in getattr(self, "device_listeners", []):
                listener.stop()
                listener.wait()

        except Exception:
            pass

        # ── Turn off ALL PSU channels before closing ─────────────────────
        # Mirrors show_test_completion so channels are off whether or not
        # the user clicked Abort first.
        
        self._safe_shutdown_all_psu_channels(context="window close")
        
        try:
            app_instance = QApplication.instance()
            if hasattr(app_instance, "_trigger_psu_shutdown"):
                app_instance._trigger_psu_shutdown(existing_psu=self.psu_inst)
            # Do NOT set self.psu_inst = None here; let the hook own lifetime.
        except Exception:
            pass

        event.accept()

    def _on_close_abort_finished(self):
        """
        Called on the main thread once AbortWorkerThread completes.
        Relays have settled → safe to close the window now.
        """
        # Close the "please wait" popup
        try:
            if hasattr(self, "_close_popup") and self._close_popup is not None:
                self._close_popup.close()
                self._close_popup = None
        except Exception:
            pass

        # Stop remaining background resources
        try:
            if self.voltage_monitor_thread:
                self.stop_voltage_monitoring()

            for listener in getattr(self, "device_listeners", []):
                listener.stop()
                listener.wait()
        except Exception:
            pass

        # ── Final belt-and-suspenders PSU shutdown right before the window
        # actually closes — covers the case where a worker thread had to be
        # force-terminate()'d mid PSU-command. print() only, no log_signal:
        # the log widget is being torn down and nothing needs to show
        # on-screen at this point.
        try:
            self._safe_shutdown_all_psu_channels(context="force close - final cleanup")
        except Exception as e:
            print(f"[FORCE CLOSE] Final PSU shutdown check failed: {e}")

        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SingleTestScreen()
    win.show()
    sys.exit(app.exec_())