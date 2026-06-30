"""
user/wants.py  --  WeShare Community (PyQt6 edition)
Two-column layout matching the reference image:
  left  = "My Wants" list with Remove buttons
  right = "Post a Want" inline form
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QTimer

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.USER_NAV


class WantsPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "wants", user, on_logout, on_navigate, "Wants")

        row = QHBoxLayout()
        row.setSpacing(16)
        self._build_my_wants(row)
        self._build_post_form(row)
        self.body.addLayout(row)
        self.body.addStretch(1)
        self._load()

    # ── My Wants list ─────────────────────────────────────────────────────────

    def _build_my_wants(self, parent_row):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)
        v.addWidget(S.body_label("My Wants", size=14, bold=True))
        v.addWidget(S.hline())

        self.list_box = QVBoxLayout()
        self.list_box.setSpacing(10)
        lw = QWidget(); lw.setLayout(self.list_box)
        v.addWidget(lw)
        v.addStretch(1)
        parent_row.addWidget(card, 1)
        self.my_wants_card = card

    def _load(self):
        while self.list_box.count():
            it = self.list_box.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        wants = DB.get_wants(self.user["id"])
        if not wants:
            empty = S.body_label("You haven't posted any wants yet.",
                                  color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_box.addWidget(empty)
            return

        for want in wants:
            self.list_box.addWidget(self._want_row(want))

    def _want_row(self, want: dict) -> QWidget:
        row = S.make_card()
        h = QHBoxLayout(row)
        h.setContentsMargins(16, 12, 16, 12)

        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(S.body_label(want.get("title", ""), size=13, bold=True))
        meta = QHBoxLayout()
        cat = want.get("category", "") or "Other"
        _, cfg = S.CATEGORY_COLORS.get(cat, (S.BG_PAGE, S.TEXT_MUTED))
        meta.addWidget(S.colored_text(cat, cfg))
        meta.addWidget(S.body_label(" • ", size=11, color=S.TEXT_MUTED))
        meta.addWidget(S.body_label(str(want.get("created_at", ""))[:10],
                                     size=11, color=S.TEXT_MUTED))
        meta.addStretch(1)
        left.addLayout(meta)
        lw = QWidget(); lw.setLayout(left)
        h.addWidget(lw, 1)

        remove_btn = S.small_btn("Remove", lambda checked=False, w=want: self._delete(w["id"]),
                                  bg=S.ERROR_LIGHT, fg=S.ERROR)
        h.addWidget(remove_btn)
        return row

    def _delete(self, want_id: int):
        res = QMessageBox.question(
            self, "Delete Want", "Remove this want post?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            DB.delete_want(want_id)
            self._load()

    # ── Post a Want form ──────────────────────────────────────────────────────

    def _build_post_form(self, parent_row):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)
        v.addWidget(S.body_label("Post a Want", size=14, bold=True))
        v.addWidget(S.hline())

        self.title_field = S.FormField("What are you looking for?",
                                        "e.g. A good bicycle", required=True)
        v.addWidget(self.title_field)

        self.cat_field = S.FormDropdown("Category", S.CATEGORIES)
        v.addWidget(self.cat_field)

        self.notes_field = S.FormTextArea(
            "Description (Optional)", "Describe what you need...", height=80)
        v.addWidget(self.notes_field)

        self.feedback = S.body_label("", size=11)
        self.feedback.setVisible(False)
        v.addWidget(self.feedback)

        post_btn = S.primary_btn("Post Want", self._submit)
        v.addWidget(post_btn)
        v.addStretch(1)

        self.title_field.returnPressed.connect(self._submit)
        parent_row.addWidget(card, 1)

    def _submit(self):
        validator = S.FormValidator()
        validator.add(self.title_field, lambda: bool(self.title_field.text()),
                       "Please enter what you need.")
        if not validator.validate():
            return

        DB.add_want(self.user["id"], self.title_field.text(),
                    self.cat_field.value(), self.notes_field.text())

        self.feedback.setVisible(True)
        self.feedback.setStyleSheet(
            f"background:{S.SUCCESS_LIGHT}; color:{S.SUCCESS}; padding:8px 10px;"
            f" border-radius:6px; font-size:12px;")
        self.feedback.setText("Posted successfully!")
        self.title_field.set_text("")
        self.notes_field.set_text("")
        QTimer.singleShot(900, self._load)
