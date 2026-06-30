"""
e2e_warnings_test.py  --  WeShare Community (PyQt6)

Targeted test suite for every EDIT / DELETE action and every
confirmation ("are you sure?") warning dialog in the app.

For each destructive action we test BOTH paths:
  - clicking "No"  -> action is cancelled, nothing changes
  - clicking "Yes" -> action proceeds, data actually changes in the DB

QMessageBox is patched at the class level so every page's call to
QMessageBox.question(...) / .information(...) / .warning(...) /
.critical(...) is intercepted without showing a real modal (so the
test can run headless / unattended), while the real page code path
(including the actual confirmation text shown to the user) still runs.
"""
import sys, os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMessageBox, QFileDialog, QDialog, QRadioButton,
    QButtonGroup, QPushButton, QWidget
)
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

# ── Fresh real data ───────────────────────────────────────────────────────
DB.register_user("Carol Edits", "0712345001", "carol@example.com", "Abcdef12", "Arusha")
DB.register_user("Dan Deletes", "0765345002", "dan@example.com", "Abcdef34", "Mbeya")
carol = DB.authenticate("carol@example.com", "Abcdef12")
dan = DB.authenticate("dan@example.com", "Abcdef34")
admin = DB.authenticate("admin@weshare.app", "admin123")

DB.post_item(carol["id"], "Old Radio", "Electronics", "Works fine", "Good",
             "Anything useful", "0712345001", "Arusha", "")
DB.post_item(dan["id"], "Office Chair", "Furniture", "Sturdy", "Fair",
             "A lamp", "0765345002", "Mbeya", "")
carol_item = DB.get_user_items(carol["id"])[0]
dan_item = DB.get_user_items(dan["id"])[0]

print("\n=== EDIT — My Items status-change dialog (real UI) ===")
from user.my_items import MyItemsPage

mi = MyItemsPage(carol, lambda: None, lambda *a, **k: None)
mi.show()
app.processEvents()
def open_edit_dialog_and_select(page, item, target_status):
    captured = {}
    orig_exec = QDialog.exec
    def fake_exec(self):
        # find the radio buttons added to this dialog and check the target one
        radios = self.findChildren(QRadioButton)
        for rb in radios:
            if rb.text().lower() == target_status:
                rb.setChecked(True)
        # find and click the "Save" button (primaryBtn)
        from PyQt6.QtWidgets import QPushButton
        for btn in self.findChildren(QPushButton):
            if btn.text() == "Save":
                btn.click()
        return QDialog.DialogCode.Accepted
    with patch.object(QDialog, "exec", fake_exec):
        page._edit(item)

open_edit_dialog_and_select(mi, carol_item, "pending")
app.processEvents()
check("Edit dialog: status really changed to 'pending' in DB",
      DB.get_user_items(carol["id"])[0]["status"] == "pending")

open_edit_dialog_and_select(mi, carol_item, "available")
app.processEvents()
check("Edit dialog: status changed back to 'available' in DB",
      DB.get_user_items(carol["id"])[0]["status"] == "available")

print("\n=== DELETE — My Items (warning: No keeps it, Yes deletes it) ===")
with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q:
    mi._delete(carol_item)
    call_args = mock_q.call_args
check("Delete-item warning dialog was actually shown", mock_q.called)
check("Delete-item warning mentions the item title", carol_item["title"] in str(call_args))
check("Clicking 'No' keeps the item in the DB",
      any(i["id"] == carol_item["id"] for i in DB.get_user_items(carol["id"])))

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
    mi._delete(carol_item)
check("Clicking 'Yes' actually deletes the item from the DB",
      not any(i["id"] == carol_item["id"] for i in DB.get_user_items(carol["id"])))

print("\n=== DELETE — Wants (warning: No keeps it, Yes removes it) ===")
from user.wants import WantsPage

DB.add_want(dan["id"], "Need a desk lamp", "Furniture", "")
want = DB.get_wants(dan["id"])[0]
wp = WantsPage(dan, lambda: None, lambda *a, **k: None)
wp.show()
app.processEvents()

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q:
    wp._delete(want["id"])
check("Delete-want warning dialog was shown", mock_q.called)
check("Clicking 'No' keeps the want", any(w["id"] == want["id"] for w in DB.get_wants(dan["id"])))

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
    wp._delete(want["id"])
check("Clicking 'Yes' removes the want", not any(w["id"] == want["id"] for w in DB.get_wants(dan["id"])))

print("\n=== ADMIN — Suspend / Delete user (with warnings) ===")
from admin.manage_users import ManageUsersPage

mup = ManageUsersPage(admin, lambda: None, lambda *a, **k: None)
mup.show()
app.processEvents()

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q:
    mup._suspend(dan)
check("Suspend warning dialog shown", mock_q.called)
check("Clicking 'No' keeps user active", DB.get_user(dan["id"])["status"] == "active")

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
    mup._suspend(dan)
check("Clicking 'Yes' suspends the user", DB.get_user(dan["id"])["status"] == "suspended")

mup._activate(dan)  # reactivate has no warning (non-destructive) — should just work
check("Activate (no warning needed) restores active status",
      DB.get_user(dan["id"])["status"] == "active")

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q:
    mup._delete(dan)
check("Delete-user warning dialog shown", mock_q.called)
check("Clicking 'No' keeps the user in DB", DB.get_user(dan["id"]) is not None)

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
    mup._delete(dan)
check("Clicking 'Yes' deletes the user from DB", DB.get_user(dan["id"]) is None)

print("\n=== SETTINGS — Delete My Account (with warning) ===")
from user.settings import SettingsPage

DB.register_user("Erica Self", "0712999000", "erica@example.com", "Abcdef12", "Tanga")
erica = DB.authenticate("erica@example.com", "Abcdef12")
logout_called = {"flag": False}
sp = SettingsPage(erica, lambda: logout_called.update(flag=True), lambda *a, **k: None,
                   on_update=lambda uid: None)
sp.show()
app.processEvents()

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q:
    sp._delete_account()
check("Delete-account warning dialog shown", mock_q.called)
check("Clicking 'No' keeps account, no logout triggered",
      DB.get_user(erica["id"]) is not None and logout_called["flag"] is False)

with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes), \
     patch.object(QMessageBox, "information", return_value=None) as mock_info:
    sp._delete_account()
check("Clicking 'Yes' actually deletes the account", DB.get_user(erica["id"]) is None)
check("A confirmation info dialog is shown after deletion", mock_info.called)
check("on_logout() is triggered after account deletion", logout_called["flag"] is True)

print("\n=== SIDEBAR — Sign Out warning (common.confirm_logout) ===")
from common import confirm_logout

logout_flag = {"v": False}
parent = QWidget()
with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.No):
    confirm_logout(parent, lambda: logout_flag.update(v=True))
check("Sign-out 'No' does not log out", logout_flag["v"] is False)

with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes):
    confirm_logout(parent, lambda: logout_flag.update(v=True))
check("Sign-out 'Yes' logs out", logout_flag["v"] is True)

print("\n=== BROWSE — Exchange request warnings/info dialogs ===")
from user.browse import BrowsePage

DB.register_user("Frank NoItems", "0712888777", "frank@example.com", "Abcdef12", "Geita")
frank = DB.authenticate("frank@example.com", "Abcdef12")
bp = BrowsePage(frank, lambda: None, lambda *a, **k: None)
bp.show()
app.processEvents()
bp._all_items = DB.get_all_items()
target_item = DB.get_user_items(carol["id"])
if not target_item:
    DB.post_item(carol["id"], "Spare Radio", "Electronics", "", "Good", "anything",
                  "0712345001", "Arusha", "")
    target_item = DB.get_user_items(carol["id"])
target_item = target_item[0]

with patch.object(QMessageBox, "information", return_value=None) as mock_info:
    bp._request_exchange(target_item, parent)
check("'No items to offer' info dialog shown for user with nothing to offer", mock_info.called)

# Now give Frank an item and complete a real request through the picker dialog
DB.post_item(frank["id"], "Spare Charger", "Electronics", "", "Good", "anything",
              "0712888777", "Geita", "")
frank_item = DB.get_user_items(frank["id"])[0]

def drive_pick_dialog():
    orig_exec = QDialog.exec
    def fake_exec(self):
        for rb in self.findChildren(QRadioButton):
            rb.setChecked(True)
        for btn in self.findChildren(QPushButton):
            if btn.text() == "Send Request":
                btn.click()
        return QDialog.DialogCode.Accepted
    with patch.object(QDialog, "exec", fake_exec), \
         patch.object(QMessageBox, "information", return_value=None) as mock_info2:
        bp._request_exchange(target_item, parent)
    return mock_info2

mock_info2 = drive_pick_dialog()
exchanges_now = DB.get_exchange_history(frank["id"], "all")
check("Real exchange request created via picker dialog", len(exchanges_now) >= 1)
check("Success info dialog shown after sending request", mock_info2.called)

print("\n=== ADD ITEM — File-too-large warning ===")
from user.add_item import AddItemPage

ai = AddItemPage(carol, lambda: None, lambda *a, **k: None)
ai.show()
app.processEvents()
big_file = "/tmp/bigfile_test.png"
with open(big_file, "wb") as f:
    f.write(b"0" * (6 * 1024 * 1024))  # 6MB, over the 5MB cap

with patch.object(QFileDialog, "getOpenFileName", return_value=(big_file, "")), \
     patch.object(QMessageBox, "warning", return_value=None) as mock_warn:
    ai._pick_image()
check("Oversized image triggers a 'File Too Large' warning", mock_warn.called)
check("Oversized image is NOT accepted as the item image", ai._image_path == "")
os.remove(big_file)

print("\n" + "=" * 60)
print(f"TOTAL PASS: {len(PASS)}   TOTAL FAIL: {len(FAIL)}")
if FAIL:
    print("FAILURES:")
    for f in FAIL:
        print("  -", f)
print("=" * 60)
sys.exit(1 if FAIL else 0)
