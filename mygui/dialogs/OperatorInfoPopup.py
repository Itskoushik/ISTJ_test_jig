from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QSize, QTimer

class _SpaceSafeButton(QPushButton):
    """QPushButton that ignores the Space key entirely (never auto-clicks
    on Space) while Enter/click behavior stays normal. Needed because
    QAbstractButton consumes Space itself before a parent dialog's
    keyPressEvent ever sees it."""
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            event.ignore()
            return
        super().keyPressEvent(event)
        
class OperatorInfoPopup(QDialog):
    def __init__(self, title, message, image_path=None, buttons="ok",
                 timer_seconds=None, rich_html=False, image_size=420, parent=None):
        super().__init__(parent)
        self.result_status = None
        self.operator_response = None
        self.timer_seconds = timer_seconds
        self.timer = None
        self.remaining_time = None
        self._image_size = image_size   # ← controls image display size

        self.setWindowTitle(title)
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumWidth(600)
        self.setStyleSheet("QDialog { border: none; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # TITLE
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_label.setStyleSheet("color: #0b1c2d;")
        main_layout.addWidget(title_label)

        # COUNTDOWN TIMER
        if self.timer_seconds is not None:
            self.remaining_time = self.timer_seconds
            self.timer_label = QLabel(str(self.remaining_time))
            self.timer_label.setAlignment(Qt.AlignCenter)
            self.timer_label.setFont(QFont("Segoe UI", 32, QFont.Bold))
            self.timer_label.setStyleSheet("color: #444;")
            main_layout.addWidget(self.timer_label)

            self.timer = QTimer(self)
            self.timer.timeout.connect(self._update_timer)
            self.timer.start(1000)

        # IMAGE (OPTIONAL)
        if image_path:
            image_label = QLabel()
            pixmap = QPixmap(str(image_path))
            if not pixmap.isNull():
                # image_size controls popup image display size (default 420)
                img_size = getattr(self, '_image_size', 420)
                image_label.setPixmap(
                    pixmap.scaled(QSize(img_size, img_size), Qt.KeepAspectRatio,
                                  Qt.SmoothTransformation)
                )
                image_label.setAlignment(Qt.AlignCenter)
                main_layout.addWidget(image_label)

        # MESSAGE
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignLeft)
        self.message_label.setFont(QFont("Segoe UI", 11))
        self.message_label.setStyleSheet("color: #1a1a1a; padding: 6px 4px;")
        main_layout.addWidget(self.message_label)

        # DYNAMIC LABEL (only created when rich_html=True)
        self.dynamic_label = None
        if rich_html:
            self.dynamic_label = QLabel("")
            self.dynamic_label.setAlignment(Qt.AlignLeft)
            self.dynamic_label.setFont(QFont("Segoe UI", 11))
            self.dynamic_label.setWordWrap(True)
            self.dynamic_label.setTextFormat(Qt.RichText)
            self.dynamic_label.setMinimumHeight(80)
            self.dynamic_label.setStyleSheet(
                "padding: 8px; border: 1px solid #e0e0e0; border-radius: 4px;"
                "background-color: #fafafa;"
            )
            main_layout.addWidget(self.dynamic_label)

                # BUTTONS
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if buttons == "yes_no":
            self.yes_btn = _SpaceSafeButton("Yes")
            self.yes_btn.setFixedSize(120, 38)
            self.yes_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.yes_btn.setFocusPolicy(Qt.StrongFocus)
            self.yes_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2e7d32; color: white;
                    border: 1px solid #1b5e20; border-radius: 2px;
                }
                QPushButton:hover { background-color: #1b5e20; }
            """)
            self.yes_btn.clicked.connect(self._on_yes)

            self.no_btn = _SpaceSafeButton("No")
            self.no_btn.setFixedSize(120, 38)
            self.no_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.no_btn.setFocusPolicy(Qt.StrongFocus)
            self.no_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f; color: white;
                    border: 1px solid #b71c1c; border-radius: 2px;
                }
                QPushButton:hover { background-color: #b71c1c; }
            """)
            self.no_btn.clicked.connect(self._on_no)

            btn_layout.addWidget(self.yes_btn)
            btn_layout.addWidget(self.no_btn)
            self.yes_btn.setFocus()

        elif buttons == "acknowledge":
            self.ack_btn = _SpaceSafeButton("I Acknowledge")
            self.ack_btn.setFixedSize(160, 38)
            self.ack_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.ack_btn.setFocusPolicy(Qt.StrongFocus)
            self.ack_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0b3d91; color: white;
                    border: 1px solid #082c66; border-radius: 2px;
                }
                QPushButton:hover { background-color: #082c66; }
            """)
            self.ack_btn.clicked.connect(self.accept)
            btn_layout.addWidget(self.ack_btn)
            self.ack_btn.setFocus()

        else:  # OK
            self.ok_btn = _SpaceSafeButton("OK")
            self.ok_btn.setFixedSize(120, 38)
            self.ok_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.ok_btn.setFocusPolicy(Qt.StrongFocus)
            self.ok_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0b3d91; color: white;
                    border: 1px solid #082c66; border-radius: 2px;
                }
                QPushButton:hover { background-color: #082c66; }
            """)
            self.ok_btn.clicked.connect(self.accept)
            btn_layout.addWidget(self.ok_btn)
            self.ok_btn.setFocus()

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def _update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.timer_label.setText(str(self.remaining_time))
        else:
            self.timer.stop()
            
    def keyPressEvent(self, event):
        key = event.key()

        # Escape must NOT close/reject the popup — operator threads are
        # blocked on Event.wait() and nothing else will ever unblock them.
        if key == Qt.Key_Escape:
            event.ignore()
            return

        # Enter/Return activates whichever button currently has focus.
        if key in (Qt.Key_Return, Qt.Key_Enter):
            focused = self.focusWidget()
            if isinstance(focused, QPushButton):
                focused.click()
            elif hasattr(self, "yes_btn"):
                self.yes_btn.click()
            elif hasattr(self, "ack_btn"):
                self.ack_btn.click()
            elif hasattr(self, "ok_btn"):
                self.ok_btn.click()
            return

        # Left/Right/Up/Down swap focus between Yes and No (no-op for OK-only popups).
        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            if hasattr(self, "yes_btn") and hasattr(self, "no_btn"):
                if self.yes_btn.hasFocus():
                    self.no_btn.setFocus()
                else:
                    self.yes_btn.setFocus()
            return

        # Tab / Shift+Tab move focus normally.
        if key == Qt.Key_Tab:
            self.focusNextChild()
            return
        if key == Qt.Key_Backtab:
            self.focusPreviousChild()
            return

        super().keyPressEvent(event)
        
    def _on_yes(self):
        if self.timer:
            self.timer.stop()
        self.result_status = "PASS"
        self.operator_response = "YES"
        self.done(QDialog.Accepted)

    def _on_no(self):
        if self.timer:
            self.timer.stop()
        self.result_status = "FAIL"
        self.operator_response = "NO"
        self.done(QDialog.Rejected)

    def get_result(self):
        return self.result_status, self.operator_response

    def set_dynamic_text(self, html: str):
        """Push live HTML into the dynamic label. Thread-safe via Qt signal."""
        if self.dynamic_label is not None and self.isVisible():
            self.dynamic_label.setText(html)
            self.dynamic_label.repaint()

    # Keep old name as alias so nothing else breaks
    def update_dynamic_text(self, text: str):
        self.set_dynamic_text(text)