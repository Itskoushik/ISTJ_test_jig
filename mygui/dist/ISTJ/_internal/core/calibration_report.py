"""
core/calibration_report.py

Handles the "Print Calibration Report" workflow:
  1. Create a fresh calibration report excel (duplicate of calibration_self.xlsx)
     via excel_writer.create_calibration_report().
  2. Write each device's Last Calibrated / Due date into that excel using
     excel_writer.write_excel_calibration() — cell mapping is centralized in
     DEVICE_CELL_MAP below so it's a one-place edit later.
  3. Convert the excel to PDF (win32com -> LibreOffice fallback, with the same
     xml patching used for test reports, so page breaks/headers/footers survive).
  4. Try to print the PDF via the OS print dialog (user picks the printer).
     If the dialog is cancelled or printing isn't available, fall back to
     opening the PDF in the default viewer.
"""

import os
import re
import json
import platform
import subprocess
import zipfile
from datetime import date
from pathlib import Path

from core.paths import PDF_CALIBRATION_REPORTS_DIR, EXCEL_CALIBRATION_REPORTS_DIR
from core.excel_logger import (   
    create_calibration_report,
    write_excel_calibration,
    get_active_calibration_report,
)


class CalibrationReportError(Exception):
    """Raised when calibration report generation, conversion, or printing fails."""
    pass


# =========================================================
# CELL MAPPING — edit this when the real template layout is known
# =========================================================
# Each device maps to (last_date_cell, due_date_cell) in calibration_self.xlsx.
# Row 1 is assumed to be headers; devices occupy rows 2-6, column B = Last,
# column C = Due. Change freely — nothing else needs to change when you do.
DEVICE_CELL_MAP = {
    "PSU (Power Supply)":       ("H6", "I6"),
    "Audio Analyzer":           ("H8", "I8"),
    "ISTJ":                     ("H14", "I14"),
    "DMM (Digital Multimeter)": ("H10", "I10"),
    "Oscilloscope":             ("H12", "I12"),
}

REPORT_BASENAME = "calibration_summary_CB"


def _fmt(d: date) -> str:
    return d.strftime("%d-%m-%Y")


def _fingerprint(calibration_data: dict) -> dict:
    """
    Build a stable, comparable snapshot of the data that ends up in the
    report. Two calls with identical calibration_data produce identical
    fingerprints, regardless of dict ordering.
    """
    return {
        device: {
            "last": _fmt(data["last"]),
            "due": _fmt(data["due"]),
        }
        for device, data in sorted(calibration_data.items())
        if device in DEVICE_CELL_MAP
    }


def _existing_cb_numbers() -> list:
    """Return sorted list of existing CB numbers, e.g. [1, 2, 3]."""
    pattern = re.compile(rf"^{re.escape(REPORT_BASENAME)}(\d+)\.xlsx$")
    nums = []
    for f in EXCEL_CALIBRATION_REPORTS_DIR.glob(f"{REPORT_BASENAME}*.xlsx"):
        m = pattern.match(f.name)
        if m:
            nums.append(int(m.group(1)))
    return sorted(nums)


def _find_matching_report(fingerprint: dict):
    """
    Look at the most recent existing CB report's fingerprint sidecar.
    If it matches the current fingerprint, return its xlsx path (so we can
    reuse/reprint it without creating a new numbered file).
    Returns None if no match (including: no reports exist yet).
    """
    nums = _existing_cb_numbers()
    if not nums:
        return None

    latest_num = nums[-1]
    latest_xlsx = EXCEL_CALIBRATION_REPORTS_DIR / f"{REPORT_BASENAME}{latest_num:02d}.xlsx"
    sidecar = latest_xlsx.with_suffix(".json")

    if not sidecar.exists():
        return None

    try:
        stored = json.loads(sidecar.read_text())
    except Exception:
        return None

    if stored == fingerprint:
        return latest_xlsx
    return None


# =========================================================
# STEP 1 + 2 — create (or reuse) report, write all device dates into it
# =========================================================
def populate_calibration_report(calibration_data: dict) -> str:
    """
    calibration_data: same shape as EquipmentSelfCheckScreen.calibration_data,
    i.e. {"PSU (Power Supply)": {"last": date(...), "due": date(...)}, ...}

    If the current data matches the most recently generated report, reuse
    that exact file (so repeated clicks with no changes don't pile up new
    numbered reports). Otherwise create the next calibration_summary_CB##
    and write every known device's Last/Due date into it.
    """
    fingerprint = _fingerprint(calibration_data)

    existing = _find_matching_report(fingerprint)
    if existing:
        global_path = str(existing)
        # Make sure excel_logger treats this as the active file too,
        # in case anything else writes to it later in the same session.
        from core import excel_logger
        excel_logger.CURRENT_CALIBRATION_REPORT_PATH = global_path
        with open(excel_logger.ACTIVE_CALIBRATION_FILE, "w") as f:
            f.write(global_path)
        return global_path

    nums = _existing_cb_numbers()
    next_num = (nums[-1] + 1) if nums else 1
    filename = f"{REPORT_BASENAME}{next_num:02d}"

    create_calibration_report(filename=filename)  # sets the new file as active

    for device_name, cells in DEVICE_CELL_MAP.items():
        data = calibration_data.get(device_name)
        if not data:
            continue
        last_cell, due_cell = cells
        write_excel_calibration(last_cell, _fmt(data["last"]))
        write_excel_calibration(due_cell, _fmt(data["due"]))

    new_path = get_active_calibration_report()

    # Save the fingerprint sidecar so future clicks can detect "no change"
    sidecar = Path(new_path).with_suffix(".json")
    sidecar.write_text(json.dumps(fingerprint, indent=2))

    return new_path


# =========================================================
# STEP 3 — convert to PDF (win32com -> LibreOffice fallback)
# =========================================================
def convert_calibration_to_pdf(xlsx_path: str) -> Path:
    xlsx_path = Path(xlsx_path)
    base_name = xlsx_path.stem
    pdf_path = PDF_CALIBRATION_REPORTS_DIR / f"{base_name}.pdf"

    xlsx_abs = str(xlsx_path.resolve())
    pdf_abs = str(pdf_path.resolve())
    output_dir = str(PDF_CALIBRATION_REPORTS_DIR)

    if platform.system() == "Windows":
        try:
            import win32com.client
            import pythoncom

            _patch_xlsx_for_libreoffice(xlsx_abs)

            pythoncom.CoInitialize()
            try:
                excel = win32com.client.DispatchEx("Excel.Application")
                excel.Visible = False
                excel.DisplayAlerts = False

                wb = excel.Workbooks.Open(xlsx_abs)
                try:
                    wb.ExportAsFixedFormat(
                        Type=0,
                        Filename=pdf_abs,
                        Quality=0,
                        IncludeDocProperties=True,
                        IgnorePrintAreas=False,
                        OpenAfterPublish=False,
                    )
                finally:
                    wb.Close(SaveChanges=False)
                    excel.Quit()
            finally:
                pythoncom.CoUninitialize()

            return pdf_path

        except ImportError:
            pass
        except Exception as e:
            print(f"[Calibration PDF] win32com export failed ({e}), trying LibreOffice…")

        libreoffice_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        soffice = next((p for p in libreoffice_paths if os.path.exists(p)), None)
        if not soffice:
            raise CalibrationReportError(
                "Neither win32com (Excel) nor LibreOffice is available.\n"
                "Install either Microsoft Excel + pywin32  OR  LibreOffice."
            )
        _run_libreoffice(soffice, xlsx_abs, output_dir, pdf_abs)

    else:
        _run_libreoffice("libreoffice", xlsx_abs, output_dir, pdf_abs)

    return pdf_path


def _run_libreoffice(soffice: str, xlsx_abs: str, output_dir: str, pdf_abs: str):
    _patch_xlsx_for_libreoffice(xlsx_abs)
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
    result = subprocess.run(cmd, check=True, timeout=60, capture_output=True, text=True)
    if result.returncode != 0:
        raise CalibrationReportError(f"LibreOffice failed:\n{result.stderr}")

    generated = os.path.join(
        output_dir,
        os.path.splitext(os.path.basename(xlsx_abs))[0] + ".pdf"
    )
    if os.path.abspath(generated) != os.path.abspath(pdf_abs):
        if os.path.exists(generated):
            os.replace(generated, pdf_abs)


def _patch_xlsx_for_libreoffice(xlsx_abs: str):
    with zipfile.ZipFile(xlsx_abs, 'r') as z:
        files = {n: z.read(n) for n in z.namelist()}

    sheet_key = 'xl/worksheets/sheet1.xml'
    if sheet_key not in files:
        return

    xml = files[sheet_key].decode('utf-8')
    new_xml = xml

    new_xml = re.sub(
        r'(<pageSetup\b[^/]*?)\bscale="\d+"',
        r'\1fitToWidth="1"',
        new_xml
    )

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

    def fix_margins(m):
        attrs = m.group(0)
        footer_match = re.search(r'footer="([^"]+)"', attrs)
        bottom_match = re.search(r'bottom="([^"]+)"', attrs)
        if footer_match and bottom_match:
            bottom_val = float(bottom_match.group(1))
            footer_val = float(footer_match.group(1))
            if bottom_val < footer_val:
                attrs = re.sub(r'bottom="[^"]+"', f'bottom="{footer_val}"', attrs)
                attrs = re.sub(r'footer="[^"]+"', 'footer="0.19685039370078741"', attrs)
        return attrs

    new_xml = re.sub(r'<pageMargins[^/]*/>', fix_margins, new_xml)

    FOOTER_CONTENT = "&amp;C&amp;P of &amp;N"
    hf_match = re.search(r'<headerFooter[^>]*>(.*?)</headerFooter>', new_xml, re.DOTALL)
    if hf_match:
        hf_inner = hf_match.group(1)
        hf_tag = re.search(r'<headerFooter([^>]*)>', new_xml).group(0)
        new_tag = '<headerFooter scaleWithDoc="0" alignWithMargins="0">'
        new_xml = new_xml.replace(hf_tag, new_tag)
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
        return

    files[sheet_key] = new_xml.encode('utf-8')

    tmp = xlsx_abs + ".patching.tmp"
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for name, data in files.items():
            zout.writestr(name, data)
    os.replace(tmp, xlsx_abs)


# =========================================================
# STEP 4 — print via OS dialog, fallback to opening PDF
# =========================================================
def print_or_open_pdf(pdf_path: Path):
    """
    Windows: try ShellExecuteW with 'print' verb (more reliable than os.startfile).
    If that fails or no printer is set up, fall back to opening the PDF normally.
    Non-Windows: open directly (no reliable cross-platform print dialog for PDF).
    """
    pdf_str = str(pdf_path.resolve())

    if platform.system() == "Windows":
        try:
            import ctypes
            # ShellExecuteW returns > 32 on success
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,       # hwnd
                "print",    # verb
                pdf_str,    # file
                None,       # parameters
                None,       # directory
                1,          # SW_SHOWNORMAL
            )
            if ret > 32:
                return
            print(f"[Calibration Report] ShellExecute 'print' returned {ret}, opening PDF instead.")
        except Exception as e:
            print(f"[Calibration Report] Print failed ({e}), opening PDF instead.")
        _open_with_default_viewer(pdf_path)
    else:
        _open_with_default_viewer(pdf_path)


def _open_with_default_viewer(path: Path):
    path_str = str(path)
    try:
        if platform.system() == "Windows":
            os.startfile(path_str)
        elif platform.system() == "Darwin":
            subprocess.run(["open", path_str], check=True)
        else:
            subprocess.run(["xdg-open", path_str], check=True)
    except Exception as e:
        raise CalibrationReportError(f"Could not open PDF viewer for {path_str}: {e}")


# =========================================================
# PUBLIC ENTRY POINT
# =========================================================
def generate_and_print_calibration_report(calibration_data: dict) -> Path:
    """
    Full pipeline: create+populate calibration excel -> convert to PDF
    -> print (OS dialog) or fall back to opening the PDF.
    Returns the final PDF path. Raises CalibrationReportError on failure.
    """
    xlsx_path = populate_calibration_report(calibration_data)
    pdf_path = convert_calibration_to_pdf(xlsx_path)
    print_or_open_pdf(pdf_path)
    return pdf_path