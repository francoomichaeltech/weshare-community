"""
user/messages.py  --  WeShare Community (PyQt6 edition)
Two-panel messenger: conversation list (left) + thread (right).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QDialog, QPushButton
)
from PyQt6.QtCore import Qt, QTimer

import styles_qt as S
import database as DB
from common import PageScaffold, confirm_logout

NAV = S.USER_NAV


class ConvRow(QFrame):
    clicked_partner = None

    def __init__(self, partner, active, on_click):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        bg = S.BG_HOVER if active else S.BG_CARD
        self.setStyleSheet(f"background:{bg};")
        h = QHBoxLayout(self)
        h.setContentsMargins(12, 10, 12, 10)

        name = partner.get("full_name", partner.get("name", "Unknown"))
        av = QLabel(name[:2].upper())
        av.setFixedSize(36, 36)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(
            f"background:{S.PRIMARY_DARK}; color:white; border-radius:18px; font-weight:700;")
        h.addWidget(av)

        info = QVBoxLayout()
        info.setSpacing(2)
        nrow = QHBoxLayout()
        nrow.addWidget(S.body_label(name, size=11, bold=True))
        unread = partner.get("unread", 0)
        if unread:
            badge = QLabel(str(unread))
            badge.setStyleSheet(
                f"background:{S.PRIMARY}; color:white; border-radius:8px;"
                f" padding:1px 6px; font-size:10px; font-weight:700;")
            nrow.addWidget(badge)
        nrow.addStretch(1)
        info.addLayout(nrow)

        last_txt = (partner.get("last_message", {}) or {}).get("content", "")
        if len(last_txt) > 34:
            last_txt = last_txt[:32] + "..."
        if last_txt:
            info.addWidget(S.body_label(last_txt, size=10, color=S.TEXT_MUTED))

        iw = QWidget(); iw.setLayout(info)
        h.addWidget(iw, 1)

        self.mousePressEvent = lambda e: on_click(partner["id"])


class MessagesPage(PageScaffold):

    def __init__(self, user, on_logout, on_navigate, partner_id=None):
        super().__init__(NAV, "messages", user, on_logout, on_navigate,
                          "Messages", "Your conversations", scrollable=False)
        self._partner_id = partner_id
        self._partner = None

        new_btn = S.primary_btn("New Message", self._new_message_dialog)
        self.header.add_widget(new_btn)

        row = QHBoxLayout()
        row.setSpacing(0)

        # Left panel
        left = S.make_card()
        left.setFixedWidth(260)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(0)
        lv.addWidget(S.body_label("Conversations", size=11, bold=True,
                                   color=S.TEXT_MUTED), 0)
        lv.itemAt(0).widget().setContentsMargins(14, 10, 14, 10)
        lv.addWidget(S.hline())

        self.conv_scroll = QScrollArea()
        self.conv_scroll.setWidgetResizable(True)
        self.conv_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.conv_scroll.setObjectName("convScroll")
        self.conv_scroll.setStyleSheet(
            f"QScrollArea#convScroll{{background:{S.BG_CARD}; border:none;}}")
        self.conv_holder = QWidget()
        self.conv_holder.setObjectName("convHolder")
        self.conv_holder.setStyleSheet(
            f"QWidget#convHolder{{background:{S.BG_CARD};}}")
        self.conv_layout = QVBoxLayout(self.conv_holder)
        self.conv_layout.setContentsMargins(0, 0, 0, 0)
        self.conv_layout.setSpacing(0)
        self.conv_layout.addStretch(1)
        self.conv_scroll.setWidget(self.conv_holder)
        lv.addWidget(self.conv_scroll, 1)
        row.addWidget(left)

        # Right panel (thread)
        self.thread_panel = QVBoxLayout()
        self.thread_panel.setContentsMargins(16, 0, 0, 0)
        tw = QWidget(); tw.setLayout(self.thread_panel)
        row.addWidget(tw, 1)

        self.body.addLayout(row)

        self._load_conversations()
        if partner_id:
            self._open_thread(partner_id)
        else:
            self._show_placeholder()

    # ── Conversation list ────────────────────────────────────────────────────

    def _load_conversations(self):
        while self.conv_layout.count():
            it = self.conv_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        convs = DB.get_conversations(self.user["id"])
        if not convs:
            empty = S.body_label("No messages yet.", size=11, color=S.TEXT_MUTED)
            empty.setContentsMargins(14, 12, 14, 12)
            self.conv_layout.addWidget(empty)
            self.conv_layout.addStretch(1)
            return

        for partner in convs:
            active = partner["id"] == self._partner_id
            row = ConvRow(partner, active, self._open_thread)
            self.conv_layout.addWidget(row)
            self.conv_layout.addWidget(S.hline())
        self.conv_layout.addStretch(1)

    # ── Thread panel ─────────────────────────────────────────────────────────

    def _clear_thread(self):
        while self.thread_panel.count():
            it = self.thread_panel.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

    def _show_placeholder(self):
        self._clear_thread()
        lbl = S.body_label("Select a conversation to start messaging.",
                            color=S.TEXT_MUTED)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thread_panel.addStretch(1)
        self.thread_panel.addWidget(lbl)
        self.thread_panel.addStretch(1)

    def _open_thread(self, partner_id: int):
        self._partner_id = partner_id
        self._partner = DB.get_user(partner_id)
        self._load_conversations()
        self._build_thread()

    def _build_thread(self):
        self._clear_thread()
        if not self._partner:
            self._show_placeholder()
            return

        pname = self._partner.get("full_name", self._partner.get("name", "User"))

        thdr = S.make_card()
        th = QHBoxLayout(thdr)
        th.setContentsMargins(16, 10, 16, 10)
        th.addWidget(S.body_label(pname, size=13, bold=True))
        loc = self._partner.get("location", "")
        if loc:
            th.addWidget(S.body_label(f"  {loc}", size=11, color=S.TEXT_MUTED))
        th.addStretch(1)
        self.thread_panel.addWidget(thdr)

        self.msg_scroll = QScrollArea()
        self.msg_scroll.setWidgetResizable(True)
        self.msg_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.msg_scroll.setObjectName("msgScroll")
        self.msg_scroll.setStyleSheet(
            f"QScrollArea#msgScroll{{background:{S.BG_PAGE}; border:none;}}")
        self.msg_holder = QWidget()
        self.msg_holder.setObjectName("msgHolder")
        self.msg_holder.setStyleSheet(
            f"QWidget#msgHolder{{background:{S.BG_PAGE};}}")
        self.msg_layout = QVBoxLayout(self.msg_holder)
        self.msg_layout.setContentsMargins(16, 12, 16, 12)
        self.msg_layout.setSpacing(6)
        self.msg_scroll.setWidget(self.msg_holder)
        self.thread_panel.addWidget(self.msg_scroll, 1)

        self._refresh_messages()

        input_bar = S.make_card()
        ib = QHBoxLayout(input_bar)
        ib.setContentsMargins(14, 10, 14, 10)
        self.msg_field = S.FormField("", "Type a message...")
        ib.addWidget(self.msg_field, 1)
        send_btn = S.primary_btn("Send", self._send)
        ib.addWidget(send_btn)
        self.msg_field.returnPressed.connect(self._send)
        self.thread_panel.addWidget(input_bar)

    def _refresh_messages(self):
        while self.msg_layout.count():
            it = self.msg_layout.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()

        msgs = DB.get_thread(self.user["id"], self._partner_id)
        if not msgs:
            lbl = S.body_label("No messages yet. Say hello!", color=S.TEXT_MUTED)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.msg_layout.addWidget(lbl)
            self.msg_layout.addStretch(1)
            return

        for msg in msgs:
            is_mine = msg["sender_id"] == self.user["id"]
            self.msg_layout.addWidget(self._bubble(msg, is_mine))
        self.msg_layout.addStretch(1)
        QTimer.singleShot(50, lambda: self.msg_scroll.verticalScrollBar().setValue(
            self.msg_scroll.verticalScrollBar().maximum()))

    def _bubble(self, msg, is_mine):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 2, 0, 2)

        bubble = QFrame()
        bg = S.PRIMARY if is_mine else S.BG_CARD
        fg = "white" if is_mine else S.TEXT_DARK
        border = S.PRIMARY if is_mine else S.BORDER
        bubble.setStyleSheet(
            f"background:{bg}; border:1px solid {border}; border-radius:10px;")
        bubble.setMaximumWidth(420)
        bv = QVBoxLayout(bubble)
        bv.setContentsMargins(12, 8, 12, 8)
        bv.setSpacing(2)
        content_lbl = QLabel(msg.get("content", ""))
        content_lbl.setWordWrap(True)
        content_lbl.setStyleSheet(f"color:{fg}; background:transparent; font-size:12px;")
        bv.addWidget(content_lbl)
        time_lbl = QLabel(str(msg.get("created_at", ""))[11:16])
        time_lbl.setStyleSheet(
            f"color:{'#A8C8EC' if is_mine else S.TEXT_MUTED}; background:transparent;"
            f" font-size:10px;")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        bv.addWidget(time_lbl)

        if is_mine:
            h.addStretch(1)
            h.addWidget(bubble)
        else:
            h.addWidget(bubble)
            h.addStretch(1)
        return row

    def _send(self):
        body = self.msg_field.raw_text().strip()
        if not body:
            return
        DB.send_message(self.user["id"], self._partner_id, body)
        self.msg_field.set_text("")
        self._refresh_messages()

    # ── New message dialog ───────────────────────────────────────────────────

    def _new_message_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("New Message")
        dlg.resize(420, 220)
        dlg.setObjectName("dlgRoot")
        dlg.setStyleSheet(f"QDialog#dlgRoot{{background:{S.BG_PAGE};}}")
        v = QVBoxLayout(dlg)
        v.addWidget(S.h_label("Search user by name or email", size=14, weight=700))

        field = S.FormField("Name or Email", required=True)
        v.addWidget(field)

        def _go():
            term = field.text()
            if not term:
                field.show_error("Please enter a name or email.")
                return
            users = DB.search_users(term)
            users = [u for u in users if u["id"] != self.user["id"]]
            if not users:
                field.show_error("No user found.")
                return
            dlg.close()
            self._open_thread(users[0]["id"])

        v.addWidget(S.primary_btn("Start Conversation", _go))
        field.returnPressed.connect(_go)
        dlg.exec()
