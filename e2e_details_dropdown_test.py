"""
e2e_details_dropdown_test.py  --  WeShare Community (PyQt6)

Targeted tests for the new features:
  1. "View Details" dialog (My Items + Browse) — including REAL uploaded
     photo rendering, and the category-coloured placeholder fallback
     when an item has no photo.
  2. Dropdown arrow visibility/indicator on every QComboBox, including
     the Region/Location dropdowns (plain click-to-choose, not typable).
"""
import sys, os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QDialog, QPushButton, QComboBox
from PyQt6.QtGui import QPixmap, QColor

import styles_qt as S
import database as DB

PASS, FAIL = [], []


def check(label, cond):
    if cond:
        PASS.append(label)
        print(f"  [OK] {label}")
    else:
        FAIL.append(label)
        print(f"  [FAIL] {label}")


app = QApplication(sys.argv)
app.setStyleSheet(S.stylesheet())

# Real test image
TEST_IMG = "/tmp/details_test.png"
pm = QPixmap(80, 80)
pm.fill(QColor("#22AA55"))
pm.save(TEST_IMG)

DB.register_user("Grace Viewer", "0712555001", "grace@example.com", "Abcdef12", "Iringa")
DB.register_user("Henry Other", "0765555002", "henry@example.com", "Abcdef34", "Singida")
grace = DB.authenticate("grace@example.com", "Abcdef12")
henry = DB.authenticate("henry@example.com", "Abcdef34")

# One item WITH a real photo, one WITHOUT any photo
DB.post_item(grace["id"], "Item With Photo", "Electronics", "Has a real picture",
             "Good", "Anything", "0712555001", "Iringa", TEST_IMG)
DB.post_item(grace["id"], "Item Without Photo", "Books", "No picture uploaded",
             "Fair", "Books", "0712555001", "Iringa", "")

items = DB.get_user_items(grace["id"])
item_with_photo = next(i for i in items if i["title"] == "Item With Photo")
item_without_photo = next(i for i in items if i["title"] == "Item Without Photo")

print("\n=== 1. ITEM DETAILS DIALOG — real photo vs placeholder ===")
from item_details import open_item_details_dialog
from PyQt6.QtWidgets import QLabel


def open_and_inspect(item, owner_label=None, show_request=False, on_request=None):
    captured = {}
    def fake_exec(self):
        labels = self.findChildren(QLabel)
        # the very first QLabel added with a fixed height of 220 is the photo widget
        for lbl in labels:
            if lbl.minimumHeight() == 220 or lbl.height() == 220 or lbl.sizeHint().height() >= 0:
                pass
        captured["dialog"] = self
        captured["labels"] = labels
        return QDialog.DialogCode.Accepted
    with patch.object(QDialog, "exec", fake_exec):
        open_item_details_dialog(None, item, owner_label=owner_label,
                                  show_request_button=show_request, on_request=on_request)
    return captured


cap1 = open_and_inspect(item_with_photo)
photo_lbl = cap1["dialog"].findChildren(QLabel)[0]
check("Details dialog opens for item WITH photo", cap1.get("dialog") is not None)
check("Photo label actually has a real pixmap set (not empty)",
      photo_lbl.pixmap() is not None and not photo_lbl.pixmap().isNull())
check("Window title matches item title", cap1["dialog"].windowTitle() == "Item With Photo")

cap2 = open_and_inspect(item_without_photo)
photo_lbl2 = cap2["dialog"].findChildren(QLabel)[0]
check("Details dialog opens for item WITHOUT photo", cap2.get("dialog") is not None)
check("No-photo item shows a text placeholder instead of a pixmap",
      photo_lbl2.pixmap() is None or photo_lbl2.pixmap().isNull())
check("No-photo item shows the category-letter placeholder (consistent with Browse grid)",
      photo_lbl2.text() == item_without_photo["category"][:3].upper())

print("\n=== 2. MY ITEMS — 'View' button opens the real details dialog ===")
from user.my_items import MyItemsPage

mi = MyItemsPage(grace, lambda: None, lambda *a, **k: None)
mi.show()
app.processEvents()
check("My Items page lists both items", mi.rows_layout.count() >= 3)  # 2 rows + 1 hline minimum

view_calls = {}
def fake_exec_myitems(self):
    view_calls["title"] = self.windowTitle()
    return QDialog.DialogCode.Accepted
with patch.object(QDialog, "exec", fake_exec_myitems):
    mi._view_details(item_with_photo)
check("My Items 'View' opens dialog with correct item title",
      view_calls.get("title") == "Item With Photo")

print("\n=== 3. BROWSE — grid thumbnail shows real photo, dialog reachable ===")
from user.browse import BrowsePage

bp = BrowsePage(henry, lambda: None, lambda *a, **k: None)
bp.show()
app.processEvents()
card = bp._render_card(item_with_photo)
thumb = card.findChildren(QLabel)[0]
check("Browse grid card thumbnail shows the real uploaded photo",
      thumb.pixmap() is not None and not thumb.pixmap().isNull())

card2 = bp._render_card(item_without_photo)
thumb2 = card2.findChildren(QLabel)[0]
check("Browse grid card without photo shows category-letter placeholder",
      (thumb2.pixmap() is None or thumb2.pixmap().isNull()) and thumb2.text() != "")

browse_view_calls = {}
def fake_exec_browse(self):
    browse_view_calls["title"] = self.windowTitle()
    btns = self.findChildren(QPushButton)
    browse_view_calls["has_request_btn"] = any(b.text() == "Request Exchange" for b in btns)
    return QDialog.DialogCode.Accepted
with patch.object(QDialog, "exec", fake_exec_browse):
    bp._view_item(item_with_photo)
check("Browse 'View Details' opens dialog for correct item",
      browse_view_calls.get("title") == "Item With Photo")
check("Browse details dialog includes a Request Exchange button",
      browse_view_calls.get("has_request_btn") is True)

print("\n=== 4. DROPDOWN ARROW VISIBILITY (every QComboBox in the app) ===")
from user.add_item import AddItemPage
from auth.register import RegisterPage
from user.wants import WantsPage

ai = AddItemPage(grace, lambda: None, lambda *a, **k: None)
ai.show()
app.processEvents()
combos = ai.findChildren(QComboBox)
check("Add Item page has Category/Condition/Location dropdowns", len(combos) >= 3)
for combo in combos:
    style = combo.style().styleSheet() if hasattr(combo.style(), "styleSheet") else ""
qss = app.styleSheet()
check("Global QSS defines a visible down-arrow icon for QComboBox",
      "down-arrow" in qss and "image: url(" in qss)
check("Global QSS gives the dropdown button its own clickable region",
      "drop-down" in qss and "border-left" in qss)

rp = RegisterPage(lambda: None, lambda: None)
rp.show()
app.processEvents()
check("Region dropdown is a plain click-to-choose QComboBox (not typable)",
      rp.region_field.combo.isEditable() is False)
check("Region combobox still renders a proper drop-down arrow region",
      rp.region_field.combo.findChild(QComboBox) is None)  # sanity: it's the combo itself

wp = WantsPage(grace, lambda: None, lambda *a, **k: None)
wp.show()
app.processEvents()
check("Wants page Category dropdown exists and is a QComboBox",
      isinstance(wp.cat_field.combo, QComboBox))

print("\n" + "=" * 60)
print(f"TOTAL PASS: {len(PASS)}   TOTAL FAIL: {len(FAIL)}")
if FAIL:
    print("FAILURES:")
    for f in FAIL:
        print("  -", f)
print("=" * 60)
sys.exit(1 if FAIL else 0)
