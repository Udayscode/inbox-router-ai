"""
Stage 2 of the chat pipeline. Takes a {query_type, params} dict (produced
by gemini.nl_to_query) and returns a plain dict of REAL numbers/rows from
the database. This is the only thing gemini.phrase_answer is allowed to
see — it never touches raw emails or re-derives a count from scratch,
which is what keeps two identical questions returning identical answers
(spec explicitly flags inconsistency as a red flag).
"""

from typing import Optional
from sqlmodel import Session, select, func
from models import Task, EmailLog


def run_query(query_type: str, params: dict, candidate_id: str, session: Session) -> dict:
    if query_type == "count_by_category":
        return _count_by_category(candidate_id, session)
    if query_type == "count_skipped_by_reason":
        return _count_skipped_by_reason(candidate_id, session)
    if query_type == "list_triage":
        return _list_triage(candidate_id, session)
    if query_type == "spurious_rate":
        return _spurious_rate(candidate_id, session)
    if query_type == "compound_filter":
        return _compound_filter(candidate_id, session, params)
    if query_type == "sum_deal_value":
        return _sum_deal_value(candidate_id, session)
    if query_type == "thread_update_history":
        return _thread_update_history(candidate_id, session)
    if query_type == "count_field_value":
        return _count_field_value(candidate_id, session, params)
    if query_type == "unsupported":
        return {"unsupported": True, "reason": params.get("reason", "This is outside what I can answer.")}
    return {"unsupported": True, "reason": f"Unrecognized query type: {query_type}"}


def _count_by_category(cid: str, s: Session) -> dict:
    rows = s.exec(
        select(Task.category, func.count()).where(Task.candidate_id == cid).group_by(Task.category)
    ).all()
    out = {cat: count for cat, count in rows}
    # Also surface marketing-lookalike spam specifically, since it's a
    # named sample question (§7.3 #2) — read from EmailLog, not Task.
    spam_count = s.exec(
        select(func.count()).where(
            EmailLog.candidate_id == cid,
            EmailLog.decision == "skipped",
            EmailLog.skip_reason == "spam",
        )
    ).one()
    out["skipped_marketing_lookalike_spam"] = spam_count
    return out


def _count_skipped_by_reason(cid: str, s: Session) -> dict:
    rows = s.exec(
        select(EmailLog.skip_reason, func.count())
        .where(EmailLog.candidate_id == cid, EmailLog.decision == "skipped")
        .group_by(EmailLog.skip_reason)
    ).all()
    return {reason or "unknown": count for reason, count in rows}


def _list_triage(cid: str, s: Session) -> dict:
    rows = s.exec(select(Task).where(Task.candidate_id == cid, Task.assignee_id == "u_triage")).all()
    return {
        "triage_count": len(rows),
        "triage_task_ids": [t.task_id for t in rows],
        "triage_reasons": {t.task_id: t.description for t in rows},
    }


def _spurious_rate(cid: str, s: Session) -> dict:
    spurious = s.exec(
        select(func.count()).where(EmailLog.candidate_id == cid, EmailLog.is_spurious_flag == True)  # noqa: E712
    ).one()
    processed = s.exec(select(func.count()).where(EmailLog.candidate_id == cid)).one()
    rate = round(spurious / processed, 4) if processed else 0.0
    return {"spurious_count": spurious, "processed": processed, "spurious_rate": rate}


def _compound_filter(cid: str, s: Session, params: dict) -> dict:
    query = select(Task).where(Task.candidate_id == cid)
    if params.get("priority"):
        query = query.where(Task.priority == params["priority"])
    if params.get("confidence_lt") is not None:
        query = query.where(Task.confidence < params["confidence_lt"])
    rows = s.exec(query).all()
    return {"matches": [{"task_id": t.task_id, "priority": t.priority, "confidence": t.confidence} for t in rows]}


def _sum_deal_value(cid: str, s: Session) -> dict:
    rows = s.exec(
        select(Task.deal_value_inr).where(Task.candidate_id == cid, Task.category == "enterprise_rfp")
    ).all()
    stated = [v for v in rows if v is not None]
    return {
        "total_deal_value_inr": sum(stated),
        "rfps_with_no_stated_value": len(rows) - len(stated),
    }


def _thread_update_history(cid: str, s: Session) -> dict:
    rows = s.exec(
        select(EmailLog.thread_id, func.count())
        .where(EmailLog.candidate_id == cid, EmailLog.decision == "updated")
        .group_by(EmailLog.thread_id)
        .having(func.count() > 0)
    ).all()
    return {"threads_updated_multiple_times": [tid for tid, _ in rows]}


def _count_field_value(cid: str, s: Session, params: dict) -> dict:
    field, value = params.get("field"), params.get("value")
    col = Task.category if field == "category" else EmailLog.skip_reason
    model = Task if field == "category" else EmailLog
    count = s.exec(select(func.count()).where(model.candidate_id == cid, col == value)).one()
    return {f"{value}_count": count}