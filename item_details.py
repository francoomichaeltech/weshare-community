"""
item_details.py  --  WeShare Community (PyQt6 edition)
Shared "Item Details" dialog: shows the real uploaded photo (or a
category-coloured placeholder if none), plus every stored field —
used by both Browse Items ("View Details") and My Items ("Details").
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QWidget
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

import styles_qt as S


def open_item_details_dialog(parent, item: dict, owner_label: str = None,
                              show_request_button: bool = False,
                              on_request=None):
    """
    Opens a modal dialog with full item details, including the actual
    uploaded photo when available.

    owner_label: text to show for "Posted by" (falls back to item's
                 own 'owner_name' field if not given).
    show_request_button: if True, shows a "Request Exchange" button
                 that calls on_request(item, dialog) when clicked.
    """
    dlg = QDialog(parent)
    dlg.setWindowTitle(item.get("title", "Item Details"))
    dlg.resize(480, 560)
    dlg.setObjectName("dlgRoot")
    dlg.setStyleSheet(f"QDialog#dlgRoot{{background:{S.BG_PAGE};}}")

    outer = QVBoxLayout(dlg)
    outer.setContentsMargins(0, 0, 0, 0)

    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QScrollArea.Shape.NoFrame)
    area.setObjectName("detailsScroll")
    area.setStyleSheet(f"QScrollArea#detailsScroll{{background:{S.BG_PAGE}; border:none;}}")
    outer.addWidget(area, 1)

    body = QWidget()
    body.setObjectName("detailsBody")
    body.setStyleSheet(f"QWidget#detailsBody{{background:{S.BG_PAGE};}}")
    v = QVBoxLayout(body)
    v.setContentsMargins(20, 20, 20, 20)
    v.setSpacing(10)

    # ── Photo (real image if present, else a category-coloured block) ──────
    cat = item.get("category", "Other")
    cbg, cfg = S.CATEGORY_COLORS.get(cat, (S.PRIMARY_LIGHT, S.PRIMARY))
    img_path = item.get("image_path", "")

    photo = QLabel()
    photo.setFixedHeight(220)
    photo.setAlignment(Qt.AlignmentFlag.AlignCenter)

    pix = QPixmap(img_path) if img_path and os.path.exists(img_path) else QPixmap()
    if not pix.isNull():
        scaled = pix.scaled(440, 220, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
        photo.setPixmap(scaled)
        photo.setStyleSheet(f"background:{S.BG_CARD}; border-radius:10px;")
    else:
        photo.setText("No photo provided" if img_path else cat[:3].upper())
        photo.setStyleSheet(
            f"background:{cbg}; color:{cfg}; font-weight:700; font-size:14px;"
            f" border-radius:10px;")
    v.addWidget(photo)

    # ── Title + category/status badges ──────────────────────────────────────
    title_lbl = S.h_label(item.get("title", ""), size=17, weight=700)
    title_lbl.setWordWrap(True)
    v.addWidget(title_lbl)

    badge_row = QHBoxLayout()
    badge_row.addWidget(S.category_pill(cat))
    if item.get("status"):
        badge_row.addWidget(S.status_badge(item.get("status")))
    badge_row.addStretch(1)
    v.addLayout(badge_row)
    v.addWidget(S.hline())

    # ── Key/value fields ──────────────────────────────────────────────────────
    fields = [
        ("Condition", item.get("condition", "")),
        ("Location", item.get("location", "")),
        ("Posted by", owner_label or item.get("owner_name", "")),
        ("Contact phone", item.get("phone", "")),
        ("Wants in exchange", item.get("exchange_for", "")),
        ("Posted on", str(item.get("created_at", ""))[:16]),
    ]
    for label, val in fields:
        if not val:
            continue
        row = QHBoxLayout()
        lbl = S.body_label(f"{label}:", size=12, bold=True)
        lbl.setFixedWidth(150)
        row.addWidget(lbl)
        vlbl = S.body_label(str(val), size=12, color=S.TEXT_MUTED)
        vlbl.setWordWrap(True)
        row.addWidget(vlbl, 1)
        v.addLayout(row)

    desc = (item.get("description", "") or "").strip()
    if desc:
        v.addWidget(S.hline())
        v.addWidget(S.body_label("Description", size=12, bold=True))
        dl = S.body_label(desc, size=12, color=S.TEXT_MUTED)
        dl.setWordWrap(True)
        v.addWidget(dl)

    v.addStretch(1)
    area.setWidget(body)

    # ── Action buttons (fixed footer) ───────────────────────────────────────
    footer = QWidget()
    footer.setObjectName("detailsFooter")
    footer.setStyleSheet(
        f"QWidget#detailsFooter{{background:{S.BG_CARD}; border-top:1px solid {S.BORDER};}}")
    fv = QVBoxLayout(footer)
    fv.setContentsMargins(20, 12, 20, 12)
    fv.setSpacing(8)
    if show_request_button and on_request:
        req_btn = S.primary_btn("Request Exchange",
                                 lambda: on_request(item, dlg))
        fv.addWidget(req_btn)
    close_btn = S.ghost_btn("Close", dlg.close)
    fv.addWidget(close_btn)
    outer.addWidget(footer)

    dlg.exec()
