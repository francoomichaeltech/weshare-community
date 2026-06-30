"""
user/profile.py  --  WeShare Community (PyQt6 edition)
Left: avatar card with stats.  Right: edit profile + change password.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.USER_NAV


class ProfilePage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "profile", user, on_logout, on_navigate, "My Profile")
        self.fresh_user = DB.get_user(user["id"]) or user

        row = QHBoxLayout()
        row.setSpacing(16)
        self._build_avatar_card(row)
        self._build_edit_card(row)
        self.body.addLayout(row)
        self.body.addStretch(1)

    # ── Avatar / stats card ──────────────────────────────────────────────────

    def _build_avatar_card(self, parent_row):
        card = S.make_card()
        card.setFixedWidth(260)
        v = QVBoxLayout(card)
        v.setContentsMargins(20, 28, 20, 20)
        v.setSpacing(4)
        v.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        name = self.fresh_user.get("full_name", "")
        initials = "".join([p[0] for p in name.split()[:2]]).upper() or "U"
        self.avatar_lbl = QLabel(initials)
        self.avatar_lbl.setFixedSize(90, 90)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet(
            f"background:{S.PRIMARY_LIGHT}; color:{S.PRIMARY}; border-radius:45px;"
            f" font-size:26px; font-weight:700;")
        v.addWidget(self.avatar_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        v.addSpacing(10)

        self.name_lbl = S.h_label(name, size=15, weight=700)
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        v.addWidget(self.name_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.email_lbl = S.body_label(self.fresh_user.get("email", ""), size=11, color=S.PRIMARY)
        self.email_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        v.addWidget(self.email_lbl)
        self.loc_lbl = S.body_label(self.fresh_user.get("location", ""), size=11, color=S.TEXT_MUTED)
        self.loc_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        v.addWidget(self.loc_lbl)

        v.addSpacing(10)
        bio_text = (self.fresh_user.get("bio") or "").strip() or "No bio added yet."
        self.bio_lbl = S.body_label(bio_text, size=11,
                                     color=S.TEXT_MUTED if not self.fresh_user.get("bio") else S.TEXT_DARK)
        self.bio_lbl.setWordWrap(True)
        self.bio_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        v.addWidget(self.bio_lbl)

        v.addSpacing(14)
        v.addWidget(S.hline())
        v.addSpacing(10)

        stats = DB.get_user_stats(self.user["id"]) or {}
        stat_row = QHBoxLayout()
        for label, val in [
            ("Items", stats.get("items_posted", 0)),
            ("Exchanges", stats.get("exchanges_done", 0)),
            ("Rating", f"{stats.get('avg_rating', 0.0):.1f}"),
        ]:
            col = QVBoxLayout()
            vlbl = S.h_label(str(val), size=14, weight=700, color=S.PRIMARY)
            vlbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(vlbl)
            llbl = S.body_label(label, size=10, color=S.TEXT_MUTED)
            llbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(llbl)
            cw = QWidget(); cw.setLayout(col)
            stat_row.addWidget(cw)
        srw = QWidget(); srw.setLayout(stat_row)
        v.addWidget(srw)
        v.addStretch(1)

        parent_row.addWidget(card, 1)

    def _refresh_avatar_card(self):
        """Reflects the freshly-saved profile data immediately, in real
        time, without requiring the user to leave and revisit the page."""
        u = self.fresh_user
        name = u.get("full_name", "")
        initials = "".join([p[0] for p in name.split()[:2]]).upper() or "U"
        self.avatar_lbl.setText(initials)
        self.name_lbl.setText(name)
        self.email_lbl.setText(u.get("email", ""))
        self.loc_lbl.setText(u.get("location", ""))
        bio = (u.get("bio") or "").strip()
        self.bio_lbl.setText(bio or "No bio added yet.")
        self.bio_lbl.setStyleSheet(
            f"color:{S.TEXT_DARK if bio else S.TEXT_MUTED}; background:transparent;")

    # ── Edit profile / password card ─────────────────────────────────────────

    def _build_edit_card(self, parent_row):
        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(8)

        v.addWidget(S.h_label("Edit Profile", size=15, weight=700))
        v.addWidget(S.body_label(
            "This information is visible to other members on your public profile.",
            size=11, color=S.TEXT_MUTED))
        v.addWidget(S.hline())

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self.name_field = S.FormField("Full Name", required=True)
        self.name_field.set_text(self.fresh_user.get("full_name", ""))
        self.phone_field = S.FormField("Phone")
        self.phone_field.set_text(self.fresh_user.get("phone", ""))
        row1.addWidget(self.name_field)
        row1.addWidget(self.phone_field)
        v.addLayout(row1)

        self.email_field = S.FormField("Email", required=True)
        self.email_field.set_text(self.fresh_user.get("email", ""))
        v.addWidget(self.email_field)

        self.loc_field = S.FormDropdown("Location / Region", S.REGIONS)
        loc = self.fresh_user.get("location", "")
        if loc:
            self.loc_field.set_value(loc)
        v.addWidget(self.loc_field)

        self.bio_field = S.FormTextArea("Bio (visible to all)", height=70)
        self.bio_field.set_text(self.fresh_user.get("bio", ""))
        v.addWidget(self.bio_field)

        v.addSpacing(6)
        v.addWidget(S.body_label("Change Password", size=12, bold=True))
        self.cur_pw = S.FormField("Current Password", password=True)
        v.addWidget(self.cur_pw)
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        self.new_pw = S.FormField("New Password", f"At least {S.PASSWORD_MIN_LEN} characters",
                                   password=True)
        self.new_pw2 = S.FormField("Confirm New Password", "Repeat password", password=True)
        row2.addWidget(self.new_pw)
        row2.addWidget(self.new_pw2)
        v.addLayout(row2)

        self.feedback = QLabel("")
        self.feedback.setWordWrap(True)
        self.feedback.setVisible(False)
        v.addWidget(self.feedback)

        v.addWidget(S.primary_btn("Save Changes", self._save))

        for f in (self.name_field, self.phone_field, self.email_field):
            f.returnPressed.connect(self._save)

        parent_row.addWidget(card, 2)

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        self.feedback.setVisible(False)

        v = S.FormValidator()
        v.add(self.name_field, lambda: bool(self.name_field.text()),
              "Full name is required.")
        v.add(self.email_field, lambda: bool(self.email_field.text()),
              "Email is required.")
        if self.new_pw.raw_text() or self.new_pw2.raw_text() or self.cur_pw.raw_text():
            v.add(self.cur_pw, lambda: bool(self.cur_pw.raw_text()),
                  "Enter your current password to change it.")
            v.add(self.cur_pw,
                  lambda: DB.authenticate(self.fresh_user["email"],
                                          self.cur_pw.raw_text()) is not None,
                  "Current password is incorrect.")
            v.add(self.new_pw, lambda: len(self.new_pw.raw_text()) >= S.PASSWORD_MIN_LEN,
                  f"New password must be at least {S.PASSWORD_MIN_LEN} characters.")
            v.add(self.new_pw, lambda: not S.password_errors(self.new_pw.raw_text()),
                  "Password needs an uppercase letter, a lowercase letter, "
                  "and a number.")
            v.add(self.new_pw2, lambda: self.new_pw.raw_text() == self.new_pw2.raw_text(),
                  "Passwords do not match.")
        if not v.validate():
            return

        data = {
            "full_name": self.name_field.text(),
            "email": self.email_field.text(),
            "phone": self.phone_field.text(),
            "location": self.loc_field.value(),
            "bio": self.bio_field.text(),
        }
        if self.new_pw.raw_text():
            data["password"] = self.new_pw.raw_text()

        ok, msg = DB.update_user(self.user["id"], data)
        self.feedback.setVisible(True)
        if ok:
            self.feedback.setStyleSheet(
                f"background:{S.SUCCESS_LIGHT}; color:{S.SUCCESS}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.feedback.setText("Profile updated successfully.")
            self.fresh_user = DB.get_user(self.user["id"])
            self.user.update(self.fresh_user)
            self._refresh_avatar_card()
            self.cur_pw.set_text(""); self.new_pw.set_text(""); self.new_pw2.set_text("")
        else:
            self.feedback.setStyleSheet(
                f"background:{S.ERROR_LIGHT}; color:{S.ERROR}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.feedback.setText(msg)
