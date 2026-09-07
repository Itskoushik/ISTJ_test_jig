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


def _make_warning_icon(size=110, icon_size=84):
    """Glow circle + caution.png icon, matching the mockup."""
    wrap = QLabel()
    wrap.setFixedSize(size, size)
    wrap.setAlignment(Qt.AlignCenter)
    wrap.setStyleSheet(f"""
        QLabel {{
            background-color: #fff3e0;
            border-radius: {size // 2}px;
            border: none;
        }}
    """)
    pix = QPixmap(str(RESOURCES_DIR / "caution.png"))
    if not pix.isNull():
        wrap.setPixmap(pix.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return wrap


class WarningDialog(QDialog):
    """Reusable warning popup matching the app's design language."""

    def __init__(self, parent=None, *, title="Warning",
                 heading="Something went wrong.",
                 description="Please check your input and try again.",
                 ok_text="OK"):
        super().__init__(parent)
        self.setStyleSheet("QLabel { border: none; }")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(560)

        card = QFrame(self)
        card.setGeometry(0, 0, 560, 430)
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 14px;
                border: 1px solid #e2e6ec;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        outer = QVBoxLayout(card)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ---- Title bar ----
        title_bar = QFrame()
        title_bar.setFixedHeight(56)
        title_bar.setStyleSheet("QFrame { border-bottom: 1px solid #eef1f5; }")
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(20, 0, 16, 0)
        tb_layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(QIcon(str(RESOURCES_DIR / "istj.png")).pixmap(22, 22))
        logo.setStyleSheet("border: none; background: transparent;")
        tb_layout.addWidget(logo)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Arial", 12, QFont.Bold))
        title_lbl.setStyleSheet("color: #17233d; border: none; background: transparent;")
        tb_layout.addWidget(title_lbl)
        tb_layout.addStretch()

        close_x = QPushButton("✕")
        close_x.setFixedSize(28, 28)
        close_x.setCursor(Qt.PointingHandCursor)
        close_x.setStyleSheet("""
            QPushButton { border: none; background: #eef3fc; border-radius: 6px; color: #17233d; font-size: 14px; }
            QPushButton:hover { background: #dde6f5; }
        """)
        close_x.clicked.connect(self.reject)
        tb_layout.addWidget(close_x)

        outer.addWidget(title_bar)

        # ---- Body ----
        body = QVBoxLayout()
        body.setContentsMargins(40, 30, 40, 20)
        body.setSpacing(10)
        body.setAlignment(Qt.AlignHCenter)

        icon = _make_warning_icon()
        body.addWidget(icon, 0, Qt.AlignHCenter)
        body.addSpacing(10)

        heading_lbl = QLabel(heading)
        heading_lbl.setFont(QFont("Arial", 17, QFont.Bold))
        heading_lbl.setStyleSheet("color: #17233d; border: none; background: transparent;")
        heading_lbl.setAlignment(Qt.AlignCenter)
        body.addWidget(heading_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setFont(QFont("Arial", 11))
        desc_lbl.setStyleSheet("color: #6b7484; border: none; background: transparent;")
        desc_lbl.setAlignment(Qt.AlignCenter)
        body.addWidget(desc_lbl)

        outer.addLayout(body)

        # ---- Footer ----
        footer = QFrame()
        footer.setFixedHeight(90)
        footer.setStyleSheet("""
            QFrame {
                border-top: 1px solid #eef1f5;
                background-color: #ffffff;
                border-bottom-left-radius: 14px;
                border-bottom-right-radius: 14px;
            }
        """)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(40, 20, 40, 20)

        ok_btn = QPushButton(ok_text)
        ok_btn.setMinimumHeight(48)
        ok_btn.setFont(QFont("Arial", 12, QFont.Bold))
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2; color: white;
                border: none; border-radius: 8px;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
        """)
        ok_btn.clicked.connect(self.accept)
        f_layout.addWidget(ok_btn)

        outer.addWidget(footer)
        card.adjustSize()
        self.setFixedHeight(card.sizeHint().height())


class StationBoxUI(QMainWindow):

    def __init__(self,parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        
        self.setWindowTitle("Station Box")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
        self.setMinimumSize(1100, 750)
        self.setStyleSheet("background:#F4F5F7;")
        self.showMaximized()

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

        # SELECT ALL
        self.select_all_item = TestItem("SELECT ALL", "Check or uncheck all tests at once.")
        self.select_all_item.checkbox.setTristate(True)
        self.select_all_item.checkbox.setChecked(True)
        self.select_all_item.checkbox.stateChanged.connect(self.on_select_all_changed)
        scroll_layout.addWidget(self.select_all_item)

        self.test_items = []

        for t in tests:
            item = TestItem(t[0], t[1])
            item.checkbox.setChecked(True)
            item.checkbox.stateChanged.connect(self.on_child_checkbox_changed)
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
        
    def on_select_all_changed(self, state):
        """Propagate Select All → all individual checkboxes."""
        checked = (state == Qt.Checked)
        for item in self.test_items:
            item.checkbox.blockSignals(True)        # prevent feedback loop
            item.checkbox.setChecked(checked)
            item.checkbox.blockSignals(False)
    def on_child_checkbox_changed(self):
        """Update Select All state when any individual checkbox changes."""
        all_checked  = all(i.checkbox.isChecked() for i in self.test_items)
        none_checked = not any(i.checkbox.isChecked() for i in self.test_items)

        self.select_all_item.checkbox.blockSignals(True)
        if all_checked:
            self.select_all_item.checkbox.setCheckState(Qt.Checked)
        elif none_checked:
            self.select_all_item.checkbox.setCheckState(Qt.Unchecked)
        else:
            self.select_all_item.checkbox.setCheckState(Qt.PartiallyChecked)
        self.select_all_item.checkbox.blockSignals(False)
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
            WarningDialog(
                self,
                title="No Tests Selected",
                heading="Please select at least one test.",
                description="You need to choose a test to continue.",
            ).exec_()
            return

        print("Selected tests:", selected_tests)

        self.single_test = SingleTestScreen(
        selected_tests=selected_tests,
        previous_screen=self,
        entry_mode="station"
          )
        
        # ✅ Register with HALApplication so eventFilter can see it
        app = QApplication.instance()
        if hasattr(app, "current_screen"):
            app.current_screen = self.single_test
        self.single_test.show()

        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = StationBoxUI()
    win.show()
    sys.exit(app.exec_())