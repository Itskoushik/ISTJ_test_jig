import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook
from db.db_paths import TEST_REPORT_OUTPUT_DIR
from core.paths import EXCEL_CALIBRATION_REPORTS_DIR
from threading import Lock
from core.paths import SELF_TEST_REPORTS_DIR, EXCEL_TEST_REPORTS_DIR, LOGS_SELF_TEST_DIR, LOGS_PDF_DIR
from openpyxl.styles import PatternFill
from openpyxl.utils import column_index_from_string, get_column_letter

CURRENT_COLUMN_OFFSET = 0
CURRENT_ROW_OFFSET = 0

def _get_bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

# ✅ Templates — read from bundle
TEMPLATE_PATH_ALH1 = _get_bundle_dir() / "db" / "test_report_alh1.xlsx"
TEMPLATE_PATH_ALH2 = _get_bundle_dir() / "db" / "test_report_alh2.xlsx"
TEMPLATE_PATH_ALH3 = _get_bundle_dir() / "db" / "test_report_alh3.xlsx"
TEMPLATE_PATH_ALH4 = _get_bundle_dir() / "db" / "test_report_alh4.xlsx"
TEMPLATE_PATH_CALIBRATION = _get_bundle_dir() / "db" / "calibration_self.xlsx"
TEMPLATE_PATH_SELF_TEST = _get_bundle_dir() / "db" / "self_test_template.xlsx"
TEMPLATE_PATH_SELF_TEST_RS_ETHER = _get_bundle_dir() / "db" / "self_rs_ether.xlsx"
CURRENT_REPORT_PATH = None
CURRENT_CALIBRATION_REPORT_PATH = None
CURRENT_SELF_TEST_REPORT_PATH = None
CURRENT_SELF_TEST_LOG_PATH    = None
excel_lock = Lock()

# ✅ Ensure output dir exists before using it
TEST_REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ACTIVE_FILE = TEST_REPORT_OUTPUT_DIR / "active_report_path.txt"

EXCEL_CALIBRATION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
ACTIVE_CALIBRATION_FILE = EXCEL_CALIBRATION_REPORTS_DIR / "active_calibration_report_path.txt"
EXCEL_TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SELF_TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_SELF_TEST_DIR.mkdir(parents=True, exist_ok=True)
LOGS_PDF_DIR.mkdir(parents=True, exist_ok=True)


FAIL_FILL = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
# PASS_FILL = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")


# =========================================================
# CREATE NEW REPORT
# =========================================================
def reset_column_offset():
    global CURRENT_COLUMN_OFFSET
    CURRENT_COLUMN_OFFSET = 0
    
def next_column(step=1):
    global CURRENT_COLUMN_OFFSET
    CURRENT_COLUMN_OFFSET += step
def reset_row_offset():
    global CURRENT_ROW_OFFSET
    CURRENT_ROW_OFFSET = 0

def next_row(step=1):
    global CURRENT_ROW_OFFSET
    CURRENT_ROW_OFFSET += step
# =========================================================
# CREATE CALIBRATION REPORT (duplicate of calibration_self.xlsx)
# =========================================================
def create_calibration_report(filename: str = None):
    global CURRENT_CALIBRATION_REPORT_PATH

    if not TEMPLATE_PATH_CALIBRATION.exists():
        raise FileNotFoundError(
            f"\n❌ CALIBRATION TEMPLATE NOT FOUND: {TEMPLATE_PATH_CALIBRATION}"
        )

    if filename:
        new_path = EXCEL_CALIBRATION_REPORTS_DIR / f"{filename}.xlsx"
    else:
        base = "calibration_report_"
        num = 1
        while True:
            candidate = f"{base}{num:02d}.xlsx"
            new_path = EXCEL_CALIBRATION_REPORTS_DIR / candidate
            if not new_path.exists():
                break
            num += 1

    shutil.copy(str(TEMPLATE_PATH_CALIBRATION), str(new_path))
    CURRENT_CALIBRATION_REPORT_PATH = str(new_path)

    # ✅ Fix header/footer so openpyxl doesn't strip it on first open
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _wb = load_workbook(str(new_path))
        for _ws in _wb.worksheets:
            _ws.oddFooter.center.text = "&P of &N"
        _wb.save(str(new_path))
        _wb.close()
    except Exception as _hf_err:
        print(f"⚠ Calibration header/footer fix skipped: {_hf_err}")

    # ✅ Persist active path to disk (was missing — caused reuse logic to break)
    with open(ACTIVE_CALIBRATION_FILE, "w") as f:
        f.write(CURRENT_CALIBRATION_REPORT_PATH)
# =========================================================
def create_model_report(model):
    global CURRENT_REPORT_PATH
    model = model.upper()

    # ✅ Select template per model
    _TEMPLATE_MAP = {
        "N200 - ALH1": TEMPLATE_PATH_ALH1,
        "N200 - ALH2": TEMPLATE_PATH_ALH2,
        "N200 - ALH3": TEMPLATE_PATH_ALH3,
        "N200 - ALH4": TEMPLATE_PATH_ALH4,
    }
    template_path = _TEMPLATE_MAP.get(model, TEMPLATE_PATH_ALH1)

    # ✅ Guard — give clear error if template missing from bundle
    if not template_path.exists():
        raise FileNotFoundError(
            f"\n❌ TEMPLATE NOT FOUND: {template_path}"
            f"\n   Make sure --add-data 'db;db' is in build command"
            f"\n   And test_report_alh1/2/3/4.xlsx exist in db/"
        )
    # ✅ Create unique output filename
    base = f"test_report_{model}_"
    num  = 1
    while True:
        filename = f"{base}{num:02d}.xlsx"
        new_path = TEST_REPORT_OUTPUT_DIR / filename
        if not new_path.exists():
            break
        num += 1

    # ✅ Copy template to writable output location
    shutil.copy(str(template_path), str(new_path))
    CURRENT_REPORT_PATH = str(new_path)

    # ✅ Fix header/footer so openpyxl can parse it without stripping it
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _wb = load_workbook(str(new_path))
        for _ws in _wb.worksheets:
            _ws.oddFooter.center.text = "&P of &N"
        _wb.save(str(new_path))
        _wb.close()
    except Exception as _hf_err:
        print(f"⚠ Header/footer fix skipped: {_hf_err}")

    with open(ACTIVE_FILE, "w") as f:
        f.write(CURRENT_REPORT_PATH)
        
        
# =========================================================
# GET ACTIVE CALIBRATION REPORT PATH (SAFE)
# =========================================================
def get_active_calibration_report():
    global CURRENT_CALIBRATION_REPORT_PATH

    if CURRENT_CALIBRATION_REPORT_PATH:
        return CURRENT_CALIBRATION_REPORT_PATH

    if ACTIVE_CALIBRATION_FILE.exists():
        CURRENT_CALIBRATION_REPORT_PATH = ACTIVE_CALIBRATION_FILE.read_text().strip()
        print("📂 Loaded active calibration report:", CURRENT_CALIBRATION_REPORT_PATH)
        return CURRENT_CALIBRATION_REPORT_PATH

    print("❌ No active calibration report found")
    return None
def write_excel_calibration(cell, value):
    """Same as write_excel(), but targets the active CALIBRATION report."""
    print(f"write excel (calibration) {cell} , {value}")
    path = get_active_calibration_report()
    if not path:
        print("❌ No calibration report path available for writing")
        return

    if callable(value):
        value = value()

    try:
        with excel_lock:
            wb = load_workbook(path)
            ws = wb.active

            existing = ws[cell].value
            if existing and str(existing).upper() == "FAIL":
                print(f"⛔ Cannot overwrite FAIL in {cell}")
                wb.close()
                return

            print(f"✏ Writing → {cell} = {value}")
            ws[cell] = value
            if str(value).upper() == "FAIL":
                ws[cell].fill = FAIL_FILL
            wb.save(path)
            wb.close()

    except Exception as e:
        print("❌ Excel write error (calibration):", e)
# =========================================================
# GET ACTIVE REPORT PATH (SAFE)
# =========================================================
def get_active_report():
    global CURRENT_REPORT_PATH

    if CURRENT_REPORT_PATH:
        
        return CURRENT_REPORT_PATH

    # load from file if not in memory
    if ACTIVE_FILE.exists():
        CURRENT_REPORT_PATH = ACTIVE_FILE.read_text().strip()
        print("📂 Loaded active report:", CURRENT_REPORT_PATH)
        return CURRENT_REPORT_PATH

    print("❌ No active report found")
    return None

# =========================================================
# RENAME REPORT WITH FINAL NAME
# =========================================================
def rename_report(new_name: str) -> str:
    """
    Rename the active report file to new_name.
    Returns the new path string, or old path if rename fails.
    """
    global CURRENT_REPORT_PATH

    path = get_active_report()
    if not path:
        return path

    try:
        old_path = Path(path)
        new_path = old_path.parent / f"{new_name}.xlsx"

        # avoid overwrite — append counter if exists
        counter = 1
        while new_path.exists():
            new_path = old_path.parent / f"{new_name}_{counter}.xlsx"
            counter += 1

        old_path.rename(new_path)
        CURRENT_REPORT_PATH = str(new_path)

        with open(ACTIVE_FILE, "w") as f:
            f.write(CURRENT_REPORT_PATH)

        print(f"📝 REPORT RENAMED → {CURRENT_REPORT_PATH}")
        return CURRENT_REPORT_PATH

    except Exception as e:
        print(f"❌ Rename failed: {e}")
        return path
    
def has_any_fail_in_report() -> bool:
    """
    Scan the active report workbook for any cell containing 'FAIL'.
    Returns True if at least one FAIL found, False otherwise.
    """
    path = get_active_report()
    if not path:
        print("❌ No report path available for scanning")
        return False

    try:
        with excel_lock:
            wb = load_workbook(path)
            ws = wb.active

            for row in ws.iter_rows():
                for cell in row:
                    if cell.value and str(cell.value).strip().upper() == "FAIL":
                        print(f"❌ FAIL found at cell {cell.coordinate}")
                        wb.close()
                        return True

            wb.close()
            print("✅ No FAIL found in report")
            return False

    except Exception as e:
        print(f"❌ Error scanning report: {e}")
        return False
# =========================================================
# WRITE TO EXCEL
# =========================================================
def write_excel(cell, value):
    print(f"write excel {cell} , {value}")
    path = get_active_report()
    if not path:
        print("❌ No report path available for writing")
        return

    if callable(value):
        value = value()

    try:
        with excel_lock:
            wb = load_workbook(path)
            ws = wb.active

            existing = ws[cell].value
            if existing and str(existing).upper() == "FAIL":
                print(f"⛔ Cannot overwrite FAIL in {cell}")
                wb.close()
                return

            print(f"✏ Writing → {cell} = {value}")
            ws[cell] = value
            # 🔴 APPLY RED FILL IF FAIL
            if str(value).upper() == "FAIL":
                ws[cell].fill = FAIL_FILL
            # # 🟢 PASS → GREEN
            # elif str(value).upper() == "PASS":
            #     ws[cell].fill = PASS_FILL
            wb.save(path)
            wb.close()

    except Exception as e:
        print("❌ Excel write error:", e)

def write_excel_dynamic(base_cell, value):

    global CURRENT_COLUMN_OFFSET
    global CURRENT_ROW_OFFSET

    col_letters = ''.join(filter(str.isalpha, base_cell))
    row_numbers = ''.join(filter(str.isdigit, base_cell))

    base_col_index = column_index_from_string(col_letters)
    base_row = int(row_numbers)

    # apply offsets
    new_col_index = base_col_index + CURRENT_COLUMN_OFFSET
    new_row = base_row + CURRENT_ROW_OFFSET

    new_col_letter = get_column_letter(new_col_index)

    new_cell = f"{new_col_letter}{new_row}"

    write_excel(new_cell, value)
# =========================================================
# FINAL SAVE
# =========================================================
def finalize_report():
    path = get_active_report()
    if not path:
        return

    try:
        with excel_lock:
            wb = load_workbook(path)
            wb.save(path)
            wb.close()
            print(f"💾 FINAL REPORT SAVED: {path}")
    except Exception as e:
        print("❌ Final save error:", e)
        
# =========================================================
# SELF-TEST REPORT — CREATE / WRITE / FINALIZE / LOG
# =========================================================

RS_ETHER_DEVICES = {"ETHERNET", "RS232", "RS422"}

def create_self_test_report(device_name: str) -> str:
    global CURRENT_SELF_TEST_REPORT_PATH

    is_rs_ether = device_name.upper() in RS_ETHER_DEVICES
    template_path = TEMPLATE_PATH_SELF_TEST_RS_ETHER if is_rs_ether else TEMPLATE_PATH_SELF_TEST

    if not template_path.exists():
        raise FileNotFoundError(
            f"\n❌ SELF-TEST TEMPLATE NOT FOUND: {template_path}"
        )

    safe = device_name.replace(" ", "_").replace("(", "").replace(")", "")
    ts   = datetime.now().strftime("%d%m%Y_%H%M%S")
    dest = EXCEL_TEST_REPORTS_DIR / f"SELF_{safe}_TEMP_{ts}.xlsx"
    shutil.copy(str(template_path), str(dest))
    CURRENT_SELF_TEST_REPORT_PATH = str(dest)

    # ✅ Fix header so openpyxl doesn't strip it, and replace &[File] with proper title
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _wb = load_workbook(str(dest))
        for _ws in _wb.worksheets:
            _ws.oddHeader.center.text = "HAL Testing – Self Test Report"
            _ws.oddHeader.center.size = 12
            _ws.oddFooter.center.text = "&P of &N"
        _wb.save(str(dest))
        _wb.close()
    except Exception as _hf_err:
        print(f"⚠ Self-test header/footer fix skipped: {_hf_err}")

    print(f"[SELF-TEST] Report created ({'RS/ETHER' if is_rs_ether else 'STANDARD'} template): {dest}")
    return CURRENT_SELF_TEST_REPORT_PATH


def write_self_test_excel(cell: str, value, sheet_name: str = "Sheet2"):
    """Write a single cell into the active self-test report."""
    path = CURRENT_SELF_TEST_REPORT_PATH
    if not path:
        print(f"[SELF-TEST EXCEL] No active report — skipping {cell}={value}")
        return
    try:
        with excel_lock:
            wb = load_workbook(path)
            ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb.active
            ws[cell] = value
            if str(value).upper() == "FAIL":
                ws[cell].fill = FAIL_FILL
            wb.save(path)
            wb.close()
        print(f"[SELF-TEST EXCEL] {cell} = {value}")
    except Exception as e:
        print(f"[SELF-TEST EXCEL] write error {cell}={value}: {e}")

# =========================================================
# SELF-TEST LOG (.txt) — CREATE / APPEND / FINALIZE
# =========================================================

def create_self_test_log(device_name: str) -> str:
    """
    Create a temp .log/.txt file for live self-test logging.
    Mirrors create_self_test_report's temp-file pattern.
    """
    safe = device_name.replace(" ", "_").replace("(", "").replace(")", "")
    ts   = datetime.now().strftime("%d%m%Y_%H%M%S")
    dest = LOGS_SELF_TEST_DIR / f"SELF_{safe}_TEMP_{ts}.log"
    dest.touch()
    print(f"[SELF-TEST LOG] Temp log created: {dest}")
    return str(dest)


def append_self_test_log(log_path: str, line: str):
    """Append a single already-formatted line to the live self-test log file."""
    if not log_path:
        return
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[SELF-TEST LOG] append failed: {e}")


def finalize_self_test_report(device_name: str, result: str, log_lines: list):
    """
    Write PASS/FAIL into the active self-test xlsx, finalize it, rename it to
    SELF_<DEVICE>_<PASS/FAIL>_<DATE>_<TIME>.xlsx, then convert that exact file
    to PDF (preserving header/footer/page breaks) into LOGS_PDF_DIR... actually
    into SELF_TEST_REPORTS_DIR per the report-pdf naming convention, and return
    (xlsx_path, pdf_path).
    """
    global CURRENT_SELF_TEST_REPORT_PATH
    from core.paths import PDF_TEST_REPORTS_DIR
    import platform

    path = CURRENT_SELF_TEST_REPORT_PATH
    if not path or not Path(path).exists():
        print("[SELF-TEST] No active self-test report to finalize")
        return None, None

    safe = device_name.replace(" ", "_").replace("(", "").replace(")", "")
    ts   = datetime.now().strftime("%d%m%Y_%H%M")
    safe = device_name.replace(" ", "_").replace("(", "").replace(")", "")
    ts   = datetime.now().strftime("%d%m%Y_%H%M")
    final_xlsx = EXCEL_TEST_REPORTS_DIR / f"SELF_TEST_{safe}_{result}_{ts}.xlsx"

    # ── Step 1: Save current state at temp path ───────────────────────────
    try:
        with excel_lock:
            wb = load_workbook(path)
            wb.save(path)
            wb.close()
    except Exception as e:
        print(f"[SELF-TEST] finalize save failed: {e}")

    # ── Step 2: Rename temp → final ───────────────────────────────────────
    try:
        counter = 1
        candidate = final_xlsx
        while candidate.exists():
            candidate = EXCEL_TEST_REPORTS_DIR / f"SELF_TEST_{safe}_{result}_{ts}_{counter}.xlsx"
            counter += 1
        final_xlsx = candidate
        Path(path).rename(final_xlsx)
        CURRENT_SELF_TEST_REPORT_PATH = str(final_xlsx)
    except Exception as e:
        print(f"[SELF-TEST] rename failed: {e}")
        final_xlsx = Path(path)

    # ── Step 3: Patch header with final filename (file exists now) ────────
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _hdr_wb = load_workbook(str(final_xlsx))
        for _hdr_ws in _hdr_wb.worksheets:
            _hdr_ws.oddHeader.center.text = final_xlsx.stem
            _hdr_ws.oddHeader.center.size = 11
        _hdr_wb.save(str(final_xlsx))
        _hdr_wb.close()
        print(f"[SELF-TEST] Header updated → {final_xlsx.stem}")
    except Exception as _hf:
        print(f"[SELF-TEST] Header update skipped: {_hf}")

    # ── Step 4: Convert to PDF ────────────────────────────────────────────
    final_pdf = SELF_TEST_REPORTS_DIR / f"{final_xlsx.stem}.pdf"
    try:
        from dialogs.test_completion_dialog import TestCompletionModal
        _dummy = TestCompletionModal.__new__(TestCompletionModal)
        _dummy._patch_xlsx_for_libreoffice(str(final_xlsx.resolve()))

        xlsx_abs = str(final_xlsx.resolve())
        pdf_abs  = str(final_pdf.resolve())

        if platform.system() == "Windows":
            try:
                import win32com.client, pythoncom
                pythoncom.CoInitialize()
                try:
                    excel = win32com.client.DispatchEx("Excel.Application")
                    excel.Visible = False
                    excel.DisplayAlerts = False
                    wb = excel.Workbooks.Open(xlsx_abs)
                    try:
                        wb.ExportAsFixedFormat(
                            Type=0, Filename=pdf_abs, Quality=0,
                            IncludeDocProperties=True, IgnorePrintAreas=False,
                            OpenAfterPublish=False,
                        )
                    finally:
                        wb.Close(SaveChanges=False)
                        excel.Quit()
                finally:
                    pythoncom.CoUninitialize()
            except Exception as e:
                print(f"[SELF-TEST PDF] win32com failed ({e}), trying LibreOffice…")
                _run_libreoffice_for_self_test(xlsx_abs, str(SELF_TEST_REPORTS_DIR), pdf_abs)
        else:
            _run_libreoffice_for_self_test(xlsx_abs, str(SELF_TEST_REPORTS_DIR), pdf_abs)
    except Exception as e:
        print(f"[SELF-TEST PDF] conversion failed: {e}")
        final_pdf = None

    return str(final_xlsx), (str(final_pdf) if final_pdf else None)


def _run_libreoffice_for_self_test(xlsx_abs: str, output_dir: str, pdf_abs: str):
    import subprocess, os as _os
    cmd = [
        "libreoffice" if sys.platform != "win32" else _find_soffice_windows(),
        "--headless", "--norestore", "--nofirststartwizard",
        "--infilter=Calc MS Excel 2007 XML",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        xlsx_abs,
    ]
    result = subprocess.run(cmd, check=True, timeout=60, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice failed:\n{result.stderr}")
    generated = _os.path.join(output_dir, Path(xlsx_abs).stem + ".pdf")
    if _os.path.abspath(generated) != _os.path.abspath(pdf_abs) and _os.path.exists(generated):
        _os.replace(generated, pdf_abs)


def _find_soffice_windows():
    for p in [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]:
        if Path(p).exists():
            return p
    raise RuntimeError("LibreOffice not found")
