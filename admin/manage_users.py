"""
admin/manage_users.py  --  WeShare Community (PyQt6 edition)
Search + table: Name | Email | Region | Role | Status | Joined | Actions.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.ADMIN_NAV


class ManageUsersPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "users", user, on_logout, on_navigate,
                          "Manage Users", "View, suspend, and remove community members")

        search_row = QHBoxLayout()
        self.search_field = S.FormField("", "Search users by name or email...")
        search_row.addWidget(self.search_field, 1)
        search_btn = S.primary_btn("Search", self._load)
        search_row.addWidget(search_btn)
        self.search_field.returnPressed.connect(self._load)
        self.body.addLayout(search_row)

        self.card = S.make_card()
        self.cv = QVBoxLayout(self.card)
        self.cv.setContentsMargins(0, 0, 0, 0)
        self.cv.setSpacing(0)

        head = QHBoxLayout()
        head.setContentsMargins(20, 10, 20, 10)
        for label, stretch in [("Name", 2), ("Email", 3), ("Region", 2),
                                ("Role", 1), ("Status", 2), ("Joined", 1), ("Actions", 2)]:
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

        self._load()

    def _clear_rows(self):
        while self.rows_layout.count():
            it = self.rows_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def _load(self):
        self._clear_rows()
        term = self.search_field.text()
        users = DB.search_users(term) if term else DB.get_all_users()

        if not users:
            from PyQt6.QtWidgets import QLabel
            empty = S.body_label("No users found.", color=S.TEXT_MUTED)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setContentsMargins(0, 30, 0, 30)
            self.rows_layout.addWidget(empty)
        else:
            for u in users:
                self.rows_layout.addWidget(self._row(u))
                self.rows_layout.addWidget(S.hline())
        self.status_lbl.setText(f"{len(users)} user(s) found")

    def _row(self, u: dict) -> QWidget:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(20, 10, 20, 10)

        h.addWidget(S.body_label(u.get("full_name", ""), size=12), 2)
        h.addWidget(S.colored_text(u.get("email", ""), S.PRIMARY), 3)
        h.addWidget(S.body_label(u.get("location", ""), size=11, color=S.TEXT_MUTED), 2)

        role = u.get("role", "user")
        role_lbl = S.body_label(role, size=11,
                                 color=S.PRIMARY if role == "admin" else S.TEXT_MUTED, bold=(role == "admin"))
        h.addWidget(role_lbl, 1)

        badge_box = QHBoxLayout()
        badge_box.addWidget(S.status_badge(u.get("status", "active")))
        badge_box.addStretch(1)
        bw = QWidget(); bw.setLayout(badge_box)
        h.addWidget(bw, 2)

        h.addWidget(S.body_label(str(u.get("created_at", ""))[:10],
                                  size=11, color=S.TEXT_MUTED), 1)

        actions = QHBoxLayout()
        actions.setSpacing(6)
        view_btn = S.small_btn("View", lambda checked=False, uu=u: self._view(uu))
        actions.addWidget(view_btn)
        if u.get("id") != self.user["id"]:
            if u.get("status") == "suspended":
                act_btn = S.small_btn("Activate", lambda checked=False, uu=u: self._activate(uu),
                                       bg=S.SUCCESS_LIGHT, fg=S.SUCCESS)
            else:
                act_btn = S.small_btn("Suspend", lambda checked=False, uu=u: self._suspend(uu),
                                       bg=S.WARNING_LIGHT, fg=S.WARNING)
            actions.addWidget(act_btn)
            del_btn = S.small_btn("Delete", lambda checked=False, uu=u: self._delete(uu),
                                   bg=S.ERROR_LIGHT, fg=S.ERROR)
            actions.addWidget(del_btn)
        actions.addStretch(1)
        aw = QWidget(); aw.setLayout(actions)
        h.addWidget(aw, 2)
        return row

    def _view(self, u: dict):
        dlg = QDialog(self)
        dlg.setWindowTitle(u.get("full_name", "User"))
        dlg.resize(380, 280)
        dlg.setObjectName("dlgRoot")
        dlg.setStyleSheet(f"QDialog#dlgRoot{{background:{S.BG_PAGE};}}")
        v = QVBoxLayout(dlg)
        v.addWidget(S.h_label(u.get("full_name", ""), size=15, weight=700))
        for label, key in [("Email", "email"), ("Phone", "phone"),
                            ("Region", "location"), ("Role", "role"),
                            ("Status", "status"), ("Joined", "created_at")]:
            row = QHBoxLayout()
            row.addWidget(S.body_label(f"{label}:", bold=True))
            row.addWidget(S.body_label(str(u.get(key, "")), color=S.TEXT_MUTED))
            row.addStretch(1)
            v.addLayout(row)
        v.addStretch(1)
        v.addWidget(S.ghost_btn("Close", dlg.close))
        dlg.exec()

    def _suspend(self, u: dict):
        res = QMessageBox.question(
            self, "Suspend User", "Suspend this user's account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            DB.set_user_status(u["id"], "suspended")
            self._load()

    def _activate(self, u: dict):
        DB.set_user_status(u["id"], "active")
        self._load()

    def _delete(self, u: dict):
        res = QMessageBox.question(
            self, "Delete User",
            "Permanently delete this user?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            DB.delete_user(u["id"])
            self._load()
