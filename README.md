# Email Triage Agent

An intelligent email classification system powered by Claude AI that automatically categorizes, summarizes, and learns from your emails.

## Features

- **Intelligent Classification** — Uses Claude Haiku to classify emails by urgency (URGENT/FYI/IGNORE) and category (Personal, Advertisement, Spam, Entertainment, Knowledge and News, Payment confirmation, Rest)
- **Multi-Account Support** — Fetch emails from multiple Gmail and Outlook/Hotmail accounts simultaneously
- **Email Summarization** — Get quick summaries of emails on-demand
- **Learning System** — Flag emails to provide feedback; the AI learns from your corrections for better future classifications
- **Web UI** — Clean, responsive interface with filtering, search, and email expansion
- **No API Billing** — Uses Claude Code Pro subscription, avoiding direct API costs

## Tech Stack

- **Backend:** Python, FastAPI, LangChain
- **Frontend:** Vanilla JavaScript, HTML/CSS
- **Database:** SQLite (for learning memory)
- **AI Model:** Claude Haiku 4.5
- **Dependency Management:** Poetry
- **CI/CD:** GitHub Actions
- **Deployment:** Docker (planned)

## Requirements

- Python 3.10+
- Poetry (for dependency management)
- Gmail/Outlook accounts with IMAP enabled
- Claude API key (from Anthropic)

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/email-agent.git
cd email-agent
```

### 2. Install dependencies
```bash
pip install poetry
poetry install
```

### 3. Configure environment
Create a `.env` file in the project root:
```
A_API_KEY=your-anthropic-api-key
ACCOUNTS=email1@gmail.com:password1:true,email2@outlook.com:password2:false
```

**Account format:** `email:password:keep_unread(true/false)`

### Gmail Setup
1. Enable IMAP in Gmail settings
2. Generate App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Use the 16-character app password in `.env`

### Outlook/Hotmail Setup
1. Enable IMAP in Outlook settings
2. Use your email password in `.env`

## Usage

### Run locally
```bash
# Development
poetry install
python -m uvicorn src.api:app --reload --port 8000

# Production
poetry install --only main
python -m uvicorn src.api:app --port 8000
```

Then open `http://localhost:8000` in your browser.

### Fetch and classify emails
```bash
# Fetch emails from configured accounts
python src/fetch_mails.py

# Classify emails using Claude AI
python src/agent.py
```

### Run tests
```bash
poetry run pytest --cov=src
```

## Project Structure

```
email-agent/
├── src/
│   ├── api.py              # FastAPI server, REST endpoints
│   ├── agent.py            # Email classification with Claude
│   ├── fetch_mails.py      # IMAP email fetching
│   ├── db.py               # SQLite database for flagged emails
│   └── test.py             # Basic connectivity test
├── static/
│   └── index.html          # Web UI
├── emails/
│   └── emails.json         # Fetched emails (runtime)
├── logs/
│   └── *.log               # Application logs
├── memory.db               # SQLite database (runtime)
├── pyproject.toml          # Dependency definitions
├── poetry.lock             # Locked dependency versions
├── .gitignore
├── .github/
│   └── workflows/
│       └── test.yml        # GitHub Actions CI/CD
└── README.md
```

## How It Works

### 1. Email Fetching (`fetch_mails.py`)
- Connects to Gmail/Outlook via IMAP
- Fetches unread emails from the last 7 days (configurable)
- Saves email headers and bodies to `emails/emails.json`

### 2. Email Classification (`agent.py`)
- Sends email headers to Claude Haiku with a classification prompt
- Includes learning context from previously flagged emails
- Claude returns JSON with urgency and category for each email
- Updates `emails.json` with classification results

### 3. Web UI (`static/index.html`)
- Displays classified emails with filtering by category
- Click emails to expand and see full body
- "Summarize" button calls Claude for on-demand summaries
- "Flag" button marks emails for learning feedback

### 4. Learning Loop (`db.py`)
- Flagged emails stored in SQLite database
- Agent.py retrieves flagged emails on next run
- Includes them in the classification prompt: "Learn from these corrections:"
- AI improves classifications based on your feedback

## API Endpoints

- `GET /` — Redirects to web UI
- `GET /emails` — Get all emails
- `GET /emails/urgent` — Get urgent emails only
- `GET /emails/{index}/summary` — Get/generate email summary
- `POST /flag/{index}` — Flag email for learning
- `DELETE /flag/{index}` — Unflag email
- `GET /flagged` — List all flagged emails
- `POST /refresh` — Fetch and classify emails

## Development

### Adding dependencies
```bash
poetry add package-name              # Production
poetry add --group dev package-name  # Development
```

### Running tests
```bash
poetry run pytest                    # Run all tests
poetry run pytest --cov=src          # With coverage
poetry run pytest -v                 # Verbose output
```

## Deployment

### Docker
```bash
docker build -t email-agent .
docker run -p 8000:8000 --env-file .env email-agent
```

### Environment variables
```
A_API_KEY=your-anthropic-api-key
ACCOUNTS=email1@gmail.com:password1:true
```

## Learning Notes

This project demonstrates:
- **LLM integration** — Using Claude via LangChain
- **Feedback loops** — Teaching AI from user corrections
- **Full-stack development** — Python backend + vanilla JS frontend
- **Email protocols** — IMAP for Gmail and Outlook
- **Database design** — SQLite for persistent memory
- **Dependency management** — Poetry for Python projects
- **CI/CD** — GitHub Actions for automated testing
- **Clean architecture** — Separation of concerns (fetch, classify, serve, learn)

## Future Improvements

- [ ] OAuth2 authentication (instead of passwords)
- [ ] Reply drafting for urgent emails
- [ ] Advanced filtering and search
- [ ] Email attachment handling
- [ ] Multi-user support with authentication
- [ ] Rate limiting and caching

## License

MIT
