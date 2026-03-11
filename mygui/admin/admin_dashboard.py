from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QFrame, QLineEdit, QHeaderView, QAbstractItemView,
    QMessageBox, QComboBox, QFileDialog
)
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QBrush
from PyQt5.QtCore import pyqtSignal, Qt
from pathlib import Path
from datetime import datetime
import sqlite3
import win32com.client
import json
from core.paths import RESOURCES_DIR, REPORTS_DIR
from PyQt5.QtWidgets import QScrollArea

# ===============================
# PATHS
# ===============================
BASE_DIR = Path(__file__).parent
DEFAULT_PROFILE_PIC = RESOURCES_DIR / "robo.png"
XL_REPORTS_DIR = REPORTS_DIR / "xl"
PDF_REPORTS_DIR = REPORTS_DIR / "pdfs"
CONFIG_DIR = BASE_DIR / "admin_configs"
CONFIG_DIR.mkdir(exist_ok=True)


# ===============================
# ADMIN DASHBOARD
# ===============================
class AdminDashboard(QMainWindow):
    logout_requested = pyqtSignal()

    def __init__(self, admin_name: str, designation: str):
        super().__init__()
        self.admin_name = admin_name
        self.designation = designation
        
        # User settings (in-memory + config file)
        self.user_settings = self._load_settings()
        self.profile_pixmap = None

        self.pending_actions_pending = set()
        self.pending_actions_approved = set()

        self.setWindowTitle("HAL – Admin Dashboard")
        self.setGeometry(80, 80, 1600, 950)
        self.setMinimumSize(1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f7fa, stop:1 #ffffff);
            }
        """)

        # Create main container with sidebar + content layout
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Add sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Create content area (header + content)
        self.content_wrapper = QWidget()
        self.content_layout = QVBoxLayout(self.content_wrapper)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Initialize database first
        self._init_db()

        # Add main content (non-scrollable, fitted)
        self.main_content = QWidget()
        main_root = QVBoxLayout(self.main_content)
        main_root.setContentsMargins(35, 25, 35, 30)
        main_root.setSpacing(18)
        main_root.addWidget(self._create_main_area())
        self._refresh_tables()

        main_root.addStretch(0)
        

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.main_content)

        self.content_layout.addWidget(scroll, 1)
        main_layout.addWidget(self.content_wrapper, 1)

    # ===============================
    # SETTINGS STORAGE
    # ===============================
    def _load_settings(self):
        config_file = self._get_config_file()
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "name": self.admin_name,
            "designation": self.designation,
            "profile_image": None
        }


    def _get_config_file(self):
        safe_name = self.admin_name.lower().replace(" ", "_")
        safe_role = self.designation.lower().replace(" ", "_")
        return CONFIG_DIR / f"{safe_name}_{safe_role}.json"

    def _save_settings(self):
        config_file = self._get_config_file()
        with open(config_file, "w") as f:
            json.dump(self.user_settings, f, indent=2)

    # ===============================
    # SIDEBAR
    # ===============================
    def _create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(260)

        # IMPORTANT: scope style only to this sidebar
        sidebar.setObjectName("Sidebar")
        sidebar.setFrameShape(QFrame.NoFrame)
        sidebar.setStyleSheet("""
            QFrame#Sidebar {
                background-color: #e8f0f8;
                border-right: 1px solid #d0dce8;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 25, 20, 30)
        layout.setSpacing(15)

        # ================= Logo =================
        logo_path = RESOURCES_DIR / "hal_logo.png"
        logo_label = QLabel()
        logo_label.setStyleSheet("border: none;")
        logo_label.setAlignment(Qt.AlignHCenter)

        if logo_path.exists():
            hal_pixmap = QPixmap(str(logo_path))
            if not hal_pixmap.isNull():
                logo_label.setPixmap(
                    hal_pixmap.scaledToWidth(120, Qt.SmoothTransformation)
                )
            else:
                logo_label.setText("HAL")
                logo_label.setFont(QFont("Arial", 24, QFont.Bold))
                logo_label.setStyleSheet("color: #1a4fa3; border: none;")
        else:
            logo_label.setText("HAL")
            logo_label.setFont(QFont("Arial", 24, QFont.Bold))
            logo_label.setStyleSheet("color: #1a4fa3; border: none;")

        layout.addWidget(logo_label)

        layout.addSpacing(20)

        # ================= Profile Photo =================
        photo_size = 120
        pixmap = QPixmap(photo_size, photo_size)
        pixmap.fill(Qt.transparent)

        # 1️⃣ Admin-specific uploaded image (highest priority)
        profile_image_path = self.user_settings.get("profile_image")

        if profile_image_path and Path(profile_image_path).exists():
            original = QPixmap(profile_image_path)
            pixmap = original.scaledToWidth(photo_size, Qt.SmoothTransformation)

        # 2️⃣ Default common profile image (robo.png)
        elif DEFAULT_PROFILE_PIC.exists():
            original = QPixmap(str(DEFAULT_PROFILE_PIC))
            pixmap = original.scaledToWidth(photo_size, Qt.SmoothTransformation)

        # 3️⃣ Absolute fallback (should never happen)
        else:
            pixmap = self._create_circular_placeholder(photo_size)


        # Circular mask
        mask = QPixmap(photo_size, photo_size)
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawEllipse(0, 0, photo_size, photo_size)
        painter.end()
        pixmap.setMask(mask.createMaskFromColor(Qt.transparent))

        self.photo_label = QLabel()
        self.photo_label.setPixmap(pixmap)
        self.photo_label.setAlignment(Qt.AlignHCenter)
        self.photo_label.setStyleSheet("border: none;")
        layout.addWidget(self.photo_label)

        self.profile_pixmap = pixmap

        # ================= Name =================
        name_to_display = self.user_settings.get("name", self.admin_name)
        name_parts = name_to_display.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        self.welcome_label = QLabel(f"{first_name.capitalize()} {last_name.capitalize()}")
        self.welcome_label.setFont(QFont("Arial", 13, QFont.Bold))
        self.welcome_label.setStyleSheet("color: #1a4fa3; border: none;")
        self.welcome_label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(self.welcome_label)

        # ================= Designation =================
        designation = QLabel(self.designation)
        designation.setFont(QFont("Arial", 9))
        designation.setStyleSheet("color: #666666; border: none;")
        designation.setAlignment(Qt.AlignHCenter)
        layout.addWidget(designation)

        layout.addSpacing(25)

        # ================= Navigation =================
        self.dashboard_nav = QPushButton("DASHBOARD")
        self.dashboard_nav.setFont(QFont("Arial", 10, QFont.Bold))
        self.dashboard_nav.setCursor(Qt.PointingHandCursor)
        self.dashboard_nav.setEnabled(False)
        self.dashboard_nav.setStyleSheet("""
            QPushButton {
                background-color: #d0dce8;
                color: #1a4fa3;
                border: none;
                border-radius: 6px;
                padding: 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #c0cce0;
            }
        """)
        self.dashboard_nav.clicked.connect(self._back_to_dashboard)
        layout.addWidget(self.dashboard_nav)

        self.settings_nav = QPushButton("SETTINGS")
        self.settings_nav.setFont(QFont("Arial", 10, QFont.Bold))
        self.settings_nav.setCursor(Qt.PointingHandCursor)
        self.settings_nav.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
                padding: 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #d0dce8;
                border-radius: 6px;
            }
        """)
        self.settings_nav.clicked.connect(self._show_settings)
        layout.addWidget(self.settings_nav)

        layout.addStretch()

        # ================= Logout =================
        logout = QPushButton("Logout")
        logout.setFont(QFont("Arial", 9, QFont.Bold))
        logout.setCursor(Qt.PointingHandCursor)
        logout.setFixedHeight(40)
        logout.setStyleSheet("""
            QPushButton {
                background-color: #5a8fc8;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a7fb8;
            }
            QPushButton:pressed {
                background-color: #3a6fa8;
            }
        """)
        logout.clicked.connect(self._on_logout_clicked)
        layout.addWidget(logout)

        return sidebar


    def _create_circular_placeholder(self, size):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor("#5a8fc8")))
        painter.drawEllipse(0, 0, size, size)
        
        initials = "".join(word[0].upper() for word in self.admin_name.split())
        painter.setFont(QFont("Arial", 28, QFont.Bold))
        painter.setPen(QColor("white"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, initials)
        painter.end()
        return pixmap
    def _format_name(self, name: str) -> str:
        parts = name.strip().split()
        return " ".join(p.capitalize() for p in parts)

    def _get_button_stylesheet(self, button_type="primary"):
        """Helper method to apply consistent button styling"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3d5a7a;
                    color: white;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #2d4a6a;
                }
                QPushButton:pressed {
                    background-color: #1d3a5a;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """
        }
        return styles.get(button_type, styles["primary"])
    
    def _show_settings(self):
        # Update nav buttons
        self.dashboard_nav.setEnabled(True)
        self.settings_nav.setEnabled(False)
        self.dashboard_nav.setStyleSheet("""
            QPushButton {
            background-color: transparent;
            color: #666666;
            border: none;
            padding: 10px;
            text-align: left;
            }
            QPushButton:hover {
            background-color: #d0dce8;
            border-radius: 6px;
            }
        """)
        self.settings_nav.setStyleSheet("""
            QPushButton {
            background-color: #d0dce8;
            color: #1a4fa3;
            border: none;
            border-radius: 6px;
            padding: 10px;
            text-align: left;
            }
            QPushButton:hover {
            background-color: #c0cce0;
            }
        """)
        
        # Clear and replace content
        while self.content_layout.count():
            widget = self.content_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        settings_widget = self._create_settings_view()
        self.content_layout.addWidget(settings_widget, 1)
        

    def _back_to_dashboard(self):
        # Update nav buttons
        self.dashboard_nav.setEnabled(False)
        self.settings_nav.setEnabled(True)
        self.dashboard_nav.setStyleSheet("""
            QPushButton {
            background-color: #d0dce8;
            color: #1a4fa3;
            border: none;
            border-radius: 6px;
            padding: 10px;
            text-align: left;
            }
            QPushButton:hover {
            background-color: #c0cce0;
            }
        """)
        self.settings_nav.setStyleSheet("""
            QPushButton {
            background-color: transparent;
            color: #666666;
            border: none;
            padding: 10px;
            text-align: left;
            }
            QPushButton:hover {
            background-color: #d0dce8;
            border-radius: 6px;
            }
        """)
        
        # Clear and replace content
        while self.content_layout.count():
            widget = self.content_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        main_content = QWidget()
        main_root = QVBoxLayout(main_content)
        main_root.setContentsMargins(35, 25, 35, 30)
        main_root.setSpacing(18)
        main_root.addWidget(self._create_main_area())
        self._refresh_tables()
        main_root.addStretch(0)
        
        self.content_layout.addWidget(main_content, 1)
        

    # ===============================
    # SETTINGS VIEW
    # ===============================
    def _create_settings_view(self):
        settings = QWidget()
        layout = QVBoxLayout(settings)
        layout.setContentsMargins(35, 25, 35, 30)
        layout.setSpacing(20)

        # Title
        header = QLabel("Settings")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #1a3a5c;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Main content area with white background
        content = QWidget()
        content.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        content.setMaximumWidth(500)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(40, 30, 40, 30)
        content_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # ========== PROFILE IMAGE SECTION ==========
        profile_title = QLabel("Profile Picture")
        profile_title.setFont(QFont("Arial", 11, QFont.Bold))
        profile_title.setStyleSheet("color: #1a3a5c;")
        profile_title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(profile_title)

        # Current profile image display
        self.settings_photo_label = QLabel()
        self.settings_photo_label.setAlignment(Qt.AlignCenter)
        self.settings_photo_label.setFixedSize(120, 120)
        if self.profile_pixmap:
            self.settings_photo_label.setPixmap(self.profile_pixmap)
        elif DEFAULT_PROFILE_PIC.exists():
            self.settings_photo_label.setPixmap(
                QPixmap(str(DEFAULT_PROFILE_PIC)).scaledToWidth(120, Qt.SmoothTransformation)
            )
        content_layout.addWidget(self.settings_photo_label, alignment=Qt.AlignCenter)

        upload_btn = QPushButton("Upload Profile Picture")
        upload_btn.setFixedWidth(200)
        upload_btn.setFixedHeight(36)
        upload_btn.setFont(QFont("Arial", 9, QFont.Bold))
        upload_btn.setCursor(Qt.PointingHandCursor)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #5a8fc8;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4a7fb8;
            }
            QPushButton:pressed {
                background-color: #3a6fa8;
            }
        """)
        upload_btn.clicked.connect(self._upload_profile_picture)
        content_layout.addWidget(upload_btn, alignment=Qt.AlignCenter)

        content_layout.addSpacing(20)

        # ========== ACTION BUTTONS ==========
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 0, 0, 0)

        save_btn = QPushButton("Save Settings")
        save_btn.setFixedWidth(160)
        save_btn.setFixedHeight(38)
        save_btn.setFont(QFont("Arial", 9, QFont.Bold))
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
            background-color: #4caf50;
            color: white;
            border: none;
            border-radius: 5px;
            }
            QPushButton:hover {
            background-color: #45a049;
            }
            QPushButton:pressed {
            background-color: #3d8b40;
            }
        """)
        save_btn.clicked.connect(self._save_settings_action)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addStretch()

        content_layout.addLayout(button_layout)

        # Add content to main layout with centering
        content_wrapper = QWidget()
        wrapper_layout = QHBoxLayout(content_wrapper)
        wrapper_layout.addStretch()
        wrapper_layout.addWidget(content)
        wrapper_layout.addStretch()
        
        layout.addWidget(content_wrapper, 1)

        return settings

    def _upload_profile_picture(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Picture",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "Error", "Failed to load image")
                return
            
            # Scale to 120x120
            scaled = pixmap.scaledToWidth(120, Qt.SmoothTransformation)
            
            # Create circular mask
            mask = QPixmap(120, 120)
            mask.fill(Qt.transparent)
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(Qt.white)
            painter.drawEllipse(0, 0, 120, 120)
            painter.end()
            scaled.setMask(mask.createMaskFromColor(Qt.transparent))
            
            # Update display
            self.settings_photo_label.setPixmap(scaled)
            self.profile_pixmap = scaled
            
            # Store path in settings
            self.user_settings["profile_image"] = file_path

    def _save_settings_action(self):
        """
        Save admin settings safely.
        Currently supports:
        - Profile picture
        - Persisted admin name (already known)
        """

        # Ensure name always exists (fallback safety)
        self.user_settings["name"] = self.user_settings.get("name", self.admin_name)

        # Save to config file
        self._save_settings()

        # Update sidebar name
        name_to_display = self.user_settings.get("name", self.admin_name)
        name_parts = name_to_display.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        self.welcome_label.setText(f"{first_name.capitalize()} {last_name.capitalize()}")

        # Update sidebar profile photo
        if self.profile_pixmap:
            self.photo_label.setPixmap(self.profile_pixmap)
        elif DEFAULT_PROFILE_PIC.exists():
            self.photo_label.setPixmap(
                QPixmap(str(DEFAULT_PROFILE_PIC)).scaledToWidth(120, Qt.SmoothTransformation)
            )

        QMessageBox.information(self, "Success", "Settings saved successfully!")


    # ===============================
    # MAIN AREA
    # ===============================
    def _create_main_area(self):
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Welcome heading
        formatted_name = self._format_name(self.user_settings.get("name", self.admin_name))
        header = QLabel(f"Welcome {formatted_name}")

        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #1a3a5c;")
        header.setMaximumHeight(35)
        layout.addWidget(header)

        # Search + Filter row
        search_filter_layout = QHBoxLayout()
        search_filter_layout.setContentsMargins(0, 0, 0, 0)
        search_filter_layout.setSpacing(10)

        # 🔹 Push everything to the RIGHT
        search_filter_layout.addStretch()

        # Search field
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search reports...")
        self.search_bar.setFixedHeight(38)
        self.search_bar.setFixedWidth(260)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d5d5d5;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #5a8fc8;
                background-color: #fafbfc;
            }
        """)
        self.search_bar.textChanged.connect(self._filter_tables)
        search_filter_layout.addWidget(self.search_bar)

        # Filter dropdown
        filter_combo = QComboBox()
        filter_combo.addItems(["All", "Pending", "Approved"])
        filter_combo.setFixedHeight(38)
        filter_combo.setFixedWidth(140)
        filter_combo.setFont(QFont("Arial", 9))
        filter_combo.setStyleSheet("""
            QComboBox {
            border: 1px solid #d5d5d5;
            border-radius: 6px;
            padding: 8px 12px;
            background-color: #ffffff;
            font-size: 9pt;
            }
            QComboBox::drop-down {
            border: none;
            }
            QComboBox:focus {
            border: 1px solid #5a8fc8;
            background-color: #fafbfc;
            }
        """)
        filter_combo.currentTextChanged.connect(self._filter_by_status)
        search_filter_layout.addWidget(filter_combo)

        layout.addLayout(search_filter_layout)



        # ========== PENDING SECTION ==========
        pending_title = QLabel("PENDING TEST REPORTS")
        pending_title.setFont(QFont("Arial", 10, QFont.Bold))
        pending_title.setStyleSheet("color: #1a3a5c;")
        pending_title.setMaximumHeight(20)
        layout.addWidget(pending_title)

        layout.addWidget(self._create_pending_table())

        # Save Pending button
        save_pending_layout = QHBoxLayout()
        save_pending_layout.setContentsMargins(0, 0, 0, 0)
        save_pending_layout.setSpacing(0)
        save_pending_layout.addStretch()
        self.save_pending_btn = QPushButton("Save pending")
        self.save_pending_btn.setFixedWidth(200)
        self.save_pending_btn.setFixedHeight(38)
        self.save_pending_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.save_pending_btn.setCursor(Qt.PointingHandCursor)
        self.save_pending_btn.setStyleSheet(self._get_button_stylesheet("primary"))
        self.save_pending_btn.clicked.connect(
            lambda: self._save_approvals(self.pending_actions_pending)
        )
        save_pending_layout.addWidget(self.save_pending_btn)
        save_pending_layout.addStretch()
        layout.addLayout(save_pending_layout)

        layout.addSpacing(12)

        # ========== APPROVED SECTION ==========
        approved_title = QLabel("APPROVED TEST REPORTS")
        approved_title.setFont(QFont("Arial", 10, QFont.Bold))
        approved_title.setStyleSheet("color: #1a3a5c;")
        approved_title.setMaximumHeight(20)
        layout.addWidget(approved_title)

        layout.addWidget(self._create_approved_table())

        # Save Approved button
        save_approved_layout = QHBoxLayout()
        save_approved_layout.setContentsMargins(0, 0, 0, 0)
        save_approved_layout.setSpacing(0)
        save_approved_layout.addStretch()
        self.save_approved_btn = QPushButton("Save Approved")
        self.save_approved_btn.setFixedWidth(200)
        self.save_approved_btn.setFixedHeight(38)
        self.save_approved_btn.setFont(QFont("Arial", 9, QFont.Bold))
        self.save_approved_btn.setCursor(Qt.PointingHandCursor)
        self.save_approved_btn.setStyleSheet(self._get_button_stylesheet("primary"))
        self.save_approved_btn.clicked.connect(
            lambda: self._save_approvals(self.pending_actions_approved)
        )
        save_approved_layout.addWidget(self.save_approved_btn)
        save_approved_layout.addStretch()
        layout.addLayout(save_approved_layout)

        return main

    # ===============================
    # TABLE SETUP
    # ===============================
    def _create_pending_table(self):
        self.pending_table = QTableWidget(0, 4)
        self.pending_table.setHorizontalHeaderLabels(
            ["Engineer", "Report Name", "Status", "Action"]
        )
        self._table_common(self.pending_table)
        
        return self.pending_table

    def _create_approved_table(self):
        self.approved_table = QTableWidget(0, 5)
        self.approved_table.setHorizontalHeaderLabels(
            ["Engineer", "Report Name", "Status", "Priority", "Action"]
        )
        self._table_common(self.approved_table)
       
        return self.approved_table

    def _table_common(self, table):
        table.setMinimumHeight(300)
        table.verticalHeader().setVisible(False)
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setStretchLastSection(True)
        
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setWordWrap(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.itemClicked.connect(self._on_report_clicked)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)

        table.setColumnWidth(0, 100)
        table.setColumnWidth(1, 220)
        table.setColumnWidth(2, 280)
        if table.columnCount() == 5:
            table.setColumnWidth(3, 80)
            table.setColumnWidth(4, 100)

        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background-color: #ffffff;
                gridline-color: #f0f0f0;
                alternate-background-color: #f9fafb;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #4caf50;
                color: white;
            }
            QHeaderView::section {
                background-color: #f5f6fa;
                color: #1a3a5c;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 9pt;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        table.setAlternatingRowColors(True)

    # ===============================
    # DATABASE
    # ===============================
    def _init_db(self):
        from db.db_paths import ADMIN_DASHBOARD_DB_PATH
        self.conn = sqlite3.connect(ADMIN_DASHBOARD_DB_PATH)

        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS approvals (
                report_name TEXT PRIMARY KEY,
                senior_approved INTEGER DEFAULT 0,
                manager_approved INTEGER DEFAULT 0,
                gm_approved INTEGER DEFAULT 0,
                pdf_generated INTEGER DEFAULT 0,
                last_updated TEXT
            )
        """)
        self.conn.commit()

    # ===============================
    # REFRESH TABLES
    # ===============================
    def _refresh_tables(self):
        self.pending_table.setRowCount(0)
        self.approved_table.setRowCount(0)
        self.pending_actions_pending.clear()
        self.pending_actions_approved.clear()

        c = self.conn.cursor()

        for file in XL_REPORTS_DIR.glob("*.xls*"):
            report = file.stem

            c.execute("""
                SELECT senior_approved, manager_approved, gm_approved, pdf_generated
                FROM approvals WHERE report_name=?
            """, (report,))
            row = c.fetchone()

            if not row:
                c.execute("INSERT INTO approvals(report_name) VALUES(?)", (report,))
                self.conn.commit()
                s = m = g = pdf = 0
            else:
                s, m, g, pdf = row

            if s and m and g and pdf:
                continue

            status_lines = []
            if s: status_lines.append("• Approved by Senior Test Engineer")
            if m: status_lines.append("• Approved by Manager")
            if g: status_lines.append("• Approved by General Manager")
            status = "\n".join(status_lines) if status_lines else "Pending"

            priority = "HIGH" if g else ("MODERATE" if m else "NORMAL")

            if s or m or g:
                self._add_approved_row(report, status, priority, s, m, g)
            else:
                self._add_pending_row(report)

        self.pending_table.resizeRowsToContents()
        self.approved_table.resizeRowsToContents()

    # ===============================
    # ROW HELPERS
    # ===============================
    def _report_item(self, report):
        item = QTableWidgetItem(report)
        item.setForeground(QColor("#0052cc"))
        item.setFont(QFont("Arial", 9, QFont.Bold))
        return item

    def _add_pending_row(self, report):
        r = self.pending_table.rowCount()
        self.pending_table.insertRow(r)
        
        engineer_item = QTableWidgetItem("Test Engineer")
        engineer_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.pending_table.setItem(r, 0, engineer_item)
        
        self.pending_table.setItem(r, 1, self._report_item(report))
        
        status_item = QTableWidgetItem("Pending")
        status_item.setFont(QFont("Arial", 9))
        status_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.pending_table.setItem(r, 2, status_item)

        btn = QPushButton("Approve")
        btn.setFixedHeight(34)
        btn.setFont(QFont("Arial", 8, QFont.Bold))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        btn.clicked.connect(lambda _, b=btn, r=report: self._toggle(b, r, True))
        self.pending_table.setCellWidget(r, 3, btn)

    def _add_approved_row(self, report, status, priority, s, m, g):
        r = self.approved_table.rowCount()
        self.approved_table.insertRow(r)
        
        engineer_item = QTableWidgetItem("Test Engineer")
        engineer_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.approved_table.setItem(r, 0, engineer_item)
        
        self.approved_table.setItem(r, 1, self._report_item(report))
        
        status_item = QTableWidgetItem(status)

        # 🔹 Ensure multiline rendering
        status_item.setTextAlignment(Qt.AlignLeft | Qt.AlignTop)
        status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
        status_item.setFont(QFont("Arial", 9))
        status_item.setToolTip(status)  # hover shows full text

        self.approved_table.setItem(r, 2, status_item)

        # 🔹 Auto-adjust row height based on content
        self.approved_table.resizeRowToContents(r)


        priority_item = QTableWidgetItem(priority)
        priority_item.setFont(QFont("Arial", 9, QFont.Bold))
        priority_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.approved_table.setItem(r, 3, priority_item)

        if self._can_approve(s, m, g):
            btn = QPushButton("Approve")
            btn.setFixedHeight(34)
            btn.setFont(QFont("Arial", 8, QFont.Bold))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            btn.clicked.connect(lambda _, b=btn, r=report: self._toggle(b, r, False))
            self.approved_table.setCellWidget(r, 4, btn)
        else:
            view = QPushButton("View")
            view.setFixedHeight(34)
            view.setFont(QFont("Arial", 8, QFont.Bold))
            view.setCursor(Qt.PointingHandCursor)
            view.setStyleSheet("""
                QPushButton {
                    background-color: #5a8fc8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #4a7fb8;
                }
                QPushButton:pressed {
                    background-color: #3a6fa8;
                }
            """)
            view.clicked.connect(lambda _, r=report: self._open_excel_readonly(r))
            self.approved_table.setCellWidget(r, 4, view)

    def _toggle(self, btn, report, is_pending):
        target = self.pending_actions_pending if is_pending else self.pending_actions_approved
        if btn.text() == "Approve":
            btn.setText("Cancel")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #e68900;
                }
                QPushButton:pressed {
                    background-color: #cc7a00;
                }
            """)
            target.add(report)
        else:
            btn.setText("Approve")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
            target.discard(report)

    # ===============================
    # APPROVAL PERMISSION CHECK (CORE – DO NOT MODIFY)
    # ===============================
    def _can_approve(self, s, m, g):
        return (
            (self.designation == "Senior Test Engineer" and not s) or
            (self.designation == "Manager" and not m) or
            (self.designation == "General Manager" and not g)
        )

    # ===============================
    # SAVE + PDF
    # ===============================
    def _save_approvals(self, reports):
        if not reports:
            return

        c = self.conn.cursor()
        col = {
            "Senior Test Engineer": "senior_approved",
            "Manager": "manager_approved",
            "General Manager": "gm_approved"
        }[self.designation]

        for report in list(reports):
            c.execute(
                f"UPDATE approvals SET {col}=1, last_updated=? WHERE report_name=?",
                (datetime.now().isoformat(), report)
            )

            c.execute("""
                SELECT senior_approved, manager_approved, gm_approved, pdf_generated
                FROM approvals WHERE report_name=?
            """, (report,))
            s, m, g, pdf_done = c.fetchone()

            if s and m and g and not pdf_done:
                reply = QMessageBox.question(
                    self,
                    "Final Approval",
                    f"All approvals completed for:\n\n{report}\n\nGenerate PDF?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    if self._convert_excel_to_pdf(report):
                        QMessageBox.information(
                            self, "PDF Generated", f"{report}.pdf created"
                        )
                        c.execute(
                            "UPDATE approvals SET pdf_generated=1, last_updated=? WHERE report_name=?",
                            (datetime.now().isoformat(), report)
                        )
                else:
                    # 🔥 ROLLBACK CURRENT USER APPROVAL
                    c.execute(
                        f"UPDATE approvals SET {col}=0 WHERE report_name=?",
                        (report,)
                    )
                    reports.discard(report)  # reset UI toggle state


        self.conn.commit()
        self._refresh_tables()

    # ===============================
    # EXCEL → PDF
    # ===============================
    def _convert_excel_to_pdf(self, report):
        xlsx = XL_REPORTS_DIR / f"{report}.xlsx"
        pdf = PDF_REPORTS_DIR / f"{report}.pdf"
        PDF_REPORTS_DIR.mkdir(exist_ok=True)

        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        try:
            wb = excel.Workbooks.Open(str(xlsx), ReadOnly=True)
            wb.ExportAsFixedFormat(0, str(pdf))
            wb.Close(False)
            return True
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", str(e))
            return False
        finally:
            excel.Quit()

    # ===============================
    # READ ONLY EXCEL
    # ===============================
    def _open_excel_readonly(self, report):
        path = XL_REPORTS_DIR / f"{report}.xlsx"
        if not path.exists():
            return

        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = True
        excel.DisplayAlerts = False

        wb = excel.Workbooks.Open(str(path), ReadOnly=True)
        wb.Protect(Structure=True, Windows=True)
        for sh in wb.Sheets:
            sh.Protect()

        excel.CommandBars("Worksheet Menu Bar").Controls("File").Enabled = False

    def _on_report_clicked(self, item):
        if item.column() == 1:
            self._open_excel_readonly(item.text())

    def _filter_tables(self):
        text = self.search_bar.text().lower()
        for table in (self.pending_table, self.approved_table):
            for i in range(table.rowCount()):
                table.setRowHidden(i, text not in table.item(i, 1).text().lower())

    def _filter_by_status(self, status):
        """Filter tables by approval status"""
        for i in range(self.pending_table.rowCount()):
            show = (status == "All" or status == "Pending")
            self.pending_table.setRowHidden(i, not show)
        
        for i in range(self.approved_table.rowCount()):
            show = (status == "All" or status == "Approved")
            self.approved_table.setRowHidden(i, not show)

    def _on_logout_clicked(self):
        self.logout_requested.emit()
        self.close()
