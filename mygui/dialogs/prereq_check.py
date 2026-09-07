import os
import winreg
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from datetime import datetime
from PyQt5.QtGui import QIcon
from core.paths import RESOURCES_DIR
import sys

PREREQUISITES = [
    {
        "name": "APx500 Software",
        "registry_key": r"SOFTWARE\Audio Precision\APx500",
        "exe_path": r"\\?\C:\Program Files\Audio Precision\APx500 9.2\AudioPrecision.APx500.exe",
    },
    {
        "name": "LibreOffice",
        "registry_key": r"SOFTWARE\LibreOffice\LibreOffice",
        "exe_path": r"\\?\C:\Program Files\LibreOffice\program\soffice.exe",
    },
    {
        "name": "OCD Tool",
        "registry_key": r"SOFTWARE\Tektronix\TekVisa",
        "exe_path": r"\\?\C:\Program Files (x86)\Tektronix\OpenChoice PC Communication Software\OpenChoiceDesktop.exe",
    },
]


def check_registry(key_path: str) -> bool:
    try:
        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        winreg.OpenKey(reg, key_path)
        return True
    except (FileNotFoundError, OSError):
        return False

import hashlib
from db.db_paths import DATABASE_DIR  # make sure this resolves to {app}

def check_istj_integrity() -> bool:
    import hashlib

    try:
        exe_path = os.path.abspath(sys.executable)

        # Compute actual hash of this exe
        sha256 = hashlib.sha256()
        with open(exe_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual = sha256.hexdigest().lower()[:16]

        hash_file = DATABASE_DIR / "istj.hash"

        if not hash_file.exists():
            # First run (no installer): self-register this exe's hash as trusted
            hash_file.parent.mkdir(parents=True, exist_ok=True)
            hash_file.write_text(actual)
            print(f"[INTEGRITY] Hash file created on first run: {actual}")
            return True

        expected = hash_file.read_text().strip().lower()
        match = (actual == expected)
        if not match:
            print(f"[INTEGRITY] MISMATCH — expected: {expected[:16]}... got: {actual[:16]}...")
        return match

    except Exception as e:
        print(f"[INTEGRITY] Check failed: {e}")
        return False
    
def run_prereq_check() -> dict:
    results = {}

    # ISTJ integrity check — always first
    results["ISTJ"] = check_istj_integrity()

    for prereq in PREREQUISITES:
        reg_ok = check_registry(prereq["registry_key"])

        exe_path = prereq["exe_path"]
        if isinstance(exe_path, list):
            exe_ok = any(os.path.exists(p) for p in exe_path)
        else:
            exe_ok = os.path.exists(exe_path)

        results[prereq["name"]] = reg_ok and exe_ok

    return results


class PrereqCheckDialog(QDialog):
    def __init__(self, results: dict, parent=None):
        super().__init__(parent)
        self.all_passed = all(results.values())
        missing = sum(1 for v in results.values() if not v)

        self.setWindowTitle("ISTJ — System Readiness Check")
        self.setWindowIcon(QIcon(str(RESOURCES_DIR / "istj.png")))
        # Wider dialog so nothing gets clipped; height scales with number of prereqs
        self.setFixedSize(580, 120 + len(results) * 56 + 130)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.setStyleSheet("QDialog { background-color: #eaecef; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet("background-color: #ffffff; border: none;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(32, 20, 32, 18)
        header_layout.setSpacing(6)

        title = QLabel("System Readiness Check")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #1a5da8; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel("All components must be verified before test operations begin.")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet("color: #6b7280; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        # Allow the label to wrap if the window ever gets resized narrower
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)

        # ── Checksum display ──────────────────────────────────────
        try:
            from db.db_paths import DATABASE_DIR
            hash_file = DATABASE_DIR / "istj.hash"
            expected = hash_file.read_text().strip().upper()

            exe_path = os.path.abspath(sys.executable)
            sha256 = hashlib.sha256()
            with open(exe_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            actual = sha256.hexdigest().upper()[:16]

            if actual == expected:
                checksum_text = f"SOFTWARE CHECKSUM : {actual}"
                checksum_color = "#1a5da8"
            else:
                checksum_text = f"⚠  MISMATCH  |  Expected: {expected[:16]}...  Got: {actual[:16]}..."
                checksum_color = "#d32f2f"
        except Exception:
            checksum_text = "SOFTWARE CHECKSUM  unavailable"
            checksum_color = "#9ca3af"

        checksum_lbl = QLabel(checksum_text)
        checksum_lbl.setFont(QFont("Courier", 7))
        checksum_lbl.setStyleSheet(f"color: {checksum_color}; background: transparent;")
        checksum_lbl.setAlignment(Qt.AlignCenter)
        checksum_lbl.setWordWrap(True)
        header_layout.addWidget(checksum_lbl)

        root.addWidget(header)   # ← this line already exists, don't add it again


        # ── Thin blue accent line ─────────────────────────────────
        accent = QFrame()
        accent.setFixedHeight(3)
        accent.setStyleSheet("background-color: #1a5da8; border: none;")
        root.addWidget(accent)

        # ── Info bar ──────────────────────────────────────────────
        infobar = QFrame()
        infobar.setFixedHeight(30)
        infobar.setStyleSheet("background-color: #dde3ea; border: none;")
        info_layout = QHBoxLayout(infobar)
        info_layout.setContentsMargins(28, 0, 28, 0)

        info_left = QLabel("VERSION: 1.0.1-BETA")
        info_left.setFont(QFont("Courier", 8))
        info_left.setStyleSheet("color: #374151; background: transparent;")
        info_layout.addWidget(info_left)

        info_layout.addStretch()

        now = datetime.now().strftime("%d-%m-%Y  %H:%M")
        info_right = QLabel(now)
        info_right.setFont(QFont("Courier", 8))
        info_right.setStyleSheet("color: #374151; background: transparent;")
        info_layout.addWidget(info_right)

        root.addWidget(infobar)

        # ── Checklist body ────────────────────────────────────────
        body = QFrame()
        body.setStyleSheet("background-color: #eaecef; border: none;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 18, 24, 10)
        body_layout.setSpacing(10)

        for name, ok in results.items():
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #d1d5db;
                    border-radius: 6px;
                }
            """)
            row.setFixedHeight(48)

            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(16, 0, 16, 0)
            row_layout.setSpacing(12)

            # Status dot
            dot = QLabel("●")
            dot.setFont(QFont("Arial", 11))
            dot.setStyleSheet(
                f"color: {'#1a5da8' if ok else '#d32f2f'}; background: transparent; border: none;"
            )
            dot.setFixedWidth(18)
            row_layout.addWidget(dot)

            # Component name
            name_lbl = QLabel(name)
            name_lbl.setFont(QFont("Arial", 10, QFont.Bold))
            name_lbl.setStyleSheet("color: #1f2937; background: transparent; border: none;")
            row_layout.addWidget(name_lbl, 1)

            # Status badge
            badge = QLabel("Installed" if ok else "Not Found")
            badge.setFont(QFont("Arial", 9, QFont.Bold))
            badge.setFixedHeight(24)
            badge.setAlignment(Qt.AlignCenter)
            badge.setMinimumWidth(90)
            if ok:
                badge.setStyleSheet("""
                    color: #1a5da8;
                    background-color: #dbeafe;
                    border-radius: 12px;
                    padding: 0px 14px;
                    border: none;
                """)
            else:
                badge.setStyleSheet("""
                    color: #b91c1c;
                    background-color: #fee2e2;
                    border-radius: 12px;
                    padding: 0px 14px;
                    border: none;
                """)
            row_layout.addWidget(badge)
            body_layout.addWidget(row)

        # ── Status strip ──────────────────────────────────────────
        body_layout.addSpacing(8)
        strip = QFrame()
        strip.setStyleSheet(f"""
            QFrame {{
                background-color: {'#dbeafe' if self.all_passed else '#fee2e2'};
                border-left: 3px solid {'#1a5da8' if self.all_passed else '#d32f2f'};
                border-radius: 0px;
            }}
        """)
        strip_layout = QHBoxLayout(strip)
        strip_layout.setContentsMargins(14, 10, 14, 10)

        status_msg = (
            "All systems ready — click Proceed to continue."
            if self.all_passed
            else f"{missing} component{'s' if missing > 1 else ''} missing. Some features may not work."
        )
        strip_lbl = QLabel(status_msg)
        strip_lbl.setFont(QFont("Arial", 9))
        strip_lbl.setWordWrap(True)
        strip_lbl.setStyleSheet(
            f"color: {'#1e3a5f' if self.all_passed else '#7f1d1d'}; background: transparent; border: none;"
        )
        strip_layout.addWidget(strip_lbl)
        body_layout.addWidget(strip)

        body_layout.addStretch()
        root.addWidget(body)

        # ── Footer buttons ────────────────────────────────────────
        footer = QFrame()
        footer.setFixedHeight(66)
        footer.setStyleSheet("background-color: #eaecef; border: none;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 12, 24, 12)
        footer_layout.setSpacing(12)
        footer_layout.addStretch()

        if not self.all_passed:
            abort_btn = QPushButton("Cancel")
            abort_btn.setMinimumHeight(38)
            abort_btn.setMinimumWidth(110)
            abort_btn.setFont(QFont("Arial", 10, QFont.Bold))
            abort_btn.setCursor(Qt.PointingHandCursor)
            abort_btn.setStyleSheet("""
                QPushButton {
                    background-color: #eaecef;
                    color: #d32f2f;
                    border: 1.5px solid #d32f2f;
                    border-radius: 5px;
                    padding: 6px 16px;
                }
                QPushButton:hover { background-color: #fee2e2; }
                QPushButton:pressed { background-color: #fecaca; }
            """)
            abort_btn.clicked.connect(self.reject)
            footer_layout.addWidget(abort_btn)

            override_btn = QPushButton("Continue Anyway")
            override_btn.setMinimumHeight(38)
            override_btn.setFont(QFont("Arial", 10, QFont.Bold))
            override_btn.setCursor(Qt.PointingHandCursor)
            override_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f59e0b;
                    color: #ffffff;
                    border: none;
                    border-radius: 5px;
                    padding: 6px 20px;
                }
                QPushButton:hover { background-color: #d97706; }
                QPushButton:pressed { background-color: #b45309; }
            """)
            override_btn.clicked.connect(self.accept)
            footer_layout.addWidget(override_btn)

        else:
            proceed_btn = QPushButton("PROCEED")
            proceed_btn.setMinimumHeight(38)
            proceed_btn.setMinimumWidth(160)
            proceed_btn.setFont(QFont("Arial", 10, QFont.Bold))
            proceed_btn.setCursor(Qt.PointingHandCursor)
            proceed_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1a5da8;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 6px 22px;
                    letter-spacing: 1px;
                }
                QPushButton:hover { background-color: #154a8a; }
                QPushButton:pressed { background-color: #0f3860; }
            """)
            proceed_btn.clicked.connect(self.accept)
            footer_layout.addWidget(proceed_btn)

        footer_layout.addStretch()
        root.addWidget(footer)

        # ── Copyright bar ─────────────────────────────────────────
        copyright_bar = QFrame()
        copyright_bar.setFixedHeight(28)
        copyright_bar.setStyleSheet("background-color: #eaecef; border: none;")
        copy_layout = QHBoxLayout(copyright_bar)
        copy_layout.setContentsMargins(0, 0, 0, 0)

        copy_lbl = QLabel("© 2025 Zing Technologies. All rights reserved.")
        copy_lbl.setFont(QFont("Arial", 8))
        copy_lbl.setStyleSheet("color: #9ca3af; background: transparent;")
        copy_lbl.setAlignment(Qt.AlignCenter)
        copy_layout.addWidget(copy_lbl)

        root.addWidget(copyright_bar)