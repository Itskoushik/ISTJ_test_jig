import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from core.paths import RESOURCES_DIR
from screens.single_test_interface import SingleTestScreen

STATION_IMG = str(RESOURCES_DIR / "station box.png")  

class TestItem(QWidget):

    def __init__(self, title, description):
        super().__init__()
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.desc_visible = False

        self.setStyleSheet("border:none;background:transparent;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        # HEADER
        header = QWidget()
        header.setStyleSheet("background:white;border:none;")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15,12,15,12)

        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("border:none;")

        self.title = QLabel(title)
        self.title.setFont(QFont("Segoe UI",11,QFont.Bold))
        self.title.setStyleSheet("border:none;")

        self.arrow = QLabel("▾")
        self.arrow.setFont(QFont("Segoe UI",13))
        self.arrow.setStyleSheet("color:#6b7280;border:none;")

        header_layout.addWidget(self.checkbox)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.title)
        header_layout.addStretch()
        header_layout.addWidget(self.arrow)

        header.setLayout(header_layout)
        header.mousePressEvent = self.toggle_description

        # DESCRIPTION
        self.description = QLabel(description)
        self.description.setWordWrap(True)

        self.description.setStyleSheet("""
        QLabel{
            color:#6b7280;
            background:transparent;
            border-left:1px solid #e5e7eb;
            border-right:1px solid #e5e7eb;
            border-bottom:1px solid #e5e7eb;
            border-radius:6px;
            padding:6px 10px;
        }
        """)

        self.description.setContentsMargins(45,6,15,10)
        self.description.hide()

        # SEPARATOR
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background:#e5e7eb;border:none;")
        line.setMaximumHeight(1)

        main_layout.addWidget(header)
        main_layout.addWidget(self.description)
        main_layout.addWidget(line)

        self.setLayout(main_layout)


    def toggle_description(self, event):

        if self.desc_visible:
            self.description.hide()
            self.arrow.setText("▾")
        else:
            self.description.show()
            self.arrow.setText("▴")

        self.desc_visible = not self.desc_visible

        self.adjustSize()
        self.parentWidget().adjustSize()



class StationBoxUI(QMainWindow):

    def __init__(self,parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        
        self.setWindowTitle("Station Box")
        self.resize(1400, 900)
        self.setMinimumSize(1100, 750)
        self.setStyleSheet("background:#F4F5F7;")

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40,25,40,25)
        main_layout.setSpacing(6)

        # TOP BAR
        top = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(100,36)
        back_btn.clicked.connect(self.go_back)

        back_btn.setStyleSheet("""
        QPushButton{
        background:white;
        border:1px solid #d1d5db;
        border-radius:6px;
        font-weight:bold;
        }
        QPushButton:hover{
        background:#eef2f7;
        }
        """)

        title = QLabel("STATION BOX")
        title.setFont(QFont("Segoe UI",22,QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        top.addWidget(back_btn)
        top.addStretch(1)
        top.addWidget(title)
        top.addStretch(1)
        top.addSpacing(120)   # balances space for the image on the right

        main_layout.addLayout(top)

        # HEADER ROW
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0,0,0,0)
        header_row.setSpacing(10)

        subtitle = QLabel("Select Tests to Run")
        subtitle.setFont(QFont("Segoe UI",14))
        subtitle.setStyleSheet("color:#374151;")
        subtitle.setContentsMargins(0,0,0,0)

        header_row.addWidget(subtitle)
        header_row.addStretch()

        # STATION IMAGE
        pix = QPixmap(STATION_IMG)

        img = QLabel()
        img.setMaximumSize(320,180)
        img.setPixmap(pix.scaled(img.maximumSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        img.setStyleSheet("border:none;background:transparent;")

        header_row.addWidget(img)

        main_layout.addLayout(header_row)

        # move the card closer to the image
        main_layout.addSpacing(-30)

        # CARD
        card = QFrame()
        card.setStyleSheet("""
        QFrame{
        background:white;
        border:1px solid #e5e7eb;
        border-radius:10px;
        }
        """)

        card_layout = QVBoxLayout()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card_layout.setSizeConstraint(QLayout.SetMinimumSize)
        card_layout.setContentsMargins(25,25,25,25)
        card_layout.setSpacing(0)

        tests = [
            ("MICROPHONE AUDIO TEST","Test and verify the audio input from the microphone."),
            ("PHONES AUDIO TEST","Test and verify the audio output to the headphones."),
            ("MIC LIMITER TEST","Check the microphone limiter functionality and response."),
            ("VOS DELAY TEST","Verify the Mic mute for 0.5s to 1.5s"),
            ("VOLTAGE MEASUREMENT TEST","Verify the electrical voltage levels of station box in NORMAL and STBY modes. Ensure measured values are within specified limits to confirm proper functionality."),
            ("RESISTANCE MEASUREMENT TEST","Verify the electrical resistance of station box switches and connectors in NORMAL and STBY modes. Ensure measured values are within specified limits to confirm proper functionality."),
            ("TRANSIENT TEST","Verify the MOD of the station box."),
            ("LIGHTING TEST","Verify the illumination of the station box faceplate legends to ensure all markings are clearly visible and uniformly lit")
        ]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
        QScrollBar:vertical {
            border: none;
            background: transparent;
            width: 8px;
            margin: 0px;
        }

        QScrollBar::handle:vertical {
            background: #cbd5e1;
            border-radius: 4px;
            min-height: 30px;
        }

        QScrollBar::handle:vertical:hover {
            background: #94a3b8;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }

        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: none;
        }
        """)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(0)

        self.test_items = []

        for t in tests:
            item = TestItem(t[0], t[1])
            self.test_items.append(item)
            scroll_layout.addWidget(item)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)

        card_layout.addWidget(scroll)

        card_layout.addSpacing(20)

        # RUN BUTTON
        run_btn = QPushButton("RUN TEST SEQ")
        run_btn.clicked.connect(self.run_selected_tests)
        run_btn.setMinimumSize(220,45)
        run_btn.setMaximumWidth(320)

        run_btn.setStyleSheet("""
        QPushButton{
        background:#5B76A8;
        color:white;
        border-radius:6px;
        font-weight:bold;
        font-size:14px;
        }
        QPushButton:hover{
        background:#6f89b5;
        }
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(run_btn)
        btn_layout.addStretch()

        card_layout.addLayout(btn_layout)

        card.setLayout(card_layout)

        main_layout.addWidget(card, 1)

        central.setLayout(main_layout)

    def go_back(self):
        if self.parent_window:
            self.parent_window.show()
        self.close()
    def run_selected_tests(self):

        selected_tests = []

        for item in self.test_items:

            title = item.title.text()

            if item.checkbox.isChecked():

                if title == "MICROPHONE AUDIO TEST":
                    selected_tests.append("microphone_audio")

                elif title == "PHONES AUDIO TEST":
                    selected_tests.append("phones_audio")

                elif title == "MIC LIMITER TEST":
                    selected_tests.append("mic_limiter")

                elif title == "VOS DELAY TEST":
                    selected_tests.append("vos_delay")

                elif title == "VOLTAGE MEASUREMENT TEST":
                    selected_tests.append("voltage_measurement")

                elif title == "RESISTANCE MEASUREMENT TEST":
                    selected_tests.append("resistance_measurement")

                elif title == "TRANSIENT TEST":
                    selected_tests.append("transient")

                elif title == "LIGHTING TEST":
                    selected_tests.append("lighting_test")

        if not selected_tests:
            QMessageBox.warning(self,"No Tests","Please select at least one test.")
            return

        print("Selected tests:", selected_tests)

        self.single_test = SingleTestScreen(
        selected_tests=selected_tests,
        previous_screen=self,
        entry_mode="station"
          )
        self.single_test.show()

        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = StationBoxUI()
    win.show()
    sys.exit(app.exec_())