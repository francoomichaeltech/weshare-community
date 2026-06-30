"""
user/add_item.py  --  WeShare Community (PyQt6 edition)
Full-page Post Item screen with sidebar nav and image upload preview.
"""
import sys, os, shutil, uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer

import styles_qt as S
import database as DB
from common import PageScaffold

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets", "uploads")
NAV = S.USER_NAV


class AddItemPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "post", user, on_logout, on_navigate,
                          "Post a New Item", "Share something with your community")
        self._image_path = ""
        os.makedirs(UPLOADS_DIR, exist_ok=True)

        row = QHBoxLayout()
        row.setSpacing(16)
        self._build_form(row)
        self._build_preview(row)
        self.body.addLayout(row)
        self.body.addStretch(1)

    # ── Form ─────────────────────────────────────────────────────────────────

    def _build_form(self, parent_row):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(8)

        v.addWidget(S.h_label("Item Details", size=15, weight=700))
        v.addWidget(S.hline())

        v.addWidget(S.body_label("Posted by", size=11, bold=True))
        name = self.user.get("full_name", self.user.get("name", ""))
        ro = QLabel(name)
        ro.setStyleSheet(
            f"background:{S.BG_PAGE}; border:1px solid {S.BORDER}; border-radius:6px;"
            f" padding:8px 10px; color:{S.TEXT_MUTED};")
        v.addWidget(ro)

        self.title_field = S.FormField("Item Name", "e.g. Samsung Galaxy S10", required=True)
        v.addWidget(self.title_field)

        self.cat_field = S.FormDropdown("Category", S.CATEGORIES)
        self.cond_field = S.FormDropdown("Condition", S.CONDITIONS)
        cat_row = QHBoxLayout()
        cat_row.setSpacing(12)
        cat_row.addWidget(self.cat_field)
        cat_row.addWidget(self.cond_field)
        v.addLayout(cat_row)

        self.desc_field = S.FormTextArea(
            "Description  (condition, age, size, etc.)",
            "Describe the item, its condition, any defects...", height=90)
        v.addWidget(self.desc_field)

        self.exch_field = S.FormField(
            "Exchange For  (what you want in return)",
            "e.g. A bicycle or kitchen items", required=True)
        v.addWidget(self.exch_field)

        self.phone_field = S.FormField("Contact Phone", "06xxxxxxxx / 07xxxxxxxx",
                                        required=True)
        S.restrict_phone_input(self.phone_field.edit)
        phone = self.user.get("phone", "")
        if phone:
            self.phone_field.set_text(phone)
        v.addWidget(self.phone_field)

        self.loc_field = S.FormDropdown(
            "Location", S.REGIONS, required=True)
        loc = self.user.get("location", "")
        if loc:
            self.loc_field.set_value(loc)
        v.addWidget(self.loc_field)

        self.feedback = QLabel("")
        self.feedback.setWordWrap(True)
        self.feedback.setVisible(False)
        v.addWidget(self.feedback)

        btn_row = QHBoxLayout()
        post_btn = S.primary_btn("Post Item", self._submit)
        cancel_btn = S.ghost_btn("Cancel", lambda: self.on_navigate("dashboard"))
        btn_row.addWidget(post_btn, 1)
        btn_row.addWidget(cancel_btn, 1)
        v.addLayout(btn_row)

        for f in (self.title_field, self.exch_field, self.phone_field):
            f.returnPressed.connect(self._submit)

        parent_row.addWidget(card, 2)

    # ── Image preview panel ───────────────────────────────────────────────────

    def _build_preview(self, parent_row):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(8)

        v.addWidget(S.h_label("Item Image *", size=15, weight=700))
        v.addWidget(S.hline())
        v.addWidget(S.body_label("Required. JPG, PNG or GIF — max 5 MB",
                                  size=11, color=S.TEXT_MUTED))

        self.img_lbl = QLabel("Click to upload image\n(JPG/PNG, max 5MB)")
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setFixedHeight(160)
        self.img_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.img_lbl.setWordWrap(True)
        self.img_lbl.setStyleSheet(
            f"background:{S.PRIMARY_LIGHT}; border:2px dashed {S.PRIMARY};"
            f" border-radius:8px; color:{S.PRIMARY}; font-size:12px;")
        self.img_lbl.mousePressEvent = lambda e: self._pick_image()
        v.addWidget(self.img_lbl)

        choose_btn = S.secondary_btn("Choose Image", self._pick_image)
        v.addWidget(choose_btn)
        remove_btn = S.ghost_btn("Remove Image", self._remove_image)
        v.addWidget(remove_btn)

        self.img_name_lbl = S.body_label("", size=11, color=S.TEXT_MUTED)
        self.img_name_lbl.setWordWrap(True)
        v.addWidget(self.img_name_lbl)

        self.img_error_lbl = QLabel("")
        self.img_error_lbl.setStyleSheet(
            f"color:{S.ERROR}; font-size:11px; background:transparent;")
        self.img_error_lbl.setWordWrap(True)
        self.img_error_lbl.setVisible(False)
        v.addWidget(self.img_error_lbl)
        v.addStretch(1)

        parent_row.addWidget(card, 1)

    # ── Image helpers ─────────────────────────────────────────────────────────

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Item Image", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp)")
        if not path:
            return
        try:
            if os.path.getsize(path) > 5 * 1024 * 1024:
                QMessageBox.warning(self, "File Too Large",
                                     "Please choose an image under 5 MB.")
                return
            ext = os.path.splitext(path)[1]
            fname = f"{uuid.uuid4().hex}{ext}"
            dest = os.path.join(UPLOADS_DIR, fname)
            shutil.copy2(path, dest)
            self._image_path = dest

            pix = QPixmap(dest)
            if not pix.isNull():
                pix = pix.scaled(220, 160, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
                self.img_lbl.setPixmap(pix)
                self.img_lbl.setStyleSheet(
                    f"background:{S.BG_CARD}; border:1px solid {S.BORDER}; border-radius:8px;")
            size_mb = os.path.getsize(dest) / (1024 * 1024)
            self.img_name_lbl.setText(
                f"{os.path.basename(path)}  ({size_mb:.1f} MB)\nClick image to change")
            self._clear_image_error()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not load image:\n{exc}")

    def _remove_image(self):
        self._image_path = ""
        self.img_lbl.setPixmap(QPixmap())
        self.img_lbl.setText("Click to upload image\n(JPG/PNG, max 5MB)")
        self.img_lbl.setStyleSheet(
            f"background:{S.PRIMARY_LIGHT}; border:2px dashed {S.PRIMARY};"
            f" border-radius:8px; color:{S.PRIMARY}; font-size:12px;")
        self.img_name_lbl.setText("")

    def _clear_image_error(self):
        self.img_error_lbl.setVisible(False)
        self.img_error_lbl.setText("")
        self.img_lbl.setStyleSheet(
            f"background:{S.PRIMARY_LIGHT}; border:2px dashed {S.PRIMARY};"
            f" border-radius:8px; color:{S.PRIMARY}; font-size:12px;")

    def _show_image_error(self, msg):
        self.img_error_lbl.setText(msg)
        self.img_error_lbl.setVisible(True)
        self.img_lbl.setStyleSheet(
            f"background:#FFF5F5; border:2px dashed {S.ERROR};"
            f" border-radius:8px; color:{S.ERROR}; font-size:12px;")

    # ── Validation & submit ───────────────────────────────────────────────────

    def _submit(self):
        self.feedback.setVisible(False)
        self._clear_image_error()

        v = S.FormValidator()
        v.add(self.title_field, lambda: bool(self.title_field.text()),
              "Item name is required.")
        v.add(self.title_field, lambda: len(self.title_field.text()) >= 3,
              "Item name must be at least 3 characters.")
        v.add(self.exch_field, lambda: bool(self.exch_field.text()),
              "Please specify what you want in exchange.")
        v.add(self.phone_field, lambda: bool(self.phone_field.text()),
              "Contact phone number is required.")
        v.add(self.phone_field, lambda: bool(S.PHONE_RE.match(self.phone_field.text())),
              "Phone number must start with 06 or 07 (10 digits, e.g. 0712345678).")
        v.add(self.loc_field, lambda: bool(self.loc_field.value()),
              "Please select a location.")
        if not v.validate():
            return

        if not self._image_path:
            self._show_image_error("Please add a photo of the item before posting.")
            return

        DB.post_item(
            user_id=self.user["id"],
            title=self.title_field.text(),
            category=self.cat_field.value(),
            description=self.desc_field.text(),
            condition=self.cond_field.value(),
            exchange_for=self.exch_field.text(),
            phone=self.phone_field.text(),
            location=self.loc_field.value(),
            image_path=self._image_path)

        self.feedback.setVisible(True)
        self.feedback.setStyleSheet(
            f"background:{S.SUCCESS_LIGHT}; color:{S.SUCCESS}; padding:8px 10px;"
            f" border-radius:6px; font-size:12px;")
        self.feedback.setText("Item posted successfully! Your item is now live.")
        QTimer.singleShot(1200, lambda: self.on_navigate("my_items"))
