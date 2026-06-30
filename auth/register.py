"""
auth/register.py  --  WeShare Community (PyQt6 edition)
Full blue background with centred white card. Matches reference UI exactly.
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer

import styles_qt as S
import database as DB

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class RegisterPage(QWidget):

    def __init__(self, on_success, on_back, parent=None):
        super().__init__(parent)
        self.on_success = on_success
        self.on_back     = on_back
        self.setObjectName("authRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.auth_background_qss("authRoot"))
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.Shape.NoFrame)
        area.setObjectName("regScroll")
        area.setStyleSheet("QScrollArea#regScroll{background: transparent; border: none;}")
        outer.addWidget(area)

        holder = QWidget()
        holder.setObjectName("regHolder")
        holder.setStyleSheet("QWidget#regHolder{background: transparent;}")
        hv = QVBoxLayout(holder)
        hv.setContentsMargins(0, 40, 0, 40)
        hv.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)

        card = S.make_card()
        card.setFixedWidth(560)
        card.setStyleSheet(
            f"QFrame#card{{background:{S.BG_CARD}; border:1px solid {S.BORDER};"
            f" border-radius:12px;}}")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(40, 30, 40, 30)
        cv.setSpacing(0)
        S.apply_elevation(card)

        cv.addWidget(S.h_label("Create Account", size=20, weight=700),
                     alignment=Qt.AlignmentFlag.AlignHCenter)
        sub = S.body_label("Join the WeShare community today", size=11, color=S.PRIMARY)
        sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cv.addSpacing(2)
        cv.addWidget(sub, alignment=Qt.AlignmentFlag.AlignHCenter)
        cv.addSpacing(14)
        cv.addWidget(S.hline())
        cv.addSpacing(10)

        row1 = QHBoxLayout()
        row1.setSpacing(16)
        self.name_field = S.FormField("Full Name", "Your full name", required=True)
        self.phone_field = S.FormField("Phone Number", "06xxxxxxxx / 07xxxxxxxx",
                                        required=True)
        S.restrict_phone_input(self.phone_field.edit)
        row1.addWidget(self.name_field)
        row1.addWidget(self.phone_field)
        cv.addLayout(row1)
        cv.addSpacing(6)

        self.email_field = S.FormField("Email Address", "you@example.com", required=True)
        cv.addWidget(self.email_field)
        cv.addSpacing(6)

        row2 = QHBoxLayout()
        row2.setSpacing(16)
        self.pw_field = S.FormField(
            "Password", f"At least {S.PASSWORD_MIN_LEN} characters",
            required=True, password=True)
        self.pw2_field = S.FormField("Confirm Password", "Repeat password",
                                      required=True, password=True)
        row2.addWidget(self.pw_field)
        row2.addWidget(self.pw2_field)
        cv.addLayout(row2)
        cv.addSpacing(6)

        self.region_field = S.FormDropdown(
            "Region", S.REGIONS, required=True,
            placeholder="Select your region...")
        cv.addWidget(self.region_field)

        self.feedback = QLabel("")
        self.feedback.setWordWrap(True)
        self.feedback.setVisible(False)
        cv.addSpacing(8)
        cv.addWidget(self.feedback)

        cv.addSpacing(14)
        submit = S.primary_btn("Create Account", self._submit)
        cv.addWidget(submit)

        cv.addSpacing(14)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(S.body_label("Already have an account?", size=11, color=S.TEXT_MUTED))
        si_btn = S.link_btn(" Sign in", self.on_back)
        bottom.addWidget(si_btn)
        bottom.addStretch(1)
        cv.addLayout(bottom)

        for f in (self.name_field, self.phone_field, self.email_field,
                  self.pw_field, self.pw2_field):
            f.returnPressed.connect(self._submit)

        row.addWidget(card)
        row.addStretch(1)
        hv.addLayout(row)
        hv.addStretch(1)
        area.setWidget(holder)

    # ── Validation & submit ───────────────────────────────────────────────────

    def _submit(self):
        self.feedback.setVisible(False)

        v = S.FormValidator()

        # 1) Full Name
        v.add(self.name_field, lambda: bool(self.name_field.text()),
              "Full name is required.")

        # 2) Phone Number — 06xxxxxxxx or 07xxxxxxxx, exactly 10 digits
        v.add(self.phone_field, lambda: bool(self.phone_field.text()),
              "Phone number is required.")
        v.add(self.phone_field, lambda: len(self.phone_field.text()) == 10,
              "Phone number must be exactly 10 digits.")
        v.add(self.phone_field, lambda: bool(S.PHONE_RE.match(self.phone_field.text())),
              "Phone number must start with 06 or 07 (e.g. 0712345678).")

        # 3) Email Address
        v.add(self.email_field, lambda: bool(self.email_field.text()),
              "Email address is required.")
        v.add(self.email_field, lambda: bool(EMAIL_RE.match(self.email_field.text())),
              "Enter a valid email address.")

        # 4) Password — min length + complexity (uppercase, lowercase, digit)
        v.add(self.pw_field, lambda: bool(self.pw_field.raw_text()),
              "Password is required.")
        v.add(self.pw_field,
              lambda: len(self.pw_field.raw_text()) >= S.PASSWORD_MIN_LEN,
              f"Password must be at least {S.PASSWORD_MIN_LEN} characters.")
        v.add(self.pw_field,
              lambda: not S.password_errors(self.pw_field.raw_text()),
              "Password needs an uppercase letter, a lowercase letter, "
              "and a number.")

        # 5) Confirm Password
        v.add(self.pw2_field, lambda: bool(self.pw2_field.raw_text()),
              "Please confirm your password.")
        v.add(self.pw2_field,
              lambda: self.pw_field.raw_text() == self.pw2_field.raw_text(),
              "Passwords do not match.")

        # 6) Region
        v.add(self.region_field, lambda: bool(self.region_field.value()),
              "Please select your region.")

        if not v.validate():
            return

        ok, msg = DB.register_user(
            self.name_field.text(), self.email_field.text(),
            self.phone_field.text(), self.pw_field.raw_text(),
            self.region_field.value())

        self.feedback.setVisible(True)
        if ok:
            self.feedback.setStyleSheet(
                f"background:{S.SUCCESS_LIGHT}; color:{S.SUCCESS}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.feedback.setText(msg)
            QTimer.singleShot(1400, self.on_success)
        else:
            self.feedback.setStyleSheet(
                f"background:{S.ERROR_LIGHT}; color:{S.ERROR}; padding:8px 10px;"
                f" border-radius:6px; font-size:12px;")
            self.feedback.setText(msg)
