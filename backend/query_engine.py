"""
Stage 2 of the chat pipeline. Takes a {query_type, params} dict (produced
by gemini.nl_to_query) and returns a structured dict containing both:
  - 'current_batch': real numbers/rows scoped to the specific batch uploaded
  - 'all_time': historical totals across all batches ever processed
This allows the LLM in Stage 3 to answer questions specifically about the
current batch while also remembering historical context without hallucinating.
"""

from typing import Optional
from sqlmodel import Session, select, func
from models import Task, EmailLog, Run


def run_query(
    query_type: str,
    params: dict,
    candidate_id: str,
    session: Session,
    batch_id: Optional[str] = None,
) -> dict:
    if query_type == "unsupported":
        return {"unsupported": True, "reason": params.get("reason", "This is outside what I can answer.")}

    # If no batch_id specified, resolve to the most recent batch_id / run_id
    if not batch_id:
        latest_log = session.exec(
            select(EmailLog.batch_id, EmailLog.run_id)
            .where(EmailLog.candidate_id == candidate_id)
            .order_by(EmailLog.created_at.desc())
        ).first()
        if latest_log:
            batch_id = latest_log[0] or latest_log[1]

    handlers = {
        "count_by_category": _count_by_category,
        "count_skipped_by_reason": _count_skipped_by_reason,
        "list_triage": _list_triage,
        "spurious_rate": _spurious_rate,
        "compound_filter": _compound_filter,
        "sum_deal_value": _sum_deal_value,
        "thread_update_history": _thread_update_history,
        "count_field_value": _count_field_value,
    }

    handler = handlers.get(query_type)
    if not handler:
        return {"unsupported": True, "reason": f"Unrecognized query type: {query_type}"}

    if query_type in ("compound_filter", "count_field_value"):
        return handler(candidate_id, session, params, batch_id)
    return handler(candidate_id, session, batch_id)


def _count_by_category(cid: str, s: Session, batch_id: Optional[str] = None) -> dict:
    all_rows = s.exec(
        select(Task.category, func.count()).where(Task.candidate_id == cid).group_by(Task.category)
    ).all()
    all_time = {cat: count for cat, count in all_rows}
    all_spam = s.exec(
        select(func.count()).where(
            EmailLog.candidate_id == cid,
            EmailLog.decision == "skipped",
            EmailLog.skip_reason == "spam",
        )
    ).one()
    all_time["skipped_marketing_lookalike_spam"] = all_spam
    all_time["total_tasks"] = sum(count for cat, count in all_rows)

    batch_data = {}
    if batch_id:
        batch_rows = s.exec(
            select(EmailLog.category, func.count())
            .where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
                EmailLog.decision.in_(["created", "updated"])
            )
            .group_by(EmailLog.category)
        ).all()
        batch_data = {cat or "unknown": count for cat, count in batch_rows}
        batch_spam = s.exec(
            select(func.count()).where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
                EmailLog.decision == "skipped",
                EmailLog.skip_reason == "spam",
            )
        ).one()
        batch_data["skipped_marketing_lookalike_spam"] = batch_spam
        batch_total = s.exec(
            select(func.count()).where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id)
            )
        ).one()
        batch_data["total_emails_in_batch"] = batch_total

    return {
        "current_batch": batch_data if batch_data else all_time,
        "all_time": all_time,
    }


def _count_skipped_by_reason(cid: str, s: Session, batch_id: Optional[str] = None) -> dict:
    all_rows = s.exec(
        select(EmailLog.skip_reason, func.count())
        .where(EmailLog.candidate_id == cid, EmailLog.decision == "skipped")
        .group_by(EmailLog.skip_reason)
    ).all()
    all_time = {reason or "unknown": count for reason, count in all_rows}

    batch_data = {}
    if batch_id:
        b_rows = s.exec(
            select(EmailLog.skip_reason, func.count())
            .where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
                EmailLog.decision == "skipped",
            )
            .group_by(EmailLog.skip_reason)
        ).all()
        batch_data = {reason or "unknown": count for reason, count in b_rows}

    return {
        "current_batch": batch_data if batch_data else all_time,
        "all_time": all_time,
    }


def _list_triage(cid: str, s: Session, batch_id: Optional[str] = None) -> dict:
    all_rows = s.exec(select(Task).where(Task.candidate_id == cid, Task.assignee_id == "u_triage")).all()
    all_time = {
        "triage_count": len(all_rows),
        "triage_task_ids": [t.task_id for t in all_rows],
        "triage_reasons": {t.task_id: t.description for t in all_rows},
    }

    batch_data = {}
    if batch_id:
        b_logs = s.exec(
            select(EmailLog)
            .where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
                EmailLog.assignee_id == "u_triage",
            )
        ).all()
        batch_data = {
            "triage_count": len(b_logs),
            "triage_email_ids": [l.email_id for l in b_logs],
            "triage_reasons": {l.email_id: l.reasoning or "Ambiguous scope" for l in b_logs},
        }

    return {
        "current_batch": batch_data if batch_data else all_time,
        "all_time": all_time,
    }


def _spurious_rate(cid: str, s: Session, batch_id: Optional[str] = None) -> dict:
    all_spurious = s.exec(
        select(func.count()).where(EmailLog.candidate_id == cid, EmailLog.is_spurious_flag == True)  # noqa: E712
    ).one()
    all_processed = s.exec(select(func.count()).where(EmailLog.candidate_id == cid)).one()
    all_rate = round(all_spurious / all_processed, 4) if all_processed else 0.0
    all_time = {"spurious_count": all_spurious, "processed": all_processed, "spurious_rate": all_rate}

    batch_data = {}
    if batch_id:
        b_spurious = s.exec(
            select(func.count()).where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
                EmailLog.is_spurious_flag == True,  # noqa: E712
            )
        ).one()
        b_processed = s.exec(
            select(func.count()).where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
            )
        ).one()
        b_rate = round(b_spurious / b_processed, 4) if b_processed else 0.0
        batch_data = {"spurious_count": b_spurious, "processed": b_processed, "spurious_rate": b_rate}

    return {
        "current_batch": batch_data if batch_data else all_time,
        "all_time": all_time,
    }


def _sum_deal_value(cid: str, s: Session, batch_id: Optional[str] = None) -> dict:
    all_rows = s.exec(
        select(Task.deal_value_inr).where(Task.candidate_id == cid, Task.category == "enterprise_rfp")
    ).all()
    all_stated = [v for v in all_rows if v is not None]
    all_time = {
        "total_deal_value_inr": sum(all_stated),
        "rfps_with_stated_value_count": len(all_stated),
        "rfps_with_no_stated_value_count": len(all_rows) - len(all_stated),
    }

    batch_data = {}
    if batch_id:
        b_tasks = s.exec(
            select(Task.deal_value_inr)
            .join(EmailLog, EmailLog.task_id == Task.task_id)
            .where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
                Task.category == "enterprise_rfp",
            )
        ).all()
        b_stated = [v for v in b_tasks if v is not None]
        batch_data = {
            "total_deal_value_inr": sum(b_stated),
            "rfps_with_stated_value_count": len(b_stated),
            "rfps_with_no_stated_value_count": len(b_tasks) - len(b_stated),
        }

    return {
        "current_batch": batch_data if batch_data else all_time,
        "all_time": all_time,
    }


def _thread_update_history(cid: str, s: Session, batch_id: Optional[str] = None) -> dict:
    rows = s.exec(
        select(EmailLog.thread_id, func.count())
        .where(EmailLog.candidate_id == cid, EmailLog.decision == "updated")
        .group_by(EmailLog.thread_id)
        .having(func.count() > 0)
    ).all()
    all_time = {"threads_updated_multiple_times": [tid for tid, _ in rows]}

    batch_data = {}
    if batch_id:
        b_rows = s.exec(
            select(EmailLog.thread_id)
            .where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
                EmailLog.decision == "updated",
            )
        ).all()
        batch_data = {"threads_updated_in_this_batch": list(set(b_rows))}

    return {
        "current_batch": batch_data if batch_data else all_time,
        "all_time": all_time,
    }


def _count_field_value(cid: str, s: Session, params: dict, batch_id: Optional[str] = None) -> dict:
    field, value = params.get("field"), params.get("value")
    if value in ["proposal", "rfp", "proposals", "rfps", "proposal_rfp"]:
        value = "enterprise_rfp"
        field = "category"

    col = Task.category if field == "category" else EmailLog.skip_reason
    model = Task if field == "category" else EmailLog
    all_count = s.exec(select(func.count()).where(model.candidate_id == cid, col == value)).one()
    all_time = {f"{value}_count": all_count}

    batch_data = {}
    if batch_id:
        log_col = EmailLog.category if field == "category" else EmailLog.skip_reason
        b_count = s.exec(
            select(func.count()).where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
                log_col == value,
            )
        ).one()
        batch_data = {f"{value}_count": b_count}

    return {
        "current_batch": batch_data if batch_data else all_time,
        "all_time": all_time,
    }


def _compound_filter(cid: str, s: Session, params: dict, batch_id: Optional[str] = None) -> dict:
    query = select(Task).where(Task.candidate_id == cid)
    if params.get("priority"):
        query = query.where(Task.priority == params["priority"])
    if params.get("confidence_lt") is not None:
        query = query.where(Task.confidence < params["confidence_lt"])
    rows = s.exec(query).all()
    all_time = {"matches": [{"task_id": t.task_id, "priority": t.priority, "confidence": t.confidence} for t in rows]}

    batch_data = {}
    if batch_id:
        b_query = (
            select(Task)
            .join(EmailLog, EmailLog.task_id == Task.task_id)
            .where(
                EmailLog.candidate_id == cid,
                (EmailLog.batch_id == batch_id) | (EmailLog.run_id == batch_id),
            )
        )
        if params.get("priority"):
            b_query = b_query.where(Task.priority == params["priority"])
        if params.get("confidence_lt") is not None:
            b_query = b_query.where(Task.confidence < params["confidence_lt"])
        b_rows = s.exec(b_query).all()
        batch_data = {"matches": [{"task_id": t.task_id, "priority": t.priority, "confidence": t.confidence} for t in b_rows]}

    return {
        "current_batch": batch_data if batch_data else all_time,
        "all_time": all_time,
    }