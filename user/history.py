"""
user/history.py  --  WeShare Community (PyQt6 edition)
Exchange History matching reference image: Item | With | Status | Date | Review.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QDialog, QRadioButton, QButtonGroup
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.USER_NAV


class HistoryPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "history", user, on_logout, on_navigate,
                          "Exchange History",
                          "All your exchange requests — sent and received")

        filt = QHBoxLayout()
        filt.addWidget(S.body_label("Filter: ", size=11, bold=True))
        self._filter_buttons = {}
        for label, val in [("All", "all"), ("Pending", "pending"),
                            ("Completed", "completed"), ("Cancelled", "cancelled")]:
            btn = S.small_btn(label, lambda checked=False, v=val: self._set_filter(v))
            self._filter_buttons[val] = btn
            filt.addWidget(btn)
        filt.addStretch(1)
        self.body.addLayout(filt)

        self.card = S.make_card()
        self.cv = QVBoxLayout(self.card)
        self.cv.setContentsMargins(0, 0, 0, 0)
        self.cv.setSpacing(0)

        head = QHBoxLayout()
        head.setContentsMargins(20, 10, 20, 10)
        for label, stretch in [("Item", 3), ("With", 2), ("Status", 2),
                                ("Date", 1), ("Review", 2)]:
            head.addWidget(S.body_label(label, size=10, bold=True, color=S.TEXT_MUTED), stretch)
        hw = QWidget(); hw.setLayout(head)
        self.cv.addWidget(hw)
        self.cv.addWidget(S.hline())

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(0)
        rw = QWidget(); rw.setLayout(self.rows_layout)
        self.cv.addWidget(rw)

        self.body.addWidget(self.card)
        self.status_lbl = S.body_label("", size=11, color=S.TEXT_MUTED)
        self.body.addWidget(self.status_lbl)
        self.body.addStretch(1)

        self._active = "all"
        self._set_filter("all")

    def _highlight(self):
        for val, btn in self._filter_buttons.items():
            active = val == self._active
            bg = S.PRIMARY if active else S.BG_PAGE
            fg = "white" if active else S.TEXT_MUTED
            btn.setStyleSheet(
                f"QPushButton{{background:{bg}; color:{fg}; border:1px solid {bg};"
                f" border-radius:5px; padding:5px 10px; font-size:12px;}}")

    def _clear_rows(self):
        while self.rows_layout.count():
            it = self.rows_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def _set_filter(self, val):
        self._active = val
        self._highlight()
        self._clear_rows()
        rows = DB.get_exchange_history(self.user["id"], val)
        if not rows:
            empty = S.body_label("No exchange records found.", color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 30, 0, 30)
            self.rows_layout.addWidget(empty)
        else:
            for ex in rows:
                self.rows_layout.addWidget(self._row(ex))
                self.rows_layout.addWidget(S.hline())
        self.status_lbl.setText(f"{len(rows)} record(s)")

    def _row(self, ex: dict) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(20, 10, 20, 10)

        item_title = ex.get("item_given") or ex.get("item_received") or "—"
        h.addWidget(S.body_label(item_title, size=12), 3)
        h.addWidget(S.colored_text(ex.get("partner_name", "—"), S.PRIMARY), 2)

        badge_box = QHBoxLayout()
        badge_box.addWidget(S.status_badge(ex.get("status", "pending")))
        badge_box.addStretch(1)
        bw = QWidget(); bw.setLayout(badge_box)
        h.addWidget(bw, 2)

        h.addWidget(S.body_label(str(ex.get("created_at", ""))[:10],
                                  size=11, color=S.TEXT_MUTED), 1)

        action_box = QHBoxLayout()
        if ex.get("status") == "completed":
            rev_btn = S.small_btn("Leave Review", lambda checked=False, e=ex: self._review_dialog(e))
            action_box.addWidget(rev_btn)
        action_box.addStretch(1)
        aw = QWidget(); aw.setLayout(action_box)
        h.addWidget(aw, 2)
        return row

    def _review_dialog(self, ex: dict):
        partner_name = ex.get("partner_name", "this member")
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Review {partner_name}")
        dlg.resize(400, 320)
        dlg.setObjectName("dlgRoot")
        dlg.setStyleSheet(f"QDialog#dlgRoot{{background:{S.BG_PAGE};}}")
        v = QVBoxLayout(dlg)
        v.addWidget(S.h_label(f"Review {partner_name}", size=14, weight=700))
        v.addWidget(S.body_label("Rating", size=11, bold=True))

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

        # Determine the reviewee user id (the partner, not me)
        reviewee_id = (ex.get("owner_id") if ex.get("requester_id") == self.user["id"]
                       else ex.get("requester_id"))

        def _submit():
            rating = 5
            for i, rb in enumerate(radios, start=1):
                if rb.isChecked():
                    rating = i
            DB.add_review(self.user["id"], reviewee_id, rating,
                          comment_field.text(), exchange_id=ex.get("id"))
            dlg.close()

        v.addWidget(S.primary_btn("Submit Review", _submit))
        dlg.exec()
