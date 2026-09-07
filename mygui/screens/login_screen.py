from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal ,QStringListModel
from PyQt5.QtGui import QFont, QPixmap, QIcon
import sqlite3
from core.paths import RESOURCES_DIR,SESSION_FILE
from db.db_paths import EMPLOYEE_DB_PATH
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import QTimer, QStringListModel



import webbrowser
from PyQt5.QtCore import QPoint, QSize

APP_VERSION = "v1.0.0"
version_icon_path = str(RESOURCES_DIR / "version.png")
download_icon_path = str(RESOURCES_DIR / "download.png")
UPDATE_URL = "https://zingtec.vercel.app/"
info_icon_path = str(RESOURCES_DIR / "information.png")
profile_pic=str(RESOURCES_DIR / "profile.png")
id_pic=str(RESOURCES_DIR / "idcard.png")
designation_icon_path=str(RESOURCES_DIR / "briefcase.png")
hide_icon=str(RESOURCES_DIR / "hide.png")
show_icon=str(RESOURCES_DIR / "eye.png")
password_icon=str(RESOURCES_DIR / "locked.png")

# ── FAQ: header icon + per-category icons (change paths here ONLY) ─────────
faq_header_icon_path = str(RESOURCES_DIR / "chat.png")

FAQ_ICON_MAP = {
    "general":         str(RESOURCES_DIR / "istj.png"),
    "login":           str(RESOURCES_DIR / "user.png"),
    "device":          str(RESOURCES_DIR / "responsive.png"),
    "testing":         str(RESOURCES_DIR / "exam.png"),
    "reports":         str(RESOURCES_DIR / "clipboard.png"),
    "updates":         str(RESOURCES_DIR / "refresh.png"),
    "troubleshooting": str(RESOURCES_DIR / "troubleshoot.png"),
}

FAQ_DATA = [
    {"q": "What is ISTJ?",
     "a": "ISTJ is an Intercom System Test Jig application developed by Zing Technologies for automated testing, validation, and report generation of supported hardware devices.",
     "icon": "general"},
    {"q": "Which version of ISTJ am I using?",
     "a": "Click the ⓘ Information button in the top-right corner to view the current software version and check for updates.",
     "icon": "updates"},
    {"q": "How do I update ISTJ?",
     "a": "Open the Information panel and click Check for New Version. If an update is available, you'll be prompted to download and install it.",
     "icon": "updates"},
    {"q": "I can't log in. What should I do?",
     "a": "• Verify your Employee Name and ID.\n• Ensure you're connected to the company network (if required).\n• Contact your administrator if the issue persists.",
     "icon": "login"},
    {"q": "How do I register as a new employee?",
     "a": "Click New Employee? Register and complete the registration process.",
     "icon": "login"},
    {"q": "No devices are detected.",
     "a": "• Ensure all devices are powered on.\n• Check USB/Ethernet/Serial cable connections.\n• Verify drivers are installed.\n• Restart the application and reconnect the devices.",
     "icon": "device"},
    {"q": "Why is my Ethernet device not detected?",
     "a": "• Ensure the Ethernet cable is connected securely.\n• Verify Internet/LAN is enabled.\n• Check the network adapter status.\n• Try reconnecting the cable.",
     "icon": "device"},
    {"q": "The serial device is not connecting.",
     "a": "• Select the correct COM port.\n• Ensure no other application is using the port.\n• Verify the baud rate and communication settings.",
     "icon": "device"},
    {"q": "Can I stop a running test?",
     "a": "Yes. Click Abort Test to safely stop the current test.",
     "icon": "testing"},
    {"q": "Can I rerun only a failed test?",
     "a": "Yes. Failed tests can be rerun individually from the test summary.",
     "icon": "testing"},
    {"q": "What happens if a test fails?",
     "a": "ISTJ displays the failure reason and may provide options to Retry, Tune, Skip, or Abort depending on the test configuration.",
     "icon": "testing"},
    {"q": "Where are test reports saved?",
     "a": "Reports are automatically saved after successful completion and can be viewed from View Reports.",
     "icon": "reports"},
    {"q": "Can I export reports?",
     "a": "Yes. Reports can be exported in Excel or PDF format depending on your configuration.",
     "icon": "reports"},
    {"q": "How do I check for updates?",
     "a": "Click the ⓘ Information button and select Check for New Version.",
     "icon": "updates"},
    {"q": "Will updating remove my reports?",
     "a": "No. Updating ISTJ does not affect existing reports or configuration files.",
     "icon": "updates"},
    {"q": "The application is slow or frozen.",
     "a": "• Close unnecessary applications.\n• Restart ISTJ.\n• Restart the connected hardware if necessary.",
     "icon": "troubleshooting"},
    {"q": "How do I reconnect disconnected devices?",
     "a": "Use the Reconnect option or restart the affected device.",
     "icon": "troubleshooting"},
    {"q": "Who should I contact for support?",
     "a": "Contact your system administrator or the Zing Technologies support team.",
     "icon": "troubleshooting"},
]


class AboutPopup(QDialog):
    def __init__(self, parent, anchor_widget):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(270, 160)
        self.setStyleSheet("""
            QDialog {
                background: white;
                border: 1px solid #c9d4e3;
                border-radius: 12px;
            }
            QLabel { background: transparent; border:none; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header row
        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(QIcon(info_icon_path).pixmap(22, 22))
        header.addWidget(icon_lbl)
        title = QLabel("About ISTJ")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color:#14213d; letter-spacing:0.2px;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton{border:none;background:transparent;color:#888;}"
            "QPushButton:hover{color:#1a5da8;}"
        )
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Version row
        version_row = QHBoxLayout()
        version_row.setSpacing(10)
        tag_lbl = QLabel()
        tag_lbl.setPixmap(QIcon(version_icon_path).pixmap(32, 32))   # bigger icon
        tag_lbl.setFixedSize(32, 32)
        version_row.addWidget(tag_lbl, 0, Qt.AlignVCenter)

        version_text = QWidget()
        version_text_layout = QVBoxLayout(version_text)
        version_text_layout.setSpacing(0)
        version_text_layout.setContentsMargins(0, 0, 0, 0)

        cur_lbl = QLabel("Current Version")
        cur_lbl.setStyleSheet("""
            color:#8a94a6;
            font-size:10.5px;
            letter-spacing:0.3px;
            padding: 0px;
            margin: 0px;
        """)
        cur_lbl.setFont(QFont("Segoe UI", 8))

        ver_lbl = QLabel(APP_VERSION)
        ver_lbl.setStyleSheet("""
            color:#14213d;
            font-weight:600;
            font-size:14px;
            padding: 0px;
            margin: 0px;
        """)
        ver_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))

        version_text_layout.addWidget(cur_lbl)
        version_text_layout.addWidget(ver_lbl)

        version_row.addWidget(version_text, 0, Qt.AlignVCenter)
        version_row.addStretch()
        layout.addLayout(version_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#eee;")
        layout.addWidget(sep)

        # Download / check for update button
        download_btn = QPushButton("  Check for New Version")
        download_btn.setIcon(QIcon(download_icon_path))
        download_btn.setIconSize(QSize(16, 16))
        download_btn.setCursor(Qt.PointingHandCursor)
        download_btn.setMinimumHeight(34)
        download_btn.setToolTip(UPDATE_URL)
        download_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 8px;
                color: white;
                background: #1a5da8;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover { background:#154a8a; }
            QPushButton:pressed { background:#0f3860; }
        """)
        download_btn.clicked.connect(lambda: webbrowser.open(UPDATE_URL))
        layout.addWidget(download_btn)

    def show_at(self, widget):
        btn_top_left = widget.mapToGlobal(QPoint(0, widget.height() + 6))
        # Right-align popup's right edge with button's right edge
        x = btn_top_left.x() + widget.width() - self.width()
        y = btn_top_left.y()
        self.move(x, y)
        self.exec_()


# ============================================================================
# SCREEN 1: LOGIN SCREEN
# ============================================================================


class LoginScreen(QMainWindow):
    login_success = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.init_employee_db()
        self.employee_cache = {}   # name → emp_id cache
        self.setWindowTitle("ISTJ - Login")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
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
            }
            QPushButton:hover {
                background-color: #d0e8f2;
            }
        """)
        # border-right: none;
        
        self.employee_tab_btn.clicked.connect(self.show_employee_login)
        tab_buttons_layout.addWidget(self.employee_tab_btn)

        # self.admin_tab_btn = QPushButton("Admin Login")
        # self.admin_tab_btn.setMinimumHeight(40)
        # self.admin_tab_btn.setFont(QFont("Arial", 10, QFont.Bold))
        # self.admin_tab_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #f5f5f5;
        #         color: #666666;
        #         border: 1px solid #d0d0d0;
        #         border-radius: 0px;
        #         padding: 10px;
        #     }
        #     QPushButton:hover {
        #         background-color: #eeeeee;
        #     }
        # """)
        # self.admin_tab_btn.clicked.connect(self.show_admin_login)
        # tab_buttons_layout.addWidget(self.admin_tab_btn)

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
        employee_form_layout.setSpacing(0)

        # Internal stacked widget: 0=login, 1=register
        self.login_stack = QStackedWidget()
        employee_form_layout.addWidget(self.login_stack)

        # ── PAGE 0: LOGIN ──────────────────────────────────────────────
        login_page = QWidget()
        login_page_layout = QVBoxLayout(login_page)
        login_page_layout.setContentsMargins(0, 0, 0, 0)
        login_page_layout.setSpacing(20)

        employee_title_label = QLabel("Employee Login")
        employee_title_label.setFont(QFont("Arial", 24, QFont.Bold))
        employee_title_label.setAlignment(Qt.AlignCenter)
        employee_title_label.setStyleSheet("color: #1a5da8; background-color: transparent;")
        login_page_layout.addWidget(employee_title_label)

        name_container = QHBoxLayout()
        name_icon = QLabel()
        name_icon.setPixmap(QPixmap(profile_pic).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        name_container.addWidget(name_icon)
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self.suggest_names)
        self.name_input.setPlaceholderText("Enter Employee Name")
        self.name_input.setStyleSheet(self.input_style())
        name_container.addWidget(self.name_input)
        login_page_layout.addLayout(name_container)

        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.on_completer_activated)
        self.name_input.setCompleter(self.completer)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchContains)
        self.name_input.returnPressed.connect(self.handle_enter_pressed)

        id_container = QHBoxLayout()
        id_icon = QLabel()
        id_icon.setPixmap(QPixmap(id_pic).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        id_container.addWidget(id_icon)
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Employee ID")
        self.id_input.setEchoMode(QLineEdit.Password)
        self.id_input.setStyleSheet(self.input_style())
        self.id_input.returnPressed.connect(self.validate_employee_login)
        id_container.addWidget(self.id_input)
        self.emp_eye_btn = QPushButton()
        self.emp_eye_btn.setIcon(QIcon(hide_icon))
        self.emp_eye_btn.setCheckable(True)
        self.emp_eye_btn.setFixedSize(28, 28)
        self.emp_eye_btn.setStyleSheet("border:none;")
        self.emp_eye_btn.clicked.connect(self.toggle_emp_password)
        id_container.addWidget(self.emp_eye_btn)
        login_page_layout.addLayout(id_container)

        self.employee_login_btn = QPushButton("LOGIN")
        self.employee_login_btn.setStyleSheet(self.button_style())
        self.employee_login_btn.clicked.connect(self.validate_employee_login)
        self.employee_login_btn.setDefault(True)
        self.employee_login_btn.setAutoDefault(True)
        login_page_layout.addWidget(self.employee_login_btn)

        self.register_btn = QPushButton("New Employee? Register")
        self.register_btn.setStyleSheet("""
            QPushButton { background: transparent; color:#1a5da8; border:none; font-weight:bold; }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.register_btn.clicked.connect(self.show_register_inline)
        login_page_layout.addWidget(self.register_btn)

        faq_help_layout = QHBoxLayout()
        faq_help_layout.setAlignment(Qt.AlignCenter)
        faq_btn = QPushButton("FAQ")
        faq_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #888888; border: none; font-size: 11px; }
            QPushButton:hover { text-decoration: underline; color: #1a5da8; }
        """)
        faq_btn.clicked.connect(lambda: self.show_faq())
        separator_label = QLabel("|")
        separator_label.setStyleSheet("color: #cccccc;")
        help_btn = QPushButton("HELP")
        help_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #888888; border: none; font-size: 11px; }
            QPushButton:hover { text-decoration: underline; color: #1a5da8; }
        """)
        help_btn.clicked.connect(lambda: self.show_help())
        faq_help_layout.addWidget(faq_btn)
        faq_help_layout.addWidget(separator_label)
        faq_help_layout.addWidget(help_btn)
        login_page_layout.addLayout(faq_help_layout)
        login_page_layout.addStretch()

        self.login_stack.addWidget(login_page)   # index 0

        # ── PAGE 1: REGISTER ───────────────────────────────────────────
        reg_page = QWidget()
        reg_page_layout = QVBoxLayout(reg_page)
        reg_page_layout.setContentsMargins(0, 8, 0, 0)
        reg_page_layout.setSpacing(10)

        reg_title = QLabel("Create Employee Account")
        reg_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        reg_title.setAlignment(Qt.AlignCenter)
        reg_title.setStyleSheet("color:#1a5da8; background:transparent;")
        reg_page_layout.addWidget(reg_title)

        reg_subtitle = QLabel("Fill in the details below to register")
        reg_subtitle.setAlignment(Qt.AlignCenter)
        reg_subtitle.setStyleSheet("color:#9aafcc; background:transparent; font-size:11px;")
        reg_page_layout.addWidget(reg_subtitle)

        # helper for inline register fields
        def reg_label(text):
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
            lbl.setStyleSheet("color:#5a7aa8; background:transparent; border:none;")
            return lbl

        field_frame_style = """
            QFrame {
                border: 1.5px solid #dde4f0;
                border-radius: 10px;
                background: #f6f9ff;
            }
        """
        inner_field_style = """
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 13px;
                color: #222;
            }
            QLineEdit::placeholder { color: #b0bdd4; }
        """
        eye_style = "QPushButton { border:none; background:transparent; padding:2px; }"

        def make_reg_field(placeholder, is_password=False):
            frame = QFrame()
            frame.setStyleSheet(field_frame_style)
            h = QHBoxLayout(frame)
            h.setContentsMargins(12, 0, 8, 0)
            h.setSpacing(4)
            fld = QLineEdit()
            fld.setPlaceholderText(placeholder)
            fld.setFrame(False)
            fld.setMinimumHeight(42)
            fld.setStyleSheet(inner_field_style)
            if is_password:
                fld.setEchoMode(QLineEdit.Password)
            h.addWidget(fld, 1)
            eye = None
            if is_password:
                eye = QPushButton()
                eye.setIcon(QIcon(hide_icon))
                eye.setCheckable(True)
                eye.setFixedSize(26, 26)
                eye.setStyleSheet(eye_style)
                eye.setCursor(Qt.PointingHandCursor)
                def _toggle(checked, f=fld, b=eye):
                    if checked:
                        f.setEchoMode(QLineEdit.Normal); b.setIcon(QIcon(show_icon))
                    else:
                        f.setEchoMode(QLineEdit.Password); b.setIcon(QIcon(hide_icon))
                eye.clicked.connect(_toggle)
                h.addWidget(eye)
            return fld, frame

        reg_page_layout.addWidget(reg_label("EMPLOYEE NAME"))
        self.reg_name, reg_name_frame = make_reg_field("Full name as per records")
        reg_page_layout.addWidget(reg_name_frame)

        reg_page_layout.addWidget(reg_label("EMPLOYEE ID  (used as password)"))
        self.reg_empid, reg_empid_frame = make_reg_field("Create your Employee ID", is_password=True)
        reg_page_layout.addWidget(reg_empid_frame)

        reg_page_layout.addWidget(reg_label("CONFIRM EMPLOYEE ID"))
        self.reg_confirm, reg_confirm_frame = make_reg_field("Re-enter Employee ID", is_password=True)
        reg_page_layout.addWidget(reg_confirm_frame)

        self.reg_name.returnPressed.connect(lambda: self.reg_empid.setFocus())
        self.reg_empid.returnPressed.connect(lambda: self.reg_confirm.setFocus())
        self.reg_confirm.returnPressed.connect(self.create_employee_inline)

        self.create_acc_btn = QPushButton("  Create Account")
        self.create_acc_btn.setMinimumHeight(46)
        self.create_acc_btn.setCursor(Qt.PointingHandCursor)
        self.create_acc_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.create_acc_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1a5da8, stop:1 #3b9ee8);
                color: white; border: none; border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #154a8a, stop:1 #2f87cc);
            }
            QPushButton:pressed { background: #0f3860; }
        """)
        self.create_acc_btn.clicked.connect(self.create_employee_inline)
        reg_page_layout.addWidget(self.create_acc_btn)

        back_to_login_btn = QPushButton("← Back to Login")
        back_to_login_btn.setStyleSheet("""
            QPushButton { background:transparent; color:#1a5da8; border:none; font-weight:bold; }
            QPushButton:hover { text-decoration: underline; }
        """)
        back_to_login_btn.clicked.connect(self.show_login_inline)
        reg_page_layout.addWidget(back_to_login_btn, alignment=Qt.AlignCenter)
        reg_page_layout.addStretch()

        self.login_stack.addWidget(reg_page)   # index 1
        stacked_layout.addWidget(self.employee_form)

        tab_layout.addWidget(self.stacked_widget, 1)
        layout.addWidget(self.tab_widget, 1)

        # Footer
        footer_label = QLabel("© 2026 Zing Technologies. All rights reserved.")
        footer_label.setFont(QFont("Arial", 8))
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #999999; background-color: transparent;")
        layout.addWidget(footer_label)

        # Show employee login by default
        self.show_employee_login()
        self.create_info_button()
    
    def create_info_button(self):
        self.info_btn = QPushButton(self)
        self.info_btn.setIcon(QIcon(info_icon_path))
        self.info_btn.setIconSize(QSize(30, 30))      # was 18 — now nearly fills the 32px button
        self.info_btn.setFixedSize(32, 32)
        self.info_btn.setCursor(Qt.PointingHandCursor)
        self.info_btn.setToolTip("About ISTJ")
        self.info_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(26, 93, 168, 0.12);
                border-radius: 16px;
            }
            QPushButton:pressed {
                background: rgba(26, 93, 168, 0.22);
                border-radius: 16px;
            }
        """)
        self.info_btn.clicked.connect(self.show_about_popup)
        self.info_btn.move(self.width() - 48, 16)
        self.info_btn.raise_()

    def show_about_popup(self):
        popup = AboutPopup(self, self.info_btn)
        popup.show_at(self.info_btn)
    
    # ================= EMPLOYEE DATABASE INIT =================
    def init_employee_db(self):
        conn = sqlite3.connect(EMPLOYEE_DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                emp_id TEXT
            )
        """)

        conn.commit()
        conn.close()
        
    def show_register_inline(self):
        self.reg_name.clear()
        self.reg_empid.clear()
        self.reg_confirm.clear()
        self.setFixedSize(550, 660)
        self.login_stack.setCurrentIndex(1)
        self.reg_name.setFocus()

    def show_login_inline(self):
        self.setFixedSize(550, 600) 
        self.login_stack.setCurrentIndex(0)
        self.name_input.setFocus()

    def create_employee_inline(self):
        name    = self.reg_name.text().strip()
        empid   = self.reg_empid.text().strip()
        confirm = self.reg_confirm.text().strip()

        if not name or not empid:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return
        if empid != confirm:
            QMessageBox.warning(self, "Error", "Employee ID does not match.")
            return

        conn = sqlite3.connect(EMPLOYEE_DB_PATH)
        cur  = conn.cursor()
        try:
            cur.execute("INSERT INTO employees(name, emp_id) VALUES(?,?)", (name, empid))
            conn.commit()
            self.suggest_names()   # refresh autocomplete cache

            # success banner then auto-switch back
            dlg = QDialog(self)
            dlg.setWindowTitle("Success")
            dlg.setFixedSize(360, 220)
            dlg.setStyleSheet("QDialog{background:#f0f6ff;} QLabel{background:transparent;border:none;}")
            v = QVBoxLayout(dlg)
            v.setContentsMargins(36, 24, 36, 24)
            v.setSpacing(6)
            ck = QLabel("✔")
            ck.setAlignment(Qt.AlignCenter)
            ck.setFont(QFont("Segoe UI", 36, QFont.Bold))
            ck.setStyleSheet("color:#22c55e;")
            v.addWidget(ck)
            t = QLabel("Employee Registered!")
            t.setAlignment(Qt.AlignCenter)
            t.setFont(QFont("Segoe UI", 15, QFont.Bold))
            t.setStyleSheet("color:#1a5da8;")
            v.addWidget(t)
            m = QLabel(f"{name} has been registered successfully.")
            m.setWordWrap(True)
            m.setAlignment(Qt.AlignCenter)
            m.setFont(QFont("Segoe UI", 10))
            m.setStyleSheet("color:#444;")
            v.addWidget(m)
            v.addSpacing(10)
            ok = QPushButton("Go to Login")
            ok.setFixedSize(130, 38)
            ok.setCursor(Qt.PointingHandCursor)
            ok.setFont(QFont("Segoe UI", 10, QFont.Bold))
            ok.setStyleSheet("""
                QPushButton{background:#1a5da8;color:white;border:none;border-radius:8px;}
                QPushButton:hover{background:#154a8a;}
            """)
            ok.clicked.connect(dlg.accept)
            v.addWidget(ok, alignment=Qt.AlignCenter)
            dlg.exec_()

            # pre-fill name and switch back
            self.name_input.setText(name)
            self.id_input.clear()
            self.show_login_inline()

        except Exception:
            QMessageBox.warning(self, "Error", "An employee with this name already exists.")
        finally:
            conn.close()
    
    def show_faq(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("FAQ")
        dlg.setMinimumSize(600, 560)
        dlg.resize(700, 620)
        dlg.setStyleSheet("""
            QDialog { background-color: #f4f6fb; }
            QLabel { background: transparent; border: none; }
        """)

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Content ──────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 0)
        content_layout.setSpacing(16)

        title_row = QHBoxLayout()
        title_row.setSpacing(14)
        bubble = QLabel("?")
        bubble.setFixedSize(48, 48)
        bubble.setAlignment(Qt.AlignCenter)
        bubble.setFont(QFont("Segoe UI", 18, QFont.Bold))
        bubble.setStyleSheet("background:#1a5da8; color:white; border-radius:12px;")
        title_row.addWidget(bubble)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        main_title = QLabel("Frequently Asked Questions")
        main_title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        main_title.setStyleSheet("color:#14213d;")
        title_col.addWidget(main_title)
        underline = QFrame()
        underline.setFixedSize(60, 3)
        underline.setStyleSheet("background:#1a5da8; border-radius:2px;")
        title_col.addWidget(underline)
        title_row.addLayout(title_col)
        title_row.addStretch()
        content_layout.addLayout(title_row)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border:none; }
            QScrollBar:vertical {
                width: 9px;
                background: transparent;
                margin: 2px 0px 2px 0px;
            }
            QScrollBar::handle:vertical {
                background: #c8d4e0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #9fb3d1; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        cards_container = QWidget()
        cards_container.setStyleSheet("background:transparent;")
        cards_holder = QVBoxLayout(cards_container)
        cards_holder.setContentsMargins(0, 0, 8, 16)
        cards_holder.setSpacing(14)

        scroll_area.setWidget(cards_container)
        content_layout.addWidget(scroll_area, 1)

        outer.addWidget(content, 1)

        # ── Footer: just Close ─────────────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet("background:#eef1f8; border-top:1px solid #e5e7eb;")
        footer.setFixedHeight(64)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        footer_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setMinimumHeight(40)
        close_btn.setMinimumWidth(140)
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1a5da8, stop:1 #3b9ee8);
                color:white; border:none; border-radius:8px; font-weight:bold;
            }
            QPushButton:hover { background:#154a8a; }
        """)
        close_btn.clicked.connect(dlg.accept)
        footer_layout.addWidget(close_btn)
        footer_layout.addStretch()

        outer.addWidget(footer)

        # ── Render all FAQ cards into the scrollable list ─────────────────
        def make_card(index, item):
            card = QFrame()
            card.setStyleSheet("""
                QFrame { background:#ffffff; border:none; border-radius:10px; }
            """)
            row = QHBoxLayout(card)
            row.setContentsMargins(18, 16, 18, 16)
            row.setSpacing(16)

            num_lbl = QLabel(str(index + 1))
            num_lbl.setFixedSize(34, 34)
            num_lbl.setAlignment(Qt.AlignCenter)
            num_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
            num_lbl.setStyleSheet("background:#1a5da8; color:white; border-radius:17px;")
            row.addWidget(num_lbl, 0, Qt.AlignTop)

            text_col = QVBoxLayout()
            text_col.setSpacing(4)
            q_lbl = QLabel(f"Q: {item['q']}")
            q_lbl.setWordWrap(True)
            q_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            q_lbl.setStyleSheet("color:#14213d;")
            text_col.addWidget(q_lbl)

            a_lbl = QLabel(f"A: {item['a']}")
            a_lbl.setWordWrap(True)
            a_lbl.setFont(QFont("Segoe UI", 10))
            a_lbl.setStyleSheet("color:#5a6b8c;")
            text_col.addWidget(a_lbl)
            row.addLayout(text_col, 1)

            icon_path = FAQ_ICON_MAP.get(item["icon"], FAQ_ICON_MAP["general"])
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(40, 40)
            icon_lbl.setPixmap(QIcon(icon_path).pixmap(26, 26))
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet("border:none; border-radius:20px; background:#f4f8ff;")
            row.addWidget(icon_lbl, 0, Qt.AlignTop)

            return card

        for i, item in enumerate(FAQ_DATA):
            cards_holder.addWidget(make_card(i, item))
        cards_holder.addStretch()

        dlg.exec_()

    def show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Help")
        dlg.setMinimumSize(460, 480)
        dlg.resize(480, 520)
        dlg.setStyleSheet("""
            QDialog { background-color: #f4f6fb; }
            QLabel { background: transparent; border: none; }
        """)

        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Content ──────────────────────────────────────────────────────
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(36, 32, 36, 0)
        content_layout.setSpacing(20)

        title_row = QHBoxLayout()
        title_row.setSpacing(20)

        badge = QLabel()
        badge.setFixedSize(96, 96)
        badge.setAlignment(Qt.AlignCenter)
        badge.setPixmap(QIcon(str(RESOURCES_DIR / "helpdesk.png")).pixmap(52, 52))
        badge.setStyleSheet("background:#eaf1fc; border-radius:48px;")
        title_row.addWidget(badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(6)
        main_title = QLabel("Help & Support")
        main_title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        main_title.setStyleSheet("color:#14213d;")
        title_col.addWidget(main_title)

        underline = QFrame()
        underline.setFixedSize(60, 3)
        underline.setStyleSheet("background:#1a5da8; border-radius:2px;")
        title_col.addWidget(underline)

        subtitle = QLabel("For login issues or any other assistance,\nplease contact your system administrator.")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color:#5a6b8c;")
        title_col.addWidget(subtitle)

        title_row.addLayout(title_col)
        title_row.addStretch()
        content_layout.addLayout(title_row)

        # ── Info card ────────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet("QFrame { background:#ffffff; border:none; border-radius:14px; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(0)

        def make_row(icon_file, label_text, value_text, is_link=False):
            row = QHBoxLayout()
            row.setContentsMargins(0, 14, 0, 14)
            row.setSpacing(16)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(48, 48)
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setPixmap(QIcon(str(RESOURCES_DIR / icon_file)).pixmap(24, 24))
            icon_lbl.setStyleSheet("background:#eaf1fc; border-radius:24px;")
            row.addWidget(icon_lbl, 0, Qt.AlignTop)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
            lbl.setStyleSheet("color:#14213d;")
            text_col.addWidget(lbl)

            val = QLabel(value_text)
            val.setFont(QFont("Segoe UI", 11))
            val.setStyleSheet(f"color:{'#1a5da8' if is_link else '#5a6b8c'};")
            text_col.addWidget(val)

            row.addLayout(text_col, 1)
            return row

        card_layout.addLayout(make_row("email.png", "Support Email", "sales@zingtec.com", is_link=True))

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background:#e5e7eb;")
        sep1.setFixedHeight(1)
        card_layout.addWidget(sep1)

        card_layout.addLayout(make_row("phone-call.png", "Phone", "080-25236609", is_link=True))

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background:#e5e7eb;")
        sep2.setFixedHeight(1)
        card_layout.addWidget(sep2)

        card_layout.addLayout(make_row("building.png", "About", "ISTJ - Powered by Zing Technologies"))

        content_layout.addWidget(card)
        content_layout.addStretch()

        outer.addWidget(content, 1)

        # ── Footer: centered Close ────────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet("background:#eef1f8; border-top:1px solid #e5e7eb;")
        footer.setFixedHeight(76)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 16, 20, 16)
        footer_layout.addStretch()

        close_btn = QPushButton(" Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setMinimumHeight(44)
        close_btn.setMinimumWidth(160)
        close_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1a5da8, stop:1 #3b9ee8);
                color:white; border:none; border-radius:10px;
            }
            QPushButton:hover { background:#154a8a; }
        """)
        close_btn.clicked.connect(dlg.accept)
        footer_layout.addWidget(close_btn)
        footer_layout.addStretch()

        outer.addWidget(footer)

        dlg.exec_()
        
    def handle_enter_pressed(self):
        text = self.name_input.text().strip()
        # If popup is open, let Qt handle the selection (on_completer_activated fires)
        if self.completer.popup() and self.completer.popup().isVisible():
            return
        if text in self.employee_cache:
            self.id_input.setText(self.employee_cache[text])
        self.id_input.setFocus()

        
    def show_employee_login(self):
        """Show employee login form"""
        self.employee_form.show()
        self.name_input.setFocus()

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
    def toggle_emp_password(self):
        if self.emp_eye_btn.isChecked():
            self.id_input.setEchoMode(QLineEdit.Normal)
            self.emp_eye_btn.setIcon(QIcon(show_icon))
        else:
            self.id_input.setEchoMode(QLineEdit.Password)
            self.emp_eye_btn.setIcon(QIcon(hide_icon))
            
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
    def suggest_names(self):
        text = self.name_input.text().strip()

        conn = sqlite3.connect(EMPLOYEE_DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT name, emp_id FROM employees")
        rows = cur.fetchall()
        conn.close()

        names = []
        self.employee_cache.clear()

        for name, empid in rows:
            names.append(name)
            self.employee_cache[name] = empid

        model = QStringListModel(names)
        self.completer.setModel(model)



    def validate_employee_login(self):
        name = self.name_input.text().strip()
        emp_id = self.id_input.text().strip()

        if not name or not emp_id:
            self.show_error_popup("Enter Name and ID")
            return

        conn = sqlite3.connect(EMPLOYEE_DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM employees WHERE name=? AND emp_id=?",
            (name, emp_id)
        )
        row = cur.fetchone()
        conn.close()

        if row:
            # ✅ WRITE SESSION FILE (OVERWRITE EVERY LOGIN)
            with open(SESSION_FILE, "w") as f:
                f.write(f"{name}\n")
                f.write(f"{emp_id}\n")
                f.write("Employee\n")
            self.login_success.emit(name, emp_id, "Employee")
        else:
            self.show_error_popup("Employee not registered. Please register first.")

    def on_completer_activated(self, selected_name: str):
        """Fires on click OR Enter/arrow-key selection from the popup."""
        self.name_input.blockSignals(True)
        self.name_input.setText(selected_name)
        self.name_input.blockSignals(False)

        empid = self.employee_cache.get(selected_name, "")
        self.id_input.setText(empid)
        self.id_input.setFocus()

    def show_error_popup(self, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Login Error")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.exec_()
 
# ============================================================================
# EMPLOYEE REGISTER SCREEN (CLEAN VERSION - NO WINDOW INSIDE WINDOW)
# ============================================================================
class RegisterEmployee(QDialog):
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Register Employee")
        self.setFixedSize(480, 520)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f0f6ff, stop:1 #ffffff);
            }
        """)
 
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
 
        # ── Top accent bar ─────────────────────────────────────────────────
        accent = QFrame()
        accent.setFixedHeight(6)
        accent.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                             "stop:0 #1a5da8, stop:1 #3b9ee8); border:none;")
        outer.addWidget(accent)
 
        # ── Card ───────────────────────────────────────────────────────────
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 16px;
            }
        """)
        card_shadow_wrapper = QVBoxLayout()
        card_shadow_wrapper.setContentsMargins(24, 20, 24, 24)
        card_shadow_wrapper.addWidget(card)
        outer.addLayout(card_shadow_wrapper)
 
        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(0)
 
        # ── Icon + Title ───────────────────────────────────────────────────
        icon_lbl = QLabel("👤")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 30))
        icon_lbl.setStyleSheet("background:transparent; border:none; color:#1a5da8;")
        layout.addWidget(icon_lbl)
 
        layout.addSpacing(4)
 
        title = QLabel("Create Employee Account")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#1a5da8; background:transparent; border:none;")
        layout.addWidget(title)
 
        subtitle = QLabel("Fill in the details below to register")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color:#9aafcc; background:transparent; border:none;")
        layout.addWidget(subtitle)
 
        layout.addSpacing(22)
 
        # ── Shared field style ─────────────────────────────────────────────
        field_style = """
            QLineEdit {
                border: 1.5px solid #dde4f0;
                border-radius: 10px;
                padding: 10px 14px;
                background: #f6f9ff;
                font-size: 13px;
                color: #222;
            }
            QLineEdit:focus {
                border: 2px solid #1a5da8;
                background: #ffffff;
            }
            QLineEdit::placeholder { color: #b0bdd4; }
        """
        eye_style = """
            QPushButton {
                border: none;
                background: transparent;
                padding: 2px;
            }
            QPushButton:hover { opacity: 0.7; }
        """
 
        def make_label(text):
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
            lbl.setStyleSheet("color:#5a7aa8; background:transparent; border:none;")
            return lbl
 
        def make_field(placeholder, is_password=False):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(0)
 
            container = QFrame()
            container.setStyleSheet("""
                QFrame {
                    border: 1.5px solid #dde4f0;
                    border-radius: 10px;
                    background: #f6f9ff;
                }
                QFrame:focus-within {
                    border: 2px solid #1a5da8;
                    background: white;
                }
            """)
            h = QHBoxLayout(container)
            h.setContentsMargins(12, 0, 8, 0)
            h.setSpacing(4)
 
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setFrame(False)
            field.setMinimumHeight(42)
            field.setStyleSheet("""
                QLineEdit {
                    border: none;
                    background: transparent;
                    font-size: 13px;
                    color: #222;
                    padding: 0px;
                }
                QLineEdit::placeholder { color: #b0bdd4; }
            """)
            if is_password:
                field.setEchoMode(QLineEdit.Password)
            h.addWidget(field, 1)
 
            eye_btn = None
            if is_password:
                eye_btn = QPushButton()
                eye_btn.setIcon(QIcon(hide_icon))
                eye_btn.setCheckable(True)
                eye_btn.setFixedSize(26, 26)
                eye_btn.setStyleSheet(eye_style)
                eye_btn.setCursor(Qt.PointingHandCursor)
 
                def _toggle(checked, f=field, b=eye_btn):
                    if checked:
                        f.setEchoMode(QLineEdit.Normal)
                        b.setIcon(QIcon(show_icon))
                    else:
                        f.setEchoMode(QLineEdit.Password)
                        b.setIcon(QIcon(hide_icon))
 
                eye_btn.clicked.connect(_toggle)
                h.addWidget(eye_btn)
 
            row.addWidget(container)
            return field, eye_btn, row
 
        # ── Name field ─────────────────────────────────────────────────────
        layout.addWidget(make_label("EMPLOYEE NAME"))
        layout.addSpacing(5)
 
        name_container = QFrame()
        name_container.setStyleSheet("""
            QFrame {
                border: 1.5px solid #dde4f0;
                border-radius: 10px;
                background: #f6f9ff;
            }
        """)
        name_h = QHBoxLayout(name_container)
        name_h.setContentsMargins(12, 0, 8, 0)
        name_h.setSpacing(4)
 
        self.name = QLineEdit()
        self.name.setPlaceholderText("Full name as per records")
        self.name.setFrame(False)
        self.name.setMinimumHeight(42)
        self.name.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 13px;
                color: #222;
            }
            QLineEdit::placeholder { color: #b0bdd4; }
        """)
        name_h.addWidget(self.name)
        layout.addWidget(name_container)
 
        layout.addSpacing(14)
 
        # ── Employee ID (password) ─────────────────────────────────────────
        layout.addWidget(make_label("EMPLOYEE ID  (used as password)"))
        layout.addSpacing(5)
        self.empid, _e1, empid_row = make_field("Create your Employee ID", is_password=True)
        layout.addLayout(empid_row)
 
        layout.addSpacing(14)
 
        # ── Confirm Employee ID ────────────────────────────────────────────
        layout.addWidget(make_label("CONFIRM EMPLOYEE ID"))
        layout.addSpacing(5)
        self.confirm, _e2, confirm_row = make_field("Re-enter Employee ID", is_password=True)
        layout.addLayout(confirm_row)

        self.name.returnPressed.connect(lambda: self.empid.setFocus())
        self.empid.returnPressed.connect(lambda: self.confirm.setFocus())
        self.confirm.returnPressed.connect(self.create_employee)
 
        layout.addSpacing(26)
 
        # ── Register button ────────────────────────────────────────────────
        self.btn = QPushButton("  Create Account")
        self.btn.setMinimumHeight(46)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1a5da8, stop:1 #3b9ee8);
                color: white;
                border: none;
                border-radius: 10px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #154a8a, stop:1 #2f87cc);
            }
            QPushButton:pressed {
                background: #0f3860;
            }
        """)
        self.btn.clicked.connect(self.create_employee)
        layout.addWidget(self.btn)
 
        layout.addStretch()
 
    # ── Logic (unchanged) ──────────────────────────────────────────────────
    def create_employee(self):
        import sqlite3
        from db.db_paths import EMPLOYEE_DB_PATH
 
        name    = self.name.text().strip()
        empid   = self.empid.text().strip()
        confirm = self.confirm.text().strip()
 
        if not name or not empid:
            QMessageBox.warning(self, "Error", "All fields are required.")
            return
 
        if empid != confirm:
            QMessageBox.warning(self, "Error", "Employee ID does not match.")
            return
 
        conn = sqlite3.connect(EMPLOYEE_DB_PATH)
        cur  = conn.cursor()
 
        try:
            cur.execute(
                "INSERT INTO employees(name, emp_id) VALUES(?,?)",
                (name, empid)
            )
            conn.commit()
            self.show_success_popup("Employee Registered Successfully!")
            self.accept()
        except Exception:
            QMessageBox.warning(self, "Error", "An employee with this name already exists.")
        finally:
            conn.close()
 
    def show_success_popup(self, message):
        dlg = QDialog(self)
        dlg.setWindowTitle("Success")
        dlg.setModal(True)
        dlg.setFixedSize(380, 240)
        dlg.setStyleSheet("QDialog { background:#f0f6ff; } QLabel { background:transparent; border:none; }")
 
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(40, 28, 40, 28)
        layout.setSpacing(6)
 
        icon = QLabel("✔")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Segoe UI", 38, QFont.Bold))
        icon.setStyleSheet("color:#22c55e;")
        layout.addWidget(icon)
 
        title = QLabel("Success")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color:#1a5da8;")
        layout.addWidget(title)
 
        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setFont(QFont("Segoe UI", 11))
        msg.setStyleSheet("color:#444;")
        layout.addWidget(msg)
 
        layout.addSpacing(12)
 
        ok = QPushButton("OK")
        ok.setFixedSize(110, 38)
        ok.setCursor(Qt.PointingHandCursor)
        ok.setFont(QFont("Segoe UI", 10, QFont.Bold))
        ok.setStyleSheet("""
            QPushButton { background:#1a5da8; color:white; border:none;
                          border-radius:8px; }
            QPushButton:hover { background:#154a8a; }
        """)
        ok.clicked.connect(dlg.accept)
        layout.addWidget(ok, alignment=Qt.AlignCenter)
 
        dlg.exec_()




