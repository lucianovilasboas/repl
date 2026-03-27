"""Tests for arithmetic operations."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def test_add():
    s = make_stack(3, 4)
    dispatch("+", s, {})
    assert top(s) == 7
    assert s.depth() == 1


def test_sub():
    s = make_stack(10, 3)
    dispatch("-", s, {})
    assert top(s) == 7


def test_mul():
    s = make_stack(6, 7)
    dispatch("*", s, {})
    assert top(s) == 42


def test_div():
    s = make_stack(10, 4)
    dispatch("/", s, {})
    assert top(s) == 2.5


def test_div_by_zero():
    s = make_stack(10, 0)
    with pytest.raises(RPNError, match="division by zero"):
        dispatch("/", s, {})
    assert s.depth() == 2  # values restored


def test_neg():
    s = make_stack(5)
    dispatch("NEG", s, {})
    assert top(s) == -5


def test_abs():
    s = make_stack(-7)
    dispatch("ABS", s, {})
    assert top(s) == 7


def test_mod():
    s = make_stack(10, 3)
    dispatch("MOD", s, {})
    assert top(s) == 1


def test_ip():
    s = make_stack(3.7)
    dispatch("IP", s, {})
    assert top(s) == 3


def test_fp():
    s = make_stack(3.7)
    dispatch("FP", s, {})
    assert abs(top(s) - 0.7) < 1e-10


def test_min_max():
    s = make_stack(3, 7)
    dispatch("MIN", s, {})
    assert top(s) == 3

    s = make_stack(3, 7)
    dispatch("MAX", s, {})
    assert top(s) == 7


def test_sign():
    s = make_stack(-5)
    dispatch("SIGN", s, {})
    assert top(s) == -1

    s = make_stack(0)
    dispatch("SIGN", s, {})
    assert top(s) == 0

    s = make_stack(10)
    dispatch("SIGN", s, {})
    assert top(s) == 1


def test_complex_expression():
    """2 3 * 4 + = 10."""
    s = make_stack(2, 3)
    dispatch("*", s, {})
    s.push(RPNNumber(4))
    dispatch("+", s, {})
    assert top(s) == 10
    assert s.depth() == 1


def test_too_few_args():
    s = Stack()
    with pytest.raises(RPNError, match="Too Few Arguments"):
        dispatch("+", s, {})
