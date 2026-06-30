"""
user/my_items.py  --  WeShare Community (PyQt6 edition)
My Items: table — Title | Category | Condition | Status | Posted | Actions.
"""
import sys, os, datetime, shutil, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QDialog, QRadioButton,
    QButtonGroup, QMessageBox, QScrollArea, QFrame, QFileDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets", "uploads")
NAV = S.USER_NAV


def _fmt_date(raw):
    try:
        d = datetime.datetime.fromisoformat(str(raw))
        return d.strftime("%b %d")
    except Exception:
        return str(raw)[:10]


class MyItemsPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "my_items", user, on_logout, on_navigate,
                          "My Items")
        self.card = S.make_card()
        self.cv = QVBoxLayout(self.card)
        self.cv.setContentsMargins(0, 0, 0, 0)
        self.cv.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(20, 14, 20, 14)
        top.addWidget(S.body_label("My Posted Items", size=14, bold=True))
        top.addStretch(1)
        add_btn = S.primary_btn("+ Add New", lambda: self.on_navigate("post"))
        top.addWidget(add_btn)
        tw = QWidget(); tw.setLayout(top)
        self.cv.addWidget(tw)
        self.cv.addWidget(S.hline())

        head = QHBoxLayout()
        head.setContentsMargins(20, 8, 20, 8)
        for label, stretch in [("Title", 3), ("Category", 2), ("Condition", 2),
                                ("Status", 2), ("Posted", 1), ("Actions", 3)]:
            head.addWidget(S.body_label(label, size=10, bold=True, color=S.TEXT_MUTED), stretch)
        hw = QWidget(); hw.setLayout(head)
        self.cv.addWidget(hw)
        self.cv.addWidget(S.hline())

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        rw = QWidget(); rw.setLayout(self.rows_layout)
        self.cv.addWidget(rw)

        self.body.addWidget(self.card)
        self.body.addStretch(1)
        self._load()

    def _clear_rows(self):
        while self.rows_layout.count():
            it = self.rows_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def _load(self):
        self._clear_rows()
        items = DB.get_user_items(self.user["id"])
        if not items:
            empty = S.body_label("You have not posted any items yet.",
                                  color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 30, 0, 30)
            self.rows_layout.addWidget(empty)
            return
        for item in items:
            self.rows_layout.addWidget(self._row(item))
            self.rows_layout.addWidget(S.hline())

    def _row(self, item: dict) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(20, 12, 20, 12)

        h.addWidget(S.body_label(item.get("title", "")[:42]), 3)

        cat = item.get("category", "")
        _, cfg = S.CATEGORY_COLORS.get(cat, (S.BG_PAGE, S.TEXT_MUTED))
        h.addWidget(S.colored_text(cat, cfg), 2)

        h.addWidget(S.body_label(item.get("condition", ""), size=11, color=S.TEXT_MUTED), 2)

        badge_box = QHBoxLayout()
        badge_box.addWidget(S.status_badge(item.get("status", "available")))
        badge_box.addStretch(1)
        bw = QWidget(); bw.setLayout(badge_box)
        h.addWidget(bw, 2)

        h.addWidget(S.body_label(_fmt_date(item.get("created_at", "")),
                                  size=11, color=S.TEXT_MUTED), 1)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        view_btn = S.small_btn("View", lambda checked=False, i=item: self._view_details(i))
        edit_btn = S.small_btn("Edit", lambda checked=False, i=item: self._edit(i))
        del_btn = S.small_btn("Delete", lambda checked=False, i=item: self._delete(i),
                               bg=S.ERROR_LIGHT, fg=S.ERROR)
        actions.addWidget(view_btn)
        actions.addWidget(edit_btn)
        actions.addWidget(del_btn)
        actions.addStretch(1)
        aw = QWidget(); aw.setLayout(actions)
        h.addWidget(aw, 3)
        return row

    def _view_details(self, item: dict):
        from item_details import open_item_details_dialog
        owner_name = self.user.get("full_name", self.user.get("name", ""))
        open_item_details_dialog(self, item, owner_label=owner_name)

    def _edit(self, item: dict):
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Item")
        dlg.resize(460, 660)
        dlg.setObjectName("dlgRoot")
        dlg.setStyleSheet(f"QDialog#dlgRoot{{background:{S.BG_PAGE};}}")
        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(20, 18, 20, 14)
        outer.setSpacing(10)

        outer.addWidget(S.body_label(f"Edit '{item.get('title', '')}'",
                                      size=14, bold=True))
        outer.addWidget(S.body_label(
            "Fix any details below if something was entered by mistake.",
            size=11, color=S.TEXT_MUTED))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        v = QVBoxLayout(inner)
        v.setContentsMargins(0, 4, 6, 4)
        v.setSpacing(10)

        # ── Photo (optional change) ─────────────────────────────────────
        img_lbl = QLabel()
        img_lbl.setFixedHeight(120)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        state = {"image_path": item.get("image_path", "")}

        def _refresh_thumb():
            pix = QPixmap(state["image_path"]) if state["image_path"] else QPixmap()
            if not pix.isNull():
                pix = pix.scaledToHeight(120, Qt.TransformationMode.SmoothTransformation)
                img_lbl.setPixmap(pix)
                img_lbl.setStyleSheet(
                    f"background:{S.BG_CARD}; border:1px solid {S.BORDER}; border-radius:8px;")
            else:
                img_lbl.setPixmap(QPixmap())
                img_lbl.setText("No photo")
                img_lbl.setStyleSheet(
                    f"background:{S.BG_PAGE}; border:2px dashed {S.BORDER};"
                    f" border-radius:8px; color:{S.TEXT_MUTED}; font-size:12px;")

        def _pick_image():
            path, _ = QFileDialog.getOpenFileName(
                dlg, "Select Item Image", "",
                "Images (*.png *.jpg *.jpeg *.gif *.bmp)")
            if not path:
                return
            if os.path.getsize(path) > 5 * 1024 * 1024:
                QMessageBox.warning(dlg, "File Too Large",
                                     "Please choose an image under 5 MB.")
                return
            os.makedirs(UPLOADS_DIR, exist_ok=True)
            ext = os.path.splitext(path)[1]
            fname = f"{uuid.uuid4().hex}{ext}"
            dest = os.path.join(UPLOADS_DIR, fname)
            shutil.copy2(path, dest)
            state["image_path"] = dest
            _refresh_thumb()

        img_lbl.mousePressEvent = lambda e: _pick_image()
        _refresh_thumb()
        v.addWidget(img_lbl)
        change_photo_btn = S.secondary_btn("Change Photo", _pick_image)
        v.addWidget(change_photo_btn)

        # ── Editable fields ──────────────────────────────────────────────
        title_field = S.FormField("Item Name", required=True)
        title_field.set_text(item.get("title", ""))
        v.addWidget(title_field)

        cat_field = S.FormDropdown("Category", S.CATEGORIES)
        cat_field.set_value(item.get("category", ""))
        cond_field = S.FormDropdown("Condition", S.CONDITIONS)
        cond_field.set_value(item.get("condition", ""))
        cat_row = QHBoxLayout()
        cat_row.setSpacing(10)
        cat_row.addWidget(cat_field)
        cat_row.addWidget(cond_field)
        v.addLayout(cat_row)

        desc_field = S.FormTextArea("Description", height=80)
        desc_field.set_text(item.get("description", ""))
        v.addWidget(desc_field)

        exch_field = S.FormField("Exchange For", required=True)
        exch_field.set_text(item.get("exchange_for", ""))
        v.addWidget(exch_field)

        phone_field = S.FormField("Contact Phone", required=True)
        S.restrict_phone_input(phone_field.edit)
        phone_field.set_text(item.get("phone", ""))
        v.addWidget(phone_field)

        loc_field = S.FormDropdown("Location", S.REGIONS, required=True)
        loc_field.set_value(item.get("location", ""))
        v.addWidget(loc_field)

        v.addWidget(S.hline())
        v.addWidget(S.body_label("Change status:", size=11, bold=True,
                                  color=S.TEXT_DARK))

        group = QButtonGroup(dlg)
        radios = []
        current = item.get("status", "available")
        status_row = QHBoxLayout()
        status_row.setSpacing(14)
        for st in ("available", "unavailable", "pending"):
            rb = QRadioButton(st.capitalize())
            if st == current:
                rb.setChecked(True)
            group.addButton(rb)
            radios.append((rb, st))
            status_row.addWidget(rb)
        status_row.addStretch(1)
        v.addLayout(status_row)

        feedback = QLabel("")
        feedback.setWordWrap(True)
        feedback.setVisible(False)
        v.addWidget(feedback)
        v.addStretch(1)

        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)

        def _save():
            feedback.setVisible(False)
            validator = S.FormValidator()
            validator.add(title_field, lambda: bool(title_field.text()),
                          "Item name is required.")
            validator.add(title_field, lambda: len(title_field.text()) >= 3,
                          "Item name must be at least 3 characters.")
            validator.add(exch_field, lambda: bool(exch_field.text()),
                          "Please specify what you want in exchange.")
            validator.add(phone_field, lambda: bool(phone_field.text()),
                          "Contact phone number is required.")
            validator.add(phone_field,
                          lambda: bool(S.PHONE_RE.match(phone_field.text())),
                          "Phone number must start with 06 or 07 (10 digits).")
            validator.add(loc_field, lambda: bool(loc_field.value()),
                          "Please select a location.")
            if not validator.validate():
                return

            status_value = current
            for rb, st in radios:
                if rb.isChecked():
                    status_value = st
                    break

            DB.update_item(item["id"], {
                "title": title_field.text(),
                "category": cat_field.value(),
                "condition": cond_field.value(),
                "description": desc_field.text(),
                "exchange_for": exch_field.text(),
                "phone": phone_field.text(),
                "location": loc_field.value(),
                "image_path": state["image_path"],
                "status": status_value,
            })
            dlg.close()
            self._load()

        btn_row = QHBoxLayout()
        cancel_btn = S.ghost_btn("Cancel", dlg.close)
        save_btn = S.primary_btn("Save", _save)
        btn_row.addWidget(cancel_btn, 1)
        btn_row.addWidget(save_btn, 1)
        outer.addLayout(btn_row)

        dlg.exec()

    def _delete(self, item: dict):
        res = QMessageBox.question(
            self, "Delete Item",
            f"Delete '{item.get('title', '')}'?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            DB.delete_item(item["id"])
            self._load()
