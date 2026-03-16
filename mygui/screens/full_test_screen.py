from dialogs.calibration_popup import CalibrationPopup
from dialogs.test_completion_dialog import TestCompletionModal
from dialogs.abort_test_dialog import AbortTestConfirmationPopup
from dialogs.disconnect_result_dialog import DisconnectResultDialog
from dialogs.OperatorInfoPopup import OperatorInfoPopup
from dialogs.logs_viewer_dialog import LogsViewerDialog
from threading import Event
from core.logger import Logger
from core.paths import RESOURCES_DIR, LOGS_DIR,SESSION_FILE
from core.stm32_commands import STM32RelayController
from core.excel_logger import create_model_report,finalize_report,write_excel


import time
from datetime import datetime
from PyQt5.QtGui import QFont, QPixmap, QColor, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize, QThread
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, QDialog,
    QScrollArea, QSizePolicy, QGridLayout, QFrame, QMessageBox, QApplication
)
import pyvisa
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
    jb_seq
)

from devices.apx_analyzer import configure_apx,generator_control



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


# ============================================================================
# SCREEN 4: FULL TEST SCREEN (MODIFIED HEADER WITH BACK BUTTON)
# ============================================================================
class FullTestScreen(QMainWindow):
    """
    Main test execution screen with PSU automation, configuration management,
    and live voltage/current monitoring.
    """
    test_completed = pyqtSignal()
    return_to_test_selection = pyqtSignal()
    return_to_connection = pyqtSignal()
    log_signal = pyqtSignal(str, bool) 
    show_popup_signal = pyqtSignal(str, str, object, str, object)



    
    def __init__(self):
        super().__init__()
        self.show_popup_signal.connect(self.show_operator_popup)
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

        self.operator_event = Event()
        self.device_listeners = []
        self.overall_test_passed = True
        self.logs_history = [] # To store (timestamp, message, is_error)
        self._disconnect_in_progress = False
        self.abort_event = Event()   # ✅ For immediate termination request
        self.psu_thread = None       # ✅ Track the running automation thread
        self.init_thread = None


        self.setWindowTitle("HAL - Full Test")
        self.setGeometry(50, 50, 1400, 950)
        self.setMinimumSize(QSize(1000, 750))
        self.setStyleSheet("background-color: #f5f5f5;")
        self.log_signal.connect(self.append_log)
        self.logger = Logger(LOGS_DIR / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
        alhx_model_label = QLabel("Station Box:")
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

        # graphs_btn = QPushButton("📊 Graphs")
        # graphs_btn.setMinimumHeight(44)
        # graphs_btn.setFont(QFont("Arial", 10, QFont.Bold))
        # graphs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # graphs_btn.setIconSize(QSize(18, 18))
        # graphs_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #f57c00;
        #         color: white;
        #         border: none;
        #         border-radius: 4px;
        #         padding: 10px 16px;
        #         font-weight: bold;
        #     }
        #     QPushButton:hover {
        #         background-color: #e65100;
        #     }
        #     QPushButton:pressed {
        #         background-color: #d44d00;
        #     }
        # """)
        # action_layout.addWidget(graphs_btn)

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


        # Initialize junction box dependent state
        self.on_jbox_selection_changed(self.jbox_combo.currentText())


    def is_junction_box_mode(self) -> bool:
        station = self.alhx_combo.currentText().strip().upper()
        jbox = self.jbox_combo.currentText().strip().upper()
        return station in ["ALH1", "ALH2", "ALH3"] and jbox == "ALH4"

    
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
    # STEP 1: CONTROL PANEL VALIDATION
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
        if not self.mod_combo.currentText():
            self.show_validation_error("ALHx Module (MOD) must be selected")
            return False
        
        # Check Junction Box dependent fields
        jbox_selection = self.jbox_combo.currentText()
        if jbox_selection != "No Junction Box":
            # Junction Box is selected - validate dependent fields
            if not self.jbox_serial.text().strip():
                self.show_validation_error("Junction Box Serial Number must be filled")
                return False
            
            if not self.mod_jbox_combo.currentText():
                self.show_validation_error("Junction Box Module (MOD) must be selected")
                return False
        
        # Check if configuration is locked
        if not self.config_locked:
            self.show_validation_error("Configuration must be LOCKED before starting the test")
            return False
        
        return True

    def start_voltage_monitoring(self):
        if self.voltage_monitor_thread and self.voltage_monitor_thread.isRunning():
            return

        self.voltage_stop_event.clear()

        self.voltage_monitor_thread = VoltageMonitorThread(
            psu_send_command=self.psu_send_command,
            stop_event=self.voltage_stop_event
        )

        self.voltage_monitor_thread.voltage_signal.connect(
            self.on_voltage_update
        )
        self.voltage_monitor_thread.error_signal.connect(
            lambda e: self.log_signal.emit(f"Voltage monitor error: {e}", True)
        )

        self.voltage_monitor_thread.start()
        self.log_signal.emit("Live voltage monitoring STARTED", False)


    def stop_voltage_monitoring(self):
        if self.voltage_monitor_thread:
            self.voltage_stop_event.set()
            self.voltage_monitor_thread.wait()
            self.voltage_monitor_thread = None
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
        Display validation error message in popup dialog.
        
        Args:
            message: Error message to display
        """
        QMessageBox.warning(self, "Validation Error", message, QMessageBox.Ok)

    # ========================================================================
    # STEP 2: PSU AUTOMATION METHODS (DP832 DATASHEET COMPLIANT)
    # ========================================================================
    from psu.psu_helpers import find_psu
  
    def psu_send_command(self, command: str) -> str:

        try:

            if not self.psu_inst:
                self.log_signal.emit("ERROR: PSU not initialized", True)
                return ""

            with self.psu_lock:

                if "?" in command:
                    return self.psu_inst.query(command).strip()
                else:
                    self.psu_inst.write(command)
                    return ""

        except Exception as e:

            if not self._disconnect_in_progress:
                self._disconnect_in_progress = True

                self.log_signal.emit(f"PSU COMMUNICATION LOST: {e}", True)

                QTimer.singleShot(
                    0,
                    lambda: self.on_device_disconnected(
                        DeviceType.PSU,
                        "Power Supply communication lost.\nTest aborted."
                    )
                )

            return ""


    def freeze_psu_front_panel(self):
        """
        Lock PSU front panel to prevent manual changes during automation.
        
        SCPI Command: SYST:LOCK ON (DP832 Datasheet §5.2)
        """
        self.psu_send_command(PSUCommands.SYSTEM_LOCK_ON)
        self.log_signal.emit("PSU front panel LOCKED (SYST:LOCK ON)", False)

    def unfreeze_psu_front_panel(self):
        """
        Unlock PSU front panel to allow manual changes.
        
        SCPI Command: SYST:LOCK OFF (DP832 Datasheet §5.2)
        """
        self.psu_send_command(PSUCommands.SYSTEM_LOCK_OFF)
        self.log_signal.emit("PSU front panel UNLOCKED (SYST:LOCK OFF)", False)
    

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
        Current: 1.3A
        Output ON until task completes
        """

        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 1")
        time.sleep(0.1)

        self.psu_send_command("SOUR1:VOLT 28.0")
        self.psu_send_command("SOUR1:CURR 1.3")

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        
        self.current_channel = 1
        self.log_signal.emit("Ch1 OUTPUT ON (28V, 1.3A)", False)
        self.operator_event.clear()
        # self.show_popup_signal.emit(
        #     "Channel 1 Active",
        #     "Channel 1 is ON at 28V.\nClick OK to proceed.",
        #     None,"ok",None
        # )
        # self.operator_event.wait()
        self.log_signal.emit("Operator confirmed Channel 1", False)
        time.sleep(15)

        


        # -------------------------------------------------
        # ADD YOUR LOGIC HERE
        # Output remains ON until this logic completes
        

        

    
    def worker_ch2_28v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)

        self.psu_send_command("SOUR2:VOLT 28.0")
        self.psu_send_command("SOUR2:CURR 1.3")

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        self.current_channel = 2
        self.log_signal.emit("Ch2 OUTPUT ON (28V, 1.3A)", False)
        
        # ADD YOUR LOGIC HERE
        time.sleep(15)
        self.psu_send_command("OUTP OFF")
        self.stop_voltage_monitoring()
        self.log_signal.emit("Ch2 OUTPUT OFF (28V step complete)", False)

    def worker_ch2_12v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)

        self.psu_send_command("SOUR2:VOLT 12.0")
        self.psu_send_command("SOUR2:CURR 1.3")

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        self.current_channel = 2
        self.log_signal.emit("Ch2 OUTPUT ON (12V, 1.3A)", False)

        # ADD YOUR LOGIC HERE

        self.psu_send_command("OUTP OFF")
        self.stop_voltage_monitoring()
        self.log_signal.emit("Ch2 OUTPUT OFF (16V step complete)", False)

    def worker_ch2_5v(self):
        self.psu_send_command("*CLS")
        self.psu_send_command("INST:NSEL 2")
        time.sleep(0.1)

        self.psu_send_command("SOUR2:VOLT 5.0")
        self.psu_send_command("SOUR2:CURR 1.3")

        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        self.current_channel = 2
        self.log_signal.emit("Ch2 OUTPUT ON (5V, 1.3A)", False)

        # ADD YOUR LOGIC HERE

        self.psu_send_command("OUTP OFF")
        self.stop_voltage_monitoring()
        self.log_signal.emit("Ch2 OUTPUT OFF (8V step complete)", False)
        
    
    
    
    def run_channel_sequence(self, channel: int):
        print("\n==============================")
        print(f"ENTER run_channel_sequence(channel={channel})")
        print("==============================")

        self.debug_active_channel("START")

        self.psu_send_command("*CLS")
        self.psu_send_command(f"INST:NSEL {channel}")
        time.sleep(0.1)

        self.debug_active_channel("AFTER INST:NSEL")

        # 🔴 SET VOLTAGE / CURRENT
        self.psu_send_command(f"SOUR{channel}:VOLT 28.0")
        self.psu_send_command(f"SOUR{channel}:CURR 1.35")


        self.debug_active_channel("AFTER SET V/I")

        # 🔴 OUTPUT ON
        self.psu_send_command("OUTP ON")
        time.sleep(0.5)   # ⏳ let PSU settle
        self.start_voltage_monitoring()
        time.sleep(0.2)

        self.debug_active_channel("AFTER OUTP ON")

        out_state = self.psu_send_command("OUTP?")
        print(f"CHANNEL {channel} OUTPUT STATE AFTER ON:", out_state)

        self.current_channel = channel
        self.log_signal.emit(f"Ch{channel} OUTPUT ON", False)


        self.debug_active_channel("BEFORE OUTP OFF")

        self.psu_send_command("*CLS")
        self.psu_send_command(f"INST:NSEL {channel}")
        self.psu_send_command("OUTP OFF")
        self.stop_voltage_monitoring()

        self.debug_active_channel("AFTER OUTP OFF")

        self.log_signal.emit(f"Ch{channel} OUTPUT OFF", False)


    
    
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

    def update_voltage_label(self):
        """Update top-right voltage/current label with live readings"""
        channel_str = f"CH{self.current_channel}" if self.current_channel else "PSU"
        self.voltage_label.setText(
            f"Power Supply: {channel_str} → {self.voltage_value:.2f} V | {self.current_value:.2f} A"
        )
    
    def show_operator_popup(self, title, message, image_path=None, buttons="ok", timer_seconds=None):
        if getattr(self, "_disconnect_in_progress", False):
            return

        popup = OperatorInfoPopup(
            title=title,
            message=message,
            image_path=image_path,
            buttons=buttons,
            timer_seconds=timer_seconds,
            parent=self
        )

        def handle_result(result):
            # 🔥 GET result from popup
            res, operator = popup.get_result()

            # store globally for excel
            self.last_test_result = res
            self.last_operator_response = operator

            print("RESULT:", res)
            print("OPERATOR:", operator)

            if buttons == "yes_no":
                if result == QDialog.Accepted:
                    # YES → PASS
                    self.operator_event.set()
                else:
                    # NO → FAIL but continue test
                    self.log_signal.emit("Operator clicked NO, continuing test...", True)
                    self.operator_event.set()
            else:
                self.operator_event.set()

        popup.finished.connect(handle_result)
        popup.show()
    def check_abort(self):
        """
        Call this frequently inside long-running processes.
        Raises Exception to break thread execution instantly.
        """
        if self.abort_event.is_set():
            raise Exception("TEST_ABORTED_BY_USER")


    # ========================================================================
    # STEP 3: RUN PSU AUTOMATION SEQUENCE
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
            jb_seq.run_norm(self)
            time.sleep(0.5)
            jb_seq.run_stby(self)
            time.sleep(0.5)
            self.log_signal.emit("========== ALL JUNCTION BOX TESTS COMPLETED ==========", False)
            QTimer.singleShot(500, self.show_test_completion)

        except Exception as e:
            self.log_signal.emit(f"ERROR: Junction Box PSU automation failed - {str(e)}", True)

    def run_psu_automation_no_jbox(self):
        try:
            
            if not self.psu_inst:
                self.psu_inst = self.find_psu()

            if not self.psu_inst:
                self.log_signal.emit("ERROR: PSU not found", True)
                return
            self.test_running = True
            # 🔑 Enter REMOTE mode ONCE
            self.psu_send_command("SYST:REM")
            time.sleep(0.2)

            # 🔥 HARD RE-BIND CHANNEL CONTEXT (CRITICAL)
            self.psu_send_command("INST:NSEL 1")
            time.sleep(0.1)

            # 🔒 Lock front panel AFTER setup
            self.freeze_psu_front_panel()
            time.sleep(0.2)

            # 🔑 RE-ENTER REMOTE MODE (CRITICAL FIX)
            self.psu_send_command("SYST:REM")
            time.sleep(0.2)

            # 🔁 Force starting channel to CH1
            self.psu_send_command("INST:NSEL 1")
            time.sleep(0.1)



            # ▶ CHANNEL 1 SEQUENCE
            self.worker_channel_1()
            time.sleep(2)

            # # ▶ CHANNEL 2 SEQUENCE – STEP 1
            # self.worker_ch2_28v()
            # time.sleep(1)

            # # ▶ CHANNEL 2 SEQUENCE – STEP 2
            # self.worker_ch2_12v()
            # time.sleep(1)

            # # ▶ CHANNEL 2 SEQUENCE – STEP 3
            # self.worker_ch2_5v()
            # time.sleep(1)

            # 🔓 Unlock PSU
            # self.unfreeze_psu_front_panel()
            # time.sleep(0.3)


            #ggs
            self.check_abort()
            

            self.log_signal.emit("Step 8: Connecting the audio analyser input mic controller (J13) and phones connector (J15) ", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_j13_on():
                self.log_signal.emit("J13 successfully set to ON", False)
                time.sleep(0.5)
                if STM32RelayController.set_j15_on():
                    self.log_signal.emit("J15 successfully set to ON", False)
                    time.sleep(0.5)
                else:
                    self.log_signal.emit("ERROR: Failed to set J15 to ON", True)
                    return
                
            else:
                self.log_signal.emit("ERROR: Failed to set J13 and/or J15 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            
            
            self.log_signal.emit("Step 9: Connecting the audio analyser generator output with Connector (J27) ", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_j27_on():
                self.log_signal.emit("J27 successfully set to ON", False)
                time.sleep(0.5)
                
            else:
                self.log_signal.emit("ERROR: Failed to  J27 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()

            configure_apx(self)
            generator_control(self, level="750.0 uVrms", frequency=1000,state="on")

            self.log_signal.emit("Step 10: Setting Switch (S24) NORM to ON.  ", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_s24_on():
                self.log_signal.emit("S24 successfully set to ON", False)
                time.sleep(0.5)
                
            else:
                self.log_signal.emit("ERROR: Failed to  S24 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            
            
            self.log_signal.emit("INITIALIZATION COMPLETE", False)
            
            microphone_audio.run_norm(self)
            time.sleep(0.5)
            self.check_abort()
            phones_audio.run(self)
            time.sleep(0.5)
            self.check_abort()
            mic_limiter.run(self)
            time.sleep(0.5)
            self.check_abort()
            vos_delay.run_norm(self)
            time.sleep(0.5)
            self.check_abort()
            voltage_measurement.run_norm(self)
            time.sleep(0.5)
            self.check_abort()
            resistance_measurement.run_norm(self)
            time.sleep(0.5)
            transient.run(self)
            time.sleep(0.5)
            self.check_abort()
            lighting_test.run_norm(self)
            time.sleep(0.5)
            self.check_abort()
            self.log_signal.emit("==========All TESTS COMPLETED IN NORMAL MODE==========", False)
            time.sleep(2)



            # 🛑 PAUSE POINT – Operator Setup Instructions
            self.operator_event.clear()

            self.show_popup_signal.emit(
                "⚠ Operator Setup Required",
                "• Connect cables J65 to J101 and J66 to J102.\n"
                "• Turn the ICS knobs fully CW.\n"
                "• Set MIC Mode to HOT.\n"
                "• Turn TX SEL knobs fully CCW and to the OUT position.\n"
                "• Turn RX SEL knobs fully CCW.\n"
                "• Set STBY/NORM switch to NORM position.",
                RESOURCES_DIR / "knob.png",  # optional image
                "ok",
                None
            )

            # ⏸ Wait for operator confirmation
            self.operator_event.wait()

            time.sleep(2)

            self.log_signal.emit("========== INITIALIZATION START ==========", False)
            time.sleep(1)
            self.log_signal.emit("Switching all Relays to Default state", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_default_states():
                self.log_signal.emit("All relays successfully set to default states", False)
            else:
                self.log_signal.emit("ERROR: Failed to set all relays to default states", True)
                return

            # ✅ Do not freeze GUI during settle delay
            self.log_signal.emit("Waiting 20 seconds for relays to settle...", False)

            self.abortable_sleep(20)

            self.log_signal.emit("COMMENCING TESTS UNDER STBY MODE", False)
            
            self.log_signal.emit("Step 1: LOCAL/REMOTE (S23) → LOCAL", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_s23_local():
                self.log_signal.emit("S23 successfully set to LOCAL", False)
            else:
                self.log_signal.emit("ERROR: Failed to set S23 to LOCAL", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            
            self.log_signal.emit("Step 2: LOAD (S31) → 600 OHM", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_s31_600ohm():
                self.log_signal.emit("S31 successfully set to 600 OHM", False)
            else:
                self.log_signal.emit("ERROR: Failed to set S31 to 600 OHM", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()

            
            self.log_signal.emit("Step 3: All switches DOWN", False)
            self.logger.log("# WRITE SWITCH CONTROL LOGIC HERE", False)
            time.sleep(0.5)
            self.check_abort()
            
            self.log_signal.emit("Step 4: Connecting the power supply connector (J58)", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_j58_on():
                self.log_signal.emit("J58 successfully set to ON", False)
            else:
                self.log_signal.emit("ERROR: Failed to set J58 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            
            self.log_signal.emit("Step 5: Connecting the power supply connector (J60)", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_j60_on():
                self.log_signal.emit("J60 successfully set to ON", False)
            else:
                self.log_signal.emit("ERROR: Failed to set J60 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            
            self.log_signal.emit("Step 6: Power Supply set to 28V (SOUR:VOLT 28.0)", False)
            self.logger.log("# WRITE SCPI LOGIC HERE", False)
            time.sleep(0.5)
            self.check_abort()
            self.worker_channel_1()
            
            self.log_signal.emit("Step 7: Live voltage monitoring enabled", False)

            self.log_signal.emit("========== PSU AUTOMATION STARTING ==========", False)
            time.sleep(1)
            self.check_abort()
            self.log_signal.emit("Step 8: Connecting the audio analyser input mic controller (J13) and phones connector (J15) ", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_j13_on():
                self.log_signal.emit("J13 successfully set to ON", False)
                time.sleep(0.5)
                if STM32RelayController.set_j15_on():
                    self.log_signal.emit("J15 successfully set to ON", False)
                    time.sleep(0.5)
                else:
                    self.log_signal.emit("ERROR: Failed to set J15 to ON", True)
                    return
                
            else:
                self.log_signal.emit("ERROR: Failed to set J13 and/or J15 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            
            
            self.log_signal.emit("Step 9: Connecting the audio analyser generator output with connector (J27) ", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_j27_on():
                self.log_signal.emit("J27 successfully set to ON", False)
                time.sleep(0.5)
                
            else:
                self.log_signal.emit("ERROR: Failed to  J27 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            
            
            
            
            self.log_signal.emit("Step 10: Setting Switch (S24) NORM to ON.  ", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_s24_on():
                self.log_signal.emit("S24 successfully set to ON", False)
                time.sleep(0.5)
                
            else:
                self.log_signal.emit("ERROR: Failed to  S24 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            
            
            
            
            self.log_signal.emit("Step 11: Setting Switch (S25) STBY to ON.  ", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_s25_on():
                self.log_signal.emit("S25 successfully set to ON", False)
                time.sleep(0.5)
                
            else:
                self.log_signal.emit("ERROR: Failed to  S25 to ON", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            self.log_signal.emit("Step 12: Setting Switch (S24) NORM to OFF.  ", False)
            QApplication.processEvents()   # 🔑 FORCE UI UPDATE

            if STM32RelayController.set_s24_off():
                self.log_signal.emit("S24 successfully set to OFF", False)
                time.sleep(0.5)
                
            else:
                self.log_signal.emit("ERROR: Failed to  S24 to OFF", True)
                return

            QApplication.processEvents()
            time.sleep(0.5)
            self.check_abort()
            self.log_signal.emit("INITIALIZATION COMPLETE", False)
            self.check_abort()
            microphone_audio.run_stby(self)
            time.sleep(0.5)
            self.check_abort()
            vos_delay.run_stby(self)
            time.sleep(0.5)
            self.check_abort()
            voltage_measurement.run_stby(self)
            time.sleep(0.5)
            self.check_abort() 
            resistance_measurement.run_stby(self)
            time.sleep(0.5)
            self.check_abort()
            lighting_test.run_stby(self)
            time.sleep(0.5)
            self.check_abort()
            
            self.log_signal.emit("==========All TESTS COMPLETED IN STBY MODE==========", False)
            time.sleep(2)
            self.check_abort()
            self.log_signal.emit("Ch1 OUTPUT OFF", False)
            self.log_signal.emit("✓ PSU automation COMPLETED", False)
            # 🔓 Unlock PSU
            self.unfreeze_psu_front_panel()
            time.sleep(0.3)
            QTimer.singleShot(500, self.show_test_completion)

            

        except Exception as e:
            self.log_signal.emit(f"ERROR: PSU automation failed - {str(e)}", True)
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
    def on_back_clicked(self):
        """
        Handle Back button click.
        If test is running, show abort confirmation; otherwise return immediately.
        """
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
        if text.strip().upper() == "ALH4":

            # disable all except ALH2
            for i in range(self.alhx_combo.count()):
                item_text = self.alhx_combo.itemText(i)

                if item_text == "ALH2":
                    self.alhx_combo.model().item(i).setEnabled(True)
                else:
                    self.alhx_combo.model().item(i).setEnabled(False)

            # auto-switch to ALH2 if something else selected
            if self.alhx_combo.currentText() != "ALH2":
                self.alhx_combo.setCurrentText("ALH2")

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
        self.jbox_combo.setEnabled(True)
        # Re-apply junction box dependent state
        self.on_jbox_selection_changed(self.jbox_combo.currentText())
        self.lock_btn.setText("Lock On")
        self.logger.log("Configuration unlocked", False)
        self.log_signal.emit("Configuration UNLOCKED - You can now modify settings", False)

    def start_test(self):
        """
        Start test after validation.
        Shows calibration dialog ONLY when No Junction Box / normal mode.
        """
        # Validate control panel
        if not self.validate_control_panel():
            return
        # Disable lock button once test starts
        self.lock_btn.setEnabled(False)
        # 🔒 Disable start button once test begins
        self.start_btn.setEnabled(False)
        model = self.alhx_combo.currentText().strip()
        now = datetime.now()
        # ==========================================================
        # 🔴 CASE 1: JUNCTION BOX MODE (ALH4)
        # ==========================================================
        if self.is_junction_box_mode():

            # 🔥 Load separate Junction Box template
            create_model_report("ALH4")   # Your separate JB template name

            # Employee Details
            write_excel("E3", self.session_name)
            write_excel("E4", self.session_id)

            # Station Box (ALH2 forced)
            write_excel("E5", model)
            write_excel("E6", self.alhx_serial.text().strip())
            write_excel("E8", self.mod_combo.currentText())

            # 🔥 Junction Box Fields (Different Layout Area)
            write_excel("H3", "ALH4")
            write_excel("H4", self.jbox_serial.text().strip())
            write_excel("H5", self.mod_jbox_combo.currentText())

            write_excel("E7", "Full Test Run - With Junction Box")

            write_excel("L4", now.strftime("%d-%m-%Y"))
            write_excel("L5", now.strftime("%H-%M-%S"))
        else:
            create_model_report(model)
            # ================= HEADER DATA WRITE =================

            # Employee Details
            write_excel("C2", self.session_name)          # Employee Name
            write_excel("C3", self.session_id)            # Employee ID

            # LRU / Model
            write_excel("C4", model)                      # LRU (ALH1/2/3)

            # Serial Number
            write_excel("C5", self.alhx_serial.text().strip())

            # Test Type
            write_excel("C6", "Full test run")
            # MOD (ALH Module)
            write_excel("C7", self.mod_combo.currentText())

            # Date & Time
            write_excel("G2", now.strftime("%d-%m-%Y"))   # Date
            write_excel("G3", now.strftime("%H-%M-%S"))   # Time
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
        calibration = CalibrationPopup(self)
        if calibration.exec_() == QDialog.Accepted:
            self.abort_event.clear()
            self.test_running = True
            self.logger.log("Calibration acknowledged - Starting test initialization", False)
            self.log_text.clear()

            # ✅ Run initialization in background thread
            self.init_thread = InitializationThread(self)
            self.init_thread.start()



    def run_initialization(self):
        if self.is_junction_box_mode():
            box_init.run_init_jbox(self)
        else:
            box_init.run_init_sb(self)
        # RUN PSU AUTOMATION SEQUENCE (depends on Junction Box selection)
        if self.is_junction_box_mode():
            self.psu_thread = PSUAutomationThread(self)   # (later we can replace with PSUAutomationThreadJBox)
            self.psu_thread.start()
        else:
            self.psu_thread = PSUAutomationThread(self)
            self.psu_thread.start()


        

    def start_device_monitoring(self):
        self.device_listeners = []

        # 🔴 FORCE PSU HANDLE BEFORE STARTING LISTENER
        if not self.psu_inst:
            self.psu_inst = self.find_psu()

        if self.psu_inst:
            psu_listener = PSUListener(self.psu_inst, self.psu_lock)
            psu_listener.disconnected.connect(self.on_device_disconnected)
            self.device_listeners.append(psu_listener)

        # STM32 serial must be stored from ConnectionWorker
        if hasattr(self, "stm32_serial") and self.stm32_serial:
            mcu_listener = STM32Listener(self.stm32_serial)
            mcu_listener.disconnected.connect(self.on_device_disconnected)
            self.device_listeners.append(mcu_listener)

        for listener in self.device_listeners:
            listener.start()

    def append_log(self, message: str, error: bool = False):
        """
        Append timestamped message to running logs.
        Only logs ACTIONS, never live voltage values (to avoid spam).
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # ✅ STORE logs with error flag (for Detailed Logs Viewer)
        self.logs_history.append((timestamp, message, error))

        if error:
            self.log_text.setTextColor(QColor("#d32f2f"))  # Red for errors
        else:
            self.log_text.setTextColor(QColor("#1b5e20"))  # Green for normal

        self.log_text.append(f"[{timestamp}] {message}")
        self.logger.log(message, error)

        # Reset text color
        self.log_text.setTextColor(QColor("#333"))

        
    def show_test_completion(self):
        # 🔴 TURN OFF PSU OUTPUT IMMEDIATELY
        try:
            if self.psu_inst:
                with self.psu_lock:
                    self.psu_inst.write("OUTP OFF")
                self.log_signal.emit("⚠ PSU OUTPUT TURNED OFF (Abort)", True)
        except Exception as e:
            self.log_signal.emit(f"PSU OFF failed during abort: {e}", True)
        self.start_btn.setEnabled(True)
        completion = TestCompletionModal(self)
        completion.exec_()
            # ================= WRITE RESULT =================
        # ✅ FINAL OVERALL RESULT
        if self.overall_test_passed:
            result = "PASS"
        else:
            result = "FAIL"

        write_excel("G4", result)

        finalize_report()

        completion = TestCompletionModal(self)
        completion.exec_()
        
    def disconnect_and_return(self):
        """
        DISCONNECT button handler with handshake
        + Aborts current test if running
        """
        # ✅ Abort running test FIRST
        if self.test_running:
            self.log_signal.emit("DISCONNECT clicked → Aborting current test...", True)

            # trigger abort flag
            self.abort_event.set()

            # safely stop threads + listeners + UI reset
            self.abort_test_internal()

        # ✅ Now do disconnect handshake
        success = self.perform_disconnect_handshake()

        # ✅ Popup result
        dialog = DisconnectResultDialog(success, self)
        dialog.exec_()

        if success:
            self.return_to_connection.emit()
            self.close()


    def abort_test(self):
        # Only allow abort if test is running
        if not self.test_running:
            QMessageBox.information(self, "Abort Test", "No test is currently running.")
            return

        confirm = AbortTestConfirmationPopup(self)
        if confirm.exec_() != QDialog.Accepted:
            return

        #  Show terminating popup
        terminating_popup = OperatorInfoPopup(
            title="Terminating Test",
            message="Terminating the test...\nPlease wait.",
            image_path=None,
            buttons="ok",
            timer_seconds=2,
            parent=self
        )
        terminating_popup.show()
        QApplication.processEvents()

        # ✅ Trigger abort flag (thread-safe)
        self.abort_event.set()

        # ✅ Stop test safely
        self.abort_test_internal()

        # ✅ Clear logs
        self.log_text.clear()

        # ✅ Close popup if still open
        terminating_popup.close()


    def abort_test_internal(self):
        """Forcefully abort running test + cleanup"""

        # 🔴 TURN OFF PSU OUTPUT IMMEDIATELY
        try:
            if self.psu_inst:
                with self.psu_lock:
                    self.psu_inst.write("OUTP OFF")
                self.log_signal.emit("⚠ PSU OUTPUT TURNED OFF (Abort)", True)
        except Exception as e:
            self.log_signal.emit(f"PSU OFF failed during abort: {e}", True)
        

        # 🔥 FORCE SAVE CURRENT REPORT
        try:
            finalize_report()
        except:
            pass

        self.test_running = False
        self.start_btn.setEnabled(True)

        # Release any operator waits
        try:
            self.operator_event.set()
        except Exception:
            pass

        # Stop monitoring
        try:
            self.stop_voltage_monitoring()
        except Exception:
            pass

        # Stop listeners
        for listener in getattr(self, "device_listeners", []):
            try:
                listener.stop()
                listener.wait()
            except Exception:
                pass

        # Stop PSU automation thread
        if self.psu_thread and self.psu_thread.isRunning():
            try:
                self.psu_thread.terminate()
                self.psu_thread.wait(2000)
            except Exception:
                pass

        # Reset UI state
        self.unlock_configuration()
        self.lock_btn.setEnabled(True)

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



    def on_device_disconnected(self, device: DeviceType, message: str):
        # 🔴 Prevent multiple triggers
        if self._disconnect_in_progress:
            return
        self._disconnect_in_progress = True

        # 🚨 Abort test immediately on device disconnect
        self.abort_test_internal()


        # 🔕 Release any operator wait()
        try:
            self.operator_event.set()
        except Exception:
            pass

        # Stop voltage monitoring
        self.stop_voltage_monitoring()

        # Best-effort PSU OFF
        try:
            if self.psu_inst:
                self.psu_inst.write("OUTP OFF")
        except Exception:
            pass

        # Stop device listeners
        for listener in self.device_listeners:
            listener.stop()
            listener.wait()

        # 🔥 FORCE CLOSE ALL EXISTING POPUPS
        self._force_close_all_dialogs()

        # 🔔 Show ONLY ONE disconnect popup
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(f"{device.value} Disconnected")
        msg.setText(
            f"{message}\n"
            "Test aborted.\n"
            "Returning to connection screen…"
        )
        msg.setStandardButtons(QMessageBox.Ok)

        # On OK → close screen and return to connection page
        msg.buttonClicked.connect(
            lambda _: (
                self.close(),
                self.return_to_connection.emit()
            )
        )

        msg.exec_()





    
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
            # 1️⃣ Stop voltage monitoring thread
            if self.voltage_monitor_thread:
                self.stop_voltage_monitoring()
                time.sleep(0.5)

            # 2️⃣ STOP DEVICE LISTENER THREADS  ⬅️ ADD HERE
            for listener in getattr(self, "device_listeners", []):
                listener.stop()
                listener.wait()

            # 3️⃣ Close PSU VISA session
            if self.psu_inst:
                self.psu_inst.close()

        except Exception:
            pass

        event.accept()

