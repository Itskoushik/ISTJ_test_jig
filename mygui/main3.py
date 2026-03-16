import sys
from pathlib import Path
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox
)

from db.admin_auth import init_admin_auth_db

from screens.login_screen import LoginScreen
from screens.connection_screen import ConnectionScreen
from screens.test_selection_screen import TestSelectionScreen
from screens.test_reports_screen import TestReportsScreen
from screens.equipment_self_check_screen import EquipmentSelfCheckScreen
from screens.full_test_screen import FullTestScreen

from core.exception_handler import global_exception_handler
import sys

sys.excepthook = global_exception_handler

# ============================================================================
# DIRECTORY SETUP
# ============================================================================

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "test_reports"

for directory in [ REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

from core.paths import (
    RESOURCES_DIR
)


import sys
import traceback

def except_hook(exctype, value, tb):
    print("\n REAL ERROR TRACEBACK ")
    traceback.print_exception(exctype, value, tb)

sys.excepthook = except_hook

class HALApplication(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.main_window = None
        self.current_screen = None
        self.device_status = {}


    def show_login(self):
        """Show login screen"""
        if self.main_window is None:
            self.main_window = QMainWindow()
            self.main_window.setGeometry(100, 100, 550, 550)
            self.main_window.setWindowTitle("HAL")
            self.main_window.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
            self.main_window.setFixedSize(550, 550)
            self.main_window.setStyleSheet("background: linear-gradient(to bottom, #e0f7fa, #ffffff);")
        
        login_screen = LoginScreen()
        login_screen.login_success.connect(self.on_login_success)
        login_screen.show()
        self.current_screen = login_screen

    def on_login_success(self, name, emp_id, real_designation):
        self.logged_in_name = name
        self.logged_in_emp_id = emp_id

        # 🔒 NEVER close current screen during navigation
        if self.current_screen:
            self.current_screen.hide()

        if emp_id in ["META_ADMIN_SELF", "META_ADMIN_MASTER"]:
            from admin.meta_admin_dashboard import MetaAdminDashboard
            self.current_screen = MetaAdminDashboard(
                name,
                emp_id,
                real_designation
            )

            # 🔑 ADD THIS LINE (CRITICAL)
            self.current_screen.restart_login.connect(self.show_login)

            self.current_screen.show()
            return


        if emp_id in ["Senior Test Engineer", "Manager", "General Manager"]:
            try:
                self.current_screen = self.show_admin_dashboard(name, emp_id)
            except Exception as e:
                QMessageBox.critical(self, "Critical Error", str(e))
            return

        try:
            self.current_screen = self.show_connection(name, emp_id)
        except Exception as e:
            QMessageBox.critical(self, "Critical Error", str(e))



            
    def show_admin_dashboard(self, admin_name, designation):
        from admin.admin_dashboard import AdminDashboard
        dashboard = AdminDashboard(admin_name, designation)
        dashboard.logout_requested.connect(self.show_login)
        dashboard.show()
        return dashboard



    def show_connection(self, name, emp_id):
        """Show connection screen"""
        connection_screen = ConnectionScreen(name, emp_id)
        connection_screen.test_selection_requested.connect(self.on_connection_complete)
        connection_screen.show()
        self.current_screen = connection_screen
        return connection_screen

        

    def on_connection_complete(self):
        """Handle connection completion"""
        if self.current_screen:
            # SAVE DEVICE STATUS FROM CONNECTION SCREEN
            self.device_status = getattr(self.current_screen, "device_status", {})
            self.current_screen.close()

        self.show_test_selection()


    def show_test_selection(self):
        test_selection_screen = TestSelectionScreen()
        test_selection_screen.full_test_requested.connect(self.show_full_test)
        test_selection_screen.unit_test_requested.connect(self.show_unit_test)
        test_selection_screen.equipment_self_test_requested.connect(
            self.show_equipment_self_check
        )

        test_selection_screen.test_reports_requested.connect(
            self.show_test_reports
        )
        test_selection_screen.return_to_connection.connect(self.on_disconnect_return)

        test_selection_screen.show()
        self.current_screen = test_selection_screen


    def show_full_test(self):
        """Show full test screen"""
        if self.current_screen:
            self.current_screen.close()
        full_test_screen = FullTestScreen()
        full_test_screen.return_to_test_selection.connect(self.on_full_test_return)
        full_test_screen.return_to_connection.connect(self.on_disconnect_return)
        full_test_screen.show()
        self.current_screen = full_test_screen
        
    def on_disconnect_return(self):
        if self.current_screen:
            self.current_screen.close()

        self.show_connection(
            self.logged_in_name,
            self.logged_in_emp_id
        )


    def on_full_test_return(self):
        """Handle return from full test screen"""
        if self.current_screen:
            self.current_screen.close()
        self.show_test_selection()
    def show_equipment_self_check(self):
        """Show Equipment Self Check screen"""
        if self.current_screen:
            self.current_screen.close()

        equipment_screen = EquipmentSelfCheckScreen(device_status=self.device_status)
        equipment_screen.return_to_test_selection.connect(self.show_test_selection)
        equipment_screen.show()

        self.current_screen = equipment_screen
    def show_test_reports(self):
        if self.current_screen:
            self.current_screen.close()

        reports_screen = TestReportsScreen()
        reports_screen.return_to_test_selection.connect(self.show_test_selection)
        reports_screen.show()

        self.current_screen = reports_screen

    def show_unit_test(self):
        """Show unit test screen (placeholder)"""
        pass

if __name__ == "__main__":
    init_admin_auth_db()
    app = HALApplication()
    app.show_login()
    sys.exit(app.exec_())

