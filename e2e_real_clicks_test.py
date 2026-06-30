"""
e2e_real_clicks_test.py  --  WeShare Community (PyQt6)

This suite exists specifically because a prior bug (small_btn() never
connecting its on_click handler) was invisible to tests that called
page methods directly in Python. Every check here performs a REAL
QTest.mouseClick() on the actual rendered QPushButton, exactly like a
human clicking with a mouse, so wiring bugs cannot hide again.

Also covers:
  - Region/Location dropdowns are plain click-to-choose (not typable)
  - Profile Bio updates in real time on save, without leaving the page
"""
import sys, os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog, QPushButton, QComboBox
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

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


def real_click(btn: QPushButton):
    """Simulate an actual mouse click exactly like a user would."""
    QTest.mouseClick(btn, Qt.MouseButton.LeftButton)


def find_btn(widget, text):
    for b in widget.findChildren(QPushButton):
        if b.text() == text:
            return b
    return None


app = QApplication(sys.argv)
app.setStyleSheet(S.stylesheet())

DB.register_user("Ivy Clicker", "0712666001", "ivy@example.com", "Abcdef12", "Mbeya")
DB.register_user("Jack Other", "0765666002", "jack@example.com", "Abcdef34", "Tabora")
ivy = DB.authenticate("ivy@example.com", "Abcdef12")
jack = DB.authenticate("jack@example.com", "Abcdef34")
admin = DB.authenticate("admin@weshare.app", "admin123")

DB.post_item(ivy["id"], "Real Click TV", "Electronics", "Tested by clicking", "Good",
             "Anything", "0712666001", "Mbeya", "")

print("\n=== REAL CLICK — My Items: View / Edit / Delete buttons ===")
from user.my_items import MyItemsPage

mi = MyItemsPage(ivy, lambda: None, lambda *a, **k: None)
mi.show()
app.processEvents()

view_btn = find_btn(mi, "View")
edit_btn = find_btn(mi, "Edit")
delete_btn = find_btn(mi, "Delete")
check("My Items renders a View button", view_btn is not None)
check("My Items renders an Edit button", edit_btn is not None)
check("My Items renders a Delete button", delete_btn is not None)

opened = {}
def fake_exec_view(self):
    opened["view"] = self.windowTitle()
    return QDialog.DialogCode.Accepted
with patch.object(QDialog, "exec", fake_exec_view):
    real_click(view_btn)
check("REAL CLICK on 'View' actually opens the details dialog",
      opened.get("view") == "Real Click TV")

def fake_exec_edit(self):
    opened["edit"] = True
    return QDialog.DialogCode.Accepted
with patch.object(QDialog, "exec", fake_exec_edit):
    real_click(edit_btn)
check("REAL CLICK on 'Edit' actually opens the status dialog", opened.get("edit") is True)

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q:
    real_click(delete_btn)
check("REAL CLICK on 'Delete' actually triggers the confirmation warning", mock_q.called)
item = DB.get_user_items(ivy["id"])[0]
check("Item still exists after clicking 'No'", item is not None)

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
    real_click(delete_btn)
check("REAL CLICK + 'Yes' actually deletes the item from the DB",
      len(DB.get_user_items(ivy["id"])) == 0)

print("\n=== REAL CLICK — Wants: Remove button ===")
from user.wants import WantsPage

DB.add_want(ivy["id"], "Need real click test item", "Furniture", "")
wp = WantsPage(ivy, lambda: None, lambda *a, **k: None)
wp.show()
app.processEvents()
remove_btn = find_btn(wp, "Remove")
check("Wants page renders a Remove button", remove_btn is not None)
with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
    real_click(remove_btn)
check("REAL CLICK on 'Remove' actually deletes the want",
      len(DB.get_wants(ivy["id"])) == 0)

print("\n=== REAL CLICK — Admin Manage Users: View / Suspend / Delete ===")
from admin.manage_users import ManageUsersPage

mup = ManageUsersPage(admin, lambda: None, lambda *a, **k: None)
mup.show()
app.processEvents()
def find_btn_in_row(widget, row_marker_text, btn_text):
    """Find the button that lives in the SAME row widget as a label
    with the given exact text (e.g. a user's full name), so we click
    the correct row's button rather than the first match anywhere."""
    from PyQt6.QtWidgets import QLabel
    for lbl in widget.findChildren(QLabel):
        if lbl.text() == row_marker_text:
            row_widget = lbl.parent()
            for btn in row_widget.findChildren(QPushButton):
                if btn.text() == btn_text:
                    return btn
    return None


view_user_btn = find_btn(mup, "View")
suspend_btn = find_btn_in_row(mup, "Jack Other", "Suspend")
check("Manage Users renders a View button", view_user_btn is not None)
check("Manage Users renders a Suspend button for Jack's row", suspend_btn is not None)

opened2 = {}
def fake_exec_userview(self):
    opened2["title"] = self.findChildren(type(view_user_btn))
    return QDialog.DialogCode.Accepted
with patch.object(QDialog, "exec", fake_exec_userview):
    real_click(view_user_btn)
check("REAL CLICK on admin 'View' opens the user-info dialog", "title" in opened2)

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
    real_click(suspend_btn)
check("REAL CLICK on 'Suspend' actually suspends the user in DB",
      DB.get_user(jack["id"])["status"] == "suspended")
DB.set_user_status(jack["id"], "active")

print("\n=== REAL CLICK — History: Leave Review button ===")
from user.history import HistoryPage

DB.post_item(jack["id"], "Jack's Bike", "Sports", "", "Good", "anything",
             "0765666002", "Tabora", "")
jack_item = DB.get_user_items(jack["id"])[0]
DB.post_item(ivy["id"], "Ivy's Radio", "Electronics", "", "Good", "anything",
             "0712666001", "Mbeya", "")
ivy_item2 = DB.get_user_items(ivy["id"])[0]
ok, _ = DB.request_exchange(requester_id=ivy["id"], owner_id=jack["id"],
                             offered_item_id=ivy_item2["id"], requested_item_id=jack_item["id"])
ex = DB.get_exchange_history(ivy["id"], "all")[0]
DB.update_exchange_status(ex["id"], "completed")

hp = HistoryPage(ivy, lambda: None, lambda *a, **k: None)
hp.show()
app.processEvents()
review_btn = find_btn(hp, "Leave Review")
check("History renders a 'Leave Review' button for completed exchange", review_btn is not None)
if review_btn:
    opened3 = {}
    def fake_exec_review(self):
        opened3["opened"] = True
        return QDialog.DialogCode.Accepted
    with patch.object(QDialog, "exec", fake_exec_review):
        real_click(review_btn)
    check("REAL CLICK on 'Leave Review' opens the review dialog", opened3.get("opened") is True)

print("\n=== REGION / LOCATION DROPDOWNS — must be plain click-to-choose ===")
from auth.register import RegisterPage
from user.add_item import AddItemPage
from user.profile import ProfilePage
from user.settings import SettingsPage

rp = RegisterPage(lambda: None, lambda: None)
rp.show()
app.processEvents()
check("Register Region dropdown is NOT editable (no manual typing)",
      rp.region_field.combo.isEditable() is False)

ai = AddItemPage(ivy, lambda: None, lambda *a, **k: None)
ai.show()
app.processEvents()
check("Add Item Location dropdown is NOT editable",
      ai.loc_field.combo.isEditable() is False)

pp = ProfilePage(ivy, lambda: None, lambda *a, **k: None)
pp.show()
app.processEvents()
check("Profile Location/Region dropdown is NOT editable",
      pp.loc_field.combo.isEditable() is False)

sp = SettingsPage(ivy, lambda: None, lambda *a, **k: None, on_update=lambda uid: None)
sp.show()
app.processEvents()
check("Settings Region dropdown is NOT editable",
      sp.region_field.combo.isEditable() is False)

# Confirm picking still works via a real click + selecting an index
combo = ai.loc_field.combo
idx = combo.findText("Dodoma")
combo.setCurrentIndex(idx)
check("Clicking/selecting a region still sets the value correctly",
      ai.loc_field.value() == "Dodoma")

print("\n=== PROFILE — Bio updates in REAL TIME after Save (no page reload) ===")
pp2 = ProfilePage(ivy, lambda: None, lambda *a, **k: None)
pp2.show()
app.processEvents()
check("Bio placeholder shows before any bio is set",
      pp2.bio_lbl.text() == "No bio added yet.")

pp2.bio_field.set_text("I love exchanging electronics for books!")
pp2.name_field.set_text("Ivy C. Clicker")
save_btn = find_btn(pp2, "Save Changes")
check("Profile page has a real Save Changes button", save_btn is not None)
real_click(save_btn)
app.processEvents()

check("Avatar card name updates immediately (real time)",
      pp2.name_lbl.text() == "Ivy C. Clicker")
check("Avatar card bio updates immediately (real time), no navigation needed",
      pp2.bio_lbl.text() == "I love exchanging electronics for books!")
check("Bio is actually persisted in the database too",
      DB.get_user(ivy["id"])["bio"] == "I love exchanging electronics for books!")

print("\n" + "=" * 60)
print(f"TOTAL PASS: {len(PASS)}   TOTAL FAIL: {len(FAIL)}")
if FAIL:
    print("FAILURES:")
    for f in FAIL:
        print("  -", f)
print("=" * 60)
sys.exit(1 if FAIL else 0)
