"""
common.py  --  WeShare Community (PyQt6 edition)
Shared page scaffold: sidebar + header + scrollable body.
Used by every user/admin page so the layout matches the reference
screenshots exactly and code stays DRY.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt

import styles_qt as S


def confirm_logout(parent, on_logout):
    box = QMessageBox(parent)
    box.setWindowTitle("Sign Out")
    box.setText("Are you sure you want to sign out?")
    box.setIcon(QMessageBox.Icon.Question)
    box.setStandardButtons(QMessageBox.StandardButton.Yes |
                            QMessageBox.StandardButton.No)
    box.setDefaultButton(QMessageBox.StandardButton.No)
    if box.exec() == QMessageBox.StandardButton.Yes:
        on_logout()


def scroll_wrap(content: QWidget) -> QScrollArea:
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setObjectName("pageScroll")
    area.setStyleSheet(f"QScrollArea#pageScroll{{background:{S.BG_PAGE}; border:none;}}")
    area.setWidget(content)
    return area


class PageScaffold(QWidget):
    """
    Builds: [Sidebar][ header (PageHeader) / body (vbox, scrollable) ]
    Subclasses call super().__init__(...) then add widgets to self.body.
    """

    def __init__(self, nav_items, active_key, user, on_logout, on_navigate,
                 title, subtitle="", scrollable=True, parent=None):
        super().__init__(parent)
        self.user        = user
        self.on_logout   = on_logout
        self.on_navigate = on_navigate

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        uname = user.get("full_name", user.get("name", "User"))
        urole = user.get("location", "") if user.get("role") != "admin" \
            else "Administrator"

        self.sidebar = S.Sidebar(
            nav_items, active_key, uname, urole,
            on_nav=self.on_navigate,
            on_logout=lambda: confirm_logout(self, self.on_logout))
        root.addWidget(self.sidebar)

        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        main_w = QWidget()
        main_w.setObjectName("scaffoldMain")
        main_w.setStyleSheet(f"QWidget#scaffoldMain{{background:{S.BG_PAGE};}}")
        main_w.setLayout(main)
        root.addWidget(main_w, 1)

        self.header = S.PageHeader(title, subtitle, uname)
        main.addWidget(self.header)

        self.body = QVBoxLayout()
        self.body.setContentsMargins(24, 20, 24, 20)
        self.body.setSpacing(14)
        body_w = QWidget()
        body_w.setObjectName("scaffoldBody")
        body_w.setStyleSheet(f"QWidget#scaffoldBody{{background:{S.BG_PAGE};}}")
        body_w.setLayout(self.body)

        if scrollable:
            area = scroll_wrap(body_w)
            main.addWidget(area, 1)
        else:
            main.addWidget(body_w, 1)
        self.body_widget = body_w
