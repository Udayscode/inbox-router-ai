import os

# --- Identity -----------------------------------------------------------
# The candidate_id every task/log row must carry. Loaded from env so the
# same code works for anyone who clones this repo — but the deployed
# instance's .env pins it to one real email, per the spec's "byte-identical
# everywhere" rule.
CANDIDATE_ID = os.environ.get("CANDIDATE_ID", "").strip().lower()

# --- Database -------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./local_dev.db")

# --- Gemini -----------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

# --- CORS -----------------------------------------------------------------
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")

# --- Enums (single source of truth — used in Pydantic models, DB CHECK
# constraints, and validation error messages, so they can never drift
# out of sync with each other) ---------------------------------------------
ASSIGNEE_IDS = ["u_aarti", "u_rohit", "u_meera", "u_karan", "u_divya", "u_triage"]
CATEGORIES = ["enterprise_rfp", "smb_enquiry", "marketing", "alliances", "finance", "triage"]
PRIORITIES = ["high", "medium", "low"]

TEAM_ROSTER = [
    {"user_id": "u_aarti", "name": "Aarti Menon", "department": "Sales — Enterprise",
     "scope": "RFPs, RFIs, tenders, and inbound deals above ₹10,00,000"},
    {"user_id": "u_rohit", "name": "Rohit Sharma", "department": "Sales — SMB",
     "scope": "Product enquiries, demo requests, deals at or below ₹10,00,000"},
    {"user_id": "u_meera", "name": "Meera Iyer", "department": "Marketing",
     "scope": "Webinars, event and conference sponsorships, content collaborations, PR and media"},
    {"user_id": "u_karan", "name": "Karan Doshi", "department": "Alliances",
     "scope": "Reseller, channel partner, and technology integration proposals"},
    {"user_id": "u_divya", "name": "Divya Rao", "department": "Finance",
     "scope": "Invoices, purchase orders, payment reminders, GST and vendor billing"},
    {"user_id": "u_triage", "name": "Triage Queue", "department": "Operations",
     "scope": "Ambiguous items requiring human review"},
]


def normalize_candidate_id(value: str) -> str:
    """Single normalisation function used on every write AND every read
    path, so priya+fde@gmail.com never silently diverges from
    priya@gmail.com. Per spec §2, only lower+trim — no alias stripping,
    since that's on the caller to send clean."""
    return (value or "").strip().lower()