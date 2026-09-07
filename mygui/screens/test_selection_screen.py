from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import *
from PyQt5.QtCore import QSize , QTimer
from core.screen_utils import sp, responsive_size, responsive_geometry
from matplotlib.pylab import outer
from screens.lru_selection import Singletestselection
from core.paths import RESOURCES_DIR, PDF_TEST_REPORTS_DIR
from screens.test_reports_screen import EmptyStateDialog
import time
class DisconnectPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Disconnect")
        self.setFixedSize(responsive_size(0.30, 0.38, min_w=460, min_h=360, max_w=560, max_h=460))
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(sp(30), sp(30), sp(30), sp(50))

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border-radius: 14px;
                border: 1px solid #e5e7eb;
            }
        """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(sp(24))
        shadow.setXOffset(0)
        shadow.setYOffset(sp(6))
        shadow.setColor(QColor(0, 0, 0, 90))
        card.setGraphicsEffect(shadow)

        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(sp(18), sp(18), sp(18), sp(18))
        layout.setSpacing(sp(12))
        
        # Icon badge (socket.png in a circular red-tinted background)
        icon_wrap = QLabel()
        icon_wrap.setFixedSize(sp(72), sp(72))
        icon_wrap.setAlignment(Qt.AlignCenter)
        icon_wrap.setStyleSheet("""
            QLabel {
                background-color: #fdecea;
                border-radius: %dpx;
            }
        """ % (sp(36)))
        socket_pixmap = QPixmap(str(RESOURCES_DIR / "socket.png"))
        if not socket_pixmap.isNull():
            icon_wrap.setPixmap(socket_pixmap.scaled(sp(34), sp(34), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(icon_wrap, 0, Qt.AlignCenter)
        layout.addSpacing(sp(10))

        # Title row
        title = QLabel("Disconnect ISTJ")
        title.setFont(QFont("Arial", sp(15), QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #111827; border: none;")
        layout.addWidget(title)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #e5e7eb; background-color: #e5e7eb; max-height: 1px;")
        layout.addWidget(divider)
        layout.addSpacing(sp(6))

        self.sub = QLabel("Do you want to disconnect from ISTJ and return to the connection screen?")
        self.sub.setFont(QFont("Arial", sp(11)))
        self.sub.setWordWrap(True)
        self.sub.setAlignment(Qt.AlignCenter)
        self.sub.setStyleSheet("color: #374151; border: none;")
        layout.addWidget(self.sub)
        layout.addSpacing(sp(10))

        info_box = QFrame()
        info_box.setStyleSheet("""
            QFrame {
                background-color: #eaf2fb;
                border: 1px solid #cfe0f5;
                border-radius: 8px;
            }
        """)
        info_layout = QHBoxLayout(info_box)
        info_layout.setContentsMargins(sp(12), sp(10), sp(12), sp(10))
        info_layout.setSpacing(sp(10))

        info_icon = QLabel("i")
        info_icon.setFixedSize(sp(20), sp(20))
        info_icon.setAlignment(Qt.AlignCenter)
        info_icon.setStyleSheet("""
            background-color: #1a5da8;
            color: white;
            border-radius: %dpx;
            font-weight: bold;
        """ % sp(10))

        info_text = QLabel("Ongoing tests will be stopped and any unsaved data may be lost.")
        info_text.setWordWrap(True)
        info_text.setFont(QFont("Arial", sp(9)))
        info_text.setStyleSheet("color: #1a5da8; border: none;")

        info_layout.addWidget(info_icon, 0, Qt.AlignTop)
        info_layout.addWidget(info_text)
        layout.addWidget(info_box)

        self.status = QLabel("")
        self.status.setFont(QFont("Arial", sp(10), QFont.Bold))
        self.status.setStyleSheet("color: #1a5da8; border: none;")
        layout.addWidget(self.status)

        layout.addStretch()

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(sp(12))

        self.no_btn = QPushButton("  Cancel")
        self.no_btn.setFixedSize(sp(180), sp(44))
        self.no_btn.setIcon(QIcon(str(RESOURCES_DIR / "cancel_x.png")))  # or reuse an existing X icon
        self.no_btn.setIconSize(QSize(sp(14), sp(14)))
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

        self.yes_btn = QPushButton("  Disconnect")
        self.yes_btn.setFixedSize(sp(180), sp(44))
        socket_btn_icon = QPixmap(str(RESOURCES_DIR / "socket.png"))
        if not socket_btn_icon.isNull():
            self.yes_btn.setIcon(QIcon(socket_btn_icon))
        self.yes_btn.setIconSize(QSize(sp(16), sp(16)))
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

        btn_row.addStretch()
        btn_row.addWidget(self.no_btn)
        btn_row.addWidget(self.yes_btn)
        btn_row.addStretch()

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
        self.setUpdatesEnabled(False)   # ✅ Suppress repaints during construction
        self.setWindowTitle("HAL - Test Selection")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
        x, y, w, h = responsive_geometry(0.55, 0.8, min_w=800, min_h=650, max_w=1300, max_h=1000)
        self.setGeometry(x, y, w, h)
        self.setMinimumSize(sp(800), sp(650))
        self.setStyleSheet("background-color: #f5f5f5;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(sp(40), sp(40), sp(40), sp(40))
        layout.setSpacing(sp(18))
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
        top_bar.setFixedHeight(sp(80))

        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(sp(20), sp(10), sp(20), sp(10))
        top_layout.setSpacing(sp(10))

        # Logo Left
        logo_label = QLabel()
        logo_pixmap = QPixmap(str(RESOURCES_DIR / "hal_logo.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaledToWidth(sp(140), Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_layout.addWidget(logo_label)

        top_layout.addStretch()


        # Disconnect Button Right
        disconnect_btn = QPushButton()
        disconnect_btn.setMinimumHeight(sp(44))
        disconnect_btn.setMinimumWidth(sp(160))
        disconnect_btn.setMaximumWidth(sp(160))
        disconnect_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        disconnect_btn.setFont(QFont("Arial", sp(8), QFont.Bold))
        disconnect_btn.setIconSize(QSize(sp(15), sp(15)))

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
        title_label.setFont(QFont("Arial", sp(18), QFont.Bold))
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
        grid_layout.setContentsMargins(sp(20), sp(20), sp(20), sp(20))
        grid_layout.setHorizontalSpacing(sp(24))
        grid_layout.setVerticalSpacing(sp(24))

        # =========================
        # ROW 0, COL 0: RUN FULL TEST BUTTON (PRIMARY)
        # =========================
        full_test_btn = QPushButton()
        full_test_btn.setMinimumSize(sp(280), sp(200))
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
        full_layout.setSpacing(sp(16))
        full_layout.setAlignment(Qt.AlignCenter)

        full_icon = QLabel()
        full_icon.setPixmap(QPixmap(str(RESOURCES_DIR / "full_test.png")).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        full_icon.setAlignment(Qt.AlignCenter)
        full_icon.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        full_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        full_text = QLabel("RUN FULL TEST")
        full_text.setFont(QFont("Arial", sp(12), QFont.Bold))
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
        unit_test_btn.setMinimumSize(sp(280), sp(200))
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
        unit_layout.setSpacing(sp(16))
        unit_layout.setAlignment(Qt.AlignCenter)

        unit_icon = QLabel()
        unit_icon.setPixmap(QPixmap(str(RESOURCES_DIR / "unit_test.png")).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        unit_icon.setAlignment(Qt.AlignCenter)
        unit_icon.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        unit_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        unit_text = QLabel("RUN SINGLE TEST")
        unit_text.setFont(QFont("Arial", sp(12), QFont.Bold))
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
        calibrations_btn.setMinimumSize(sp(280), sp(200))
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
        calib_layout.setSpacing(sp(16))
        calib_layout.setAlignment(Qt.AlignCenter)

        calib_icon = QLabel()
        calib_icon.setPixmap(QPixmap(str(RESOURCES_DIR / "calibrations.png")).scaled(
            sp(64), sp(64), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ) if QPixmap(str(RESOURCES_DIR / "calibrations.png")).isNull() == False else QPixmap(sp(64), sp(64)))
        calib_icon.setAlignment(Qt.AlignCenter)
        calib_icon.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        calib_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        calib_text = QLabel("EQUIPMENT SELF TEST")
        calib_text.setFont(QFont("Arial", sp(12), QFont.Bold))
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
        reports_btn.setMinimumSize(sp(280), sp(200))
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
        reports_layout.setSpacing(sp(16))
        reports_layout.setAlignment(Qt.AlignCenter)

        reports_icon = QLabel()
        reports_icon.setPixmap(QPixmap(str(RESOURCES_DIR / "test_reports.png")).scaled(
            sp(64), sp(64), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ) if QPixmap(str(RESOURCES_DIR / "test_reports.png")).isNull() == False else QPixmap(sp(64), sp(64)))
        reports_icon.setAlignment(Qt.AlignCenter)
        reports_icon.setStyleSheet("background-color: transparent; border: none; padding: 0px; margin: 0px;")
        reports_icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        reports_text = QLabel("PRINT REPORT")
        reports_text.setFont(QFont("Arial", sp(12), QFont.Bold))
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
        self.setUpdatesEnabled(True)

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
        """
        Disconnect sequence:
        1. Find PSU and try to turn off all channels.
        2. If that attempt fails, re-discover the PSU (fresh instrument handle)
        and retry turning off all channels once.
        Returns True if either attempt succeeded.
        """
        import pyvisa

        def find_psu(resource_manager):
            for resource in resource_manager.list_resources():
                try:
                    inst = resource_manager.open_resource(resource)
                    inst.timeout = 2000
                    idn = inst.query("*IDN?").strip()
                    if "RIGOL" in idn.upper() and "DP8" in idn.upper():
                        return inst
                    inst.close()
                except Exception:
                    continue
            return None

        def turn_off_all_channels(inst):
            for ch in [1, 2, 3]:
                inst.write(f"INST:NSEL {ch}")
                time.sleep(0.1)
                inst.write("OUTP OFF")
                time.sleep(0.1)

        rm = None
        psu_inst = None
        shutdown_ok = False

        # ---------- Attempt 1 ----------
        try:
            rm = pyvisa.ResourceManager()
            psu_inst = find_psu(rm)
            if psu_inst:
                turn_off_all_channels(psu_inst)
                shutdown_ok = True
                print("[DISCONNECT] All PSU channels turned OFF (attempt 1)")
            else:
                print("[DISCONNECT] PSU not found (attempt 1)")
        except Exception as e:
            print(f"[DISCONNECT] Attempt 1 failed: {e}")

        # ---------- Attempt 2: fresh PSU handle, retry ----------
        if not shutdown_ok:
            try:
                if psu_inst:
                    try:
                        psu_inst.close()
                    except Exception:
                        pass
                if rm is None:
                    rm = pyvisa.ResourceManager()
                psu_inst = find_psu(rm)
                if psu_inst:
                    turn_off_all_channels(psu_inst)
                    shutdown_ok = True
                    print("[DISCONNECT] All PSU channels turned OFF (attempt 2)")
                else:
                    print("[DISCONNECT] PSU not found (attempt 2)")
            except Exception as e:
                print(f"[DISCONNECT] Attempt 2 failed: {e}")

        if psu_inst:
            try:
                psu_inst.close()
            except Exception:
                pass
        if rm:
            try:
                rm.close()
            except Exception:
                pass

        return shutdown_ok