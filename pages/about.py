"""
pages/about.py  --  WeShare Community (PyQt6 edition)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

import styles_qt as S
from pages._static import static_page

SECTIONS = [
    ("What is WeShare Community?", [
        "WeShare Community is a platform that brings people together through "
        "the exchange of goods, skills, and services.",
        "Our mission is to promote a culture of sharing and sustainable "
        "consumption within local communities across Tanzania.",
        "We believe that every item, skill, or service that goes unused is a "
        "missed opportunity for someone else in your community.",
    ]),
    ("How It Works", [
        "Post items or services you are willing to share or exchange with "
        "other community members for free.",
        "Browse available listings from people near you and send an exchange "
        "request directly to the owner.",
        "Both parties agree on the exchange terms and complete the transaction "
        "at a time and place that suits them.",
        "After each exchange, leave a review to help build trust across the "
        "community and recognise reliable members.",
    ]),
    ("Our Values", [
        "Community First: We believe strong communities are built on trust, "
        "generosity, and mutual support — not just transactions.",
        "Sustainability: By sharing instead of buying new, we collectively "
        "reduce waste and our environmental footprint.",
        "Inclusivity: WeShare is open to everyone regardless of background, "
        "income, or location within Tanzania.",
        "Safety: We provide clear tools to report inappropriate behaviour "
        "and maintain a respectful, safe space for all members.",
    ]),
    ("Who Can Join?", [
        "Anyone can join WeShare Community. Whether you have household items, "
        "tools, clothes, or professional skills to share, there is a place for "
        "you here.",
        "Registration is completely free and takes less than two minutes. "
        "No fees, no subscriptions — just community.",
        "Once registered, you can start posting items and browsing listings "
        "from other members in your area immediately.",
    ]),
    ("Contact Us", [
        "For support, feedback, or partnership enquiries, please reach out to "
        "our team and we will be happy to help.",
        "Email: support@wesharecommunity.app",
        "We respond to all messages within 24 hours on business days.",
    ]),
]


class AboutPage(QWidget):
    def __init__(self, on_get_started=None, parent=None):
        super().__init__(parent)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(S.primary_btn("Get Started", on_get_started or (lambda: None)))
        btn_w = QWidget()
        btn_w.setLayout(btn_row)

        page = static_page("About WeShare Community", SECTIONS, extra_widget=btn_w)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(page)
