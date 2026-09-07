import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from core.paths import RESOURCES_DIR


JUNCTION_IMG = str(RESOURCES_DIR / "Junction box.png")  
GROUND_CREW_PARENTS = {
    "GROUND CREW PRIMARY INTERCOM CHANNEL TEST",
    "GROUND CREW PRIVATE INTERCOM CHANNEL TEST",
    "GROUND CREW OVERRIDE INTERCOM CHANNEL TEST",
    "GROUND CREW CVR OUTPUT LEVEL TEST",
}
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


def _make_warning_icon(size=100, icon_size=74):
    """Glow circle + caution.png icon."""
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
    """Reusable side-by-side warning popup: icon left, text + optional info box right."""

    def __init__(self, parent=None, *, title="Warning",
                 heading="Something went wrong.",
                 description_lines=None,
                 info_title=None, info_desc=None,
                 ok_text="OK"):
        super().__init__(parent)
        self.setStyleSheet("QLabel { border: none; }")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(660)

        description_lines = description_lines or []

        card = QFrame(self)
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

        outer_wrap = QVBoxLayout(self)
        outer_wrap.setContentsMargins(0, 0, 0, 0)
        outer_wrap.addWidget(card)

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
        title_lbl.setFont(QFont("Arial", 13, QFont.Bold))
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

        # ---- Body: icon left, text right ----
        body = QHBoxLayout()
        body.setContentsMargins(40, 30, 40, 20)
        body.setSpacing(30)

        icon = _make_warning_icon()
        body.addWidget(icon, 0, Qt.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(8)

        heading_lbl = QLabel(heading)
        heading_lbl.setFont(QFont("Arial", 16, QFont.Bold))
        heading_lbl.setStyleSheet("color: #17233d; border: none; background: transparent;")
        heading_lbl.setWordWrap(True)
        text_col.addWidget(heading_lbl)

        for line in description_lines:
            d = QLabel(line)
            d.setFont(QFont("Arial", 10))
            d.setStyleSheet("color: #6b7484; border: none; background: transparent;")
            d.setWordWrap(True)
            d.setTextFormat(Qt.RichText)   # allows <b>/<span style='color:...'> highlights
            text_col.addWidget(d)

        if info_title:
            info_box = QFrame()
            info_box.setStyleSheet("""
                QFrame {
                    background-color: #fff8e6;
                    border: 1px solid #ffe4a3;
                    border-radius: 8px;
                }
            """)
            info_layout = QHBoxLayout(info_box)
            info_layout.setContentsMargins(14, 12, 14, 12)
            info_layout.setSpacing(12)

            info_icon = QLabel("i")
            info_icon.setFixedSize(22, 22)
            info_icon.setAlignment(Qt.AlignCenter)
            info_icon.setStyleSheet("""
                QLabel {
                    background-color: #fbc02d; color: white;
                    border-radius: 11px; font-weight: bold; border: none;
                }
            """)
            info_layout.addWidget(info_icon, 0, Qt.AlignTop)

            info_text_col = QVBoxLayout()
            info_text_col.setSpacing(2)
            it = QLabel(info_title)
            it.setFont(QFont("Arial", 10, QFont.Bold))
            it.setStyleSheet("color: #17233d; border: none; background: transparent;")
            info_text_col.addWidget(it)
            if info_desc:
                idesc = QLabel(info_desc)
                idesc.setFont(QFont("Arial", 9))
                idesc.setStyleSheet("color: #6b7484; border: none; background: transparent;")
                idesc.setWordWrap(True)
                info_text_col.addWidget(idesc)
            info_layout.addLayout(info_text_col, 1)

            text_col.addSpacing(6)
            text_col.addWidget(info_box)

        body.addLayout(text_col, 1)
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
        f_layout.addStretch()

        ok_btn = QPushButton(f"  {ok_text}")
        ok_btn.setMinimumSize(140, 48)
        ok_btn.setFont(QFont("Arial", 12, QFont.Bold))
        ok_btn.setCursor(Qt.PointingHandCursor)
        check_path = RESOURCES_DIR / "check_circle.png"
        if check_path.exists():
            ok_btn.setIcon(QIcon(str(check_path)))
            ok_btn.setIconSize(QSize(18, 18))
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
        self.setFixedHeight(card.sizeHint().height())


class JunctionBoxUI(QMainWindow):

    def __init__(self,parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        
        self.setWindowTitle("Junction Box")
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
            ("GROUND CREW PRIMARY INTERCOM CHANNEL TEST",None,["ICS VOLUME TEST", "ICS LIMITER TEST"]),
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
        # SELECT ALL
        self.select_all_item = TestItem("SELECT ALL", "Check or uncheck all tests at once.", None)
        self.select_all_item.checkbox.setTristate(True)
        self.select_all_item.checkbox.setCheckState(Qt.Checked)
        self.select_all_item.checkbox.stateChanged.connect(self.on_select_all_changed)
        scroll_layout.addWidget(self.select_all_item)
        
        # Add connector checkboxes
        connector_label = QLabel("Connectors to Test:")
        connector_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        connector_label.setStyleSheet("color:#374151; border:none; background:transparent;")
        card_layout.addWidget(connector_label)

        connector_row = QHBoxLayout()
        self.connector_checks = {}
        for conn in ["J103", "J104", "J105", "J106", "J107"]:
            cb = QCheckBox(conn)
            cb.setChecked(True)  # default: all selected
            cb.setFont(QFont("Segoe UI", 10))
            cb.setStyleSheet("color:#374151; padding:4px;")
            self.connector_checks[conn] = cb
            connector_row.addWidget(cb)
        connector_row.addStretch()
        card_layout.addLayout(connector_row)

        for title, desc, subs in tests:
            item = TestItem(title, desc, subs)
            item.checkbox.blockSignals(True)                    
            item.checkbox.setChecked(True)                      
            # Also check all subtests if they exist            
            for subtest_cb in item.subtest_boxes:              
                subtest_cb.blockSignals(True)                  
                subtest_cb.setChecked(True)                    
                subtest_cb.blockSignals(False)                 
            item.checkbox.blockSignals(False)                  
            item.checkbox.stateChanged.connect(self.on_child_checkbox_changed)
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
    def on_select_all_changed(self, state):
        checked = (state == Qt.Checked)
        for item in self.test_items:
            item.checkbox.blockSignals(True)
            item.checkbox.setChecked(checked)
            item.checkbox.blockSignals(False)
            # Also sync all subtests directly
            for sub_cb in item.subtest_boxes:
                sub_cb.blockSignals(True)
                sub_cb.setChecked(checked)
                sub_cb.blockSignals(False)

    def on_child_checkbox_changed(self):
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

    def go_back(self):
        if self.parent_window:
            self.parent_window.show()
        self.close()
    def run_selected_tests(self):
        selected_tests = []
        for item in self.test_items:
            selected_tests.extend(item.get_selected_tests())

        if not selected_tests:
            WarningDialog(
                self,
                title="No Tests Selected",
                heading="Please select at least one test.",
                description_lines=["You need to choose a test to continue."],
            ).exec_()
            return

        # Collect selected connectors
        selected_connectors = [
            conn for conn, cb in self.connector_checks.items() if cb.isChecked()
        ]
        if not selected_connectors:
            WarningDialog(
                self,
                title="Connector Selection Required",
                heading="Please choose at least one connector.",
                description_lines=[
                    "To continue, select one or more connectors from "
                    "<span style='color:#1976d2; font-weight:bold;'>J103–J107</span>.",
                    "You must select at least one connector.",
                ],
                info_title="Need help?",
                info_desc="Refer to the connector layout for more information.",
            ).exec_()
            return
        # Block ground-crew-only runs with multiple connectors
        has_gc = any(
            (t.split("::")[0].strip() if "::" in t else t.strip()) in GROUND_CREW_PARENTS
            for t in selected_tests
        )
        has_user = any(
            (t.split("::")[0].strip() if "::" in t else t.strip()) not in GROUND_CREW_PARENTS
            for t in selected_tests
        )
        if has_gc and not has_user and len(selected_connectors) > 1:
            WarningDialog(
                self,
                title="Connector Selection Error",
                heading="Ground Crew tests run on a single connector only.",
                description_lines=[
                    "Please select exactly one connector from "
                    "<span style='color:#1976d2; font-weight:bold;'>J103–J107</span> "
                    "when running Ground Crew tests without any User tests."
                ],
            ).exec_()
            return
        from screens.single_test_interface import SingleTestScreen
        self.single_test = SingleTestScreen(
            selected_tests=selected_tests,
            previous_screen=self,
            entry_mode="junction",
            selected_connectors=selected_connectors   # NEW
        )
        self.single_test.return_to_test_selection.connect(self.show)
        self.single_test.show()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = JunctionBoxUI()
    win.show()
    sys.exit(app.exec_())