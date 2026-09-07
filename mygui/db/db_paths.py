from pathlib import Path
import os
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent   # {app} — same folder db_paths.py's INSTALL_DIR resolves to
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = Path(__file__).resolve().parent.parent

BASE_DIR.mkdir(parents=True, exist_ok=True)

def _set_hidden(path: Path) -> None:
    """Apply the Windows FILE_ATTRIBUTE_HIDDEN flag to a folder. No-op on failure."""
    if os.name != "nt":
        return
    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        pass


# Database directory — saved inside db\database\
DATABASE_DIR = BASE_DIR / "db" / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
_set_hidden(DATABASE_DIR)


# Test report OUTPUT directory (writable)
TEST_REPORT_OUTPUT_DIR = BASE_DIR / "db" / "test report excel"
TEST_REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
_set_hidden(TEST_REPORT_OUTPUT_DIR)

# Template paths — read from bundle (inside EXE)
EXCEL_TEMPLATE_ALH1 = BUNDLE_DIR / "db" / "test_report_alh1.xlsx"
EXCEL_TEMPLATE_ALH2 = BUNDLE_DIR / "db" / "test_report_alh2.xlsx"
EXCEL_TEMPLATE_ALH3 = BUNDLE_DIR / "db" / "test_report_alh3.xlsx"
EXCEL_TEMPLATE_ALH4 = BUNDLE_DIR / "db" / "test_report_alh4.xlsx"
EXCEL_TEMPLATE_CALIBRATION = BUNDLE_DIR / "db" / "calibration_self.xlsx"
EXCEL_TEMPLATE_SELF_TEST = BUNDLE_DIR / "db" / "self_test_template.xlsx"
EXCEL_TEMPLATE_SELF_TEST_RS_ETHER = BUNDLE_DIR / "db" / "self_rs_ether.xlsx"

# Database paths — all .db files inside db\database\
CALIBRATION_DB_PATH     = DATABASE_DIR / "calibration.db"
EMPLOYEE_DB_PATH        = DATABASE_DIR / "employee_auth.db"