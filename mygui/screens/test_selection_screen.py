from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize , QTimer

from screens.lru_selection import Singletestselection
from core.paths import RESOURCES_DIR, PDF_TEST_REPORTS_DIR

class DisconnectPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Disconnect")
        self.setFixedSize(420, 240)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 14px;
                border: 1px solid #e5e7eb;
            }
        """)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Title row
        title = QLabel("Disconnect ISTJ")
        title.setFont(QFont("Arial", 13, QFont.Bold))
        title.setStyleSheet("color: #111827; border: none;")
        layout.addWidget(title)

        self.sub = QLabel("Do you want to disconnect and return to connection screen?")
        self.sub.setFont(QFont("Arial", 10))
        self.sub.setWordWrap(True)
        self.sub.setStyleSheet("color: #374151; border: none;")
        layout.addWidget(self.sub)

        self.status = QLabel("")
        self.status.setFont(QFont("Arial", 10, QFont.Bold))
        self.status.setStyleSheet("color: #1a5da8; border: none;")
        layout.addWidget(self.status)

        layout.addStretch()

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.no_btn = QPushButton("Cancel")
        self.no_btn.setFixedSize(110, 36)
        self.no_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-weight: bold;
                color: #111827;
            }
            QPushButton:hover { background: #f9fafb; }
        """)

        self.yes_btn = QPushButton("Disconnect")
        self.yes_btn.setFixedSize(130, 36)
        self.yes_btn.setStyleSheet("""
            QPushButton {
                background: #d32f2f;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover { background: #b71c1c; }
        """)

        btn_row.addWidget(self.no_btn)
        btn_row.addWidget(self.yes_btn)

        layout.addLayout(btn_row)

        self.no_btn.clicked.connect(lambda: self.done(QDialog.Rejected))
        self.yes_btn.clicked.connect(lambda: self.done(QDialog.Accepted))

    def set_working(self):
        self.status.setText("Disconnecting... please wait")
        self.yes_btn.setEnabled(False)
        self.no_btn.setEnabled(False)

    def set_success(self):
        self.status.setStyleSheet("color: #1b5e20; font-weight: bold;")
        self.status.setText("✓ Disconnected Successfully")
        self.yes_btn.hide()
        self.no_btn.setText("OK")
        self.no_btn.setEnabled(True)

    def set_failed(self):
        self.status.setStyleSheet("color: #d32f2f; font-weight: bold;")
        self.status.setText("✗ Disconnect Failed")
        self.yes_btn.setEnabled(True)
        self.no_btn.setEnabled(True)
        self.yes_btn.setText("Retry")


class TestSelectionScreen(QMainWindow):
    full_test_requested = pyqtSignal()
    unit_test_requested = pyqtSignal()
    equipment_self_test_requested = pyqtSignal()
    test_reports_requested = pyqtSignal()
    return_to_connection = pyqtSignal()
    


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
        layout.setSpacing(18)
        # ==============================
        # TOP HEADER BAR (Logo + Title + Disconnect)
        # ==============================
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                border-radius: 0px;
            }
        """)
        top_bar.setFixedHeight(80)

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)
        top_layout.setSpacing(10)

        # Logo Left
        logo_label = QLabel()
        logo_pixmap = QPixmap(str(RESOURCES_DIR / "hal_logo.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaledToWidth(140, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_layout.addWidget(logo_label)

        top_layout.addStretch()


        # Disconnect Button Right
        disconnect_btn = QPushButton()
        disconnect_btn.setMinimumHeight(44)
        disconnect_btn.setMinimumWidth(160)
        disconnect_btn.setMaximumWidth(160)
        disconnect_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        disconnect_btn.setFont(QFont("Arial", 8, QFont.Bold))
        disconnect_btn.setIconSize(QSize(15, 15))

        disconnect_icon = QPixmap(str(RESOURCES_DIR / "disconnect.png"))
        if not disconnect_icon.isNull():
            disconnect_btn.setIcon(QIcon(disconnect_icon))

        disconnect_btn.setText("DISCONNECT")
        disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 14px;
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

        layout.addWidget(top_bar)
        
        # ==============================
        # TITLE BELOW HEADER
        # ==============================
        title_label = QLabel("Select Mode")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #1a5da8;
                background-color: transparent;
                letter-spacing: 0.6px;
                margin-top: 10px;
                margin-bottom: 10px;
            }
        """)
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

        unit_test_btn.clicked.connect(self.open_station_selection)
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
    def open_station_selection(self):
        self.station_window = Singletestselection(self)
        # self.station_window.return_to_connection.connect(self.return_to_connection.emit)
        self.station_window.show()
        self.hide()
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



    def disconnect_and_return(self):
        popup = DisconnectPopup(self)

        # Ask first
        if popup.exec_() != QDialog.Accepted:
            return

        # Show working state
        popup = DisconnectPopup(self)
        popup.show()
        popup.set_working()
        QApplication.processEvents()

        success = self.perform_disconnect_handshake()

        if success:
           popup.set_success()
           QTimer.singleShot(700, lambda: (popup.close(), self.return_to_connection.emit(), self.close()))
        else:
            popup.set_failed()



    def perform_disconnect_handshake(self) -> bool:
        try:
            import serial
            import serial.tools.list_ports
            import time

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
                if (
                    port.vid == 0x0483
                    or "STM32" in port.description
                    or "ST-Link" in port.description
                    or "USB Serial" in port.description
                ):
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

