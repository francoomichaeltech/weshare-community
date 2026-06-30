"""
admin/dashboard.py  --  WeShare Community (PyQt6 edition)
Admin overview: 4 stat cards + Recent Users / Recent Exchanges lists,
matching the reference image exactly.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.ADMIN_NAV


class AdminDashboardPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "dashboard", user, on_logout, on_navigate,
                          "Admin Dashboard")
        self._load()

    def _load(self):
        stats = DB.get_admin_stats()

        row = QHBoxLayout()
        row.setSpacing(14)
        cards = [
            ("Total Users",   stats.get("total_users", 0),     S.PRIMARY),
            ("Active Items",  stats.get("available_items", 0), S.SUCCESS),
            ("Exchanges",     stats.get("total_exchanges", 0),  S.INFO),
            ("Reports",       stats.get("pending_reports", 0),  S.ERROR),
        ]
        for label, val, color in cards:
            row.addWidget(S.stat_card(label, val, color))
        self.body.addLayout(row)

        lists_row = QHBoxLayout()
        lists_row.setSpacing(14)
        self._build_recent_users(lists_row)
        self._build_recent_exchanges(lists_row)
        self.body.addLayout(lists_row)
        self.body.addStretch(1)

    def _build_recent_users(self, parent_row):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)
        v.addWidget(S.body_label("Recent Users", size=13, bold=True))
        v.addWidget(S.hline())

        users = DB.get_all_users()[:6]
        if not users:
            v.addWidget(S.body_label("No users yet.", color=S.TEXT_MUTED))
        for u in users:
            row = QHBoxLayout()
            col = QVBoxLayout()
            col.setSpacing(1)
            col.addWidget(S.body_label(u.get("full_name", ""), size=12, bold=True))
            col.addWidget(S.body_label(u.get("email", ""), size=10, color=S.PRIMARY))
            cw = QWidget(); cw.setLayout(col)
            row.addWidget(cw, 1)
            row.addWidget(S.status_badge(u.get("status", "active")))
            v.addLayout(row)
            v.addWidget(S.hline())
        parent_row.addWidget(card, 1)

    def _build_recent_exchanges(self, parent_row):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)
        v.addWidget(S.body_label("Recent Exchanges", size=13, bold=True))
        v.addWidget(S.hline())

        exchanges = DB.get_all_exchanges()[:6]
        if not exchanges:
            v.addWidget(S.body_label("No exchanges yet.", color=S.TEXT_MUTED))
        for ex in exchanges:
            row = QHBoxLayout()
            col = QVBoxLayout()
            col.setSpacing(1)
            title = ex.get("item_received") or ex.get("item_given") or "—"
            col.addWidget(S.body_label(title, size=12, bold=True))
            sub = f"{ex.get('requester_name', '—')} > {ex.get('owner_name', '—')}"
            col.addWidget(S.body_label(sub, size=10, color=S.TEXT_MUTED))
            cw = QWidget(); cw.setLayout(col)
            row.addWidget(cw, 1)
            row.addWidget(S.status_badge(ex.get("status", "pending")))
            v.addLayout(row)
            v.addWidget(S.hline())
        parent_row.addWidget(card, 1)
