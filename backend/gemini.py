import json
import time
from typing import Optional

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

genai.configure(api_key=GEMINI_API_KEY)

CLASSIFY_SYSTEM_PROMPT = """You are classifying an inbound email to a B2B sales inbox. Return ONLY a JSON object, no markdown fences, no commentary.

Team and scope:
- u_aarti (Sales-Enterprise): RFPs, RFIs, tenders, inbound deals above ₹10,00,000
- u_rohit (Sales-SMB): product enquiries, demo requests, deals at or below ₹10,00,000
- u_meera (Marketing): webinars, event/conference sponsorships, content collaborations, PR, media
- u_karan (Alliances): reseller, channel partner, technology integration proposals
- u_divya (Finance): invoices, POs, payment reminders, GST/vendor billing
- u_triage: genuinely ambiguous items, or items spanning two departments' scope

Critical judgment calls:
1. DIRECTION OF INTENT: is this email FROM a prospect/customer who needs something FROM us, or
   FROM a vendor/agency trying to SELL something TO us (SEO agencies, marketing agencies, cold
   outreach)? Only the former is actionable. Vendor pitches that use marketing-adjacent language
   ("content marketing", "webinar promotion", "PR outreach") are still spam if THEY are selling
   TO us — do not route these to u_meera.
2. Out-of-office auto-replies and newsletters/mailing-list content are NEVER actionable, even
   if they mention business topics.
3. Do NOT infer a company_name from an email domain unless the company is unambiguously named
   in the body/signature. Leave null rather than guess.
4. Do NOT infer a deal_value_inr or due_date that isn't literally stated or a clear calculation
   from stated figures. Leave null rather than guess.
5. Flag is_psu_or_govt=true if this is a government body, PSU, or public tender notice.
6. If the email genuinely spans two departments' scope with no way to prioritize one (e.g. both
   a sales evaluation AND a marketing ask with no dominant one), set category="triage",
   assignee_id="u_triage", and confidence <= 0.5, explaining both asks in reasoning.

Return exactly this JSON shape:
{
  "is_actionable": true/false,
  "skip_reason": "out_of_office" | "newsletter" | "spam" | null,
  "category": "enterprise_rfp" | "smb_enquiry" | "marketing" | "alliances" | "finance" | "triage" | null,
  "assignee_id": "u_aarti" | "u_rohit" | "u_meera" | "u_karan" | "u_divya" | "u_triage" | null,
  "is_psu_or_govt": true/false,
  "due_date_raw": "<verbatim date phrase from email, or null>",
  "deal_value_raw": "<verbatim amount phrase from email, or null>",
  "company_name": "<company name if unambiguous, else null>",
  "title": "<short task title, <=10 words>",
  "description": "<1-2 sentence summary of what's needed>",
  "confidence": 0.0-1.0,
  "reasoning": "<one sentence: why this routing>"
}
"""

CHAT_QUERY_SYSTEM_PROMPT = """You translate a natural-language question about a processed email
batch into ONE structured query. Return ONLY JSON, no markdown fences.

Available query types:
- "count_by_category": no params (Use this for general category counts, proposals, RFPs, marketing vs spam, etc.)
- "count_skipped_by_reason": no params
- "list_triage": no params
- "spurious_rate": no params
- "compound_filter": params: {"priority": "high"|"medium"|"low"|null, "confidence_lt": float|null}
- "sum_deal_value": no params (sums deal_value_inr across category=enterprise_rfp tasks)
- "thread_update_history": no params (threads with >1 update)
- "count_field_value": params: {"field": "category"|"skip_reason", "value": "<the value asked about>"}
  (use this ONLY for specific terms like "GST refund" or custom terms that are NOT general categories like proposal/RFP)
- "unsupported": params: {"reason": "<why this can't be answered, e.g. it asks for an action>"}

Return exactly: {"query_type": "...", "params": {...}}
If the question asks you to DO something (send an email, create a task manually, etc.) rather than
ask about existing data, use "unsupported".
"""


def _call_gemini(prompt: str, system: str, retries: int = 5) -> str:
    model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system)
    last_err = None
    for attempt in range(retries):
        try:
            resp = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json", "temperature": 0.1},
            )
            return resp.text
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str or "Quota exceeded" in err_str:
                # If rate limit (15 RPM), wait 4.5 seconds so rate limit bucket resets
                time.sleep(4.5 * (attempt + 1))
            else:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff for network glitches
    raise RuntimeError(f"Gemini call failed after {retries} attempts: {last_err}")


def classify_email(subject: str, body: str, from_name: str, from_email: str, cc: list) -> dict:
    prompt = (
        f"From: {from_name} <{from_email}>\nCC: {cc}\nSubject: {subject}\n\nBody:\n{body}"
    )
    raw = _call_gemini(prompt, CLASSIFY_SYSTEM_PROMPT)
    return json.loads(raw)


def nl_to_query(question: str) -> dict:
    raw = _call_gemini(question, CHAT_QUERY_SYSTEM_PROMPT)
    return json.loads(raw)


def phrase_answer(question: str, query_result: dict) -> str:
    """Stage 3: Gemini is given ONLY the already-computed result, never
    the raw emails, and is explicitly told not to add numbers that
    aren't in query_result."""
    system = (
        "You answer a question using ONLY the JSON data provided. Never state a number that "
        "isn't present in the data. If a count is 0, say so plainly and directly. If the data "
        "indicates the question is unsupported or out of scope, say so plainly and do not "
        "attempt to answer anyway. Keep the answer to 2-3 sentences, no markdown."
    )
    prompt = f"Question: {question}\n\nData: {json.dumps(query_result)}"
    model = genai.GenerativeModel(GEMINI_MODEL, system_instruction=system)
    resp = model.generate_content(prompt, generation_config={"temperature": 0.1})
    return resp.text.strip()