from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class _SpaceSafeButton(QPushButton):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            event.ignore()
            return
        super().keyPressEvent(event)

class AbortTestConfirmationPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Abort Test?")
        self.setGeometry(400, 300, 500, 250)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 4px;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Warning Title
        title = QLabel("Abort Test?")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #d32f2f; border: none;")
        layout.addWidget(title)

        # Message
        message = QLabel(
            "A test is currently running. Do you want to abort it and return to the Test Selection screen?"
        )
        message.setFont(QFont("Arial", 10))
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("border: none;")
        layout.addWidget(message)

        layout.addStretch()

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.abort_go_back_btn = _SpaceSafeButton("Yes, Abort & Go Back")
        self.abort_go_back_btn.setMinimumHeight(36)
        self.abort_go_back_btn.setMinimumWidth(140)
        self.abort_go_back_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.abort_go_back_btn.setFocusPolicy(Qt.StrongFocus)
        self.abort_go_back_btn.setAutoDefault(False)
        self.abort_go_back_btn.setDefault(False)
        self.abort_go_back_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.abort_go_back_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.abort_go_back_btn)

        self.cancel_btn = _SpaceSafeButton("Cancel")
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.cancel_btn.setFocusPolicy(Qt.StrongFocus)
        self.cancel_btn.setAutoDefault(True)
        self.cancel_btn.setDefault(True)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.cancel_btn.setFocus()