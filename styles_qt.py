"""
styles_qt.py  --  WeShare Community (PyQt6 edition)
Central design system: colors, fonts, QSS and reusable widget helpers.
Every page imports from here so the whole app keeps one consistent look,
matching the original reference screenshots pixel-for-pixel in spirit.
"""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QVBoxLayout, QHBoxLayout, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
    QCompleter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor

# ── Palette (identical values to the Tkinter styles.py) ─────────────────────
PRIMARY        = "#1D4ED8"
PRIMARY_DARK   = "#1E3A8A"
PRIMARY_LIGHT  = "#DBEAFE"
PRIMARY_HOVER  = "#2563EB"

SUCCESS        = "#15803D"
SUCCESS_LIGHT  = "#DCFCE7"
ERROR          = "#DC2626"
ERROR_LIGHT    = "#FEE2E2"
WARNING        = "#B45309"
WARNING_LIGHT  = "#FEF3C7"
INFO           = "#0369A1"
INFO_LIGHT     = "#E0F2FE"

BG_PAGE        = "#F1F5F9"
BG_CARD        = "#FFFFFF"
BG_INPUT       = "#F8FAFC"
BG_HOVER       = "#EFF6FF"
BG_SIDEBAR     = "#1E293B"
BG_SIDEBAR_SEL = "#1D4ED8"
BG_SIDEBAR_HOV = "#263548"

TEXT_DARK      = "#0F172A"
TEXT_MUTED     = "#64748B"
TEXT_LIGHT     = "#FFFFFF"
TEXT_SIDEBAR   = "#94A3B8"

BORDER         = "#E2E8F0"
BORDER_FOCUS   = "#1D4ED8"
BORDER_ERROR   = "#DC2626"

FAMILY = "Segoe UI, Helvetica, Arial, sans-serif"

# ── Validation helpers (shared across all forms) ────────────────────────────
import re as _re

# Tanzanian mobile number: starts with 06 or 07, exactly 10 digits total.
PHONE_RE = _re.compile(r"^0[67]\d{8}$")

# Password policy: at least 8 characters, at least one uppercase letter,
# one lowercase letter and one digit.
PASSWORD_MIN_LEN = 8


def password_errors(pw: str):
    """Returns a list of human-readable problems with `pw` (empty = valid)."""
    issues = []
    if len(pw) < PASSWORD_MIN_LEN:
        issues.append(f"at least {PASSWORD_MIN_LEN} characters")
    if not _re.search(r"[A-Z]", pw):
        issues.append("one uppercase letter")
    if not _re.search(r"[a-z]", pw):
        issues.append("one lowercase letter")
    if not _re.search(r"\d", pw):
        issues.append("one number")
    return issues


def restrict_phone_input(line_edit):
    """Limits a QLineEdit to digits only, max 10 characters (06xxxxxxxx /
    07xxxxxxxx), so the field simply stops accepting more once it hits 10."""
    from PyQt6.QtGui import QRegularExpressionValidator
    from PyQt6.QtCore import QRegularExpression
    validator = QRegularExpressionValidator(QRegularExpression(r"^\d{0,10}$"))
    line_edit.setValidator(validator)
    line_edit.setMaxLength(10)


def auth_background_qss(object_name: str) -> str:
    """Soft diagonal navy->blue gradient for full-page auth screens —
    gentler on the eyes than a single flat saturated blue fill."""
    return (
        f"QWidget#{object_name}{{"
        f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
        f" stop:0 #16245C, stop:0.55 #1E3A8A, stop:1 #2748B5);"
        f"}}"
    )


# ── Dropdown chevron icons ───────────────────────────────────────────────────
# Generated once to disk as real PNGs and referenced via image: url(...) in
# the QComboBox QSS below. A pure-QSS border triangle for ::down-arrow proved
# unreliable across styles/platforms (rendered as a stray bar in testing),
# so a small real icon is the dependable cross-platform choice.
import os as _os

_ICONS_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "assets", "icons")
CHEVRON_GRAY = _os.path.join(_ICONS_DIR, "chevron_down_gray.png")
CHEVRON_BLUE = _os.path.join(_ICONS_DIR, "chevron_down_blue.png")


def _draw_chevron(path, color_hex):
    from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor
    from PyQt6.QtCore import Qt as _Qt
    size = 16
    pm = QPixmap(size, size)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor(color_hex))
    pen.setWidth(2)
    pen.setCapStyle(_Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(_Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    # simple downward chevron  ⌄
    p.drawLine(4, 6, 8, 10)
    p.drawLine(8, 10, 12, 6)
    p.end()
    pm.save(path)


def ensure_chevron_icons():
    _os.makedirs(_ICONS_DIR, exist_ok=True)
    if not _os.path.exists(CHEVRON_GRAY):
        _draw_chevron(CHEVRON_GRAY, TEXT_MUTED)
    if not _os.path.exists(CHEVRON_BLUE):
        _draw_chevron(CHEVRON_BLUE, PRIMARY)

# ── Domain constants ─────────────────────────────────────────────────────────
CATEGORIES = [
    "Electronics", "Clothing", "Furniture", "Books", "Toys",
    "Sports", "Kitchen", "Tools", "Garden", "Art",
    "Music", "Vehicles", "Jewellery", "Food", "Other",
]

CONDITIONS = ["New", "Like New", "Good", "Fair", "Needs Repair"]

REGIONS = [
    "Dar es Salaam", "Mwanza", "Arusha", "Dodoma", "Mbeya",
    "Morogoro", "Tanga", "Zanzibar", "Kilimanjaro", "Kagera",
    "Kigoma", "Shinyanga", "Tabora", "Singida", "Iringa",
    "Ruvuma", "Lindi", "Mtwara", "Rukwa", "Pwani",
    "Manyara", "Geita", "Simiyu", "Njombe", "Katavi",
]

CATEGORY_COLORS = {
    "Electronics": ("#EEF2FF", "#4338CA"),
    "Clothing":    ("#FDF2F8", "#BE185D"),
    "Furniture":   ("#FFFBEB", "#92400E"),
    "Books":       ("#ECFDF5", "#065F46"),
    "Toys":        ("#FFF7ED", "#C2410C"),
    "Sports":      ("#F0FDF4", "#15803D"),
    "Kitchen":     ("#FFF1F2", "#BE123C"),
    "Tools":       ("#F0F9FF", "#0369A1"),
    "Garden":      ("#F7FEE7", "#3F6212"),
    "Art":         ("#FDF4FF", "#7E22CE"),
    "Music":       ("#FFFBEB", "#92400E"),
    "Vehicles":    ("#E0F2FE", "#0369A1"),
    "Jewellery":   ("#FDF2F8", "#DB2777"),
    "Food":        ("#ECFDF5", "#16A34A"),
    "Other":       ("#F8FAFC", "#475569"),
}

STATUS_COLORS = {
    "available":  (SUCCESS_LIGHT, SUCCESS),
    "pending":    (WARNING_LIGHT, WARNING),
    "completed":  (INFO_LIGHT,    INFO),
    "cancelled":  (ERROR_LIGHT,   ERROR),
    "active":     (SUCCESS_LIGHT, SUCCESS),
    "suspended":  (ERROR_LIGHT,   ERROR),
    "approved":   (SUCCESS_LIGHT, SUCCESS),
    "rejected":   (ERROR_LIGHT,   ERROR),
    "resolved":   (INFO_LIGHT,    INFO),
    "exchanged":  (INFO_LIGHT,    INFO),
    "unavailable":(BG_PAGE,       TEXT_MUTED),
    "dismissed":  (BG_PAGE,       TEXT_MUTED),
}

USER_NAV = [
    ("Dashboard",     "dashboard"),
    ("Browse Items",  "browse"),
    ("My Items",      "my_items"),
    ("Add Item",      "post"),
    ("Messages",      "messages"),
    ("Wants",         "wants"),
    ("Notifications", "notifications"),
    ("History",       "history"),
    ("Profile",       "profile"),
    ("Settings",      "settings"),
]

ADMIN_NAV = [
    ("Dashboard",    "dashboard"),
    ("Manage Users", "users"),
    ("Items",        "items"),
    ("Exchanges",    "exchanges"),
    ("Reports",      "reports"),
    ("Analytics",    "analytics"),
    ("Settings",     "settings"),
]


# ── Global QSS ───────────────────────────────────────────────────────────────
def stylesheet() -> str:
    ensure_chevron_icons()
    return f"""
    QWidget {{
        font-family: {FAMILY};
        font-size: 13px;
        color: {TEXT_DARK};
    }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: {BG_PAGE}; width: 10px; margin: 0; border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: #CBD5E1; border-radius: 5px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: {BG_PAGE}; height: 10px; margin: 0; border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background: #CBD5E1; border-radius: 5px; min-width: 24px;
    }}

    QLineEdit, QTextEdit, QComboBox {{
        background: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 13px;
        color: {TEXT_DARK};
        selection-background-color: {PRIMARY_LIGHT};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: 1.5px solid {BORDER_FOCUS};
    }}
    QLineEdit[error="true"], QTextEdit[error="true"], QComboBox[error="true"] {{
        border: 1.5px solid {BORDER_ERROR};
        background: #FFF5F5;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        border: none;
        border-left: 1px solid {BORDER};
        width: 30px;
        background: {BG_PAGE};
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }}
    QComboBox:hover::drop-down {{ background: {PRIMARY_LIGHT}; }}
    QComboBox::down-arrow {{
        subcontrol-origin: padding;
        subcontrol-position: center;
        image: url({CHEVRON_GRAY.replace(_os.sep, '/')});
        width: 12px;
        height: 12px;
    }}
    QComboBox::down-arrow:hover, QComboBox::down-arrow:on {{
        image: url({CHEVRON_BLUE.replace(_os.sep, '/')});
    }}
    QComboBox:hover {{ border: 1px solid {PRIMARY}; }}
    QComboBox QAbstractItemView {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 4px;
        selection-background-color: {PRIMARY_LIGHT};
        selection-color: {PRIMARY};
        outline: none;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 28px;
        padding: 4px 8px;
        border-radius: 5px;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background: {BG_HOVER};
        color: {PRIMARY};
    }}

    QPushButton {{ font-family: {FAMILY}; }}

    QPushButton#primaryBtn {{
        background: {PRIMARY}; color: {TEXT_LIGHT};
        border: none; border-radius: 6px;
        padding: 10px 18px; font-weight: 600; font-size: 13px;
    }}
    QPushButton#primaryBtn:hover {{ background: {PRIMARY_HOVER}; }}
    QPushButton#primaryBtn:pressed {{ background: {PRIMARY_DARK}; }}
    QPushButton#primaryBtn:disabled {{ background: #93C5FD; }}

    QPushButton#secondaryBtn {{
        background: {BG_CARD}; color: {PRIMARY};
        border: 1px solid {BORDER}; border-radius: 6px;
        padding: 9px 16px; font-weight: 600; font-size: 13px;
    }}
    QPushButton#secondaryBtn:hover {{ background: {PRIMARY_LIGHT}; }}

    QPushButton#ghostBtn {{
        background: transparent; color: {TEXT_MUTED};
        border: none; padding: 8px 14px; font-size: 13px;
    }}
    QPushButton#ghostBtn:hover {{ color: {TEXT_DARK}; }}

    QPushButton#linkBtn {{
        background: transparent; color: {PRIMARY};
        border: none; font-weight: 600; font-size: 13px;
        text-align: left; padding: 0;
    }}
    QPushButton#linkBtn:hover {{ color: {PRIMARY_DARK}; text-decoration: underline; }}

    QPushButton#dangerBtn {{
        background: {ERROR}; color: {TEXT_LIGHT};
        border: none; border-radius: 6px;
        padding: 9px 16px; font-weight: 600;
    }}
    QPushButton#dangerBtn:hover {{ background: #B91C1C; }}

    QPushButton#smallBtn {{
        background: {BG_PAGE}; color: {PRIMARY};
        border: 1px solid {BORDER}; border-radius: 5px;
        padding: 5px 10px; font-size: 12px;
    }}
    QPushButton#smallBtn:hover {{ background: {PRIMARY_LIGHT}; }}

    QPushButton#showToggle {{
        background: transparent; color: {PRIMARY};
        border: none; font-size: 12px; font-weight: 600;
        padding: 0 6px;
    }}

    QFrame#card {{
        background: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 10px;
    }}
    QFrame#sidebar {{ background: {BG_SIDEBAR}; }}
    QFrame#header {{
        background: {BG_CARD};
        border-bottom: 1px solid {BORDER};
    }}
    """


# ── Small label/text helpers ─────────────────────────────────────────────────
def h_label(text, size=20, weight=700, color=TEXT_DARK, parent=None):
    lbl = QLabel(text, parent)
    f = QFont()
    f.setPointSize(size)
    f.setWeight(QFont.Weight.Bold if weight >= 600 else QFont.Weight.Normal)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color:{color}; background: transparent;")
    return lbl


def body_label(text, size=13, color=TEXT_DARK, bold=False, parent=None):
    lbl = QLabel(text, parent)
    f = QFont()
    f.setPointSize(size)
    if bold:
        f.setWeight(QFont.Weight.Bold)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color:{color}; background: transparent;")
    return lbl


def hline(color=BORDER, height=1):
    ln = QFrame()
    ln.setFixedHeight(height)
    ln.setStyleSheet(f"background:{color}; border:none;")
    return ln


def make_card():
    f = QFrame()
    f.setObjectName("card")
    return f


def apply_elevation(widget, blur=36, y_offset=10, alpha=70):
    """Soft drop shadow for elevated surfaces (e.g. the login/register card),
    giving real depth instead of a flat cutout against the background."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_offset)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)
    return effect


# ── Form field with label + inline error + sequential validation support ────
class FormField(QWidget):
    """Labelled QLineEdit with an inline error message below it."""
    returnPressed = pyqtSignal()

    def __init__(self, label_text, placeholder="", required=False,
                 password=False, parent=None):
        super().__init__(parent)
        self.required = required
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)

        if label_text:
            cap = label_text + (" *" if required else "")
            lay.addWidget(body_label(cap, size=11, bold=True, color=TEXT_DARK))

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setMinimumHeight(36)
        if password:
            self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        row.addWidget(self.edit)
        self._toggle = None
        if password:
            self._toggle = QPushButton("Show")
            self._toggle.setObjectName("showToggle")
            self._toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._toggle.clicked.connect(self._toggle_pw)
            # overlay-style: put inside a frame with edit for a single bordered look
            wrap = QFrame()
            wrap.setStyleSheet(
                f"QFrame{{background:{BG_INPUT}; border:1px solid {BORDER}; "
                f"border-radius:6px;}}")
            wl = QHBoxLayout(wrap)
            wl.setContentsMargins(0, 0, 4, 0)
            wl.setSpacing(0)
            self.edit.setStyleSheet("border: none; background: transparent;")
            wl.addWidget(self.edit)
            wl.addWidget(self._toggle)
            lay.addWidget(wrap)
            self._wrap = wrap
        else:
            lay.addLayout(row)
            self._wrap = self.edit

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet(f"color:{ERROR}; font-size:11px; background:transparent;")
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setVisible(False)
        lay.addWidget(self.error_lbl)

        self.edit.returnPressed.connect(self.returnPressed.emit)
        self.edit.textChanged.connect(self.clear_error)

    def _toggle_pw(self):
        if self.edit.echoMode() == QLineEdit.EchoMode.Password:
            self.edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle.setText("Hide")
        else:
            self.edit.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle.setText("Show")

    def text(self):
        return self.edit.text().strip()

    def raw_text(self):
        return self.edit.text()

    def set_text(self, t):
        self.edit.setText(t)

    def clear_error(self, *_):
        self.error_lbl.setVisible(False)
        self.error_lbl.setText("")
        self.edit.setProperty("error", False)
        self.edit.style().unpolish(self.edit)
        self.edit.style().polish(self.edit)

    def show_error(self, msg):
        self.error_lbl.setText(msg)
        self.error_lbl.setVisible(True)
        self.edit.setProperty("error", True)
        self.edit.style().unpolish(self.edit)
        self.edit.style().polish(self.edit)
        self.edit.setFocus()


class FormTextArea(QWidget):
    """Labelled multi-line text box with inline error."""

    def __init__(self, label_text, placeholder="", required=False,
                 height=90, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        if label_text:
            cap = label_text + (" *" if required else "")
            lay.addWidget(body_label(cap, size=11, bold=True, color=TEXT_DARK))
        self.edit = QTextEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setFixedHeight(height)
        lay.addWidget(self.edit)
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet(f"color:{ERROR}; font-size:11px; background:transparent;")
        self.error_lbl.setVisible(False)
        lay.addWidget(self.error_lbl)
        self.edit.textChanged.connect(self.clear_error)

    def text(self):
        return self.edit.toPlainText().strip()

    def set_text(self, t):
        self.edit.setPlainText(t)

    def clear_error(self, *_):
        self.error_lbl.setVisible(False)
        self.error_lbl.setText("")
        self.edit.setProperty("error", False)
        self.edit.style().unpolish(self.edit)
        self.edit.style().polish(self.edit)

    def show_error(self, msg):
        self.error_lbl.setText(msg)
        self.error_lbl.setVisible(True)
        self.edit.setProperty("error", True)
        self.edit.style().unpolish(self.edit)
        self.edit.style().polish(self.edit)
        self.edit.setFocus()


class _BoundedCombo(QComboBox):
    """QComboBox whose popup is capped to `maxVisibleItems` rows and is
    always pinned directly under the field.

    Qt's normal popup-sizing logic (when a stylesheet is applied to the
    dropdown, as we do here) sometimes ignores maxVisibleItems for longer
    lists and tries to render every row at once. The popup then becomes
    taller than the space left on screen, so Qt flips it upward -- it ends
    up floating above/over the form instead of attached just below the
    field, like short lists (e.g. Category) already appear. This override
    forces the popup back to a sane, capped height and re-pins it under
    the field every time it opens, so every dropdown -- short or long --
    behaves the same way.
    """

    def showPopup(self):
        super().showPopup()
        if self.isEditable() or self.count() == 0:
            return
        popup = self.view().window()
        row_h = self.view().sizeHintForRow(0) or 28
        rows = min(self.count(), self.maxVisibleItems())
        target_h = row_h * rows + 12
        popup.resize(popup.width(), target_h)
        popup.move(self.mapToGlobal(self.rect().bottomLeft()))


class FormDropdown(QWidget):
    """Labelled QComboBox with inline error. First item may be a placeholder.
    Pass searchable=True to let the user type to filter options live
    (e.g. Region) -- makes long lists much faster and nicer to use."""

    def __init__(self, label_text, values, required=False,
                 placeholder=None, searchable=False, parent=None):
        super().__init__(parent)
        self.required = required
        self._placeholder = placeholder
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        if label_text:
            cap = label_text + (" *" if required else "")
            lay.addWidget(body_label(cap, size=11, bold=True, color=TEXT_DARK))
        self.combo = _BoundedCombo()
        self.combo.setMinimumHeight(36)
        self.combo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # Cap how many rows the popup shows at once. Without this, long
        # lists (e.g. Region, which has 25 entries) try to render every
        # row in one go; the popup then grows taller than the space below
        # the field and Qt flips it upward, so it ends up floating over
        # the form instead of sitting attached just under the field --
        # exactly like the short lists (e.g. Category) already do.
        self.combo.setMaxVisibleItems(7)
        if placeholder:
            self.combo.addItem(placeholder)
        self.combo.addItems(values)

        if searchable:
            self.combo.setEditable(True)
            self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            self.combo.completer().setCompletionMode(
                QCompleter.CompletionMode.PopupCompletion)
            self.combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
            self.combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            if placeholder:
                self.combo.lineEdit().setPlaceholderText(placeholder)
                self.combo.setCurrentIndex(-1)
                self.combo.lineEdit().clear()

        lay.addWidget(self.combo)
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet(f"color:{ERROR}; font-size:11px; background:transparent;")
        self.error_lbl.setVisible(False)
        lay.addWidget(self.error_lbl)
        self.combo.currentIndexChanged.connect(self.clear_error)

    def value(self):
        txt = self.combo.currentText().strip()
        if self._placeholder and txt == self._placeholder:
            return ""
        return txt

    def set_value(self, v):
        idx = self.combo.findText(v)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)

    def clear_error(self, *_):
        self.error_lbl.setVisible(False)
        self.error_lbl.setText("")
        self.combo.setProperty("error", False)
        self.combo.style().unpolish(self.combo)
        self.combo.style().polish(self.combo)

    def show_error(self, msg):
        self.error_lbl.setText(msg)
        self.error_lbl.setVisible(True)
        self.combo.setProperty("error", True)
        self.combo.style().unpolish(self.combo)
        self.combo.style().polish(self.combo)
        self.combo.setFocus()


# ── Sequential form validator ────────────────────────────────────────────────
class FormValidator:
    """
    Runs a list of (field, check_fn, message) validators IN ORDER.
    On submit: clears all errors, then evaluates each rule; the first
    rule that fails shows its error under the field, focuses that field,
    scrolls to it, and stops — exactly like the reference screenshots
    (go to the first empty/invalid field with a warning underneath).
    """

    def __init__(self):
        self._rules = []
        self._fields = []

    def add(self, field, check_fn, message):
        self._rules.append((field, check_fn, message))
        if field not in self._fields:
            self._fields.append(field)

    def clear(self):
        for f in self._fields:
            f.clear_error()

    def validate(self) -> bool:
        self.clear()
        for field, check_fn, message in self._rules:
            if not check_fn():
                field.show_error(message)
                return False
        return True


# ── Buttons ───────────────────────────────────────────────────────────────────
def primary_btn(text, on_click=None, parent=None):
    btn = QPushButton(text, parent)
    btn.setObjectName("primaryBtn")
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    btn.setMinimumHeight(40)
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def secondary_btn(text, on_click=None, parent=None):
    btn = QPushButton(text, parent)
    btn.setObjectName("secondaryBtn")
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    btn.setMinimumHeight(38)
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def ghost_btn(text, on_click=None, parent=None):
    btn = QPushButton(text, parent)
    btn.setObjectName("ghostBtn")
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def danger_btn(text, on_click=None, parent=None):
    btn = QPushButton(text, parent)
    btn.setObjectName("dangerBtn")
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def link_btn(text, on_click=None, parent=None):
    btn = QPushButton(text, parent)
    btn.setObjectName("linkBtn")
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    btn.setFlat(True)
    if on_click:
        btn.clicked.connect(on_click)
    return btn


def small_btn(text, on_click=None, bg=None, fg=None, parent=None):
    btn = QPushButton(text, parent)
    btn.setObjectName("smallBtn")
    btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    if bg or fg:
        bg = bg or BG_PAGE
        fg = fg or PRIMARY
        btn.setStyleSheet(
            f"QPushButton#smallBtn{{background:{bg}; color:{fg}; "
            f"border:1px solid {bg}; border-radius:5px; padding:5px 10px; font-size:12px;}}"
            f"QPushButton#smallBtn:hover{{background:{fg}; color:white;}}")
    if on_click:
        btn.clicked.connect(on_click)
    return btn


# ── Status / category badges ─────────────────────────────────────────────────
def status_badge(status: str) -> QLabel:
    bg, fg = STATUS_COLORS.get((status or "").lower(), (BG_PAGE, TEXT_MUTED))
    lbl = QLabel((status or "").capitalize())
    lbl.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:10px; "
        f"padding:3px 10px; font-size:11px; font-weight:600;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


def category_pill(category: str) -> QLabel:
    bg, fg = CATEGORY_COLORS.get(category, ("#F8FAFC", "#475569"))
    lbl = QLabel(category)
    lbl.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:10px; "
        f"padding:3px 10px; font-size:11px; font-weight:600;")
    return lbl


def colored_text(text, color):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{color}; background:transparent; font-size:12px;")
    return lbl


# ── Stat card ─────────────────────────────────────────────────────────────────
def stat_card(label: str, value, color=PRIMARY) -> QFrame:
    card = make_card()
    v = QVBoxLayout(card)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)
    strip = QFrame()
    strip.setFixedHeight(3)
    strip.setStyleSheet(f"background:{color}; border-radius:0px;")
    v.addWidget(strip)
    inner = QVBoxLayout()
    inner.setContentsMargins(18, 14, 18, 14)
    inner.setSpacing(2)
    val_lbl = h_label(str(value), size=22, weight=700, color=color)
    inner.addWidget(val_lbl)
    inner.addWidget(body_label(label, size=11, color=TEXT_MUTED))
    holder = QWidget()
    holder.setLayout(inner)
    v.addWidget(holder)
    return card


# ── Page header bar ───────────────────────────────────────────────────────────
class PageHeader(QFrame):
    def __init__(self, title, subtitle="", user_name="", parent=None):
        super().__init__(parent)
        self.setObjectName("header")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(24, 14, 24, 14)
        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(h_label(title, size=16, weight=700))
        if subtitle:
            left.addWidget(body_label(subtitle, size=11, color=TEXT_MUTED))
        lw = QWidget()
        lw.setLayout(left)
        lay.addWidget(lw)
        lay.addStretch(1)
        self.right_box = QHBoxLayout()
        self.right_box.setSpacing(10)
        rw = QWidget()
        rw.setLayout(self.right_box)
        lay.addWidget(rw)
        if user_name:
            pill = QLabel(user_name)
            pill.setStyleSheet(
                f"background:{PRIMARY_LIGHT}; color:{PRIMARY}; "
                f"border-radius:14px; padding:8px 16px; font-size:12px; font-weight:600;")
            self.right_box.addWidget(pill)

    def add_widget(self, w):
        self.right_box.insertWidget(0, w)


# ── Sidebar ───────────────────────────────────────────────────────────────────
class SidebarButton(QPushButton):
    def __init__(self, text, active=False, danger=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCheckable(False)
        self.setMinimumHeight(40)
        self._active = active
        self._danger = danger
        self._apply()

    def _apply(self):
        if self._danger:
            self.setStyleSheet(
                "QPushButton{background:transparent; color:#F87171; border:none;"
                " text-align:left; padding:10px 18px; font-size:13px;}"
                "QPushButton:hover{background:#7F1D1D; color:white;}")
        elif self._active:
            self.setStyleSheet(
                f"QPushButton{{background:{BG_SIDEBAR_SEL}; color:white; border:none;"
                f" text-align:left; padding:10px 18px; font-size:13px; font-weight:600;"
                f" border-radius:0px;}}")
        else:
            self.setStyleSheet(
                f"QPushButton{{background:transparent; color:{TEXT_SIDEBAR}; border:none;"
                f" text-align:left; padding:10px 18px; font-size:13px;}}"
                f"QPushButton:hover{{background:{BG_SIDEBAR_HOV}; color:white;}}")


class Sidebar(QFrame):
    """Left navigation column. nav_items = [(label, key), ...]"""

    def __init__(self, nav_items, active_key, user_name, user_role,
                 on_nav, on_logout, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        brand = QVBoxLayout()
        brand.setContentsMargins(18, 18, 18, 14)
        brand.setSpacing(0)
        brand.addWidget(h_label("WeShare", size=15, weight=700, color="white"))
        brand.addWidget(body_label("Community", size=9, color=TEXT_SIDEBAR))
        bw = QWidget()
        bw.setLayout(brand)
        v.addWidget(bw)
        v.addWidget(hline("#334155"))

        # user pill
        pill_box = QHBoxLayout()
        pill_box.setContentsMargins(14, 12, 14, 12)
        pill_box.setSpacing(10)
        initials = (user_name or "U")[:2].upper()
        av = QLabel(initials)
        av.setFixedSize(34, 34)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(
            f"background:{BG_SIDEBAR_SEL}; color:white; border-radius:17px; font-weight:700;")
        pill_box.addWidget(av)
        info = QVBoxLayout()
        info.setSpacing(0)
        name_lbl = body_label((user_name or "")[:18], size=10, color="white", bold=True)
        info.addWidget(name_lbl)
        info.addWidget(body_label(str(user_role or "")[:20], size=8, color=TEXT_SIDEBAR))
        iw = QWidget()
        iw.setLayout(info)
        pill_box.addWidget(iw)
        pill_box.addStretch(1)
        pw = QWidget()
        pw.setLayout(pill_box)
        v.addWidget(pw)
        v.addWidget(hline("#334155"))

        for label, key in nav_items:
            btn = SidebarButton(label, active=(key == active_key))
            btn.clicked.connect(lambda _=False, k=key: on_nav(k))
            v.addWidget(btn)

        v.addStretch(1)
        v.addWidget(hline("#334155"))
        lo_btn = SidebarButton("Sign Out", danger=True)
        lo_btn.clicked.connect(lambda: on_logout())
        v.addWidget(lo_btn)
