"""
pages/terms.py  --  WeShare Community (PyQt6 edition)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from pages._static import static_page

SECTIONS = [
    ("Acceptance of Terms",
     "By using WeShare Community, you agree to these Terms and Conditions. "
     "If you do not agree, please do not use the platform."),
    ("User Responsibilities",
     "You are responsible for all content you post. Items must be accurately "
     "described. Misrepresentation, fraud, or abuse will result in account suspension."),
    ("Prohibited Items",
     "You may not post illegal items, weapons, controlled substances, or anything "
     "that violates local laws or community safety guidelines."),
    ("Exchanges",
     "WeShare Community facilitates connections between users but is not responsible "
     "for the outcome of exchanges. Users agree to meet in safe, public locations."),
    ("Account Termination",
     "We reserve the right to terminate accounts that violate these terms, "
     "engage in spam, harassment, or otherwise harm the community."),
    ("Changes to Terms",
     "These terms may be updated periodically. Continued use of the platform "
     "after changes constitutes acceptance of the new terms."),
]


class TermsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        page = static_page("Terms and Conditions", SECTIONS)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(page)
