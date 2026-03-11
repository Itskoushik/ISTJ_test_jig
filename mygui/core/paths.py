from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

RESOURCES_DIR = BASE_DIR / "resourses"
LOGS_DIR = BASE_DIR / "logs" / "connection logs"
LOGS_DETAILED_DIR = BASE_DIR / "logs" / "logs_detailed"
LOGS_PDF_DIR = BASE_DIR / "logs" / "logs_pdf"
REPORTS_DIR = BASE_DIR / "test_reports"
PDF_TEST_REPORTS_DIR = REPORTS_DIR / "pdfs"
SESSION_FILE = BASE_DIR / "session.txt"

for d in [RESOURCES_DIR, LOGS_DIR, REPORTS_DIR, LOGS_PDF_DIR, PDF_TEST_REPORTS_DIR,LOGS_DETAILED_DIR]:
    d.mkdir(parents=True, exist_ok=True)
