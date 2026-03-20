"""
Tests for FastAPI endpoints (api.py)

Tests the REST API without calling external services:
- GET /emails - retrieve emails
- POST /flag/{index} - flag email
- DELETE /flag/{index} - unflag email
- GET /flagged - get flagged emails

Note: Summary generation test requires mocking Claude API
"""

import json
import tempfile
from pathlib import Path
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
api_key = os.getenv("A_API_KEY")

# If no API key, mock the LLM so api.py can import without crashing
if not api_key:
    sys.modules['langchain_anthropic'] = MagicMock()

import db
from fastapi.testclient import TestClient
from api import app

# Create test client
client = TestClient(app)


def setup_test_db(tmpdir):
    """Setup a test database."""
    db_path = Path(tmpdir) / "test.db"
    db.DB_PATH = db_path
    db.init_db()
    return db_path


def setup_test_emails(tmpdir):
    """Setup sample emails for testing."""
    emails_dir = Path(tmpdir) / "emails"
    emails_dir.mkdir()
    emails_file = emails_dir / "emails.json"

    sample_emails = [
        {
            "index": 0,
            "from": "boss@company.com",
            "date": "2026-03-20",
            "subject": "Urgent: Quarterly Review",
            "body": "Please complete your review by EOD",
            "account": "user@gmail.com",
            "urgency": "URGENT",
            "category": "Personal",
            "summary": ""
        },
        {
            "index": 1,
            "from": "amazon@amazon.com",
            "date": "2026-03-19",
            "subject": "Your order has shipped",
            "body": "Tracking: 12345",
            "account": "user@gmail.com",
            "urgency": "FYI",
            "category": "Payment confirmation",
            "summary": ""
        },
        {
            "index": 2,
            "from": "spam@ads.com",
            "date": "2026-03-18",
            "subject": "BUY NOW!!!",
            "body": "Click here to win!",
            "account": "user@gmail.com",
            "urgency": "IGNORE",
            "category": "Spam",
            "summary": ""
        }
    ]

    emails_file.write_text(json.dumps(sample_emails, indent=2))
    return emails_file


def test_get_all_emails():
    """Test GET /emails returns all emails."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        emails_file = setup_test_emails(tmpdir)

        # Patch the emails_path in api.py
        with patch('api.emails_path', emails_file):
            # ACTION: Request all emails
            response = client.get("/emails")

            # ASSERT
            assert response.status_code == 200
            emails = response.json()
            assert len(emails) == 3
            assert emails[0]["from"] == "boss@company.com"
            assert emails[1]["from"] == "amazon@amazon.com"


def test_get_urgent_emails():
    """Test GET /emails/urgent returns only urgent emails."""

    with tempfile.TemporaryDirectory() as tmpdir:
        emails_file = setup_test_emails(tmpdir)

        with patch('api.emails_path', emails_file):
            response = client.get("/emails/urgent")

            assert response.status_code == 200
            urgent = response.json()
            assert len(urgent) == 1
            assert urgent[0]["urgency"] == "URGENT"
            assert urgent[0]["subject"] == "Urgent: Quarterly Review"


def test_flag_email():
    """Test POST /flag/{index} saves flagged email to database."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        emails_file = setup_test_emails(tmpdir)
        setup_test_db(tmpdir)

        with patch('api.emails_path', emails_file):
            # ACTION: Flag email 0
            response = client.post("/flag/0")

            # ASSERT
            assert response.status_code == 200
            assert response.json() == {"status": "flagged"}

            # Verify it was saved to database
            flagged = db.get_flagged_emails()
            assert len(flagged) == 1
            assert flagged[0]["email_index"] == 0


def test_unflag_email():
    """Test DELETE /flag/{index} removes flagged email."""

    with tempfile.TemporaryDirectory() as tmpdir:
        emails_file = setup_test_emails(tmpdir)
        setup_test_db(tmpdir)

        with patch('api.emails_path', emails_file):
            # Setup: Flag an email first
            client.post("/flag/0")
            assert len(db.get_flagged_emails()) == 1

            # ACTION: Unflag it
            response = client.delete("/flag/0")

            # ASSERT
            assert response.status_code == 200
            assert response.json() == {"status": "unflagged"}
            assert len(db.get_flagged_emails()) == 0


def test_get_flagged_emails():
    """Test GET /flagged returns all flagged emails."""

    with tempfile.TemporaryDirectory() as tmpdir:
        emails_file = setup_test_emails(tmpdir)
        setup_test_db(tmpdir)

        with patch('api.emails_path', emails_file):
            # Setup: Flag some emails
            client.post("/flag/0")
            client.post("/flag/1")

            # ACTION: Get flagged
            response = client.get("/flagged")

            # ASSERT
            assert response.status_code == 200
            flagged = response.json()
            assert len(flagged) == 2


def test_get_emails_by_category():
    """Test GET /emails/category/{category} filters by category."""

    with tempfile.TemporaryDirectory() as tmpdir:
        emails_file = setup_test_emails(tmpdir)

        with patch('api.emails_path', emails_file):
            # ACTION: Get Personal emails
            response = client.get("/emails/category/Personal")

            # ASSERT
            assert response.status_code == 200
            personal = response.json()
            assert len(personal) == 1
            assert personal[0]["category"] == "Personal"

            # ACTION: Get Spam emails
            response = client.get("/emails/category/Spam")
            spam = response.json()
            assert len(spam) == 1
            assert spam[0]["urgency"] == "IGNORE"


@pytest.mark.skipif(not api_key, reason="Requires A_API_KEY in .env")
def test_get_email_summary_with_mock():
    """
    Test GET /emails/{index}/summary generates summary.

    Note: We mock the LLM response to avoid API calls in tests.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        emails_file = setup_test_emails(tmpdir)

        with patch('api.emails_path', emails_file):
            # Mock the LLM response
            mock_llm_response = MagicMock()
            mock_llm_response.content = "This is a test summary of the quarterly review email."

            with patch('api.chain.invoke', return_value=mock_llm_response):
                # ACTION: Request summary
                response = client.get("/emails/0/summary")

                # ASSERT
                assert response.status_code == 200
                data = response.json()
                assert "summary" in data
                assert "quarterly review" in data["summary"].lower()


if __name__ == "__main__":
    # Run manually
    print("⚠️  Note: These tests are meant to be run with pytest")
    print("Run with: poetry run pytest tests/test_api.py -v")
