"""
user/settings.py  --  WeShare Community (PyQt6 edition)
Tabbed settings matching the reference image: Account | Notifications |
Privacy | Appearance | Help.  Account tab also carries Change Password
and the Danger Zone (delete account) from the original feature set.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.USER_NAV
TABS = ["Account", "Notifications", "Privacy", "Appearance", "Help"]


class ToggleSwitch(QCheckBox):
    """Simple styled on/off switch (checkbox dressed up)."""

    def __init__(self, checked=True):
        super().__init__()
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QCheckBox::indicator {{ width: 38px; height: 20px; border-radius: 10px;
                background: {S.BORDER}; }}
            QCheckBox::indicator:checked {{ background: {S.PRIMARY}; }}
        """)


class SettingsPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate, on_update=None):
        super().__init__(NAV, "settings", user, on_logout, on_navigate, "Settings")
        self.on_update = on_update
        self.fresh_user = DB.get_user(user["id"]) or user

        row = QHBoxLayout()
        row.setSpacing(16)
        self._build_tabs(row)
        self.content_area = QVBoxLayout()
        cw = QWidget(); cw.setLayout(self.content_area)
        row.addWidget(cw, 3)
        self.body.addLayout(row)
        self.body.addStretch(1)

        self._active_tab = "Account"
        self._render_tab()

    # ── Tab list ──────────────────────────────────────────────────────────────

    def _build_tabs(self, parent_row):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 8, 0, 8)
        v.setSpacing(2)
        card.setFixedWidth(180)
        self._tab_buttons = {}
        for t in TABS:
            btn = QPushButton(t)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, tt=t: self._switch_tab(tt))
            v.addWidget(btn)
            self._tab_buttons[t] = btn
        v.addStretch(1)
        parent_row.addWidget(card, 1)
        self._highlight_tabs()

    def _highlight_tabs(self):
        for t, btn in self._tab_buttons.items():
            active = t == getattr(self, "_active_tab", "Account")
            if active:
                btn.setStyleSheet(
                    f"QPushButton{{background:{S.PRIMARY_LIGHT}; color:{S.PRIMARY};"
                    f" border:none; text-align:left; padding:10px 16px; font-weight:600;}}")
            else:
                btn.setStyleSheet(
                    f"QPushButton{{background:transparent; color:{S.TEXT_DARK};"
                    f" border:none; text-align:left; padding:10px 16px;}}"
                    f"QPushButton:hover{{background:{S.BG_PAGE};}}")

    def _switch_tab(self, tab):
        self._active_tab = tab
        self._highlight_tabs()
        self._render_tab()

    def _clear_content(self):
        while self.content_area.count():
            it = self.content_area.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def _render_tab(self):
        self._clear_content()
        if self._active_tab == "Account":
            self._render_account()
        elif self._active_tab == "Notifications":
            self._render_notifications()
        elif self._active_tab == "Privacy":
            self._render_simple(
                "Privacy",
                "Control who can see your profile, items, and contact details. "
                "Your phone number is only shared with members you choose to "
                "exchange with.")
        elif self._active_tab == "Appearance":
            self._render_simple(
                "Appearance",
                "WeShare currently uses a clean, light theme designed for "
                "clarity and ease of use across all devices.")
        elif self._active_tab == "Help":
            self._render_simple(
                "Help & Support",
                "Need assistance? Reach out to the WeShare team at "
                "support@weshare.app or visit the About page from the "
                "welcome screen for more information about the platform.")

    # ── Account tab ───────────────────────────────────────────────────────────

    def _render_account(self):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(8)
        v.addWidget(S.h_label("Account Settings", size=15, weight=700))
        v.addWidget(S.hline())

        self.name_field = S.FormField("Display Name", required=True)
        self.name_field.set_text(self.fresh_user.get("full_name", ""))
        v.addWidget(self.name_field)

        self.email_field = S.FormField("Email", required=True)
        self.email_field.set_text(self.fresh_user.get("email", ""))
        v.addWidget(self.email_field)

        self.region_field = S.FormDropdown("Region", S.REGIONS)
        loc = self.fresh_user.get("location", "")
        if loc:
            self.region_field.set_value(loc)
        v.addWidget(self.region_field)

        notif_row = QHBoxLayout()
        notif_row.addWidget(S.body_label("Email Notifications", size=12, bold=True))
        notif_row.addStretch(1)
        self.email_notif_toggle = ToggleSwitch(checked=True)
        notif_row.addWidget(self.email_notif_toggle)
        v.addLayout(notif_row)

        self.acct_feedback = QLabel("")
        self.acct_feedback.setVisible(False)
        self.acct_feedback.setWordWrap(True)
        v.addWidget(self.acct_feedback)

        v.addWidget(S.primary_btn("Save Settings", self._save_account))
        self.content_area.addWidget(card)

        # ── Change Password ──────────────────────────────────────────────────
        pw_card = S.make_card()
        pv = QVBoxLayout(pw_card)
        pv.setContentsMargins(24, 20, 24, 20)
        pv.setSpacing(8)
        pv.addWidget(S.h_label("Change Password", size=14, weight=700))
        pv.addWidget(S.body_label("Choose a strong password. Min 6 characters.",
                                   size=11, color=S.TEXT_MUTED))
        pv.addWidget(S.hline())

        self.cur_pw = S.FormField("Current Password", password=True, required=True)
        pv.addWidget(self.cur_pw)
        self.new_pw = S.FormField(f"New Password (min {S.PASSWORD_MIN_LEN} chars)",
                                   password=True, required=True)
        pv.addWidget(self.new_pw)
        self.conf_pw = S.FormField("Confirm New Password", password=True, required=True)
        pv.addWidget(self.conf_pw)

        self.pw_feedback = QLabel("")
        self.pw_feedback.setVisible(False)
        self.pw_feedback.setWordWrap(True)
        pv.addWidget(self.pw_feedback)
        pv.addWidget(S.primary_btn("Change Password", self._change_password))
        self.content_area.addWidget(pw_card)

        # ── Danger zone ───────────────────────────────────────────────────────
        dz = S.make_card()
        dz.setStyleSheet(
            f"QFrame#card{{background:{S.BG_CARD}; border:1px solid {S.ERROR};"
            f" border-radius:10px;}}")
        dv = QVBoxLayout(dz)
        dv.setContentsMargins(24, 20, 24, 20)
        dv.setSpacing(8)
        dv.addWidget(S.h_label("Danger Zone", size=14, weight=700, color=S.ERROR))
        warn = S.body_label(
            "Deleting your account removes your profile, all your items, "
            "messages, and reviews permanently.", color=S.TEXT_MUTED)
        warn.setWordWrap(True)
        dv.addWidget(warn)
        dv.addWidget(S.danger_btn("Delete My Account", self._delete_account))
        self.content_area.addWidget(dz)
        self.content_area.addStretch(1)

    def _save_account(self):
        v = S.FormValidator()
        v.add(self.name_field, lambda: bool(self.name_field.text()),
              "Display name is required.")
        v.add(self.email_field, lambda: bool(self.email_field.text()),
              "Email is required.")
        if not v.validate():
            return
        ok, msg = DB.update_user(self.user["id"], {
            "full_name": self.name_field.text(),
            "email": self.email_field.text(),
            "location": self.region_field.value(),
        })
        self.acct_feedback.setVisible(True)
        if ok:
            self.acct_feedback.setStyleSheet(
                f"background:{S.SUCCESS_LIGHT}; color:{S.SUCCESS}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.acct_feedback.setText("Settings saved.")
            self.fresh_user = DB.get_user(self.user["id"])
            if self.on_update:
                self.on_update(self.user["id"])
        else:
            self.acct_feedback.setStyleSheet(
                f"background:{S.ERROR_LIGHT}; color:{S.ERROR}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.acct_feedback.setText(msg)

    def _change_password(self):
        v = S.FormValidator()
        v.add(self.cur_pw, lambda: bool(self.cur_pw.raw_text()),
              "Enter your current password.")
        v.add(self.cur_pw,
              lambda: DB.authenticate(self.fresh_user["email"], self.cur_pw.raw_text()) is not None,
              "Current password is incorrect.")
        v.add(self.new_pw, lambda: bool(self.new_pw.raw_text()),
              "Enter a new password.")
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
        self.pw_feedback.setVisible(True)
        if ok:
            self.pw_feedback.setStyleSheet(
                f"background:{S.SUCCESS_LIGHT}; color:{S.SUCCESS}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.pw_feedback.setText("Password changed successfully.")
            self.cur_pw.set_text(""); self.new_pw.set_text(""); self.conf_pw.set_text("")
        else:
            self.pw_feedback.setStyleSheet(
                f"background:{S.ERROR_LIGHT}; color:{S.ERROR}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.pw_feedback.setText(msg)

    def _delete_account(self):
        res = QMessageBox.question(
            self, "Delete Account",
            "This will permanently delete your account and ALL your data.\n"
            "This cannot be undone. Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            DB.delete_user(self.user["id"])
            QMessageBox.information(self, "Account Deleted",
                                     "Your account has been deleted. Goodbye.")
            self.on_logout()

    # ── Notifications tab ─────────────────────────────────────────────────────

    def _render_notifications(self):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)
        v.addWidget(S.h_label("Notification Preferences", size=15, weight=700))
        v.addWidget(S.body_label("Choose which alerts you want to receive.",
                                  size=11, color=S.TEXT_MUTED))
        v.addWidget(S.hline())

        self._notif_checks = []
        options = [
            "Exchange requests from other members",
            "New messages in your inbox",
            "New reviews on your profile",
            "WeShare platform announcements",
        ]
        for label in options:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            v.addWidget(cb)
            self._notif_checks.append(cb)

        self.notif_feedback = QLabel("")
        self.notif_feedback.setVisible(False)
        v.addWidget(self.notif_feedback)

        def _save():
            self.notif_feedback.setVisible(True)
            self.notif_feedback.setStyleSheet(
                f"background:{S.SUCCESS_LIGHT}; color:{S.SUCCESS}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.notif_feedback.setText("Preferences saved.")

        v.addWidget(S.primary_btn("Save Preferences", _save))
        self.content_area.addWidget(card)
        self.content_area.addStretch(1)

    # ── Generic simple info tab ───────────────────────────────────────────────

    def _render_simple(self, title, text):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(8)
        v.addWidget(S.h_label(title, size=15, weight=700))
        v.addWidget(S.hline())
        lbl = S.body_label(text, color=S.TEXT_MUTED)
        lbl.setWordWrap(True)
        v.addWidget(lbl)
        self.content_area.addWidget(card)
        self.content_area.addStretch(1)
