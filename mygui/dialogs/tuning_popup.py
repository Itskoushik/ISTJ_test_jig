"""
TuningPopup – operator-assisted tuning dialog.

Shows live resistance / voltage / APX readings with min/max limits and
PASS/FAIL status. Values displayed to 4 decimal places.
Operator adjusts hardware in real-time then clicks "Proceed" to retry.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QApplication, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence


class TuningPopup(QDialog):
    """
    Live-reading tuning popup (non-modal).

    Parameters
    ----------
    title   : str       – e.g. "Tuning: COM 1 KEY Connector"
    unit    : str       – "voltage", "resistance", "vrms", "mvrms", "uvrms"
    min_val : str|None  – e.g. "8.5V", "1K", "4.95"
    max_val : str|None  – e.g. "9.5V", "10K", "6.05"
    parent  : QWidget
    """

    tuning_done = pyqtSignal()   # emitted when user clicks "Proceed"

    def __init__(self, title="Tuning", unit="voltage",
             min_val=None, max_val=None, parent=None, section_title=""):
        super().__init__(parent)
        self.unit    = unit.lower()
        self.min_val = min_val
        self.max_val = max_val
        self._forced_value = None

        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowStaysOnTopHint
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
        )
        self.setModal(False)   # non-modal so background thread can update it

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── header ────────────────────────────────────────────────────────
        hdr = QLabel(title)
        hdr.setFont(QFont("Arial", 13, QFont.Bold))
        hdr.setStyleSheet("color: #1a5da8;")
        layout.addWidget(hdr)

        if section_title:
            sec_lbl = QLabel(section_title)
            sec_lbl.setAlignment(Qt.AlignCenter)
            sec_lbl.setFont(QFont("Arial", 9, QFont.Bold))
            sec_lbl.setStyleSheet(
                "color: white; background: #1a5da8; border-radius: 4px; padding: 4px 10px;"
            )
            layout.addWidget(sec_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(sep)

        # ── live value display (large, centred) ───────────────────────────
        self.value_label = QLabel(self._make_html("—", "#888888"))
        self.value_label.setTextFormat(Qt.RichText)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setMinimumHeight(90)
        self.value_label.setStyleSheet("""
            QLabel {
                background: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 14px;
            }
        """)
        layout.addWidget(self.value_label)

        # ── limits row ────────────────────────────────────────────────────
        lim_layout = QHBoxLayout()

        min_txt = f"Min: <b>{min_val}</b>" if min_val else "Min: <b>—</b>"
        max_txt = f"Max: <b>{max_val}</b>" if max_val else "Max: <b>—</b>"

        for txt in (min_txt, max_txt):
            lbl = QLabel(txt)
            lbl.setTextFormat(Qt.RichText)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont("Arial", 10))
            lim_layout.addWidget(lbl)
        layout.addLayout(lim_layout)

        # ── unit hint ─────────────────────────────────────────────────────
        unit_display = {
            "voltage":    "DC Voltage (V / mV)",
            "resistance": "Resistance (Ω / kΩ / MΩ)",
            "vrms":       "APX Level (Vrms)",
            "mvrms":      "APX Level (mVrms)",
            "uvrms":      "APX Level (µVrms)",
        }.get(self.unit, self.unit)

        unit_lbl = QLabel(f"Measuring: {unit_display}")
        unit_lbl.setAlignment(Qt.AlignCenter)
        unit_lbl.setFont(QFont("Arial", 9))
        unit_lbl.setStyleSheet("color: #555; font-style: italic;")
        layout.addWidget(unit_lbl)

        # ── instruction ───────────────────────────────────────────────────
        instr = QLabel(
            "Adjust hardware until the reading is within limits,\n"
            "then click <b>Proceed</b> to retry the test step."
        )
        instr.setTextFormat(Qt.RichText)
        instr.setAlignment(Qt.AlignCenter)
        instr.setFont(QFont("Arial", 9))
        instr.setStyleSheet("color: #555;")
        layout.addWidget(instr)

        # ── done button ───────────────────────────────────────────────────
        self.done_btn = QPushButton("✔  Proceed")
        self.done_btn.setMinimumHeight(46)
        self.done_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.done_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover   { background-color: #1b5e20; }
            QPushButton:pressed { background-color: #0d3f1f; }
        """)
        self.done_btn.clicked.connect(self._on_done)
        layout.addWidget(self.done_btn)
        
        # ── Ctrl+F shortcut → Force Pass dialog ──────────────────────────────
        shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut.activated.connect(self._open_force_pass)

        # hint_lbl = QLabel("Press <b>Ctrl+F</b> to force pass with a manual value")
        # hint_lbl.setTextFormat(Qt.RichText)
        # hint_lbl.setAlignment(Qt.AlignCenter)
        # hint_lbl.setFont(QFont("Arial", 8))
        # hint_lbl.setStyleSheet("color: #aaa; font-style: italic; margin-top: 4px;")
        # layout.addWidget(hint_lbl)

    # ── public API ────────────────────────────────────────────────────────

    def update_reading(self, display_value: str, status: str):
        """
        Update live reading.

        Parameters
        ----------
        display_value : str  – already-formatted string with 4 decimals,
                               e.g. "8.9700 V" or "75.3000 Ω" or "4.9500 Vrms"
        status        : str  – "PASS" or "FAIL"
        """
        colour = "#2e7d32" if status == "PASS" else "#d32f2f"
        symbol = "✔  PASS" if status == "PASS" else "✘  FAIL"
        self.value_label.setText(self._make_html(display_value, colour, symbol))
        QApplication.processEvents()

    def set_dynamic_text(self, html: str):
        """Compatible with update_popup_signal — no-op here."""
        pass

    # ── private ───────────────────────────────────────────────────────────

    def _make_html(self, value: str, colour: str, badge: str = "") -> str:
        badge_html = (
            f"<br><span style='font-size:14px; color:{colour};'>{badge}</span>"
            if badge else ""
        )
        return (
            f"<span style='font-size:28px; font-weight:bold; "
            f"font-family:Courier New; color:{colour};'>"
            f"{value}</span>{badge_html}"
        )

    def _on_done(self):
        self.tuning_done.emit()
        self.accept()

    def closeEvent(self, event):
        self.tuning_done.emit()
        event.accept()
        
    def _open_force_pass(self):
        unit_display = {
            "voltage":    "DC Voltage (V)  e.g. 11.05",
            "resistance": "Resistance (Ω)  e.g. 75.0",
            "vrms":       "APX Level (Vrms)  e.g. 2.00",
            "mvrms":      "APX Level (mVrms)  e.g. 8.050",
            "uvrms":      "APX Level (µVrms)  e.g. 750.0",
        }.get(self.unit, f"Value ({self.unit})")

        dlg = QDialog(self)
        dlg.setWindowTitle("Force Pass — Manual Value")
        dlg.setMinimumWidth(340)
        dlg.setWindowFlags(
            dlg.windowFlags() | Qt.WindowStaysOnTopHint
            | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        title_lbl = QLabel("Force Pass")
        title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        title_lbl.setStyleSheet("color: #e65100;")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        hint = QLabel(f"Enter value for:<br><b>{unit_display}</b>")
        hint.setTextFormat(Qt.RichText)
        hint.setAlignment(Qt.AlignCenter)
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet("color: #555;")
        layout.addWidget(hint)

        inp = QLineEdit()
        inp.setPlaceholderText("Enter numeric value...")
        inp.setMinimumHeight(38)
        inp.setFont(QFont("Courier New", 11))
        inp.setAlignment(Qt.AlignCenter)
        inp.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdbdbd; border-radius: 4px;
                padding: 4px 8px; background: #fafafa;
            }
            QLineEdit:focus { border: 1px solid #e65100; }
        """)
        layout.addWidget(inp)

        err_lbl = QLabel("")
        err_lbl.setAlignment(Qt.AlignCenter)
        err_lbl.setFont(QFont("Arial", 8))
        err_lbl.setStyleSheet("color: #d32f2f;")
        layout.addWidget(err_lbl)

        btn_row = QHBoxLayout(); btn_row.setSpacing(8)

        ok_btn = QPushButton("✔  OK")
        ok_btn.setMinimumHeight(38)
        ok_btn.setFont(QFont("Arial", 10, QFont.Bold))
        ok_btn.setStyleSheet("""
            QPushButton { background:#e65100; color:white; border:none; border-radius:4px; }
            QPushButton:hover { background:#bf360c; }
        """)

        cancel_btn = QPushButton("✖  Cancel")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setFont(QFont("Arial", 10, QFont.Bold))
        cancel_btn.setStyleSheet("""
            QPushButton { background:#757575; color:white; border:none; border-radius:4px; }
            QPushButton:hover { background:#616161; }
        """)

        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        def _on_ok():
            txt = inp.text().strip()
            try:
                self._forced_value = float(txt)
                dlg.accept()
                # close the tuning popup — _on_done will fire the signal
                self._on_done()
            except ValueError:
                err_lbl.setText("⚠ Please enter a valid number.")
                inp.setStyleSheet("""
                    QLineEdit {
                        border: 1px solid #d32f2f; border-radius: 4px;
                        padding: 4px 8px; background: #fff3f3;
                    }
                """)

        ok_btn.clicked.connect(_on_ok)
        cancel_btn.clicked.connect(dlg.reject)
        inp.returnPressed.connect(_on_ok)

        dlg.exec_()

    def get_forced_value(self):
        """Returns float if operator set a manual value via Ctrl+F, else None."""
        return self._forced_value