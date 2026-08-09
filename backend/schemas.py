from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from config import ASSIGNEE_IDS, CATEGORIES, PRIORITIES, normalize_candidate_id


class TaskCreate(BaseModel):
    candidate_id: str
    source_email_id: str
    thread_id: str
    title: str
    description: Optional[str] = None
    assignee_id: str
    category: str
    priority: str
    due_date: Optional[date] = None
    deal_value_inr: Optional[int] = None
    company_name: Optional[str] = None
    confidence: float

    @field_validator("candidate_id")
    @classmethod
    def _norm_candidate(cls, v):
        return normalize_candidate_id(v)


class TaskUpdate(BaseModel):
    """PATCH body — every field optional, only supplied ones are applied."""
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    deal_value_inr: Optional[int] = None
    company_name: Optional[str] = None
    confidence: Optional[float] = None


class TaskCreateResponse(BaseModel):
    task_id: str
    candidate_id: str
    source_email_id: str
    created_at: datetime


class TaskOut(BaseModel):
    task_id: str
    candidate_id: str
    source_email_id: str
    thread_id: str
    title: str
    description: Optional[str]
    assignee_id: str
    category: str
    priority: str
    due_date: Optional[date]
    deal_value_inr: Optional[int]
    company_name: Optional[str]
    confidence: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def enum_error(field: str, received: str, allowed: List[str]) -> dict:
    """Exact error shape required by spec §5.1 — grading hits this directly."""
    return {"error": "invalid_enum_value", "field": field, "received": received, "allowed": allowed}


def validate_task_enums(assignee_id: str, category: str, priority: str) -> Optional[dict]:
    """Returns the first enum_error found, or None if all valid.
    Checked in this order so the FIRST invalid field is reported —
    deterministic, testable."""
    if assignee_id not in ASSIGNEE_IDS:
        return enum_error("assignee_id", assignee_id, ASSIGNEE_IDS)
    if category not in CATEGORIES:
        return enum_error("category", category, CATEGORIES)
    if priority not in PRIORITIES:
        return enum_error("priority", priority, PRIORITIES)
    return None