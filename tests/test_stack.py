"""Tests for the RPN stack."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from stack import Stack, StackUnderflowError
from rpn_types import RPNNumber, RPNString


def test_push_pop():
    s = Stack()
    s.push(RPNNumber(42))
    assert s.pop() == RPNNumber(42)


def test_pop_empty():
    s = Stack()
    with pytest.raises(StackUnderflowError):
        s.pop()


def test_depth():
    s = Stack()
    assert s.depth() == 0
    s.push(RPNNumber(1))
    s.push(RPNNumber(2))
    assert s.depth() == 2


def test_peek():
    s = Stack()
    s.push(RPNNumber(10))
    s.push(RPNNumber(20))
    assert s.peek(1) == RPNNumber(20)
    assert s.peek(2) == RPNNumber(10)


def test_clear():
    s = Stack()
    s.push(RPNNumber(1))
    s.push(RPNNumber(2))
    s.clear()
    assert s.depth() == 0


def test_snapshot_restore():
    s = Stack()
    s.push(RPNNumber(1))
    s.push(RPNNumber(2))
    snap = s.snapshot()
    s.push(RPNNumber(3))
    s.restore(snap)
    assert s.depth() == 2
    assert s.peek(1) == RPNNumber(2)


def test_roll():
    s = Stack()
    s.push(RPNNumber(1))
    s.push(RPNNumber(2))
    s.push(RPNNumber(3))
    s.roll(3)  # move level 3 to top: 2 3 1
    assert s.pop() == RPNNumber(1)
    assert s.pop() == RPNNumber(3)
    assert s.pop() == RPNNumber(2)


def test_pick():
    s = Stack()
    s.push(RPNNumber(10))
    s.push(RPNNumber(20))
    s.push(RPNNumber(30))
    s.pick(2)  # copy level 2 to top
    assert s.pop() == RPNNumber(20)
    assert s.depth() == 3
