import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import  *
from core.paths import RESOURCES_DIR
from screens.station_box import StationBoxUI
from screens.junction_box import JunctionBoxUI

class Singletestselection(QMainWindow):
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_window = parent_window
        self.initUI()
        
    
    def initUI(self):
        """Initialize the main UI"""
        # Window configuration
        self.setWindowTitle("LRU Selection Interface")
        # self.setGeometry(0, 0, 800, 700)
        self.setFixedSize(900, 650)
        
        # Apply window styling
        self.setStyleSheet("background-color: #F4F5F7;")
        
        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout (vertical)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(10)  
        top_bar = QHBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(100,35)
        back_btn.setStyleSheet("""
        QPushButton{
        background:#ffffff;
        border:1px solid #cfd6df;
        border-radius:6px;
        font-weight:bold;
        }

        QPushButton:hover{
        background:#eef2f7;
        }
        """)

        back_btn.clicked.connect(self.go_back)

        top_bar.addWidget(back_btn)
        top_bar.addStretch()

        main_layout.addLayout(top_bar)
                
        # ===== HEADER SECTION =====
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Title label
        title_label = QLabel("Select LRU Type")
        title_font = QFont("Segoe UI")
        title_font.setPointSize(20)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #555; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("""
            QFrame{
            border:none;
            background:#d9dde3;
            max-height:1px;
            }
            """)
        divider.setMaximumHeight(1)
        header_layout.addWidget(divider)
        
        main_layout.addLayout(header_layout)
        main_layout.addStretch()
        
              
        # ===== TWO SELECTION CARDS =====
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(80)
        cards_layout.setContentsMargins(0, 40, 0, 20)
        cards_layout.addStretch()

        # Left Card - Station Box
        left_card = self.create_card(
            title="STATION BOX",
            button_text="SELECT",
            button_color="#5B76A8",
            card_type="station"
        )
        cards_layout.addWidget(left_card)

        cards_layout.addSpacing(30)

        # Right Card - Junction Box
        right_card = self.create_card(
            title="JUNCTION BOX",
            button_text="SELECT",
            button_color="#4B4F54",
            card_type="junction"
        )
        cards_layout.addWidget(right_card)

        cards_layout.addStretch()

        main_layout.addLayout(cards_layout)
        main_layout.addStretch()
        
        
      
        central_widget.setLayout(main_layout)
    def go_back(self):
        if self.parent_window:
            self.parent_window.show()
        self.close()
    
    def create_card(self, title, button_text, button_color, card_type):
        """Create a selection card with title, icon placeholder, and button"""
        card_frame = QFrame()
        card_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #D3D3D3;
            }
        """)
        card_frame.setFixedSize(360, 320)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # Title label
        title_label = QLabel(title)
        title_font = QFont("Segoe UI")
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            color:#1f2933;
            border:none;
            background:transparent;
            """)
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)
        
        # Image icon
        icon_placeholder = QLabel()

        if card_type == "station":
            img_path = str(RESOURCES_DIR / "station box.png")
        else:
            img_path = str(RESOURCES_DIR / "junction box.png")

        pixmap = QPixmap(img_path)

        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                280, 230,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        icon_placeholder.setStyleSheet("""
        QLabel{
            border:none;
            background:transparent;
        }
        """)
        icon_placeholder.setPixmap(pixmap)
        icon_placeholder.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(icon_placeholder, 1)
        
        # Select button
        select_button = QPushButton(button_text)
        select_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        select_button.setFixedHeight(40)
        select_button.setStyleSheet(f"""
                QPushButton {{
                background-color:{button_color};
                color:white;
                border-radius:6px;
                border:none;
                font-weight:bold;
                letter-spacing:1px;
                }}

                QPushButton:hover {{
                background-color:{self.lighten_color(button_color)};
                }}

                QPushButton:pressed {{
                background-color:{self.darken_color(button_color)};
                }}
                """)
        
        # Connect button click
        if card_type == "station":
            select_button.clicked.connect(self.on_station_selected)
        else:
            select_button.clicked.connect(self.on_junction_selected)
        
        card_layout.addWidget(select_button)
        card_frame.setLayout(card_layout)
        
        return card_frame
    
    def on_station_selected(self):
        """Handle Station Box selection"""
        self.station_window = StationBoxUI(parent_window=self)
        self.station_window.show()
        self.hide()
    
    def on_junction_selected(self):
        """Handle Junction Box selection"""
        self.junction_window = JunctionBoxUI(parent_window=self)
        self.junction_window.show()
        self.hide()
    
    @staticmethod
    def lighten_color(hex_color):
        """Lighten a hex color"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def darken_color(hex_color):
        """Darken a hex color"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, r - 30)
        g = max(0, g - 30)
        b = max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"


def main():
    app = QApplication(sys.argv)
    window = Singletestselection()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
