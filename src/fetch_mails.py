"""
Fetches emails from Gmail and Outlook/Hotmail accounts via IMAP.

Setup:
- Add to email-agent/.env:
  ACCOUNTS=account1@gmail.com:password1:true,account2@hotmail.com:password2:false

  Format per account: email:password:keep_unread(true/false)

- Gmail: enable IMAP + generate App Password at myaccount.google.com/apppasswords
- Hotmail/Outlook: enable IMAP in Outlook settings
"""

import imaplib
import email
import email.policy
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

log_dir = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "fetch_mails.log")),
        logging.FileHandler(os.path.join(log_dir, "app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../emails")
MAX_EMAILS = 50  # per account

IMAP_SERVERS = {
    "gmail.com": "imap.gmail.com",
    "hotmail.com": "imap-mail.outlook.com",
    "outlook.com": "imap-mail.outlook.com",
    "live.com": "imap-mail.outlook.com",
}

GMAIL_DOMAINS = {"gmail.com"}


def build_search_query(domain):
    since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    if domain in GMAIL_DOMAINS:
        return 'X-GM-RAW "is:unread newer_than:7d"'
    return f'(UNSEEN SINCE {since})'


def get_imap_config(address):
    domain = address.split("@")[-1].lower()
    if domain not in IMAP_SERVERS:
        raise SystemExit(f"Unsupported email domain: {domain}")
    return IMAP_SERVERS[domain], build_search_query(domain)


def fetch_account(address, password, keep_unread=False):
    domain = address.split("@")[-1].lower()
    server, search_query = get_imap_config(address)
    logger.info(f"Connecting as {address} ({server})...")
    mail = imaplib.IMAP4_SSL(server)
    mail.login(address, password)

    if domain in GMAIL_DOMAINS:
        mail.select('"[Gmail]/All Mail"')
    else:
        mail.select("inbox")

    _, data = mail.search(None, search_query)
    email_ids = data[0].split()
    recent_ids = email_ids[-MAX_EMAILS:]

    logger.info(f"Fetching {len(recent_ids)} emails...")
    emails = []

    for eid in reversed(recent_ids):
        _, msg_data = mail.fetch(eid, "(RFC822)")
        if keep_unread:
            mail.store(eid, '-FLAGS', '\\Seen')
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw, policy=email.policy.default)

        subject = msg.get("Subject", "(no subject)")
        sender = msg.get("From", "")
        date = msg.get("Date", "")
        body_part = msg.get_body(preferencelist=("plain", "html"))
        body = body_part.get_content() if body_part else ""

        emails.append({
            "account": address,
            "from": sender,
            "date": date,
            "subject": subject,
            "body": body.strip(),
            "urgency": "",
            "category": "",
            "summary": ""
        })

        logger.debug(f"  {subject[:60]}")

    mail.logout()
    return emails


def fetch_emails():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    accounts_env = os.getenv("ACCOUNTS", "")
    if not accounts_env:
        raise SystemExit("ACCOUNTS not set in .env")

    accounts = [a.strip().split(":") for a in accounts_env.split(",")]

    all_emails = []
    for parts in accounts:
        address, password = parts[0], parts[1]
        keep_unread = len(parts) > 2 and parts[2].lower() == "true"
        all_emails.extend(fetch_account(address, password, keep_unread))

    for i, e in enumerate(all_emails):
        e["index"] = i

    output_file = os.path.join(OUTPUT_DIR, "emails.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_emails, f, ensure_ascii=False, indent=2)

    logger.info(f"Done. {len(all_emails)} emails saved to: {output_file}")


if __name__ == "__main__":
    fetch_emails()
    sys.exit(0)
