"""
pages/safety.py  --  WeShare Community (PyQt6 edition)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from pages._static import static_page

SECTIONS = [
    ("Meeting in Person",
     "Always meet exchange partners in a public, well-lit location such as "
     "a shopping centre, library, or police station parking lot. Bring a friend "
     "if possible and let someone know where you are going."),
    ("Verifying Items",
     "Inspect items carefully before completing an exchange. Ask for photos "
     "in advance and do not proceed if the item does not match its description."),
    ("Protecting Your Personal Information",
     "Never share sensitive personal information such as your home address, "
     "bank details, or ID documents with other users. Use the in-app messaging "
     "system for all communication."),
    ("Recognising Scams",
     "Be cautious of users who request money transfers, ask you to move "
     "communication off the platform, or pressure you to exchange quickly. "
     "Report suspicious activity immediately."),
    ("Reporting Problems",
     "Use the Report button on any user profile or item listing to flag "
     "inappropriate content or behaviour. Our moderation team reviews all "
     "reports within 24 hours."),
    ("Emergency Situations",
     "If you feel threatened or unsafe, leave the situation immediately and "
     "contact local emergency services. Then report the incident to WeShare "
     "support so we can take appropriate action."),
]


class SafetyPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        page = static_page("Safety Guidelines", SECTIONS)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(page)
