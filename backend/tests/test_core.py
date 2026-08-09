import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from parsing import parse_inr_amount, hours_until_deadline
from rules import apply_rules, cheap_prefilter
from schemas import validate_task_enums


# --- parsing.py -------------------------------------------------------------

def test_lakhs():
    assert parse_inr_amount("Indicative budget is Rs. 25 lakhs.") == 25_00_000

def test_crore_decimal():
    assert parse_inr_amount("Budget approx 1.2 cr allocated hai") == 1_20_00_000

def test_raw_rupee_figure():
    assert parse_inr_amount("Estimated value: Rs. 6,50,000.") == 6_50_000

def test_no_value_returns_none():
    assert parse_inr_amount("Nothing urgent, just checking in.") is None

def test_invoice_amount_not_conflated():
    # Ex.5: invoice amount is parseable but must NOT be used as deal_value —
    # that's a routing-layer decision (don't call extract_deal_value on
    # finance-category emails), this test just confirms parsing itself works.
    assert parse_inr_amount("invoice ... for Rs. 1,18,000 (incl. 18% GST)") == 1_18_000


# --- rules.py: 72h escalation -----------------------------------------------

def test_72h_escalation_triggers():
    received = datetime(2026, 8, 2, 16, 45)
    hrs = hours_until_deadline(received, "2026-08-03")
    assert hrs is not None and 0 <= hrs <= 72

def test_72h_escalation_not_triggered_for_11_days_out():
    received = datetime(2026, 8, 1, 9, 0)
    hrs = hours_until_deadline(received, "2026-08-12")
    assert hrs > 72


# --- rules.py: apply_rules against worked examples --------------------------

def test_example1_clean_rfp_medium_priority():
    out = apply_rules(
        llm_assignee_id="u_aarti", llm_category="enterprise_rfp", llm_priority_signal="medium",
        is_psu_or_govt=False, deal_value_inr=25_00_000, due_date="2026-08-12",
        received_at=datetime(2026, 8, 1, 9, 0),
    )
    assert out == {"assignee_id": "u_aarti", "priority": "medium"}

def test_example3_psu_override_beats_value_rule():
    # ₹6.5L is below threshold (-> would suggest u_rohit) but PSU override
    # forces u_aarti regardless. This is THE trap the spec calls out.
    out = apply_rules(
        llm_assignee_id="u_rohit", llm_category="enterprise_rfp", llm_priority_signal="medium",
        is_psu_or_govt=True, deal_value_inr=6_50_000, due_date="2026-08-03",
        received_at=datetime(2026, 8, 1, 14, 20),
    )
    assert out["assignee_id"] == "u_aarti"
    assert out["priority"] == "high"  # ~51h out

def test_example4_marketing_not_overridden_by_value():
    # Sponsorship email has a stated amount but category is 'marketing',
    # not 'enterprise_rfp' -> value-based override must NOT fire.
    out = apply_rules(
        llm_assignee_id="u_meera", llm_category="marketing", llm_priority_signal="high",
        is_psu_or_govt=False, deal_value_inr=4_00_000, due_date="2026-08-03",
        received_at=datetime(2026, 8, 2, 16, 45),
    )
    assert out["assignee_id"] == "u_meera"

def test_example12_hinglish_high_value_medium_priority():
    out = apply_rules(
        llm_assignee_id="u_aarti", llm_category="enterprise_rfp", llm_priority_signal="medium",
        is_psu_or_govt=False, deal_value_inr=1_20_00_000, due_date="2026-08-20",
        received_at=datetime(2026, 8, 5, 10, 0),
    )
    assert out == {"assignee_id": "u_aarti", "priority": "medium"}


# --- rules.py: cheap_prefilter ----------------------------------------------

def test_prefilter_catches_ooo():
    assert cheap_prefilter("Out of Office", "I am currently out of office until 14th August.") == "out_of_office"

def test_prefilter_catches_newsletter():
    assert cheap_prefilter("B2B Growth Weekly", "...  [Unsubscribe]") == "newsletter"

def test_prefilter_lets_spam_through_to_llm():
    # Example 8's SEO spam has none of the obvious markers -> must NOT be
    # caught here; it needs the LLM's "direction of intent" judgment.
    assert cheap_prefilter(
        "Quick question about your SEO",
        "We've helped 200+ SaaS companies 3x their organic traffic. Free audit attached.",
    ) is None


# --- schemas.py: exact 400 error shape --------------------------------------

def test_enum_error_shape():
    err = validate_task_enums("Aarti", "enterprise_rfp", "high")
    assert err == {
        "error": "invalid_enum_value",
        "field": "assignee_id",
        "received": "Aarti",
        "allowed": ["u_aarti", "u_rohit", "u_meera", "u_karan", "u_divya", "u_triage"],
    }

def test_valid_enums_pass():
    assert validate_task_enums("u_aarti", "enterprise_rfp", "high") is None