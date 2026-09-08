#!/usr/bin/env python3
"""Minimalist world clock: selected country's time vs. Brazil's time."""
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QFont, QColor, QCursor
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QGraphicsDropShadowEffect, QFrame,
)


def flag_emoji(country_code: str) -> str:
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in country_code.upper())


BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")
BRAZIL_CODE = "BR"
BRAZIL_LABEL = f"{flag_emoji(BRAZIL_CODE)}  Brazil (Brasília)"

# (display name, IANA tz, ISO country code for the flag)
COUNTRIES = [
    ("Argentina", "America/Argentina/Buenos_Aires", "AR"),
    ("Australia (Sydney)", "Australia/Sydney", "AU"),
    ("Austria", "Europe/Vienna", "AT"),
    ("Belgium", "Europe/Brussels", "BE"),
    ("Canada (Toronto)", "America/Toronto", "CA"),
    ("Chile", "America/Santiago", "CL"),
    ("China", "Asia/Shanghai", "CN"),
    ("Egypt", "Africa/Cairo", "EG"),
    ("Finland", "Europe/Helsinki", "FI"),
    ("France", "Europe/Paris", "FR"),
    ("Germany", "Europe/Berlin", "DE"),
    ("Greece", "Europe/Athens", "GR"),
    ("India", "Asia/Kolkata", "IN"),
    ("Indonesia (Jakarta)", "Asia/Jakarta", "ID"),
    ("Ireland", "Europe/Dublin", "IE"),
    ("Israel", "Asia/Jerusalem", "IL"),
    ("Italy", "Europe/Rome", "IT"),
    ("Japan", "Asia/Tokyo", "JP"),
    ("Mexico", "America/Mexico_City", "MX"),
    ("Netherlands", "Europe/Amsterdam", "NL"),
    ("New Zealand", "Pacific/Auckland", "NZ"),
    ("Nigeria", "Africa/Lagos", "NG"),
    ("Norway", "Europe/Oslo", "NO"),
    ("Philippines", "Asia/Manila", "PH"),
    ("Poland", "Europe/Warsaw", "PL"),
    ("Portugal", "Europe/Lisbon", "PT"),
    ("Russia (Moscow)", "Europe/Moscow", "RU"),
    ("Saudi Arabia", "Asia/Riyadh", "SA"),
    ("Singapore", "Asia/Singapore", "SG"),
    ("South Africa", "Africa/Johannesburg", "ZA"),
    ("South Korea", "Asia/Seoul", "KR"),
    ("Spain", "Europe/Madrid", "ES"),
    ("Sweden", "Europe/Stockholm", "SE"),
    ("Switzerland", "Europe/Zurich", "CH"),
    ("Thailand", "Asia/Bangkok", "TH"),
    ("Turkey", "Europe/Istanbul", "TR"),
    ("United Arab Emirates", "Asia/Dubai", "AE"),
    ("United Kingdom", "Europe/London", "GB"),
    ("United States (Los Angeles)", "America/Los_Angeles", "US"),
    ("United States (New York)", "America/New_York", "US"),
    ("Vietnam", "Asia/Ho_Chi_Minh", "VN"),
]

WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

ACCENT = "#7C8CFF"
ACCENT_SOFT = "rgba(124, 140, 255, 0.16)"
BG_CARD = "#171821"
BG_CARD_TOP = "#1c1e29"
BORDER = "rgba(255, 255, 255, 0.07)"
TEXT_PRIMARY = "#F2F3F8"
TEXT_MUTED = "#8B8FA3"


def format_offset(dt: datetime) -> str:
    offset = dt.utcoffset()
    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    h, m = divmod(total_minutes, 60)
    return f"UTC{sign}{h}" + (f":{m:02d}" if m else "")


def format_diff(dt_target: datetime, dt_brazil: datetime) -> str:
    delta_minutes = int((dt_target.utcoffset() - dt_brazil.utcoffset()).total_seconds() // 60)
    sign = "+" if delta_minutes >= 0 else "-"
    delta_minutes = abs(delta_minutes)
    h, m = divmod(delta_minutes, 60)
    if delta_minutes == 0:
        return "same time"
    txt = f"{sign}{h}h"
    if m:
        txt += f"{m:02d}"
    return txt


def format_date(dt: datetime) -> str:
    return f"{WEEKDAYS_EN[dt.weekday()]}, {MONTHS_EN[dt.month - 1]} {dt.day}"


class WorldClock(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("aceaswall", "WorldClock")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(612, 314)
        self._drag_pos = None
        self._build_ui()
        self._restore_selection()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)
        self._tick()

    # ---------- UI ----------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(50, 46, 50, 56)

        self.card = QFrame(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet(f"""
            #card {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BG_CARD_TOP}, stop:1 {BG_CARD});
                border-radius: 22px;
                border: 1px solid {BORDER};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 70))
        self.card.setGraphicsEffect(shadow)
        outer.addWidget(self.card)

        root = QVBoxLayout(self.card)
        root.setContentsMargins(28, 20, 20, 24)
        root.setSpacing(0)

        # top bar: title tag + close button
        top_bar = QHBoxLayout()
        tag = QLabel("WORLD CLOCK")
        tag.setStyleSheet(f"color: {TEXT_MUTED}; letter-spacing: 2px;")
        tag.setFont(QFont("Noto Sans", 9, QFont.DemiBold))
        top_bar.addWidget(tag)
        top_bar.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                color: {TEXT_MUTED};
                background: transparent;
                border: none;
                font-size: 18px;
                border-radius: 13px;
            }}
            QPushButton:hover {{
                color: {TEXT_PRIMARY};
                background: rgba(255,255,255,0.08);
            }}
        """)
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        root.addLayout(top_bar)
        root.addSpacing(18)

        body = QHBoxLayout()
        body.setSpacing(28)

        # ---- left: selected country big clock ----
        left = QVBoxLayout()
        left.setSpacing(6)
        left.addStretch()

        self.time_label = QLabel("--:--")
        self.time_label.setFont(QFont("Noto Sans Mono", 52, QFont.Medium))
        self.time_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        left.addWidget(self.time_label)

        self.date_label = QLabel("")
        self.date_label.setFont(QFont("Noto Sans", 11))
        self.date_label.setStyleSheet(f"color: {TEXT_MUTED};")
        left.addWidget(self.date_label)
        left.addStretch()
        body.addLayout(left, 1)

        # vertical divider
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setStyleSheet(f"background: {BORDER}; max-width: 1px; border: none;")
        body.addWidget(divider)

        # ---- right: country picker + brazil info ----
        right = QVBoxLayout()
        right.setSpacing(10)
        right.addStretch()

        self.country_combo = QComboBox()
        self.country_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        for name, tz, code in COUNTRIES:
            self.country_combo.addItem(f"{flag_emoji(code)}  {name}", (tz, code))
        self.country_combo.setFont(QFont("Noto Sans", 15, QFont.DemiBold))
        self.country_combo.setCursor(QCursor(Qt.PointingHandCursor))
        self.country_combo.setToolTip("Click to change country")
        self.country_combo.setStyleSheet(f"""
            QComboBox {{
                color: {TEXT_PRIMARY};
                background: transparent;
                border: none;
                border-bottom: 1px dashed rgba(255, 255, 255, 0.28);
                padding: 2px 0 5px 0;
            }}
            QComboBox:hover {{
                color: {ACCENT};
                border-bottom: 1px dashed {ACCENT};
            }}
            QComboBox::drop-down {{ width: 0; border: none; }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD_TOP};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 10px;
                selection-background-color: {ACCENT_SOFT};
                outline: none;
                padding: 6px;
            }}
        """)
        self.country_combo.currentIndexChanged.connect(self._save_selection)
        right.addWidget(self.country_combo, 0, Qt.AlignLeft)

        self.offset_label = QLabel("UTC+0")
        self.offset_label.setFont(QFont("Noto Sans Mono", 10))
        self.offset_label.setStyleSheet(f"color: {TEXT_MUTED};")
        right.addWidget(self.offset_label)

        right.addSpacing(6)

        brazil_row = QHBoxLayout()
        brazil_row.setSpacing(8)
        brazil_label = QLabel(BRAZIL_LABEL)
        brazil_label.setFont(QFont("Noto Sans", 11))
        brazil_label.setStyleSheet(f"color: {TEXT_MUTED};")
        brazil_row.addWidget(brazil_label)
        brazil_row.addStretch()
        self.brazil_time_label = QLabel("--:--")
        self.brazil_time_label.setFont(QFont("Noto Sans Mono", 13, QFont.DemiBold))
        self.brazil_time_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        brazil_row.addWidget(self.brazil_time_label)
        right.addLayout(brazil_row)

        self.diff_badge = QLabel("+0h")
        self.diff_badge.setFont(QFont("Noto Sans", 11, QFont.DemiBold))
        self.diff_badge.setAlignment(Qt.AlignCenter)
        self.diff_badge.setFixedHeight(28)
        self.diff_badge.setStyleSheet(f"""
            color: {ACCENT};
            background: {ACCENT_SOFT};
            border-radius: 14px;
            padding: 0 14px;
        """)
        right.addWidget(self.diff_badge, 0, Qt.AlignLeft)

        right.addStretch()
        body.addLayout(right, 1)

        root.addLayout(body)

    # ---------- persistence ----------
    def _restore_selection(self):
        saved_tz = self.settings.value("tz", "Europe/Lisbon")
        idx = self.country_combo.findData(saved_tz, role=Qt.UserRole,
                                           flags=Qt.MatchExactly)
        if idx < 0:
            for i in range(self.country_combo.count()):
                if self.country_combo.itemData(i)[0] == saved_tz:
                    idx = i
                    break
        self.country_combo.setCurrentIndex(idx if idx >= 0 else 0)

    def _save_selection(self):
        tz, _code = self.country_combo.currentData()
        self.settings.setValue("tz", tz)

    # ---------- clock update ----------
    def _tick(self):
        tz_name, _code = self.country_combo.currentData()
        target_tz = ZoneInfo(tz_name)

        now_utc = datetime.now(ZoneInfo("UTC"))
        now_target = now_utc.astimezone(target_tz)
        now_brazil = now_utc.astimezone(BRAZIL_TZ)

        self.time_label.setText(now_target.strftime("%H:%M"))
        self.date_label.setText(format_date(now_target))
        self.brazil_time_label.setText(now_brazil.strftime("%H:%M"))
        self.offset_label.setText(format_offset(now_target))
        self.diff_badge.setText(format_diff(now_target, now_brazil))

    # ---------- drag to move (frameless window) ----------
    # On Wayland, QWidget.move() does not reposition borderless windows: the
    # compositor only allows moving via a native "system move" request.
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        handle = self.windowHandle()
        if handle is not None and handle.startSystemMove():
            event.accept()
            return
        # fallback (older X11 / compositors without startSystemMove support)
        self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


def main():
    app = QApplication(sys.argv)
    win = WorldClock()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
