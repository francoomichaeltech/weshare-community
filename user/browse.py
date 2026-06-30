"""
user/browse.py  --  WeShare Community (PyQt6 edition)
Browse Items: search bar + 3-column grid of item cards.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QDialog,
    QFrame, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

import styles_qt as S
import database as DB
from common import PageScaffold

NAV = S.USER_NAV
COLS = 3


class BrowsePage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate):
        super().__init__(NAV, "browse", user, on_logout, on_navigate,
                          "Browse Items")
        self._all_items = []
        self._build_search()
        self.grid_holder = QWidget()
        self.grid_layout = QGridLayout(self.grid_holder)
        self.grid_layout.setSpacing(16)
        self.body.addWidget(self.grid_holder)
        self.body.addStretch(1)
        self._load()

    def _build_search(self):
        row = QHBoxLayout()
        self.search_field = S.FormField("", "Search items...")
        row.addWidget(self.search_field, 1)
        btn = S.primary_btn("Search", self._do_search)
        row.addWidget(btn)
        self.search_field.returnPressed.connect(self._do_search)
        self.body.addLayout(row)

    def _do_search(self):
        self._render_grid(self.search_field.text())

    def _load(self):
        self._all_items = DB.get_all_items()
        self._render_grid("")

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _render_grid(self, query=""):
        self._clear_grid()
        items = self._all_items
        if query:
            q = query.lower()
            items = [i for i in items if
                     q in (i.get("title", "") or "").lower() or
                     q in (i.get("category", "") or "").lower() or
                     q in (i.get("location", "") or "").lower()]

        items = [i for i in items
                 if i.get("status", "available") == "available"
                 and i.get("user_id") != self.user["id"]]

        if not items:
            lbl = S.body_label(
                "No items found." if query else "No items available yet.",
                color=S.TEXT_MUTED)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(lbl, 0, 0, 1, COLS)
            return

        for idx, item in enumerate(items):
            r, c = divmod(idx, COLS)
            self.grid_layout.addWidget(self._render_card(item), r, c)
        for c in range(COLS):
            self.grid_layout.setColumnStretch(c, 1)

    def _render_card(self, item: dict) -> QFrame:
        cat = item.get("category", "Other")
        cbg, cfg = S.CATEGORY_COLORS.get(cat, (S.PRIMARY_LIGHT, S.PRIMARY))

        card = S.make_card()
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        img = QLabel()
        img.setFixedHeight(120)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_path = item.get("image_path", "")
        pix = QPixmap(img_path) if img_path and os.path.exists(img_path) else QPixmap()
        if not pix.isNull():
            img.setPixmap(pix.scaled(
                300, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation))
            img.setStyleSheet(
                f"background:{S.BG_CARD}; border-top-left-radius:10px;"
                f" border-top-right-radius:10px;")
        else:
            img.setText(cat[:3].upper())
            img.setStyleSheet(
                f"background:{cbg}; color:{cfg}; font-weight:700; font-size:13px;"
                f" border-top-left-radius:10px; border-top-right-radius:10px;")
        v.addWidget(img)

        body = QVBoxLayout()
        body.setContentsMargins(14, 10, 14, 14)
        body.setSpacing(4)
        title = S.body_label(item.get("title", "")[:32], size=13, bold=True)
        title.setWordWrap(True)
        body.addWidget(title)

        meta = QHBoxLayout()
        meta.addWidget(S.colored_text(cat, cfg))
        meta.addWidget(S.body_label(" • ", size=11, color=S.TEXT_MUTED))
        meta.addWidget(S.body_label(item.get("condition", ""), size=11, color=S.TEXT_MUTED))
        meta.addStretch(1)
        body.addLayout(meta)

        loc = item.get("location", "")
        if loc:
            body.addWidget(S.body_label(loc, size=11, color=S.TEXT_MUTED))

        view_btn = S.primary_btn("View Details", lambda checked=False, i=item: self._view_item(i))
        body.addWidget(view_btn)

        bw = QWidget()
        bw.setLayout(body)
        v.addWidget(bw)
        return card

    def _view_item(self, item: dict):
        from item_details import open_item_details_dialog
        open_item_details_dialog(
            self, item,
            show_request_button=True,
            on_request=self._request_exchange)

    def _request_exchange(self, item: dict, parent_dlg):
        my_items = DB.get_user_items(self.user["id"])
        available_mine = [i for i in my_items
                           if i.get("status", "available") == "available"]
        if not available_mine:
            QMessageBox.information(
                self, "No Items to Offer",
                "You need to post at least one available item before "
                "requesting an exchange.")
            return

        pick = QDialog(self)
        pick.setWindowTitle("Select Item to Offer")
        pick.resize(420, 320)
        pick.setObjectName("dlgRoot")
        pick.setStyleSheet(f"QDialog#dlgRoot{{background:{S.BG_PAGE};}}")
        v = QVBoxLayout(pick)
        v.addWidget(S.body_label("Which item do you want to offer?", size=13, bold=True))

        group = QButtonGroup(pick)
        radios = []
        for mi in available_mine:
            rb = QRadioButton(mi.get("title", ""))
            group.addButton(rb)
            radios.append((rb, mi["id"]))
            v.addWidget(rb)
        if radios:
            radios[0][0].setChecked(True)

        v.addStretch(1)

        def _confirm():
            offered_id = None
            for rb, iid in radios:
                if rb.isChecked():
                    offered_id = iid
                    break
            owner_id = item.get("user_id")
            if not owner_id:
                QMessageBox.critical(self, "Error", "Cannot determine item owner.")
                return
            ok, msg = DB.request_exchange(
                requester_id=self.user["id"], owner_id=owner_id,
                offered_item_id=offered_id, requested_item_id=item["id"])
            pick.close()
            parent_dlg.close()
            if ok:
                QMessageBox.information(self, "Exchange Requested",
                                         "Your exchange request has been sent!")
                self._load()
            else:
                QMessageBox.critical(self, "Error", msg)

        v.addWidget(S.primary_btn("Send Request", _confirm))
        v.addWidget(S.ghost_btn("Cancel", pick.close))
        pick.exec()
