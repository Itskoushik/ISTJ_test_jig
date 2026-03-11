import traceback
from PyQt5.QtWidgets import QMessageBox


# ============================================================================
# Global Exception Handler
# ============================================================================


def global_exception_handler(exctype, value, tb):
    msg = ''.join(traceback.format_exception(exctype, value, tb))
    QMessageBox.critical(
        None,
        "Critical Error",
        "An unexpected error occurred.\n\n"
        "The application will remain open.\n"
        "Please contact the system administrator."
    )
    print(msg)

