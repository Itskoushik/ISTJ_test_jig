from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from core.paths import EXCEL_TEST_REPORTS_DIR,PDF_TEST_REPORTS_DIR
import shutil
import os
import subprocess
import sys


class TestCompletionModal(QDialog):
    def __init__(self, parent=None, report_path=None, save_as_pdf=False, result="pass"):
        super().__init__(parent)
        self.report_path = report_path
        self.save_as_pdf = save_as_pdf
        self.result = result.lower()
        banner_color = "#1b5e20" if self.result == "pass" else "#b71c1c"
        self.setWindowTitle("Test Complete")
        self.setFixedSize(620, 320)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
        """)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top green banner ──────────────────────────────────────
        banner = QFrame()
        banner.setFixedHeight(90)
        banner.setStyleSheet(f"background-color: {banner_color}; border: none;")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(24, 12, 24, 12)
        banner_layout.setSpacing(4)

        result_icon = "✓" if self.result == "pass" else "✕"
        result_text = "PASS" if self.result == "pass" else "FAIL"
        check_label = QLabel(f"{result_icon}  Test Completed  —  {result_text}")
        check_label.setFont(QFont("Arial", 15, QFont.Bold))
        check_label.setStyleSheet("color: #ffffff; background: transparent;")
        check_label.setAlignment(Qt.AlignCenter)
        banner_layout.addWidget(check_label)

        sub_label = QLabel("The test report has been generated and is ready to save.")
        sub_label.setFont(QFont("Arial", 9))
        sub_label.setStyleSheet("color: #ffcdd2; background: transparent;")
        sub_label.setAlignment(Qt.AlignCenter)
        banner_layout.addWidget(sub_label)

        root_layout.addWidget(banner)

        # ── Body ─────────────────────────────────────────────────
        body = QFrame()
        body.setStyleSheet("background-color: #f5f7fa; border: none;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(32, 24, 32, 24)
        body_layout.setSpacing(16)

        # File info box
        if self.report_path:
            file_frame = QFrame()
            file_frame.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                }
            """)
            file_layout = QHBoxLayout(file_frame)
            file_layout.setContentsMargins(14, 10, 14, 10)
            file_layout.setSpacing(10)

            icon_label = QLabel("📄")
            icon_label.setFont(QFont("Arial", 16))
            icon_label.setStyleSheet("background: transparent; border: none;")
            icon_label.setFixedWidth(28)
            file_layout.addWidget(icon_label)

            filename = os.path.basename(self.report_path)
            name_label = QLabel(filename)
            name_label.setFont(QFont("Courier", 9))
            name_label.setStyleSheet("color: #374151; background: transparent; border: none;")
            name_label.setWordWrap(False)
            file_layout.addWidget(name_label, 1)

            body_layout.addWidget(file_frame)

        # Instruction text
        instruction = QLabel("Click  Save  to choose where to store the report,\nor  Terminate  to discard it.")
        instruction.setFont(QFont("Arial", 9))
        instruction.setStyleSheet("color: #6b7280; background: transparent;")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setWordWrap(True)
        body_layout.addWidget(instruction)

        body_layout.addStretch()

        # ── Buttons ───────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        terminate_btn = QPushButton("✕  Terminate")
        terminate_btn.setMinimumHeight(40)
        terminate_btn.setFont(QFont("Arial", 10, QFont.Bold))
        terminate_btn.setCursor(Qt.PointingHandCursor)
        terminate_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #d32f2f;
                border: 1.5px solid #d32f2f;
                border-radius: 5px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #fdecea;
            }
            QPushButton:pressed {
                background-color: #f5c6c6;
            }
        """)
        terminate_btn.clicked.connect(self.reject)
        btn_layout.addWidget(terminate_btn)

        save_btn = QPushButton("💾  Save Report")
        save_btn.setMinimumHeight(40)
        save_btn.setFont(QFont("Arial", 10, QFont.Bold))
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a5da8;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background-color: #154a8a;
            }
            QPushButton:pressed {
                background-color: #0f3860;
            }
        """)
        save_btn.clicked.connect(self.on_save_clicked)
        btn_layout.addWidget(save_btn)

        body_layout.addLayout(btn_layout)
        root_layout.addWidget(body)

    def on_save_clicked(self):
        if not self.report_path:
            self.accept()
            return

        try:
            base_name = os.path.splitext(os.path.basename(self.report_path))[0]

            if self.save_as_pdf:
                # ── Convert xlsx → pdf and save to PDF_TEST_REPORTS_DIR ──
                pdf_dest = PDF_TEST_REPORTS_DIR / f"{base_name}.pdf"
                self._convert_xlsx_to_pdf(self.report_path, str(pdf_dest))
                self.accept()
            else:
                # ── Save xlsx to EXCEL_TEST_REPORTS_DIR ──
                dest = EXCEL_TEST_REPORTS_DIR / os.path.basename(self.report_path)
                if os.path.abspath(self.report_path) != os.path.abspath(str(dest)):
                    shutil.copy(self.report_path, str(dest))
                self.accept()

        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Could not save report:\n{e}")

    def _convert_xlsx_to_pdf(self, xlsx_path: str, pdf_path: str):
        """
        Convert xlsx → pdf, preserving:
        - Manual page breaks (set in Page Break Preview)
        - Header (e.g. &[File] → filename) on every sheet
        - Footer (e.g. Page &[Page] of &[Pages]) on every sheet

        Strategy (Windows):
        1. Try win32com  — uses Excel's own print engine; honours everything natively.
        2. Fall back to LibreOffice if win32com / Excel not available.

        Strategy (Linux / macOS):
        LibreOffice only (win32com is Windows-only).
        """
        import platform
        output_dir = str(PDF_TEST_REPORTS_DIR)
        xlsx_abs   = os.path.abspath(xlsx_path)
        pdf_abs    = os.path.abspath(pdf_path)

        if platform.system() == "Windows":
            # ── Attempt 1: win32com (Excel COM) ──────────────────────────────
            try:
                import win32com.client
                import pythoncom

                # Patch the file BEFORE opening in Excel so the template
                # already has correct fitToWidth/margins/headerFooter baked in.
                # Then just open and export — no PageSetup manipulation needed.
                self._patch_xlsx_for_libreoffice(xlsx_abs)  # safe to call here too

                pythoncom.CoInitialize()
                try:
                    excel = win32com.client.DispatchEx("Excel.Application")
                    excel.Visible       = False
                    excel.DisplayAlerts = False

                    wb = excel.Workbooks.Open(xlsx_abs)
                    try:
                        wb.ExportAsFixedFormat(
                            Type                 = 0,      # xlTypePDF
                            Filename             = pdf_abs,
                            Quality              = 0,      # xlQualityStandard
                            IncludeDocProperties = True,
                            IgnorePrintAreas     = False,
                            OpenAfterPublish     = False,
                        )
                    finally:
                        wb.Close(SaveChanges=False)
                        excel.Quit()
                finally:
                    pythoncom.CoUninitialize()

                return   # success

            except ImportError:
                pass     # win32com not installed → fall through
            except Exception as e:
                print(f"[PDF] win32com export failed ({e}), trying LibreOffice…")

            # ── Attempt 2: LibreOffice on Windows ────────────────────────────
            libreoffice_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
            soffice = next((p for p in libreoffice_paths if os.path.exists(p)), None)
            if not soffice:
                raise RuntimeError(
                    "Neither win32com (Excel) nor LibreOffice is available.\n"
                    "Install either Microsoft Excel + pywin32  OR  LibreOffice."
                )
            self._run_libreoffice(soffice, xlsx_abs, output_dir, pdf_abs)

        else:
            # ── Linux / macOS: LibreOffice only ──────────────────────────────
            soffice = "libreoffice"
            self._run_libreoffice(soffice, xlsx_abs, output_dir, pdf_abs)


    def _run_libreoffice(self, soffice: str, xlsx_abs: str, output_dir: str, pdf_abs: str):
        """
        Run LibreOffice headless conversion, then rename the output to pdf_abs.

        Key flags that preserve page breaks:
        --infilter="Calc MS Excel 2007 XML"
            Tells LibreOffice to load the file as Excel, not guess the format.
            This ensures the manual page-break data embedded in the xlsx is read.

        Flags intentionally NOT used:
        --printer-name / paper-size overrides → these reset the page layout and
        destroy manual breaks.  LibreOffice reads Excel's stored breaks fine
        without any extra flags.
        """
        self._patch_xlsx_for_libreoffice(xlsx_abs)
        cmd = [
            soffice,
            "--headless",
            "--norestore",
            "--nofirststartwizard",
            "--infilter=Calc MS Excel 2007 XML",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            xlsx_abs,
        ]
        result = subprocess.run(cmd, check=True, timeout=60,
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice failed:\n{result.stderr}")

        # LibreOffice saves as <original_stem>.pdf in outdir
        generated = os.path.join(
            output_dir,
            os.path.splitext(os.path.basename(xlsx_abs))[0] + ".pdf"
        )
        if os.path.abspath(generated) != os.path.abspath(pdf_abs):
            if os.path.exists(generated):
                os.replace(generated, pdf_abs)
                
    def _patch_xlsx_for_libreoffice(self, xlsx_abs: str):
        """
        Patch xlsx XML so LibreOffice produces a PDF that matches Excel exactly:
        - Correct page count  (fitToWidth instead of scale)
        - Footer "Page X of N" visible  (bottom margin must be >= footer margin)
        - Header filename visible  (scaleWithDoc/alignWithMargins flags)
        - fitToPage activated in sheetPr
        This method is a no-op if all fixes are already applied.
        """
        import zipfile, re, os

        with zipfile.ZipFile(xlsx_abs, 'r') as z:
            files = {n: z.read(n) for n in z.namelist()}

        xml = files['xl/worksheets/sheet1.xml'].decode('utf-8')
        new_xml = xml

        # ── Fix 1: Replace scale="XX" with fitToWidth="1" ──────────────────────
        # LibreOffice re-flows pages when it sees a fixed scale value,
        # ignoring manual row breaks. fitToWidth tells it to respect them.
        new_xml = re.sub(
            r'(<pageSetup\b[^/]*?)\bscale="\d+"',
            r'\1fitToWidth="1"',
            new_xml
        )

        # ── Fix 2: Activate fitToPage in sheetPr ───────────────────────────────
        # Without this flag, fitToWidth/fitToHeight in pageSetup are ignored.
        if 'pageSetUpPr' not in new_xml:
            if re.search(r'<sheetPr[\s>]', new_xml):
                new_xml = re.sub(
                    r'(<sheetPr[^>]*>)',
                    r'\1<pageSetUpPr fitToPage="1"/>',
                    new_xml
                )
            else:
                new_xml = new_xml.replace(
                    '<sheetData>',
                    '<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr><sheetData>',
                    1
                )

        # ── Fix 3: Ensure bottom margin >= footer margin ────────────────────────
        # If bottom="0" the footer sits below the physical page edge and
        # LibreOffice simply doesn't render it → "Page X of N" disappears.
        # We copy the footer margin value into bottom so the footer is inside
        # the printable area. We only do this when bottom is zero.
        def fix_margins(m):
            attrs = m.group(0)
            # Extract footer margin value
            footer_match = re.search(r'footer="([^"]+)"', attrs)
            bottom_match = re.search(r'bottom="([^"]+)"', attrs)
            if footer_match and bottom_match:
                bottom_val = float(bottom_match.group(1))
                footer_val = float(footer_match.group(1))
                if bottom_val < footer_val:
                    # Set bottom equal to old footer value, shrink footer slightly
                    attrs = re.sub(r'bottom="[^"]+"', f'bottom="{footer_val}"', attrs)
                    attrs = re.sub(r'footer="[^"]+"', 'footer="0.19685039370078741"', attrs)
            return attrs

        new_xml = re.sub(r'<pageMargins[^/]*/>', fix_margins, new_xml)

        # ── Fix 4: Ensure headerFooter has correct attributes AND footer content ──
        FOOTER_CONTENT = "&amp;C&amp;P of &amp;N"

        hf_match = re.search(r'<headerFooter[^>]*>(.*?)</headerFooter>', new_xml, re.DOTALL)
        if hf_match:
            hf_inner = hf_match.group(1)
            hf_tag   = re.search(r'<headerFooter([^>]*)>', new_xml).group(0)
            new_tag  = '<headerFooter scaleWithDoc="0" alignWithMargins="0">'
            new_xml  = new_xml.replace(hf_tag, new_tag)
            if '<oddFooter>' not in hf_inner:
                new_xml = new_xml.replace(
                    '</headerFooter>',
                    f'<oddFooter>{FOOTER_CONTENT}</oddFooter></headerFooter>',
                    1
                )
        else:
            hf_block = (
                f'<headerFooter scaleWithDoc="0" alignWithMargins="0">'
                f'<oddFooter>{FOOTER_CONTENT}</oddFooter>'
                f'</headerFooter>'
            )
            if '<pageMargins' in new_xml:
                new_xml = re.sub(r'(<pageMargins)', hf_block + r'\1', new_xml, count=1)
            else:
                new_xml = new_xml.replace('</sheetData>', '</sheetData>' + hf_block, 1)

        if new_xml == xml:
            return  # nothing changed, skip rewrite

        files['xl/worksheets/sheet1.xml'] = new_xml.encode('utf-8')

        tmp = xlsx_abs + ".patching.tmp"
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
            for name, data in files.items():
                zout.writestr(name, data)
        os.replace(tmp, xlsx_abs)