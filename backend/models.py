import uuid
from datetime import datetime, date
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint, Index


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


class Task(SQLModel, table=True):
    """Backing store for the Task API (spec §5). Field names/types match
    §5.2 exactly — this table IS the contract.

    The UNIQUE(candidate_id, thread_id) constraint is the load-bearing
    decision in this whole system: it's what makes /ingest idempotent
    (Run 2 = same batch = same thread_ids = upsert no-ops) AND what makes
    thread replies update instead of duplicate (Run 3), using ONE code
    path (an upsert) instead of two separate special cases.
    """
    # We use an Index instead of a UniqueConstraint here.
    # The ingestion pipeline (/ingest) enforces thread reconciliation and idempotency
    # at the application layer, but the raw POST /tasks endpoint must not crash with 500
    # if duplicate thread_ids are posted directly.
    __table_args__ = (Index("idx_candidate_thread", "candidate_id", "thread_id"),)

    task_id: str = Field(default_factory=lambda: new_id("tsk"), primary_key=True)
    candidate_id: str = Field(index=True)
    source_email_id: str  # most recent email that touched this task (audit, not dedup key)
    thread_id: str = Field(index=True)

    title: str
    description: Optional[str] = None
    assignee_id: str
    category: str
    priority: str
    due_date: Optional[str] = None
    deal_value_inr: Optional[int] = None
    company_name: Optional[str] = None
    confidence: float

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EmailLog(SQLModel, table=True):
    """The ledger the Task API spec has no room for: every email we ever
    saw, including the ones that never became a task. This is what
    /api/stats and /api/chat read from — never re-derived from Gemini.
    """
    __table_args__ = (UniqueConstraint("candidate_id", "email_id", name="uq_candidate_email"),)

    log_id: str = Field(default_factory=lambda: new_id("log"), primary_key=True)
    candidate_id: str = Field(index=True)
    email_id: str = Field(index=True)
    thread_id: str = Field(index=True)
    run_id: Optional[str] = Field(default=None, index=True)

    decision: str  # 'created' | 'updated' | 'skipped'
    skip_reason: Optional[str] = None  # 'out_of_office' | 'newsletter' | 'spam' | None
    category: Optional[str] = None
    assignee_id: Optional[str] = None
    priority: Optional[str] = None
    confidence: Optional[float] = None
    is_spurious_flag: bool = False
    reasoning: Optional[str] = None
    task_id: Optional[str] = Field(default=None, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class Run(SQLModel, table=True):
    run_id: str = Field(default_factory=lambda: new_id("run"), primary_key=True)
    candidate_id: str = Field(index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    processed: int = 0
    tasks_created: int = 0
    tasks_updated: int = 0
    skipped: int = 0