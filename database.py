"""
database.py  --  WeShare Community
Single SQLite backend with a module-level singleton.
All other modules call:   import database as DB   then  DB.function(...)
"""
import sqlite3
import hashlib
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "weshare.db")


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Internal connection
# ---------------------------------------------------------------------------
_conn: sqlite3.Connection = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
        _migrate()
        _seed_admin()
    return _conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def _migrate():
    c = _conn
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name     TEXT    NOT NULL,
        email         TEXT    NOT NULL UNIQUE,
        phone         TEXT    DEFAULT '',
        location      TEXT    DEFAULT '',
        bio           TEXT    DEFAULT '',
        password_hash TEXT    NOT NULL,
        role          TEXT    NOT NULL DEFAULT 'user',
        status        TEXT    NOT NULL DEFAULT 'active',
        created_at    TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS items (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title        TEXT    NOT NULL,
        category     TEXT    NOT NULL DEFAULT 'Other',
        description  TEXT    DEFAULT '',
        condition    TEXT    DEFAULT 'Good',
        exchange_for TEXT    DEFAULT '',
        phone        TEXT    DEFAULT '',
        location     TEXT    DEFAULT '',
        image_path   TEXT    DEFAULT '',
        status       TEXT    NOT NULL DEFAULT 'available',
        created_at   TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS exchanges (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        requester_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        owner_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        offered_item_id   INTEGER REFERENCES items(id) ON DELETE SET NULL,
        requested_item_id INTEGER REFERENCES items(id) ON DELETE SET NULL,
        status            TEXT    NOT NULL DEFAULT 'pending',
        created_at        TEXT    NOT NULL,
        updated_at        TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS messages (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        content     TEXT    NOT NULL,
        is_read     INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        message    TEXT    NOT NULL,
        is_read    INTEGER NOT NULL DEFAULT 0,
        created_at TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS wants (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title      TEXT    NOT NULL,
        category   TEXT    DEFAULT '',
        notes      TEXT    DEFAULT '',
        created_at TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        reviewer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        reviewee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        exchange_id INTEGER REFERENCES exchanges(id) ON DELETE SET NULL,
        rating      INTEGER NOT NULL DEFAULT 5,
        comment     TEXT    DEFAULT '',
        created_at  TEXT    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS reports (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        against_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        reason      TEXT    NOT NULL,
        status      TEXT    NOT NULL DEFAULT 'pending',
        created_at  TEXT    NOT NULL
    );
    """)
    c.commit()
    # Safeguard: add 'condition' column to pre-existing databases that
    # were created before this column existed (additive, non-breaking).
    cols = [r[1] for r in c.execute("PRAGMA table_info(items)").fetchall()]
    if "condition" not in cols:
        c.execute("ALTER TABLE items ADD COLUMN condition TEXT DEFAULT 'Good'")
        c.commit()


def _seed_admin():
    c = _conn
    row = c.execute(
        "SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
    if not row:
        c.execute(
            "INSERT INTO users "
            "(full_name,email,phone,location,bio,"
            " password_hash,role,status,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            ("Administrator", "admin@weshare.app",
             "", "Dar es Salaam", "",
             _hash("admin123"), "admin", "active", _now()))
        c.commit()


# Initialise on import
_get_conn()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def register_user(full_name: str, email: str, phone: str,
                  password: str, location: str = "") -> tuple:
    """Returns (success: bool, message: str)."""
    c = _get_conn()
    if c.execute("SELECT id FROM users WHERE email=?",
                 (email,)).fetchone():
        return False, "An account with that email already exists."
    try:
        c.execute(
            "INSERT INTO users "
            "(full_name,email,phone,location,bio,"
            " password_hash,role,status,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (full_name, email, phone, location, "",
             _hash(password), "user", "active", _now()))
        c.commit()
        return True, "Account created successfully. You can now sign in."
    except sqlite3.IntegrityError as exc:
        return False, str(exc)


def authenticate(identifier: str, password: str):
    """
    identifier = email or phone.
    Returns user dict on success, None on failure.
    """
    c = _get_conn()
    row = c.execute(
        "SELECT * FROM users WHERE email=? OR phone=?",
        (identifier, identifier)).fetchone()
    if not row:
        return None
    row = dict(row)
    if row["password_hash"] != _hash(password):
        return None
    if row["status"] == "suspended":
        row["is_banned"] = True
    else:
        row["is_banned"] = False
    # Convenience alias so older code using user["name"] still works
    row["name"] = row["full_name"]
    return row


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_user(uid: int):
    c = _get_conn()
    r = c.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if r:
        d = dict(r)
        d["name"] = d["full_name"]
        return d
    return None


def get_all_users():
    c = _get_conn()
    rows = c.execute(
        "SELECT * FROM users ORDER BY created_at DESC").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["name"] = d["full_name"]
        result.append(d)
    return result


def search_users(q: str):
    c   = _get_conn()
    like = f"%{q}%"
    rows = c.execute(
        "SELECT * FROM users "
        "WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ? "
        "ORDER BY full_name",
        (like, like, like)).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["name"] = d["full_name"]
        result.append(d)
    return result


def update_user(uid: int, data: dict) -> tuple:
    """data may contain: full_name, email, phone, location, bio, password."""
    c = _get_conn()
    if "email" in data:
        clash = c.execute(
            "SELECT id FROM users WHERE email=? AND id!=?",
            (data["email"], uid)).fetchone()
        if clash:
            return False, "That email address is already in use."
    sets, vals = [], []
    for k in ("full_name", "email", "phone", "location", "bio"):
        if k in data:
            sets.append(f"{k}=?")
            vals.append(data[k])
    if "password" in data:
        sets.append("password_hash=?")
        vals.append(_hash(data["password"]))
    if not sets:
        return True, "No changes."
    vals.append(uid)
    c.execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?", vals)
    c.commit()
    return True, "Profile updated."


def set_user_status(uid: int, status: str):
    c = _get_conn()
    c.execute("UPDATE users SET status=? WHERE id=?", (status, uid))
    c.commit()


def delete_user(uid: int):
    c = _get_conn()
    c.execute("DELETE FROM users WHERE id=?", (uid,))
    c.commit()


def get_user_stats(uid: int) -> dict:
    c = _get_conn()
    posted = c.execute(
        "SELECT COUNT(*) FROM items WHERE user_id=?", (uid,)).fetchone()[0]
    done = c.execute(
        "SELECT COUNT(*) FROM exchanges "
        "WHERE (requester_id=? OR owner_id=?) AND status='completed'",
        (uid, uid)).fetchone()[0]
    avg_row = c.execute(
        "SELECT AVG(rating) FROM reviews WHERE reviewee_id=?",
        (uid,)).fetchone()
    avg = round(avg_row[0] or 0.0, 1)
    cnt = c.execute(
        "SELECT COUNT(*) FROM reviews WHERE reviewee_id=?",
        (uid,)).fetchone()[0]
    return {"items_posted": posted, "exchanges_done": done,
            "avg_rating": avg, "review_count": cnt}


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

def post_item(user_id: int, title: str, category: str,
              description: str = "", condition: str = "Good",
              exchange_for: str = "",
              phone: str = "", location: str = "",
              image_path: str = ""):
    c = _get_conn()
    c.execute(
        "INSERT INTO items "
        "(user_id,title,category,description,condition,exchange_for,"
        " phone,location,image_path,status,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (user_id, title, category, description, condition, exchange_for,
         phone, location, image_path, "available", _now()))
    c.commit()


def get_all_items(category: str = "All", search: str = ""):
    """
    Returns available items from OTHER users.
    category='All' means no category filter.
    """
    c    = _get_conn()
    like = f"%{search}%"
    base = (
        "SELECT i.*, u.full_name AS owner_name "
        "FROM items i "
        "JOIN users u ON i.user_id=u.id "
        "WHERE i.status='available' "
        "  AND (i.title LIKE ? OR i.description LIKE ?) "
    )
    if category and category != "All":
        rows = c.execute(
            base + "  AND i.category=? "
                   "ORDER BY i.created_at DESC",
            (like, like, category)).fetchall()
    else:
        rows = c.execute(
            base + "ORDER BY i.created_at DESC",
            (like, like)).fetchall()
    return [dict(r) for r in rows]


def get_user_items(uid: int):
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT * FROM items WHERE user_id=? ORDER BY created_at DESC",
        (uid,)).fetchall()]


def get_item(item_id: int):
    c = _get_conn()
    r = c.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return dict(r) if r else None


def update_item(item_id: int, data: dict):
    c     = _get_conn()
    allowed = ["title", "category", "description", "condition", "exchange_for",
               "phone", "location", "image_path", "status"]
    sets, vals = [], []
    for k in allowed:
        if k in data:
            sets.append(f"{k}=?")
            vals.append(data[k])
    if sets:
        vals.append(item_id)
        c.execute(f"UPDATE items SET {', '.join(sets)} WHERE id=?", vals)
        c.commit()


def delete_item(item_id: int):
    c = _get_conn()
    c.execute("DELETE FROM items WHERE id=?", (item_id,))
    c.commit()


def get_all_items_admin():
    """Admin: all items regardless of status."""
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT i.*, u.full_name AS owner_name "
        "FROM items i JOIN users u ON i.user_id=u.id "
        "ORDER BY i.created_at DESC").fetchall()]


def get_recent_items(n: int = 10):
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT i.*, u.full_name AS owner_name "
        "FROM items i JOIN users u ON i.user_id=u.id "
        "ORDER BY i.created_at DESC LIMIT ?", (n,)).fetchall()]


# ---------------------------------------------------------------------------
# Exchanges
# ---------------------------------------------------------------------------

def request_exchange(requester_id: int, owner_id: int,
                     offered_item_id, requested_item_id) -> tuple:
    c = _get_conn()
    dup = c.execute(
        "SELECT id FROM exchanges "
        "WHERE requester_id=? AND requested_item_id=? AND status='pending'",
        (requester_id, requested_item_id)).fetchone()
    if dup:
        return False, "You already have a pending request for this item."
    c.execute(
        "INSERT INTO exchanges "
        "(requester_id,owner_id,offered_item_id,requested_item_id,"
        " status,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
        (requester_id, owner_id, offered_item_id, requested_item_id,
         "pending", _now(), _now()))
    c.commit()
    req = get_user(requester_id)
    if req:
        add_notification(owner_id,
                         f"{req['full_name']} sent you an exchange request.")
    return True, "Request sent."


def get_user_exchanges(uid: int):
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT e.*, "
        "  req.full_name AS requester_name, "
        "  own.full_name AS owner_name, "
        "  oi.title AS item_given, "
        "  ri.title AS item_received "
        "FROM exchanges e "
        "JOIN users req ON e.requester_id=req.id "
        "JOIN users own ON e.owner_id=own.id "
        "LEFT JOIN items oi ON e.offered_item_id=oi.id "
        "LEFT JOIN items ri ON e.requested_item_id=ri.id "
        "WHERE e.requester_id=? OR e.owner_id=? "
        "ORDER BY e.created_at DESC",
        (uid, uid)).fetchall()]


def update_exchange_status(exchange_id: int, status: str):
    c = _get_conn()
    c.execute("UPDATE exchanges SET status=?, updated_at=? WHERE id=?",
              (status, _now(), exchange_id))
    c.commit()


def get_all_exchanges():
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT e.*, "
        "  req.full_name AS requester_name, "
        "  own.full_name AS owner_name, "
        "  oi.title AS item_given, "
        "  ri.title AS item_received "
        "FROM exchanges e "
        "JOIN users req ON e.requester_id=req.id "
        "JOIN users own ON e.owner_id=own.id "
        "LEFT JOIN items oi ON e.offered_item_id=oi.id "
        "LEFT JOIN items ri ON e.requested_item_id=ri.id "
        "ORDER BY e.created_at DESC").fetchall()]


def get_exchange_history(uid: int, status_filter: str = "all"):
    c    = _get_conn()
    base = (
        "SELECT e.*, "
        "  CASE WHEN e.requester_id=? "
        "       THEN own.full_name ELSE req.full_name END AS partner_name, "
        "  oi.title AS item_given, "
        "  ri.title AS item_received "
        "FROM exchanges e "
        "JOIN users req ON e.requester_id=req.id "
        "JOIN users own ON e.owner_id=own.id "
        "LEFT JOIN items oi ON e.offered_item_id=oi.id "
        "LEFT JOIN items ri ON e.requested_item_id=ri.id "
    )
    if status_filter == "all":
        return [dict(r) for r in c.execute(
            base + "WHERE e.requester_id=? OR e.owner_id=? "
                   "ORDER BY e.created_at DESC",
            (uid, uid, uid)).fetchall()]
    return [dict(r) for r in c.execute(
        base + "WHERE (e.requester_id=? OR e.owner_id=?) "
               "  AND e.status=? ORDER BY e.created_at DESC",
        (uid, uid, uid, status_filter)).fetchall()]


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

def send_message(sender_id: int, receiver_id: int, content: str):
    c = _get_conn()
    c.execute(
        "INSERT INTO messages "
        "(sender_id,receiver_id,content,is_read,created_at) "
        "VALUES (?,?,?,0,?)",
        (sender_id, receiver_id, content, _now()))
    c.commit()
    sender = get_user(sender_id)
    if sender:
        add_notification(receiver_id,
                         f"New message from {sender['full_name']}.")


def get_conversations(uid: int):
    """Return list of partner user dicts plus last_message and unread count."""
    c = _get_conn()
    partner_ids = c.execute(
        "SELECT DISTINCT "
        "  CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END AS pid "
        "FROM messages "
        "WHERE sender_id=? OR receiver_id=?",
        (uid, uid, uid)).fetchall()
    result = []
    for row in partner_ids:
        pid = row["pid"]
        partner = get_user(pid)
        if not partner:
            continue
        last = c.execute(
            "SELECT content, created_at FROM messages "
            "WHERE (sender_id=? AND receiver_id=?) "
            "   OR (sender_id=? AND receiver_id=?) "
            "ORDER BY created_at DESC LIMIT 1",
            (uid, pid, pid, uid)).fetchone()
        unread = c.execute(
            "SELECT COUNT(*) FROM messages "
            "WHERE sender_id=? AND receiver_id=? AND is_read=0",
            (pid, uid)).fetchone()[0]
        partner["last_message"] = dict(last) if last else {}
        partner["unread"]       = unread
        result.append(partner)
    return result


def get_thread(uid: int, partner_id: int):
    c = _get_conn()
    rows = c.execute(
        "SELECT * FROM messages "
        "WHERE (sender_id=? AND receiver_id=?) "
        "   OR (sender_id=? AND receiver_id=?) "
        "ORDER BY created_at ASC",
        (uid, partner_id, partner_id, uid)).fetchall()
    # Mark received messages as read
    c.execute(
        "UPDATE messages SET is_read=1 "
        "WHERE receiver_id=? AND sender_id=? AND is_read=0",
        (uid, partner_id))
    c.commit()
    return [dict(r) for r in rows]


def unread_message_count(uid: int) -> int:
    c = _get_conn()
    return c.execute(
        "SELECT COUNT(*) FROM messages WHERE receiver_id=? AND is_read=0",
        (uid,)).fetchone()[0]


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def add_notification(uid: int, message: str):
    c = _get_conn()
    c.execute(
        "INSERT INTO notifications (user_id,message,is_read,created_at) "
        "VALUES (?,?,0,?)",
        (uid, message, _now()))
    c.commit()


def get_notifications(uid: int):
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT * FROM notifications WHERE user_id=? "
        "ORDER BY created_at DESC",
        (uid,)).fetchall()]


def mark_notification_read(nid: int):
    c = _get_conn()
    c.execute("UPDATE notifications SET is_read=1 WHERE id=?", (nid,))
    c.commit()


def mark_all_notifications_read(uid: int):
    c = _get_conn()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (uid,))
    c.commit()


def unread_notification_count(uid: int) -> int:
    c = _get_conn()
    return c.execute(
        "SELECT COUNT(*) FROM notifications "
        "WHERE user_id=? AND is_read=0",
        (uid,)).fetchone()[0]


# ---------------------------------------------------------------------------
# Wants
# ---------------------------------------------------------------------------

def add_want(user_id: int, title: str,
             category: str = "", notes: str = ""):
    c = _get_conn()
    c.execute(
        "INSERT INTO wants (user_id,title,category,notes,created_at) "
        "VALUES (?,?,?,?,?)",
        (user_id, title, category, notes, _now()))
    c.commit()


def get_wants(uid: int):
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT * FROM wants WHERE user_id=? ORDER BY created_at DESC",
        (uid,)).fetchall()]


def get_all_wants():
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT w.*, u.full_name AS user_name "
        "FROM wants w JOIN users u ON w.user_id=u.id "
        "ORDER BY w.created_at DESC").fetchall()]


def delete_want(want_id: int):
    c = _get_conn()
    c.execute("DELETE FROM wants WHERE id=?", (want_id,))
    c.commit()


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

def add_review(reviewer_id: int, reviewee_id: int,
               rating: int, comment: str = "",
               exchange_id=None):
    c = _get_conn()
    c.execute(
        "INSERT INTO reviews "
        "(reviewer_id,reviewee_id,exchange_id,rating,comment,created_at) "
        "VALUES (?,?,?,?,?,?)",
        (reviewer_id, reviewee_id, exchange_id, rating, comment, _now()))
    c.commit()


def get_reviews_for_user(uid: int):
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT r.*, u.full_name AS reviewer_name "
        "FROM reviews r JOIN users u ON r.reviewer_id=u.id "
        "WHERE r.reviewee_id=? ORDER BY r.created_at DESC",
        (uid,)).fetchall()]


def get_reviews_by_user(uid: int):
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT r.*, u.full_name AS reviewee_name "
        "FROM reviews r JOIN users u ON r.reviewee_id=u.id "
        "WHERE r.reviewer_id=? ORDER BY r.created_at DESC",
        (uid,)).fetchall()]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

def add_report(reporter_id: int, against_id: int, reason: str):
    c = _get_conn()
    c.execute(
        "INSERT INTO reports "
        "(reporter_id,against_id,reason,status,created_at) "
        "VALUES (?,?,?,?,?)",
        (reporter_id, against_id, reason, "pending", _now()))
    c.commit()


def get_all_reports():
    c = _get_conn()
    return [dict(r) for r in c.execute(
        "SELECT rp.*, "
        "  ur.full_name AS reporter_name, "
        "  ua.full_name AS against_name "
        "FROM reports rp "
        "JOIN users ur ON rp.reporter_id=ur.id "
        "JOIN users ua ON rp.against_id=ua.id "
        "ORDER BY rp.created_at DESC").fetchall()]


def update_report_status(report_id: int, status: str):
    c = _get_conn()
    c.execute("UPDATE reports SET status=? WHERE id=?", (status, report_id))
    c.commit()


# ---------------------------------------------------------------------------
# Admin analytics
# ---------------------------------------------------------------------------

def count_user_exchanges(uid: int) -> int:
    c = _get_conn()
    return c.execute(
        "SELECT COUNT(*) FROM exchanges "
        "WHERE (requester_id=? OR owner_id=?) AND status='completed'",
        (uid, uid)).fetchone()[0]


def count_user_wants(uid: int) -> int:
    c = _get_conn()
    return c.execute(
        "SELECT COUNT(*) FROM wants WHERE user_id=?",
        (uid,)).fetchone()[0]


def get_avg_rating(uid: int):
    c = _get_conn()
    row = c.execute(
        "SELECT AVG(rating) FROM reviews WHERE reviewee_id=?",
        (uid,)).fetchone()
    return row[0] if row and row[0] else None


def get_admin_stats() -> dict:
    c = _get_conn()
    users      = c.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    items      = c.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    available  = c.execute("SELECT COUNT(*) FROM items WHERE status='available'").fetchone()[0]
    exchanges  = c.execute("SELECT COUNT(*) FROM exchanges").fetchone()[0]
    completed  = c.execute("SELECT COUNT(*) FROM exchanges WHERE status='completed'").fetchone()[0]
    pending    = c.execute("SELECT COUNT(*) FROM exchanges WHERE status='pending'").fetchone()[0]
    messages   = c.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    reports    = c.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0]
    wants      = c.execute("SELECT COUNT(*) FROM wants").fetchone()[0]
    return {
        "total_users":    users,
        "total_items":    items,
        "available_items": available,
        "total_exchanges": exchanges,
        "completed_exchanges": completed,
        "pending_exchanges": pending,
        "total_messages": messages,
        "pending_reports": reports,
        "total_wants": wants,
    }
