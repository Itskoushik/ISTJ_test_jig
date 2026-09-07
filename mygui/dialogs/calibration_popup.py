from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtCore import Qt
from core.paths import RESOURCES_DIR


MODEL_IMAGES = {
    "N200 - ALH1": "alh1.png",
    "N200 - ALH2": "alh2.png",
    "N200 - ALH3": "alh3.png",
}


class CalibrationPopup(QDialog):
    def __init__(self, parent=None, model: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Message")
        self.setGeometry(200, 200, 700, 550) 
        self.setModal(True)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Set Station Box Front Panel \n to Following Positions")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Pick image based on selected model; fall back to sb.png
        image_file = MODEL_IMAGES.get(model, "sb.png")
        knob_label = QLabel()
        knob_pixmap = QPixmap(str(RESOURCES_DIR / image_file))
        if knob_pixmap.isNull():
            knob_pixmap = QPixmap(500, 400)
            knob_pixmap.fill(QColor("#e0e0e0"))
        else:
            knob_pixmap = knob_pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        knob_label.setPixmap(knob_pixmap)
        knob_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(knob_label)

        # Instructions
        instructions = QLabel(
            "• Turn the ICS knobs fully CW.\n"
            "• Set MIC Mode to HOT.\n"
            "• Turn TX SEL knobs fully CCW and to the OUT position.\n"
            "• Turn RX SEL knobs fully CCW.\n"
        )
        instructions.setFont(QFont("Arial", 10))
        instructions.setAlignment(Qt.AlignLeft)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addStretch()

        # Acknowledge Button
        self.ack_btn = QPushButton("I Acknowledge")
        self.ack_btn.setMinimumHeight(40)
        self.ack_btn.setMaximumWidth(200)
        self.ack_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.ack_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ack_btn.setFocusPolicy(Qt.StrongFocus)
        self.ack_btn.setStyleSheet("""
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
        self.ack_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.ack_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.ack_btn.setFocus()
        
    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Escape:
            event.ignore()
            return

        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.ack_btn.click()
            return

        super().keyPressEvent(event)