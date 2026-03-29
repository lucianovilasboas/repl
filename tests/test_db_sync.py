"""Tests for db_sync — synchronous database access for REPL sessions."""

import os
import sys
import json
import pytest

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use an in-memory SQLite database for tests
os.environ["RPN_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

# We need to patch the sync engine BEFORE importing db_sync
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import Base from the api (to share the same metadata)
from api.database import Base

_test_engine = create_engine("sqlite:///:memory:", echo=False)
_TestSession = sessionmaker(bind=_test_engine)


@pytest.fixture(autouse=True)
def _setup_db(monkeypatch):
    """Create a fresh in-memory DB for every test."""
    import db_sync
    monkeypatch.setattr(db_sync, "engine", _test_engine)
    monkeypatch.setattr(db_sync, "SessionLocal", _TestSession)
    Base.metadata.create_all(_test_engine)
    yield
    Base.metadata.drop_all(_test_engine)


# ── Now import the module under test ─────────────────────────────────
import db_sync
from stack import Stack
from rpn_types import RPNNumber, RPNString, RPNList


# ── User tests ───────────────────────────────────────────────────────

class TestUserCRUD:
    def test_create_and_find_user(self):
        user = db_sync.create_user("alice", "alice@test.com", "secret")
        assert user.username == "alice"
        assert user.id  # uuid assigned

        found = db_sync.find_user("alice")
        assert found is not None
        assert found.username == "alice"

    def test_find_user_not_exists(self):
        assert db_sync.find_user("ghost") is None

    def test_verify_user_correct_password(self):
        db_sync.create_user("bob", "bob@test.com", "pass123")
        user = db_sync.verify_user("bob", "pass123")
        assert user is not None
        assert user.username == "bob"

    def test_verify_user_wrong_password(self):
        db_sync.create_user("carol", "carol@test.com", "right")
        assert db_sync.verify_user("carol", "wrong") is None

    def test_verify_user_not_exists(self):
        assert db_sync.verify_user("nobody", "whatever") is None


# ── Session tests ────────────────────────────────────────────────────

class TestSessionCRUD:
    def _make_user(self):
        return db_sync.create_user("tester", "tester@test.com", "pw")

    def test_create_session(self):
        user = self._make_user()
        sess = db_sync.create_session(user.id, "my_calc")
        assert sess["name"] == "my_calc"
        assert sess["id"]
        assert sess["stack_json"] == "[]"

    def test_list_sessions(self):
        user = self._make_user()
        db_sync.create_session(user.id, "first")
        db_sync.create_session(user.id, "second")
        sessions = db_sync.list_sessions(user.id)
        assert len(sessions) == 2
        names = {s["name"] for s in sessions}
        assert names == {"first", "second"}

    def test_get_session(self):
        user = self._make_user()
        created = db_sync.create_session(user.id, "test_get")
        fetched = db_sync.get_session(created["id"], user.id)
        assert fetched is not None
        assert fetched["name"] == "test_get"

    def test_get_session_wrong_user(self):
        user = self._make_user()
        other = db_sync.create_user("other", "other@test.com", "pw")
        sess = db_sync.create_session(user.id, "private")
        assert db_sync.get_session(sess["id"], other.id) is None

    def test_delete_session(self):
        user = self._make_user()
        sess = db_sync.create_session(user.id, "to_delete")
        assert db_sync.delete_session(sess["id"], user.id) is True
        assert db_sync.get_session(sess["id"], user.id) is None

    def test_delete_session_not_found(self):
        user = self._make_user()
        assert db_sync.delete_session("nonexistent-uuid", user.id) is False


# ── Persist and reload state ─────────────────────────────────────────

class TestStatePersistence:
    def _make_user_and_session(self):
        user = db_sync.create_user("calc_user", "calc@test.com", "pw")
        sess = db_sync.create_session(user.id, "calc_sess")
        return user, sess

    def test_save_and_load_stack(self):
        user, sess = self._make_user_and_session()
        stack = Stack()
        stack.push(RPNNumber(42))
        stack.push(RPNNumber(3.14))
        variables = {}
        settings = {"angle_mode": "DEG", "num_format": "FIX", "fix_digits": 2, "stack_lines": 8}
        undo_stack = []

        db_sync.save_session(sess["id"], stack, variables, settings, undo_stack)

        reloaded = db_sync.get_session(sess["id"], user.id)
        items, vars_, sett, undo = db_sync.load_session_state(reloaded)

        assert len(items) == 2
        assert items[0].value == 42
        assert items[1].value == 3.14
        assert sett["angle_mode"] == "DEG"
        assert sett["fix_digits"] == 2
        assert sett["stack_lines"] == 8

    def test_save_and_load_variables(self):
        user, sess = self._make_user_and_session()
        stack = Stack()
        variables = {"X": RPNNumber(99), "MSG": RPNString("hello")}
        settings = {"angle_mode": "RAD", "num_format": "STD", "fix_digits": None}

        db_sync.save_session(sess["id"], stack, variables, settings, [])

        reloaded = db_sync.get_session(sess["id"], user.id)
        items, vars_, sett, undo = db_sync.load_session_state(reloaded)

        assert vars_["X"].value == 99
        assert vars_["MSG"].value == "hello"

    def test_save_and_load_undo_stack(self):
        user, sess = self._make_user_and_session()
        stack = Stack()
        stack.push(RPNNumber(10))
        # Simulate undo snapshot: stack had [5] before
        undo_stack = [[RPNNumber(5)]]
        settings = {"angle_mode": "RAD", "num_format": "STD", "fix_digits": None}

        db_sync.save_session(sess["id"], stack, {}, settings, undo_stack)

        reloaded = db_sync.get_session(sess["id"], user.id)
        items, vars_, sett, undo = db_sync.load_session_state(reloaded)

        assert len(undo) == 1
        assert len(undo[0]) == 1
        assert undo[0][0].value == 5

    def test_save_and_load_list_variable(self):
        user, sess = self._make_user_and_session()
        stack = Stack()
        variables = {"L": RPNList([RPNNumber(1), RPNNumber(2), RPNNumber(3)])}
        settings = {"angle_mode": "RAD", "num_format": "STD", "fix_digits": None}

        db_sync.save_session(sess["id"], stack, variables, settings, [])

        reloaded = db_sync.get_session(sess["id"], user.id)
        items, vars_, sett, undo = db_sync.load_session_state(reloaded)

        assert isinstance(vars_["L"], RPNList)
        assert len(vars_["L"].value) == 3
        assert vars_["L"].value[0].value == 1
