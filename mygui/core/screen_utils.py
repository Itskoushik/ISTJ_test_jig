"""
core/screen_utils.py

Centralized helpers for making windows, dialogs, and popups responsive
across different monitor sizes and DPI settings, instead of hardcoding
pixel values that only look right on one screen.
"""
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSize


def _screen_geometry():
    screen = QApplication.primaryScreen()
    return screen.availableGeometry() if screen else None


def scale_factor() -> float:
    """
    Multiplier based on the current screen's logical DPI vs a 96-DPI
    baseline (Windows 100% scaling). Use to scale fonts/padding/icons so
    proportions hold on high-DPI or scaled displays.
    """
    screen = QApplication.primaryScreen()
    if not screen:
        return 1.0
    dpi = screen.logicalDotsPerInch()
    return max(0.85, min(dpi / 96.0, 1.6))   # clamp so text never gets silly tiny/huge


def sp(value: int) -> int:
    """Scale a pixel/point value by the current DPI scale factor."""
    return int(round(value * scale_factor()))


def responsive_size(width_ratio: float, height_ratio: float,
                     min_w: int = None, min_h: int = None,
                     max_w: int = None, max_h: int = None) -> QSize:
    """
    A QSize that is a ratio of the *available* screen size (excludes
    taskbars), clamped to sane min/max bounds. Use instead of
    setFixedSize/setMinimumSize(hardcoded, hardcoded).
    """
    geo = _screen_geometry()
    if geo is None:
        w, h = 1000, 700
    else:
        w = int(geo.width() * width_ratio)
        h = int(geo.height() * height_ratio)

    if min_w: w = max(w, min_w)
    if min_h: h = max(h, min_h)
    if max_w: w = min(w, max_w)
    if max_h: h = min(h, max_h)
    return QSize(w, h)


def responsive_geometry(width_ratio: float, height_ratio: float,
                         min_w: int = None, min_h: int = None,
                         max_w: int = None, max_h: int = None):
    """
    Like responsive_size, but also returns a centered (x, y) position —
    handy for QMainWindow.setGeometry(x, y, w, h).
    """
    size = responsive_size(width_ratio, height_ratio, min_w, min_h, max_w, max_h)
    geo = _screen_geometry()
    if geo is None:
        return 100, 100, size.width(), size.height()
    x = geo.x() + (geo.width() - size.width()) // 2
    y = geo.y() + (geo.height() - size.height()) // 2
    return x, y, size.width(), size.height()