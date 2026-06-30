"""
pages/_static.py  --  WeShare Community (PyQt6 edition)
Shared scrollable static-content page builder used by About/Terms/Privacy/Safety.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt

import styles_qt as S


def static_page(title: str, sections, extra_widget=None) -> QWidget:
    """
    sections: list of (heading, paragraphs) where paragraphs is a str
              or a list of str.
    Returns a ready-to-display QWidget (place inside a dialog or stack).
    """
    root = QWidget()
    root.setObjectName("staticRoot")
    root.setStyleSheet(f"QWidget#staticRoot{{background:{S.BG_PAGE};}}")
    outer = QVBoxLayout(root)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    topbar = S.make_card()
    topbar.setStyleSheet(
        f"QFrame#card{{background:{S.BG_CARD}; border:none; border-bottom:1px solid {S.BORDER};"
        f" border-radius:0px;}}")
    tv = QVBoxLayout(topbar)
    tv.setContentsMargins(20, 14, 20, 14)
    tv.addWidget(S.h_label(title, size=16, weight=700))
    outer.addWidget(topbar)

    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    body = QWidget()
    body.setObjectName("staticBody")
    body.setStyleSheet(f"QWidget#staticBody{{background:{S.BG_PAGE};}}")
    bv = QVBoxLayout(body)
    bv.setContentsMargins(28, 22, 28, 22)
    bv.setSpacing(14)

    for heading, content in sections:
        card = S.make_card()
        cv = QVBoxLayout(card)
        cv.setContentsMargins(24, 18, 24, 18)
        cv.setSpacing(8)
        cv.addWidget(S.h_label(heading, size=14, weight=700, color=S.PRIMARY))
        cv.addWidget(S.hline())

        paragraphs = content if isinstance(content, list) else [content]
        for para in paragraphs:
            lbl = S.body_label(para, size=12, color=S.TEXT_DARK)
            lbl.setWordWrap(True)
            cv.addWidget(lbl)
        bv.addWidget(card)

    if extra_widget:
        bv.addWidget(extra_widget)
    bv.addStretch(1)

    area.setWidget(body)
    outer.addWidget(area, 1)
    return root
