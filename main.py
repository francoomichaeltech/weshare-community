"""
main.py  --  WeShare Community (PyQt6 edition)
Application entry point and page router.
Run:  python main.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QDialog, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

import styles_qt as S
import database as DB


class InfoDialog(QDialog):
    """Modal overlay for About / Terms / Privacy / Safety pages."""

    def __init__(self, parent, title, widget):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 600)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(widget)
        self.setObjectName("infoDialog")
        self.setStyleSheet(f"QDialog#infoDialog{{background:{S.BG_PAGE};}}")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        DB._get_conn()  # initialise DB on startup
        self.setWindowTitle("WeShare Community")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 680)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._session = None
        self._current = None

        self._go("login")

    # ── Navigation ───────────────────────────────────────────────────────────

    def _go(self, key, **kwargs):
        widget = self._build(key, **kwargs)
        if widget is None:
            return
        old = self._current
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)
        self._current = widget
        if old is not None:
            self.stack.removeWidget(old)
            old.deleteLater()

    def _build(self, key, **kwargs):
        # ── Auth ──────────────────────────────────────────────────────────
        if key == "login":
            from auth.login import LoginPage
            return LoginPage(on_login=self._on_login,
                              on_register=lambda: self._go("register"))

        if key == "register":
            from auth.register import RegisterPage
            return RegisterPage(on_success=lambda: self._go("login"),
                                 on_back=lambda: self._go("login"))

        if key == "logout":
            self._session = None
            from auth.login import LoginPage
            return LoginPage(on_login=self._on_login,
                              on_register=lambda: self._go("register"))

        # ── Guard ─────────────────────────────────────────────────────────
        if not self._session:
            from auth.login import LoginPage
            return LoginPage(on_login=self._on_login,
                              on_register=lambda: self._go("register"))

        u = self._session

        # ── Info pages → modal dialog overlay ──────────────────────────────
        if key in ("about", "terms", "privacy", "safety"):
            self._open_info(key)
            return None

        # ── Admin / user pages ──────────────────────────────────────────────
        if u.get("role") == "admin":
            return self._admin_page(key, u, **kwargs)
        return self._user_page(key, u, **kwargs)

    # ── User page factory ────────────────────────────────────────────────────

    def _user_page(self, key, u, **kwargs):
        nav = self._go

        if key in ("dashboard", "home"):
            from user.dashboard import DashboardPage
            return DashboardPage(u, self._logout, nav)
        if key == "browse":
            from user.browse import BrowsePage
            return BrowsePage(u, self._logout, nav)
        if key == "post":
            from user.add_item import AddItemPage
            return AddItemPage(u, self._logout, nav)
        if key == "my_items":
            from user.my_items import MyItemsPage
            return MyItemsPage(u, self._logout, nav)
        if key == "messages":
            from user.messages import MessagesPage
            return MessagesPage(u, self._logout, nav,
                                 partner_id=kwargs.get("partner_id"))
        if key == "wants":
            from user.wants import WantsPage
            return WantsPage(u, self._logout, nav)
        if key == "profile":
            from user.profile import ProfilePage
            return ProfilePage(u, self._logout, nav)
        if key == "notifications":
            from user.notifications import NotificationsPage
            return NotificationsPage(u, self._logout, nav)
        if key == "history":
            from user.history import HistoryPage
            return HistoryPage(u, self._logout, nav)
        if key == "reviews":
            from user.review import ReviewsPage
            return ReviewsPage(u, self._logout, nav)
        if key == "settings":
            from user.settings import SettingsPage
            return SettingsPage(u, self._logout, nav, on_update=self._refresh_session)

        from user.dashboard import DashboardPage
        return DashboardPage(u, self._logout, nav)

    # ── Admin page factory ───────────────────────────────────────────────────

    def _admin_page(self, key, u, **kwargs):
        nav = self._go

        if key == "dashboard":
            from admin.dashboard import AdminDashboardPage
            return AdminDashboardPage(u, self._logout, nav)
        if key == "users":
            from admin.manage_users import ManageUsersPage
            return ManageUsersPage(u, self._logout, nav)
        if key in ("items", "exchanges"):
            from admin.exchanges import ExchangesPage
            return ExchangesPage(u, self._logout, nav)
        if key == "reports":
            from admin.reports import ReportsPage
            return ReportsPage(u, self._logout, nav)
        if key == "analytics":
            from admin.analytics import AnalyticsPage
            return AnalyticsPage(u, self._logout, nav)
        if key == "settings":
            from admin.settings import AdminSettingsPage
            return AdminSettingsPage(u, self._logout, nav)

        from admin.dashboard import AdminDashboardPage
        return AdminDashboardPage(u, self._logout, nav)

    # ── Info pages ───────────────────────────────────────────────────────────

    def _open_info(self, key):
        mapping = {
            "about":   ("About WeShare",    "pages.about",   "AboutPage"),
            "terms":   ("Terms of Service", "pages.terms",   "TermsPage"),
            "privacy": ("Privacy Policy",   "pages.privacy", "PrivacyPage"),
            "safety":  ("Safety Guide",     "pages.safety",  "SafetyPage"),
        }
        title, mod_path, cls_name = mapping[key]
        import importlib
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        dlg = InfoDialog(self, title, cls())
        dlg.exec()

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _on_login(self, user: dict):
        self._session = user
        self._go("dashboard")

    def _refresh_session(self, uid: int):
        updated = DB.get_user(uid)
        if updated:
            updated["name"] = updated.get("full_name", "")
            self._session = updated

    def _logout(self):
        self._go("logout")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(S.stylesheet())
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
