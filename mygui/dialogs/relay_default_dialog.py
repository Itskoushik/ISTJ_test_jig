"""
Relay -> Default-state progress popup.

Shown whenever STM32RelayController.set_default_states() runs. It reports,
live, which relay is being switched OFF ("Switching S27 OFF...",
"Disconnecting J07...") and how far the sweep is ("Relay 4 of 90").

How it is wired (no call site has to change):
  * set_default_states() (core/stm32_commands.py) calls a plain-Python
    progress callback for every relay. That callback runs on the TEST /
    ABORT WORKER thread.
  * RelayDefaultProgressController (below) lives on the GUI thread and turns
    those callbacks into Qt signals, which Qt delivers queued on the GUI
    thread. The dialog is therefore only ever touched from the GUI thread.
  * The worker thread NEVER waits on this dialog. It cannot slow down or
    block the relay sweep.

Install once from the screen:  install_default_state_popup(self)
"""
import math

from PyQt5.QtCore import Qt, QObject, QTimer, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QFont, QPainter, QColor, QPen, QPainterPath, QPixmap,
    QLinearGradient, QRadialGradient, QBrush,
)
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QFrame, QWidget, QGraphicsDropShadowEffect,
)
from core.paths import RESOURCES_DIR

# After a fully successful sweep the popup closes itself after this many ms
# (Finish / X still work immediately). A sweep with failures never auto-closes.
# Set to 0 to always require a click on Finish, like the self-test abort popup.
AUTO_CLOSE_MS = 1200


def describe_relay(name: str):
    """'J07' -> 'Disconnecting J07…',  'S27' -> 'Switching S27 OFF…'"""
    n = name.upper()
    if n.startswith("J"):
        return f"Disconnecting {n}…"
    return f"Switching {n} OFF…"


# ── Painted widgets (no fonts/emoji/image dependencies) ─────────────────────
class _StatusBadge(QWidget):
    """Gear with a spinning arc while running, shield+tick on success,
    shield+'!' on failure."""
    _BLUE, _GREEN, _RED = "#1668e3", "#2e7d32", "#c62828"

    def __init__(self, size=124, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._state = "run"
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._angle = (self._angle - 9) % 360
        self.update()

    def set_state(self, state):
        self._state = state
        if state == "run":
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def stop(self):
        self._timer.stop()

    @staticmethod
    def _gear_path(c, r_out, r_in, r_hole, teeth=8):
        path = QPainterPath()
        step = 2 * math.pi / teeth
        t1, t2 = step * 0.30, step * 0.17
        first = True
        for i in range(teeth):
            a = step * i
            for r, da in ((r_in, -t1), (r_out, -t2), (r_out, t2), (r_in, t1)):
                pt = QPointF(c.x() + r * math.cos(a + da),
                             c.y() + r * math.sin(a + da))
                if first:
                    path.moveTo(pt)
                    first = False
                else:
                    path.lineTo(pt)
        path.closeSubpath()
        path.addEllipse(c, r_hole, r_hole)          # odd-even fill -> hole
        return path

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        col = QColor({"run": self._BLUE, "ok": self._GREEN,
                      "fail": self._RED}[self._state])
        c = QPointF(self.width() / 2, self.height() / 2)
        r = self.width() / 2

        glow = QRadialGradient(c, r)
        a = QColor(col); a.setAlpha(70)
        b = QColor(col); b.setAlpha(0)
        glow.setColorAt(0.0, a)
        glow.setColorAt(1.0, b)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(c, r, r)

        ring = QColor(col); ring.setAlpha(34)
        p.setBrush(ring)
        p.drawEllipse(c, r * 0.68, r * 0.68)

        if self._state == "run":
            p.setBrush(QBrush(col))
            p.drawPath(self._gear_path(c, r * 0.36, r * 0.29, r * 0.15))
            p.setPen(QPen(col, 4, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            rr = r * 0.90
            p.drawArc(QRectF(c.x() - rr, c.y() - rr, 2 * rr, 2 * rr),
                      int(self._angle * 16), 95 * 16)
            return

        # shield
        h, w = r * 0.40, r * 0.33
        sh = QPainterPath()
        sh.moveTo(c.x(), c.y() - h)
        sh.lineTo(c.x() + w, c.y() - h * 0.70)
        sh.lineTo(c.x() + w, c.y() + h * 0.05)
        sh.quadTo(c.x() + w, c.y() + h * 0.65, c.x(), c.y() + h)
        sh.quadTo(c.x() - w, c.y() + h * 0.65, c.x() - w, c.y() + h * 0.05)
        sh.lineTo(c.x() - w, c.y() - h * 0.70)
        sh.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(col))
        p.drawPath(sh)

        p.setPen(QPen(Qt.white, 4.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        k = w * 0.55
        if self._state == "ok":
            tick = QPainterPath()
            tick.moveTo(c.x() - k, c.y() + k * 0.05)
            tick.lineTo(c.x() - k * 0.25, c.y() + k * 0.75)
            tick.lineTo(c.x() + k, c.y() - k * 0.65)
            p.drawPath(tick)
        else:
            p.drawLine(QPointF(c.x(), c.y() - k * 0.9), QPointF(c.x(), c.y() + k * 0.15))
            p.drawPoint(QPointF(c.x(), c.y() + k * 0.75))
class _ProgressTrack(QWidget):
    """Self-painted progress bar. Same API subset the dialog already uses
    (setRange / setMaximum / maximum / setValue), but immune to stylesheet
    cascading from parent QFrames."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._min, self._max, self._value = 0, 1, 0
        self._c1, self._c2 = QColor("#1976d2"), QColor("#42a5f5")
        self.setMinimumWidth(120)

    def setRange(self, lo, hi):
        self._min, self._max = lo, max(hi, lo + 1)
        self.update()

    def setMaximum(self, hi):
        self._max = max(hi, self._min + 1)
        self.update()

    def maximum(self):
        return self._max

    def setValue(self, v):
        self._value = max(self._min, min(v, self._max))
        self.update()

    def set_colors(self, c1, c2):
        self._c1, self._c2 = QColor(c1), QColor(c2)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        rad = r.height() / 2

        # track
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#c3cfe2"))
        p.drawRoundedRect(r, rad, rad)

        # fill
        frac = (self._value - self._min) / float(self._max - self._min)
        if frac > 0:
            w = min(r.width(), max(r.height(), r.width() * frac))  # visible pill from relay #1
            fill = QRectF(r.left(), r.top(), w, r.height())
            g = QLinearGradient(fill.left(), 0, fill.right(), 0)
            g.setColorAt(0.0, self._c1)
            g.setColorAt(1.0, self._c2)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(fill, rad, rad)

        # outline
        p.setPen(QPen(QColor("#a9b9d3"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), rad, rad)

class _Card(QFrame):
    """Rounded white card with a soft blue header tint and corner wave."""
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rr = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        clip = QPainterPath()
        clip.addRoundedRect(rr, 16, 16)
        p.setClipPath(clip)

        g = QLinearGradient(0, 0, 0, self.height())
        g.setColorAt(0.0, QColor("#e6f0ff"))
        g.setColorAt(0.22, QColor("#ffffff"))
        g.setColorAt(1.0, QColor("#f6f9ff"))
        p.fillPath(clip, QBrush(g))

        w, h = self.width(), self.height()
        wave = QPainterPath()
        wave.moveTo(0, h - 74)
        wave.cubicTo(w * 0.14, h - 100, w * 0.30, h - 34, w * 0.52, h - 22)
        wave.lineTo(w * 0.52, h)
        wave.lineTo(0, h)
        wave.closeSubpath()
        p.fillPath(wave, QColor(100, 170, 255, 55))

        p.setClipping(False)
        edge = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor("#7fa6de"), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(edge, 16, 16)


# ── The dialog ──────────────────────────────────────────────────────────────
class RelayDefaultProgressDialog(QDialog):
    """
    Progress popup for 'Switch Relays to Default'. GUI-thread only.
    Finish / X stay disabled until the sweep has ended.
    """
    _PANEL = {   # state -> (bg, border, icon bg, icon text, title colour)
        "run":  ("#eef4ff", "#bcd3f8", "#dbe8fd", "↻", "#1565c0"),
        "ok":   ("#e8f5e9", "#bfe3c3", "#d3ecd6", "✓", "#1b7a2b"),
        "fail": ("#ffebee", "#f2b8bd", "#fbd5d8", "!", "#c62828"),
    }
    _SHADOW_MARGIN = 26

    def __init__(self, parent=None):
        super().__init__(parent)
        self._done = False
        self._failed_so_far = 0
        self.failed = []
        self.setWindowTitle("Switch Relays to Default")
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(660)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(self._SHADOW_MARGIN, self._SHADOW_MARGIN,
                                 self._SHADOW_MARGIN, self._SHADOW_MARGIN)
        card = _Card()
        outer.addWidget(card)

        root = QVBoxLayout(card)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # header
        head = QHBoxLayout()
        head.setContentsMargins(24, 14, 18, 8)
        head.setSpacing(16)
        logo = QLabel()
        pix = QPixmap(str(RESOURCES_DIR / "hal_logo.png"))
        if pix.isNull():
            logo.setText("HAL")
            logo.setFont(QFont("Arial", 14, QFont.Bold))
            logo.setStyleSheet("color:#1a5da8; background:transparent;")
        else:
            logo.setPixmap(pix.scaledToWidth(86, Qt.SmoothTransformation))
            logo.setStyleSheet("background:transparent;")
        head.addWidget(logo, 0, Qt.AlignVCenter)
        htitle = QLabel("Switch Relays to Default")
        htitle.setFont(QFont("Arial", 12))
        htitle.setStyleSheet("color:#1a1a1a; background:transparent;")
        head.addWidget(htitle, 1, Qt.AlignVCenter)
        self.x_btn = QPushButton("✕")
        self.x_btn.setFixedSize(34, 34)
        self.x_btn.setEnabled(False)
        self.x_btn.setCursor(Qt.PointingHandCursor)
        self.x_btn.setStyleSheet("""
            QPushButton { background:#e3ecf9; color:#1a3a6b; border:none;
                          border-radius:17px; font-size:13px; font-weight:bold; }
            QPushButton:hover    { background:#d2e0f5; }
            QPushButton:disabled { background:#eef2f8; color:#b5bfd0; }
        """)
        self.x_btn.clicked.connect(self.accept)
        head.addWidget(self.x_btn, 0, Qt.AlignVCenter)
        root.addLayout(head)

        # body
        body = QVBoxLayout()
        body.setContentsMargins(34, 6, 34, 26)
        body.setSpacing(10)

        self.badge = _StatusBadge(124)
        body.addWidget(self.badge, 0, Qt.AlignHCenter)

        self.title_lbl = QLabel("Switching Relays to Default")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setFont(QFont("Arial", 22, QFont.Bold))
        self.title_lbl.setStyleSheet("color:#0d1b3e; background:transparent;")
        body.addWidget(self.title_lbl)

        self.status_lbl = QLabel("Turning OFF all relays and returning to default state…")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setFont(QFont("Arial", 10))
        self.status_lbl.setStyleSheet("color:#5b6478; background:transparent;")
        body.addWidget(self.status_lbl)
        body.addSpacing(6)

        prow = QFrame()
        prow.setObjectName("progRow")
        prow.setStyleSheet("QFrame#progRow { background:#eef3fb; border:none; border-radius:14px; }")
        pl = QHBoxLayout(prow)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(14)
        self.bar = _ProgressTrack()
        self.bar.setRange(0, 1)
        self.bar.setValue(0)
        self.bar.setFixedHeight(16)
        self._set_bar_color("#1976d2", "#42a5f5")
        self.pct_lbl = QLabel("0%")
        self.pct_lbl.setFont(QFont("Arial", 12, QFont.Bold))
        self.pct_lbl.setMinimumWidth(48)
        self.pct_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pct_lbl.setStyleSheet("color:#1976d2; background:transparent;")
        pl.addWidget(self.bar, 1)
        pl.addWidget(self.pct_lbl, 0)
        body.addWidget(prow)

        self.panel = QFrame()
        self.panel.setObjectName("relayPanel")
        pn = QHBoxLayout(self.panel)
        pn.setContentsMargins(18, 12, 18, 12)
        pn.setSpacing(14)
        self.p_icon = QLabel()
        self.p_icon.setFixedSize(46, 46)
        self.p_icon.setAlignment(Qt.AlignCenter)
        self.p_icon.setFont(QFont("Arial", 18, QFont.Bold))
        self.p_div = QFrame()
        self.p_div.setFixedWidth(2)
        col = QVBoxLayout()
        col.setSpacing(2)
        self.p_title = QLabel("")
        self.p_title.setFont(QFont("Arial", 13, QFont.Bold))
        self.p_sub = QLabel("")
        self.p_sub.setObjectName("relaySub")
        self.p_sub.setFrameShape(QFrame.NoFrame)
        self.p_sub.setWordWrap(True)
        self.p_sub.setFont(QFont("Arial", 10))
        self.p_sub.setStyleSheet(
            "QLabel#relaySub { color:#5b6478; background:transparent; border:none; }")
        col.addWidget(self.p_title)
        col.addWidget(self.p_sub)
        pn.addWidget(self.p_icon, 0)
        pn.addWidget(self.p_div, 0)
        pn.addLayout(col, 1)
        body.addWidget(self.panel)
        self._set_panel("run", "Preparing…", "Starting relay sweep")

        self.auto_note = QLabel("")
        self.auto_note.setAlignment(Qt.AlignCenter)
        self.auto_note.setFont(QFont("Arial", 9))
        self.auto_note.setStyleSheet("color:#5b6478; background:transparent;")
        body.addWidget(self.auto_note)

        self.finish_btn = QPushButton("✓ Proceed")
        self.finish_btn.setEnabled(False)
        self.finish_btn.setMinimumHeight(46)
        self.finish_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.finish_btn.setCursor(Qt.PointingHandCursor)
        self.finish_btn.setStyleSheet("""
            QPushButton { background-color:#0b5ed7; color:white; border:none;
                          border-radius:10px; padding:8px 16px; }
            QPushButton:hover    { background-color:#0a53be; }
            QPushButton:pressed  { background-color:#084298; }
            QPushButton:disabled { background-color:#cfd8e6; color:#9aa5b8; }
        """)
        self.finish_btn.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.finish_btn)
        row.addStretch(1)
        body.addSpacing(4)
        body.addLayout(row)
        root.addLayout(body)
        
    def paintEvent(self, _):
        """Soft drop shadow painted manually around the card."""
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m = self._SHADOW_MARGIN
        card = QRectF(self.rect()).adjusted(m, m, -m, -m)
        p.setPen(Qt.NoPen)
        n = 16
        for i in range(n, 0, -1):                       # outermost (faintest) first
            a = int(14 * (1 - i / (n + 1.0)) ** 2)
            p.setBrush(QColor(0, 0, 0, a))
            p.drawRoundedRect(card.translated(0, 6).adjusted(-i, -i, i, i),
                              16 + i, 16 + i)

    # ── helpers ─────────────────────────────────────────────────────────
    def _set_bar_color(self, c1, c2):
        self.bar.set_colors(c1, c2)

    def _set_panel(self, state, title, sub):
        bg, border, ibg, itxt, tcol = self._PANEL[state]
        self.panel.setStyleSheet(
            f"QFrame#relayPanel {{ background:{bg}; border:1px solid {border}; border-radius:14px; }}")
        self.p_icon.setText(itxt)
        self.p_icon.setStyleSheet(
            f"background:{ibg}; color:{tcol}; border:none; border-radius:23px;")
        self.p_div.setStyleSheet(f"background:{tcol}; border:none;")
        self.p_title.setText(title)
        self.p_title.setFrameShape(QFrame.NoFrame)
        self.p_title.setStyleSheet(f"color:{tcol}; background:transparent; border:none;")
        self.p_sub.setText(sub)

    # ── public API (call from GUI thread only) ──────────────────────────
    def begin(self, total):
        """(Re)start the display. Also used when the sweep is restarted."""
        self._done = False
        self._failed_so_far = 0
        self.failed = []
        self.badge.set_state("run")
        self.bar.setRange(0, max(total, 1))
        self.bar.setValue(0)
        self.pct_lbl.setText("0%")
        self.pct_lbl.setStyleSheet("color:#1976d2; background:transparent;")
        self._set_bar_color("#1976d2", "#42a5f5")
        self.status_lbl.setText("Turning OFF all relays and returning to default state…")
        self._set_panel("run", "Preparing…", f"0 of {total} relays switched OFF")
        if AUTO_CLOSE_MS > 0:
            self.auto_note.setText("This window will close automatically once all relays are OFF.")
        else:
            self.auto_note.setText("")
        self.finish_btn.setEnabled(False)
        self.x_btn.setEnabled(False)

    def relay_started(self, done, total, name):
        # 'done' = relays already attempted, so this is number done+1
        sub = f"Relay {done + 1} of {total}"
        if self._failed_so_far:
            sub += f"  ·  {self._failed_so_far} failed so far"
        self._set_panel("run", describe_relay(name), sub)

    def relay_done(self, done, total, name, ok):
        if not ok:
            self._failed_so_far += 1
            self.failed.append(name.upper())
        self.bar.setMaximum(max(total, 1))
        self.bar.setValue(done)
        self.pct_lbl.setText(f"{int(done * 100 / max(total, 1))}%")

    def finish(self, failed):
        self.failed = [f.upper() for f in failed]
        self._done = True
        self.bar.setValue(self.bar.maximum())
        self.pct_lbl.setText("100%")
        if self.failed:
            shown = ", ".join(self.failed[:12])
            if len(self.failed) > 12:
                shown += f"  (+{len(self.failed) - 12} more)"
            self.badge.set_state("fail")
            self._set_bar_color("#c62828", "#ef5350")
            self.pct_lbl.setStyleSheet("color:#c62828; background:transparent;")
            self.status_lbl.setText("Finished with errors.")
            self._set_panel("fail", "Could not confirm default state for some relays", shown)
            self.auto_note.setText("Automatic close is disabled because some relays failed. "
                                   "Click Proceed to continue.")
        else:
            self.badge.set_state("ok")
            self._set_bar_color("#2e7d32", "#66bb6a")
            self.pct_lbl.setStyleSheet("color:#2e7d32; background:transparent;")
            self.status_lbl.setText("Hardware is now in its default state.")
            self._set_panel("ok", "All relays switched to default state",
                            "System is now in a safe state.")
            if AUTO_CLOSE_MS > 0:
                self.auto_note.setText("Proceeding automatically…")
                QTimer.singleShot(AUTO_CLOSE_MS, self._auto_close)
            else:
                self.auto_note.setText("Click Proceed to continue.")
        self.finish_btn.setEnabled(True)
        self.x_btn.setEnabled(True)

    def _auto_close(self):
        if self._done and self.isVisible() and not self.failed:
            self.accept()

    def force_close(self):
        """Close regardless of state (sweep aborted / stopped mid-way)."""
        self._done = True
        self.badge.stop()
        self.hide()

    # Block Esc / window close while the sweep is still running.
    def reject(self):
        if self._done:
            self.badge.stop()
            super().reject()

    def closeEvent(self, event):
        if self._done:
            self.badge.stop()
            event.accept()
        else:
            event.ignore()


# ── GUI-thread bridge ───────────────────────────────────────────────────────
class RelayDefaultProgressController(QObject):
    """
    Receives progress callbacks from ANY thread (set_default_states runs on
    the test/abort worker) and re-emits them as Qt signals. Because this
    object is created on the GUI thread, the connected slots run there
    (queued), so the dialog is only ever touched from the GUI thread.
    """
    _sig_start = pyqtSignal(int)
    _sig_relay_start = pyqtSignal(int, int, str)
    _sig_relay_done = pyqtSignal(int, int, str, bool)
    _sig_end = pyqtSignal(list)
    _sig_hide = pyqtSignal()

    def __init__(self, window):
        super().__init__(window)
        self._window = window
        self._dlg = None
        self._sig_start.connect(self._on_start)
        self._sig_relay_start.connect(self._on_relay_start)
        self._sig_relay_done.connect(self._on_relay_done)
        self._sig_end.connect(self._on_end)
        self._sig_hide.connect(self._on_hide)

    # -- worker-thread side ------------------------------------------------
    def callback(self, event, *args):
        if event == "start":
            self._sig_start.emit(int(args[0]))
        elif event == "relay_start":
            self._sig_relay_start.emit(int(args[0]), int(args[1]), str(args[2]))
        elif event == "relay_done":
            self._sig_relay_done.emit(int(args[0]), int(args[1]), str(args[2]), bool(args[3]))
        elif event == "end":
            self._sig_end.emit(list(args[0]))
        elif event in ("pause", "abort"):
            self._sig_hide.emit()

    # -- GUI-thread side ---------------------------------------------------
    def _ensure_dialog(self):
        if self._dlg is None:
            self._dlg = RelayDefaultProgressDialog(self._window)
        return self._dlg

    def _on_start(self, total):
        dlg = self._ensure_dialog()
        dlg.begin(total)
        dlg.show()
        dlg.raise_()

    def _on_relay_start(self, done, total, name):
        if self._dlg is not None and self._dlg.isVisible():
            self._dlg.relay_started(done, total, name)

    def _on_relay_done(self, done, total, name, ok):
        if self._dlg is not None:
            self._dlg.relay_done(done, total, name, ok)

    def _on_end(self, failed):
        if self._dlg is not None and self._dlg.isVisible():
            self._dlg.finish(failed)

    def _on_hide(self):
        if self._dlg is not None:
            self._dlg.force_close()


def install_default_state_popup(screen):
    """
    Call once from the GUI thread (e.g. next to
    STM32RelayController.register_screen(self)). Safe to call repeatedly.
    """
    from core.stm32_commands import STM32RelayController
    ctrl = getattr(screen, "_default_popup_ctrl", None)
    if ctrl is None:
        ctrl = RelayDefaultProgressController(screen)
        screen._default_popup_ctrl = ctrl
    STM32RelayController.register_default_progress_callback(ctrl.callback)
    return ctrl


def uninstall_default_state_popup():
    from core.stm32_commands import STM32RelayController
    STM32RelayController.register_default_progress_callback(None)