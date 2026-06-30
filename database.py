"""
Database Layer — FatherSpace
-----------------------------
SQLite-based storage. Handles:
- Anonymous user registration (maps Telegram ID → DadAnon ID, encrypted)
- Message history per channel
- Bans and reports
- Stats for admins

PRIVACY NOTE:
Telegram IDs are hashed before storage using SHA-256 + a secret salt.
This means even if the database is compromised, real Telegram IDs
cannot be recovered. The mapping is one-way.
"""

import sqlite3
import hashlib
import os
import random
import string
from datetime import datetime
from config.settings import DB_PATH

# Secret salt — change this before deployment and keep it private
_SALT = os.environ.get("FATHERSPACE_SALT", "change_this_salt_before_deploy_xK9p")


def _hash_id(telegram_id: int) -> str:
    """One-way hash of Telegram ID. Cannot be reversed."""
    raw = f"{_SALT}:{telegram_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _generate_dad_id() -> str:
    """Generate a human-friendly anonymous ID like DadAnon#4721"""
    number = random.randint(1000, 9999)
    return f"DadAnon#{number}"


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables on first run."""
    conn = get_connection()
    c = conn.cursor()

    # Users — no real identity stored, only hashed ID + anonymous alias
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            hashed_id       TEXT PRIMARY KEY,
            dad_id          TEXT UNIQUE NOT NULL,
            joined_at       TEXT NOT NULL,
            is_banned       INTEGER DEFAULT 0,
            message_count   INTEGER DEFAULT 0,
            active_channel  TEXT DEFAULT NULL
        )
    """)

    # Messages — stored against dad_id only, never real identity
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            dad_id          TEXT NOT NULL,
            channel         TEXT NOT NULL,
            content         TEXT,
            msg_type        TEXT DEFAULT 'text',
            posted_at       TEXT NOT NULL,
            reply_to_id     INTEGER DEFAULT NULL,
            is_flagged      INTEGER DEFAULT 0
        )
    """)

    # Reports — when members flag harmful content
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_dad_id TEXT NOT NULL,
            message_id      INTEGER NOT NULL,
            reason          TEXT,
            reported_at     TEXT NOT NULL,
            resolved        INTEGER DEFAULT 0
        )
    """)

    # Broadcast log — for admin announcements
    c.execute("""
        CREATE TABLE IF NOT EXISTS broadcasts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_by         TEXT NOT NULL,
            content         TEXT NOT NULL,
            sent_at         TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ── User Operations ───────────────────────────────────────────────────────────

def register_user(telegram_id: int) -> dict:
    """
    Register a new user or return existing one.
    Only the hashed ID is ever stored — real Telegram ID is never saved.
    """
    hashed = _hash_id(telegram_id)
    conn = get_connection()
    c = conn.cursor()

    existing = c.execute(
        "SELECT * FROM users WHERE hashed_id = ?", (hashed,)
    ).fetchone()

    if existing:
        conn.close()
        return dict(existing)

    # Generate a unique DadAnon ID
    dad_id = _generate_dad_id()
    while c.execute("SELECT 1 FROM users WHERE dad_id = ?", (dad_id,)).fetchone():
        dad_id = _generate_dad_id()

    now = datetime.utcnow().isoformat()
    c.execute("""
        INSERT INTO users (hashed_id, dad_id, joined_at)
        VALUES (?, ?, ?)
    """, (hashed, dad_id, now))
    conn.commit()

    user = c.execute(
        "SELECT * FROM users WHERE hashed_id = ?", (hashed,)
    ).fetchone()
    conn.close()
    return dict(user)


def get_user(telegram_id: int) -> dict | None:
    """Look up user by Telegram ID (hashed before lookup)."""
    hashed = _hash_id(telegram_id)
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE hashed_id = ?", (hashed,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def set_active_channel(telegram_id: int, channel: str):
    """Remember which channel the user is posting to."""
    hashed = _hash_id(telegram_id)
    conn = get_connection()
    conn.execute(
        "UPDATE users SET active_channel = ? WHERE hashed_id = ?",
        (channel, hashed)
    )
    conn.commit()
    conn.close()


def increment_message_count(telegram_id: int):
    hashed = _hash_id(telegram_id)
    conn = get_connection()
    conn.execute(
        "UPDATE users SET message_count = message_count + 1 WHERE hashed_id = ?",
        (hashed,)
    )
    conn.commit()
    conn.close()


def is_banned(telegram_id: int) -> bool:
    user = get_user(telegram_id)
    return bool(user and user["is_banned"])


def ban_user_by_dad_id(dad_id: str):
    conn = get_connection()
    conn.execute("UPDATE users SET is_banned = 1 WHERE dad_id = ?", (dad_id,))
    conn.commit()
    conn.close()


def unban_user_by_dad_id(dad_id: str):
    conn = get_connection()
    conn.execute("UPDATE users SET is_banned = 0 WHERE dad_id = ?", (dad_id,))
    conn.commit()
    conn.close()


def get_all_hashed_ids() -> list[str]:
    """For broadcasting — returns all hashed IDs of non-banned users."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT hashed_id FROM users WHERE is_banned = 0"
    ).fetchall()
    conn.close()
    return [r["hashed_id"] for r in rows]


# ── Message Operations ────────────────────────────────────────────────────────

def save_message(dad_id: str, channel: str, content: str,
                 msg_type: str = "text", reply_to_id: int = None) -> int:
    """Save a message. Returns the new message ID."""
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    cursor = conn.execute("""
        INSERT INTO messages (dad_id, channel, content, msg_type, posted_at, reply_to_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (dad_id, channel, content, msg_type, now, reply_to_id))
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return msg_id


def get_recent_messages(channel: str, limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM messages
        WHERE channel = ? AND is_flagged = 0
        ORDER BY posted_at DESC LIMIT ?
    """, (channel, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def flag_message(message_id: int):
    conn = get_connection()
    conn.execute("UPDATE messages SET is_flagged = 1 WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()


# ── Reports ───────────────────────────────────────────────────────────────────

def file_report(reporter_dad_id: str, message_id: int, reason: str):
    conn = get_connection()
    conn.execute("""
        INSERT INTO reports (reporter_dad_id, message_id, reason, reported_at)
        VALUES (?, ?, ?, ?)
    """, (reporter_dad_id, message_id, reason, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_pending_reports() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reports WHERE resolved = 0 ORDER BY reported_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    conn = get_connection()
    total_users = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 0").fetchone()[0]
    total_messages = conn.execute("SELECT COUNT(*) FROM messages WHERE is_flagged = 0").fetchone()[0]
    pending_reports = conn.execute("SELECT COUNT(*) FROM reports WHERE resolved = 0").fetchone()[0]
    bans = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1").fetchone()[0]

    channel_counts = conn.execute("""
        SELECT channel, COUNT(*) as count FROM messages
        WHERE is_flagged = 0
        GROUP BY channel ORDER BY count DESC
    """).fetchall()

    conn.close()
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "pending_reports": pending_reports,
        "bans": bans,
        "channels": [dict(r) for r in channel_counts]
    }
