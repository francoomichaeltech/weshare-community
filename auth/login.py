"""
auth/login.py  --  WeShare Community (PyQt6 edition)
Full blue background with centred white card. Matches reference UI exactly.
"""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt

import styles_qt as S
import database as DB

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class LoginPage(QWidget):

    def __init__(self, on_login, on_register, parent=None):
        super().__init__(parent)
        self.on_login    = on_login
        self.on_register = on_register
        self.setObjectName("authRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.auth_background_qss("authRoot"))
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)

        card = S.make_card()
        card.setFixedWidth(420)
        card.setStyleSheet(
            f"QFrame#card{{background:{S.BG_CARD}; border:1px solid {S.BORDER};"
            f" border-radius:12px;}}")
        cv = QVBoxLayout(card)
        cv.setContentsMargins(40, 32, 40, 32)
        cv.setSpacing(0)
        S.apply_elevation(card)

        cv.addWidget(S.h_label("Welcome Back", size=20, weight=700),
                     alignment=Qt.AlignmentFlag.AlignHCenter)
        sub = S.body_label("Sign in to your WeShare account", size=11, color=S.TEXT_MUTED)
        sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        cv.addSpacing(2)
        cv.addWidget(sub, alignment=Qt.AlignmentFlag.AlignHCenter)
        cv.addSpacing(14)
        cv.addWidget(S.hline())
        cv.addSpacing(14)

        self.id_field = S.FormField("Email Address", "Enter your email", required=True)
        cv.addWidget(self.id_field)
        cv.addSpacing(6)

        self.pw_field = S.FormField("Password", "Enter your password",
                                     required=True, password=True)
        cv.addWidget(self.pw_field)

        fp_row = QHBoxLayout()
        fp_row.addStretch(1)
        forgot = S.link_btn("Forgot Password?")
        forgot.setStyleSheet(forgot.styleSheet() + "font-size:11px;")
        fp_row.addWidget(forgot)
        cv.addLayout(fp_row)

        self.global_err = QLabel("")
        self.global_err.setWordWrap(True)
        self.global_err.setStyleSheet(
            f"background:{S.ERROR_LIGHT}; color:{S.ERROR}; padding:8px 10px;"
            f" border-radius:6px; font-size:12px;")
        self.global_err.setVisible(False)
        cv.addSpacing(8)
        cv.addWidget(self.global_err)

        cv.addSpacing(14)
        submit = S.primary_btn("Sign In", self._submit)
        cv.addWidget(submit)

        cv.addSpacing(18)
        cv.addWidget(S.hline())
        cv.addSpacing(10)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(S.body_label("Don't have an account?", size=11, color=S.TEXT_MUTED))
        reg_btn = S.link_btn(" Register here", self.on_register)
        bottom.addWidget(reg_btn)
        bottom.addStretch(1)
        cv.addLayout(bottom)

        self.id_field.returnPressed.connect(self._submit)
        self.pw_field.returnPressed.connect(self._submit)

        row.addWidget(card)
        row.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)

    # ── Validation & submit ───────────────────────────────────────────────────

    def _submit(self):
        self.global_err.setVisible(False)
        validator = S.FormValidator()
        validator.add(self.id_field, lambda: bool(self.id_field.text()),
                      "Email address is required.")
        validator.add(self.id_field, lambda: bool(EMAIL_RE.match(self.id_field.text())),
                      "Enter a valid email address.")
        validator.add(self.pw_field, lambda: bool(self.pw_field.raw_text()),
                      "Password is required.")
        if not validator.validate():
            return

        identifier = self.id_field.text()
        password   = self.pw_field.raw_text()

        user = DB.authenticate(identifier, password)
        if not user:
            self._show_global("Incorrect email or password.")
            self.pw_field.edit.clear()
            self.pw_field.edit.setFocus()
            return

        if user.get("is_banned"):
            self._show_global("Your account has been suspended.")
            return

        self.on_login(user)

    def _show_global(self, msg):
        self.global_err.setText(msg)
        self.global_err.setVisible(True)
