from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class DisconnectResultDialog(QDialog):
    def __init__(self, success: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Disconnect" if success else "Disconnect Failed")
        self.setModal(True)
        self.setFixedSize(360, 220)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border: none;
            }
            QLabel {
                color: #374151;
                background-color: transparent;
            }
            QPushButton {
                min-height: 34px;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton#primary {
                background-color: #1a5da8;
                color: white;
                border: none;
            }
            QPushButton#primary:hover {
                background-color: #154a8a;
            }
            QPushButton#danger {
                background-color: #d32f2f;
                color: white;
                border: none;
            }
            QPushButton#danger:hover {
                background-color: #b71c1c;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        icon_label = QLabel("✓" if success else "⚠")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Arial", 28, QFont.Bold))
        icon_label.setStyleSheet("color: #1b5e20; background-color: transparent;" if success else "color: #d32f2f; background-color: transparent;")
        layout.addWidget(icon_label)

        title = QLabel("Disconnected successfully." if success else "Disconnect failed.")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("background-color: transparent;")
        layout.addWidget(title)

        desc = QLabel(
            "You can now return to the Connection screen."
            if success else
            "Please check the cable or device and try disconnecting again."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("background-color: transparent;")
        layout.addWidget(desc)

        layout.addStretch()

        btn = QPushButton("OK" if success else "Retry")
        btn.setObjectName("primary" if success else "danger")
        btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
