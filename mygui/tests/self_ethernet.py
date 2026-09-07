"""
Ethernet self-test module.

Provides EthernetTestDialog: a dedicated popup that:
  - pauses other device listeners while open, resumes them on close
  - reads live adapter details from the OS (adapter name, IP, MAC/physical
    address, link speed) defaulting every field to "None" until a
    connection is detected
  - shows a dynamic red/green status banner (matches provided reference UI)
    using check.png for the connected state and remove.png for disconnected
  - has a Ping button that:
      * if Ethernet is NOT detected -> warns "please ensure your system is
        connected to the internet" and does nothing else
      * if Ethernet IS detected -> launches Microsoft Edge via Selenium,
        navigates to www.google.com, and inspects whether the page
        actually rendered or whether the browser fell back to its
        offline/"dinosaur" error page. Logs the result into the self-test
        excel report:
            F19 = "successful PING"                     H19 = "PASS"
            F19 = "NO internet (ethernet detected)"      H19 = "FAIL"
  - has a Cancel button
"""

import platform
import re
import socket
import subprocess

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIcon, QPixmap

from openpyxl import load_workbook

from core.excel_logger import finalize_self_test_report
from core.paths import RESOURCES_DIR

PING_URL = "https://www.google.com/"
PING_HOST = "www.google.com"


# ──────────────────────────────────────────────────────────────────────────
# Detection helpers
# ──────────────────────────────────────────────────────────────────────────
def get_physical_address(adapter_name: str = None) -> str:
    system = platform.system()
    try:
        if system == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            output = subprocess.check_output(
                ["getmac", "/fo", "csv", "/v"],
                text=True, stderr=subprocess.DEVNULL, timeout=5,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            lines = [ln for ln in output.strip().splitlines() if ln.strip()]
            if len(lines) < 2:
                return None

            best_match = None
            for line in lines[1:]:
                # CSV fields look like: "Connection Name","Network Adapter","Physical Address","Transport Name"
                fields = [f.strip().strip('"') for f in line.split('","')]
                fields = [f.strip('"') for f in fields]
                if len(fields) < 3:
                    continue
                conn_name, adapter_desc, phys_addr = fields[0], fields[1], fields[2]
                if not phys_addr or phys_addr.upper() == "N/A":
                    continue

                normalized = phys_addr.replace("-", ":").upper()
                if adapter_name and (
                    adapter_name.lower() in conn_name.lower()
                    or adapter_name.lower() in adapter_desc.lower()
                ):
                    return normalized
                if best_match is None:
                    best_match = normalized
            return best_match
        else:
            output = subprocess.check_output(["ip", "link"], text=True, timeout=5)
            match = re.search(r"link/ether\s+([0-9a-fA-F:]{17})", output)
            if match:
                return match.group(1).upper()
    except Exception:
        pass
    return None


def get_ethernet_details() -> dict:
    """
    Returns adapter details. Every field defaults to None / "Not Connected"
    unless a live, up ethernet-type interface is found.
    """
    details = {
        "adapter": None,
        "ip": None,
        "mac": None,
        "speed": None,
        "status": "Not Connected",
    }
    try:
        import psutil
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for iface, st in stats.items():
            lname = iface.lower()
            is_eth_like = (
                "eth" in lname or "ethernet" in lname or lname.startswith("en")
            )
            is_virtual = any(
                k in lname for k in ("vmware", "virtual", "loopback", "lo",
                                     "docker", "vbox", "wi-fi", "wifi", "wlan")
            )
            if is_eth_like and not is_virtual and st.isup:
                details["adapter"] = iface
                details["speed"] = f"{st.speed} Mbps" if st.speed else "Unknown"
                details["status"] = "Connected"
                for addr in addrs.get(iface, []):
                    fam = str(addr.family)
                    if addr.family == socket.AF_INET:
                        details["ip"] = addr.address
                    elif "AF_LINK" in fam or "AF_PACKET" in fam:
                        details["mac"] = addr.address
                break
    except ImportError:
        # psutil not installed -> can't enumerate adapters; leave defaults.
        pass
    except Exception:
        pass

    # Prefer the OS-native physical-address lookup — more reliable than
    # psutil's AF_LINK entries, especially on Windows. Only fall back to
    # whatever psutil found (if anything) when this comes back empty.
    phys = get_physical_address(details.get("adapter"))
    if phys:
        details["mac"] = phys

    return details


def is_ethernet_connected() -> bool:
    return get_ethernet_details()["status"] == "Connected"


def verify_site_via_edge(url: str = PING_URL, timeout: int = 20,
                          sync_time: int = 20, log_callback=None) -> tuple:
    def _log(msg):
        if log_callback:
            log_callback(msg)

    try:
        from selenium import webdriver
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.edge.service import Service as EdgeService
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import WebDriverException, TimeoutException
    except ImportError:
        _log("selenium is not installed")
        return False, "selenium is not installed"

    options = EdgeOptions()
    options.add_argument("--start-maximized")

    service = EdgeService()
    if platform.system() == "Windows":
        service.creationflags = subprocess.CREATE_NO_WINDOW

    driver = None
    try:
        _log("Launching Microsoft Edge...")
        driver = webdriver.Edge(service=service, options=options)
        driver.set_page_load_timeout(timeout)

        try:
            _log(f"Navigating to {url} ...")
            driver.get(url)
        except TimeoutException:
            _log("Page load timed out — checking current page state before failing.")

        _log(f"Waiting up to {sync_time}s for page to fully render...")
        try:
            WebDriverWait(driver, sync_time).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            _log("Page reported readyState=complete.")
        except TimeoutException:
            _log(f"readyState never reached 'complete' within {sync_time}s — proceeding with current state.")

        error_markers = (
            "err_internet_disconnected",
            "err_connection",
            "err_name_not_resolved",
            "no internet connection",
            "there is no internet connection",
        )

        import time as _t

        def _settle(max_wait=4.0, interval=0.5):
            # Let a same-tick auto-retry/redirect settle before judging. A single
            # blind 1.0s sleep was too short on some systems — Chromium's
            # interstitial-to-real-page swap can take longer, which was the
            # source of the false FAIL even though the page visibly finished
            # loading a moment later.
            waited = 0.0
            while waited < max_wait:
                _t.sleep(interval)
                waited += interval
                _src = (driver.page_source or "").lower()
                if _src.strip() and not any(m in _src for m in error_markers):
                    return
        _settle()

        # Chromium sometimes shows a transient offline/error interstitial
        # for a moment before auto-retrying and loading the real page.
        # Re-check a few times instead of trusting a single snapshot.
        import time
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            current_url = (driver.current_url or "").lower()
            title = (driver.title or "").lower()
            page_source = (driver.page_source or "").lower()

            is_error_scheme = current_url.startswith("edge-error://") or current_url.startswith("chrome-error://")
            # Only check the short, reliable `title` for error text — scanning the
            # full page_source was matching marker substrings that legitimately
            # appear inside Google's own HTML/JS/query-strings, which produced a
            # false FAIL even after the page had genuinely finished loading.
            has_error_marker = any(m in title for m in error_markers)
            page_loaded = bool(title.strip()) or "google" in current_url

            if not is_error_scheme and not has_error_marker and page_source.strip() and page_loaded:
                _log("Page loaded successfully.")
                return True, "page loaded successfully"

            if attempt < max_attempts:
                _log(f"Interstitial/error state detected (attempt {attempt}/{max_attempts}) — re-navigating in 2s...")
                time.sleep(2)
                try:
                    driver.get(url)
                    WebDriverWait(driver, sync_time).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except TimeoutException:
                    _log("Re-navigation readyState timeout — proceeding with current state.")
                except WebDriverException as re_nav_e:
                    _log(f"Re-navigation failed: {re_nav_e}")
                _settle()

        if current_url.startswith("edge-error://") or current_url.startswith("chrome-error://"):
            _log("Browser redirected to offline error page.")
            return False, "browser redirected to offline error page"
        if not page_source.strip():
            _log("Page did not render (empty response).")
            return False, "page did not render (empty response)"

        _log("Offline/error page detected.")
        return False, "offline/error page detected"

    except WebDriverException as e:
        _log(f"WebDriver error: {e}")
        return False, f"webdriver error: {e}"
    except Exception as e:
        _log(f"Unexpected error: {e}")
        return False, f"unexpected error: {e}"
    finally:
        if driver is not None:
            try:
                driver.quit()
                _log("Closed Edge session.")
            except Exception:
                pass


def log_ping_result_to_excel(report_path, success: bool, ethernet_connected: bool):
    """Writes the ping outcome into the self-test report at F19 / H19."""
    if not report_path:
        return
    try:
        wb = load_workbook(report_path)
        ws = wb.active
        if success:
            ws["F19"] = "successful PING"
            ws["H19"] = "PASS"
        else:
            ws["F19"] = ("NO internet (ethernet detected)" if ethernet_connected
                          else "NO ethernet detected")
            ws["H19"] = "FAIL"
        wb.save(report_path)
    except Exception as e:
        print(f"[ETHERNET SELF TEST] Excel log failed (non-fatal): {e}")


# ──────────────────────────────────────────────────────────────────────────
# Small UI helpers
# ──────────────────────────────────────────────────────────────────────────
def _icon_pixmap(filename: str, size: int) -> QPixmap:
    path = RESOURCES_DIR / filename
    pix = QPixmap(str(path))
    if pix.isNull():
        return QPixmap()
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


class _InfoRow(QFrame):
    """One row inside the Adapter Information card: icon + label + value."""
    def __init__(self, icon_filename: str, label_text: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { border: none; background: transparent; }")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 10, 0, 10)
        row.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(28, 28)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("border:none; background:transparent;")
        pix = _icon_pixmap(icon_filename, 22)
        if not pix.isNull():
            icon_lbl.setPixmap(pix)
        row.addWidget(icon_lbl, 0)

        name_lbl = QLabel(label_text)
        name_lbl.setFont(QFont("Arial", 10, QFont.Bold))
        name_lbl.setStyleSheet("color:#1a1a2e; border:none; background:transparent; padding:0px;")
        row.addWidget(name_lbl, 1)

        self.value_lbl = QLabel("None")
        self.value_lbl.setFont(QFont("Arial", 10))
        self.value_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_lbl.setStyleSheet("color:#6b7280; border:none; background:transparent; padding:0px;")
        row.addWidget(self.value_lbl, 0)

    def set_value(self, text: str):
        self.value_lbl.setText(text or "None")


def _hline() -> QFrame:
    line = QFrame()
    line.setFixedHeight(1)
    line.setStyleSheet("background-color:#e5e7eb; border:none;")
    return line


# ──────────────────────────────────────────────────────────────────────────
# Dialog
# ──────────────────────────────────────────────────────────────────────────
class EthernetTestDialog(QDialog):
    def __init__(self, parent=None, report_path=None):
        super().__init__(parent)
        self._report_path = report_path
        self._monitor = getattr(parent, "_monitor", None) if parent else None
        self._listeners_paused = False
        self._ethernet_connected = False
        self.test_completed = False
        self.test_result = "PASS"
        self.log_lines = []

        self.setWindowTitle("Ethernet Self Test")
        icon_path = RESOURCES_DIR / "ethernet1.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        from core.screen_utils import responsive_size
        self.resize(responsive_size(0.32, 0.75, min_w=520, min_h=620, max_w=760, max_h=900))
        self.setMinimumSize(480, 560)
        self.setStyleSheet("""
            QDialog { background-color: #f5f7fa; }
            QLabel  { background: transparent; border: none; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 22, 24, 22)
        outer.setSpacing(16)

        # ── Header: circular port icon + title/subtitle ─────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        icon_badge = QLabel()
        icon_badge.setFixedSize(64, 64)
        icon_badge.setAlignment(Qt.AlignCenter)
        icon_badge.setStyleSheet("""
            QLabel {
                background-color: #e3f0ff;
                border-radius: 32px;
            }
        """)
        pix = _icon_pixmap("ethernet1.png", 34)
        if not pix.isNull():
            icon_badge.setPixmap(pix)
        header_row.addWidget(icon_badge, 0, Qt.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title_lbl = QLabel("Ethernet Self Test")
        title_lbl.setFont(QFont("Arial", 20, QFont.Bold))
        title_lbl.setStyleSheet("color:#0d1b3e;")
        title_col.addWidget(title_lbl)
        subtitle_lbl = QLabel("Checking adapter status and internet connectivity.")
        subtitle_lbl.setFont(QFont("Arial", 10))
        subtitle_lbl.setStyleSheet("color:#6b7280;")
        title_col.addWidget(subtitle_lbl)
        header_row.addLayout(title_col, 1)

        outer.addLayout(header_row)

        # ── Scrollable body: banner + adapter info + activity log ───────
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.body_scroll.setFrameShape(QFrame.NoFrame)
        self.body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 8px; background: #f1f3f5; }
            QScrollBar::handle:vertical { background:#c0c0c0; border-radius:4px; min-height:30px; }
            QScrollBar::handle:vertical:hover { background:#a0a0a0; }
        """)

        body_widget = QWidget()
        body_widget.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 4, 0)
        body_layout.setSpacing(14)

        # ── Status banner (dynamic red / green) ──────────────────────────
        self.banner = QFrame()
        self.banner.setMinimumHeight(72)
        self.banner.setMaximumHeight(84)
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(14, 8, 14, 8)
        banner_layout.setSpacing(12)

        self.banner_badge_lbl = QLabel()
        self.banner_badge_lbl.setFixedSize(32, 32)
        self.banner_badge_lbl.setAlignment(Qt.AlignCenter)
        banner_layout.addWidget(self.banner_badge_lbl, 0, Qt.AlignVCenter)

        banner_text_col = QVBoxLayout()
        banner_text_col.setSpacing(1)
        self.banner_title_lbl = QLabel("Status: Not Connected")
        self.banner_title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        self.banner_title_lbl.setStyleSheet("border: none; background: transparent; padding: 0px;")
        banner_text_col.addWidget(self.banner_title_lbl)
        self.banner_sub_lbl = QLabel("No active Ethernet connection detected.")
        self.banner_sub_lbl.setFont(QFont("Arial", 9))
        self.banner_sub_lbl.setStyleSheet("color:#374151; border: none; background: transparent; padding: 0px;")
        self.banner_sub_lbl.setWordWrap(True)
        banner_text_col.addWidget(self.banner_sub_lbl)
        banner_layout.addLayout(banner_text_col, 1)

        self._graphic_container = QWidget()
        self._graphic_container.setFixedSize(60, 60)
        self._graphic_container.setStyleSheet("border: none; background: transparent;")
        self.cable_lbl = QLabel(self._graphic_container)
        self.cable_lbl.setGeometry(0, 0, 60, 60)
        self.cable_lbl.setAlignment(Qt.AlignCenter)
        self.cable_lbl.setStyleSheet("border: none; background: transparent;")
        self.corner_badge_lbl = QLabel(self._graphic_container)
        self.corner_badge_lbl.setGeometry(36, 36, 22, 22)
        self.corner_badge_lbl.setAlignment(Qt.AlignCenter)
        self.corner_badge_lbl.setStyleSheet("border: none; background: transparent;")
        banner_layout.addWidget(self._graphic_container, 0, Qt.AlignVCenter)

        body_layout.addWidget(self.banner)

        # ── Adapter Information card ─────────────────────────────────────
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 16, 20, 8)
        info_layout.setSpacing(2)

        info_header = QHBoxLayout()
        info_header.setSpacing(10)
        info_icon = QLabel("i")
        info_icon.setFixedSize(24, 24)
        info_icon.setAlignment(Qt.AlignCenter)
        info_icon.setFont(QFont("Arial", 10, QFont.Bold))
        info_icon.setStyleSheet("""
            QLabel { background-color:#1976d2; color:white; border-radius:12px; }
        """)
        info_header.addWidget(info_icon, 0)
        info_title = QLabel("Adapter Information")
        info_title.setFont(QFont("Arial", 12, QFont.Bold))
        info_title.setStyleSheet("color:#0d1b3e; border:none; background:transparent; padding:0px;")
        info_header.addWidget(info_title, 1)

        self.info_toggle_btn = QPushButton("\u25BC")
        self.info_toggle_btn.setFixedSize(24, 24)
        self.info_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.info_toggle_btn.setStyleSheet("""
            QPushButton { border:none; background:transparent; color:#6b7280; font-size:11px; }
            QPushButton:hover { color:#1976d2; }
        """)
        self.info_toggle_btn.clicked.connect(self._toggle_info_card)
        info_header.addWidget(self.info_toggle_btn, 0)

        info_layout.addLayout(info_header)
        info_layout.addSpacing(6)

        # No nested scroll area anymore — this content scrolls as part of
        # the shared body_scroll, so it can just lay out naturally.
        self.info_content = QWidget()
        self.info_content.setStyleSheet("background: transparent; border: none;")
        info_content_layout = QVBoxLayout(self.info_content)
        info_content_layout.setContentsMargins(0, 0, 0, 0)
        info_content_layout.setSpacing(0)

        self.adapter_row = _InfoRow("monitor.png", "Adapter")
        info_content_layout.addWidget(self.adapter_row)
        info_content_layout.addWidget(_hline())

        self.ip_row = _InfoRow("ip.png", "IP Address")
        info_content_layout.addWidget(self.ip_row)
        info_content_layout.addWidget(_hline())

        self.mac_row = _InfoRow("mac.png", "MAC Address")
        info_content_layout.addWidget(self.mac_row)
        info_content_layout.addWidget(_hline())

        self.speed_row = _InfoRow("speed.png", "Link Speed")
        info_content_layout.addWidget(self.speed_row)

        info_layout.addWidget(self.info_content)
        body_layout.addWidget(info_card, 0)

        # ── Activity console — shows live progress during Ping ──────────
        console_label = QLabel("Activity Log")
        console_label.setFont(QFont("Arial", 10, QFont.Bold))
        console_label.setStyleSheet("color:#0d1b3e; margin-top:4px;")
        body_layout.addWidget(console_label)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumHeight(160)
        self.console.setFont(QFont("Consolas", 9))
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color:#0d1117; color:#c9d1d9;
                border:1px solid #30363d; border-radius:8px; padding:8px;
            }
        """)
        self.console.setPlaceholderText("Press Ping to run diagnostics...")
        body_layout.addWidget(self.console, 1)

        self.body_scroll.setWidget(body_widget)
        outer.addWidget(self.body_scroll, 1)

        # ── Ping result line (only shown after a ping attempt) ───────────
        self.result_lbl = QLabel("")
        self.result_lbl.setFont(QFont("Arial", 10, QFont.Bold))
        self.result_lbl.setWordWrap(True)
        self.result_lbl.setAlignment(Qt.AlignCenter)
        outer.addWidget(self.result_lbl)

        # ── Buttons + subtext ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        ping_col = QVBoxLayout()
        ping_col.setSpacing(6)
        self.ping_btn = QPushButton("  Ping")
        self.ping_btn.setMinimumHeight(52)
        self.ping_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.ping_btn.setCursor(Qt.PointingHandCursor)
        heartbeat_pix = _icon_pixmap("heartbeat.png", 20)
        if not heartbeat_pix.isNull():
            self.ping_btn.setIcon(QIcon(str(RESOURCES_DIR / "heartbeat.png")))
            self.ping_btn.setIconSize(QSize(20, 20))
        self.ping_btn.setStyleSheet("""
            QPushButton { background:#1976d2; color:white; border-radius:10px; border:none; }
            QPushButton:hover { background:#1565c0; }
            QPushButton:pressed { background:#0d47a1; }
            QPushButton:disabled { background:#90a4c4; color:#eef2ff; }
        """)
        self.ping_btn.clicked.connect(self._on_ping)
        ping_col.addWidget(self.ping_btn)
        ping_hint = QLabel("Test connectivity to a host")
        ping_hint.setAlignment(Qt.AlignCenter)
        ping_hint.setFont(QFont("Arial", 8))
        ping_hint.setStyleSheet("color:#9ca3af;")
        ping_col.addWidget(ping_hint)
        btn_row.addLayout(ping_col, 1)

        cancel_col = QVBoxLayout()
        cancel_col.setSpacing(6)
        self.cancel_btn = QPushButton("  Close")
        self.cancel_btn.setMinimumHeight(52)
        self.cancel_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        remove_pix = _icon_pixmap("remove.png", 20)
        if not remove_pix.isNull():
            self.cancel_btn.setIcon(QIcon(str(RESOURCES_DIR / "remove.png")))
            self.cancel_btn.setIconSize(QSize(20, 20))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background:#ffffff; color:#374151; border:1.5px solid #d1d5db;
                border-radius:10px;
            }
            QPushButton:hover { background:#f3f4f6; }
        """)
        self.cancel_btn.clicked.connect(self.close)
        cancel_col.addWidget(self.cancel_btn)
        cancel_hint = QLabel("Close this window")
        cancel_hint.setAlignment(Qt.AlignCenter)
        cancel_hint.setFont(QFont("Arial", 8))
        cancel_hint.setStyleSheet("color:#9ca3af;")
        cancel_col.addWidget(cancel_hint)
        btn_row.addLayout(cancel_col, 1)

        outer.addLayout(btn_row)

        self._pause_listeners()
        self._refresh_status()

        # ── Live auto-detect: poll adapter status while dialog is open ──
        self._ping_in_progress = False
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._auto_poll_status)
        self._poll_timer.start(2000)   # check every 2s

    # ------------------------------------------------------------------
    def _pause_listeners(self):
        if self._monitor is not None and not self._listeners_paused:
            for lst in getattr(self._monitor, "_listeners", []):
                try:
                    lst.pause()
                except Exception:
                    pass
            self._listeners_paused = True

    def _resume_listeners(self):
        if self._monitor is not None and self._listeners_paused:
            for lst in getattr(self._monitor, "_listeners", []):
                try:
                    lst.resume()
                except Exception:
                    pass
            self._listeners_paused = False

    def _toggle_info_card(self):
        expanded = self.info_content.isVisible()
        self.info_content.setVisible(not expanded)
        self.info_toggle_btn.setText("\u25B6" if expanded else "\u25BC")
        self.info_content.updateGeometry()
        self.layout().activate()
        self.updateGeometry()
        self.update()

    def _log_console(self, msg: str):
        ts = QTime.currentTime().toString("HH:mm:ss")
        line = f"[{ts}] {msg}"
        self.log_lines.append(line)
        self.console.appendPlainText(line)
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())
        QApplication.processEvents()

    def _set_banner_style(self, connected: bool):
        if connected:
            self.banner.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e9;
                    border: 1px solid #66bb6a;
                    border-radius: 12px;
                }
            """)
            self.banner_title_lbl.setStyleSheet(
                "color:#2e7d32; border:none; background:transparent; padding:0px;"
            )
            self.banner_badge_lbl.setText("")
            check_pix = _icon_pixmap("check.png", 40)
            if not check_pix.isNull():
                self.banner_badge_lbl.setPixmap(check_pix)
                self.banner_badge_lbl.setStyleSheet("background: transparent; border:none;")
            else:
                self.banner_badge_lbl.setStyleSheet("""
                    QLabel { background-color:#2e7d32; border-radius:22px; color:white; border:none; }
                """)
                self.banner_badge_lbl.setText("\u2713")
                self.banner_badge_lbl.setFont(QFont("Arial", 16, QFont.Bold))
        else:
            self.banner.setStyleSheet("""
                QFrame {
                    background-color: #ffebee;
                    border: 1px solid #ef9a9a;
                    border-radius: 12px;
                }
            """)
            self.banner_title_lbl.setStyleSheet(
                "color:#c62828; border:none; background:transparent; padding:0px;"
            )
            self.banner_badge_lbl.setText("")
            remove_pix = _icon_pixmap("remove.png", 40)
            if not remove_pix.isNull():
                self.banner_badge_lbl.setPixmap(remove_pix)
                self.banner_badge_lbl.setStyleSheet("background: transparent; border:none;")
            else:
                self.banner_badge_lbl.setStyleSheet("""
                    QLabel { background-color:#c62828; border-radius:22px; color:white; border:none; }
                """)
                self.banner_badge_lbl.setText("\u2715")
                self.banner_badge_lbl.setFont(QFont("Arial", 16, QFont.Bold))

        # Cable graphic + corner badge
        cable_pix = _icon_pixmap("ethernet2.png", 50)
        if not cable_pix.isNull():
            self.cable_lbl.setPixmap(cable_pix)

        if connected:
            check_pix_small = _icon_pixmap("check.png", 28)
            self.corner_badge_lbl.setText("")
            if not check_pix_small.isNull():
                self.corner_badge_lbl.setPixmap(check_pix_small)
                self.corner_badge_lbl.setStyleSheet("background: transparent; border:none;")
            else:
                self.corner_badge_lbl.setStyleSheet("""
                    QLabel { background-color:#2e7d32; border-radius:16px; color:white; border:none; }
                """)
                self.corner_badge_lbl.setText("\u2713")
                self.corner_badge_lbl.setFont(QFont("Arial", 12, QFont.Bold))
        else:
            remove_pix_small = _icon_pixmap("remove.png", 28)
            self.corner_badge_lbl.setText("")
            if not remove_pix_small.isNull():
                self.corner_badge_lbl.setPixmap(remove_pix_small)
                self.corner_badge_lbl.setStyleSheet("background: transparent; border:none;")
            else:
                self.corner_badge_lbl.setStyleSheet("""
                    QLabel { background-color:#c62828; border-radius:16px; color:white; border:none; }
                """)
                self.corner_badge_lbl.setText("\u2715")
                self.corner_badge_lbl.setFont(QFont("Arial", 12, QFont.Bold))
        self.corner_badge_lbl.raise_()

    def _refresh_status(self):
        details = get_ethernet_details()
        connected = details["status"] == "Connected"
        self._ethernet_connected = connected

        self._set_banner_style(connected)

        if connected:
            self.banner_title_lbl.setText("Status: Connected")
            self.banner_sub_lbl.setText("Ethernet adapter is active and online.")
        else:
            self.banner_title_lbl.setText("Status: Not Connected")
            self.banner_sub_lbl.setText("No active Ethernet connection detected.")

        self.adapter_row.set_value(details["adapter"])
        self.ip_row.set_value(details["ip"])
        self.mac_row.set_value(details["mac"])
        self.speed_row.set_value(details["speed"])
        
    def _auto_poll_status(self):
        """Runs every 2s while the dialog is open. Detects cable plug/unplug
        without requiring the user to click Ping."""
        if self._ping_in_progress:
            return  # don't fight with an in-flight Selenium ping
        was_connected = self._ethernet_connected
        self._refresh_status()
        if was_connected != self._ethernet_connected:
            # Connection state flipped — clear any stale ping result text
            self.result_lbl.setText("")

    def _on_ping(self):
        self._refresh_status()
        self.console.clear()

        if not self._ethernet_connected:
            self._log_console("Ping aborted — no Ethernet adapter detected.")
            QMessageBox.warning(
                self, "No Ethernet Connection",
                "Please ensure your system is connected to the internet."
            )
            return
        self._ping_in_progress = True
        self.ping_btn.setEnabled(False)
        self.ping_btn.setText("Launching Edge...")
        self.result_lbl.setText(f"Opening {PING_HOST} in Microsoft Edge...")
        self.result_lbl.setStyleSheet("color:#374151;")
        self._log_console("Ethernet detected — starting connectivity check.")
        QApplication.processEvents()

        success, reason = verify_site_via_edge(PING_URL, sync_time=20, log_callback=self._log_console)

        if success:
            self.result_lbl.setText("\u2713 successful PING")
            self.result_lbl.setStyleSheet("color:#2e7d32;")
            self.test_result = "PASS"
        else:
            self.result_lbl.setText(f"\u2715 NO internet (ethernet detected) \u2014 {reason}")
            self.result_lbl.setStyleSheet("color:#c62828;")
            self.test_result = "FAIL"

        self._log_console(f"Result: {'PASS' if success else 'FAIL'} — {reason}")
        log_ping_result_to_excel(self._report_path, success, self._ethernet_connected)

        try:
            xlsx_path, pdf_path = finalize_self_test_report(
                "ETHERNET", self.test_result, self.log_lines
            )
            self._final_xlsx = xlsx_path
            self._final_pdf = pdf_path
            self._log_console(f"Report finalized → {pdf_path}")
        except Exception as e:
            self._log_console(f"Report finalize failed (non-fatal): {e}")
            self._final_xlsx = None
            self._final_pdf = None

        self.ping_btn.setEnabled(True)
        self.ping_btn.setText("  Ping")
        self.test_completed = True
        self._ping_in_progress = False

    def closeEvent(self, event):
        if hasattr(self, "_poll_timer"):
            self._poll_timer.stop()
        self._resume_listeners()
        event.accept()
        self.done(QDialog.Accepted if self.test_completed else QDialog.Rejected)

def run(screen):
    """
    Kept only for backward compatibility with SelfTestWorker._SELF_TEST_MAP.
    Ethernet no longer runs through the generic worker thread — it uses its
    own EthernetTestDialog instead (see _on_merged_self_test wiring).
    """
    pass