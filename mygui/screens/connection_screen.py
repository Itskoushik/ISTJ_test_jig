from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QFont, QColor, QPixmap, QDesktopServices
from datetime import datetime
from workers.connection_worker import ConnectionWorker
from core.logger import Logger, export_logs_to_pdf
from core.paths import RESOURCES_DIR, LOGS_DIR, LOGS_PDF_DIR





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
        
        # ===== Logout Button Top Right =====
        top_layout = QHBoxLayout()
        top_layout.addStretch()

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setFixedSize(120, 40)
        self.logout_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 2px solid #e53935;
                color: #e53935;
                border-radius: 8px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #e53935;
                color: white;
            }
        """)
        self.logout_btn.clicked.connect(self.show_logout_popup)

        top_layout.addWidget(self.logout_btn)
        layout.addLayout(top_layout)


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
        self.connection_in_progress = False
        
    def start_connection(self):

        # Prevent multiple clicks
        if getattr(self, "connection_in_progress", False):
            return

        self.connection_in_progress = True
        self.connect_btn.setEnabled(False)
        self.logout_btn.setEnabled(False)
        self.connect_btn.setText("CONNECTING...")

        self.log_text.clear()
        self.retry_count = 0

        # 🔄 Refresh detailed logs ONLY on CONNECT
        self.detailed_logger.clear()

        self.start_actual_connection()
        
    def show_logout_popup(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            from screens.login_screen import LoginScreen

            self.login_screen = LoginScreen()
            self.login_screen.show()

            # reconnect login flow
            self.login_screen.login_success.connect(self.reopen_connection_screen)

            self.close()






    def start_retry_cycle(self):
        self.connection_in_progress = True
        self.logout_btn.setEnabled(True)
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
                self.connection_in_progress = False
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
                self.failure_details["Audio Analyzer"] = {
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
        self.connection_in_progress = False
        self.connect_btn.setEnabled(True)
        self.logout_btn.setEnabled(False)
        self.connect_btn.setText("CONNECT")
        
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
        
    # ================= LOGOUT POPUP =================
    def show_success_popup(self, message):
        dlg = QDialog(self)
        dlg.setWindowTitle("Success")
        dlg.setModal(True)
        dlg.resize(420, 240)   # bigger window
        dlg.setStyleSheet("""
            QDialog{
                background:#f2f2f2;
                border:none;
            }
            QLabel{
                border:none;
                background:transparent;
            }
        """)

        main = QVBoxLayout(dlg)
        main.setContentsMargins(30,25,30,25)
        main.setSpacing(12)

        # ===== ICON =====
        icon = QLabel("✔")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Segoe UI", 34, QFont.Bold))
        icon.setStyleSheet("color:#22c55e; border:none;")
        main.addWidget(icon)

        # ===== TITLE =====
        title = QLabel("Success")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color:#1a5da8; border:none;")
        main.addWidget(title)

        # ===== MESSAGE =====
        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setFont(QFont("Segoe UI", 12))
        msg.setStyleSheet("color:#333; border:none;")
        main.addWidget(msg)

        main.addSpacing(10)

        # ===== BUTTON =====
        ok = QPushButton("OK")
        ok.setFixedHeight(40)
        ok.setCursor(Qt.PointingHandCursor)
        ok.setStyleSheet("""
            QPushButton{
                background:#1a5da8;
                color:white;
                border:none;
                border-radius:8px;
                font-weight:bold;
                padding:8px 30px;
            }
            QPushButton:hover{background:#154a8a;}
        """)
        ok.clicked.connect(dlg.accept)

        main.addWidget(ok, alignment=Qt.AlignCenter)

        dlg.exec_()





    # ===== RETURN TO LOGIN SCREEN =====
    def confirm_logout(self, dialog):
        dialog.accept()

        from screens.login_screen import LoginScreen

        self.login_screen = LoginScreen()
        self.login_screen.show()

        # 🔥 IMPORTANT: reconnect login flow again
        self.login_screen.login_success.connect(self.reopen_connection_screen)

        self.close()
        
    def reopen_connection_screen(self, name, emp_id, role):
        # reopen connection screen after logout login
        self.new_connection = ConnectionScreen(name, emp_id)
        self.new_connection.show()
        self.login_screen.close()



