from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QUrl
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from pathlib import Path

from core.paths import PDF_TEST_REPORTS_DIR



class TestReportsScreen(QMainWindow):
    return_to_test_selection = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HAL - Test Reports")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet("background-color: #f5f5f5;")

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

        # Right spacer (keeps title perfectly centered)
        header_layout.addSpacing(110)

        layout.addWidget(header_frame)



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


        layout.addWidget(self.report_list)
        self.load_reports()


    # -------------------------------------------------
    def load_reports(self):
        self.report_list.clear()

        if not PDF_TEST_REPORTS_DIR.exists():
            QMessageBox.warning(self, "Error", "PDF reports directory not found.")
            return

        pdf_files = sorted(PDF_TEST_REPORTS_DIR.glob("*.pdf"))

        if not pdf_files:
            QMessageBox.information(self, "No Test Reports", "No test reports found.")
            return

        for pdf in pdf_files:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 48))

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(12, 6, 12, 6)
            row_layout.setSpacing(10)

            # 📄 File name (clickable)
            name_label = QLabel(pdf.name)
            name_label.setFont(QFont("Arial", 10))
            name_label.setStyleSheet("""
                QLabel {
                    color: #1a5da8;
                }
                QLabel:hover {
                    text-decoration: underline;
                }
            """)
            name_label.setCursor(Qt.PointingHandCursor)
            name_label.mousePressEvent = lambda _, p=pdf: self.open_pdf_path(p)
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # 🖨 Print button
            print_btn = QPushButton("Print")
            print_btn.setFixedSize(90, 32)
            print_btn.setFont(QFont("Arial", 9, QFont.Bold))
            print_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a5da8;
                    color: white;
                    border-radius: 4px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #154a8a;
                }
            """)
            print_btn.clicked.connect(lambda _, p=pdf: self.print_pdf(p))

            row_layout.addWidget(name_label)
            row_layout.addWidget(print_btn)

            self.report_list.addItem(item)
            self.report_list.setItemWidget(item, row_widget)
    # -------------------------------------------------
    def open_pdf_path(self, pdf_path: Path):
        """Open PDF in default system viewer"""
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf_path)))
    
    def print_pdf(self, pdf_path: Path):
        """Open print preview for a specific PDF"""
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(
            lambda _: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(pdf_path))
            )
        )
        preview.exec_()

    # -------------------------------------------------
    def on_back_clicked(self):
        self.return_to_test_selection.emit()
        self.close()
