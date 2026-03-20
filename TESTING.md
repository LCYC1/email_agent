# Testing Guide

## Quick Start

```bash
# Run all tests (skips expensive integration tests)
poetry run pytest tests/ -v

# Run only database tests
poetry run pytest tests/test_db.py -v

# Run with coverage report
poetry run pytest tests/ --cov=src --cov-report=html
```

## Test Types

### Unit Tests (Fast, Free)
**Location:** `tests/test_db.py`

Tests database operations in isolation:
- Flagging emails
- Unflagging emails
- Retrieving flagged emails

**Run:**
```bash
poetry run pytest tests/test_db.py -v
```

**Cost:** Free (uses temporary SQLite database, no API calls)
**Time:** < 1 second

---

### Integration Tests (Slower, Costs Money)
**Location:** `tests/test_agent.py`

Tests email classification with REAL Claude API:
- Claude parses email headers correctly
- Claude respects learning context
- Classifications are sensible

**Skipped by default** to save costs (~$0.002 per run).

**Run integration tests:**

**PowerShell:**
```powershell
$env:RUN_INTEGRATION_TESTS="true"
poetry run pytest tests/test_agent.py -v
```

**Bash:**
```bash
RUN_INTEGRATION_TESTS=true poetry run pytest tests/test_agent.py -v
```

**Cost:** ~$0.002 per test run (Haiku is very cheap)
**Time:** 5-10 seconds (API latency)

---

## Common Commands

```bash
# Run all tests, stop on first failure
poetry run pytest tests/ -x

# Run tests matching a pattern
poetry run pytest tests/ -k "flag" -v

# Run with verbose output + coverage
poetry run pytest tests/ -v --cov=src

# Generate HTML coverage report
poetry run pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

## GitHub Actions

Tests run automatically on every push:
- **Unit tests:** Always run (fast, free)
- **Integration tests:** Skipped by default (no cost in CI)

To manually trigger full tests on GitHub:
1. Go to Actions tab
2. Click "Tests" workflow
3. Click "Run workflow"
4. Select branch
5. Check logs to see integration tests run

---

## Cost Breakdown

| Test | Cost | Speed |
|------|------|-------|
| All unit tests | Free | < 1s |
| Single integration test | ~$0.001 | 5-10s |
| All tests (with integration) | ~$0.002 | 10-15s |

## Debugging Failed Tests

**If test fails, add verbose output:**
```bash
poetry run pytest tests/test_name.py -vv -s
```

**If integration test fails with JSON error:**
- Claude might return unexpected format
- Check the actual response in the error message
- Update the test or prompt accordingly

**If test hangs:**
- Press Ctrl+C to cancel
- Check for infinite loops in code

---

## Writing New Tests

Pattern for all tests:
```python
def test_something_does_something():
    # SETUP: Prepare test data
    # ACTION: Do the thing
    # ASSERT: Verify it worked
    assert result == expected
```

Example:
```python
def test_emails_are_classified():
    # SETUP
    emails = [{"index": 0, "subject": "Urgent: Meeting"}]

    # ACTION
    classified = classify(emails)

    # ASSERT
    assert classified[0]["urgency"] == "URGENT"
```

---

## Tips

- **Local development:** Run `poetry run pytest tests/` often (cheap, fast)
- **Before pushing:** Run integration tests once to verify Claude works
- **In CI/CD:** Unit tests only (GitHub Actions runs on every commit)
- **Monitor costs:** Integration tests cost ~$1/year if run weekly

---

## Troubleshooting

**"No tests collected"**
- Check test files are in `tests/` directory
- Check test functions start with `test_`

**"A_API_KEY not set"**
- Create `.env` file with your API key
- Integration tests skip gracefully if key missing

**"poetry: command not found"**
- Install poetry: `pip install poetry`
- Or use `python -m poetry` instead

**Tests pass locally but fail in GitHub Actions**
- GitHub Actions uses Python 3.10 (check pyproject.toml)
- Missing dependencies? Check poetry.lock is committed
- API issues? Check logs for actual error message
