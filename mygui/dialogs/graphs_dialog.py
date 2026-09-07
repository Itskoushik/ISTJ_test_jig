"""
graphs_dialog.py — Non-blocking test results graph viewer.

Fixes:
• Bigger dropdown, buttons, legend font
• Per-series normalization: each SI unit plotted as its own series
  so mVrms (451) never dwarfs Vrms (2.0) on the same axis
• Y-axis auto-range with 15% padding so nothing clips
• APX Audio mode uses correct log regex
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QScrollArea, QWidget, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import re
from collections import defaultdict

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

_SERIES_COLORS = [
    (26,  93, 168),
    (211, 47,  47),
    (46, 125,  50),
    (245, 124,   0),
    (123,  31, 162),
    (0,   151, 167),
]

# unit key (lowercase, µ→u) → (SI factor, SI label)
_UNIT_META = {
    "mv":    (1e-3,  "V"),
    "v":     (1,     "V"),
    "kv":    (1e3,   "V"),
    "o":     (1,     "Ω"),
    "ko":    (1e3,   "Ω"),
    "mo":    (1e6,   "Ω"),
    "ohm":   (1,     "Ω"),
    "vrms":  (1,     "Vrms"),
    "mvrms": (1e-3,  "Vrms"),
    "uvrms": (1e-6,  "Vrms"),
}

def _unit_key(raw_unit: str) -> str:
    return (raw_unit.lower()
            .replace("µ", "u")
            .replace("ω", "o")
            .replace("kω", "ko")
            .replace("mω", "mo")
            .replace("ω", "o"))


class GraphsDialog(QDialog):
    def __init__(self, parent=None, logs_history=None):
        super().__init__(parent)
        self.logs_history = logs_history or []
        self.setWindowTitle("HAL – Test Results Graph")
        self.setMinimumSize(1060, 700)
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowStaysOnTopHint
        )
        self._build_ui()
        self._refresh()

        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

    # ─────────────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Title
        title = QLabel("Test Measurement Graph")
        title.setFont(QFont("Arial", 15, QFont.Bold))
        title.setStyleSheet("color: #1a5da8;")
        root.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#e0e0e0;")
        root.addWidget(sep)

        if not PYQTGRAPH_AVAILABLE:
            root.addWidget(QLabel(
                "⚠  pyqtgraph is not installed.\n"
                "Run:  pip install pyqtgraph --break-system-packages"
            ))
            self._add_close(root)
            return

        # Controls row
        ctrl = QHBoxLayout(); ctrl.setSpacing(12)

        show_lbl = QLabel("Show:")
        show_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        show_lbl.setStyleSheet("color:#374151;")
        ctrl.addWidget(show_lbl)

        self.mode_combo = QComboBox()
        self.mode_combo.setMinimumHeight(42)
        self.mode_combo.setMinimumWidth(340)
        self.mode_combo.setFont(QFont("Arial", 11))
        self.mode_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                padding: 8px 12px;
                background: #ffffff;
                color: #222;
                font-size: 11pt;
            }
            QComboBox:focus { border: 1px solid #1a5da8; }
            QComboBox::drop-down { border: none; width: 26px; }
            QComboBox QAbstractItemView {
                font-size: 11pt;
                selection-background-color: #1a5da8;
            }
        """)
        self.mode_combo.addItems([
            "Voltage  (V / mV)",
            "Resistance  (Ω / kΩ / MΩ)",
            "APX Audio  (Vrms / mVrms / µVrms)",
            "All numeric",
        ])
        self.mode_combo.currentIndexChanged.connect(self._refresh)
        ctrl.addWidget(self.mode_combo)
        ctrl.addStretch()

        refresh_btn = QPushButton("⟳  Refresh")
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setMinimumWidth(130)
        refresh_btn.setFont(QFont("Arial", 11, QFont.Bold))
        refresh_btn.setStyleSheet("""
            QPushButton {
                background:#1a5da8; color:white; border:none;
                border-radius:5px; padding:8px 18px;
            }
            QPushButton:hover { background:#154a8a; }
        """)
        refresh_btn.clicked.connect(self._refresh)
        ctrl.addWidget(refresh_btn)
        root.addLayout(ctrl)

        # Plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#fafbfc")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setLabel("left",   "Value",  color="#333", size="11pt")
        self.plot_widget.setLabel("bottom", "Step #", color="#333", size="11pt")
        self.plot_widget.getAxis("left").setStyle(tickFont=QFont("Courier New", 9))
        self.plot_widget.getAxis("bottom").setStyle(tickFont=QFont("Arial", 9))
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.plot_widget, 4)

        # Scrollable legend
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(130)
        scroll.setMaximumHeight(210)
        scroll.setStyleSheet("QScrollArea{border:1px solid #e0e0e0;border-radius:4px;}")
        leg_w = QWidget(); leg_w.setStyleSheet("background:#ffffff;")
        leg_lay = QVBoxLayout(leg_w)
        leg_lay.setContentsMargins(10, 8, 10, 8)
        self.legend_label = QLabel("(no data yet)")
        self.legend_label.setFont(QFont("Courier New", 9))
        self.legend_label.setWordWrap(False)
        self.legend_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        leg_lay.addWidget(self.legend_label)
        leg_lay.addStretch()
        scroll.setWidget(leg_w)
        root.addWidget(scroll, 1)

        self._add_close(root)

    def _add_close(self, layout):
        btn = QPushButton("✕  Close")
        btn.setMinimumHeight(42)
        btn.setMinimumWidth(130)
        btn.setFont(QFont("Arial", 11, QFont.Bold))
        btn.setStyleSheet("""
            QPushButton {
                background:#d32f2f; color:white; border:none;
                border-radius:5px; padding:8px 20px;
            }
            QPushButton:hover { background:#b71c1c; }
        """)
        btn.clicked.connect(self.close)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn)
        layout.addLayout(row)

    # ─────────────────────────────────────────────────────────────────────
    # Parsing
    # ─────────────────────────────────────────────────────────────────────

    _VOLT_PAT = re.compile(
        r"^(.+?):\s*([-\d.]+)\s*(mV|V)\b.*?(PASS|FAIL)", re.IGNORECASE)
    _RES_PAT  = re.compile(
        r"^(.+?):\s*([-\d.]+)\s*(kΩ|MΩ|Ω|ohm)\b.*?(PASS|FAIL)", re.IGNORECASE)
    _APX_PAT  = re.compile(
        r"^(.+?):\s*([-\d.]+)\s*(mVrms|µVrms|uVrms|Vrms)\b.*?(PASS|FAIL)",
        re.IGNORECASE)
    _ALL_PAT  = re.compile(
        r"^(.+?):\s*([-\d.]+)\s*([A-Za-zΩµk]+).*?(PASS|FAIL)", re.IGNORECASE)

    def _parse_logs(self, mode: int):
        pats = {0: self._VOLT_PAT, 1: self._RES_PAT,
                2: self._APX_PAT,  3: self._ALL_PAT}
        pat = pats.get(mode, self._ALL_PAT)

        results = []
        step = 0
        for entry in self.logs_history:
            _, msg, _ = entry[0], entry[1], entry[2]
            m = pat.match(msg.strip())
            if not m:
                continue
            label, val_str, unit, pf = (
                m.group(1).strip(), m.group(2), m.group(3), m.group(4))
            try:
                raw = float(val_str)
                uk  = _unit_key(unit)
                factor, si_unit = _UNIT_META.get(uk, (1.0, unit))
                results.append({
                    "step":    step,
                    "label":   label,
                    "raw":     raw,
                    "value":   raw * factor,
                    "unit":    unit,
                    "si_unit": si_unit,
                    "pass":    pf.upper() == "PASS",
                })
                step += 1
            except ValueError:
                pass
        return results

    # ─────────────────────────────────────────────────────────────────────
    # Rendering
    # ─────────────────────────────────────────────────────────────────────

    def _refresh(self):
        if not PYQTGRAPH_AVAILABLE:
            return
        import pyqtgraph as pg

        mode = self.mode_combo.currentIndex()
        data = self._parse_logs(mode)
        self.plot_widget.clear()

        if not data:
            self.legend_label.setText(
                "No matching measurements found in current logs.\n"
                "Results appear here automatically as the test runs."
            )
            self.plot_widget.setLabel("left", "Value")
            return

        # Group by SI unit so mixed units each get their own colour series
        series: dict = defaultdict(list)
        for d in data:
            series[d["si_unit"]].append(d)

        legend_lines = []
        all_y = []
        color_idx = 0

        for si_unit, pts in series.items():
            col = _SERIES_COLORS[color_idx % len(_SERIES_COLORS)]
            color_idx += 1

            xs = [p["step"] for p in pts]
            ys = [p["value"] for p in pts]
            all_y.extend(ys)

            # Line
            self.plot_widget.plot(xs, ys,
                pen=pg.mkPen(color=col, width=2),
                name=si_unit)

            # Coloured scatter dots
            px, py, fx, fy = [], [], [], []
            for p in pts:
                if p["pass"]: px.append(p["step"]); py.append(p["value"])
                else:         fx.append(p["step"]); fy.append(p["value"])

            if px:
                self.plot_widget.addItem(pg.ScatterPlotItem(
                    px, py, symbol="o", size=14,
                    brush=pg.mkBrush(46, 125, 50, 230),
                    pen=pg.mkPen("w", width=1)))
            if fx:
                self.plot_widget.addItem(pg.ScatterPlotItem(
                    fx, fy, symbol="o", size=14,
                    brush=pg.mkBrush(211, 47, 47, 230),
                    pen=pg.mkPen("w", width=1)))

            for p in pts:
                sym = "✔ PASS" if p["pass"] else "✘ FAIL"
                legend_lines.append(
                    f"  {sym}  Step {p['step']:2d}  "
                    f"{p['label'][:44]:<44s}  "
                    f"{p['raw']:>12.4f} {p['unit']}")

        # Y-axis: auto-range with 15% padding
        if all_y:
            mn, mx = min(all_y), max(all_y)
            span = mx - mn if mx != mn else max(abs(mx), 0.001)
            pad  = span * 0.15
            self.plot_widget.setYRange(mn - pad, mx + pad, padding=0)

        # X-axis
        if data:
            self.plot_widget.setXRange(-0.4, data[-1]["step"] + 0.4, padding=0)

        # Axis label
        self.plot_widget.setLabel(
            "left", " / ".join(series.keys()), color="#333", size="11pt")

        self.legend_label.setText(
            "\n".join(legend_lines) if legend_lines else "No data.")

    def closeEvent(self, event):
        self._timer.stop()
        event.accept()