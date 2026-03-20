"""
Tests for database operations (db.py)

Pattern: SETUP → ACTION → ASSERT
"""

import sqlite3
import tempfile
from pathlib import Path
import sys

# Add src to path so we can import db
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import db


def test_flag_email_saves_to_db():
    """Test that flagging an email saves it to the database."""

    # SETUP: Create a temporary database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db.DB_PATH = db_path  # Override the database path

        # Initialize the database
        db.init_db()

        # ACTION: Flag an email
        db.flag_email(
            email_index=5,
            sender="alice@example.com",
            summary="Important meeting",
            is_urgent=True,
            reason="Needs immediate response"
        )

        # ASSERT: Verify it was saved
        flagged = db.get_flagged_emails()
        assert len(flagged) == 1, "Should have 1 flagged email"
        assert flagged[0]["email_index"] == 5, "Email index should be 5"
        assert flagged[0]["sender"] == "alice@example.com", "Sender should match"
        assert flagged[0]["summary"] == "Important meeting", "Summary should match"


def test_unflag_email_removes_from_db():
    """Test that unflagging an email removes it from the database."""

    # SETUP
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db.DB_PATH = db_path
        db.init_db()

        # Flag an email first
        db.flag_email(5, "alice@example.com", "Test", is_urgent=True)
        assert len(db.get_flagged_emails()) == 1, "Should have 1 flagged email after flagging"

        # ACTION: Unflag it
        db.unflag_email(5)

        # ASSERT: Verify it's gone
        flagged = db.get_flagged_emails()
        assert len(flagged) == 0, "Should have 0 flagged emails after unflagging"


def test_get_urgent_flagged_limits_results():
    """Test that get_urgent_flagged returns max 20 emails."""

    # SETUP
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db.DB_PATH = db_path
        db.init_db()

        # ACTION: Flag 25 urgent emails
        for i in range(25):
            db.flag_email(i, f"sender{i}@example.com", f"Email {i}", is_urgent=True)

        # ASSERT: Should return only 20 (the limit)
        urgent = db.get_urgent_flagged()
        assert len(urgent) == 20, "Should return max 20 urgent emails"


if __name__ == "__main__":
    # Run tests manually for learning
    test_flag_email_saves_to_db()
    print("✓ test_flag_email_saves_to_db passed")

    test_unflag_email_removes_from_db()
    print("✓ test_unflag_email_removes_from_db passed")

    test_get_urgent_flagged_limits_results()
    print("✓ test_get_urgent_flagged_limits_results passed")

    print("\nAll tests passed!")
