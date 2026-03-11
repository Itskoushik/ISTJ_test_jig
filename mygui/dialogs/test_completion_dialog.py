from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class TestCompletionModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Report")
        self.setGeometry(300, 300, 450, 250)
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

        # Success Icon/Title
        title = QLabel("✓ Test report successfully generated.")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1b5e20;")
        layout.addWidget(title)

        info_text = QLabel(
            "You can either click on 'Save' to store the report or 'Terminate'\nto close it."
        )
        info_text.setFont(QFont("Arial", 10))
        info_text.setAlignment(Qt.AlignCenter)
        info_text.setWordWrap(True)
        layout.addWidget(info_text)

        layout.addStretch()

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(36)
        save_btn.setMinimumWidth(100)
        save_btn.setFont(QFont("Arial", 10, QFont.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
        """)
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        terminate_btn = QPushButton("Terminate")
        terminate_btn.setMinimumHeight(36)
        terminate_btn.setMinimumWidth(100)
        terminate_btn.setFont(QFont("Arial", 10, QFont.Bold))
        terminate_btn.setStyleSheet("""
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
        terminate_btn.clicked.connect(self.reject)
        button_layout.addWidget(terminate_btn)

        layout.addLayout(button_layout)