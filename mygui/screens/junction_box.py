import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from core.paths import RESOURCES_DIR


JUNCTION_IMG = str(RESOURCES_DIR / "Junction box.png")  

class TestItem(QWidget):

    def __init__(self, title, description=None, subtests=None):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.subtests = subtests or []
        self.parent_title = title.strip() 
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
        self.title.setStyleSheet("border:none;background:white;")

        self.arrow = QLabel("▾")
        self.arrow.setFont(QFont("Segoe UI",13))
        self.arrow.setStyleSheet("color:#6b7280;border:none;background:white;")

        header_layout.addWidget(self.checkbox)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.title)
        header_layout.addStretch()
        header_layout.addWidget(self.arrow)

        header.setLayout(header_layout)
        header.mousePressEvent = self.toggle_dropdown

        main_layout.addWidget(header)

        # CONTENT CONTAINER
        self.content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(45,6,15,10)

        self.subtest_boxes = []

        # DESCRIPTION MODE
        if description and not self.subtests:

            self.desc_label = QLabel(description)
            self.desc_label.setWordWrap(True)

            self.desc_label.setStyleSheet("""
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

            content_layout.addWidget(self.desc_label)

        # SUBTEST MODE
        for sub in self.subtests:

            cb = QCheckBox(sub)

            cb.setStyleSheet("""
            QCheckBox{
                color:#374151;
                padding:4px;
                border-left:1px solid #e5e7eb;
                border-right:1px solid #e5e7eb;
            }
            """)

            cb.stateChanged.connect(self.update_main_checkbox)

            content_layout.addWidget(cb)

            self.subtest_boxes.append(cb)

        self.content.setLayout(content_layout)
        self.content.hide()

        main_layout.addWidget(self.content)

        # SEPARATOR
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background:#e5e7eb;border:none;")
        line.setMaximumHeight(1)

        main_layout.addWidget(line)

        self.setLayout(main_layout)

        self.checkbox.stateChanged.connect(self.toggle_all_subtests)

    def toggle_dropdown(self, event):

        if self.desc_visible:
            self.content.hide()
            self.arrow.setText("▾")
        else:
            self.content.show()
            self.arrow.setText("▴")

        self.desc_visible = not self.desc_visible

        self.adjustSize()
        self.parentWidget().adjustSize()
        
    def get_selected_tests(self):

        selected = []

        parent = self.parent_title

        # if no subtests → main checkbox represents test
        if not self.subtest_boxes:
            if self.checkbox.isChecked():
                selected.append(parent)
            return selected

        # if subtests exist → return checked ones
        for cb in self.subtest_boxes:
            if cb.isChecked():
                sub = cb.text().strip()
                selected.append(f"{parent}::{sub}")

        return selected
    def toggle_all_subtests(self, state):

        if not self.subtest_boxes:
            return

        for cb in self.subtest_boxes:
            cb.blockSignals(True)
            cb.setChecked(state == Qt.Checked)
            cb.blockSignals(False)

    def update_main_checkbox(self):

        if not self.subtest_boxes:
            return

        checked = all(cb.isChecked() for cb in self.subtest_boxes)

        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)


class JunctionBoxUI(QMainWindow):

    def __init__(self,parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        
        self.setWindowTitle("Junction Box")
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

        title = QLabel("Junction Box")
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

        # Junction IMAGE
        pix = QPixmap(JUNCTION_IMG)

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
            ("POWER SUPPLY TEST","Test and verify the audio input from the microphone.",None),
            ("USER PRIMARY INTERCOM CHANNEL TEST",None,["ICS VOLUME TEST", "ICS VOLUME CONTROL TEST","SONIC MUTE TEST","TX PTT TEST"]),
            ("USER PRIVATE INTERCOM CHANNEL TEST",None,["ICS VOLUME TEST"]),
            ("USER OVERRIDE INTERCOM CHANNEL TEST",None,["ICS VOLUME TEST"]),
            ("USER CVR AUDIO TEST",None,["CVR OUTPUT LEVEL TEST"]),
            ("USER TRANSMIT AUDIO TEST",None,["TX OUTPUT LEVEL TEST"]),
            ("USER RECEIVE AUDIO TEST",None,["RX SELECTION AND MUTING TEST"]),
            ("GROUND CREW PRIMARY INTERCOM CHANNEL TEST",None,["ICS VOLUME TEST", "ICS LIMITER TEST","HEADSET CHECK TEST"]),
            ("GROUND CREW PRIVATE INTERCOM CHANNEL TEST",None,None),
            ("GROUND CREW OVERRIDE INTERCOM CHANNEL TEST",None,None),
            ("GROUND CREW CVR OUTPUT LEVEL TEST",None,None)
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

        for title, desc, subs in tests:
            item = TestItem(title, desc, subs)
            scroll_layout.addWidget(item)
            self.test_items.append(item)

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
            selected_tests.extend(item.get_selected_tests())

        if not selected_tests:
            QMessageBox.warning(self, "No Test Selected", "Please select at least one test.")
            return

        from screens.single_test_interface import SingleTestScreen

        self.single_test = SingleTestScreen(
        selected_tests=selected_tests,
        previous_screen=self,
        entry_mode="junction"
        )
        self.single_test.return_to_test_selection.connect(self.show)

        self.single_test.show()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = JunctionBoxUI()
    win.show()
    sys.exit(app.exec_())