from pathlib import Path
import os
import sys

# Detect if running as EXE or Python
if getattr(sys, "frozen", False):
    BASE_DIR = Path(os.getenv("LOCALAPPDATA")) / "HAL_Testing"
else:
    BASE_DIR = Path(__file__).resolve().parent

BASE_DIR.mkdir(parents=True, exist_ok=True)

# Database directory
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# Test report directory
TEST_REPORT_OUTPUT_DIR = BASE_DIR / "test_report_excel"
TEST_REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Excel report files
EXCEL_REPORT_PATH = TEST_REPORT_OUTPUT_DIR / "test_report_alh123.xlsx"
EXCEL_REPORT_PATH_ALH4 = TEST_REPORT_OUTPUT_DIR / "test_report_alh4.xlsx"

# Database paths
ADMIN_DB_PATH = DATABASE_DIR / "admin_auth.db"
ADMIN_DASHBOARD_DB_PATH = DATABASE_DIR / "admin_dashboard.db"
CALIBRATION_DB_PATH = DATABASE_DIR / "calibration.db"
EMPLOYEE_DB_PATH = DATABASE_DIR / "employee_auth.db"