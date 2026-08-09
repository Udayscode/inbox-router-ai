import re
from datetime import datetime, date, timedelta
from typing import Optional


def parse_inr_amount(text: str) -> Optional[int]:
    """Parse Indian currency shorthand into integer rupees.
    Handles: 'Rs. 25 lakhs', '₹4,00,000', '1.2 cr', '6,50,000', '25L'.
    Returns None if nothing parseable is found — callers must NOT guess.
    """
    if not text:
        return None
    t = text.lower().replace(",", "")

    # crore: "1.2 cr", "1.2 crore", "1.2crore"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(cr|crores?)\b", t)
    if m:
        return round(float(m.group(1)) * 1_00_00_000)

    # lakh: "25 lakhs", "25L", "25 lac"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(lakhs?|lacs?|l)\b", t)
    if m:
        return round(float(m.group(1)) * 1_00_000)

    # raw rupee figure: "rs. 650000", "₹1,18,000" (commas already stripped above)
    m = re.search(r"(?:rs\.?|inr|₹)\s*(\d{4,})", t)
    if m:
        return int(m.group(1))

    return None


_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def parse_due_date(raw_phrase: Optional[str], received_at: datetime) -> Optional[str]:
    """Parse a verbatim date phrase (as extracted by the LLM from the
    email text) into 'YYYY-MM-DD'. Deliberately conservative: handles the
    formats that actually show up in the worked examples (explicit dates,
    'tomorrow', 'today'), and returns None for anything vague ('next
    week', 'soon') rather than guess — a wrong invented date is worse
    than no date per spec §5.2.
    """
    if not raw_phrase:
        return None
    t = raw_phrase.strip().lower()

    if "tomorrow" in t:
        return (received_at + timedelta(days=1)).strftime("%Y-%m-%d")
    if "today" in t or "eod" in t and "tomorrow" not in t:
        return received_at.strftime("%Y-%m-%d")

    # ISO: 2026-08-12
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            pass

    # DD-MM-YYYY or DD/MM/YYYY
    m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            pass

    # "12th August 2026" / "12 August 2026" / "11th Aug"
    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]+)\s*(\d{4})?", t)
    if m:
        d = int(m.group(1))
        month_name = m.group(2)
        year = int(m.group(3)) if m.group(3) else received_at.year
        mo = _MONTHS.get(month_name)
        if mo:
            try:
                candidate = date(year, mo, d)
                # If the parsed date already passed relative to received_at
                # and no year was stated, assume next year (deadline can't
                # be in the past).
                if not m.group(3) and candidate < received_at.date():
                    candidate = date(year + 1, mo, d)
                return candidate.isoformat()
            except ValueError:
                pass

    # Day-only, no month stated: "20th ko hai", "by the 20th". Assume the
    # current month relative to received_at; roll to next month if that
    # day has already passed. This is a deliberate assumption (documented
    # in DECISIONS.md) — safer than leaving a clearly-intended deadline
    # null, since the day number alone is unambiguous within a ~30 day
    # window of the email.
    m = re.search(r"^\s*(\d{1,2})(?:st|nd|rd|th)?\s*$", t.strip()) or re.search(r"\bthe\s+(\d{1,2})(?:st|nd|rd|th)\b", t)
    if m:
        d = int(m.group(1))
        if 1 <= d <= 31:
            year, month = received_at.year, received_at.month
            try:
                candidate = date(year, month, d)
                if candidate < received_at.date():
                    month += 1
                    if month > 12:
                        month, year = 1, year + 1
                    candidate = date(year, month, d)
                return candidate.isoformat()
            except ValueError:
                pass

    return None


def hours_until_deadline(received_at: datetime, due_date: Optional[str]) -> Optional[float]:
    """due_date is 'YYYY-MM-DD'. Returns hours between received_at and the
    END of due_date (23:59:59), or None if due_date is missing/unparseable.
    Deliberately generous (end-of-day) since business deadlines usually
    mean 'by that date', matching the worked examples (e.g. Ex.4's
    'tomorrow EOD' -> ~31h, well inside 72h)."""
    if not due_date:
        return None
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d") + timedelta(hours=23, minutes=59)
    except ValueError:
        return None
    delta = due - received_at.replace(tzinfo=None)
    return delta.total_seconds() / 3600