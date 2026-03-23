"""
SQLite database for flagged emails and learning memory.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "memory.db"


def init_db():
    """Initialize database schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flagged_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_index INTEGER NOT NULL,
            sender TEXT NOT NULL,
            summary TEXT,
            is_urgent BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT
        )
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


def flag_email(email_index, sender, summary, is_urgent=True, reason=""):
    """Flag an email as important for learning."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO flagged_emails (email_index, sender, summary, is_urgent, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (email_index, sender, summary, is_urgent, reason))

    conn.commit()
    conn.close()
    logger.info(f"Flagged email {email_index} from {sender}")


def unflag_email(email_index):
    """Remove a flagged email."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM flagged_emails WHERE email_index = ?", (email_index,))

    conn.commit()
    conn.close()
    logger.info(f"Unflagged email {email_index}")


def get_flagged_emails():
    """Get all flagged emails."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM flagged_emails ORDER BY created_at DESC")
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]


def get_urgent_flagged():
    """Get flagged emails marked as urgent (for AI context)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sender, summary, reason
        FROM flagged_emails
        WHERE is_urgent = 1
        ORDER BY created_at DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()

    conn.close()
    return [dict(row) for row in rows]
