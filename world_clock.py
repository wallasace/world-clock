#!/usr/bin/env python3
"""Minimalist world clock: compares the time of two countries you choose."""
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, QSettings, Signal
from PySide6.QtGui import QFont, QFontDatabase, QColor, QCursor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCompleter, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QGraphicsDropShadowEffect, QFrame, QSizePolicy,
)

FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"


def load_bundled_fonts() -> None:
    """Register the bundled Noto Sans / Noto Sans Mono weights so the app
    looks the same everywhere, instead of depending on what's installed on
    the system — Windows doesn't ship Noto Sans, so without this the app
    silently fell back to a generic font there."""
    for filename in (
        "NotoSans-Regular.ttf",
        "NotoSans-SemiBold.ttf",
        "NotoSansMono-Medium.ttf",
        "NotoSansMono-SemiBold.ttf",
    ):
        QFontDatabase.addApplicationFont(str(FONTS_DIR / filename))

# Flag glyphs (regional-indicator emoji) don't reliably render as actual
# flags in Qt on Windows — most fonts/backends fall back to showing the two
# letters instead of composing a flag picture. Bundled PNGs (from
# github.com/lipis/flag-icons, MIT) sidestep that entirely and look the same
# on every platform.
FLAGS_DIR = Path(__file__).resolve().parent / "assets" / "flags"
_flag_pixmap_cache: dict[tuple[str, int], QPixmap] = {}


def flag_pixmap(country_code: str, height: int) -> QPixmap | None:
    """A rounded-corner flag pixmap for `country_code` at the given pixel
    height (4:3 aspect ratio), or None if no asset exists for that code."""
    key = (country_code.lower(), height)
    if key in _flag_pixmap_cache:
        return _flag_pixmap_cache[key]

    source = QPixmap(str(FLAGS_DIR / f"{country_code.lower()}.png"))
    if source.isNull():
        return None

    width = round(height * 4 / 3)
    scaled = source.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    rounded = QPixmap(scaled.size())
    rounded.fill(Qt.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, width, height, 2, 2)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()

    _flag_pixmap_cache[key] = rounded
    return rounded


DEFAULT_ORIGIN_TZ = "America/Sao_Paulo"
DEFAULT_TARGET_TZ = "Europe/Lisbon"

# (display name, IANA tz, ISO country code for the flag)
COUNTRIES = [
    ("Argentina", "America/Argentina/Buenos_Aires", "AR"),
    ("Australia (Sydney)", "Australia/Sydney", "AU"),
    ("Austria", "Europe/Vienna", "AT"),
    ("Belgium", "Europe/Brussels", "BE"),
    ("Brazil (Brasília)", "America/Sao_Paulo", "BR"),
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
    ("USA (Los Angeles)", "America/Los_Angeles", "US"),
    ("USA (New York)", "America/New_York", "US"),
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


def format_diff(dt_target: datetime, dt_origin: datetime) -> str:
    delta_minutes = int((dt_target.utcoffset() - dt_origin.utcoffset()).total_seconds() // 60)
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


def combo_style(text_color: str) -> str:
    return f"""
        QComboBox {{
            color: {text_color};
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
    """


def popup_style() -> str:
    return f"""
        background: {BG_CARD_TOP};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        selection-background-color: {ACCENT_SOFT};
        outline: none;
        padding: 6px;
    """


class HoverButton(QPushButton):
    """A QPushButton with the hover state applied by hand, via polling the
    cursor position instead of Enter/Leave events.

    QSS `:hover` never repaints on this window on Windows — a known Qt issue
    with Qt.FramelessWindowHint + WA_TranslucentBackground windows there,
    where the native style's hover highlight silently never appears even
    though the same stylesheet works fine on Linux. Driving the two style
    states explicitly (enterEvent/leaveEvent) fixed that, but only until the
    country-search popup (QComboBox dropdown / QCompleter popup) opens once:
    afterwards Windows stops delivering real Enter/Leave events to this
    button at all, on this frameless+translucent window, until the app is
    restarted — the popup's implicit mouse grab seems to permanently disrupt
    this window's native hover/mouse-tracking registration. Polling the
    cursor position sidesteps that entirely, since it doesn't depend on
    those events being delivered."""

    def __init__(self, text: str, base_style: str, hover_style: str):
        super().__init__(text)
        self._base_style = base_style
        self._hover_style = hover_style
        self._hovered = False
        self.setStyleSheet(self._base_style)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(80)
        self._poll_timer.timeout.connect(self._check_hover)
        self._poll_timer.start()

    def _check_hover(self):
        hovered = self.rect().contains(self.mapFromGlobal(QCursor.pos()))
        if hovered == self._hovered:
            return
        self._hovered = hovered
        self.setStyleSheet(self._hover_style if hovered else self._base_style)


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text):
        super().__init__(text)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        # Accept (don't let it bubble up) so the parent window's
        # click-anywhere-to-drag handler doesn't start a system move on us.
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # Fire on release, like QPushButton — emitting on press instead let
        # combo.showPopup() open the dropdown *while the button was still
        # down*, so the very next release landed on the popup and closed it.
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class ChevronLabel(ClickableLabel):
    """A small down-chevron, hand-drawn instead of rendered from a Unicode
    glyph ("⌄", U+2304). Noto Sans doesn't cover that codepoint, so Qt
    silently substituted a fallback font for just that one character — a
    thin arrow on Windows, a noticeably wider/bolder one on Linux. Drawing
    it ourselves makes it look identical on both."""

    def __init__(self, color: str, size: int):
        super().__init__("")
        self._color = QColor(color)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self._color)
        pen.setWidthF(max(1.4, self.width() * 0.13))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        w, h = self.width(), self.height()
        margin = w * 0.24
        top_y = h * 0.4
        bottom_y = h * 0.62
        path = QPainterPath()
        path.moveTo(margin, top_y)
        path.lineTo(w / 2, bottom_y)
        path.lineTo(w - margin, top_y)
        painter.drawPath(path)


def country_code_for_text(text: str) -> str:
    """The ISO code for the country matching `text` (exact match wins over a
    "contains" match), or "" if nothing matches — e.g. an empty field."""
    query = text.strip().lower()
    if not query:
        return ""
    for name, _tz, code in COUNTRIES:
        if name.lower() == query:
            return code
    for name, _tz, code in COUNTRIES:
        if query in name.lower():
            return code
    return ""


def combo_row(combo: QComboBox, text_color: str) -> QHBoxLayout:
    """A [flag][search field][⌄] row. The flag is a separate, read-only label
    that tracks the typed text, so deleting the country name doesn't leave a
    stray flag glyph behind (or vice versa). The "⌄" opens the full,
    unfiltered list, since the field itself is busy being a search box."""
    row = QHBoxLayout()
    row.setSpacing(8)

    flag_height = round(combo.font().pointSize() * 1.1)
    flag_label = QLabel()
    flag_label.setFixedSize(round(flag_height * 4 / 3), flag_height)
    row.addWidget(flag_label)

    def sync_flag(text):
        code = country_code_for_text(text)
        pixmap = flag_pixmap(code, flag_height) if code else None
        flag_label.setPixmap(pixmap if pixmap is not None else QPixmap())

    combo.lineEdit().textChanged.connect(sync_flag)
    sync_flag(combo.currentText())

    combo.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    row.addWidget(combo)
    chevron = ChevronLabel(text_color, size=round(combo.font().pointSize() * 1.3))
    chevron.setToolTip("Browse all countries")

    chevron.clicked.connect(combo.showPopup)
    row.addWidget(chevron)
    row.addStretch()
    return row


class _ComboSearchFocusHandler(QObject):
    """Selects all text when the search field gains focus, and snaps back to a
    valid country when it loses focus without a completion being picked."""

    def __init__(self, combo: QComboBox):
        super().__init__(combo)
        self._combo = combo

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            QTimer.singleShot(0, obj.selectAll)
        elif event.type() == QEvent.FocusOut:
            # Focus also "leaves" the line edit when its own popup opens
            # (reason == PopupFocusReason) — reverting the text here would
            # rewrite it mid-open and the popup would immediately snap shut.
            if event.reason() != Qt.PopupFocusReason:
                self._revert_if_invalid()
        return False

    def _revert_if_invalid(self):
        combo = self._combo
        idx = combo.findText(combo.currentText(), Qt.MatchFixedString)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.lineEdit().setText(combo.itemText(combo.currentIndex()))


class _DropDownBelowFilter(QObject):
    """Re-pins a popup directly below `anchor` right after it's shown.

    Qt decides whether a popup opens above or below its anchor based on
    available screen space — but on this frameless/translucent window that
    calculation sometimes comes out wrong on Windows (the popup flips
    upward with plenty of room left below), even though the exact same code
    opens downward on Linux. Overriding the position after the fact sidesteps
    whatever's miscounted, rather than trying to out-guess Qt's placement."""

    def __init__(self, anchor: QWidget, parent=None):
        super().__init__(parent)
        self._anchor = anchor

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Show:
            QTimer.singleShot(0, lambda: self._pin(obj))
        return False

    def _pin(self, popup: QWidget):
        pos = self._anchor.mapToGlobal(self._anchor.rect().bottomLeft())
        popup.window().move(pos)


class CountryCombo(QComboBox):
    """A QComboBox whose popup always drops down, never up — see
    _DropDownBelowFilter."""

    def showPopup(self):
        super().showPopup()
        pos = self.mapToGlobal(self.rect().bottomLeft())
        self.view().window().move(pos)


def make_country_combo(font_size: int, text_color: str) -> QComboBox:
    combo = CountryCombo()
    combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
    for name, tz, code in COUNTRIES:
        combo.addItem(name, (tz, code))
    combo.setFont(QFont("Noto Sans", font_size, QFont.DemiBold))
    combo.setCursor(QCursor(Qt.PointingHandCursor))
    combo.setToolTip("Type to search, or click the arrow to browse all countries")
    combo.setStyleSheet(combo_style(text_color))
    combo.view().setFont(combo.font())
    content_width = combo.view().sizeHintForColumn(0)
    combo.view().setMinimumWidth(content_width + 30)

    # Editable + a "contains" completer turns the picker into a smart search:
    # typing "sydney" finds Australia (Sydney), not just names starting with it.
    combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.NoInsert)
    line_edit = combo.lineEdit()
    line_edit.setFrame(False)
    line_edit.setStyleSheet("background: transparent; border: none;")
    focus_handler = _ComboSearchFocusHandler(combo)
    line_edit.installEventFilter(focus_handler)

    completer = QCompleter([combo.itemText(i) for i in range(combo.count())], combo)
    completer.setCaseSensitivity(Qt.CaseInsensitive)
    completer.setFilterMode(Qt.MatchContains)
    completer.setCompletionMode(QCompleter.PopupCompletion)
    completer.popup().setFont(combo.font())
    completer.popup().setStyleSheet(popup_style())
    completer.popup().setMinimumWidth(combo.view().minimumWidth())
    completer.popup().installEventFilter(_DropDownBelowFilter(line_edit, combo))

    def commit(text):
        idx = combo.findText(text, Qt.MatchFixedString)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    completer.activated[str].connect(commit)
    combo.setCompleter(completer)
    line_edit.editingFinished.connect(focus_handler._revert_if_invalid)

    # AdjustToContents under-measures editable combos with emoji glyphs
    # (font fallback renders the flag wider than QFontMetrics predicts), so
    # pin the width explicitly using the same measurement as the popup.
    combo.setMinimumWidth(content_width + 20)

    return combo


class WorldClock(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("aceaswall", "WorldClock")
        # Qt.Tool and Qt.WindowStaysOnTopHint are deliberately avoided here: on
        # KWin/Wayland they change how the window's surface is presented in a
        # way that breaks popups (QComboBox's dropdown, QCompleter's popup)
        # parented to it — clicks and typing worked, but no popup ever showed.
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(696, 356)
        self._drag_pos = None
        self._now_target = None
        self._now_origin = None
        self._colon_visible = True
        self._build_ui()
        self._restore_selections()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)
        self._tick()

        # A separate, faster timer just for the blink: the main clock still
        # only needs to recompute the actual time once a second, but the
        # blink needs to toggle twice in that time (on, then off) to read as
        # a "seconds are passing" pulse rather than a slow flash.
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._toggle_colon)
        self.blink_timer.start(500)

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

        close_btn_base = f"""
            QPushButton {{
                color: {TEXT_MUTED};
                background: transparent;
                border: none;
                font-size: 18px;
                border-radius: 13px;
            }}
        """
        close_btn_hover = f"""
            QPushButton {{
                color: {TEXT_PRIMARY};
                background: rgba(255,255,255,0.08);
                border: none;
                font-size: 18px;
                border-radius: 13px;
            }}
        """
        close_btn = HoverButton("×", close_btn_base, close_btn_hover)
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        root.addLayout(top_bar)
        root.addSpacing(18)

        body = QHBoxLayout()
        body.setSpacing(28)

        # ---- left: target country big clock ----
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

        # ---- right: target country picker + origin country picker ----
        right = QVBoxLayout()
        right.setSpacing(10)
        right.addStretch()

        self.target_combo = make_country_combo(15, TEXT_PRIMARY)
        self.target_combo.currentIndexChanged.connect(self._save_target)
        right.addLayout(combo_row(self.target_combo, TEXT_PRIMARY))

        self.target_offset_label = QLabel("UTC+0")
        self.target_offset_label.setFont(QFont("Noto Sans Mono", 10))
        self.target_offset_label.setStyleSheet(f"color: {TEXT_MUTED};")
        right.addWidget(self.target_offset_label)

        right.addSpacing(6)

        self.origin_combo = make_country_combo(11, TEXT_MUTED)
        self.origin_combo.currentIndexChanged.connect(self._save_origin)
        right.addLayout(combo_row(self.origin_combo, TEXT_MUTED))

        origin_row = QHBoxLayout()
        origin_row.setSpacing(8)
        self.origin_offset_label = QLabel("UTC+0")
        self.origin_offset_label.setFont(QFont("Noto Sans Mono", 10))
        self.origin_offset_label.setStyleSheet(f"color: {TEXT_MUTED};")
        origin_row.addWidget(self.origin_offset_label)
        origin_row.addStretch()
        self.origin_time_label = QLabel("--:--")
        self.origin_time_label.setFont(QFont("Noto Sans Mono", 13, QFont.DemiBold))
        self.origin_time_label.setStyleSheet(f"color: {TEXT_PRIMARY};")
        origin_row.addWidget(self.origin_time_label)
        right.addLayout(origin_row)

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
    @staticmethod
    def _find_tz_index(combo: QComboBox, tz: str) -> int:
        for i in range(combo.count()):
            if combo.itemData(i)[0] == tz:
                return i
        return -1

    def _restore_selections(self):
        origin_tz = self.settings.value("origin_tz", DEFAULT_ORIGIN_TZ)
        target_tz = self.settings.value("target_tz", DEFAULT_TARGET_TZ)
        self.origin_combo.setCurrentIndex(max(self._find_tz_index(self.origin_combo, origin_tz), 0))
        self.target_combo.setCurrentIndex(max(self._find_tz_index(self.target_combo, target_tz), 0))

    def _save_origin(self):
        tz, _code = self.origin_combo.currentData()
        self.settings.setValue("origin_tz", tz)

    def _save_target(self):
        tz, _code = self.target_combo.currentData()
        self.settings.setValue("target_tz", tz)

    # ---------- clock update ----------
    def _tick(self):
        origin_tz_name, _code = self.origin_combo.currentData()
        target_tz_name, _code = self.target_combo.currentData()

        now_utc = datetime.now(ZoneInfo("UTC"))
        now_target = now_utc.astimezone(ZoneInfo(target_tz_name))
        now_origin = now_utc.astimezone(ZoneInfo(origin_tz_name))

        self._now_target = now_target
        self._now_origin = now_origin
        self._render_clocks()
        self.date_label.setText(format_date(now_target))
        self.target_offset_label.setText(format_offset(now_target))
        self.origin_offset_label.setText(format_offset(now_origin))
        self.diff_badge.setText(format_diff(now_target, now_origin))

    def _toggle_colon(self):
        self._colon_visible = not self._colon_visible
        self._render_clocks()

    def _render_clocks(self):
        separator = ":" if self._colon_visible else " "
        if self._now_target is not None:
            self.time_label.setText(self._now_target.strftime(f"%H{separator}%M"))
        if self._now_origin is not None:
            self.origin_time_label.setText(self._now_origin.strftime(f"%H{separator}%M"))

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
    load_bundled_fonts()
    win = WorldClock()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
