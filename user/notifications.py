"""
user/notifications.py  --  WeShare Community (PyQt6 edition)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.USER_NAV


class NotificationsPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "notifications", user, on_logout, on_navigate,
                          "Notifications", "Your activity feed")

        mark_btn = S.small_btn("Mark All Read", self._mark_all_read,
                                bg=S.SUCCESS_LIGHT, fg=S.SUCCESS)
        self.header.add_widget(mark_btn)

        filt = QHBoxLayout()
        filt.addWidget(S.body_label("Filter: ", size=11, bold=True))
        self._filter_buttons = {}
        for opt in ("All", "Unread", "Read"):
            btn = S.small_btn(opt, lambda checked=False, o=opt: self._set_filter(o))
            self._filter_buttons[opt] = btn
            filt.addWidget(btn)
        filt.addStretch(1)
        self.body.addLayout(filt)

        self.status_lbl = S.body_label("", size=11, color=S.TEXT_MUTED)
        self.body.addWidget(self.status_lbl)

        self.list_box = QVBoxLayout()
        self.list_box.setSpacing(8)
        lw = QWidget(); lw.setLayout(self.list_box)
        self.body.addWidget(lw)
        self.body.addStretch(1)

        self._active_filter = "All"
        self._load()
        self._highlight_filter()

    def _highlight_filter(self):
        for opt, btn in self._filter_buttons.items():
            active = opt == self._active_filter
            bg = S.PRIMARY if active else S.BG_PAGE
            fg = "white" if active else S.TEXT_MUTED
            btn.setStyleSheet(
                f"QPushButton{{background:{bg}; color:{fg}; border:1px solid {bg};"
                f" border-radius:5px; padding:5px 10px; font-size:12px;}}")

    def _load(self):
        self._all = DB.get_notifications(self.user["id"])
        self._render(self._all)

    def _set_filter(self, val):
        self._active_filter = val
        self._highlight_filter()
        if val == "Unread":
            data = [n for n in self._all if not n.get("is_read")]
        elif val == "Read":
            data = [n for n in self._all if n.get("is_read")]
        else:
            data = self._all
        self._render(data)

    def _clear_list(self):
        while self.list_box.count():
            it = self.list_box.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def _render(self, notifs):
        self._clear_list()
        if not notifs:
            empty = S.body_label("No notifications to show.", color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 40, 0, 40)
            self.list_box.addWidget(empty)
            self.status_lbl.setText("0 notifications")
            return

        unread = sum(1 for n in notifs if not n.get("is_read"))
        self.status_lbl.setText(f"{len(notifs)} notification(s)  |  {unread} unread")

        for n in notifs:
            self.list_box.addWidget(self._card(n))

    def _card(self, n):
        is_read = bool(n.get("is_read"))
        bg = S.BG_CARD if is_read else S.PRIMARY_LIGHT
        card = QWidget()
        card.setObjectName("notifCard")
        card.setStyleSheet(
            f"QWidget#notifCard{{background:{bg}; border:1px solid {S.BORDER}; border-radius:8px;}}")
        v = QVBoxLayout(card)
        v.setContentsMargins(16, 10, 16, 10)
        v.setSpacing(4)

        top = QHBoxLayout()
        if not is_read:
            badge = QLabel("NEW")
            badge.setStyleSheet(
                f"background:{S.PRIMARY}; color:white; border-radius:3px;"
                f" padding:2px 6px; font-size:9px; font-weight:700;")
            top.addWidget(badge)
        top.addStretch(1)
        top.addWidget(S.body_label(str(n.get("created_at", ""))[:16],
                                    size=10, color=S.TEXT_MUTED))
        v.addLayout(top)

        msg = QLabel(n.get("message", ""))
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color:{S.TEXT_DARK}; background:transparent; font-size:12px;")
        v.addWidget(msg)

        if not is_read:
            mark_row = QHBoxLayout()
            mark_row.addStretch(1)
            mark_btn = S.link_btn("Mark as read", lambda checked=False, nid=n["id"]: self._mark_one(nid))
            mark_row.addWidget(mark_btn)
            v.addLayout(mark_row)
        return card

    def _mark_one(self, nid):
        DB.mark_notification_read(nid)
        self._load()
        self._set_filter(self._active_filter)

    def _mark_all_read(self):
        DB.mark_all_notifications_read(self.user["id"])
        self._load()
        self._set_filter(self._active_filter)
