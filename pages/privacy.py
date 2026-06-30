"""
pages/privacy.py  --  WeShare Community (PyQt6 edition)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from pages._static import static_page

SECTIONS = [
    ("Information We Collect",
     "We collect information you provide during registration (name, email, phone), "
     "content you post (items, messages, reviews), and basic usage data to improve "
     "the platform experience."),
    ("How We Use Your Information",
     "Your information is used to operate the platform, enable exchanges between "
     "users, send notifications, and improve our services. We do not sell personal data."),
    ("Data Sharing",
     "We do not share your personal data with third parties except as required "
     "by law or with your explicit consent. Your public profile (name, location, "
     "items) is visible to other registered users."),
    ("Data Security",
     "We use industry-standard security practices to protect your data. "
     "Passwords are stored as secure hashes and never in plain text."),
    ("Your Rights",
     "You have the right to access, correct, or delete your data at any time. "
     "Use the Settings page to manage your account, or contact support "
     "to request data deletion."),
    ("Cookies",
     "This desktop application does not use browser cookies. Session data "
     "is stored locally on your device for the duration of your session."),
]


class PrivacyPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        page = static_page("Privacy Policy", SECTIONS)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(page)
