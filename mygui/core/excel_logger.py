import shutil
from openpyxl import load_workbook
from db.db_paths import EXCEL_REPORT_PATH, TEST_REPORT_OUTPUT_DIR,EXCEL_REPORT_PATH_ALH4
from threading import Lock
from openpyxl.styles import PatternFill
from openpyxl.utils import column_index_from_string, get_column_letter

CURRENT_COLUMN_OFFSET = 0
CURRENT_ROW_OFFSET = 0

TEMPLATE_PATH = EXCEL_REPORT_PATH
CURRENT_REPORT_PATH = None
excel_lock = Lock()
Template_path_alh4 = EXCEL_REPORT_PATH_ALH4
ACTIVE_FILE = TEST_REPORT_OUTPUT_DIR / "active_report_path.txt"
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
    
def create_model_report(model):
    global CURRENT_REPORT_PATH

    model = model.upper()

    # =====================================================
    # 🔴 SELECT TEMPLATE BASED ON MODEL
    # =====================================================
    if model == "ALH4":
        template_path = Template_path_alh4
    else:
        template_path = TEMPLATE_PATH

    # =====================================================
    # CREATE UNIQUE FILE NAME
    # =====================================================
    base = f"test_report_{model}_"
    num = 1

    while True:
        filename = f"{base}{num:02d}.xlsx"
        new_path = TEST_REPORT_OUTPUT_DIR / filename
        if not new_path.exists():
            break
        num += 1

    # =====================================================
    # COPY CORRECT TEMPLATE
    # =====================================================
    shutil.copy(template_path, new_path)
    CURRENT_REPORT_PATH = str(new_path)

    # Save active path globally
    with open(ACTIVE_FILE, "w") as f:
        f.write(CURRENT_REPORT_PATH)

    print(f"\n📄 NEW REPORT CREATED ({model}) → {CURRENT_REPORT_PATH}\n")

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