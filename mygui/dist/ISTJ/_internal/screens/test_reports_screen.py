from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt5.QtGui import *
# from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from pathlib import Path
from core.paths import RESOURCES_DIR, PDF_TEST_REPORTS_DIR,LOGS_DETAILED_DIR,TEST_LOGS_DIR,SELF_TEST_REPORTS_DIR,LOGS_SELF_TEST_DIR,LOGS_PDF_DIR
import re
import os
import sys
from datetime import datetime

        
        
class SortableHeaderLabel(QLabel):
    clicked = pyqtSignal(str)
    ICON_NEUTRAL = " ⇅"
    ICON_ASC     = " ↑"
    ICON_DESC    = " ↓"

    def __init__(self, text: str, col_key: str, parent=None):
        super().__init__(text + self.ICON_NEUTRAL, parent)
        self.col_key   = col_key
        self.base_text = text
        self.setCursor(Qt.PointingHandCursor)

    def set_sort_state(self, active: bool, ascending: bool):
        icon = (self.ICON_ASC if ascending else self.ICON_DESC) if active else self.ICON_NEUTRAL
        self.setText(self.base_text + icon)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.col_key)
        super().mousePressEvent(event)

class EmptyStateDialog(QDialog):
    """Reusable empty-state / info popup matching the app's design language."""

    def __init__(self, parent=None, *, title="No Test Reports",
                 icon_path=None, heading="No test reports found",
                 description_lines=None, tip_icon_path=None,
                 tip_title="Generate reports",
                 tip_desc="Run your tests to generate PDF reports that will appear here.",
                 show_tip=True):
        super().__init__(parent)
        self.setStyleSheet("QLabel { border: none; }")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(560, 430)

        description_lines = description_lines or [
            "There are currently no PDF reports available.",
            "Run tests and generate reports to see them here."
        ]

        # ---- Outer shadowed rounded card ----
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
            QPushButton { border: none; background: transparent; color: #8a94a6; font-size: 14px; }
            QPushButton:hover { color: #17233d; }
        """)
        close_x.clicked.connect(self.reject)
        tb_layout.addWidget(close_x)

        outer.addWidget(title_bar)

        # ---- Body ----
        body = QVBoxLayout()
        body.setContentsMargins(40, 28, 40, 20)
        body.setSpacing(6)
        body.setAlignment(Qt.AlignHCenter)

        icon_circle = QLabel()
        icon_circle.setFixedSize(96, 96)
        icon_circle.setAlignment(Qt.AlignCenter)
        icon_circle.setStyleSheet("""
            QLabel { background-color: #eef3fc; border-radius: 48px; border: none; }
        """)
        if icon_path:
            pm = QIcon(str(icon_path)).pixmap(44, 44)
            icon_circle.setPixmap(pm)
        body.addWidget(icon_circle, 0, Qt.AlignHCenter)
        body.addSpacing(14)

        heading_lbl = QLabel(heading)
        heading_lbl.setFont(QFont("Arial", 15, QFont.Bold))
        heading_lbl.setStyleSheet("color: #17233d; border: none; background: transparent;")
        heading_lbl.setAlignment(Qt.AlignCenter)
        body.addWidget(heading_lbl)

        for line in description_lines:
            d = QLabel(line)
            d.setFont(QFont("Arial", 10))
            d.setStyleSheet("color: #6b7484; border: none; background: transparent;")
            d.setAlignment(Qt.AlignCenter)
            body.addWidget(d)
        outer.addLayout(body)

        # ---- Tip card ----
        if show_tip:
            tip_frame = QFrame()
            tip_frame.setStyleSheet("""
                QFrame { background-color: #f6f8fb; border-radius: 8px; border: 1px solid #eef1f5; }
            """)
            tip_layout = QHBoxLayout(tip_frame)
            tip_layout.setContentsMargins(16, 14, 16, 14)
            tip_layout.setSpacing(14)

            tip_icon = QLabel()
            if tip_icon_path:
                tip_icon.setPixmap(QIcon(str(tip_icon_path)).pixmap(28, 28))
            tip_icon.setStyleSheet("border: none; background: transparent;")
            tip_layout.addWidget(tip_icon, 0, Qt.AlignTop)

            tip_text_layout = QVBoxLayout()
            tip_text_layout.setSpacing(2)
            tt = QLabel(tip_title)
            tt.setFont(QFont("Arial", 10, QFont.Bold))
            tt.setStyleSheet("color: #17233d; border: none; background: transparent;")
            td = QLabel(tip_desc)
            td.setFont(QFont("Arial", 9))
            td.setStyleSheet("color: #6b7484; border: none; background: transparent;")
            td.setWordWrap(True)
            tip_text_layout.addWidget(tt)
            tip_text_layout.addWidget(td)
            tip_layout.addLayout(tip_text_layout, 1)

            wrap = QHBoxLayout()
            wrap.setContentsMargins(40, 0, 40, 0)
            wrap.addWidget(tip_frame)
            outer.addLayout(wrap)

        outer.addStretch()

        # ---- Footer ----
        footer = QFrame()
        footer.setFixedHeight(64)
        footer.setStyleSheet("QFrame { border-top: 1px solid #eef1f5; }")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(20, 0, 20, 0)
        f_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedSize(96, 36)
        close_btn.setFont(QFont("Arial", 10, QFont.Bold))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8; color: white;
                border: none; border-radius: 6px;
            }
            QPushButton:hover { background-color: #164e8e; }
        """)
        close_btn.clicked.connect(self.accept)
        f_layout.addWidget(close_btn)

        outer.addWidget(footer)


class TestReportsScreen(QMainWindow):
    return_to_test_selection = pyqtSignal()

    def __init__(self, reports_dir=None, mode="test", filter_options=None):
        super().__init__()
        self.sort_chain = []   # list of (col_key, ascending:bool), index 0 = highest priority
        self.sort_asc = True
        self.search_text = ""        # ADD THIS
        self.active_filters = set()  # ADD THIS
        self.current_section = "Test Reports"   # "Test Reports" | "Log Files"
        self.current_format  = "PDF"            # "PDF" | "TXT"
        self.reports_dir = reports_dir or PDF_TEST_REPORTS_DIR
        self.mode = mode  # "test" or "self"
        self.filter_options = filter_options or ["N200-ALH1", "N200-ALH2", "N200-ALH3", "N200-ALH4"]
        self.setWindowTitle("HAL - Test Reports")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
        self.setStyleSheet("background-color: #f5f5f5;")
        self.showMaximized()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ===== HEADER BAR (MATCHING IMAGE UI) =====
        header_frame = QFrame()
        header_frame.setFixedHeight(64)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
            }
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 10, 16, 10)
        header_layout.setSpacing(12)

        # Back Button (Left)
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(110, 36)
        back_btn.setFont(QFont("Arial", 9, QFont.Bold))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #fbc02d;
                color: #000000;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f9a825;
            }
        """)
        back_btn.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(back_btn, 0, Qt.AlignLeft)

        # Center Title
        title = QLabel("Test Reports")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1a5da8;")
        header_layout.addWidget(title, 1)

        # PDF / TXT toggle (right side, same fixed width as back btn to keep title centred)
        toggle_frame = QFrame()
        toggle_frame.setFixedSize(130, 36)
        toggle_frame.setStyleSheet("QFrame { background: transparent; }")
        toggle_layout = QHBoxLayout(toggle_frame)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(2)

        self.pdf_btn = QPushButton("PDF")
        self.pdf_btn.setFixedSize(64, 36)
        self.pdf_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.pdf_btn.setCursor(Qt.PointingHandCursor)
        self.pdf_btn.clicked.connect(lambda: self.on_format_changed("PDF"))

        self.txt_btn = QPushButton("TXT")
        self.txt_btn.setFixedSize(64, 36)
        self.txt_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.txt_btn.setCursor(Qt.PointingHandCursor)
        self.txt_btn.clicked.connect(lambda: self.on_format_changed("TXT"))

        toggle_layout.addWidget(self.pdf_btn)
        toggle_layout.addWidget(self.txt_btn)
        header_layout.addWidget(toggle_frame, 0, Qt.AlignRight)

        layout.addWidget(header_frame)
        # ===== SEARCH + FILTER BAR =====
        search_filter_frame = QFrame()
        search_filter_layout = QHBoxLayout(search_filter_frame)
        search_filter_layout.setContentsMargins(0, 0, 0, 0)
        search_filter_layout.setSpacing(10)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("  Search reports by file name...")
        self.search_box.addAction(
            QIcon(str(RESOURCES_DIR / "paper.png")),
            QLineEdit.LeadingPosition
        )
        self.search_box.setFixedHeight(36)
        self.search_box.setFont(QFont("Arial", 10))
        self.search_box.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d7e2;
                border-radius: 6px;
                padding: 4px 10px;
                background: white;
            }
        """)
        self.search_box.textChanged.connect(self.on_search_changed)
        search_filter_layout.addWidget(self.search_box)

        # Section dropdown — "Test Reports" | "Log Files"
        self.section_btn = QPushButton("Test Reports  ▾")
        self.section_btn.setFixedSize(150, 36)
        self.section_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.section_btn.setCursor(Qt.PointingHandCursor)
        self.section_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #d0d7e2;
                border-radius: 6px;
                background: white;
                padding: 4px 10px;
                color: #1a5da8;
            }
            QPushButton:hover { background: #f0f4ff; }
        """)
        self.section_btn.clicked.connect(self.show_section_menu)
        search_filter_layout.addWidget(self.section_btn)
        # NOTE: initial section text/state is set AFTER report_list is created below
        
        # Filter button (dropdown)
        self.filter_btn = QPushButton("  Filters  ▾")
        self.filter_btn.setIcon(QIcon(str(RESOURCES_DIR / "filter1.png")))
        self.filter_btn.setIconSize(QSize(16, 16))
        self.filter_btn.setFixedSize(120, 36)
        self.filter_btn.setFont(QFont("Arial", 9))
        self.filter_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #d0d7e2;
                border-radius: 6px;
                background: white;
                padding: 4px 10px;
                text-align: left;
            }
            QPushButton:hover { background: #f0f4ff; }
        """)
        self.filter_btn.clicked.connect(self.show_filter_menu)
        search_filter_layout.addWidget(self.filter_btn)

        layout.addWidget(search_filter_frame)
        
        col_header = QFrame()
        col_header.setFixedHeight(36)
        col_header.setStyleSheet("""
            QFrame { background-color: #1a5da8; border-radius: 6px 6px 0px 0px; }
        """)
        col_layout = QHBoxLayout(col_header)
        col_layout.setContentsMargins(12, 0, 12, 0)
        col_layout.setSpacing(10)

        columns = [
            ("File Name", "name",   None),
            ("Date",      "date",   100),
            ("Time",      "time",   75),
            ("Test Type", "type",   90),
            ("Status",    "status", 70),
        ]
        self._header_labels = {}

        for text, key, width in columns:
            lbl = SortableHeaderLabel(text, key)
            lbl.setFont(QFont("Arial", 9, QFont.Bold))
            lbl.setStyleSheet("QLabel { color: #ffffff; } QLabel:hover { color: #fbc02d; }")
            align = Qt.AlignLeft | Qt.AlignVCenter if key == "name" else Qt.AlignCenter
            lbl.setAlignment(align)
            if width:
                lbl.setFixedWidth(width)
            else:
                lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            lbl.clicked.connect(self.on_header_clicked)
            col_layout.addWidget(lbl)
            self._header_labels[key] = lbl

        layout.addWidget(col_header)

        # ===== LIST =====
        self.report_list = QListWidget()
        self.report_list.setFont(QFont("Arial", 10))
        self.report_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #d0d7e2;
                border-radius: 6px;
            }
        """)
        self.report_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.report_list.customContextMenuRequested.connect(self.show_report_context_menu)


        layout.addWidget(self.report_list)
        self._update_filter_btn_label()
        self._refresh_toggle_style()
        self._select_section("Test Reports")  # safe to call now
        # self.load_reports()

    
    # -------------------------------------------------
    def on_search_changed(self, text: str):
        self.search_text = text.strip().lower()
        self.load_reports()

    def show_section_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: white; border: 1px solid #d0d7e2; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 20px; font-size: 10pt; }
            QMenu::item:selected { background: #e8f0fb; color: #1a5da8; }
        """)
        for text in ["Test Reports", "Log Files"]:
            action = menu.addAction(text)
            action.triggered.connect(lambda checked, t=text: self._select_section(t))
        menu.exec_(self.section_btn.mapToGlobal(self.section_btn.rect().bottomLeft()))

    def _select_section(self, text: str):
        self.section_btn.setText(f"{text}  ▾")
        self.on_section_changed(text)

    def show_filter_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: white; border: 1px solid #d0d7e2; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 20px; font-size: 10pt; }
            QMenu::item:selected { background: #e8f0fb; color: #1a5da8; }
            QMenu::item:checked { font-weight: bold; }
        """)
        options = self.filter_options
        for opt in options:
            action = menu.addAction(opt)
            action.setCheckable(True)
            action.setChecked(opt in self.active_filters)
            action.triggered.connect(lambda checked, o=opt: self.toggle_filter(o))
        menu.addSeparator()
        clear = menu.addAction("Clear Filters")
        clear.triggered.connect(self.clear_filters)
        menu.exec_(self.filter_btn.mapToGlobal(self.filter_btn.rect().bottomLeft()))

    def toggle_filter(self, option: str):
        if option in self.active_filters:
            self.active_filters.discard(option)
        else:
            self.active_filters.add(option)
        self._update_filter_btn_label()
        self.load_reports()

    def clear_filters(self):
        self.active_filters.clear()
        self._update_filter_btn_label()
        self.load_reports()

    def _update_filter_btn_label(self):
        # Icon always present
        self.filter_btn.setIcon(QIcon(str(RESOURCES_DIR / "filter 1.png")))
        self.filter_btn.setIconSize(QSize(16, 16))
        self.filter_btn.setText("  Filters  ▾")

        if self.active_filters:
            self.filter_btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #1a5da8;
                    border-radius: 6px;
                    background: #e8f0fb;
                    padding: 4px 10px;
                    text-align: left;
                    color: #1a5da8;
                    font-weight: bold;
                }
                QPushButton:hover { background: #d0e2f8; }
            """)
        else:
            self.filter_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #d0d7e2;
                    border-radius: 6px;
                    background: white;
                    padding: 4px 10px;
                    text-align: left;
                }
                QPushButton:hover { background: #f0f4ff; }
            """)
    def on_section_changed(self, section: str):
        self.current_section = section
        if section == "Test Reports":
            self.current_format = "PDF"   # force PDF when switching to reports
        self._refresh_toggle_style()
        self.load_reports()

    def on_format_changed(self, fmt: str):
        if self.current_section == "Test Reports" and fmt == "TXT":
            return  # TXT disabled for Test Reports — ignore click
        self.current_format = fmt
        self._refresh_toggle_style()
        self.load_reports()

    def _refresh_toggle_style(self):
        ACTIVE = """
            QPushButton {
                background-color: #1a5da8; color: white;
                border: none; border-radius: 4px;
            }
        """
        INACTIVE = """
            QPushButton {
                background-color: #e0e0e0; color: #333333;
                border: none; border-radius: 4px;
            }
        """
        DISABLED = """
            QPushButton {
                background-color: #eeeeee; color: #aaaaaa;
                border: none; border-radius: 4px;
            }
        """
        txt_locked = (self.current_section == "Test Reports")

        self.pdf_btn.setStyleSheet(ACTIVE if self.current_format == "PDF" else INACTIVE)
        self.pdf_btn.setEnabled(True)

        if txt_locked:
            self.txt_btn.setStyleSheet(DISABLED)
            self.txt_btn.setEnabled(False)
            self.txt_btn.setToolTip("TXT toggle not available for Test Reports")
        else:
            self.txt_btn.setEnabled(True)
            self.txt_btn.setToolTip("")
            self.txt_btn.setStyleSheet(ACTIVE if self.current_format == "TXT" else INACTIVE)         
    def on_header_clicked(self, col_key: str):
        # Find if this col is already in the chain
        existing = next((i for i, (k, _) in enumerate(self.sort_chain) if k == col_key), None)

        if existing is not None:
            key, asc = self.sort_chain[existing]
            if asc:
                # Second click: flip to descending
                self.sort_chain[existing] = (key, False)
            else:
                # Third click: remove from chain
                self.sort_chain.pop(existing)
        else:
            default_asc = col_key not in ("date", "time")
            self.sort_chain.append((col_key, default_asc))

        # Update header labels — show priority number + direction
        for key, lbl in self._header_labels.items():
            chain_index = next((i for i, (k, _) in enumerate(self.sort_chain) if k == key), None)
            if chain_index is not None:
                _, asc = self.sort_chain[chain_index]
                priority = f" {chain_index + 1}" if len(self.sort_chain) > 1 else ""
                lbl.set_sort_state(True, asc)
                lbl.setText(lbl.base_text + (lbl.ICON_ASC if asc else lbl.ICON_DESC) + priority)
            else:
                lbl.set_sort_state(False, True)

        self.load_reports()

    def load_reports(self):
        self.report_list.clear()

        # Resolve directory and glob pattern from current section/format
        if self.current_section == "Test Reports":
            target_dir = SELF_TEST_REPORTS_DIR if self.mode == "self" else PDF_TEST_REPORTS_DIR
            glob_pattern = "*.pdf"
        elif self.current_format == "PDF":
            target_dir = LOGS_PDF_DIR if self.mode == "self" else LOGS_DETAILED_DIR
            glob_pattern = "*.pdf"
        else:  # Log Files + TXT
            target_dir = LOGS_SELF_TEST_DIR if self.mode == "self" else TEST_LOGS_DIR
            glob_pattern = "*.log"

        if not target_dir.exists():
            EmptyStateDialog(
                self,
                title="Directory Missing",
                icon_path=RESOURCES_DIR / "pdf.png",
                heading="Directory not found",
                description_lines=[f"{target_dir}", "This folder does not exist yet."],
                show_tip=False,
            ).exec_()
            return

        pdf_files = sorted(target_dir.glob(glob_pattern))

        if not pdf_files:
            EmptyStateDialog(
                self,
                title="No Test Reports",
                icon_path=RESOURCES_DIR / "pdf.png",
                heading="No test reports found",
                description_lines=[
                    "There are currently no PDF reports available.",
                    "Run tests and generate reports to see them here.",
                ],
                tip_icon_path=RESOURCES_DIR / "lab.png",
                tip_title="Generate reports",
                tip_desc="Run your tests to generate PDF reports that will appear here.",
            ).exec_()
            return

        rows = []
        for pdf in pdf_files:
            date_str, time_str, test_type, status = parse_filename_metadata(pdf)
            rows.append((pdf, date_str, time_str, test_type, status))
        # Apply search filter
        if self.search_text:
            rows = [r for r in rows if self.search_text in r[0].name.lower()]

        # Apply ALH filter
        if self.active_filters:
            rows = [r for r in rows
                    if any(f.lower() in r[0].name.lower() for f in self.active_filters)]
        if self.sort_chain:
            import functools

            def multi_sort_key(entry):
                pdf, date_str, time_str, test_type, status = entry
                keys = []
                for col, asc in self.sort_chain:
                    if col == "name":
                        val = pdf.name.lower()
                    elif col == "date":
                        try:
                            val = datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d") if date_str != "—" else "0000-00-00"
                        except ValueError:
                            val = "0000-00-00"
                    elif col == "time":
                        val = time_str if time_str != "—" else "00:00"
                    elif col == "type":
                        val = test_type.lower()
                    elif col == "status":
                        val = {"Pass": 0, "Fail": 1, "Abort": 2, "—": 3}.get(status, 99)
                    else:
                        val = ""
                    keys.append((val, asc))
                return keys

            def comparator(a, b):
                for (va, asc), (vb, _) in zip(multi_sort_key(a), multi_sort_key(b)):
                    if va < vb:
                        return -1 if asc else 1
                    if va > vb:
                        return 1 if asc else -1
                return 0

            rows.sort(key=functools.cmp_to_key(comparator))

        for pdf, date_str, time_str, test_type, status in rows:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 48))
            item.setData(Qt.UserRole, pdf)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 6, 12, 6)
            row_layout.setSpacing(10)

            name_label = QLabel(pdf.name)
            name_label.setFont(QFont("Arial", 10))
            name_label.setStyleSheet("QLabel { color: #1a5da8; } QLabel:hover { text-decoration: underline; }")
            name_label.setCursor(Qt.PointingHandCursor)
            name_label.mousePressEvent = lambda _, p=pdf: self.open_pdf_path(p)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            row_layout.addWidget(name_label)

            for val, width, extra_style in [
                (date_str,  100, "color: #444444;"),
                (time_str,  75,  "color: #444444;"),
                (test_type, 90,  "color: #1a5da8; background-color: #e8f0fb; border-radius: 4px; padding: 2px 4px;"),
            ]:
                lbl = QLabel(val)
                lbl.setFont(QFont("Arial", 9))
                lbl.setFixedWidth(width)
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setStyleSheet(f"QLabel {{ {extra_style} }}")
                row_layout.addWidget(lbl)

            bg, fg = STATUS_COLORS.get(status, STATUS_COLORS["—"])
            status_label = QLabel(status)
            status_label.setFont(QFont("Arial", 9, QFont.Bold))
            status_label.setFixedWidth(70)
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet(f"QLabel {{ color: {fg}; background-color: {bg}; border-radius: 4px; padding: 2px 4px; }}")
            row_layout.addWidget(status_label)

            self.report_list.addItem(item)
            self.report_list.setItemWidget(item, row_widget)
    # -------------------------------------------------

    def open_pdf_path(self, pdf_path: Path):
        """Open PDF in default system viewer"""
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))

    def show_report_context_menu(self, pos):
        item = self.report_list.itemAt(pos)
        if item is None:
            return
        file_path = item.data(Qt.UserRole)
        if not file_path:
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: white; border: 1px solid #d0d7e2; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 20px; font-size: 10pt; }
            QMenu::item:selected { background: #e8f0fb; color: #1a5da8; }
        """)
        open_action = menu.addAction("Open")
        explorer_action = menu.addAction("Show in File Explorer")
        copy_path_action = menu.addAction("Copy File Path")

        action = menu.exec_(self.report_list.viewport().mapToGlobal(pos))

        if action == open_action:
            self.open_pdf_path(file_path)
        elif action == explorer_action:
            self.reveal_in_file_explorer(file_path)
        elif action == copy_path_action:
            QApplication.clipboard().setText(str(file_path))

    def reveal_in_file_explorer(self, file_path: Path):
        """Open the containing folder and select/highlight the file."""
        file_path = Path(file_path)
        if not file_path.exists():
            QMessageBox.warning(
                self, "File Not Found",
                f"This file no longer exists on disk:\n{file_path}"
            )
            return
        try:
            if sys.platform == "win32":
                import subprocess
                subprocess.run(["explorer", "/select,", str(file_path)])
            elif sys.platform == "darwin":
                import subprocess
                subprocess.run(["open", "-R", str(file_path)])
            else:  # Linux fallback — just open the containing folder
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path.parent)))
        except Exception as e:
            QMessageBox.warning(self, "Explorer Error", f"Could not open file location:\n{e}")

    
    # def print_pdf(self, pdf_path: Path):
    #     """Open print preview for a specific PDF"""
    #     printer = QPrinter(QPrinter.HighResolution)
    #     preview = QPrintPreviewDialog(printer, self)
    #     preview.paintRequested.connect(
    #         lambda _: QDesktopServices.openUrl(
    #             QUrl.fromLocalFile(str(pdf_path))
    #         )
    #     )
    #     preview.exec_()

    # -------------------------------------------------
    def on_back_clicked(self):
        self.return_to_test_selection.emit()
        self.close()
        
@staticmethod        
def parse_filename_metadata(pdf_path: Path):
    name = pdf_path.stem
    upper = name.upper()

    if upper.startswith("ABORT_"):
        test_type = "Abort"
    elif upper.startswith("ST_"):
        test_type = "Single"
    elif upper.startswith("FT_"):
        test_type = "Full"
    elif upper.startswith("SELF_"):
        test_type = "Self"
    else:
        test_type = "—"

    if "PASS" in upper:
        status = "Pass"
    elif "FAIL" in upper:
        status = "Fail"
    elif "ABORT" in upper:
        status = "Abort"
    else:
        status = "—"

    m = re.search(r'(\d{2})-(\d{2})-(\d{2})', name)
    if m:
        time_str = f"{m.group(1)}:{m.group(2)}:{m.group(3)}"
    else:
        m2 = re.search(r'[_-](\d{4})$', name)
        time_str = f"{m2.group(1)[:2]}:{m2.group(1)[2:]}" if m2 else "—"

    try:
        mtime = pdf_path.stat().st_mtime
        date_str = datetime.fromtimestamp(mtime).strftime("%d-%m-%Y")
    except Exception:
        date_str = "—"

    return date_str, time_str, test_type, status


STATUS_COLORS = {
    "Pass":  ("#d4edda", "#155724"),
    "Fail":  ("#f8d7da", "#721c24"),
    "Abort": ("#fff3cd", "#856404"),
    "—":     ("#f0f0f0", "#555555"),
}