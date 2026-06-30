# WeShare Community — PyQt6 Edition

WeShare Community is a desktop community-exchange application. Members post
items they own and no longer need, describe what they would like in return,
and arrange direct item-for-item exchanges with other members instead of
buying or selling for cash. The application was rebuilt from an original
Tkinter version into **PyQt6** without altering its underlying logic
(database structure, authentication, business rules); the interface follows
the supplied reference screenshots closely, with a consistent design system
applied across every screen.

The system has two roles: a regular **User**, who posts items, browses,
exchanges, and messages other members, and an **Admin**, who oversees users,
items, exchanges, reports, and platform-wide analytics.

---

## Table of Contents

1. Requirements
2. Installation and Running the App
3. Default Admin Account
4. Project Structure
5. Architecture Overview
6. Database Schema
7. User-Facing Features (full walkthrough)
8. Admin Features (full walkthrough)
9. Shared Design System and Reusable Components
10. Form Validation Behaviour
11. Recent Fixes and Improvements
12. Testing
13. Known Notes and Limitations

---

## 1. Requirements

- Python 3.9 or newer
- PyQt6 (version 6.5.0 or newer)

All dependencies are listed in `requirements.txt`:

```
PyQt6>=6.5.0
```

## 2. Installation and Running the App

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application from the project folder:

```bash
python main.py
```

The SQLite database file (`weshare.db`) is created automatically on first
run if it does not already exist, including all tables and a seeded admin
account.

## 3. Default Admin Account

A default administrator account is seeded automatically the first time the
database is created:

- Email: `admin@weshare.app`
- Password: `admin123`

Use this account to explore every Admin feature described in this document.

## 4. Project Structure

```
main.py              Application entry point and page router (QStackedWidget)
database.py           SQLite data layer: schema, migrations, and all queries
styles_qt.py           Central design system: colors, fonts, global QSS,
                        reusable widgets (buttons, form fields, dropdowns,
                        cards, badges, sidebar/nav definitions)
common.py             Shared page scaffold (sidebar + header + scrollable
                        body) used by every user/admin page
item_details.py        Reusable "item details" modal dialog (used from
                        Browse and from My Items)
requirements.txt       Python dependencies
weshare.db              SQLite database file (auto-created if missing)
README.md              This document

auth/
  login.py             Sign-in screen
  register.py           Account creation screen (full name, phone, email,
                          password, region)

user/
  dashboard.py          User dashboard: stat cards + recent items
  browse.py              Browse/search/filter items from other members,
                          view details, request an exchange
  add_item.py             "Post a New Item" form with image upload/preview
  my_items.py              "My Items" list with View / Edit / Delete actions
                          (Edit opens a full item-edit dialog, see section 11)
  messages.py             Conversation list + thread view, start new
                          conversations, send/reply to messages
  wants.py                 "Wants" list: items a member is looking for
  notifications.py         Notification list, mark as read / mark all as read
  history.py               Exchange history (pending/completed/cancelled)
                          and the entry point for leaving a review
  review.py                 Reviews received/given, overall rating
  profile.py                 Profile view/edit (name, bio, region, avatar
                          initials, real-time UI refresh after save)
  settings.py               Tabbed account settings: account info, change
                          password, notification preferences, danger zone
                          (delete account)

admin/
  dashboard.py           Admin dashboard: stat cards + recent users/exchanges
  manage_users.py          Searchable users table; suspend/reactivate a user
  exchanges.py              All-platform exchanges table with status filter
                          (also serves the "Items" nav entry)
  reports.py                 User reports queue; mark a report resolved
  analytics.py               Items-by-category breakdown and top users by
                          number of items posted
  settings.py               Admin's own account settings and password change

pages/
  about.py, terms.py, privacy.py, safety.py, _static.py
                          Static informational pages shown in a modal
                          dialog from the footer/sidebar (About, Terms of
                          Service, Privacy Policy, Safety Guide)
```

Approximate size: about 5,800 lines of Python across 35 files.

## 5. Architecture Overview

- **Routing**: `main.py` hosts a single `QMainWindow` with a `QStackedWidget`
  that swaps between pages. A `_user_page` factory and an `_admin_page`
  factory build the correct page class for a given navigation key
  (`dashboard`, `browse`, `my_items`, `users`, `reports`, etc.), mirroring
  how the original Tkinter version swapped frames.
- **Page scaffold**: every user/admin screen subclasses `PageScaffold`
  (`common.py`), which renders a fixed sidebar (role-specific navigation
  list from `styles_qt.USER_NAV` / `styles_qt.ADMIN_NAV`), a header, and a
  scrollable content area (`self.body`) that subclasses populate.
- **Design system**: `styles_qt.py` centralizes the color palette, fonts,
  global stylesheet (QSS), and every reusable widget (buttons, labelled
  inputs, dropdowns, status badges, stat cards, cards, etc.), so every page
  shares one consistent look without duplicating styling code.
- **Data layer**: `database.py` is a single-file SQLite wrapper. It owns
  schema creation/migration, password hashing, and every read/write
  operation the rest of the app calls into (no ORM; plain `sqlite3` with
  parameterized queries).
- **Modals**: item details, message composition pop-ups, the item edit
  dialog, and the four informational pages are presented as `QDialog`
  overlays rather than separate routed pages.

## 6. Database Schema

SQLite tables created by `database.py` (`_migrate()`):

**users** — `id, full_name, email (unique), phone, location, bio,
password_hash, role (user/admin), status (active/suspended), created_at`

**items** — `id, user_id, title, category, description, condition,
exchange_for, phone, location, image_path, status (available/unavailable/
pending), created_at`

**exchanges** — `id, requester_id, owner_id, offered_item_id,
requested_item_id, status (pending/completed/cancelled), created_at,
updated_at`

**messages** — `id, sender_id, receiver_id, content, is_read, created_at`

**notifications** — `id, user_id, message, is_read, created_at`

**wants** — `id, user_id, title, category, notes, created_at`

**reviews** — `id, reviewer_id, reviewee_id, exchange_id, rating, comment,
created_at`

**reports** — `id, reporter_id, against_id, reason, status (pending/
resolved), created_at`

All foreign keys use `ON DELETE CASCADE` (or `SET NULL` where appropriate)
so removing a user or item cleans up dependent rows automatically. The
migration step is additive and non-destructive: if an older database file
is missing the `condition` column on `items`, it is added automatically
without touching existing data.

## 7. User-Facing Features (full walkthrough)

### Register
New members sign up with Full Name, Phone Number, Email Address, Password
(with confirmation), and Region (a dropdown of Tanzanian regions). The
region field is a plain click-to-choose dropdown (not free-typed), and its
popup is capped to a fixed number of visible rows so it always appears
attached directly under the field, scrolling internally for the remaining
entries rather than growing past the available screen space.

### Login
Sign in with email or phone plus password. Password fields include a
"Show/Hide" toggle. Suspended accounts are blocked with a clear message.

### Dashboard
Four stat cards: Items Posted, Exchanges Done, Wants Listed, and average
Reviews rating, followed by a list of recently posted items across the
platform.

### Browse Items
Search items by title/description, filter by category, view a grid of
items posted by other members (thumbnail, title, category, condition).
Opening "View Details" shows the full description, owner, contact info,
and a "Request Exchange" action, which opens a picker so the requester can
choose which of their own items to offer in return.

### Add Item (Post a New Item)
Form fields: Item Name, Category, Condition (New / Like New / Good / Fair /
Needs Repair), Description, Exchange For (what the member wants in
return), Contact Phone (pre-filled from the profile, restricted to valid
Tanzanian mobile formats), and Location/Region. An image is required (JPG/
PNG/GIF, max 5 MB) and is shown in a live preview panel before posting.

### My Items
Lists every item the signed-in member has posted, with Category, Condition,
status badge, post date, and three actions:

- **View** — opens the same item-details dialog used in Browse.
- **Edit** — opens a full edit dialog (see section 11) covering every
  field of the post: title, category, condition, description, exchange-for
  text, contact phone, region, the photo, and the availability status — all
  in one dialog, saved together with a single "Save" action.
- **Delete** — removes the item permanently after a confirmation prompt.

### Messages
A conversation list on the left and a thread view on the right. Members can
start a new conversation by searching another user by name or email, and
reply within an existing thread. Unread counts are tracked per message.

### Wants
A separate list (distinct from posted items) of things a member is actively
looking for, with category and free-text notes. Entries can be removed at
any time.

### Notifications
A chronological list of notifications (new exchange requests, replies,
status changes, etc.), each markable as read individually, plus a
"mark all as read" action and an unread badge/count.

### History
Shows the member's exchange history, both pending and completed, filterable
by status. Completed exchanges are the entry point for leaving a review of
the exchange partner.

### Reviews
Shows the overall rating received, the list of individual reviews received,
and reviews the member has written for others. Writing a review records a
1–5 rating plus a comment, tied to a specific completed exchange.

### Profile
Displays the member's avatar (initials), name, bio, region, and basic
stats. Editing the name/bio/region and saving updates the page in real
time (no navigation or reload required) and persists the change to the
database immediately.

### Settings
A tabbed page with:
- **Account** — update name, phone, email, region.
- **Change Password** — enforces a password-strength policy and rejects
  weak passwords.
- **Notification Preferences** — toggles for which notifications the member
  wants to receive.
- **Danger Zone** — permanently delete the account, with a confirmation
  dialog and a follow-up confirmation message before logging the member
  out.

## 8. Admin Features (full walkthrough)

Switching to the Admin role (logging in with an account whose `role` is
`admin`) replaces the sidebar with an admin-specific navigation list and
unlocks the following pages:

### Admin Dashboard
Four stat cards — Total Users, Active Items, Exchanges, and Reports
(pending) — followed by a "Recent Users" list and a "Recent Exchanges"
list, giving a quick platform-health snapshot.

### Manage Users
A searchable table of every user with Name, Email, Region, Role, Status,
and Joined date, plus an Actions column to **Suspend** a user who violates
policy or **Reactivate** a previously suspended one. Suspended users are
blocked from signing in.

### Items / Exchanges
A platform-wide table of exchanges with a status filter (pending,
completed, cancelled), letting the admin audit and monitor every exchange
happening on the platform regardless of which members are involved. This
page also serves the "Items" navigation entry.

### Reports
A queue of reports filed by members against other members or items, with
the reason and current status. The admin can mark a report as resolved
once it has been investigated and handled.

### Analytics
An "Items by Category" breakdown showing which categories are most active,
and a "Top Users by Items Posted" ranking, surfacing platform usage
patterns for operational decisions.

### Admin Settings
The admin's own account information and password-change form, kept
separate from the regular member Settings page.

## 9. Shared Design System and Reusable Components

Everything visual lives in `styles_qt.py` so the whole app stays
consistent:

- **Palette**: primary blue `#1D4ED8` (with light/hover/dark variants),
  semantic success/error/warning/info colors, neutral grays for
  backgrounds, borders, and text.
- **Global QSS**: one stylesheet applied at the `QApplication` level
  covering inputs, buttons, scrollbars, dropdown popups, and dialogs.
- **Reusable widgets**: `FormField` (labelled `QLineEdit` with inline
  error and optional password show/hide), `FormDropdown` (labelled
  `QComboBox` with inline error and an optional placeholder), `FormTextArea`
  (labelled `QTextEdit` with inline error), `FormValidator` (sequential,
  ordered validation runner), plus button helpers (`primary_btn`,
  `secondary_btn`, `ghost_btn`, `danger_btn`, `link_btn`, `small_btn`),
  `stat_card`, `status_badge`, `colored_text` (category chips), and the
  sidebar navigation lists `USER_NAV` / `ADMIN_NAV`.
- **Domain constants**: `CATEGORIES`, `CONDITIONS`, `REGIONS` (the 25
  regions of Tanzania), `CATEGORY_COLORS`, and `STATUS_COLORS`, defined
  once and reused by every dropdown/badge across the app.

## 10. Form Validation Behaviour

Every form in the application (Login, Register, Add Item, the My Items
edit dialog, Wants, Profile, Settings) follows the same validation pattern,
driven by `FormValidator`: rules are checked **in order**, and on submit
the first rule that fails shows a red inline error message directly under
the offending field, gives that field keyboard focus, and stops — exactly
one problem surfaced at a time, matching the reference screenshots. Fixing
that field and resubmitting moves on to the next failing rule, if any.

## 11. Recent Fixes and Improvements

This edition includes two recent, targeted fixes on top of the original
PyQt6 port:

**Region dropdown popup positioning.** The Region dropdown (used in
Register, Add Item, Profile, and Settings) lists 25 entries. Without a
cap on visible rows, Qt attempted to render all 25 rows in the popup at
once; since that popup was taller than the remaining space below the
field, Qt flipped it upward, so it appeared floating above the form
instead of attached directly under the field — unlike shorter lists such
as Category, which fit comfortably and looked correctly positioned. A
custom bounded combo box (`_BoundedCombo` in `styles_qt.py`) now caps the
popup to a fixed number of visible rows (with an internal scrollbar for
the rest) and re-pins the popup directly beneath the field every time it
opens. This is a single, central fix applied to every `FormDropdown`
instance in the app, so all dropdowns — long or short lists — now behave
identically, with no changes required to Category or any other dropdown.

**Full item editing from My Items.** The "Edit" action in My Items
previously only allowed changing an item's availability status. It now
opens a complete edit dialog covering every field of the post — title,
category, condition, description, exchange-for text, contact phone,
region, and the photo (with a "Change Photo" option) — alongside the
original status selector, all saved together in one "Save" action. This
lets a member correct a mistake in any part of a listing after posting it,
without deleting and re-creating the item.

## 12. Testing

The repository includes four end-to-end smoke-test scripts that exercise
the application against a real SQLite database (no mocks for the data
layer), driving the actual Qt widgets:

- `e2e_test.py` — full user and admin journeys: register, login, browse,
  request/complete an exchange, messages, wants, notifications, history,
  reviews, profile, settings, every admin page, full navigation routing,
  and the four informational pages.
- `e2e_real_clicks_test.py` — real-click interaction checks, including
  that Region/Location dropdowns are plain click-to-choose (not
  free-typed) and that profile bio updates appear immediately after save.
- `e2e_warnings_test.py` — confirmation/warning dialog behaviour (sign-out,
  account deletion, exchange request edge cases, oversized image rejection)
  and the My Items edit dialog's status-change flow.
- `e2e_details_dropdown_test.py` — item details dialog content and dropdown
  arrow/visibility checks across the app.

Run them individually with a fresh database (each script registers its own
test users, so re-running against a database that already has those
accounts will report failures for duplicate-email registration, not real
regressions):

```bash
python e2e_test.py
python e2e_real_clicks_test.py
python e2e_warnings_test.py
python e2e_details_dropdown_test.py
```

On a headless machine (no display), prefix each command with `xvfb-run -a`.

All four suites pass in full (131 checks total) against the current
codebase, including the Region-dropdown and My-Items-edit changes
described in section 11.

## 13. Known Notes and Limitations

- The app is a single-machine desktop application backed by a local SQLite
  file; it is not designed for concurrent multi-process access to the same
  database file.
- Uploaded item images are copied into `assets/uploads/` with a generated
  filename; the original file selected by the user is left untouched.
- The `searchable=True` option on `FormDropdown` (type-to-filter, intended
  for very long lists) exists in `styles_qt.py` but is not currently
  enabled on any field; every dropdown in the app today is a plain
  click-to-choose list.
- The `REGIONS` list currently models the 25 regions of mainland Tanzania
  and Zanzibar as used in the reference design; it can be extended by
  editing the `REGIONS` constant in `styles_qt.py` without touching any
  other file, since every dropdown that uses it reads from that single
  list.
