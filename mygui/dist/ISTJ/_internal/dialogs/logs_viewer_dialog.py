from PyQt5.QtGui import QFont, QTextDocument
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QMessageBox, QFileDialog
)
from PyQt5.QtCore import QSizeF

from PyQt5.QtPrintSupport import QPrinter
from datetime import datetime
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor


from core.paths import LOGS_DETAILED_DIR



class LogsViewerDialog(QDialog):
    """
    Dialog window to view detailed logs and export them to PDF.
    """

    def __init__(self, parent=None, logs_text="", logs_data=None):
        super().__init__(parent)

        self.setWindowTitle("Detailed Logs Viewer")
        self.setMinimumSize(QSize(950, 650))
        self.setStyleSheet("background-color: #ffffff;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ✅ Title
        title = QLabel("Detailed Test Logs")
        title.setFont(QFont("Arial", 13, QFont.Bold))
        title.setStyleSheet("color: #1a5da8;")
        main_layout.addWidget(title)

        # ✅ Logs text box FIRST
        self.logs_box = QTextEdit()
        self.logs_box.setReadOnly(True)
        self.logs_box.setFont(QFont("Courier", 9))
        self.logs_box.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 10px;
                background-color: #fafbfc;
                color: #111827;
            }
        """)
        main_layout.addWidget(self.logs_box)

        # ✅ Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.pdf_btn = QPushButton("📄 Generate PDF")
        self.pdf_btn.setMinimumHeight(42)
        self.pdf_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 16px;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:pressed { background-color: #0d47a1; }
        """)
        self.pdf_btn.clicked.connect(self.generate_pdf)
        btn_layout.addWidget(self.pdf_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("❌ Close")
        self.close_btn.setMinimumHeight(42)
        self.close_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 16px;
            }
            QPushButton:hover { background-color: #b71c1c; }
            QPushButton:pressed { background-color: #8e0000; }
        """)
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        main_layout.addLayout(btn_layout)

        # ✅ NOW insert logs (after logs_box exists)
        if logs_data:
            self.set_colored_logs_from_data(logs_data)
        else:
            self.set_colored_logs(logs_text)

    def set_colored_logs_from_data(self, logs_data):
        self.logs_box.clear()
        cursor = self.logs_box.textCursor()
        cursor.movePosition(QTextCursor.Start)

        normal_fmt = QTextCharFormat()
        normal_fmt.setForeground(QColor("#1b5e20"))

        error_fmt = QTextCharFormat()
        error_fmt.setForeground(QColor("#d32f2f"))
        error_fmt.setFontWeight(QFont.Bold)

        for ts, msg, err in logs_data:
            fmt = error_fmt if err else normal_fmt
            cursor.insertText(f"[{ts}] {msg}\n", fmt)

        self.logs_box.moveCursor(QTextCursor.End)
        
    def set_colored_logs(self, logs_text: str):
        """
        Insert logs as plain text but color lines:
        - Errors in RED
        - Normal in GREEN
        """
        self.logs_box.clear()

        cursor = self.logs_box.textCursor()
        cursor.movePosition(QTextCursor.Start)

        normal_fmt = QTextCharFormat()
        normal_fmt.setForeground(QColor("#1b5e20"))  # green

        error_fmt = QTextCharFormat()
        error_fmt.setForeground(QColor("#d32f2f"))   # red
        error_fmt.setFontWeight(QFont.Bold)

        for line in logs_text.splitlines():
            is_error = any(key in line.upper() for key in [
                "ERROR", "FAILED", "DISCONNECTED", "ABORT", "✗"
            ])

            fmt = error_fmt if is_error else normal_fmt

            cursor.insertText(line + "\n", fmt)

        # ✅ auto scroll to bottom
        self.logs_box.moveCursor(QTextCursor.End)




    def generate_pdf(self):
        default_name = f"HAL_Test_Logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        default_path = str(LOGS_DETAILED_DIR / default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Logs as PDF",
            default_path,
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return
        if not file_path.lower().endswith(".pdf"):
            file_path += ".pdf"

        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)

            printer.setPaperSize(QPrinter.A4)
            printer.setPageMargins(12, 12, 12, 12, QPrinter.Millimeter)

            # ✅ page rect
            page_rect = printer.pageRect(QPrinter.DevicePixel)
            page_size = QSizeF(page_rect.size())

            # ✅ Build a fresh doc (NO HTML)
            doc = QTextDocument()
            doc.setDefaultFont(QFont("Courier New", 11))
            doc.setPageSize(page_size)

            cursor = QTextCursor(doc)

            # formats
            normal_fmt = QTextCharFormat()
            normal_fmt.setForeground(QColor("#1b5e20"))

            error_fmt = QTextCharFormat()
            error_fmt.setForeground(QColor("#d32f2f"))
            error_fmt.setFontWeight(QFont.Bold)

            # ✅ READ CURRENT LOG TEXT LINE BY LINE
            for line in self.logs_box.toPlainText().splitlines():
                is_error = any(k in line.upper() for k in ["ERROR", "FAILED", "DISCONNECTED", "ABORT", "✗"])
                cursor.insertText(line + "\n", error_fmt if is_error else normal_fmt)

            # ✅ IMPORTANT: match printable width
            doc.setTextWidth(page_size.width())

            # ✅ print
            doc.print_(printer)

            QMessageBox.information(
                self,
                "PDF Generated",
                f"✅ PDF saved successfully:\n{file_path}\n\nOpening PDF now..."
            )
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

        except Exception as e:
            QMessageBox.critical(self, "PDF Export Failed", f"❌ Failed to generate PDF:\n{e}")
