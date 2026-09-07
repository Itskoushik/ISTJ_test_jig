from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from core.paths import RESOURCES_DIR, CALIBRATION_LOGS_DIR
from core.logger import Logger
from datetime import datetime, date, time
import sqlite3
from core.excel_logger import (
    create_self_test_report, create_self_test_log, append_self_test_log,
    finalize_self_test_report,write_self_test_excel
)
# Fallback: build PDF from log_lines (same as original)
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib import colors
from db.db_paths import CALIBRATION_DB_PATH
from core.paths import SELF_TEST_REPORTS_DIR,LOGS_PDF_DIR,LOGS_SELF_TEST_DIR
from screens.test_reports_screen import TestReportsScreen
from core.calibration_report import generate_and_print_calibration_report, CalibrationReportError   
from tests import self_audio_analyser,self_istj,self_dmm,self_oscilloscope,self_psu,self_ethernet,self_rs232,self_rs422
from threading import Event
from dialogs.OperatorInfoPopup import OperatorInfoPopup
from psu.psu_automation import PSUAutomation
from psu.self_test_psu_host import SelfTestPSUHost
import time as _time
from pathlib import Path 
from screens.test_reports_screen import TestReportsScreen, EmptyStateDialog
from devices.device_types import DeviceType
from devices.oscilloscope_connection import OscilloscopeConnection

_DEVICE_REPORT_NAME_MAP = {
    "PSU (Power Supply)":       "PSU_POWER_SUPPLY",
    "Audio Analyzer":           "AUDIO_ANALYZER",
    "Microcontroller":          "ISTJ_CONTROLLER",
    "DMM (Digital Multimeter)": "DMM_DIGITAL_MULTIMETER",
    "Oscilloscope":              "OSCILLOSCOPE",
    "Ethernet":                  "ETHERNET",
    "RS232":                     "RS232",
    "RS422":                     "RS422",
}

def _report_name(device_name: str) -> str:
    return _DEVICE_REPORT_NAME_MAP.get(device_name, device_name)



class CalibrationDB:
    def __init__(self, db_path=CALIBRATION_DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration (
                device_name TEXT PRIMARY KEY,
                last_date TEXT,
                due_date TEXT,
                last_test TEXT
            )
        """)
        self.conn.commit()
        # Migrate existing DB that lacks the column
        try:
            cursor.execute("ALTER TABLE calibration ADD COLUMN last_test TEXT")
            self.conn.commit()
        except Exception:
            pass   # column already exists — safe to ignore

    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT device_name, last_date, due_date, last_test FROM calibration")
        rows = cursor.fetchall()

        data = {}
        for device, last, due, last_test in rows:
            try:
                last_d = date.fromisoformat(last) if last else None
                due_d  = date.fromisoformat(due) if due else None
            except ValueError:
                last_d = None
                due_d  = None

            data[device] = {
                "last": last_d,
                "due": due_d,
                "last_test": last_test or None
            }
        return data

    def upsert(self, device_name, last_date, due_date):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO calibration (device_name, last_date, due_date)
            VALUES (?, ?, ?)
            ON CONFLICT(device_name) DO UPDATE SET
                last_date=excluded.last_date,
                due_date=excluded.due_date
        """, (device_name, last_date.isoformat(), due_date.isoformat()))
        self.conn.commit()
    def upsert_last_test(self, device_name: str, last_test: str):
        """Save the last self-test timestamp for a device."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO calibration (device_name, last_date, due_date, last_test)
            VALUES (?, '', '', ?)
            ON CONFLICT(device_name) DO UPDATE SET
                last_test=excluded.last_test
        """, (device_name, last_test))
        self.conn.commit()
def _add_one_year(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        return d.replace(year=d.year + 1, day=28)
class EquipmentSelfCheckScreen(QMainWindow):
    """
    Equipment Self Check Screen - displays device connectivity and self-test status.
    Opens as a separate page from TestSelectionScreen.
    Visually matches the provided reference image with HAL color palette.
    """
    return_to_test_selection = pyqtSignal()

    def __init__(self, device_status: dict, monitor=None):
        super().__init__()
        self._monitor = monitor
        # device_status is now already the authoritative post-scan snapshot
        # built by HALApplication.show_equipment_self_check() from
        # worker.device_status, after DeviceMonitor.refresh_for_self_test()
        # ran a real validate-or-discover pass. No bool()-of-object overlay
        # here anymore — that pattern is exactly what let a dead-but-non-None
        # VISA handle read as "Connected" in the UI.
        self.device_status = dict(device_status)
        self.db = CalibrationDB()
        self._disconnect_popup_shown: set = set()
        self._active_self_test_dialogs = []
        _today = date.today()
        default_data = {
            "PSU (POWER SUPPLY)":       {"last": date(2026, 3, 19),  "due": date(2027, 3, 19)},   # DP832
            "AUDIO ANALYSER":           {"last": date(2026, 7, 15),  "due": date(2027, 7, 15)},   # APX52B
            "ISTJ CONTROLLER":          {"last": _today,             "due": _add_one_year(_today)},
            "DMM (DIGITAL MULTIMETER)": {"last": date(2026, 3, 18),  "due": date(2027, 3, 18)},   # DM3068
            "OSCILLOSCOPE":             {"last": date(2026, 1, 28),  "due": date(2027, 1, 28)},   # TBS1072C
        }

        # Load from DB
        self.calibration_data = self.db.get_all()
        self.last_test_times = {
            name: data["last_test"]
            for name, data in self.calibration_data.items()
            if data.get("last_test")
        }  # device_name -> "YYYY-MM-DD HH:MM" string

        # If DB empty → seed defaults
        if not self.calibration_data:
            for device, dates in default_data.items():
                self.db.upsert(device, dates["last"], dates["due"])
            self.calibration_data = default_data


        self.setWindowTitle("HAL - Equipment Self Check")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
        from core.screen_utils import responsive_size
        self.setMinimumSize(responsive_size(0.55, 0.6, min_w=900, min_h=650))
        self.setStyleSheet("background-color: #f5f5f5;")
        self.showMaximized()

        self.logger = Logger(CALIBRATION_LOGS_DIR / f"equipment_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

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

        # Print Calibration Report button (CENTER-RIGHT, before status badge)
        print_cal_btn = QPushButton("  Print Calibration Report")
        print_cal_btn.setMinimumHeight(40)
        print_cal_btn.setFont(QFont("Arial", 9, QFont.Bold))
        print_cal_btn.setCursor(Qt.PointingHandCursor)
        printer_icon_path = RESOURCES_DIR / "printer.png"
        if printer_icon_path.exists():
            print_cal_btn.setIcon(QIcon(str(printer_icon_path)))
            print_cal_btn.setIconSize(QSize(18, 18))
        print_cal_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #1a5da8;
                border: 1.5px solid #1a5da8;
                border-radius: 4px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #e8f0fe;
            }
            QPushButton:pressed {
                background-color: #d2e3fc;
            }
        """)
        print_cal_btn.clicked.connect(self.on_print_calibration_report)
        header_layout.addWidget(print_cal_btn, 0, Qt.AlignRight | Qt.AlignVCenter)

        # Status Badge (CENTER-RIGHT) – Green "All Devices Detected"
        all_ok = all(self.device_status.values())   # ← compute ONCE here, early
        status_badge = QFrame()
        status_badge.setStyleSheet(f"""
            QFrame {{
                background-color: {"#e8f5e9" if all_ok else "#ffebee"};
                border: 1px solid {"#4caf50" if all_ok else "#d32f2f"};
                border-radius: 4px;
                padding: 0px;
            }}
        """)
        status_badge.setObjectName("header_status_badge")
        
        status_badge.setFixedHeight(36)
        badge_layout = QHBoxLayout(status_badge)
        badge_layout.setContentsMargins(12, 0, 12, 0)
        badge_layout.setSpacing(8)

        status_dot = QLabel("●")
        status_dot.setFont(QFont("Arial", 12))
        status_dot.setStyleSheet("color: #4caf50; background-color: transparent; border: none;")
        status_dot.setAlignment(Qt.AlignCenter)
        status_dot.setObjectName("header_status_dot")
        badge_layout.addWidget(status_dot, 0, Qt.AlignVCenter)

        status_text = QLabel(
            "All Devices Detected" if all_ok else "Some Devices Not Detected"
        )
        status_dot.setStyleSheet(
            "color: #4caf50; border: none;" if all_ok else "color: #d32f2f; border: none;"
        )

        status_text.setFont(QFont("Arial", 10, QFont.Bold))
        status_text.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        status_text.setStyleSheet(
            "color: #2e7d32; background-color: transparent; border: none; letter-spacing: 0.2px;"
            if all_ok else
            "color: #c62828; background-color: transparent; border: none; letter-spacing: 0.2px;"
        )
        status_text.setObjectName("header_status_text")
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
                "name": "PSU (POWER SUPPLY)",
                "key":  "PSU (Power Supply)",
                "port": "USB",
                "connected": self.device_status.get("PSU (Power Supply)", False),
            },
            {
                "name": "AUDIO ANALYSER",
                "key":  "Audio Analyzer",
                "port": "APX | DLL",
                "connected": self.device_status.get("Audio Analyzer", False),
            },
            {
                "name": "ISTJ CONTROLLER",
                "key":  "Microcontroller",
                "port": "COM",
                "connected": self.device_status.get("Microcontroller", False),
            },
            {
                "name": "DMM (DIGITAL MULTIMETER)",
                "key":  "DMM (Digital Multimeter)",
                "port": "USB",
                "connected": self.device_status.get("DMM (Digital Multimeter)", False),
            },
            {
                "name": "OSCILLOSCOPE",
                "key":  "Oscilloscope",
                "port": "USB",
                "connected": self.device_status.get("Oscilloscope", False),
            },
        ]


        # ===== ROW 1: PSU, Audio Analyzer, ISTJ =====
        row1_layout = QHBoxLayout()
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(20)
        for idx in range(3):
            card = self._create_device_card(devices[idx])
            row1_layout.addWidget(card, 1)
        cards_layout.addLayout(row1_layout)
        cards_layout.addSpacing(20)

        # ===== ROW 2: DMM, Oscilloscope + merged ETH/RS card =====
        row2_layout = QHBoxLayout()
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(20)
        for idx in range(3, 5):   # DMM, Oscilloscope only
            card = self._create_device_card(devices[idx])
            row2_layout.addWidget(card, 1)
        # Merged Ethernet/RS232/RS422 card
        merged_card = self._create_merged_interface_card()
        row2_layout.addWidget(merged_card, 1)
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

        run_all_btn = QPushButton("Run All Self Tests")
        run_all_btn.setObjectName("run_all_btn")
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

        generate_report_btn = QPushButton("View Reports")
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
        generate_report_btn.clicked.connect(self.on_view_reports)
        bottom_layout.addWidget(generate_report_btn)

        bottom_layout.addStretch()

        main_layout.addLayout(bottom_layout, 0)
        
    
    def _create_merged_interface_card(self) -> QFrame:
        """
        Single card for Ethernet / RS232 / RS422 with radio-button switcher.
        No calibration section. Run Self Test enabled based on connection status.
        """
        interfaces = [
            {
                "name": "ETHERNET",
                "port": "LAN | RJ45",
                "icon": "ethernet.jpeg",
                "connected": self.device_status.get("Ethernet", False),
            },
            {
                "name": "RS422",
                "port": "COM | Serial",
                "icon": "rs422.jpeg",
                "connected": self.device_status.get("RS422", False),
            },
            {
                "name": "RS232",
                "port": "COM | Serial",
                "icon": "rs232.jpeg",
                "connected": self.device_status.get("RS232", False),
            },
        ]

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 0px;
            }
        """)
        card.setMinimumHeight(340)
        card.setMaximumHeight(340)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # ── Icon + Name row (horizontal, matches other cards) ─────────────
        icon_name_row = QHBoxLayout()
        icon_name_row.setContentsMargins(0, 0, 0, 0)
        icon_name_row.setSpacing(12)

        icon_label = QLabel()
        icon_label.setFixedSize(56, 56)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background:transparent; border:none;")
        icon_name_row.addWidget(icon_label, 0, Qt.AlignLeft | Qt.AlignVCenter)

        name_label = QLabel()
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setFixedHeight(24)
        name_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_label.setStyleSheet("color:#1a1a1a; background:transparent; border:none;")
        icon_name_row.addWidget(name_label, 1, Qt.AlignLeft | Qt.AlignVCenter)

        layout.addLayout(icon_name_row)

        # ── Status dot + text ─────────────────────────────────────────────
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        status_row.setContentsMargins(0, 0, 0, 0)
        dot_lbl = QLabel("●")
        dot_lbl.setFont(QFont("Arial", 10))
        dot_lbl.setFixedWidth(14)
        dot_lbl.setStyleSheet("border:none; background:transparent;")
        status_lbl = QLabel()
        status_lbl.setFont(QFont("Arial", 10))
        status_lbl.setStyleSheet("border:none; background:transparent;")
        status_row.addWidget(dot_lbl)
        status_row.addWidget(status_lbl, 1)
        layout.addLayout(status_row)

        # ── Port label ────────────────────────────────────────────────────
        port_lbl = QLabel()
        port_lbl.setFont(QFont("Arial", 10))
        port_lbl.setStyleSheet("color:#666666; background:transparent; border:none;")
        layout.addWidget(port_lbl)

        # ── Last test label ───────────────────────────────────────────────
        last_test_lbl = QLabel("🕐  Last Test: Never")
        last_test_lbl.setFont(QFont("Arial", 9, QFont.Bold))
        last_test_lbl.setStyleSheet("""
            QLabel {
                color: #e65100;
                background-color: #fff3e0;
                border: 1px solid #ffb74d;
                border-radius: 4px;
                padding: 4px 10px;
            }
        """)
        layout.addWidget(last_test_lbl)

        layout.addStretch()

        # ── Radio button row – truly centered via wrapper widget ──────────
        btn_group = QButtonGroup(card)
        radios = []

        radio_wrapper = QWidget()
        radio_wrapper.setStyleSheet("background:transparent; border:none;")
        radio_inner = QHBoxLayout(radio_wrapper)
        radio_inner.setContentsMargins(0, 6, 0, 6)
        radio_inner.setSpacing(20)
        radio_inner.setAlignment(Qt.AlignHCenter)

        for i, iface in enumerate(interfaces):
            rb = QRadioButton(iface["name"])
            rb.setFont(QFont("Arial", 10, QFont.Bold))
            rb.setStyleSheet("""
                QRadioButton { color:#1a1a1a; background:transparent; border:none; spacing:6px; }
                QRadioButton::indicator { width:16px; height:16px; }
                QRadioButton::indicator:checked { border:2px solid #1a5da8; border-radius:8px; background:#1a5da8; }
                QRadioButton::indicator:unchecked { border:2px solid #aaaaaa; border-radius:8px; background:white; }
            """)
            btn_group.addButton(rb, i)
            radio_inner.addWidget(rb)
            radios.append(rb)

        layout.addWidget(radio_wrapper, 0, Qt.AlignHCenter)

        # ── Run Self Test button ───────────────────────────────────────────
        run_btn = QPushButton("Run Self Test")
        run_btn.setMinimumHeight(40)
        run_btn.setFont(QFont("Arial", 10, QFont.Bold))
        run_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        run_row = QHBoxLayout()
        run_row.setContentsMargins(0, 0, 0, 0)
        run_row.setSpacing(8)
        run_row.addWidget(run_btn, 1)
        layout.addLayout(run_row)

        # Tracks which interface is currently shown, so a test that finishes
        # after the user has switched radios doesn't stomp the wrong label.
        current_iface = {"name": interfaces[0]["name"]}

        # ── Update function called on radio switch ────────────────────────
        def update_card(idx):
            iface = interfaces[idx]
            current_iface["name"] = iface["name"]

            # Icon
            pix = QPixmap(str(RESOURCES_DIR / iface["icon"]))
            if not pix.isNull():
                icon_label.setPixmap(pix.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                icon_label.clear()

            # Name
            name_label.setText(iface["name"])

            # Status
            dot_lbl.setVisible(False)
            status_lbl.setVisible(False)

            # Port
            port_lbl.setText(iface["port"])


            # Last test
            lt = self.last_test_times.get(iface["name"])
            if lt:
                last_test_lbl.setText(f"🕐  Last Test: {lt}")
                last_test_lbl.setStyleSheet("""
                    QLabel {
                        color: #2e7d32; background-color: #e8f5e9;
                        border: 1px solid #81c784; border-radius: 4px; padding: 4px 10px;
                    }
                """)
            else:
                last_test_lbl.setText("🕐  Last Test: Never")
                last_test_lbl.setStyleSheet("""
                    QLabel {
                        color: #e65100; background-color: #fff3e0;
                        border: 1px solid #ffb74d; border-radius: 4px; padding: 4px 10px;
                    }
                """)

            # Run button — always enabled, single consistent style
            run_btn.setEnabled(True)
            run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a5da8; color: white;
                    border: none; border-radius: 3px;
                    padding: 6px 12px; font-weight: bold;
                }
                QPushButton:hover { background-color: #154a8a; }
                QPushButton:pressed { background-color: #0f3860; }
            """)

            # Rewire run button to current interface
            try:
                run_btn.clicked.disconnect()
            except Exception:
                pass
            run_btn.clicked.connect(lambda: self._on_merged_self_test(
                iface["name"], last_test_lbl, current_iface
            ))

        # Wire radios
        for i, rb in enumerate(radios):
            rb.toggled.connect(lambda checked, idx=i: update_card(idx) if checked else None)

        # Default: first radio selected
        radios[0].setChecked(True)
        update_card(0)

        return card

    def _on_merged_self_test(self, device_name: str, last_test_lbl: QLabel, current_iface: dict = None):
        """Run self test for a merged interface card device."""
        if device_name in ("RS232", "RS422"):
            dialog = SerialTerminalDialog(device_name, self)
            self._active_self_test_dialogs.append(dialog)

            def _on_finished(result):
                now_str = datetime.now().strftime("%d-%m-%Y %H:%M")
                self.last_test_times[device_name] = now_str
                self.db.upsert_last_test(device_name, now_str)
                # Only touch the visible label if this device is still selected —
                # otherwise we'd overwrite whatever interface the operator has
                # since switched to.
                if current_iface is None or current_iface.get("name") == device_name:
                    last_test_lbl.setText(f"🕐  Last Test: {now_str}")
                if dialog in self._active_self_test_dialogs:
                    self._active_self_test_dialogs.remove(dialog)

            dialog.finished.connect(_on_finished)
            dialog.show()
            return
        # ── NEW: dedicated Ethernet self-test dialog ────────────────────────
        if device_name == "ETHERNET":
            from tests.self_ethernet import EthernetTestDialog

            try:
                report_path = create_self_test_report(_report_name(device_name))
            except Exception as e:
                report_path = None
                print(f"[ETHERNET] report setup failed (non-fatal): {e}")

            dialog = EthernetTestDialog(self, report_path=report_path)
            self._active_self_test_dialogs.append(dialog)

            def _on_finished(result):
                if result:   # ← only stamp "last test" if a ping actually ran
                    now_str = datetime.now().strftime("%d-%m-%Y %H:%M")
                    self.last_test_times[device_name] = now_str
                    self.db.upsert_last_test(device_name, now_str)
                    # Only touch the visible label if this device is still selected —
                    # otherwise we'd overwrite whatever interface the operator has
                    # since switched to.
                    if current_iface is None or current_iface.get("name") == device_name:
                        last_test_lbl.setText(f"🕐  Last Test: {now_str}")
                        if dialog.test_result == "PASS":
                            last_test_lbl.setStyleSheet("""
                                QLabel {
                                    color: #2e7d32; background-color: #e8f5e9;
                                    border: 1px solid #81c784; border-radius: 4px; padding: 4px 10px;
                                }
                            """)
                        else:
                            last_test_lbl.setStyleSheet("""
                                QLabel {
                                    color: #c62828; background-color: #ffebee;
                                    border: 1px solid #ef9a9a; border-radius: 4px; padding: 4px 10px;
                                }
                            """)
                if dialog in self._active_self_test_dialogs:
                    self._active_self_test_dialogs.remove(dialog)

            dialog.finished.connect(_on_finished)
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            return
        dialog = SelfTestDialog(device_name, self)
        self._active_self_test_dialogs.append(dialog)

        def _on_finished(result):
            if result:
                now_str = datetime.now().strftime("%d-%m-%Y %H:%M")
                self.last_test_times[device_name] = now_str
                self.db.upsert_last_test(device_name, now_str)
                last_test_lbl.setText(f"🕐  Last Test: {now_str}")
                if dialog.test_result == "PASS":
                    last_test_lbl.setStyleSheet("""
                        QLabel {
                            color: #2e7d32; background-color: #e8f5e9;
                            border: 1px solid #81c784; border-radius: 4px; padding: 4px 10px;
                        }
                    """)
                else:
                    last_test_lbl.setStyleSheet("""
                        QLabel {
                            color: #c62828; background-color: #ffebee;
                            border: 1px solid #ef9a9a; border-radius: 4px; padding: 4px 10px;
                        }
                    """)
            if dialog in self._active_self_test_dialogs:
                self._active_self_test_dialogs.remove(dialog)

        dialog.finished.connect(_on_finished)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
    
    
    def _refresh_header_badge(self):
        """Recompute and repaint the header 'All Devices Detected' badge."""
        all_ok = all(self.device_status.values())

        badge = self.findChild(QFrame, "header_status_badge")
        dot   = self.findChild(QLabel, "header_status_dot")
        txt   = self.findChild(QLabel, "header_status_text")

        if badge:
            badge.setStyleSheet(f"""
                QFrame {{
                    background-color: {"#e8f5e9" if all_ok else "#ffebee"};
                    border: 1px solid {"#4caf50" if all_ok else "#d32f2f"};
                    border-radius: 4px;
                    padding: 0px;
                }}
            """)
        if dot:
            dot.setStyleSheet(
                "color: #4caf50; border: none;" if all_ok
                else "color: #d32f2f; border: none;"
            )
        if txt:
            txt.setText("All Devices Detected" if all_ok else "Some Devices Not Detected")
            txt.setStyleSheet(
                "color: #2e7d32; background-color: transparent; border: none; letter-spacing: 0.2px;"
                if all_ok else
                "color: #c62828; background-color: transparent; border: none; letter-spacing: 0.2px;"
            )    

    def set_scanning_lock(self, active: bool):
        """
        Disables every 'Run Self Test' button (individual + Run All) while
        the background _SelfTestRefreshThread is still validating/
        discovering devices. Without this, an operator can launch a
        SelfTestWorker against a PSU/DMM/OSC handle the refresh thread is
        concurrently replacing or closing — this is what produced the
        VI_ERROR_IO failures and cross-thread QTimer warnings when a self
        test was started during the scan window.
        Re-enables each button according to its device's actual connected
        state once the scan completes (active=False), not unconditionally —
        a device the scan found disconnected must stay disabled.
        """
        keys = [
            "PSU (Power Supply)",
            "Audio Analyzer",
            "Microcontroller",
            "DMM (Digital Multimeter)",
            "Oscilloscope",
        ]
        for key in keys:
            btn = self.findChild(QPushButton, f"run_btn_{key}")
            if btn is None:
                continue
            if active:
                btn.setEnabled(False)
            else:
                btn.setEnabled(bool(self.device_status.get(key, False)))

        run_all_btn = self.findChild(QPushButton, "run_all_btn")
        if run_all_btn is not None:
            run_all_btn.setEnabled(not active)

    def on_view_reports(self):
        pdf_files = list(SELF_TEST_REPORTS_DIR.glob("*.pdf"))

        if not pdf_files:
            EmptyStateDialog(
                self,
                title="No Test Reports",
                icon_path=RESOURCES_DIR / "pdf.png",
                heading="No test reports found",
                description_lines=[
                    "There are currently no PDF reports available.",
                    "Run tests and generate reports to see them here.",
                ],
                tip_icon_path=RESOURCES_DIR / "lab.png",
                tip_title="Generate reports",
                tip_desc="Run your tests to generate PDF reports that will appear here.",
            ).exec_()
            return

        self._self_test_reports_screen = TestReportsScreen(
            reports_dir=SELF_TEST_REPORTS_DIR,
            mode="self",
            filter_options=["Audio_Analyzer", "Oscilloscope", "ISTJ", "DMM", "Ethernet", "RS232", "RS422", "PSU"],
        )
        self._self_test_reports_screen.setWindowTitle("HAL - Self Test Reports")
        self._self_test_reports_screen.return_to_test_selection.connect(self._on_reports_back)
        self.hide()
        self._self_test_reports_screen.show()

    def _on_reports_back(self):
        if hasattr(self, '_self_test_reports_screen') and self._self_test_reports_screen:
            self._self_test_reports_screen.close()
            self._self_test_reports_screen = None
        self.show()
        self.raise_()
        
    def on_print_calibration_report(self):
        """
        Build a fresh calibration report excel from self.calibration_data,
        convert it to PDF, and print it (OS print dialog) or open the PDF
        if printing isn't available.
        """
        self.logger.log("Print Calibration Report clicked", False)
        try:
            pdf_path = generate_and_print_calibration_report(self.calibration_data)
            self.logger.log(f"Calibration report ready: {pdf_path}", False)
        except CalibrationReportError as e:
            self.logger.log(f"Calibration report failed: {e}", True)
            QMessageBox.warning(
                self,
                "Print Calibration Report Failed",
                f"Could not generate or print the calibration report:\n\n{e}",
            )

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
        card.setMinimumHeight(340)  # Fixed height for consistency
        card.setMaximumHeight(340)
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
        icon_label.setFixedSize(56, 56)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        
        # Map device names to image files
        device_icon_map = {
            "PSU (POWER SUPPLY)": "power_supply.png",
            "AUDIO ANALYSER": "audio.png",
            "ISTJ CONTROLLER": "micro.png",
            "DMM (DIGITAL MULTIMETER)": "dmm.png",
            "OSCILLOSCOPE": "oscope.png",
            "ETHERNET": "ethernet.jpeg",
            "RS232": "rs232.jpeg",
            "RS422": "rs422.jpeg",
        }
        
        icon_filename = device_icon_map.get(device["name"], "")
        if icon_filename:
            icon_path = RESOURCES_DIR / icon_filename
            icon_pixmap = QPixmap(str(icon_path))
            if not icon_pixmap.isNull():
                icon_pixmap = icon_pixmap.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(icon_pixmap)
        
        header_layout.addWidget(icon_label, 0, Qt.AlignTop | Qt.AlignLeft)

        # Device Name (Title) – Single line, no wrap
        name_label = QLabel(device["name"])
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
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
        status_dot.setObjectName(f"status_dot_{device['key']}")   # ← ADD
        status_container.addWidget(status_dot, 0)

        if device["connected"]:
            status_text = QLabel("Connected")
            status_dot.setStyleSheet("color: #4caf50; background-color: transparent; border: none;")
            status_color = "#2e7d32"
        else:
            status_text = QLabel("Not Connected")
            status_dot.setStyleSheet("color: #d32f2f; background-color: transparent; border: none;")
            status_color = "#d32f2f"

        status_text.setFont(QFont("Arial", 10))
        status_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        status_text.setStyleSheet(f"color: {status_color}; background-color: transparent; border: none;")
        status_text.setObjectName(f"status_text_{device['key']}")  # ← ADD
        status_container.addWidget(status_text, 1)

        layout.addLayout(status_container)

        # ===== Port/VISA Information =====
        port_label = QLabel(device["port"])
        port_label.setFont(QFont("Arial", 10))
        port_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        port_label.setStyleSheet("color: #666666; background-color: transparent; border: none; padding: 0px; margin: 0px;")
        layout.addWidget(port_label)

        # ===== Self-Test Result Label =====
        last_test = self.last_test_times.get(device["name"], None)
        last_test_str = f"🕐  Last Test: {last_test}" if last_test else "🕐  Last Test: Never"
        test_result = QLabel(last_test_str)
        test_result.setFont(QFont("Arial", 9, QFont.Bold))
        test_result.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        test_result.setStyleSheet("""
            QLabel {
                color: #e65100;
                background-color: #fff3e0;
                border: 1px solid #ffb74d;
                border-radius: 4px;
                padding: 4px 10px;
            }
        """)
        test_result.setObjectName(f"test_result_{device['key']}")
        layout.addWidget(test_result)

        layout.addSpacing(8)
        
        # ===== Calibration Section (Side by Side) =====
        cal = self.calibration_data.get(
            device["name"],
            {
                "last": date.today(),
                "due": date.today()
            }
        )


        cal_layout = QHBoxLayout()
        cal_layout.setSpacing(10)

        last_lbl = QPushButton(f"Last: {cal['last'].strftime('%d-%m-%Y')}")
        last_lbl.setFont(QFont("Arial", 9))
        last_lbl.setCursor(Qt.PointingHandCursor)
        last_lbl.setStyleSheet("""
            QPushButton {
                background:#f1f3f4;
                padding:6px 10px;
                border-radius:4px;
                color:#333;
                border: none;
            }
            QPushButton:hover { background:#e8e8e8; }
        """)

        due_btn = QPushButton(f"Due: {cal['due'].strftime('%d-%m-%Y')}")
        due_btn.setFont(QFont("Arial", 10))
        due_btn.setCursor(Qt.PointingHandCursor)

        today = date.today()
        days_until_due = (cal['due'] - today).days
        if days_until_due < 0:
            due_style = """
                QPushButton {
                    background:#ffebee; border:1px solid #d32f2f;
                    padding:6px 10px; border-radius:4px; color:#c62828;
                }
                QPushButton:hover { background:#ffcdd2; }
            """
        elif days_until_due <= 60:
            due_style = """
                QPushButton {
                    background:#fff3e0; border:1px solid #f57c00;
                    padding:6px 10px; border-radius:4px; color:#e65100;
                }
                QPushButton:hover { background:#ffe0b2; }
            """
        else:
            due_style = """
                QPushButton {
                    background:#e8f5e9; border:1px solid #4caf50;
                    padding:6px 10px; border-radius:4px; color:#2e7d32;
                }
                QPushButton:hover { background:#c8e6c9; }
            """
        due_btn.setStyleSheet(due_style)

        cal_layout.addWidget(last_lbl)
        cal_layout.addWidget(due_btn)
        layout.addLayout(cal_layout)

        reset_btn = QPushButton("Reset Calibration")
        reset_btn.setObjectName("Reset Calibration")

        reset_btn.setVisible(False)
        reset_btn.setFont(QFont("Arial", 9, QFont.Bold))
        reset_btn.setStyleSheet("""
            QPushButton {
                background:#1976d2;
                color:white;
                border-radius:4px;
                padding:6px 10px;
            }
            QPushButton:hover {
                background:#1565c0;
            }
        """)
        layout.addWidget(reset_btn)
        card.installEventFilter(self)
        reset_btn.installEventFilter(self)
        last_lbl.installEventFilter(self)

        def open_calibration_menu():
            reset_btn.setVisible(not reset_btn.isVisible())

        def reset_calibration():
            dialog = CalibrationDialog(device["name"], self)
            if dialog.exec_():
                new_last = dialog.last_date.date().toPyDate()   # ← was dialog.due_date
                new_due  = _add_one_year(new_last)              # ← auto-computed

                self.calibration_data[device["name"]] = {
                    "last": new_last,
                    "due":  new_due,
                }
                self.db.upsert(device["name"], new_last, new_due)

                last_lbl.setText(f"Last: {new_last.strftime('%d-%m-%Y')}")
                due_btn.setText(f"Due: {new_due.strftime('%d-%m-%Y')}")
                reset_btn.setVisible(False)
                
                
        last_lbl.clicked.connect(open_calibration_menu)
        reset_btn.clicked.connect(reset_calibration)
        
        # ===== Action Buttons (Run Self Test + dev-mode badge) =====
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)

        run_btn = QPushButton("Run Self Test")
        run_btn.setObjectName(f"run_btn_{device['key']}")
        run_btn.setMinimumHeight(40)
        run_btn.setFont(QFont("Arial", 10, QFont.Bold))
        run_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        run_btn.setEnabled(True)   # ← always enabled (dev mode)

        run_btn.setEnabled(device["connected"])   # ← disabled when device not connected

        if device["connected"]:
            run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a5da8;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #154a8a; }
                QPushButton:pressed { background-color: #0f3860; }
            """)
        else:
            run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #b0b0b0;
                    color: #f0f0f0;
                    border: none;
                    border-radius: 3px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """)

        run_btn.clicked.connect(lambda: self.on_run_device_self_test(device["key"], test_result, last_test_key=device["name"]))
        button_layout.addWidget(run_btn, 1)
        layout.addLayout(button_layout)

        return card
    def on_device_reconnected(self, ui_name: str):
        """
        Called when DeviceMonitor detects a previously disconnected device is back.
        Updates the card dot to green and re-enables Run Self Test.
        """
        self.device_status[ui_name] = True
        self._disconnect_popup_shown.discard(ui_name)  # allow popup on next disconnect
        dot = self.findChild(QLabel, f"status_dot_{ui_name}")
        txt = self.findChild(QLabel, f"status_text_{ui_name}")
        if dot:
            dot.setStyleSheet("color: #4caf50; background-color: transparent; border: none;")
        if txt:
            txt.setText("Connected")
            txt.setStyleSheet("color: #2e7d32; background-color: transparent; border: none;")

        run_btn = self.findChild(QPushButton, f"run_btn_{ui_name}")
        if run_btn:
            run_btn.setEnabled(True)
            run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a5da8;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #154a8a; }
                QPushButton:pressed { background-color: #0f3860; }
            """)    
            
        # ── Update header status badge ────────────────────────────────────
        self._refresh_header_badge()
        msg = QMessageBox(self)
        msg.setWindowTitle("Device Reconnected")
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"<b>{ui_name}</b> has been reconnected.")
        msg.setInformativeText("The device is online and ready.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setModal(False)
        msg.show()
    def on_run_device_self_test(self, device_name: str, test_result_label: QLabel = None, last_test_key: str = None):
        dialog = SelfTestDialog(device_name, self, display_name=last_test_key)
        self._active_self_test_dialogs.append(dialog)

        def _on_finished(result):
            if result:
                now_str = datetime.now().strftime("%d-%m-%Y %H:%M")
                lt_key = last_test_key or device_name
                self.last_test_times[lt_key] = now_str
                self.db.upsert_last_test(lt_key, now_str)
                if test_result_label:
                    test_result_label.setText(f"🕐  Last Test: {now_str}")
                    if dialog.test_result == "PASS":
                        test_result_label.setStyleSheet("""
                            QLabel {
                                color: #2e7d32;
                                background-color: #e8f5e9;
                                border: 1px solid #81c784;
                                border-radius: 4px;
                                padding: 4px 10px;
                            }
                        """)
                    else:
                        test_result_label.setStyleSheet("""
                            QLabel {
                                color: #c62828;
                                background-color: #ffebee;
                                border: 1px solid #ef9a9a;
                                border-radius: 4px;
                                padding: 4px 10px;
                            }
                        """)
            if dialog in self._active_self_test_dialogs:
                self._active_self_test_dialogs.remove(dialog)

        dialog.finished.connect(_on_finished)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
    def eventFilter(self, obj, event):
        if event.type() == event.MouseButtonPress:

            # If click is on Due button or Reset button → DO NOTHING
            if isinstance(obj, QPushButton) and obj.text() in (
                "Reset Calibration",
            ):
                return False

            # Otherwise hide all reset buttons
            for btn in self.findChildren(QPushButton, "Reset Calibration"):
                btn.setVisible(False)

        return super().eventFilter(obj, event)


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
        key_to_display = {
            "PSU (Power Supply)":       "PSU (POWER SUPPLY)",
            "Audio Analyzer":           "AUDIO ANALYSER",
            "Microcontroller":          "ISTJ CONTROLLER",
            "DMM (Digital Multimeter)": "DMM (DIGITAL MULTIMETER)",
            "Oscilloscope":             "OSCILLOSCOPE",
        }

        connected_keys = [k for k in key_to_display if self.device_status.get(k, False)]
        skipped_keys   = [k for k in key_to_display if not self.device_status.get(k, False)]

        dialog = SelfTestDialog(
            "All Devices", self,
            all_devices=True,
            connected_devices=connected_keys,
            skipped_devices=skipped_keys,
        )
        self._active_self_test_dialogs.append(dialog)

        def _on_finished(result):
            if result:
                now_str = datetime.now().strftime("%d-%m-%Y %H:%M")
                for key in connected_keys:
                    display = key_to_display[key]
                    self.last_test_times[display] = now_str
                    self.db.upsert_last_test(display, now_str)
                    lbl = self.findChild(QLabel, f"test_result_{key}")
                    if lbl:
                        lbl.setText(f"🕐  Last Test: {now_str}")
                        if dialog.test_result == "PASS":
                            lbl.setStyleSheet("""
                                QLabel {
                                    color: #2e7d32;
                                    background-color: #e8f5e9;
                                    border: 1px solid #81c784;
                                    border-radius: 4px;
                                    padding: 4px 10px;
                                }
                            """)
                        else:
                            lbl.setStyleSheet("""
                                QLabel {
                                    color: #c62828;
                                    background-color: #ffebee;
                                    border: 1px solid #ef9a9a;
                                    border-radius: 4px;
                                    padding: 4px 10px;
                                }
                            """)
            if dialog in self._active_self_test_dialogs:
                self._active_self_test_dialogs.remove(dialog)

        dialog.finished.connect(_on_finished)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def on_generate_report(self):
        """Handle generate self-check report (placeholder)"""
        self.logger.log("Generating equipment self-check report...", False)
        
        QMessageBox.information(
            self,
            "Report Generated",
            "Equipment self-check report successfully generated.\n\n(Placeholder functionality - wire to report generation logic later)",
            QMessageBox.Ok
        )

    # AFTER
    def on_back_clicked(self):
        self.logger.log("Returning to Test Selection from Equipment Self Check", False)

        # ── Cancel any in-flight background refresh FIRST — otherwise it
        #    can still call turn_on_psu_channel(CH3)/start a new
        #    STM32Listener after the PSU-off write below, re-powering CH3
        #    right after we've explicitly shut it down.
        app_instance = QApplication.instance()
        refresh_thread = getattr(app_instance, "_self_test_refresh_thread", None)
        if refresh_thread is not None:
            refresh_thread.cancel()

        if hasattr(self, '_monitor') and self._monitor:
            self._monitor._reconnect_timer.stop()
            for lst in self._monitor._listeners:
                try:
                    lst.pause()
                except Exception:
                    pass

            worker = getattr(self._monitor, "_worker", None)
            psu_inst = getattr(worker, "psu_inst", None) if worker else None
            if psu_inst is not None:
                from psu.psu_helpers import turn_off_all_psu_channels
                turn_off_all_psu_channels(psu_inst, psu_lock=self._monitor._psu_lock)
                self.logger.log("PSU CH1/CH2/CH3 OFF on leaving Equipment Self Check", False)

        self.return_to_test_selection.emit()
        self.close()

    def closeEvent(self, event):
        """
        Handles the OS/title-bar 'X' close — on_back_clicked() only runs for
        the in-app Back button, so without this override, closing via 'X'
        skips stopping _reconnect_timer and the listener QThreads. Those
        threads keep polling/writing the same PSU VISA handle that
        aboutToQuit's shutdown_psu_ch3() then tries to write to concurrently,
        which is the same PSU-handle race _pre_step_ch3_and_sync() warns
        about elsewhere in this file — it can make the CH1-3 OFF write on
        quit silently fail, hang, or race, and leaves the QThreads running
        un-stopped underneath the closing window.
        Mirrors on_back_clicked()'s cleanup so both exit paths behave the
        same way before the window (and, being the last visible top-level
        window, the whole app via quitOnLastWindowClosed) actually closes.
        """
        # ── Cancel any in-flight background refresh FIRST — same reasoning
        #    as on_back_clicked(): without this, the refresh thread can
        #    still power CH3 back on / start a new STM32Listener after this
        #    method has already turned the PSU off.
        app_instance = QApplication.instance()
        refresh_thread = getattr(app_instance, "_self_test_refresh_thread", None)
        if refresh_thread is not None:
            refresh_thread.cancel()

        if hasattr(self, '_monitor') and self._monitor:
            self._monitor._reconnect_timer.stop()
            for lst in self._monitor._listeners:
                try:
                    lst.pause()
                except Exception:
                    pass

            worker = getattr(self._monitor, "_worker", None)
            psu_inst = getattr(worker, "psu_inst", None) if worker else None
            if psu_inst is not None:
                from psu.psu_helpers import turn_off_all_psu_channels
                turn_off_all_psu_channels(psu_inst, psu_lock=self._monitor._psu_lock)
                self.logger.log("PSU CH1/CH2/CH3 OFF on window close (Equipment Self Check)", False)

            # Fully stop the listener QThreads, not just pause them — pause()
            # leaves the thread alive and polling; on a real close (not
            # in-app navigation) there's no screen left to resume them, so
            # they should be torn down like stop_all() does.
            self._monitor.stop_all()

        event.accept()

    def on_device_disconnected(self, ui_name: str, message: str):
        self.device_status[ui_name] = False

        dot = self.findChild(QLabel, f"status_dot_{ui_name}")
        txt = self.findChild(QLabel, f"status_text_{ui_name}")
        if dot:
            dot.setStyleSheet("color: #d32f2f; background-color: transparent; border: none;")
        if txt:
            txt.setText("Not Connected")
            txt.setStyleSheet("color: #d32f2f; background-color: transparent; border: none;")
        # ── Update header status badge ────────────────────────────────────
        self._refresh_header_badge()
        
        run_btn = self.findChild(QPushButton, f"run_btn_{ui_name}")
        if run_btn:
            run_btn.setEnabled(False)
            run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #b0b0b0;
                    color: #f0f0f0;
                    border: none;
                    border-radius: 3px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
            """)
            
        # ── Show popup ONCE per device per session ───────────────────────
        if ui_name in self._disconnect_popup_shown:
            return
        self._disconnect_popup_shown.add(ui_name)

        toast = DisconnectToast(
            f"{ui_name} Disconnected",
            "Please reconnect the device.",
            parent=self
        )
        toast.show()    
        
class LockedDateEdit(QDateEdit):
    def mousePressEvent(self, event):
        super().mousePressEvent(event)   # allow cursor & typing

    def focusInEvent(self, event):
        super().focusInEvent(event)      # allow keyboard focus



class CalibrationDialog(QDialog):
    def __init__(self, device_name: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"Calibrate – {device_name}")
        from core.screen_utils import responsive_size
        self.setMinimumSize(400, 440)
        self.resize(responsive_size(0.28, 0.55, min_w=420, min_h=460, max_w=560, max_h=620))
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f4ff;
                border: none;
            }
            QLabel {
                background: transparent;
                border: none;
            }
            QFrame {
                border: none;
                background: transparent;
            }
            QDateEdit {
                background-color: #ffffff;
                border: 1px solid #d0d8f0;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 14px;
                color: #1a1a2e;
            }
            QDateEdit::up-button,
            QDateEdit::down-button {
                width: 0px; height: 0px; border: none;
            }
            QDateEdit::up-arrow,
            QDateEdit::down-arrow {
                image: none;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(10)

        # ===== Header =====
        title = QLabel(f"Calibrate – {device_name}")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#1a1a2e; border:none; padding-bottom: 4px;")
        main_layout.addWidget(title)

        # Blue underline accent
        accent_line = QFrame()
        accent_line.setFixedHeight(3)
        accent_line.setFixedWidth(60)
        accent_line.setStyleSheet("background-color: #1976d2; border-radius: 2px;")
        accent_wrapper = QHBoxLayout()
        accent_wrapper.addStretch()
        accent_wrapper.addWidget(accent_line)
        accent_wrapper.addStretch()
        main_layout.addLayout(accent_wrapper)

        main_layout.addSpacing(6)
        # ===== Last Calibrated Date label =====
        cal_header = QHBoxLayout()
        cal_header.setSpacing(8)
        cal_name = QLabel("Last Calibrated Date")
        cal_name.setFont(QFont("Arial", 10, QFont.Bold))
        cal_name.setStyleSheet("color:#1a1a2e; border:none;")
        cal_header.addStretch()
        cal_header.addWidget(cal_name)
        cal_header.addStretch()
        main_layout.addLayout(cal_header)

        date_row = QHBoxLayout()
        date_row.setSpacing(10)

        self.last_date = LockedDateEdit()
        self.last_date.setCalendarPopup(False)
        self.last_date.setReadOnly(False)
        self.last_date.setDisplayFormat("dd-MM-yyyy")
        self.last_date.setMinimumHeight(38)
        self.last_date.setCursor(Qt.PointingHandCursor)

        if parent and device_name in parent.calibration_data:
            last = parent.calibration_data[device_name]["last"]
            self.last_date.setDate(QDate(last.year, last.month, last.day))
        else:
            self.last_date.setDate(QDate.currentDate())

        self.last_date.dateChanged.connect(self._update_due_display)
        self.last_date.setStyleSheet("""
            QDateEdit {
                background-color: #ffffff;
                border: 1px solid #c8d4f0;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 15px;
                color: #1a1a2e;
            }
            QDateEdit:hover {
                border-color: #1976d2;
            }
        """)

        # ===== Manual Calendar Widget =====
        self.calendar = QCalendarWidget(None)
        self.calendar.setWindowFlags(Qt.Popup)
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #f5faff;
                color: #0d47a1;
                border: 1px solid #90caf9;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton {
                background: #e3f2fd; color: #0d47a1;
                border: none; border-radius: 4px;
                padding: 6px; margin: 2px;
            }
            QCalendarWidget QToolButton:hover { background: #bbdefb; }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                selection-background-color: #1976d2;
                selection-color: white;
                color: #0d47a1;
                gridline-color: #bbdefb;
            }
        """)
        self.calendar.clicked.connect(self._on_date_selected)
        self.calendar.hide()

        # Inline calendar icon button (inside date field area, right side)
        inline_cal_btn = QPushButton("")
        inline_cal_btn.setCursor(Qt.PointingHandCursor)
        inline_cal_btn.setFixedSize(38, 38)
        calendar_icon_path = RESOURCES_DIR / "calendar.png"
        if calendar_icon_path.exists():
            inline_cal_btn.setIcon(QIcon(str(calendar_icon_path)))
            inline_cal_btn.setIconSize(QSize(20, 20))
        else:
            inline_cal_btn.setText("📅")  # fallback if icon missing
        inline_cal_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #c8d4f0;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #e8f0fe; }
        """)
        inline_cal_btn.clicked.connect(self._open_calendar)

        # Today button — outlined style matching reference
        today_btn = QPushButton("Today")
        today_btn.setCursor(Qt.PointingHandCursor)
        today_btn.setFixedHeight(38)
        today_btn.setMinimumWidth(70)
        today_btn.setFont(QFont("Arial", 9, QFont.Bold))
        today_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 2px solid #1976d2;
                border-radius: 10px;
                color: #1976d2;
                padding: 0px 14px;
            }
            QPushButton:hover {
                background-color: #e8f0fe;
            }
        """)
        today_btn.clicked.connect(lambda: self.last_date.setDate(QDate.currentDate()))

        date_row.addWidget(self.last_date, 1)
        date_row.addWidget(today_btn)
        date_row.addWidget(inline_cal_btn)
        main_layout.addLayout(date_row)

        # Small hint text below date field
        hint_lbl = QLabel("Set the date the device was last calibrated.")
        hint_lbl.setAlignment(Qt.AlignCenter)
        hint_lbl.setStyleSheet("color: #8892b0; font-size: 11px; border:none;")
        main_layout.addWidget(hint_lbl)

        main_layout.addSpacing(4)

        # Thin divider
        mid_divider = QFrame()
        mid_divider.setFrameShape(QFrame.HLine)
        mid_divider.setStyleSheet("background-color: #dde3f0; border:none;")
        mid_divider.setFixedHeight(1)
        main_layout.addWidget(mid_divider)

        main_layout.addSpacing(4)

        # ===== Auto-computed Due Date =====
        due_header = QHBoxLayout()
        due_header.setSpacing(6)
        due_name = QLabel("Calibration Due Date")
        due_name.setFont(QFont("Arial", 10, QFont.Bold))
        due_name.setStyleSheet("color:#1a1a2e; border:none;")
        due_header.addStretch()
        due_header.addWidget(due_name)
        due_header.addStretch()
        main_layout.addLayout(due_header)

        due_box = QFrame()
        due_box.setStyleSheet("""
            QFrame {
                background-color: #f0faf0;
                border: 1.5px solid #66bb6a;
                border-radius: 12px;
            }
        """)
        due_box.setMinimumHeight(50)
        due_box_layout = QHBoxLayout(due_box)
        due_box_layout.setContentsMargins(16, 8, 16, 8)
        due_box_layout.setSpacing(10)

        self.due_display = QLabel()
        self.due_display.setFont(QFont("Arial", 16, QFont.Bold))
        self.due_display.setAlignment(Qt.AlignCenter)
        self.due_display.setStyleSheet("color: #2e7d32; border:none; background:transparent;")
        due_box_layout.addWidget(self.due_display, 1)

        main_layout.addWidget(due_box)
        self._update_due_display()

        # Subtext below due date box
        due_hint = QLabel("Calibration Due Date is automatically set to 1 year later.")
        due_hint.setAlignment(Qt.AlignCenter)
        due_hint.setStyleSheet("color: #8892b0; font-size: 11px; border:none;")
        main_layout.addWidget(due_hint)

        # ===== Info Box =====
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #eef2ff;
                border: 1px solid #c7d2fe;
                border-radius: 10px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 14, 16, 14)
        info_layout.setSpacing(14)

        info_icon_lbl = QLabel("i")
        info_icon_lbl.setFixedSize(32, 32)
        info_icon_lbl.setAlignment(Qt.AlignCenter)
        info_icon_lbl.setFont(QFont("Arial", 13, QFont.Bold))
        info_icon_lbl.setStyleSheet("""
            QLabel {
                background-color: #1976d2;
                color: white;
                border-radius: 16px;
                border: none;
            }
        """)
        info_layout.addWidget(info_icon_lbl, 0, Qt.AlignTop)

        info_text = QLabel(
            "The Calibration Due Date will update automatically\n"
            "when you change the Last Calibrated Date."
        )
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignCenter)
        info_text.setStyleSheet("color: #374151; font-size: 11px; border:none; background:transparent;")
        info_layout.addWidget(info_text, 1)

        main_layout.addWidget(info_frame)

        main_layout.addStretch()

        # ===== Buttons =====
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setFont(QFont("Arial", 10, QFont.Bold))
        cancel_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #374151;
                border: 1.5px solid #d1d5db;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Calibration")
        save_btn.setMinimumHeight(40)
        save_btn.setFont(QFont("Arial", 10, QFont.Bold))
        save_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)
        
    def _open_calendar(self):
        pos = self.last_date.mapToGlobal(
            self.last_date.rect().bottomLeft()
        )
        self.calendar.move(pos)
        self.calendar.show()
        
        
    def _update_due_display(self):
        qdate = self.last_date.date()
        last = date(qdate.year(), qdate.month(), qdate.day())
        due = _add_one_year(last)
        if hasattr(self, "due_display"):
            self.due_display.setText(due.strftime("%d-%m-%Y"))

    def _on_date_selected(self, qdate):
        self.last_date.setDate(qdate)   # ← was self.due_date
        self.calendar.hide()


class _LogSavedPopup(QDialog):
    """Minimal modern confirmation after Save Log as PDF."""
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 200)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 20)
        card_layout.setSpacing(10)

        # ── Green tick circle ──────────────────────────────────────────
        tick = QLabel("✓  Saved")
        tick.setAlignment(Qt.AlignCenter)
        tick.setFixedSize(110, 48)
        tick.setFont(QFont("Arial", 14, QFont.Bold))
        tick.setStyleSheet("""
            QLabel {
                background-color: #e8f5e9;
                color: #2e7d32;
                border-radius: 24px;
                border: none;
                padding: 0px 12px;
            }
        """)
        tick_row = QHBoxLayout()
        tick_row.addStretch()
        tick_row.addWidget(tick)
        tick_row.addStretch()
        card_layout.addLayout(tick_row)

        # ── Title ──────────────────────────────────────────────────────
        title = QLabel("Log PDF Saved")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color:#1a1a1a; background:transparent; border:none;")
        card_layout.addWidget(title)

        # ── Filename pill ──────────────────────────────────────────────
        name_lbl = QLabel(filename)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setWordWrap(True)
        name_lbl.setFont(QFont("Consolas", 8))
        name_lbl.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                color: #1a5da8;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 6px 10px;
            }
        """)
        card_layout.addWidget(name_lbl)

        card_layout.addSpacing(4)

        # ── OK button ─────────────────────────────────────────────────
        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(36)
        ok_btn.setFont(QFont("Arial", 10, QFont.Bold))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
        """)
        ok_btn.clicked.connect(self.accept)
        ok_row = QHBoxLayout()
        ok_row.addStretch()
        ok_row.addWidget(ok_btn)
        ok_row.addStretch()
        card_layout.addLayout(ok_row)

        outer.addWidget(card)


class _TestResultPopup(QDialog):
    """Shown automatically once a self-test finishes — actual PASS/FAIL, OK only."""
    def __init__(self, result: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 240)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 20)
        card_layout.setSpacing(10)

        is_pass = (result or "PASS").strip().upper() == "PASS"

        tick = QLabel("✓  PASS" if is_pass else "✗  FAIL")
        tick.setAlignment(Qt.AlignCenter)
        tick.setFixedSize(110, 48)
        tick.setFont(QFont("Arial", 14, QFont.Bold))
        tick.setStyleSheet("""
            QLabel {
                background-color: %s;
                color: %s;
                border-radius: 24px;
                border: none;
                padding: 0px 12px;
            }
        """ % (("#e8f5e9", "#2e7d32") if is_pass else ("#ffebee", "#c62828")))
        tick_row = QHBoxLayout()
        tick_row.addStretch()
        tick_row.addWidget(tick)
        tick_row.addStretch()
        card_layout.addLayout(tick_row)

        title = QLabel("Test Completed")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color:#1a1a1a; background:transparent; border:none;")
        card_layout.addWidget(title)

        subtitle_text = (
            "Test completed successfully! Please check View Reports to view the report."
            if is_pass else
            "Test completed with failures. Please check View Reports to view the report."
        )
        subtitle = QLabel(subtitle_text)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet("color:#6b7280; background:transparent; border:none;")
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(4)

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumHeight(36)
        ok_btn.setFont(QFont("Arial", 10, QFont.Bold))
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
        """)
        ok_btn.clicked.connect(self.accept)
        ok_row = QHBoxLayout()
        ok_row.addStretch()
        ok_row.addWidget(ok_btn)
        ok_row.addStretch()
        card_layout.addLayout(ok_row)

        outer.addWidget(card)


class SelfTestWorker(QThread):
    log_signal      = pyqtSignal(str, bool)
    done_signal     = pyqtSignal(bool)
    operator_signal = pyqtSignal(str, str, str)   # title, message, image_path
    operator_yesno_signal = pyqtSignal(str, str, str)
    queue_popup_signal = pyqtSignal(str, str, object, str, object, object)  # title, message, image_path, buttons, extra, callback

    def __init__(self, device_name, all_devices, connected_devices, skipped_devices, monitor=None):
        super().__init__()
        self.device_name       = device_name
        self.all_devices       = all_devices
        self.connected_devices = connected_devices
        self.skipped_devices   = skipped_devices
        self._passed           = True
        self._operator_event = Event()
        self.abort_event = Event()
        self.last_operator_response = None  # "YES" / "NO",
        self._monitor          = monitor   # DeviceMonitor reference for pause/resume
        self.psu_host = SelfTestPSUHost(self)
        self.psu = PSUAutomation(self.psu_host)
        self.osc_conn = None   # OscilloscopeConnection, borrowed from DeviceMonitor in pre-step

    # AFTER
    def run(self):
        try:
            if self.all_devices:
                self.log_signal.emit("[INIT]    Initializing full system test sequence...", False)
                for name in self.skipped_devices:
                    self.log_signal.emit(
                        f"[SKIP]    ⚠ {name} – Not Connected. Self test skipped.", False
                    )

                _monitor = self._monitor
                if _monitor is not None:
                    for lst in getattr(_monitor, '_listeners', []):
                        try:
                            lst.pause()
                        except Exception:
                            pass
                    try:
                        _monitor._reconnect_timer.stop()
                    except Exception:
                        pass
                    self.log_signal.emit("[SELF-TEST] Device listeners paused for self-test", False)

                try:
                    for name in self.connected_devices:
                        self._run_single(name, manage_listeners=False)
                finally:
                    if _monitor is not None:
                        for lst in getattr(_monitor, '_listeners', []):
                            try:
                                lst.resume()
                            except Exception:
                                pass
                        try:
                            _monitor._reconnect_timer.start()
                        except Exception:
                            pass
                        self._handback_oscilloscope()
                        self.log_signal.emit("[SELF-TEST] Device listeners resumed", False)

                if self.connected_devices:
                    verdict = "PASSED" if self._passed else "FAILED"
                    self.log_signal.emit(
                        f"[DONE]    {'✅' if self._passed else '❌'} "
                        f"Full system self-test {verdict} (connected devices only).", False
                    )
                else:
                    self.log_signal.emit(
                        "[DONE]    ⚠ No devices connected — nothing to test.", False
                    )
            else:
                self._run_single(self.device_name)
        except Exception as e:
            self.log_signal.emit(f"[ERROR]   Unexpected error: {e}", True)
            self._passed = False
        self.done_signal.emit(self._passed)

    def _queue_popup(self, title, message, image_path, buttons, extra=None, callback=None):
        """
        Thread-safe hook so worker-thread code (e.g. dmm_reader._recover_dmm)
        can request a popup on the UI thread. Runs inside SelfTestWorker's
        QThread, so this just emits a signal — SelfTestDialog does the
        actual QDialog creation on the main thread.
        """
        self.queue_popup_signal.emit(title, message, image_path, buttons, extra, callback)

    _SELF_TEST_MAP = {
        "PSU (Power Supply)":       lambda self: self_psu.run(self),
        "Audio Analyzer":           lambda self: self_audio_analyser.run(self),
        "Microcontroller":          lambda self: self_istj.run(self),
        "DMM (Digital Multimeter)": lambda self: self_dmm.run(self),
        "Oscilloscope":             lambda self: self_oscilloscope.run(self),
        "Ethernet":                 lambda self: self_ethernet.run(self),
        "RS232":                    lambda self: self_rs232.run(self),
        "RS422":                    lambda self: self_rs422.run(self),
    }


    
    def _pre_step_ch3_and_sync(self):
        print("[PRE-STEP] Powering CH3 OFF then ON, then syncing ISTJ...")

        # ── Step 0: Borrow existing PSU handle from DeviceMonitor (no new connection) ──
        self.psu._psu_error_handled = False
        self.psu._disconnect_in_progress = False
        self.psu._psu_ready_event.set()

        try:
            # Try to get the live PSU handle already held by the DeviceMonitor
            _existing_psu = None
            if self._monitor is not None:
                _worker = getattr(self._monitor, '_worker', None)
                if _worker is not None:
                    _existing_psu = getattr(_worker, 'psu_inst', None)

            if _existing_psu is not None:
                # Reuse the live handle — no close/reopen needed
                self.psu.psu_inst = _existing_psu
                # CRITICAL: also adopt DeviceMonitor's lock. self.psu.psu_lock
                # is a separate Lock() from PSUAutomation.__init__() — without
                # this, self-test writes (INST:NSEL/VOLT/CURR) and listener
                # polling (*IDN?, OUTP? CH3) can hit the shared VISA handle
                # concurrently and interleave on the wire. This is what let
                # CH1 voltage commands land on CH3.
                if self._monitor is not None and getattr(self._monitor, "_psu_lock", None) is not None:
                    self.psu.psu_lock = self._monitor._psu_lock
                self.log_signal.emit("[PRE-STEP] PSU handle borrowed from DeviceMonitor ✓ (lock synced)", False)
                try:
                    with self.psu.psu_lock:
                        self.psu.psu_inst.write("*CLS")
                        _time.sleep(0.1)
                        self.psu.psu_inst.write("SYST:REM")
                        _time.sleep(0.2)
                except Exception as _re:
                    self.log_signal.emit(f"[PRE-STEP] SYST:REM suppressed (non-fatal): {_re}", False)
            else:
                # Fallback: open fresh handle
                self.log_signal.emit("[PRE-STEP] No existing PSU handle — opening fresh...", False)
                if self.psu.psu_inst:
                    try:
                        self.psu.psu_inst.close()
                    except Exception:
                        pass
                    self.psu.psu_inst = None
                if self.psu.rm:
                    try:
                        self.psu.rm.close()
                    except Exception:
                        pass
                    finally:
                        self.psu.rm = None

                import pyvisa as _pyvisa
                self.psu.rm = _pyvisa.ResourceManager()
                self.psu.psu_inst = self.psu.find_psu()

                if self.psu.psu_inst:
                    self.log_signal.emit("[PRE-STEP] PSU handle opened fresh ✓", False)
                    try:
                        with self.psu.psu_lock:
                            self.psu.psu_inst.write("*CLS")
                            _time.sleep(0.1)
                            self.psu.psu_inst.write("SYST:REM")
                            _time.sleep(0.2)
                    except Exception as _re:
                        self.log_signal.emit(f"[PRE-STEP] SYST:REM suppressed (non-fatal): {_re}", False)
                else:
                    self.log_signal.emit("[PRE-STEP] PSU not found — CH3 power cycle will be skipped", False)
        except Exception as e:
            self.log_signal.emit(f"[PRE-STEP] PSU handle open failed (non-fatal): {e}", False)

        # ── Step 0.5: Borrow existing Oscilloscope handle from DeviceMonitor ────
        try:
            _existing_osc = None
            if self._monitor is not None:
                _worker = getattr(self._monitor, '_worker', None)
                if _worker is not None:
                    _existing_osc = getattr(_worker, 'oscilloscope_connection', None)

            if _existing_osc is not None:
                # Stop DeviceMonitor's OscilloscopeListener so it can't race
                # the test thread for write()/query() on the same VISA session.
                self._monitor._remove_dead_listener(DeviceType.OSC)
                self._monitor._disconnected_devices.discard("Oscilloscope")

                conn = OscilloscopeConnection()
                conn.instrument = _existing_osc
                conn.resource_string = getattr(_existing_osc, "resource_name", None)
                try:
                    idn = _existing_osc.query("*IDN?").strip()
                    conn.identification = conn._parse_idn_response(idn)
                except Exception:
                    conn.identification = None

                self.osc_conn = conn
                self.log_signal.emit(
                    "[PRE-STEP] Oscilloscope handle borrowed from DeviceMonitor ✓ (listener paused)",
                    False,
                )
            else:
                self.log_signal.emit(
                    "[PRE-STEP] No existing Oscilloscope handle — will connect on first use",
                    False,
                )
        except Exception as e:
            self.log_signal.emit(f"[PRE-STEP] Oscilloscope handle borrow failed (non-fatal): {e}", False)

        # ── Step 1: Turn CH3 OFF first (power cycle the board) ──────────────────
        try:
            self.psu.psu_send_command("*CLS")
            self.psu.psu_send_command("INST:NSEL 3")
            _time.sleep(0.1)
            self.psu.psu_send_command("OUTP OFF")
            _time.sleep(1.5)   # let board fully de-power
            self.log_signal.emit("[PRE-STEP] CH3 turned OFF (board de-powered)", False)
        except Exception as e:
            self.log_signal.emit(f"[PRE-STEP] CH3 OFF failed (non-fatal): {e}", False)

        # ── Step 2: Turn CH3 ON (power board back up) ───────────────────────────
        try:
            _time.sleep(0.5)
            self.psu.worker_ch3_5v()
            self.log_signal.emit("[PRE-STEP] CH3 turned ON (5V/1A) — waiting for board to boot...", False)
            _time.sleep(8.0)   # ← increased: board needs time to power up and enumerate USB
        except Exception as e:
            self.log_signal.emit(f"[PRE-STEP] CH3 power-on failed (non-fatal): {e}", False)

        # ── Step 2.5: Release any existing Microcontroller listener's serial
        # handle before we try to open the port ourselves. pause() alone
        # leaves the port OS-locked, which is why every ISTJ sync after the
        # first successful one silently failed with the port already open.
        try:
            if self._monitor is not None:
                self._monitor._remove_dead_listener(DeviceType.MCU)
                self.log_signal.emit("[PRE-STEP] Existing ISTJ listener released ✓", False)
        except Exception as e:
            self.log_signal.emit(f"[PRE-STEP] ISTJ listener release failed (non-fatal): {e}", False)

        # ── Step 3: Identify available COM ports ────────────────────────────────
        stm32_ports = []   # ← declare BEFORE the try so Step 3.5 always sees it
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for p in ports:
                desc = p.description or ""
                if any(k in desc for k in ["Bluetooth", "Wireless", "Intel", "Modem"]):
                    continue
                if (p.vid == 0x0483 or
                        "ISTJ" in desc or
                        "ST-Link" in desc or
                        "USB Serial" in desc):
                    stm32_ports.append(p.device)

            if stm32_ports:
                self.log_signal.emit(f"[PRE-STEP] ISTJ COM port(s) found: {', '.join(stm32_ports)}", False)
            else:
                self.log_signal.emit("[PRE-STEP] No ISTJ COM port found — sync may fail", False)
        except Exception as e:
            self.log_signal.emit(f"[PRE-STEP] COM port scan failed: {e}", False)

        # ── Step 3.5: Extra wait if no COM port found yet ────────────────────────
        if not stm32_ports:
            self.log_signal.emit("[PRE-STEP] No COM port found — waiting 3s more for USB enumeration...", False)
            _time.sleep(3.0)
            # Re-scan once more
            try:
                import serial.tools.list_ports as _lp
                stm32_ports = [
                    p.device for p in _lp.comports()
                    if p.vid == 0x0483
                    or any(k in (p.description or "") for k in ["ISTJ", "ST-Link", "USB Serial"])
                    if not any(k in (p.description or "") for k in ["Bluetooth", "Wireless", "Intel", "Modem"])
                ]
                if stm32_ports:
                    self.log_signal.emit(f"[PRE-STEP] ISTJ COM port(s) found after wait: {', '.join(stm32_ports)}", False)
                else:
                    self.log_signal.emit("[PRE-STEP] Still no ISTJ COM port — sync will likely fail", False)
            except Exception:
                pass

        # ── Step 4: Sync ISTJ directly on confirmed COM port ────────────────────
        try:
            if stm32_ports:
                com_port = stm32_ports[0]
                self.log_signal.emit(f"[PRE-STEP] Using COM port: {com_port}", False)
                import serial as _serial
                tx = bytearray([0x02, 0x35, 0x02, 0xFF, 0x00, 0x98, 0x03, 0x0D])
                try:
                    ser = _serial.Serial(com_port, 115200, timeout=2)
                    ser.reset_input_buffer()
                    ser.write(tx)
                    _time.sleep(0.4)
                    rx = ser.read(8)
                    ser.close()
                    if (len(rx) == 8 and rx[0] == 0x02 and rx[1] == 0x35 and
                            rx[3] == 0xFF and rx[4] == 0x01 and
                            rx[6] == 0x03 and rx[7] == 0x0D):
                        self.log_signal.emit("[PRE-STEP] ISTJ sync confirmed ✓", False)
                    else:
                        self.log_signal.emit(f"[PRE-STEP] Sync response invalid: {rx.hex() if rx else 'empty'}", False)
                except Exception as se:
                    self.log_signal.emit(f"[PRE-STEP] Serial open failed on {com_port}: {se}", False)
            else:
                self.log_signal.emit("[PRE-STEP] No COM port found — cannot sync ISTJ", False)
            _time.sleep(2)
        except Exception as e:
            self.log_signal.emit(f"[PRE-STEP] ISTJ sync raised an exception: {e}", False)
            _time.sleep(2)

    def _handback_oscilloscope(self):
        """
        Reverse of the oscilloscope borrow in _pre_step_ch3_and_sync(): give
        DeviceMonitor back ownership of the live VISA instrument by rebuilding
        its OscilloscopeListener, so normal disconnect/reconnect polling
        resumes. Called from run()/_run_single()'s finally blocks — must be
        safe to call even if nothing was ever borrowed (self.osc_conn is None).
        """
        _monitor = self._monitor
        if _monitor is None or self.osc_conn is None:
            return

        try:
            from devices.device_listeners import OscilloscopeListener

            inst = self.osc_conn.instrument
            if inst is not None:
                _monitor._remove_dead_listener(DeviceType.OSC)
                _monitor._start(OscilloscopeListener(inst))
                _monitor._tracked_instance_ids["Oscilloscope"] = id(inst)
                _monitor._disconnected_devices.discard("Oscilloscope")
                if _monitor._worker is not None:
                    _monitor._worker.device_status["Oscilloscope"] = True

            self.log_signal.emit("[HANDBACK] Oscilloscope handle returned to DeviceMonitor ✓", False)
        except Exception as e:
            self.log_signal.emit(f"[HANDBACK] Oscilloscope handback failed (non-fatal): {e}", False)
        finally:
            self.osc_conn = None
    

    _PRE_STEP_DEVICES      = {"Oscilloscope", "Microcontroller", "DMM (Digital Multimeter)", "Audio Analyzer","PSU (Power Supply)", "DMM (Digital Multimeter)"}
    
    
    def _run_single(self, name: str, manage_listeners: bool = True):
        _monitor = self._monitor
        # ── Guard against a stale set() from a previous popup/device in this
        # run — without this, the very next operator popup's .wait() call can
        # return instantly, letting the test proceed before the operator has
        # clicked OK.
        self._operator_event.clear()

        if manage_listeners and _monitor is not None:
            for lst in getattr(_monitor, '_listeners', []):
                try:
                    lst.pause()
                except Exception:
                    pass
            try:
                _monitor._reconnect_timer.stop()
            except Exception:
                pass
            self.log_signal.emit("[SELF-TEST] Device listeners paused for self-test", False)

        try:

            # CH3 5V + ISTJ sync — devices that talk to the board.
            # Runs in full for every pre-step device, every time — unchanged.
            if name in self._PRE_STEP_DEVICES:
                self._pre_step_ch3_and_sync()
                _time.sleep(2)

            fn = self._SELF_TEST_MAP.get(name)
            if fn:
                fn(self)
            else:
                self.log_signal.emit(f"[SKIP]    No self-test defined for {name}.", False)
        except Exception as e:
            self.log_signal.emit(f"[ERROR]   {name} self-test raised: {e}", True)
            self._passed = False
        finally:
            if manage_listeners and _monitor is not None:
                for lst in getattr(_monitor, '_listeners', []):
                    try:
                        lst.resume()
                    except Exception:
                        pass
                try:
                    _monitor._reconnect_timer.start()
                except Exception:
                    pass
                self._handback_oscilloscope()
                self.log_signal.emit("[SELF-TEST] Device listeners resumed", False)

            
class SerialTerminalDialog(QDialog):
    """
    Interactive RS232/RS422 serial console.
    Step 1: pick COM port -> Connect
    Step 2: send ASCII, view TX/RX log -> Save Log as PDF / Abort Test
    """
    def __init__(self, iface_name: str, parent=None):
        super().__init__(parent)
        self.iface_name = iface_name          # "RS232" or "RS422"
        self.module = self_rs232 if iface_name == "RS232" else self_rs422
        self.ser = None
        self.log_lines = []
        self.test_completed = False
        self.test_result = "PASS"
        self.overall_result = "PASS"   # tracks worst-case across all sends this session

        # ── Self-test report setup (mirrors SelfTestDialog) ─────────────
        try:
            create_self_test_report(_report_name(iface_name))
        except Exception as _e:
            print(f"[SERIAL TEST] Report setup failed (non-fatal): {_e}")

        self.setWindowTitle(f"Serial Line Configuration – {iface_name}")
        from core.screen_utils import responsive_size
        self.setMinimumSize(420, 460)
        self.resize(responsive_size(0.30, 0.62, min_w=440, min_h=480, max_w=620, max_h=720))
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel  { color: #1a1a1a; background: transparent; border: none; padding: 0px; margin: 0px; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        # ── Title row: circular network icon + title/subtitle ──────────
        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        badge = self._circle_icon(48, "#1976d2")
        title_row.addWidget(badge, 0, Qt.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_lbl = QLabel(f"{iface_name} Test")
        title_lbl.setFont(QFont("Arial", 16, QFont.Bold))
        title_lbl.setStyleSheet("color:#0d1b3e; border:none; background:transparent;")
        title_col.addWidget(title_lbl)
        subtitle_lbl = QLabel("Select a serial port and establish a connection to start testing.")
        subtitle_lbl.setFont(QFont("Arial", 9))
        subtitle_lbl.setStyleSheet("color:#6b7280; border:none; background:transparent;")
        title_col.addWidget(subtitle_lbl)
        title_row.addLayout(title_col, 1)

        outer.addLayout(title_row)

        # ── Card 1: SERIAL PORT TO CONNECT ──────────────────────────────
        card1 = self._make_card()
        card1_layout = card1.layout()

        card1_layout.addLayout(self._section_header("SERIAL PORT TO CONNECT", "#1976d2"))

        line_lbl = QLabel("Serial Port")
        line_lbl.setFont(QFont("Arial", 10, QFont.Bold))
        line_lbl.setStyleSheet("color:#1a1a1a; border:none; background:transparent;")
        card1_layout.addWidget(line_lbl)

        self.port_combo = QComboBox()
        self.port_combo.setMinimumHeight(42)
        self.port_combo.setFont(QFont("Arial", 11, QFont.Bold))
        self.port_combo.addItems(["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "Custom"])
        self.port_combo.setCurrentText("COM1")
        self.port_combo.view().setStyleSheet("""
            QListView {
                background-color: #ffffff; color: #0d1b3e;
                outline: none;
            }
            QListView::item {
                padding: 8px 12px; border: none;
            }
            QListView::item:hover {
                background-color: #1976d2; color: #ffffff;
            }
            QListView::item:selected {
                background-color: #1565c0; color: #ffffff;
            }
        """)
        self.port_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff; color: #0d1b3e;
                border: 2px solid #1976d2; border-radius: 8px; padding: 4px 12px;
            }
            QComboBox::drop-down { border: none; width: 28px; }
        """)
        card1_layout.addWidget(self.port_combo)

        self.custom_box = QFrame()
        self.custom_box.setStyleSheet("QFrame { border: 1px solid #e0e0e0; border-radius: 8px; background:#fafbfc; }")
        custom_layout = QVBoxLayout(self.custom_box)
        custom_layout.setContentsMargins(14, 12, 14, 12)
        custom_layout.setSpacing(6)
        custom_lbl = QLabel("Custom Serial Port")
        custom_lbl.setFont(QFont("Arial", 10, QFont.Bold))
        custom_lbl.setStyleSheet("border:none; background:transparent;")
        custom_layout.addWidget(custom_lbl)
        self.custom_edit = QLineEdit()
        self.custom_edit.setPlaceholderText("COM1")
        self.custom_edit.setMinimumHeight(38)
        self.custom_edit.setFont(QFont("Arial", 10))
        self.custom_edit.setStyleSheet("""
            QLineEdit { background-color: #ffffff; color: #0d1b3e;
                        border: 1px solid #c8d4e0; border-radius: 6px; padding: 6px 10px; }
        """)
        custom_layout.addWidget(self.custom_edit)
        hint = QLabel('ℹ  Select "Custom" from the dropdown above to enter a custom serial port.')
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet("color:#1976d2; border:none; background:transparent;")
        hint.setWordWrap(True)
        custom_layout.addWidget(hint)
        card1_layout.addWidget(self.custom_box)
        self.custom_box.setVisible(False)

        self.port_combo.currentTextChanged.connect(
            lambda t: self.custom_box.setVisible(t == "Custom")
        )

        self.connect_btn = QPushButton("  Connect")
        network_icon_path = RESOURCES_DIR / "link.png"
        if network_icon_path.exists():
            self.connect_btn.setIcon(QIcon(str(network_icon_path)))
            self.connect_btn.setIconSize(QSize(18, 18))
        self.connect_btn.setMinimumHeight(44)
        self.connect_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setStyleSheet("""
            QPushButton { background:#1976d2; color:white; border-radius:8px; border:none; }
            QPushButton:hover { background:#1565c0; }
            QPushButton:pressed { background:#0d47a1; }
        """)
        self.connect_btn.clicked.connect(self._on_connect)
        card1_layout.addWidget(self.connect_btn)

        outer.addWidget(card1)

        # ── Card 2: COMMUNICATION ────────────────────────────────────────
        card2 = self._make_card()
        card2_layout = card2.layout()

        card2_layout.addLayout(self._section_header("COMMUNICATION", "#1976d2", icon_text="💬"))

        input_lbl = QLabel("Input")
        input_lbl.setFont(QFont("Arial", 10, QFont.Bold))
        input_lbl.setStyleSheet("border:none; background:transparent;")
        card2_layout.addWidget(input_lbl)

        input_row = QFrame()
        input_row.setStyleSheet("""
            QFrame { background-color: #ffffff; border: 1px solid #c8d4e0; border-radius: 8px; }
        """)
        input_row_layout = QHBoxLayout(input_row)
        input_row_layout.setContentsMargins(4, 2, 4, 2)
        input_row_layout.setSpacing(4)

        self.input_edit = QLineEdit()
        self.input_edit.setMaxLength(8)   # hard UI limit — matches 8-bit frame constraint
        self.input_edit.setPlaceholderText("Enter your message (max 8 chars)")
        self.input_edit.setMinimumHeight(40)
        self.input_edit.setFont(QFont("Arial", 11))
        self.input_edit.setStyleSheet("""
            QLineEdit { background-color: transparent; color: #0d1b3e; border: none; padding: 4px 10px; }
        """)
        self.input_edit.returnPressed.connect(self._on_send)
        input_row_layout.addWidget(self.input_edit, 1)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(38, 38)
        self.send_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton { background:transparent; color:#1976d2; border:none; }
            QPushButton:hover { color:#0d47a1; }
        """)
        self.send_btn.clicked.connect(self._on_send)
        input_row_layout.addWidget(self.send_btn)

        card2_layout.addWidget(input_row)

        display_lbl = QLabel("Display")
        display_lbl.setFont(QFont("Arial", 10, QFont.Bold))
        display_lbl.setStyleSheet("border:none; background:transparent;")
        card2_layout.addWidget(display_lbl)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Display will appear here...")
        self.log_box.setFont(QFont("Consolas", 10))
        self.log_box.setMinimumHeight(200)
        self.log_box.setStyleSheet("""
            QTextEdit { background-color: #0d0f1a; color: #cdd6f4;
                        border: 1px solid #313244; border-radius: 8px; padding: 8px; }
        """)
        card2_layout.addWidget(self.log_box, 1)

        outer.addWidget(card2, 1)

        # ── Bottom buttons — 50/50 split ─────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.cancel_btn = QPushButton("✕   Cancel")
        self.cancel_btn.setMinimumHeight(46)
        self.cancel_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #1976D2;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #1565C0;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        self.cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(self.cancel_btn, 1)

        self.save_btn = QPushButton("Save Log as PDF")
        self.save_btn.setMinimumHeight(46)
        self.save_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setVisible(False)
        self.save_btn.setStyleSheet("""
            QPushButton { background:#1976d2; color:white; border-radius:8px; border:none; }
            QPushButton:hover { background:#1565c0; }
        """)
        self.save_btn.clicked.connect(self._save_pdf)
        btn_row.addWidget(self.save_btn, 1)

        self.abort_btn = QPushButton("⛔   Abort")
        self.abort_btn.setMinimumHeight(46)
        self.abort_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.abort_btn.setCursor(Qt.PointingHandCursor)
        self.abort_btn.setVisible(False)
        self.abort_btn.setStyleSheet("""
            QPushButton { background:#e53935; color:white; border-radius:8px; border:none; }
            QPushButton:hover { background:#c62828; }
        """)
        self.abort_btn.clicked.connect(self.close)
        btn_row.addWidget(self.abort_btn, 1)

        outer.addLayout(btn_row)

    # ------------------------------------------------------------------
    def _circle_icon(self, size: int, bg_color: str) -> QLabel:
        lbl = QLabel()
        lbl.setFixedSize(size, size)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                border-radius: {size // 2}px;
                border: none;
            }}
        """)
        icon_path = RESOURCES_DIR / "network.png"
        if icon_path.exists():
            pix = QPixmap(str(icon_path))
            if not pix.isNull():
                inner = int(size * 0.5)
                lbl.setPixmap(pix.scaled(inner, inner, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        return lbl

    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 12px; }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(8)
        return card

    def _section_header(self, text: str, color: str, icon_text: str = None) -> QVBoxLayout:
        wrap = QVBoxLayout()
        wrap.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(8)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(26, 26)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"background-color:{color}; border-radius:13px; color:white; border:none;")
        if icon_text:
            icon_lbl.setText(icon_text)
            icon_lbl.setFont(QFont("Arial", 10))
        else:
            icon_path = RESOURCES_DIR / "network.png"
            if icon_path.exists():
                pix = QPixmap(str(icon_path))
                if not pix.isNull():
                    icon_lbl.setPixmap(pix.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        row.addWidget(icon_lbl, 0)

        title_lbl = QLabel(text)
        title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        title_lbl.setStyleSheet(f"color:{color}; border:none; background:transparent;")
        row.addWidget(title_lbl, 1)

        wrap.addLayout(row)

        underline = QFrame()
        underline.setFixedHeight(1)
        underline.setStyleSheet(f"background-color:{color}; border:none;")
        wrap.addWidget(underline)

        return wrap

    def _selected_port(self) -> str:
        text = self.port_combo.currentText()
        if text == "Custom":
            return self.custom_edit.text().strip() or "COM1"
        return text

    def _on_connect(self):
        port = self._selected_port()
        try:
            self.ser = self.module.open_connection(port)
        except Exception as e:
            QMessageBox.warning(self, "Connection Failed", f"Could not open {port}:\n\n{e}")
            return

        self._append(f"[CONNECT] {self.iface_name} connected on {port} "
                     f"(9600-8-N-1, flow control: none)")

        self.port_combo.setEnabled(False)
        self.custom_edit.setEnabled(False)
        self.input_edit.setFocus()

        self.cancel_btn.setVisible(False)
        self.connect_btn.setVisible(False)
        self.save_btn.setVisible(True)
        self.abort_btn.setVisible(True)

    def _on_send(self):
        if not (self.ser and self.ser.is_open):
            QMessageBox.warning(
                self, "Not Connected",
                "Serial port is not connected. Click Connect before sending data."
            )
            return

        text = self.input_edit.text()
        if not text:
            return
        self.input_edit.clear()
        try:
            tx, rx, result = self.module.send_and_receive(self.ser, text)
            self._append(f"TX >> {tx}")
            self._append(f"RX << {rx}" if rx else "RX << (no response)")
            self._append(f"[RESULT] {result}", is_error=(result == "FAIL"))

            self.test_result = result
            if result == "FAIL":
                self.overall_result = "FAIL"

        except ValueError as ve:
            self._append(f"[ERROR] {ve}", True)
            QMessageBox.warning(self, "TX Length Error", str(ve))
        except Exception as e:
            self._append(f"[ERROR] Send/receive failed: {e}", True)
            

    def _append(self, text: str, is_error: bool = False):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {text}"
        self.log_lines.append(line)
        color = "#ef5350" if is_error else ("#89dceb" if text.startswith("RX") else
                 "#a6e3a1" if text.startswith("TX") else "#f9e2af")
        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.End)
        fmt = self.log_box.currentCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(line + "\n", fmt)
        self.log_box.setTextCursor(cursor)
        self.log_box.ensureCursorVisible()

    def _save_pdf(self):
        from core.paths import LOGS_PDF_DIR
        result = "PASS"
        date_part = datetime.now().strftime("%d%m%Y_%H%M")
        pdf_path = LOGS_PDF_DIR / f"SELF_{self.iface_name}_{result}_{date_part}_LOG.pdf"

        c = rl_canvas.Canvas(str(pdf_path), pagesize=A4)
        w, h = A4
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor("#1a5da8"))
        c.drawString(40, h - 50, f"Serial Terminal Log – {self.iface_name}")
        c.setFont("Courier", 9)
        y = h - 90
        for line in self.log_lines:
            if y < 50:
                c.showPage()
                y = h - 40
                c.setFont("Courier", 9)
            c.setFillColor(colors.HexColor("#333333"))
            c.drawString(40, y, line)
            y -= 14
        c.save()
        _LogSavedPopup(pdf_path.name, parent=self).exec_()

    def closeEvent(self, event):
        self.module.close_connection(self.ser)
        self.test_completed = True
        try:
            finalize_self_test_report(
                _report_name(self.iface_name), self.overall_result, self.log_lines
            )
        except Exception as e:
            print(f"[SERIAL TEST] finalize failed (non-fatal): {e}")
        event.accept()
        self.done(QDialog.Accepted)
                    
class SelfTestDialog(QDialog):
    """
    Popup for running self-test on one or all devices.
    Runs real device modules via SelfTestWorker thread.
    """
    def __init__(
        self,
        device_name: str,
        parent=None,
        all_devices: bool = False,
        connected_devices: list = None,
        skipped_devices: list = None,
        display_name: str = None,
        
    ):
        super().__init__(parent)
        self.device_name = device_name
        self.display_name = display_name or device_name
        self.all_devices = all_devices
        self.log_lines = []
        self.test_completed = False
        self.test_result = "PASS"   # default; overwritten in _on_done

        # ── Self-test report + log setup ──────────────────────────────────
        _report_device = "All_Devices" if all_devices else _report_name(device_name)
        try:
            self._st_report_path = create_self_test_report(_report_device)
            self._st_log_path    = create_self_test_log(_report_device)
        except Exception as _e:
            print(f"[SELF-TEST] Report/log setup failed (non-fatal): {_e}")
            self._st_report_path = None
            self._st_log_path    = None
        connected_devices = connected_devices or []
        skipped_devices   = skipped_devices   or []

        self.setWindowTitle(f"Self Test Run – {self.display_name}")
        from core.screen_utils import responsive_size
        self.setMinimumSize(760, 520)
        self.resize(responsive_size(0.65, 0.8, min_w=820, min_h=560, max_w=1500, max_h=1000))
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint
        )
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel  { color: #1a1a1a; background: transparent; border: none; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(f"{'Full System' if all_devices else self.display_name} – Self Test")
        title.setFont(QFont("Consolas", 12, QFont.Bold))
        title.setStyleSheet("color:#1a5da8;")
        layout.addWidget(title)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("Consolas", 9))
        self.log_box.setStyleSheet("""
            QTextEdit {
                background-color: #11111b;
                color: #a6e3a1;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_box, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.save_btn = QPushButton("Save Log as PDF")
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumWidth(160)
        self.save_btn.setMinimumHeight(36)
        self.save_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2; color: white;
                border-radius: 4px; padding: 8px 14px; border: none;
            }
            QPushButton:hover  { background-color: #1565c0; }
            QPushButton:disabled { background-color: #555; color: #999; }
        """)
        self.save_btn.clicked.connect(self._save_pdf)
        btn_row.addWidget(self.save_btn)

        # In SelfTestDialog.__init__, replace the close_btn block:
        self.close_btn = QPushButton("Abort Test")
        self.close_btn.setMinimumWidth(100)
        self.close_btn.setMinimumHeight(36)
        self.close_btn.setEnabled(True)          # ← was False, now always clickable
        self.close_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #c62828; color: white;
                border-radius: 4px; padding: 8px 14px; border: none;
            }
            QPushButton:hover { background-color: #b71c1c; }
        """)
        self.close_btn.clicked.connect(self.close)   # funnels into closeEvent below
        btn_row.addWidget(self.close_btn)

        layout.addLayout(btn_row)

        # ── Launch worker thread ──────────────────────────────────────────
        _monitor = getattr(parent, '_monitor', None) if parent else None
        self._worker = SelfTestWorker(
            device_name, all_devices, connected_devices, skipped_devices,
            monitor=_monitor
        )
        self._worker.log_signal.connect(self._on_log)
        self._worker.done_signal.connect(self._on_done)
        self._worker.operator_signal.connect(self._show_operator_prompt)
        self._worker.operator_yesno_signal.connect(self._show_operator_yesno_prompt)
        self._worker.queue_popup_signal.connect(self._show_queued_popup)
        self._worker.start()

    @pyqtSlot(str, bool)
    def _on_log(self, message: str, is_error: bool):
        self._append(message, is_error)


    @pyqtSlot(bool)
    def _on_done(self, passed: bool):
        self.test_completed = True
        self.save_btn.setEnabled(True)
        self.close_btn.setEnabled(True)
        self.close_btn.setText("Close")
        

        # ── Override passed flag by scanning log lines for any FAIL ──────────
        # Individual test modules emit "[FAIL]" lines but may not propagate the
        # failure back through the worker's _passed flag. Scanning log_lines is
        # the authoritative source of truth.
        _log_upper = " ".join(self.log_lines).upper()
        has_fail   = "FAIL" in _log_upper
        has_pass   = "PASS" in _log_upper

        if has_fail:
            passed = False          # at least one sub-test failed → whole report is FAIL
        elif not has_pass and not passed:
            passed = False          # no PASS logged either, honour the worker's verdict

        result = "PASS" if passed else "FAIL"
        self.test_result = result   # expose to caller
        _report_device = "All_Devices" if self.all_devices else _report_name(self.device_name)

        # ── Finalise xlsx + PDF ───────────────────────────────────────────────
        try:
            xlsx_path, pdf_path = finalize_self_test_report(
                _report_device, result, self.log_lines
            )
            self._final_xlsx = xlsx_path
            self._final_pdf  = pdf_path
        except Exception as _e:
            print(f"[SELF-TEST] finalize failed (non-fatal): {_e}")
            self._final_xlsx = None
            self._final_pdf  = None

                # ── Write final log file ──────────────────────────────────────────────
        try:
            from core.paths import LOGS_SELF_TEST_DIR
            safe      = _report_device.replace(" ", "_").replace("(", "").replace(")", "")
            ts        = datetime.now().strftime("%d%m%Y_%H%M")
            final_log = LOGS_SELF_TEST_DIR / f"SELF_TEST_{safe}_{result}_{ts}.log"
            with open(final_log, "w", encoding="utf-8") as f:
                for line in self.log_lines:
                    f.write(line + "\n")
            temp_log = getattr(self, "_st_log_path", None)
            if temp_log:
                from pathlib import Path as _Path
                _tp = _Path(temp_log)
                if _tp.exists() and _tp.resolve() != final_log.resolve():
                    _tp.unlink(missing_ok=True)
            self._final_log_path = str(final_log)
            print(f"[SELF-TEST] Log saved → {final_log}")
        except Exception as _le:
            print(f"[SELF-TEST LOG] write failed (non-fatal): {_le}")
            self._final_log_path = None

        # ── Auto popup with real PASS/FAIL once the report is finalized ──
        try:
            _TestResultPopup(result, parent=self).exec_()
        except Exception as _ce:
            print(f"[SELF-TEST] Result popup failed (non-fatal): {_ce}")

    @pyqtSlot(str, str, str)
    def _show_operator_prompt(self, title: str, message: str, image_path: str):
        # ── Ensure this popup starts from a clean, unset state — closes the
        # race where the worker's .wait() (called right after emitting this
        # signal) could see a stale set() from an earlier popup and return
        # before the operator has actually clicked OK.
        self._worker._operator_event.clear()
        popup = OperatorInfoPopup(
            title=title,
            message=message,
            image_path=image_path if image_path else None,
            buttons="ok",
            parent=self
        )
        popup.finished.connect(lambda _: self._worker._operator_event.set())
        popup.setWindowModality(Qt.NonModal)
        popup.setWindowFlags(popup.windowFlags() | Qt.WindowStaysOnTopHint)
        popup.show()
    @pyqtSlot(str, str, str)
    def _show_operator_yesno_prompt(self, title: str, message: str, image_path: str):
        self._worker._operator_event.clear()
        popup = OperatorInfoPopup(
            title=title,
            message=message,
            image_path=image_path if image_path else None,
            buttons="yes_no",
            parent=self
        )

        def _on_finished(_result_code):
            self._worker.last_operator_response = popup.operator_response  # "YES" or "NO"
            self._worker._operator_event.set()

        popup.finished.connect(_on_finished)
        popup.setWindowModality(Qt.NonModal)
        popup.setWindowFlags(popup.windowFlags() | Qt.WindowStaysOnTopHint)
        popup.show()

    @pyqtSlot(str, str, object, str, object, object)
    def _show_queued_popup(self, title, message, image_path, buttons, extra, callback):
        popup = OperatorInfoPopup(
            title=title,
            message=message,
            image_path=image_path if image_path else None,
            buttons=buttons,
            parent=self
        )
        if callback:
            popup.finished.connect(lambda result: callback(result, popup))
        popup.setWindowModality(Qt.NonModal)
        popup.setWindowFlags(popup.windowFlags() | Qt.WindowStaysOnTopHint)
        popup.show()

    # ── Same rich colorizer as SingleTestScreen ──────────────────────────
    def _parse_log_line(self, message: str):
        import re
        OFF_BLACK  = "#cccccc"
        PASS_GREEN = "#4caf50"
        FAIL_RED   = "#ef5350"
        YELLOW     = "#fbc02d"
        CYAN       = "#89dceb"

        upper = message.upper()
        is_pass_line = "PASS" in upper or "✅" in upper or "✓" in upper or "SUCCESS" in upper or "SUCCESSFULLY" in upper
        is_fail_line = "FAIL" in upper or "❌" in upper or "✗" in upper

        # Section separator
        if message.startswith("==========") and message.endswith("=========="):
            return [(message, YELLOW)]

        # SKIP lines
        if "[SKIP]" in message:
            return [(message, CYAN)]

        UNIT_PATTERN = re.compile(
            r'(?<![a-zA-Z])'
            r'(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*'
            r'(Vrms|mVrms|uVrms|µVrms|dBrA|dBu|dBm|dB|mV|kΩ|GΩ|MΩ|Ω|ohm|kHz|MHz|Hz|ms|µs|us|mA|mW|rpm|°C|°F|%|V|A|s|W)'
            r'(?=\s|,|;|\.|$|\)|\]|%)',
            re.IGNORECASE
        )
        OL_PATTERN = re.compile(r'\bOL\b', re.IGNORECASE)

        clean = re.sub(r'\s*(✓\s*PASS|✗\s*FAIL|PASS|FAIL)\s*$', '', message, flags=re.IGNORECASE).rstrip()
        value_color = PASS_GREEN if is_pass_line else (FAIL_RED if is_fail_line else OFF_BLACK)

        matches = sorted(
            [(m, "unit") for m in UNIT_PATTERN.finditer(clean)] +
            [(m, "ol")   for m in OL_PATTERN.finditer(clean)],
            key=lambda x: x[0].start()
        )

        parts = []
        last = 0
        for m, _ in matches:
            if m.start() > last:
                parts.append((clean[last:m.start()], OFF_BLACK))
            parts.append((m.group(0), value_color))
            last = m.end()
        if last < len(clean):
            parts.append((clean[last:], OFF_BLACK))

        already_has_pass = "✓" in message or "✅" in message
        already_has_fail = "✗" in message or "❌" in message
        if is_pass_line and not already_has_pass:
            parts.append((" ✓ PASS", PASS_GREEN))
        elif is_fail_line and not already_has_fail:
            parts.append((" ✗ FAIL", FAIL_RED))

        return parts if parts else [(message, OFF_BLACK)]

    def _append(self, text: str, is_error: bool = False):
        import re
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {text}"
        self.log_lines.append(line)
        # Write to live log file
        if getattr(self, "_st_log_path", None):
            append_self_test_log(self._st_log_path, line)

        cursor = self.log_box.textCursor()
        cursor.movePosition(cursor.End)

        def insert(txt, color):
            fmt = self.log_box.currentCharFormat()
            fmt.setForeground(QColor(color))
            cursor.insertText(txt, fmt)

        # Timestamp in dim gray
        insert(f"[{ts}] ", "#666666")

        if is_error:
            insert(text + "\n", "#ef5350")
        else:
            parts = self._parse_log_line(text)
            for part_text, color in parts:
                insert(part_text, color)
            insert("\n", "#cccccc")

        self.log_box.setTextCursor(cursor)
        self.log_box.ensureCursorVisible()

    def _save_pdf(self):
        """
        Convert the finalized .log/.txt log file (already written by
        append_self_test_log during the run) into a colorized PDF, saved
        into LOGS_PDF_DIR. Falls back to colorizing self.log_lines directly
        if the on-disk log file is missing for any reason.
        """
        from core.paths import LOGS_PDF_DIR

        final_log_path = getattr(self, "_final_log_path", None)
        if final_log_path and Path(final_log_path).exists():
            with open(final_log_path, "r", encoding="utf-8") as f:
                lines_to_render = [ln.rstrip("\n") for ln in f.readlines()]
        else:
            lines_to_render = self.log_lines

        _report_device = "All_Devices" if self.all_devices else _report_name(self.device_name)
        safe_name = _report_device.replace(" ", "_").replace("(", "").replace(")", "")
        all_text  = " ".join(lines_to_render).upper()
        result    = "FAIL" if "FAIL" in all_text else "PASS"
        date_part = datetime.now().strftime("%d%m%Y")
        time_part = datetime.now().strftime("%H%M")
        pdf_path  = LOGS_PDF_DIR / f"SELF_TEST_{safe_name}_{result}_{date_part}_{time_part}_LOG.pdf"

        c = rl_canvas.Canvas(str(pdf_path), pagesize=A4)
        w, h = A4
        c.setFillColor(colors.HexColor("#ffffff"))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor("#1a5da8"))
        c.drawString(40, h - 50, f"Self Test Log – {_report_device}")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#444444"))
        c.drawString(40, h - 68, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        y = h - 100
        # ── Unicode → ASCII so Courier font renders cleanly ───────────────
        _UNICODE_MAP = {
            "µ": "u", "✓": "[OK]", "✅": "[OK]", "✗": "[FAIL]",
            "❌": "[FAIL]", "⚠": "[WARN]", "°": " deg",
            "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
            "Ω": "ohm", "—": "-", "–": "-", "•": "-",
            "─": "-", "━": "-", "│": "|", "→": "->", "➜": "->", "●": "*",
        }
        def _ascii_safe(s: str) -> str:
            for u, a in _UNICODE_MAP.items():
                s = s.replace(u, a)
            # Catch anything still non-latin1 and drop it cleanly instead of "?"
            return "".join(c if ord(c) < 256 else "" for c in s)

        c.setFont("Courier", 9)
        for line in lines_to_render:
            safe_line  = _ascii_safe(line)
            upper_line = safe_line.upper()

            if "FAIL" in upper_line:
                color = colors.HexColor("#c62828")
            elif "PASS" in upper_line or "[OK]" in upper_line or "SUCCESS" in upper_line:
                color = colors.HexColor("#2e7d32")
            elif "[SKIP]" in upper_line:
                color = colors.HexColor("#0277bd")
            elif safe_line.strip().startswith("==========") and safe_line.strip().endswith("=========="):
                color = colors.HexColor("#e65100")
            else:
                color = colors.HexColor("#333333")

            c.setFillColor(color)
            # Word-aware wrapping at 90 chars (safe for A4 + Courier 9)
            max_chars = 90
            words     = safe_line.split(" ")
            current   = ""
            for word in words:
                test = (current + " " + word).lstrip() if current else word
                if len(test) > max_chars:
                    if y < 50:
                        c.showPage()
                        c.setFillColor(colors.HexColor("#ffffff"))
                        c.rect(0, 0, w, h, fill=1, stroke=0)
                        y = h - 40
                        c.setFont("Courier", 9)
                        c.setFillColor(color)
                    c.drawString(40, y, current)
                    y -= 14
                    current = word
                else:
                    current = test
            if current:
                if y < 50:
                    c.showPage()
                    c.setFillColor(colors.HexColor("#ffffff"))
                    c.rect(0, 0, w, h, fill=1, stroke=0)
                    y = h - 40
                    c.setFont("Courier", 9)
                    c.setFillColor(color)
                c.drawString(40, y, current)
                y -= 14
        c.save()

        _LogSavedPopup(pdf_path.name, parent=self).exec_()

    def closeEvent(self, event):
        if not self.test_completed:
            reply = QMessageBox.question(
                self, "Abort Self Test",
                "The self test is still running.\n\n"
                "Aborting will stop it immediately, turn OFF all PSU channels, "
                "and switch CH3 back ON.\n\n"
                "Are you sure you want to abort?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
            self._abort_test()
            event.accept()
            self.done(QDialog.Rejected)   # aborted — don't record a "last test" timestamp
            return

        event.accept()
        self.done(QDialog.Accepted)       # normal completion — emits finished(), triggers DB/UI update in parent

    def _abort_test(self):
        self._append("[ABORT] Operator requested test abort — stopping...", True)

        try:
            self._worker.abort_event.set()
            self._worker._operator_event.set()
            self._worker.last_operator_response = "NO"
        except Exception:
            pass

        # AFTER
        if self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(3000)

        import core.dmm_reader as _dmm_module
        _dmm_module.force_reset_dmm_state()

        self._resume_listeners_after_abort()

        self.test_completed = True
        self.test_result = "ABORTED"
        self.save_btn.setEnabled(True)
        self.close_btn.setText("Close")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #45475a; color: white;
                border-radius: 4px; padding: 8px 14px; border: none;
            }
            QPushButton:hover { background-color: #585b70; }
        """)

    def _resume_listeners_after_abort(self):
        """Abort just stops the running test in place — no PSU channel
        shutdown, no relay default-state reset, no CH3 restore. Cleanup is
        limited to two things:
          1. Resuming the device listeners that were paused for the test
             run: terminate() can kill the worker mid self-test, before
             its own finally-block resume runs, so we resume them here
             explicitly. This puts Equipment Self Check back to normal
             monitoring.
          2. Turning the APX generator OFF: several apx_reader functions
             (generator_control, audible_reduce_until_silent,
             read_apx_meter, etc.) set Generator.On = True and only flip
             it back False at their own normal end or except block.
             terminate() can kill the worker before that line runs,
             leaving the generator driving a tone indefinitely. This is
             a direct hardware-safety cleanup, not a "reset to default
             state" step, so it stays even though relay/PSU resets don't.
        A future Run Self Test click always spins up a brand new
        SelfTestWorker and starts over from the beginning — it never
        picks this aborted run back up."""
        monitor = getattr(self._worker, "_monitor", None)
        if monitor is not None:
            for lst in getattr(monitor, "_listeners", []):
                try:
                    lst.resume()
                except Exception:
                    pass
            self._append("[ABORT] Device listeners resumed", False)

        try:
            from core import apx_reader
            apx = apx_reader.get_apx()
            if apx is not None:
                apx.BenchMode.Generator.On = False
                try:
                    apx.AudibleSignalMonitor.Enabled = False
                except Exception:
                    pass
                self._append("[ABORT] APX generator turned OFF", False)
        except Exception as e:
            self._append(f"[ABORT] APX generator shutdown skipped (non-fatal): {e}", False)

class DisconnectToast(QWidget):
    """
    Non-blocking, non-modal disconnect notification.
    Appears in the top-right of the parent window, auto-dismisses after 6 s,
    or when the user clicks the X button. Never touches the main thread event loop.
    """
    def __init__(self, title: str, body: str, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_ShowWithoutActivating)   # ← KEY: never steals focus

        self.setFixedWidth(320)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                border: 1px solid #d32f2f;
                border-radius: 8px;
            }
            QLabel { border: none; background: transparent; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # Title row
        title_row = QHBoxLayout()
        icon_lbl = QLabel("⚠")
        icon_lbl.setStyleSheet("color:#d32f2f; font-size:14px;")
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Arial", 9, QFont.Bold))
        title_lbl.setStyleSheet("color:#f38ba8;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #585b70;
                border: none; font-size: 11px;
            }
            QPushButton:hover { color: #cdd6f4; }
        """)
        close_btn.clicked.connect(self.close)
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl, 1)
        title_row.addWidget(close_btn)
        layout.addLayout(title_row)

        body_lbl = QLabel(body)
        body_lbl.setWordWrap(True)
        body_lbl.setStyleSheet("color:#cdd6f4; font-size:8pt;")
        layout.addWidget(body_lbl)

        self.adjustSize()

        # Position: top-right of parent
        if parent:
            pr = parent.geometry()
            x = pr.right() - self.width() - 16
            y = pr.top() + 80
            self.move(x, y)

        # Auto-dismiss after 6 s
        QTimer.singleShot(6000, self.close)

    def mousePressEvent(self, event):
        self.close()