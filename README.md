# Email Triage Agent

An intelligent email classification system powered by Claude AI that automatically categorizes, summarizes, and learns from your emails.

## Features

- **Intelligent Classification** — Uses Claude Haiku to classify emails by urgency (URGENT/FYI/IGNORE) and category (Personal, Advertisement, Spam, Entertainment, Knowledge and News, Payment confirmation, Rest)
- **Multi-Account Support** — Fetch emails from multiple Gmail and Outlook/Hotmail accounts simultaneously
- **Email Summarization** — Get quick summaries of emails on-demand
- **Learning System** — Flag emails to provide feedback; the AI learns from your corrections for better future classifications
- **Web UI** — Clean, responsive interface with filtering, search, and email expansion

## Tech Stack

- **Backend:** Python, FastAPI, LangChain
- **Frontend:** JavaScript, HTML/CSS
- **Database:** SQLite (for learning memory)
- **AI Model:** Claude Haiku 4.5
- **Dependency Management:** Poetry
- **CI/CD:** GitHub Actions
- **Deployment:** Docker

## Requirements

- Python 3.10+ (for local development)
- Poetry (for dependency management)
- Docker (for containerized deployment)
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
-Might be difficult to do -> MS Graph API
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

### Docker (Recommended for production)

**Quick start:**
```bash
# Create .env with your credentials
echo "A_API_KEY=your-anthropic-api-key" > .env
echo "ACCOUNTS=email@gmail.com:password:true" >> .env

# Run production
docker compose -f docker-compose.yml up

# Or development with hot reload
docker compose up
```

Open `http://localhost:8000` (or your configured PORT).

**Environment variables:**
```
A_API_KEY=your-anthropic-api-key
ACCOUNTS=email@gmail.com:password:true,email2@outlook.com:password2:false
PORT=8000  (default)
```

Data persists in `data/`, `emails/`, and `logs/` directories via volume mounts.

**Stop containers:**
```bash
docker compose down
```

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
├── data/                   # Runtime data (gitignored)
│   └── memory.db           # SQLite database
├── emails/
│   └── emails.json         # Fetched emails (runtime, gitignored)
├── logs/
│   └── *.log               # Application logs (gitignored)
├── Dockerfile              # Multi-stage build (dev/prod)
├── docker-compose.yml      # Production compose config
├── docker-compose.override.yml  # Development overrides (hot reload)
├── .dockerignore           # Docker ignore rules
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

### Docker (Recommended)

**Development (with hot reload):**
```bash
docker compose up
```

**Production (optimized build):**
```bash
docker compose -f docker-compose.yml up
```

**Build and run manually:**
```bash
docker build -t email-agent:latest --target prod .
docker run -p 8000:8000 --env-file .env email-agent:latest
```

**Push to Docker Hub:**
```bash
docker tag email-agent:latest yourusername/email-agent:latest
docker push yourusername/email-agent:latest
```

### Environment variables
Create a `.env` file (never commit this):
```
A_API_KEY=your-anthropic-api-key
ACCOUNTS=email1@gmail.com:password1:true,email2@outlook.com:password2:false
PORT=8000
```

### Cloud Deployment
- **AWS:** ECS, Fargate, or EC2
- **Heroku:** Use `docker` buildpack
- **DigitalOcean:** App Platform (Docker-native)
- **Azure:** Container Instances or App Service
- **GCP:** Cloud Run or GKE (Kubernetes)

### Kubernetes (Google Cloud GKE)

Deploy to a GKE cluster:

```bash
# 1. Build and push Docker image to Docker Hub
docker build -t email-agent:latest .
docker login
docker tag email-agent:latest fishsay/email-agent:latest
docker push fishsay/email-agent:latest

# 2. Get credentials for your GKE cluster
gcloud container clusters get-credentials agent-cluster --region europe-west1

# 3. Create deployment with environment variables OR use GC console to create cluster (Autopilot for costs) and deploy image from docker hub
kubectl create deployment email-agent --image=fishsay/email-agent:latest
kubectl set env deployment/email-agent \
  ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  ACCOUNTS=$ACCOUNTS \
  PORT=8000

# 4. Access locally via port-forward
kubectl port-forward deployment/email-agent 8000:8000
# Visit http://localhost:8000
```

**Redeploy after code changes:**
```bash
docker build -t email-agent:latest .
docker tag email-agent:latest fishsay/email-agent:latest
docker push fishsay/email-agent:latest
kubectl rollout restart deployment/email-agent -n default
```

**Monitor:**
```bash
kubectl get pods              # List running pods
kubectl logs deployment/email-agent  # View logs
```

### CI/CD (GitHub Actions)

Automated testing, building, and deployment:

```bash
# 1. Set up GitHub secrets
# Go to: repo → Settings → Secrets and variables → Actions
# Add secrets:
#   DOCKER_USERNAME = your Docker Hub username
#   DOCKER_PASSWORD = your Docker Hub password

# 2. Push code to main branch
git push origin main

# 3. GitHub Actions automatically:
#   - Runs tests (pytest)
#   - Builds Docker image
#   - Pushes to Docker Hub
#   - (You manually restart K8s when ready)
```

**Redeploy to K8s after new image:**
```bash
kubectl rollout restart deployment/email-agent -n default
```

All support `docker-compose.yml` or direct Docker image deployment.

## Learning Notes

This project demonstrates:
**LLM integration** — Using Claude via LangChain for email classification
**Feedback loops** — Teaching AI from user corrections to improve over time
**Full-stack development** — Python FastAPI backend + vanilla JS frontend
**Email protocols** — IMAP for Gmail and Outlook multi-account support
**Database design** — SQLite for persistent memory of user feedback
**Dependency management** — Poetry for reproducible Python dependencies
**CI/CD** — GitHub Actions for automated testing on every push
**Containerization** — Docker for consistent development/production environments
**SSH authentication** — Secure git operations without token management
**Clean architecture** — Separation of concerns (fetch → classify → serve → learn)

## Future Improvements

- [ ] OAuth2 authentication (instead of passwords)
- [ ] Reply drafting for urgent emails
- [ ] Advanced filtering and search
- [ ] Email attachment handling
- [ ] Multi-user support with authentication
- [ ] Rate limiting and caching

## License

MIT
