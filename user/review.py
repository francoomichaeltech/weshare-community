"""
user/review.py  --  WeShare Community (PyQt6 edition)
Reviews & Ratings page matching reference image (overall rating + list with stars).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QDialog, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.USER_NAV


def _stars(rating: int) -> str:
    rating = max(0, min(5, int(rating)))
    return "★" * rating + "☆" * (5 - rating)


class ReviewsPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "reviews", user, on_logout, on_navigate,
                          "Reviews & Ratings",
                          "Reviews you have received from community members")

        write_btn = S.primary_btn("Write a Review", self._open_write_dialog)
        self.header.add_widget(write_btn)

        self._load()

    def _load(self):
        uid = self.user["id"]
        stats = DB.get_user_stats(uid) or {}

        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)
        v.addWidget(S.body_label("Overall Rating", size=14, bold=True))
        v.addWidget(S.hline())

        avg = stats.get("avg_rating", 0.0)
        count = stats.get("review_count", 0)

        top = QHBoxLayout()
        big = S.h_label(f"{avg:.1f}" if avg else "N/A", size=24, weight=700, color=S.PRIMARY)
        top.addWidget(big)
        sub_col = QVBoxLayout()
        sub_col.addWidget(S.body_label(f"/ 5.0  from {count} reviews",
                                        size=11, color=S.TEXT_MUTED))
        star_lbl = S.body_label(_stars(round(avg)), size=16, color=S.WARNING)
        sub_col.addWidget(star_lbl)
        scw = QWidget(); scw.setLayout(sub_col)
        top.addWidget(scw)
        top.addStretch(1)
        v.addLayout(top)
        self.body.addWidget(card)

        section = S.make_card()
        sv = QVBoxLayout(section)
        sv.setContentsMargins(20, 16, 20, 16)
        sv.setSpacing(10)
        sv.addWidget(S.body_label("Reviews Received", size=14, bold=True))
        sv.addWidget(S.hline())

        reviews = DB.get_reviews_for_user(uid) or []
        if not reviews:
            empty = S.body_label("No reviews yet.", color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 24, 0, 24)
            sv.addWidget(empty)
        else:
            for rv in reviews:
                sv.addWidget(self._review_card(rv))

        self.body.addWidget(section)
        self.body.addStretch(1)

    def _review_card(self, rv: dict) -> QWidget:
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(14, 10, 14, 10)
        v.setSpacing(4)

        top = QHBoxLayout()
        top.addWidget(S.body_label(rv.get("reviewer_name", "Anonymous"), size=12, bold=True))
        top.addWidget(S.body_label(_stars(rv.get("rating", 0)), size=13, color=S.WARNING))
        top.addStretch(1)
        top.addWidget(S.body_label(str(rv.get("created_at", ""))[:10],
                                    size=10, color=S.TEXT_MUTED))
        v.addLayout(top)

        comment = (rv.get("comment") or "").strip()
        if comment:
            lbl = S.body_label(comment, size=12, color=S.TEXT_DARK)
            lbl.setWordWrap(True)
            v.addWidget(lbl)
        return card

    def _open_write_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Write a Review")
        dlg.resize(420, 380)
        dlg.setObjectName("dlgRoot")
        dlg.setStyleSheet(f"QDialog#dlgRoot{{background:{S.BG_PAGE};}}")
        v = QVBoxLayout(dlg)
        v.addWidget(S.h_label("Write a Review", size=15, weight=700))

        uid_field = S.FormField("Member Name or Email", required=True)
        v.addWidget(uid_field)

        v.addWidget(S.body_label("Rating (1 to 5)", size=11, bold=True))
        group = QButtonGroup(dlg)
        rr = QHBoxLayout()
        radios = []
        for i in range(1, 6):
            rb = QRadioButton(str(i))
            if i == 5:
                rb.setChecked(True)
            group.addButton(rb)
            radios.append(rb)
            rr.addWidget(rb)
        v.addLayout(rr)

        comment_field = S.FormTextArea("Comment", height=80)
        v.addWidget(comment_field)

        def _submit():
            term = uid_field.text()
            if not term:
                uid_field.show_error("Enter the member's name or email.")
                return
            users = DB.search_users(term)
            users = [u for u in users if u["id"] != self.user["id"]]
            if not users:
                uid_field.show_error("No matching member found.")
                return
            rating = 5
            for i, rb in enumerate(radios, start=1):
                if rb.isChecked():
                    rating = i
            DB.add_review(self.user["id"], users[0]["id"], rating, comment_field.text())
            dlg.close()
            QMessageBox.information(self, "Success", "Review submitted.")
            self._refresh()

        v.addWidget(S.primary_btn("Submit Review", _submit))
        dlg.exec()

    def _refresh(self):
        while self.body.count():
            it = self.body.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        self._load()
