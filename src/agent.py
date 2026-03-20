import os
import json
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
import db

log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "agent.log"),
        logging.FileHandler(log_dir / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
api_key = os.getenv("A_API_KEY")

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", api_key=api_key)

categorize_prompt = ChatPromptTemplate.from_template("""
You are an email triage assistant.
For each email, classify urgency and category based on the headers only.

Urgency: URGENT (if it is something that should be replied within 1 day), FYI, or IGNORE
Category: one of Personal (if it is from one person to me or sensitive information) / Advertisement / Spam / Entertainment / Knowledge and News / Payment confirmation / Rest

IMPORTANT - Learn from past corrections:
{learning_context}

Return a JSON array only, no explanation. Example:
[{{"index": 0, "urgency": "URGENT", "category": "Personal"}}]

Emails:
{emails}
""")

chain = categorize_prompt | llm

emails_path = Path(__file__).parent.parent / "emails" / "emails.json"

if not emails_path.exists():
    raise SystemExit("emails/emails.json not found. Run fetch_gmail.py first.")

emails = json.loads(emails_path.read_text(encoding="utf-8"))

# Send only headers to the LLM
headers = [{"index": e["index"], "from": e["from"], "date": e["date"], "subject": e["subject"]} for e in emails]

# Get learning context from flagged emails
flagged = db.get_urgent_flagged()
if flagged:
    learning_context = "Emails that were flagged as URGENT:\n" + "\n".join([
        f"- From: {f['sender']}, Summary: {f['summary']}" + (f", Reason: {f['reason']}" if f.get('reason') else "")
        for f in flagged
    ])
else:
    learning_context = "No flagged emails yet. Use your best judgment."

logger.info(f"Triaging {len(emails)} emails... (with {len(flagged)} learning examples)")
response = chain.invoke({
    "emails": json.dumps(headers, indent=2),
    "learning_context": learning_context
})

logger.info(f"Tokens used — input: {response.usage_metadata['input_tokens']}, output: {response.usage_metadata['output_tokens']}, total: {response.usage_metadata['total_tokens']}")

# Strip markdown code blocks if present and parse
content = response.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
results = json.loads(content)
result_map = {r["index"]: r for r in results}

for e in emails:
    result = result_map.get(e["index"], {})
    e["urgency"] = result.get("urgency", "")
    e["category"] = result.get("category", "")

emails_path.write_text(json.dumps(emails, ensure_ascii=False, indent=2), encoding="utf-8")
logger.info("Done. Urgency and category updated in emails/emails.json")
