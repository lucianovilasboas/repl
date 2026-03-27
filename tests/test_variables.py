"""Tests for variable operations."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from stack import Stack
from rpn_types import RPNNumber, RPNSymbol, RPNProgram
from operations import dispatch, RPNError
import ops  # noqa: F401


def make_stack(*values):
    s = Stack()
    for v in values:
        s.push(v)
    return s


def top(stack):
    return stack.peek(1)


def test_sto_rcl():
    s = Stack()
    variables = {}
    s.push(RPNNumber(42))
    s.push(RPNSymbol("X"))
    dispatch("STO", s, variables)
    assert s.depth() == 0
    assert "X" in variables

    s.push(RPNSymbol("X"))
    dispatch("RCL", s, variables)
    assert top(s) == RPNNumber(42)


def test_purge():
    s = Stack()
    variables = {"X": RPNNumber(42)}
    s.push(RPNSymbol("X"))
    dispatch("PURGE", s, variables)
    assert "X" not in variables


def test_variable_auto_eval():
    """Typing a variable name should push its value."""
    s = Stack()
    variables = {"X": RPNNumber(42)}
    dispatch("X", s, variables)
    assert top(s) == RPNNumber(42)


def test_program_variable_eval():
    """Typing a variable name that contains a program should execute it."""
    s = Stack()
    variables = {"DOUBLE": RPNProgram(["2", "*"])}
    s.push(RPNNumber(5))

    from ops.program import execute
    def executor(prog_tokens, stk, vrs):
        execute(prog_tokens, stk, vrs)

    dispatch("DOUBLE", s, variables, executor)
    assert top(s) == RPNNumber(10)


def test_rcl_undefined():
    s = Stack()
    variables = {}
    s.push(RPNSymbol("X"))
    with pytest.raises(RPNError, match="Undefined Name"):
        dispatch("RCL", s, variables)


def test_sto_add():
    s = Stack()
    variables = {"X": RPNNumber(10)}
    s.push(RPNNumber(5))
    s.push(RPNSymbol("X"))
    dispatch("STO+", s, variables)
    assert variables["X"] == RPNNumber(15)
