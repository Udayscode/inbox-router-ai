import os
from sqlmodel import SQLModel, create_engine, Session
from config import DATABASE_URL

# Ensure parent directory exists for SQLite database path
if DATABASE_URL.startswith("sqlite:///"):
    db_file_path = DATABASE_URL.replace("sqlite:///", "")
    parent_dir = os.path.dirname(db_file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

# check_same_thread only matters for sqlite local dev; harmless elsewhere.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db():
    """Create tables if they don't exist. Safe to call on every startup —
    does NOT drop/recreate, so it never wipes existing rows (important:
    Run 3 depends on Run 1's tasks surviving a redeploy)."""
    SQLModel.metadata.create_all(engine)
    # Safe auto-migration: add batch_id to existing run / emaillog tables if missing
    with engine.begin() as conn:
        for table, col in [("run", "batch_id"), ("emaillog", "batch_id")]:
            try:
                conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {col} VARCHAR")
            except Exception:
                pass  # column already exists or non-SQLite dialect


def get_session():
    with Session(engine) as session:
        yield session