"""
Self-test ABORT relay cleanup.

SELF-TEST ABORT SAFETY:
Every relay registered for the current self test receives an OFF command
after a CONFIRMED abort, regardless of whether software currently believes
the relay is ON or OFF. The registry below is NOT state tracking; it is a
static list of the relays each self-test module can ever drive.

This module does not touch any test module or the normal relay sequence.
It only runs after the test worker thread has fully stopped.

IMPORTANT:
Abort cleanup must not invoke CH3 power-cycle/replay recovery.
Each relay OFF attempt is independent: attempt -> record -> next.
"""
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRectF, QPointF
from PyQt5.QtGui import (
    QFont, QPainter, QColor, QPen, QPainterPath, QPixmap,
    QLinearGradient, QRadialGradient, QBrush,
)
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout,
    QFrame, QWidget, QGraphicsDropShadowEffect,
)
from core.paths import RESOURCES_DIR

# ── Registry: relays that belong to each self test ──────────────────────────
# Each entry is (label, STM32RelayController attribute name). The attribute is
# the "drive to OFF / neutral" command already used by that test's own
# shutdown code (e.g. S23 -> set_s23_local, S31/S28 -> *_neutral).
# Derived from the actual source of each tests/self_*.py module.

def _off(*names):
    return [(n.split("_")[1].upper(), n) for n in names]

_PSU_DMM_RELAYS = _off("set_j30_off", "set_s21_off", "set_s23_local")
_AUDIO_OSC_RELAYS = _off("set_j23_off", "set_s12_off")

_ISTJ_RELAYS = _off(
    # resistance test: main S21/S22/S26 + sub J30..J54
    "set_s21_off", "set_s22_off", "set_s26_off",
    *[f"set_j{n}_off" for n in range(30, 55)],
    # pairing test S/J pairs
    *[f"set_s{n:02d}_off" for n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 19)],
    *[f"set_j{n:02d}_off" for n in (7, 8, 9, 10, 11, 12, 18, 19, 20, 21, 22, 23, 24, 26, 27, 29)],
    # SB SEL pairs
    *[f"set_s{n}_off" for n in (15, 16, 17, 18, 35)],
    *[f"set_j{n}_off" for n in (13, 14, 15, 16)],
    # extra triplets
    "set_s31_neutral", "set_s28_neutral",
    # voltage relay test + visual inspection + NORM/STBY/REMOTE
    "set_s24_off", "set_s25_off",
    "set_j67_off", "set_j68_off", "set_j70_off", "set_j71_off",
    "set_s27_off", "set_s29_off", "set_s30_off", "set_s32_off",
    "set_s34_off", "set_s33_off", "set_s23_local",
)
# de-duplicate but keep order (S21 etc. appear in several sub-tests)
_seen = set()
_ISTJ_RELAYS = [r for r in _ISTJ_RELAYS if not (r[1] in _seen or _seen.add(r[1]))]

RELAYS_BY_DEVICE = {
    "PSU (Power Supply)":       _PSU_DMM_RELAYS,
    "DMM (Digital Multimeter)": _PSU_DMM_RELAYS,
    "Audio Analyzer":           _AUDIO_OSC_RELAYS,
    "Oscilloscope":             _AUDIO_OSC_RELAYS,
    "Microcontroller":          _ISTJ_RELAYS,
    # Ethernet / RS232 / RS422 self tests drive no STM32 relays.
}


def relays_for_device(device_name):
    """All relays registered for one self test (empty list if none)."""
    return list(RELAYS_BY_DEVICE.get(device_name, []))


def _default_send(attr_name, attempts=2, gap_s=0.3):
    """
    Calls the relay command directly (send_and_validate: takes _bus_lock,
    one validated frame exchange). Does NOT use send_with_retry_self_test(),
    which can sync, queue a blocking popup, reconnect the PSU, restore CH3
    and raise TEST_ABORTED_BY_USER. None of that is allowed during abort
    cleanup. A small local retry, then the failure is just recorded.
    """
    import time
    from core.stm32_commands import STM32RelayController, RelayStateTracker
    fn = getattr(STM32RelayController, attr_name, None)
    if fn is None:
        raise AttributeError(f"STM32RelayController.{attr_name} not found")
    for i in range(attempts):
        if fn():
            try:   # an OFF/neutral/local pops the tracker slot
                RelayStateTracker.record_state(attr_name, fn)
            except Exception:
                pass
            return True
        if i + 1 < attempts:
            time.sleep(gap_s)
    return False


def off_all(relays, send=_default_send, on_start=None, on_attempted=None):
    """
    Attempt OFF on EVERY relay in `relays`. Never skips one and never stops
    early: an exception or falsy result is recorded and the loop continues.
    Returns the list of failed relay labels.
    """
    failed = []
    total = len(relays)
    for i, (label, attr) in enumerate(relays):
        if on_start:
            on_start(i, total, label)
        try:
            ok = send(attr)
        except Exception as e:                       # noqa: BLE001
            print(f"[ABORT-CLEANUP] {label} OFF raised: {e}")
            ok = False
        if not ok:
            print(f"[ABORT-CLEANUP] {label} OFF FAILED")
            failed.append(label)
        if on_attempted:
            on_attempted(i + 1, total, label, ok)
    return failed


class AbortRelayCleanupWorker(QThread):
    starting = pyqtSignal(int, int, str)          # done_so_far, total, label
    attempted = pyqtSignal(int, int, str, bool)   # done, total, label, ok
    all_done = pyqtSignal(list)                   # failed labels

    def __init__(self, relays, send=_default_send, parent=None):
        super().__init__(parent)
        self._relays = list(relays)
        self._send = send

    def run(self):
        failed = off_all(
            self._relays, self._send,
            on_start=lambda i, t, l: self.starting.emit(i, t, l),
            on_attempted=lambda d, t, l, ok: self.attempted.emit(d, t, l, ok),
        )
        self.all_done.emit(failed)


class _StatusBadge(QWidget):
    """Glowing round badge: red power icon while running, green tick on
    success, red power icon on failure. Painted, so no font/emoji issues."""
    _COLORS = {"run": "#e53935", "ok": "#2e7d32", "fail": "#c62828"}

    def __init__(self, size=124, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._state = "run"

    def set_state(self, state):
        self._state = state
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        col = QColor(self._COLORS[self._state])
        c = QPointF(self.width() / 2, self.height() / 2)
        r = self.width() / 2

        glow = QRadialGradient(c, r)
        a = QColor(col); a.setAlpha(80)
        b = QColor(col); b.setAlpha(0)
        glow.setColorAt(0.0, a)
        glow.setColorAt(1.0, b)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(c, r, r)

        ring = QColor(col); ring.setAlpha(38)
        p.setBrush(ring)
        p.drawEllipse(c, r * 0.76, r * 0.76)
        p.setBrush(Qt.white)
        p.drawEllipse(c, r * 0.58, r * 0.58)

        p.setPen(QPen(col, 5.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        k = r * 0.30
        if self._state == "ok":
            path = QPainterPath()
            path.moveTo(c.x() - k, c.y() + k * 0.05)
            path.lineTo(c.x() - k * 0.3, c.y() + k * 0.7)
            path.lineTo(c.x() + k, c.y() - k * 0.6)
            p.drawPath(path)
        else:
            p.drawArc(QRectF(c.x() - k, c.y() - k + 3, 2 * k, 2 * k),
                      120 * 16, 300 * 16)                      # gap at the top
            p.drawLine(QPointF(c.x(), c.y() - k - 4), QPointF(c.x(), c.y() - 1))


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
        p.setPen(QPen(QColor("#d9e3f4"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(rr, 16, 16)


class AbortRelayCleanupDialog(QDialog):
    """
    Modal progress dialog shown after a CONFIRMED abort. Only Finish exists
    (no Cancel/Retry/Abort). Finish (and the header X) stay disabled until
    every registered relay has had its OFF attempt, i.e. progress == total.
    Shows the relay currently being switched OFF, live.
    """
    _PANEL = {   # state -> (bg, border, icon bg, icon text, title colour)
        "run":  ("#eef4ff", "#bcd3f8", "#dbe8fd", "↻", "#1565c0"),
        "ok":   ("#e8f5e9", "#bfe3c3", "#d3ecd6", "✓", "#1b7a2b"),
        "fail": ("#ffebee", "#f2b8bd", "#fbd5d8", "!", "#c62828"),
    }

    def __init__(self, relays, parent=None, send=_default_send):
        super().__init__(parent)
        self._done = False
        self.failed = []
        self._total = len(relays)
        self.setWindowTitle("Aborting Self Test")
        self.setModal(True)
        # Frameless + own header: no OS close button, cleanup must finish.
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(660)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)        # room for the shadow
        card = _Card()
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 70))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)

        root = QVBoxLayout(card)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header: logo + title + X (X enabled only when finished) ──────
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
        htitle = QLabel("Aborting Self Test")
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

        # ── Body ─────────────────────────────────────────────────────────
        body = QVBoxLayout()
        body.setContentsMargins(34, 6, 34, 26)
        body.setSpacing(10)

        self.badge = _StatusBadge(124)
        body.addWidget(self.badge, 0, Qt.AlignHCenter)

        self.title_lbl = QLabel("Aborting Self Test")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setFont(QFont("Arial", 22, QFont.Bold))
        self.title_lbl.setStyleSheet("color:#0d1b3e; background:transparent;")
        body.addWidget(self.title_lbl)

        self.status_lbl = QLabel(
            "Turning OFF all registered relays and returning to a safe idle state…")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setFont(QFont("Arial", 10))
        self.status_lbl.setStyleSheet("color:#5b6478; background:transparent;")
        body.addWidget(self.status_lbl)
        body.addSpacing(6)

        # progress row
        prow = QFrame()
        prow.setStyleSheet("QFrame { background:#eef3fb; border:none; border-radius:14px; }")
        pl = QHBoxLayout(prow)
        pl.setContentsMargins(16, 12, 16, 12)
        pl.setSpacing(14)
        self.bar = QProgressBar()
        self.bar.setRange(0, max(self._total, 1))
        self.bar.setValue(0 if self._total else 1)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(14)
        self._set_bar_color("#1976d2", "#42a5f5")
        self.pct_lbl = QLabel("0%")
        self.pct_lbl.setFont(QFont("Arial", 12, QFont.Bold))
        self.pct_lbl.setMinimumWidth(48)
        self.pct_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.pct_lbl.setStyleSheet("color:#1976d2; background:transparent;")
        pl.addWidget(self.bar, 1)
        pl.addWidget(self.pct_lbl, 0)
        body.addWidget(prow)

        # live status panel
        self.panel = QFrame()
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
        self._set_panel("run", "Preparing…", f"0 of {self._total} relays switched OFF")

        # finish button
        self.finish_btn = QPushButton("✓ Finish")
        self.finish_btn.setEnabled(False)
        self.finish_btn.setMinimumHeight(46)      # height only, no minimum width
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

        self._worker = AbortRelayCleanupWorker(relays, send, self)
        self._worker.starting.connect(self._on_starting)
        self._worker.attempted.connect(self._on_attempted)
        self._worker.all_done.connect(self._on_all_done)

    # ── helpers ──────────────────────────────────────────────────────────
    def _set_bar_color(self, c1, c2):
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background:#d5dde9; border:none; border-radius:7px; }}
            QProgressBar::chunk {{
                border-radius:7px;
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {c1}, stop:1 {c2});
            }}
        """)

    def _set_panel(self, state, title, sub):
        bg, border, ibg, itxt, tcol = self._PANEL[state]
        self.panel.setStyleSheet(
            f"QFrame {{ background:{bg}; border:1px solid {border}; border-radius:14px; }}")
        self.p_icon.setText(itxt)
        self.p_icon.setStyleSheet(
            f"background:{ibg}; color:{tcol}; border:none; border-radius:23px;")
        self.p_div.setStyleSheet(f"background:{tcol}; border:none;")
        self.p_title.setText(title)
        self.p_title.setFrameShape(QFrame.NoFrame)
        self.p_title.setStyleSheet(
            f"color:{tcol}; background:transparent; border:none;")
        self.p_sub.setText(sub)

    def exec_(self):
        self._worker.start()
        return super().exec_()

    # ── worker signals ───────────────────────────────────────────────────
    def _on_starting(self, done, total, label):
        # 'done' = relays already attempted; this one is number done+1
        self._set_panel("run", f"Switching {label} OFF…",
                        f"Relay {done + 1} of {total}")

    def _on_attempted(self, done, total, label, ok):
        self.bar.setValue(done)
        self.pct_lbl.setText(f"{int(done * 100 / max(total, 1))}%")

    def _on_all_done(self, failed):
        self.failed = failed
        self._done = True
        self.bar.setValue(self.bar.maximum())
        self.pct_lbl.setText("100%")
        if failed:
            self.badge.set_state("fail")
            self._set_bar_color("#c62828", "#ef5350")
            self.pct_lbl.setStyleSheet("color:#c62828; background:transparent;")
            self.status_lbl.setText("Cleanup finished with errors.")
            self._set_panel("fail", "Could not confirm OFF for some relays",
                            ", ".join(failed))
        else:
            self.badge.set_state("ok")
            self._set_bar_color("#2e7d32", "#66bb6a")
            self.pct_lbl.setStyleSheet("color:#2e7d32; background:transparent;")
            self.status_lbl.setText("Hardware is now in a safe state.")
            self._set_panel("ok", "All relays switched OFF",
                            "System is now in a safe state.")
        self.finish_btn.setEnabled(True)
        self.x_btn.setEnabled(True)

    # Block Esc / window close until cleanup has completed.
    def reject(self):
        if self._done:
            super().reject()

    def closeEvent(self, event):
        if self._done:
            event.accept()
        else:
            event.ignore()