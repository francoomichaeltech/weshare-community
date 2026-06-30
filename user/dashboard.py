"""
user/dashboard.py  --  WeShare Community (PyQt6 edition)
Dashboard: 4 stat cards + Recent Items table.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.USER_NAV


class DashboardPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "dashboard", user, on_logout, on_navigate,
                          "Dashboard")
        self._build_stats()
        self._build_recent()

    def _build_stats(self):
        row = QHBoxLayout()
        row.setSpacing(14)

        items_count     = len(DB.get_user_items(self.user["id"]))
        exchanges_count  = DB.count_user_exchanges(self.user["id"])
        wants_count      = DB.count_user_wants(self.user["id"])
        avg_rating       = DB.get_avg_rating(self.user["id"])
        rating_str       = f"{avg_rating:.1f} / 5" if avg_rating else "N/A"

        cards = [
            ("Items Posted",   items_count,     S.PRIMARY),
            ("Exchanges Done", exchanges_count, S.SUCCESS),
            ("Wants Listed",   wants_count,     S.WARNING),
            ("Reviews",        rating_str,      S.INFO),
        ]
        for label, value, color in cards:
            row.addWidget(S.stat_card(label, value, color))
        self.body.addLayout(row)

    def _build_recent(self):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)

        hdr = QHBoxLayout()
        hdr.addWidget(S.body_label("Recent Items", size=13, bold=True))
        hdr.addStretch(1)
        view_all = S.link_btn("View All", lambda: self.on_navigate("my_items"))
        hdr.addWidget(view_all)
        v.addLayout(hdr)
        v.addWidget(S.hline())

        items = DB.get_user_items(self.user["id"])
        if not items:
            empty = S.body_label("No items posted yet.", color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(empty)
        else:
            head = QHBoxLayout()
            for label, stretch in [("Title", 3), ("Category", 2),
                                    ("Status", 2), ("Posted", 1)]:
                lbl = S.body_label(label, size=10, bold=True, color=S.TEXT_MUTED)
                head.addWidget(lbl, stretch)
            v.addLayout(head)
            v.addWidget(S.hline())

            for item in items[:8]:
                r = QHBoxLayout()
                r.addWidget(S.body_label(item.get("title", "")[:40]), 3)

                cat = item.get("category", "")
                _, cfg = S.CATEGORY_COLORS.get(cat, (S.BG_PAGE, S.TEXT_MUTED))
                r.addWidget(S.colored_text(cat, cfg), 2)

                badge_box = QHBoxLayout()
                badge_box.addWidget(S.status_badge(item.get("status", "available")))
                badge_box.addStretch(1)
                bw = QWidget(); bw.setLayout(badge_box)
                r.addWidget(bw, 2)

                date = str(item.get("created_at", ""))[:10]
                r.addWidget(S.body_label(date, size=11, color=S.TEXT_MUTED), 1)
                v.addLayout(r)
                v.addWidget(S.hline())

        self.body.addWidget(card)
        self.body.addStretch(1)
