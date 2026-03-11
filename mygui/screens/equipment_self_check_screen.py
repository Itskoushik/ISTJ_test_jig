from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal,QDate
from PyQt5.QtGui import QFont, QPixmap, QColor
from core.paths import RESOURCES_DIR, LOGS_DIR
from core.logger import Logger
from datetime import datetime, date
import sqlite3
from db.db_paths import CALIBRATION_DB_PATH


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
                due_date TEXT
            )
        """)
        self.conn.commit()

    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT device_name, last_date, due_date FROM calibration")
        rows = cursor.fetchall()

        data = {}
        for device, last, due in rows:
            data[device] = {
                "last": date.fromisoformat(last),
                "due": date.fromisoformat(due)
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
        self.db = CalibrationDB()
        # Default values (used only if DB is empty)
        default_data = {
            "PSU (Power Supply)": {"last": date(2024, 4, 1), "due": date(2024, 10, 1)},
            "Audio Analyzer": {"last": date(2024, 3, 15), "due": date(2024, 9, 15)},
            "ISTJ": {"last": date(2023, 11, 10), "due": date(2024, 5, 10)},
            "DMM (Digital Multimeter)": {"last": date(2024, 2, 20), "due": date(2024, 8, 20)},
            "Oscilloscope": {"last": date(2024, 5, 1), "due": date(2024, 11, 1)},
        }

        # Load from DB
        self.calibration_data = self.db.get_all()

        # If DB empty → seed defaults
        if not self.calibration_data:
            for device, dates in default_data.items():
                self.db.upsert(device, dates["last"], dates["due"])
            self.calibration_data = default_data


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
            "color: #4caf50; border: none;" if all_ok else "color: #d32f2f; border: none;"
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
                "name": "Audio Analyzer",
                "port": "APX | DLL",
                "connected": self.device_status.get("Audio Analyzer", False),
            },
            {
                "name": "ISTJ",
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
        card.setMinimumHeight(320)  # Fixed height for consistency
        card.setMaximumHeight(320)
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
            "Audio Analyzer": "audio.png",
            "ISTJ": "micro.png",
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

        last_lbl = QLabel(f"Last: {cal['last'].isoformat()}")
        last_lbl.setFont(QFont("Arial", 9))
        last_lbl.setStyleSheet("""
            QLabel {
                background:#f1f3f4;
                padding:6px 10px;
                border-radius:4px;
                color:#333;
            }
        """)

        due_btn = QPushButton(f"Due: {cal['due'].isoformat()}")
        due_btn.setFont(QFont("Arial", 9))
        due_btn.setCursor(Qt.PointingHandCursor)
        due_btn.setStyleSheet("""
            QPushButton {
                background:#e8f5e9;
                border:1px solid #4caf50;
                padding:6px 10px;
                border-radius:4px;
                color:#2e7d32;
            }
            QPushButton:hover {
                background:#c8e6c9;
            }
        """)

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
        due_btn.installEventFilter(self)

        def open_calibration_menu():
            reset_btn.setVisible(not reset_btn.isVisible())

        def reset_calibration():
            dialog = CalibrationDialog(device["name"], self)
            if dialog.exec_():
                new_due = dialog.due_date.date().toPyDate()
                today = date.today()

                self.calibration_data[device["name"]] = {
                    "last": today,
                    "due": new_due,
                }

                # Save to DB
                self.db.upsert(device["name"], today, new_due)


                # Update UI
                last_lbl.setText(f"Last: {today.isoformat()}")
                due_btn.setText(f"Due: {new_due.isoformat()}")
                reset_btn.setVisible(False)
                
                
        due_btn.clicked.connect(open_calibration_menu)
        reset_btn.clicked.connect(reset_calibration)
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
        
        
class LockedDateEdit(QDateEdit):
    def mousePressEvent(self, event):
        super().mousePressEvent(event)   # allow cursor & typing

    def focusInEvent(self, event):
        super().focusInEvent(event)      # allow keyboard focus



class CalibrationDialog(QDialog):
    def __init__(self, device_name: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"Calibrate – {device_name}")
        self.setFixedSize(420, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
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
                background-color: #f5f5f5;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }

            /* REMOVE SPIN ARROWS */
            QDateEdit::up-button,
            QDateEdit::down-button {
                width: 0px;
                height: 0px;
                border: none;
            }

            QDateEdit::up-arrow,
            QDateEdit::down-arrow {
                image: none;
            }
        """)


        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(18)

        # ===== Header =====
        title = QLabel("Calibration Update")
        title.setFont(QFont("Arial", 13, QFont.Bold))
        title.setStyleSheet("color:#1a1a1a;border:none;")
        main_layout.addWidget(title)

        subtitle = QLabel(f"Device: {device_name}")
        subtitle.setStyleSheet("color:#666;border:none;")
        main_layout.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color:#e0e0e0;")
        main_layout.addWidget(divider)
        # ===== Calendar Section =====
        cal_label = QLabel("Calibration Due Date")
        cal_label.setFont(QFont("Arial", 10, QFont.Bold))
        cal_label.setContentsMargins(0, 10, 0, 4)
        main_layout.addWidget(cal_label)

        date_row = QHBoxLayout()

        self.due_date = LockedDateEdit()
        self.due_date.setCalendarPopup(False)
        self.due_date.setReadOnly(False)
        self.due_date.setDisplayFormat("dd-MM-yyyy")
        self.due_date.setMinimumHeight(38)
        self.due_date.setCursor(Qt.PointingHandCursor)

        if parent and device_name in parent.calibration_data:
            due = parent.calibration_data[device_name]["due"]
            self.due_date.setDate(QDate(due.year, due.month, due.day))
        else:
            self.due_date.setDate(QDate.currentDate())

        self.due_date.setStyleSheet("""
            QDateEdit {
                background-color: #f5f5f5;
                border: 1px solid #cfd8dc;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                color: #1a1a1a;
            }
            QDateEdit:hover {
                background-color: #eeeeee;
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
                background: #e3f2fd;
                color: #0d47a1;
                border: none;
                border-radius: 4px;
                padding: 6px;
                margin: 2px;
            }

            QCalendarWidget QToolButton:hover {
                background: #bbdefb;
            }

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


        calendar_btn = QPushButton("📅")
        calendar_btn.setCursor(Qt.PointingHandCursor)
        calendar_btn.setFixedSize(40, 38)
        calendar_btn.setStyleSheet("""
            QPushButton {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
        """)

        calendar_btn.clicked.connect(self._open_calendar)


        date_row.addWidget(self.due_date)
        date_row.addWidget(calendar_btn)
        main_layout.addLayout(date_row)


        # ===== Info Box =====
        info = QLabel(
            "ℹ️  Last Calibration will be automatically set to today\n"
            "when the due date is updated."
        )
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 12px;
                border-radius: 6px;
                color: #444;
                border: none;
            }
        """)

        main_layout.addWidget(info)

        main_layout.addStretch()

        # ===== Buttons =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumWidth(110)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e;
                color: white;
                border-radius: 4px;
                padding: 8px 14px;
                font-weight: bold;
                border:none;
            }
            QPushButton:hover {
                background-color: #757575;
                border:none;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Calibration")
        save_btn.setMinimumWidth(150)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 4px;
                padding: 8px 14px;
                font-weight: bold;
                border:none;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)
        
    def _open_calendar(self):
        pos = self.due_date.mapToGlobal(
            self.due_date.rect().bottomLeft()
        )
        self.calendar.move(pos)
        self.calendar.show()
        
        
    def _on_date_selected(self, date):
        self.due_date.setDate(date)
        self.calendar.hide()




