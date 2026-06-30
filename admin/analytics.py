"""
admin/analytics.py  --  WeShare Community (PyQt6 edition)
Stat cards + category-breakdown bars + top-users table.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.ADMIN_NAV


class AnalyticsPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "analytics", user, on_logout, on_navigate,
                          "Analytics", "Platform activity and statistics")

        stats = DB.get_admin_stats()

        self.body.addWidget(S.body_label("Overview", size=13, bold=True))
        row = QHBoxLayout()
        row.setSpacing(12)
        stat_items = [
            ("Total Users",     stats.get("total_users", 0),         S.PRIMARY),
            ("Total Items",     stats.get("total_items", 0),         S.INFO),
            ("Available Items", stats.get("available_items", 0),     S.SUCCESS),
            ("Total Exchanges", stats.get("total_exchanges", 0),      S.WARNING),
            ("Completed",       stats.get("completed_exchanges", 0),  S.SUCCESS),
            ("Pending Reports", stats.get("pending_reports", 0),      S.ERROR),
        ]
        for label, val, color in stat_items:
            row.addWidget(S.stat_card(label, val, color))
        self.body.addLayout(row)

        self.body.addWidget(S.body_label("Items by Category", size=13, bold=True))
        self.body.addWidget(self._category_chart())

        self.body.addWidget(S.body_label("Top Users by Items Posted", size=13, bold=True))
        self.body.addWidget(self._top_users_table())
        self.body.addStretch(1)

    def _category_chart(self) -> QWidget:
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(8)

        c = DB._get_conn()
        rows = c.execute(
            "SELECT category, COUNT(*) AS cnt FROM items "
            "GROUP BY category ORDER BY cnt DESC").fetchall()

        if not rows:
            v.addWidget(S.body_label("No item data available.", color=S.TEXT_MUTED))
            return card

        max_val = max(r[1] for r in rows) or 1
        for cat, cnt in rows:
            v.addLayout(self._bar_row(cat, cnt, max_val))
        return card

    def _bar_row(self, label, value, max_val):
        row = QHBoxLayout()
        cbg, cfg = S.CATEGORY_COLORS.get(label, (S.PRIMARY_LIGHT, S.PRIMARY))

        name_lbl = S.body_label(label, size=11)
        name_lbl.setFixedWidth(90)
        row.addWidget(name_lbl)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(16)
        bar_bg.setStyleSheet(f"background:{S.BG_PAGE}; border:1px solid {S.BORDER}; border-radius:4px;")
        bv = QHBoxLayout(bar_bg)
        bv.setContentsMargins(0, 0, 0, 0)
        rel = value / max_val if max_val else 0
        bar = QFrame()
        bar.setStyleSheet(f"background:{cfg}; border-radius:4px;")
        bv.addWidget(bar, int(rel * 100) if rel > 0 else 0)
        bv.addStretch(100 - int(rel * 100) if rel < 1 else 0)
        row.addWidget(bar_bg, 1)

        val_lbl = S.body_label(str(value), size=11, color=S.TEXT_MUTED)
        val_lbl.setFixedWidth(30)
        row.addWidget(val_lbl)
        return row

    def _top_users_table(self) -> QWidget:
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        head = QHBoxLayout()
        head.setContentsMargins(20, 10, 20, 10)
        for label, stretch in [("Rank", 1), ("Name", 3), ("Email", 3),
                                ("Items", 1), ("Exchanges", 1)]:
            head.addWidget(S.body_label(label, size=10, bold=True, color=S.TEXT_MUTED), stretch)
        hw = QWidget(); hw.setLayout(head)
        v.addWidget(hw)
        v.addWidget(S.hline())

        c = DB._get_conn()
        rows = c.execute(
            "SELECT u.id, u.full_name, u.email, "
            "  COUNT(DISTINCT i.id) AS item_cnt, "
            "  COUNT(DISTINCT e.id) AS exc_cnt "
            "FROM users u "
            "LEFT JOIN items i ON i.user_id=u.id "
            "LEFT JOIN exchanges e ON e.requester_id=u.id OR e.owner_id=u.id "
            "WHERE u.role='user' "
            "GROUP BY u.id ORDER BY item_cnt DESC LIMIT 10").fetchall()

        if not rows:
            empty = S.body_label("No user data available.", color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 20, 0, 20)
            v.addWidget(empty)
            return card

        for i, r in enumerate(rows, 1):
            row = QHBoxLayout()
            row.setContentsMargins(20, 8, 20, 8)
            row.addWidget(S.body_label(str(i), size=11), 1)
            row.addWidget(S.body_label(r["full_name"], size=12), 3)
            row.addWidget(S.body_label(r["email"], size=11, color=S.TEXT_MUTED), 3)
            row.addWidget(S.body_label(str(r["item_cnt"]), size=11), 1)
            row.addWidget(S.body_label(str(r["exc_cnt"]), size=11), 1)
            rw = QWidget(); rw.setLayout(row)
            v.addWidget(rw)
            v.addWidget(S.hline())
        return card
