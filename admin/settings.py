"""
admin/settings.py  --  WeShare Community (PyQt6 edition)
Admin account info (read-only) + change password.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.ADMIN_NAV


class AdminSettingsPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "settings", user, on_logout, on_navigate,
                          "Admin Settings", "Manage your administrator account")

        info_card = S.make_card()
        iv = QVBoxLayout(info_card)
        iv.setContentsMargins(24, 20, 24, 20)
        iv.setSpacing(6)
        iv.addWidget(S.h_label("Account Information", size=15, weight=700))
        iv.addWidget(S.hline())

        for label, key in [("Full Name", "full_name"), ("Email", "email"),
                            ("Phone", "phone"), ("Location", "location")]:
            row = QHBoxLayout()
            lbl = S.body_label(f"{label}:", size=11, bold=True, color=S.TEXT_MUTED)
            lbl.setFixedWidth(110)
            row.addWidget(lbl)
            row.addWidget(S.body_label(str(self.user.get(key, "") or "—"), size=12))
            row.addStretch(1)
            iv.addLayout(row)

        role_row = QHBoxLayout()
        rlbl = S.body_label("Role:", size=11, bold=True, color=S.TEXT_MUTED)
        rlbl.setFixedWidth(110)
        role_row.addWidget(rlbl)
        role_row.addWidget(S.body_label("Administrator", size=12, bold=True, color=S.PRIMARY))
        role_row.addStretch(1)
        iv.addLayout(role_row)

        self.body.addWidget(info_card)

        pw_card = S.make_card()
        pv = QVBoxLayout(pw_card)
        pv.setContentsMargins(24, 20, 24, 20)
        pv.setSpacing(8)
        pv.addWidget(S.h_label("Change Password", size=15, weight=700))
        pv.addWidget(S.hline())

        self.new_pw = S.FormField("New Password", f"At least {S.PASSWORD_MIN_LEN} characters",
                                   password=True, required=True)
        pv.addWidget(self.new_pw)
        self.conf_pw = S.FormField("Confirm New Password", password=True, required=True)
        pv.addWidget(self.conf_pw)

        self.feedback = QLabel("")
        self.feedback.setVisible(False)
        self.feedback.setWordWrap(True)
        pv.addWidget(self.feedback)

        pv.addWidget(S.primary_btn("Update Password", self._change_password))
        self.body.addWidget(pw_card)
        self.body.addStretch(1)

    def _change_password(self):
        v = S.FormValidator()
        v.add(self.new_pw, lambda: bool(self.new_pw.raw_text()),
              "New password is required.")
        v.add(self.new_pw, lambda: len(self.new_pw.raw_text()) >= S.PASSWORD_MIN_LEN,
              f"Password must be at least {S.PASSWORD_MIN_LEN} characters.")
        v.add(self.new_pw, lambda: not S.password_errors(self.new_pw.raw_text()),
              "Password needs an uppercase letter, a lowercase letter, "
              "and a number.")
        v.add(self.conf_pw, lambda: bool(self.conf_pw.raw_text()),
              "Please confirm your new password.")
        v.add(self.conf_pw, lambda: self.new_pw.raw_text() == self.conf_pw.raw_text(),
              "Passwords do not match.")
        if not v.validate():
            return

        ok, msg = DB.update_user(self.user["id"], {"password": self.new_pw.raw_text()})
        self.feedback.setVisible(True)
        if ok:
            self.feedback.setStyleSheet(
                f"background:{S.SUCCESS_LIGHT}; color:{S.SUCCESS}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.feedback.setText("Password changed successfully.")
            self.new_pw.set_text(""); self.conf_pw.set_text("")
        else:
            self.feedback.setStyleSheet(
                f"background:{S.ERROR_LIGHT}; color:{S.ERROR}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.feedback.setText(msg)
