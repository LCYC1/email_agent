import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# Add src directory to path so we can import db
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
import db

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "api.log"),
        logging.FileHandler(log_dir / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
api_key = os.getenv("A_API_KEY")

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=api_key)

summary_prompt = ChatPromptTemplate.from_template("""
Summarize this email. Include all key elements (dates, amounts, actions required, names).
Keep it short for simple emails, slightly longer for important or complex ones. No fluff.

From: {sender}
Subject: {subject}
Body: {body}
""")

app = FastAPI()

db.init_db()
logger.info("Database initialized")

emails_path = Path(__file__).parent.parent / "emails" / "emails.json"
static_path = Path(__file__).parent.parent / "static"

app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
def index():
    return RedirectResponse(url="/static/index.html")


@app.get("/emails")
def get_emails():
    return json.loads(emails_path.read_text(encoding="utf-8"))


@app.get("/emails/urgent")
def get_urgent_emails():
    emails = json.loads(emails_path.read_text(encoding="utf-8"))
    return [e for e in emails if e["urgency"] == "URGENT"]


@app.get("/emails/{index}/summary")
def get_email_summary(index: int):
    logger.info(f"Generating summary for email index {index}")
    emails = json.loads(emails_path.read_text(encoding="utf-8"))
    email = next((e for e in emails if e["index"] == index), None)
    if not email:
        logger.warning(f"Email index {index} not found")
        raise HTTPException(status_code=404, detail="Email not found")

    if email.get("summary"):
        logger.info(f"Using cached summary for email {index}")
        return {"summary": email["summary"]}

    logger.info(f"Calling LLM to summarize email {index}")
    chain = summary_prompt | llm
    response = chain.invoke({"sender": email["from"], "subject": email["subject"], "body": email["body"]})
    email["summary"] = response.content.strip()

    emails_path.write_text(json.dumps(emails, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Summary saved for email {index}")
    return {"summary": email["summary"]}


@app.post("/refresh")
def refresh_emails():
    logger.info("Refresh requested")
    try:
        src_dir = Path(__file__).parent
        logger.info("Running fetch_mails.py")
        result = subprocess.run([
            "python", str(src_dir / "fetch_mails.py")
        ], capture_output=True, text=True)
        logger.info(f"fetch_mails stdout: {result.stdout}")
        if result.returncode != 0:
            logger.error(f"fetch_mails stderr: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"fetch_mails failed: {result.stderr}")

        logger.info("Running agent.py")
        result = subprocess.run([
            "python", str(src_dir / "agent.py")
        ], capture_output=True, text=True)
        logger.info(f"agent stdout: {result.stdout}")
        if result.returncode != 0:
            logger.error(f"agent stderr: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"agent failed: {result.stderr}")
        logger.info("Refresh completed successfully")
        return {"status": "refreshed"}
    except subprocess.CalledProcessError as e:
        logger.error(f"Refresh1 failed: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {e}")


@app.get("/emails/category/{category}")
def get_emails_by_category(category: str):
    emails = json.loads(emails_path.read_text(encoding="utf-8"))
    return [e for e in emails if e["category"].lower() == category.lower()]


@app.post("/flag/{index}")
def flag_email(index: int, is_urgent: bool = True, reason: str = ""):
    logger.info(f"Flagging email {index} (urgent={is_urgent})")
    emails = json.loads(emails_path.read_text(encoding="utf-8"))
    email = next((e for e in emails if e["index"] == index), None)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    db.flag_email(index, email["from"], email["subject"][:100], is_urgent, reason)
    return {"status": "flagged"}


@app.delete("/flag/{index}")
def unflag_email(index: int):
    logger.info(f"Unflagging email {index}")
    db.unflag_email(index)
    return {"status": "unflagged"}


@app.get("/flagged")
def get_flagged():
    logger.info("Retrieving flagged emails")
    return db.get_flagged_emails()
