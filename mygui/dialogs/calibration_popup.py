from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QFont, QPixmap, QColor
from PyQt5.QtCore import Qt
from core.paths import RESOURCES_DIR



class CalibrationPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Message")
        self.setGeometry(200, 200, 600, 400)
        self.setModal(True)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Set Station Box Front Panel \n to Following Positions")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Knob Image
        knob_label = QLabel()
        knob_pixmap = QPixmap(str(RESOURCES_DIR / "knob.png"))
        if knob_pixmap.isNull():
            knob_pixmap = QPixmap(150, 150)
            knob_pixmap.fill(QColor("#e0e0e0"))
        else:
            knob_pixmap = knob_pixmap.scaledToWidth(150, Qt.SmoothTransformation)
        knob_label.setPixmap(knob_pixmap)
        knob_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(knob_label)

        # Instructions
        instructions = QLabel(
            "• Connect cables J65 to J101 and J66 to J102.\n"
            "• Turn the ICS knobs fully CW.\n"
            "• Set MIC Mode to HOT.\n"
            "• Turn TX SEL knobs fully CCW and to the OUT position.\n"
            "• Turn RX SEL knobs fully CCW.\n"
            "• STBY/NORM switch to NORM position."
        )
        instructions.setFont(QFont("Arial", 10))
        instructions.setAlignment(Qt.AlignLeft)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addStretch()

        # Acknowledge Button
        ack_btn = QPushButton("I Acknowledge")
        ack_btn.setMinimumHeight(40)
        ack_btn.setMaximumWidth(200)
        ack_btn.setFont(QFont("Arial", 11, QFont.Bold))
        ack_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        ack_btn.setStyleSheet("""
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
        ack_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ack_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
