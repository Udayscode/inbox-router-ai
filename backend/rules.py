"""
Deterministic rule engine — applied AFTER Gemini's classification, never
instead of it. Gemini decides category/intent/direction (needs judgment,
world knowledge, language handling). This module decides priority,
assignee overrides, and value/date parsing (needs arithmetic, not
judgment) — because trusting an LLM to do date math or apply the PSU
override reliably is exactly the kind of thing that causes silent
scoring failures.

Deal-value threshold and PSU override map to spec §4; the 72h escalation
is the "Additional rules" bullet.
"""

from datetime import datetime
from typing import Optional

from parsing import parse_inr_amount, hours_until_deadline

DEAL_VALUE_THRESHOLD_INR = 10_00_000  # ₹10,00,000


def apply_rules(
    *,
    llm_assignee_id: str,
    llm_category: str,
    llm_priority_signal: str,
    is_psu_or_govt: bool,
    deal_value_inr: Optional[int],
    due_date: Optional[str],
    received_at: datetime,
) -> dict:
    """Returns the FINAL {assignee_id, priority} after deterministic
    overrides. llm_* values are Gemini's first pass; this function may
    override them.
    """
    assignee_id = llm_assignee_id
    priority = llm_priority_signal

    # Rule 3: PSU/government tenders always go to Aarti, regardless of
    # value or what the LLM guessed. This beats the value-based rule —
    # it's the specific trap in Example 3.
    if is_psu_or_govt:
        assignee_id = "u_aarti"

    # Value-based routing for RFP-shaped emails only (never override a
    # non-sales category like marketing/finance/alliances just because a
    # number appears — that's the Example 4/5/6 trap in reverse).
    if llm_category == "enterprise_rfp" and deal_value_inr is not None and not is_psu_or_govt:
        assignee_id = "u_aarti" if deal_value_inr > DEAL_VALUE_THRESHOLD_INR else "u_rohit"

    # 72h deadline escalation — overrides whatever priority the LLM
    # assigned, for ANY category (spec says "regardless of owner").
    hrs = hours_until_deadline(received_at, due_date)
    if hrs is not None and 0 <= hrs <= 72:
        priority = "high"

    return {"assignee_id": assignee_id, "priority": priority}


def extract_deal_value(*texts: str) -> Optional[int]:
    """Try each text field in order (e.g. subject then body), return the
    first successfully parsed rupee amount, or None. Never fabricates —
    absence of a parseable figure means null, per spec."""
    for t in texts:
        val = parse_inr_amount(t or "")
        if val is not None:
            return val
    return None


AUTO_REPLY_MARKERS = [
    "out of office", "automatic reply", "auto-reply", "autoreply",
    "i am currently out", "on leave", "away from my desk",
]

NEWSLETTER_MARKERS = [
    "unsubscribe", "view in browser", "you are receiving this email because",
    "manage your subscription", "newsletter",
]


def cheap_prefilter(subject: str, body: str) -> Optional[str]:
    """Fast heuristic check BEFORE spending a Gemini call. Returns a
    skip_reason string if this is obviously an auto-reply or newsletter,
    else None (meaning: still needs LLM classification — most spam is
    NOT this obvious, see Example 8, which requires understanding
    direction of intent and can't be caught by keyword matching alone)."""
    text = f"{subject}\n{body}".lower()
    if any(marker in text for marker in AUTO_REPLY_MARKERS):
        return "out_of_office"
    if any(marker in text for marker in NEWSLETTER_MARKERS):
        return "newsletter"
    return None