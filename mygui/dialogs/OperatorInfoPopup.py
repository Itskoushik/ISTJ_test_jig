from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QSize, QTimer


class OperatorInfoPopup(QDialog):
    def __init__(self, title: str, message: str, image_path=None, buttons="ok", timer_seconds=None, parent=None):
        super().__init__(parent)
        self.result_status = None     # PASS / FAIL
        self.operator_response = None # YES / NO
        
        # ✅ FIX: timer_seconds now exists
        self.timer_seconds = timer_seconds
        self.timer = None
        self.remaining_time = None

        self.setWindowTitle(title)
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setMinimumWidth(600)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # ===============================
        # TITLE
        # ===============================
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: #0b1c2d;")
        main_layout.addWidget(title_label)

        # ✅ FIX: use self.timer_seconds instead of undefined timer_seconds
        if self.timer_seconds is not None:
            self.remaining_time = self.timer_seconds

            self.timer_label = QLabel(str(self.remaining_time))
            self.timer_label.setAlignment(Qt.AlignCenter)
            self.timer_label.setFont(QFont("Segoe UI", 32, QFont.Bold))
            self.timer_label.setStyleSheet("color: #444;")
            main_layout.addWidget(self.timer_label)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self._update_timer)
            self.timer.start(1000)

        # ===============================
        # IMAGE (OPTIONAL)
        # ===============================
        if image_path:
            image_label = QLabel()
            pixmap = QPixmap(str(image_path))

            if not pixmap.isNull():
                image_label.setPixmap(
                    pixmap.scaled(
                        QSize(420, 420),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
                image_label.setAlignment(Qt.AlignCenter)
                main_layout.addWidget(image_label)

        # ===============================
        # MESSAGE
        # ===============================
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignLeft)
        self.message_label.setFont(QFont("Segoe UI", 11))
        self.message_label.setStyleSheet("""
            color: #1a1a1a;
            padding: 6px 4px;
        """)
        main_layout.addWidget(self.message_label)

        # ===============================
        # BUTTONS
        # ===============================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if buttons == "yes_no":
            yes_btn = QPushButton("Yes")
            yes_btn.setFixedSize(120, 38)
            yes_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            yes_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2e7d32;
                    color: white;
                    border: 1px solid #1b5e20;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #1b5e20;
                }
            """)
            # ✅ FIX: stop timer on YES
            yes_btn.clicked.connect(self._on_yes)

            no_btn = QPushButton("No")
            no_btn.setFixedSize(120, 38)
            no_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            no_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border: 1px solid #b71c1c;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #b71c1c;
                }
            """)
            no_btn.clicked.connect(self._on_no)

            btn_layout.addWidget(yes_btn)
            btn_layout.addWidget(no_btn)

        else:  # DEFAULT = OK
            ok_btn = QPushButton("OK")
            ok_btn.setFixedSize(120, 38)
            ok_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            ok_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0b3d91;
                    color: white;
                    border: 1px solid #082c66;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #082c66;
                }
            """)
            ok_btn.clicked.connect(self.accept)
            btn_layout.addWidget(ok_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # ===============================
        # TIMER (OPTIONAL)
        # ===============================
        # ⛔ LEFT AS-IS (requested), but will NOT double-run
        # because timer_seconds is already handled above
        if False and self.timer_seconds is not None:
            pass

    def _update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.timer_label.setText(str(self.remaining_time))
        else:
            self.timer.stop()   # informational only

    # ✅ ADDED: YES handler without removing any existing logic
    def _on_yes(self):
        if self.timer:
            self.timer.stop()
        self.result_status = "PASS"
        self.operator_response = "YES"
        self.done(QDialog.Accepted)
    def _on_no(self):
        if self.timer:
            self.timer.stop()

        self.result_status = "FAIL"
        self.operator_response = "NO"

        self.done(QDialog.Rejected)
    def get_result(self):
        return self.result_status, self.operator_response
