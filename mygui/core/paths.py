from pathlib import Path
import os
import sys

if getattr(sys, "frozen", False):
    INSTALL_DIR = Path(sys.executable).parent   # {app} — wherever the user installed it, now writable
    BASE_DIR    = INSTALL_DIR                    # single source of truth — no more AppData split
    BUNDLE_DIR  = Path(sys._MEIPASS)
else:
    INSTALL_DIR = Path(__file__).resolve().parent.parent
    BASE_DIR    = Path(__file__).resolve().parent.parent
    BUNDLE_DIR  = BASE_DIR

# ✅ Read from install dir — written by Inno Setup, never by the app
RESOURCES_DIR = BUNDLE_DIR  / "resourses"

# ✅ Write to AppData — runtime logs, reports, session
LOGS_DIR               = BASE_DIR / "logs" / "connection logs"
TEST_LOGS_DIR          = BASE_DIR / "logs" / "test_logs"
CALIBRATION_LOGS_DIR    = BASE_DIR / "logs" / "calibration_logs"
LOGS_DETAILED_DIR      = BASE_DIR / "logs" / "logs_detailed"
LOGS_PDF_DIR           = BASE_DIR / "logs" / "logs_pdf"
LOGS_SELF_TEST_DIR      = BASE_DIR / "logs" / "logs_self_test"
REPORTS_DIR            = BASE_DIR / "test_reports"
CALIBRATION_REPORTS_DIR = REPORTS_DIR / "calibration_reports"
PDF_TEST_REPORTS_DIR   = REPORTS_DIR / "pdfs"
SELF_TEST_REPORTS_DIR  = REPORTS_DIR / "self-test-reports"
EXCEL_TEST_REPORTS_DIR = REPORTS_DIR / "xl"


# ── Calibration report sub-dirs (mirrors REPORTS_DIR structure) ──
EXCEL_CALIBRATION_REPORTS_DIR = CALIBRATION_REPORTS_DIR / "xl"
PDF_CALIBRATION_REPORTS_DIR   = CALIBRATION_REPORTS_DIR / "pdfs"

SESSION_FILE           = BASE_DIR / "session.txt"
APP_DIR                = BASE_DIR / "app_data"  # For any other app data needs (e.g. temp files)

# Only create writable dirs — ADMIN_DIR is created by the installer
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


# Only create writable dirs — ADMIN_DIR is created by the installer
for d in [LOGS_DIR, TEST_LOGS_DIR, CALIBRATION_LOGS_DIR, LOGS_DETAILED_DIR, LOGS_PDF_DIR,
          LOGS_SELF_TEST_DIR, REPORTS_DIR, CALIBRATION_REPORTS_DIR, PDF_TEST_REPORTS_DIR, SELF_TEST_REPORTS_DIR, EXCEL_TEST_REPORTS_DIR,
          EXCEL_CALIBRATION_REPORTS_DIR, PDF_CALIBRATION_REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Hide test_reports (and its xl subfolder) inside {app} — same hidden behavior as before
_set_hidden(REPORTS_DIR)
_set_hidden(EXCEL_TEST_REPORTS_DIR)