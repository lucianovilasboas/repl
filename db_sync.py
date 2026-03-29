"""Synchronous SQLAlchemy access for the REPL terminal client.

Shares the same database and ORM models as the async API, but uses a
synchronous engine so the REPL doesn't need asyncio.
"""

import json
import os
import sys
from contextlib import contextmanager

# Ensure project root on path
_root = os.path.dirname(os.path.abspath(__file__))
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from api.database import Base
from api.models import User, CalcSession
from api.auth import hash_password, verify_password
from state import _serialize, _deserialize

# ── Engine ───────────────────────────────────────────────────────────

def _sync_url() -> str:
    """Derive a synchronous SQLite URL from the async one in Settings."""
    from api.config import Settings
    url = Settings().database_url
    # "sqlite+aiosqlite:///./rpn_api.db" → "sqlite:///./rpn_api.db"
    return url.replace("+aiosqlite", "")

engine = create_engine(_sync_url(), echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_sync_db():
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(engine)


@contextmanager
def get_sync_session():
    """Yield a synchronous SQLAlchemy Session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── User CRUD ────────────────────────────────────────────────────────

def find_user(username: str) -> "User | None":
    with get_sync_session() as db:
        user = db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if user is None:
            return None
        uid, uname, uemail = user.id, user.username, user.email
    u = User(id=uid, username=uname, email=uemail, hashed_password="")
    return u


def create_user(username: str, email: str, password: str) -> User:
    with get_sync_session() as db:
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
        )
        db.add(user)
        db.flush()
        # Detach-safe: read attrs before session closes
        uid, uname, uemail = user.id, user.username, user.email
    # Return a transient object with the persisted id
    u = User(id=uid, username=uname, email=uemail, hashed_password="")
    return u


def verify_user(username: str, password: str) -> "User | None":
    with get_sync_session() as db:
        user = db.execute(
            select(User).where(User.username == username, User.is_active == True)  # noqa: E712
        ).scalar_one_or_none()
        if user is None or not verify_password(password, user.hashed_password):
            return None
        # Detach-safe copy
        uid, uname, uemail = user.id, user.username, user.email
    u = User(id=uid, username=uname, email=uemail, hashed_password="")
    return u


# ── Session CRUD ─────────────────────────────────────────────────────

def list_sessions(user_id: str) -> list:
    """Return list of dicts with session info (detached from ORM)."""
    with get_sync_session() as db:
        rows = db.execute(
            select(CalcSession)
            .where(CalcSession.user_id == user_id)
            .order_by(CalcSession.updated_at.desc())
        ).scalars().all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "stack_json": r.stack_json,
                "variables_json": r.variables_json,
                "settings_json": r.settings_json,
                "undo_json": r.undo_json,
                "stack_depth": len(json.loads(r.stack_json)),
                "updated_at": r.updated_at,
            }
            for r in rows
        ]


def get_session(session_id: str, user_id: str) -> "dict | None":
    with get_sync_session() as db:
        row = db.execute(
            select(CalcSession).where(
                CalcSession.id == session_id,
                CalcSession.user_id == user_id,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return {
            "id": row.id,
            "name": row.name,
            "stack_json": row.stack_json,
            "variables_json": row.variables_json,
            "settings_json": row.settings_json,
            "undo_json": row.undo_json,
        }


def create_session(user_id: str, name: str = "default") -> dict:
    with get_sync_session() as db:
        sess = CalcSession(user_id=user_id, name=name)
        db.add(sess)
        db.flush()
        return {
            "id": sess.id,
            "name": sess.name,
            "stack_json": sess.stack_json,
            "variables_json": sess.variables_json,
            "settings_json": sess.settings_json,
            "undo_json": sess.undo_json,
        }


def delete_session(session_id: str, user_id: str) -> bool:
    with get_sync_session() as db:
        row = db.execute(
            select(CalcSession).where(
                CalcSession.id == session_id,
                CalcSession.user_id == user_id,
            )
        ).scalar_one_or_none()
        if row is None:
            return False
        db.delete(row)
        return True


def save_session(session_id: str, stack, variables: dict,
                 settings: dict, undo_stack: list):
    """Serialize calculator state and persist to the CalcSession row."""
    stack_data = [_serialize(obj) for obj in stack.to_list()]
    vars_data = {k: _serialize(v) for k, v in variables.items()}
    undo_data = [
        [_serialize(obj) for obj in snap]
        for snap in undo_stack[-50:]
    ]
    with get_sync_session() as db:
        row = db.execute(
            select(CalcSession).where(CalcSession.id == session_id)
        ).scalar_one_or_none()
        if row is None:
            return
        row.stack_json = json.dumps(stack_data, ensure_ascii=False)
        row.variables_json = json.dumps(vars_data, ensure_ascii=False)
        row.settings_json = json.dumps(settings, ensure_ascii=False)
        row.undo_json = json.dumps(undo_data, ensure_ascii=False)


def load_session_state(session_dict: dict):
    """Deserialize a session dict into (stack_items, variables, settings, undo_stack)."""
    stack_items = [_deserialize(item) for item in json.loads(session_dict["stack_json"])]
    variables = {
        name: _deserialize(val)
        for name, val in json.loads(session_dict["variables_json"]).items()
    }
    settings = json.loads(session_dict["settings_json"])
    undo_stack = [
        [_deserialize(item) for item in snap]
        for snap in json.loads(session_dict["undo_json"])
    ]
    return stack_items, variables, settings, undo_stack
