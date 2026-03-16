from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal ,QStringListModel
from PyQt5.QtGui import QFont, QPixmap, QIcon
import sqlite3
from core.paths import RESOURCES_DIR,SESSION_FILE
from db.db_paths import ADMIN_DB_PATH, EMPLOYEE_DB_PATH
from PyQt5.QtWidgets import QCompleter
from PyQt5.QtCore import QTimer, QStringListModel




profile_pic=str(RESOURCES_DIR / "profile.png")
id_pic=str(RESOURCES_DIR / "idcard.png")
designation_icon_path=str(RESOURCES_DIR / "briefcase.png")
hide_icon=str(RESOURCES_DIR / "hide.png")
show_icon=str(RESOURCES_DIR / "eye.png")
password_icon=str(RESOURCES_DIR / "locked.png")
# ============================================================================
# SCREEN 1: LOGIN SCREEN
# ============================================================================


class LoginScreen(QMainWindow):
    login_success = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.init_employee_db()
        self.employee_cache = {}   # name → emp_id cache
        self.setWindowTitle("HAL - Login")
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
        name_icon = QLabel()
        name_icon.setPixmap(QPixmap(profile_pic).scaled(20,20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        name_container.addWidget(name_icon)

        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self.suggest_names)
        self.name_input.setPlaceholderText("Enter Employee Name")
        self.name_input.setStyleSheet(self.input_style())
        name_container.addWidget(self.name_input)
        employee_form_layout.addLayout(name_container)
        
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.fill_employee_id)
        self.name_input.setCompleter(self.completer)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchContains)
        self.name_input.returnPressed.connect(self.handle_enter_pressed)


        # Employee ID Field
        id_container = QHBoxLayout()
        id_icon = QLabel()
        id_icon.setPixmap(QPixmap(id_pic).scaled(20,20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
        self.emp_eye_btn.setFixedSize(28,28)
        self.emp_eye_btn.setStyleSheet("border:none;")
        self.emp_eye_btn.clicked.connect(self.toggle_emp_password)
        id_container.addWidget(self.emp_eye_btn)
        employee_form_layout.addLayout(id_container)

        # Login Button
        self.employee_login_btn = QPushButton("LOGIN")
        self.employee_login_btn.setStyleSheet(self.button_style())
        self.employee_login_btn.clicked.connect(self.validate_employee_login)
        self.employee_login_btn.setDefault(True)      
        self.employee_login_btn.setAutoDefault(True)  
        employee_form_layout.addWidget(self.employee_login_btn)
        # Register Button
        self.register_btn = QPushButton("New Employee? Register")
        self.register_btn.setStyleSheet("""
            QPushButton{
                background: transparent;
                color:#1a5da8;
                border:none;
                font-weight:bold;
            }
            QPushButton:hover{
                text-decoration: underline;
            }
        """)
        self.register_btn.clicked.connect(self.open_register_screen)
        employee_form_layout.addWidget(self.register_btn)


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
        
        admin_name_icon = QLabel()
        admin_name_icon.setPixmap(QPixmap(profile_pic).scaled(20,20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
        
        designation_icon_label = QLabel()
        designation_icon_label.setPixmap(QPixmap(designation_icon_path).scaled(20,20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        designation_icon_label.setAlignment(Qt.AlignCenter)
        designation_icon_layout.addWidget(designation_icon_label)
        
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
        
        password_icon_label = QLabel()
        password_icon_label.setPixmap(QPixmap(password_icon).scaled(20,20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        password_icon_label.setAlignment(Qt.AlignCenter)
        password_icon_layout.addWidget(password_icon_label)
        
        password_row.addWidget(password_icon_container, 0, Qt.AlignVCenter)

        self.admin_password_input = QLineEdit()
        self.admin_password_input.setPlaceholderText("Enter Password")
        self.admin_password_input.setEchoMode(QLineEdit.Password)
        self.admin_password_input.setStyleSheet(self.input_style())
        self.admin_password_input.setMinimumHeight(40)
        self.admin_password_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.admin_password_input.returnPressed.connect(self.validate_admin_login)
        password_row.addWidget(self.admin_password_input, 1)
        self.admin_eye_btn = QPushButton()
        self.admin_eye_btn.setIcon(QIcon(hide_icon))
        self.admin_eye_btn.setCheckable(True)
        self.admin_eye_btn.setFixedSize(28,28)
        self.admin_eye_btn.setStyleSheet("border:none;")
        self.admin_eye_btn.clicked.connect(self.toggle_admin_password)
        password_row.addWidget(self.admin_eye_btn)
        
        admin_form_layout.addLayout(password_row)

        # ========== LOGIN BUTTON (ISOLATED) ==========
        admin_form_layout.addSpacing(8)  # Extra spacing before button
        
        self.admin_login_btn = QPushButton("LOGIN")
        self.admin_login_btn.setStyleSheet(self.button_style())
        self.admin_login_btn.clicked.connect(self.validate_admin_login)
        self.admin_login_btn.setDefault(True)      
        self.admin_login_btn.setAutoDefault(True)
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
        
    def handle_enter_pressed(self):
        text = self.name_input.text().strip()
        if text in self.employee_cache:
            self.id_input.setText(self.employee_cache[text])
            self.id_input.setFocus()


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
    def toggle_emp_password(self):
        if self.emp_eye_btn.isChecked():
            self.id_input.setEchoMode(QLineEdit.Normal)
            self.emp_eye_btn.setIcon(QIcon(show_icon))
        else:
            self.id_input.setEchoMode(QLineEdit.Password)
            self.emp_eye_btn.setIcon(QIcon(hide_icon))


    def toggle_admin_password(self):
        if self.admin_eye_btn.isChecked():
            self.admin_password_input.setEchoMode(QLineEdit.Normal)
            self.admin_eye_btn.setIcon(QIcon(show_icon))
        else:
            self.admin_password_input.setEchoMode(QLineEdit.Password)
            self.admin_eye_btn.setIcon(QIcon(hide_icon))
            
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

        # filter suggestions live
        filtered = [n for n in names if n.lower().startswith(text.lower())]

        model = QStringListModel()
        model.setStringList(filtered)
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

    def fill_employee_id(self, selected):
        # works for mouse click + keyboard enter
        if isinstance(selected, str):
            name = selected
        else:
            name = selected.data()

        if name in self.employee_cache:
            self.id_input.setText(self.employee_cache[name])
            self.id_input.setFocus()



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

        

        if row and password == row[0]:

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
    def open_register_screen(self):
        dialog = RegisterEmployee()
        if dialog.exec_() == QDialog.Accepted:
            self.suggest_names() 



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
# EMPLOYEE REGISTER SCREEN (CLEAN VERSION - NO WINDOW INSIDE WINDOW)
# ============================================================================
class RegisterEmployee(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Register Employee")
        self.setFixedSize(540, 420)
        self.setStyleSheet("background:white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 25, 35, 25)
        layout.setSpacing(15)

        # ===== TITLE =====
        title = QLabel("Register New Employee")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ===== NAME =====
        self.name = QLineEdit()
        self.name.setPlaceholderText("Employee Name")
        self.name.setMinimumHeight(38)
        layout.addWidget(self.name)

        # ===== EMP ID =====
        self.empid = QLineEdit()
        self.empid.setPlaceholderText("Employee ID (Password)")
        self.empid.setMinimumHeight(38)
        layout.addWidget(self.empid)

        # ===== CONFIRM =====
        self.confirm = QLineEdit()
        self.confirm.setPlaceholderText("Re-enter Employee ID")
        self.confirm.setMinimumHeight(38)
        layout.addWidget(self.confirm)

        # ===== INPUT STYLE =====
        for w in [self.name, self.empid, self.confirm]:
            w.setStyleSheet("""
                QLineEdit{
                    border:1px solid #dcdcdc;
                    border-radius:8px;
                    padding:8px;
                    background:#f8f9fa;
                    font-size:13px;
                }
                QLineEdit:focus{
                    border:2px solid #1a5da8;
                    background:white;
                }
            """)

        # ===== BUTTON =====
        btn = QPushButton("Create Account")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
        QPushButton{
            background:#1a5da8;
            color:white;
            border:none;
            border-radius:8px;
            font-weight:bold;
            font-size:14px;
        }
        QPushButton:hover{
            background:#154a8a;
        }
        QPushButton:pressed{
            background:#0f3860;
        }
        """)
        btn.clicked.connect(self.create_employee)
        layout.addWidget(btn)

    # =========================================================================
    def create_employee(self):
        name = self.name.text().strip()
        empid = self.empid.text().strip()
        confirm = self.confirm.text().strip()

        if not name or not empid:
            QMessageBox.warning(self, "Error", "All fields required")
            return

        if empid != confirm:
            QMessageBox.warning(self, "Error", "Employee ID mismatch")
            return

        conn = sqlite3.connect(EMPLOYEE_DB_PATH)
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO employees(name, emp_id) VALUES(?,?)",
                (name, empid)
            )
            conn.commit()
            self.show_success_popup("Employee Registered Successfully")
            self.accept()


        except:
            QMessageBox.warning(self, "Error", "Employee already exists!")

        conn.close()
    def show_success_popup(self, message):
        dlg = QDialog(self)
        dlg.setWindowTitle("Success")
        dlg.setModal(True)
        dlg.resize(420, 260)

        dlg.setStyleSheet("""
            QDialog{
                background:#f2f2f2;
                border:none;
            }
            QLabel{
                background:transparent;
                border:none;
            }
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(40,25,40,25)
        layout.setSpacing(8)

        # ✔ ICON
        icon = QLabel("✔")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Segoe UI", 42, QFont.Bold))
        icon.setStyleSheet("color:#22c55e; background:transparent; border:none;")
        layout.addWidget(icon)

        # SUCCESS TITLE
        title = QLabel("Success")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color:#1a5da8; background:transparent; border:none;")
        layout.addWidget(title)

        # MESSAGE
        msg = QLabel(message)
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        msg.setFont(QFont("Segoe UI", 12))
        msg.setStyleSheet("color:#333; background:transparent; border:none;")
        layout.addWidget(msg)

        layout.addSpacing(15)

        # OK BUTTON
        ok = QPushButton("OK")
        ok.setFixedSize(110,40)
        ok.setCursor(Qt.PointingHandCursor)
        ok.setStyleSheet("""
            QPushButton{
                background:#1a5da8;
                color:white;
                border:none;
                border-radius:8px;
                font-weight:bold;
            }
            QPushButton:hover{background:#154a8a;}
        """)
        ok.clicked.connect(dlg.accept)

        layout.addWidget(ok, alignment=Qt.AlignCenter)

        dlg.exec_()




