"""
admin/reports.py  --  WeShare Community (PyQt6 edition)
Admin: view and resolve user reports, matching reference image.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.ADMIN_NAV
FILTER_OPTS = [("All", ""), ("Pending", "pending"), ("Resolved", "resolved")]


class ReportsPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "reports", user, on_logout, on_navigate,
                          "Reports", "User-submitted reports and complaints")
        self._filter = ""

        filt = QHBoxLayout()
        filt.addWidget(S.body_label("Filter: ", size=11, bold=True))
        self._filter_buttons = {}
        for label, val in FILTER_OPTS:
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
        for label, stretch in [("Reporter", 2), ("Against", 2), ("Reason", 3),
                                ("Date", 1), ("Status", 2), ("Action", 2)]:
            head.addWidget(S.body_label(label, size=10, bold=True, color=S.TEXT_MUTED), stretch)
        hw = QWidget(); hw.setLayout(head)
        self.cv.addWidget(hw)
        self.cv.addWidget(S.hline())

        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(0)
        rw = QWidget(); rw.setLayout(self.rows_layout)
        self.cv.addWidget(rw)

        self.body.addWidget(self.card)
        self.body.addStretch(1)
        self._set_filter("")

    def _highlight(self):
        for val, btn in self._filter_buttons.items():
            active = val == self._filter
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
        self._filter = val
        self._highlight()
        self._clear_rows()

        all_rep = DB.get_all_reports()
        rows = [r for r in all_rep if not self._filter or r.get("status") == self._filter]

        if not rows:
            empty = S.body_label("No reports found.", color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 30, 0, 30)
            self.rows_layout.addWidget(empty)
            return

        for rep in rows:
            self.rows_layout.addWidget(self._row(rep))
            self.rows_layout.addWidget(S.hline())

    def _row(self, rep: dict) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(20, 10, 20, 10)

        h.addWidget(S.body_label(rep.get("reporter_name", "—"), size=12), 2)
        h.addWidget(S.body_label(rep.get("against_name", "—"), size=12), 2)
        h.addWidget(S.body_label((rep.get("reason") or "—")[:50], size=11, color=S.TEXT_MUTED), 3)
        h.addWidget(S.body_label(str(rep.get("created_at", ""))[:10],
                                  size=11, color=S.TEXT_MUTED), 1)

        badge_box = QHBoxLayout()
        badge_box.addWidget(S.status_badge(rep.get("status", "pending")))
        badge_box.addStretch(1)
        bw = QWidget(); bw.setLayout(badge_box)
        h.addWidget(bw, 2)

        st = rep.get("status", "pending")
        rid = rep["id"]
        actions = QHBoxLayout()
        actions.setSpacing(6)
        if st == "pending":
            actions.addWidget(S.small_btn("Resolve", lambda: self._set_status(rid, "resolved"),
                                           bg=S.SUCCESS_LIGHT, fg=S.SUCCESS))
            actions.addWidget(S.small_btn("Dismiss", lambda: self._set_status(rid, "dismissed")))
        actions.addStretch(1)
        aw = QWidget(); aw.setLayout(actions)
        h.addWidget(aw, 2)
        return row

    def _set_status(self, rid, status):
        DB.update_report_status(rid, status)
        self._set_filter(self._filter)
