from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont, QMouseEvent
from PyQt5.QtCore import Qt, QEventLoop

class _SpaceSafeButton(QPushButton):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            event.ignore()
            return
        super().keyPressEvent(event)

class AbortTestConfirmationPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Abort Test?")
        self.setGeometry(400, 300, 500, 250)
        # ── Non-modal + always-on-top: if an OperatorInfoPopup is already
        # showing (also non-modal) when Abort is clicked, this dialog must
        # sit ON TOP of it and take focus, WITHOUT freezing the popup
        # underneath — the operator can still drag that popup while this
        # confirmation is up. setModal(True) used to set ApplicationModal,
        # which blocks input to every other window in the app, including
        # the one underneath, making it undraggable.
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 4px;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Warning Title
        title = QLabel("Abort Test?")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #d32f2f; border: none;")
        layout.addWidget(title)

        # Message
        message = QLabel(
            "A test is currently running. Do you want to abort it and return to the Test Selection screen?"
        )
        message.setFont(QFont("Arial", 10))
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("border: none;")
        layout.addWidget(message)

        layout.addStretch()

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.abort_go_back_btn = _SpaceSafeButton("Yes, Abort & Go Back")
        self.abort_go_back_btn.setMinimumHeight(36)
        self.abort_go_back_btn.setMinimumWidth(140)
        self.abort_go_back_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.abort_go_back_btn.setFocusPolicy(Qt.StrongFocus)
        self.abort_go_back_btn.setAutoDefault(False)
        self.abort_go_back_btn.setDefault(False)
        self.abort_go_back_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.abort_go_back_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.abort_go_back_btn)

        self.cancel_btn = _SpaceSafeButton("Cancel")
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.cancel_btn.setFocusPolicy(Qt.StrongFocus)
        self.cancel_btn.setAutoDefault(True)
        self.cancel_btn.setDefault(True)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        self.cancel_btn.setFocus()

        # ── Drag-anywhere support, same pattern as OperatorInfoPopup ───
        self._drag_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def showEvent(self, event):
        # Non-modal now, so explicitly raise above any OperatorInfoPopup
        # already on screen and grab keyboard focus so Enter/Tab/Space go
        # to THIS dialog rather than the one underneath.
        super().showEvent(event)
        self.raise_()
        self.activateWindow()

    def exec_(self):
        """
        QDialog.exec_() unconditionally sets Qt::WA_ShowModal = True
        internally, no matter what setWindowModality()/setModal() was
        called with beforehand — this is baked into Qt's C++ exec()
        implementation, not something setWindowFlags can override. Left
        alone, every call site's `confirmation.exec_()` would silently
        re-modalize this dialog and freeze any OperatorInfoPopup showing
        underneath again, defeating the whole point of going non-modal.
        Reimplement exec()'s blocking-call behavior by hand instead:
        show() + a local QEventLoop tied to finished(), so WA_ShowModal
        is never touched and callers still get the same Accepted/Rejected
        return value they'd get from the real exec_().
        """
        self.show()
        self.raise_()
        self.activateWindow()
        loop = QEventLoop(self)
        self.finished.connect(loop.quit)
        loop.exec_()
        try:
            self.finished.disconnect(loop.quit)
        except TypeError:
            pass
        return self.result()

    # PyQt5 exposes both exec() and exec_() as separate bound methods —
    # route exec() through the same override so neither name re-modalizes.
    def exec(self):
        return self.exec_()