from sqlmodel import SQLModel, create_engine, Session
from config import DATABASE_URL

# check_same_thread only matters for sqlite local dev; harmless elsewhere.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db():
    """Create tables if they don't exist. Safe to call on every startup —
    does NOT drop/recreate, so it never wipes existing rows (important:
    Run 3 depends on Run 1's tasks surviving a redeploy)."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session