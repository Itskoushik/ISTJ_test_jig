import sqlite3
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QHBoxLayout, QDialog
)


from PyQt5.QtCore import Qt
from pathlib import Path
from PyQt5.QtCore import pyqtSignal

BASE_DIR = Path(__file__).parent
from db.db_paths import ADMIN_DB_PATH


class MetaAdminDashboard(QMainWindow):
    restart_login = pyqtSignal()

    def __init__(self, admin_name, mode, real_designation):
        

        super().__init__()
        self.admin_name = admin_name
        self.mode = mode  # META_ADMIN_SELF or META_ADMIN_MASTER
        self.real_designation = real_designation


        self.setWindowTitle("HAL – Meta Admin Dashboard")
        self.setFixedSize(700, 520)


        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        if self.mode == "META_ADMIN_SELF":
            self._build_self_reset_ui(layout)
        else:
            self._build_master_ui(layout)

    # ---------------- SELF RESET ----------------
    def _build_self_reset_ui(self, layout):
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtWidgets import QFrame

        designation = self.real_designation

        # ---------- HAL LOGO ----------
        logo_label = QLabel()
        logo_path = BASE_DIR / "resourses" / "hal_logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaledToWidth(140, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)

        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        layout.addSpacing(10)

        # ---------- CARD CONTAINER ----------
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #d0dce8;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(18)

        # ---------- GREETING ----------
        title = QLabel(f"Hi {self.admin_name}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #1a4fa3;
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        card_layout.addWidget(title)

        # ---------- DESIGNATION ----------
        role = QLabel(f"Designation: {designation}")
        role.setAlignment(Qt.AlignCenter)
        role.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                padding: 0px;
                font-size: 14px;
                color: #555555;
            }
        """)
        card_layout.addWidget(role)

        card_layout.addSpacing(10)

        # ---------- QUESTION ----------
        question = QLabel("Do you want to reset your password?")
        question.setAlignment(Qt.AlignCenter)
        question.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                padding: 0px;
                font-size: 14px;
                color: #333333;
            }
        """)
        card_layout.addWidget(question)

        card_layout.addSpacing(15)

        # ---------- BUTTONS ----------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        yes_btn = QPushButton("YES")
        yes_btn.setFixedHeight(38)
        yes_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
        """)
        yes_btn.clicked.connect(self._show_reset_fields)

        no_btn = QPushButton("NO")
        no_btn.setFixedHeight(38)
        no_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: #333;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d5d5d5;
            }
        """)
        no_btn.clicked.connect(self._logout)

        btn_row.addWidget(yes_btn)
        btn_row.addWidget(no_btn)

        card_layout.addLayout(btn_row)

        layout.addWidget(card, alignment=Qt.AlignCenter)


    

    def _show_reset_fields(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Reset Password")
        dlg.setModal(True)
        dlg.setFixedSize(360, 260)

        v = QVBoxLayout(dlg)
        v.setSpacing(15)
        v.setContentsMargins(25, 25, 25, 25)

        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.Password)
        self.new_pwd.setPlaceholderText("New Password")

        self.conf_pwd = QLineEdit()
        self.conf_pwd.setEchoMode(QLineEdit.Password)
        self.conf_pwd.setPlaceholderText("Confirm Password")

        reset = QPushButton("RESET")
        reset.clicked.connect(lambda: self._reset_self_password(dlg))

        v.addWidget(self._add_eye_toggle(self.new_pwd))
        v.addWidget(self._add_eye_toggle(self.conf_pwd))
        v.addSpacing(10)
        v.addWidget(reset)

        dlg.exec_()

    def closeEvent(self, event):
    # Prevent accidental app exit
        event.ignore()
        self.hide()

    def _reset_self_password(self, dlg):
        if self.new_pwd.text() != self.conf_pwd.text():
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        conn = sqlite3.connect(ADMIN_DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO admins VALUES (?, ?, ?)",
            (
                self.admin_name,
                self.real_designation,
                self.new_pwd.text()
            )
        )

        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(FULL);")
        conn.close()

        QMessageBox.information(self, "Success", "Password reset successful")

        dlg.accept()   # ✅ close dialog properly

        self.restart_login.emit()
        self.close()





        
    def _get_real_designation(self):
        conn = sqlite3.connect(ADMIN_DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT designation FROM admins WHERE admin_name=? AND designation!='_default'",
            (self.admin_name,)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return row[0]

        QMessageBox.critical(
            self,
            "Error",
            "Admin designation not found. Please contact Master Meta Admin."
        )
        raise RuntimeError("Designation missing for admin")


    def _add_eye_toggle(self, line_edit):
        toggle_btn = QPushButton("👁")
        toggle_btn.setFixedWidth(40)

        def toggle():
            if line_edit.echoMode() == QLineEdit.Password:
                line_edit.setEchoMode(QLineEdit.Normal)
            else:
                line_edit.setEchoMode(QLineEdit.Password)

        toggle_btn.clicked.connect(toggle)

        container = QHBoxLayout()
        container.addWidget(line_edit)
        container.addWidget(toggle_btn)

        wrapper = QWidget()
        wrapper.setLayout(container)
        return wrapper


    # ---------------- MASTER RESET ----------------
    def _build_master_ui(self, layout):
        from PyQt5.QtGui import QPixmap
        # ---------- HAL LOGO ----------
        logo_label = QLabel()
        logo_path = BASE_DIR / "resourses" / "hal_logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaledToWidth(140, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)

        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        layout.addSpacing(10)

        title = QLabel("Master Meta Admin – Reset Designation Passwords")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #1a4fa3;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title)


        for role in ["Senior Test Engineer", "Manager", "General Manager"]:
            row = QHBoxLayout()

            role_lbl = QLabel(role)
            role_lbl.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                font-size: 14px;
                font-weight: 500;
                padding: 6px 10px;
            }
        """)

            pwd_lbl = QLabel("********")
            pwd_lbl.setStyleSheet("""
                QLabel {
                    border: none;
                    background: transparent;
                    font-size: 14px;
                    letter-spacing: 2px;
                    padding: 6px 10px;
                }
            """)

            reset_btn = QPushButton("Reset")
            reset_btn.setFixedWidth(80)
            reset_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a5da8;
                    color: white;
                    border-radius: 4px;
                    padding: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #154a8a;
                }
            """)


            reset_btn.clicked.connect(lambda _, r=role: self._reset_designation(r))


            row.addWidget(role_lbl, alignment=Qt.AlignVCenter)
            row.addStretch()
            row.addWidget(pwd_lbl, alignment=Qt.AlignVCenter)
            row.addWidget(reset_btn, alignment=Qt.AlignVCenter)

            wrapper = QWidget()
            wrapper.setLayout(row)
            wrapper.setStyleSheet("""
                QWidget {
                    background-color: #f5f7fa;
                    border: 1px solid #d0dce8;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
            layout.addWidget(wrapper)


        logout_btn = QPushButton("Logout")
        logout_btn.setFixedHeight(40)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)

        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)


    def _reset_designation(self, designation):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Reset {designation}")
        dlg.setModal(True)
        dlg.setFixedSize(360, 240)


        v = QVBoxLayout(dlg)

        pwd1 = QLineEdit()
        pwd1.setEchoMode(QLineEdit.Password)
        pwd1.setPlaceholderText("New Password")

        pwd2 = QLineEdit()
        pwd2.setEchoMode(QLineEdit.Password)
        pwd2.setPlaceholderText("Confirm Password")

        reset = QPushButton("RESET")

        def do_reset():
            if pwd1.text() != pwd2.text():
                QMessageBox.warning(self, "Error", "Passwords do not match")
                return
            self._apply_designation_reset(designation, pwd1.text(), dlg)

        reset.clicked.connect(do_reset)

        v.addWidget(self._add_eye_toggle(pwd1))
        v.addWidget(self._add_eye_toggle(pwd2))
        v.addWidget(reset)

        dlg.exec_()



    def _apply_designation_reset(self, designation, password, dlg):
        if not password:
            QMessageBox.warning(self, "Error", "Password cannot be empty")
            return

        conn = sqlite3.connect(ADMIN_DB_PATH)
        cur = conn.cursor()

        cur.execute(
            "UPDATE admins SET password=? WHERE designation=?",
            (password, designation)
        )

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", f"{designation} password reset")
        dlg.accept()

        # rebuild UI safely
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        self._build_master_ui(layout)

    def _logout(self):
        from main3 import LoginScreen
        self.login = LoginScreen()
        self.login.show()
        self.close()


