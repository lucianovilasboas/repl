"""Tests for scientific operations."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import pytest
from stack import Stack
from rpn_types import RPNNumber
from operations import dispatch, RPNError
import ops  # noqa: F401


def make_stack(*values):
    s = Stack()
    for v in values:
        s.push(RPNNumber(v))
    return s


def top(stack):
    return stack.peek(1).value


def test_sin():
    s = make_stack(math.pi / 2)
    dispatch("SIN", s, {})
    assert abs(top(s) - 1.0) < 1e-10


def test_cos():
    s = make_stack(0)
    dispatch("COS", s, {})
    assert abs(top(s) - 1.0) < 1e-10


def test_tan():
    s = make_stack(math.pi / 4)
    dispatch("TAN", s, {})
    assert abs(top(s) - 1.0) < 1e-10


def test_log():
    s = make_stack(100)
    dispatch("LOG", s, {})
    assert abs(top(s) - 2.0) < 1e-10


def test_ln():
    s = make_stack(math.e)
    dispatch("LN", s, {})
    assert abs(top(s) - 1.0) < 1e-10


def test_exp():
    s = make_stack(1)
    dispatch("EXP", s, {})
    assert abs(top(s) - math.e) < 1e-10


def test_sqrt():
    s = make_stack(9)
    dispatch("SQRT", s, {})
    assert top(s) == 3


def test_sq():
    s = make_stack(5)
    dispatch("SQ", s, {})
    assert top(s) == 25


def test_pow():
    s = make_stack(2, 10)
    dispatch("^", s, {})
    assert top(s) == 1024


def test_inv():
    s = make_stack(4)
    dispatch("INV", s, {})
    assert top(s) == 0.25


def test_pi():
    s = Stack()
    dispatch("PI", s, {})
    assert abs(top(s) - math.pi) < 1e-10


def test_factorial():
    s = make_stack(5)
    dispatch("!", s, {})
    assert top(s) == 120


def test_sqrt_negative():
    s = make_stack(-1)
    with pytest.raises(RPNError, match="Bad Argument Value"):
        dispatch("SQRT", s, {})


def test_log_negative():
    s = make_stack(-1)
    with pytest.raises(RPNError, match="Bad Argument Value"):
        dispatch("LOG", s, {})


def test_deg_mode():
    """Test trig in DEG mode."""
    s = Stack()
    dispatch("DEG", s, {})
    s.push(RPNNumber(90))
    dispatch("SIN", s, {})
    assert abs(top(s) - 1.0) < 1e-10
    # Restore RAD mode
    dispatch("RAD", s, {})
