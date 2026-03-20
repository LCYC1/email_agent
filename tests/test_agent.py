"""
Integration tests for email classification agent (agent.py)

These tests call the REAL Claude API to verify the classification works end-to-end.
Cost: ~$0.001 per test run (Haiku is cheap)
Value: Verifies Claude actually returns what we expect
"""

import json
import os
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
import agent

# Load API key from .env
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
api_key = os.getenv("A_API_KEY")

# Skip integration tests by default (unless RUN_INTEGRATION_TESTS env var is set)
SKIP_INTEGRATION = not os.getenv("RUN_INTEGRATION_TESTS", "").lower() in ["true", "1", "yes"]


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration test (requires API). Run with: RUN_INTEGRATION_TESTS=true pytest")
def test_claude_classifies_emails_correctly():
    """
    Integration test: Send real emails to Claude and verify classification.

    This is NOT a unit test (doesn't mock). It tests the REAL integration.
    - Calls real Claude API via agent.classify_emails()
    - Verifies response structure and content
    - Confirms AI classification works
    """

    if not api_key:
        print("⚠️  Skipping: A_API_KEY not set in .env")
        return

    # Setup real LLM
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=api_key)

    # Sample emails to classify
    sample_headers = [
        {
            "index": 0,
            "from": "boss@company.com",
            "date": "2026-03-20",
            "subject": "Urgent: Quarterly Performance Review - Due EOD"
        },
        {
            "index": 1,
            "from": "amazon@amazon.com",
            "date": "2026-03-20",
            "subject": "Your order #12345 has shipped"
        },
        {
            "index": 2,
            "from": "newsletter@spam.com",
            "date": "2026-03-20",
            "subject": "BUY NOW!!! 50% OFF EVERYTHING!!!"
        }
    ]

    # ACTION: Call the real classify_emails function from agent.py
    results = agent.classify_emails(
        sample_headers,
        "No flagged emails yet. Use your best judgment.",
        llm
    )
    result_map = {r["index"]: r for r in results}

    # ASSERT: Verify structure
    assert len(results) == 3, "Should classify all 3 emails"
    assert all("urgency" in r and "category" in r for r in results), "Should have urgency and category"

    # ASSERT: Verify sensible classifications
    # Email 0 (boss) should be URGENT or FYI
    assert result_map[0]["urgency"] in ["URGENT", "FYI"], f"Boss email should be urgent, got {result_map[0]['urgency']}"

    # Email 1 (Amazon) should be FYI or IGNORE
    assert result_map[1]["urgency"] in ["FYI", "IGNORE"], f"Amazon should be FYI/IGNORE, got {result_map[1]['urgency']}"
    assert result_map[1]["category"] == "Payment confirmation", f"Amazon should be Payment confirmation, got {result_map[1]['category']}"

    # Email 2 (spam) should be IGNORE or FYI, and category should be Spam or Advertisement
    assert result_map[2]["urgency"] in ["IGNORE", "FYI"], f"Spam should be IGNORE, got {result_map[2]['urgency']}"
    assert result_map[2]["category"] in ["Spam", "Advertisement"], f"Should be Spam or Advertisement, got {result_map[2]['category']}"

    print(f"\n✅ Claude classified emails:")
    for r in results:
        print(f"  Email {r['index']}: {r['urgency']} / {r['category']}")


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration test (requires API). Run with: RUN_INTEGRATION_TESTS=true pytest")
def test_claude_respects_learning_context():
    """
    Test that Claude incorporates learning context in classifications.

    Simulates: User flagged an email as urgent, Claude should learn from it.
    """

    if not api_key:
        print("⚠️  Skipping: A_API_KEY not set in .env")
        return

    # Setup real LLM
    llm = ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=api_key)

    sample_headers = [
        {
            "index": 0,
            "from": "john.doe@startup.co",
            "date": "2026-03-20",
            "subject": "Quick question about the proposal"
        }
    ]

    # Simulate learning context (user flagged similar email before)
    learning_context = """Emails that were flagged as URGENT:
- From: john.doe@startup.co, Summary: Startup investor asking about proposal details, Reason: Time-sensitive investment decision"""

    # ACTION: Call the real classify_emails function from agent.py
    results = agent.classify_emails(
        sample_headers,
        learning_context,
        llm
    )

    # ASSERT: With learning context, Claude should classify as URGENT
    assert results[0]["urgency"] == "URGENT", f"Should learn from context, got {results[0]['urgency']}"

    print(f"\n✅ Claude incorporated learning context:")
    print(f"  Email classified as: {results[0]['urgency']} / {results[0]['category']}")


if __name__ == "__main__":
    print("Running integration tests with REAL Claude API...\n")

    try:
        test_claude_classifies_emails_correctly()
        test_claude_respects_learning_context()
        print("\n✅ All integration tests passed!")
    except json.JSONDecodeError as e:
        print(f"\n❌ Claude returned invalid JSON: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
