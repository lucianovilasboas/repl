"""Tests for statistical / advanced list operations."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import pytest
from stack import Stack
from rpn_types import RPNNumber, RPNList, RPNProgram
from operations import dispatch, RPNError
from ops.program import execute
import ops  # noqa: F401


def make_stack(*values):
    s = Stack()
    for v in values:
        if isinstance(v, (RPNNumber, RPNList, RPNProgram)):
            s.push(v)
        else:
            s.push(RPNNumber(v))
    return s


def top(stack):
    return stack.peek(1).value


def executor(prog_tokens, stk, vrs):
    execute(prog_tokens, stk, vrs)


def make_list(*nums):
    return RPNList([RPNNumber(n) for n in nums])


# ── SUMLIST / ΣLIST ──────────────────────────────────────────────────

class TestSumlist:
    def test_basic(self):
        s = make_stack(make_list(1, 2, 3, 4, 5))
        dispatch("SUMLIST", s, {})
        assert top(s) == 15

    def test_sigma_alias(self):
        s = make_stack(make_list(10, 20, 30))
        dispatch("ΣLIST", s, {})
        assert top(s) == 60

    def test_single(self):
        s = make_stack(make_list(42))
        dispatch("SUMLIST", s, {})
        assert top(s) == 42

    def test_negatives(self):
        s = make_stack(make_list(-1, -2, 3))
        dispatch("SUMLIST", s, {})
        assert top(s) == 0


# ── SSQLIST ──────────────────────────────────────────────────────────

class TestSSQList:
    def test_basic(self):
        s = make_stack(make_list(1, 2, 3))
        dispatch("SSQLIST", s, {})
        assert top(s) == 14  # 1+4+9

    def test_single(self):
        s = make_stack(make_list(5))
        dispatch("SSQLIST", s, {})
        assert top(s) == 25


# ── PRODLIST / ΠLIST ─────────────────────────────────────────────────

class TestProdlist:
    def test_basic(self):
        s = make_stack(make_list(1, 2, 3, 4))
        dispatch("PRODLIST", s, {})
        assert top(s) == 24

    def test_pi_alias(self):
        s = make_stack(make_list(2, 3, 5))
        dispatch("ΠLIST", s, {})
        assert top(s) == 30

    def test_with_zero(self):
        s = make_stack(make_list(10, 0, 5))
        dispatch("PRODLIST", s, {})
        assert top(s) == 0


# ── MAXLIST / MINLIST ────────────────────────────────────────────────

class TestMaxMinList:
    def test_max(self):
        s = make_stack(make_list(3, 1, 4, 1, 5, 9))
        dispatch("MAXLIST", s, {})
        assert top(s) == 9

    def test_min(self):
        s = make_stack(make_list(3, 1, 4, 1, 5, 9))
        dispatch("MINLIST", s, {})
        assert top(s) == 1

    def test_max_negatives(self):
        s = make_stack(make_list(-10, -3, -7))
        dispatch("MAXLIST", s, {})
        assert top(s) == -3

    def test_min_negatives(self):
        s = make_stack(make_list(-10, -3, -7))
        dispatch("MINLIST", s, {})
        assert top(s) == -10


# ── MEAN ─────────────────────────────────────────────────────────────

class TestMean:
    def test_basic(self):
        s = make_stack(make_list(2, 4, 6))
        dispatch("MEAN", s, {})
        assert top(s) == 4

    def test_float(self):
        s = make_stack(make_list(1, 2))
        dispatch("MEAN", s, {})
        assert top(s) == 1.5

    def test_single(self):
        s = make_stack(make_list(7))
        dispatch("MEAN", s, {})
        assert top(s) == 7


# ── MEDIAN ───────────────────────────────────────────────────────────

class TestMedian:
    def test_odd(self):
        s = make_stack(make_list(3, 1, 2))
        dispatch("MEDIAN", s, {})
        assert top(s) == 2

    def test_even(self):
        s = make_stack(make_list(4, 1, 3, 2))
        dispatch("MEDIAN", s, {})
        assert top(s) == 2.5

    def test_single(self):
        s = make_stack(make_list(99))
        dispatch("MEDIAN", s, {})
        assert top(s) == 99


# ── SDEV (sample) ───────────────────────────────────────────────────

class TestSDev:
    def test_basic(self):
        s = make_stack(make_list(2, 4, 4, 4, 5, 5, 7, 9))
        dispatch("SDEV", s, {})
        expected = math.sqrt(32 / 7)  # sample sdev, mean=5, ssq_dev=32, n-1=7
        assert abs(top(s) - expected) < 1e-9

    def test_two_elements(self):
        s = make_stack(make_list(0, 2))
        dispatch("SDEV", s, {})
        expected = math.sqrt(2)
        assert abs(top(s) - expected) < 1e-9


# ── PSDEV (population) ──────────────────────────────────────────────

class TestPSDev:
    def test_basic(self):
        # pop sdev of {2,4,4,4,5,5,7,9} = sqrt(32/8) = sqrt(4) = 2
        s = make_stack(make_list(2, 4, 4, 4, 5, 5, 7, 9))
        dispatch("PSDEV", s, {})
        assert abs(top(s) - 2.0) < 1e-9

    def test_known(self):
        # { 10 20 30 } → mean=20, pop_var=200/3, psdev≈8.165
        s = make_stack(make_list(10, 20, 30))
        dispatch("PSDEV", s, {})
        expected = math.sqrt(200 / 3)
        assert abs(top(s) - expected) < 1e-9


# ── VAR / PVAR ───────────────────────────────────────────────────────

class TestVariance:
    def test_sample_var(self):
        s = make_stack(make_list(2, 4, 4, 4, 5, 5, 7, 9))
        dispatch("VAR", s, {})
        assert abs(top(s) - 32 / 7) < 1e-9  # sample var, mean=5, ssq_dev=32

    def test_pop_var(self):
        s = make_stack(make_list(2, 4, 4, 4, 5, 5, 7, 9))
        dispatch("PVAR", s, {})
        assert abs(top(s) - 4.0) < 1e-9  # pop var = 32/8 = 4


# ── TOTAL (cumulative sum) ──────────────────────────────────────────

class TestTotal:
    def test_basic(self):
        s = make_stack(make_list(1, 2, 3, 4))
        dispatch("TOTAL", s, {})
        lst = s.pop()
        vals = [x.value for x in lst.value]
        assert vals == [1, 3, 6, 10]


# ── DELTALIST / ΔLIST ────────────────────────────────────────────────

class TestDeltalist:
    def test_basic(self):
        s = make_stack(make_list(1, 3, 6, 10))
        dispatch("DELTALIST", s, {})
        lst = s.pop()
        vals = [x.value for x in lst.value]
        assert vals == [2, 3, 4]

    def test_delta_alias(self):
        s = make_stack(make_list(10, 7, 3))
        dispatch("ΔLIST", s, {})
        lst = s.pop()
        vals = [x.value for x in lst.value]
        assert vals == [-3, -4]


# ── SUB (sublist extraction) ────────────────────────────────────────

class TestSub:
    def test_basic(self):
        s = make_stack(make_list(10, 20, 30, 40, 50))
        s.push(RPNNumber(2))
        s.push(RPNNumber(4))
        dispatch("SUB", s, {})
        lst = s.pop()
        vals = [x.value for x in lst.value]
        assert vals == [20, 30, 40]

    def test_single_element(self):
        s = make_stack(make_list(10, 20, 30))
        s.push(RPNNumber(1))
        s.push(RPNNumber(1))
        dispatch("SUB", s, {})
        lst = s.pop()
        vals = [x.value for x in lst.value]
        assert vals == [10]


# ── DOLIST ───────────────────────────────────────────────────────────

class TestDolist:
    def test_square_each(self):
        s = make_stack(make_list(1, 2, 3))
        s.push(RPNProgram(["DUP", "*"]))
        dispatch("DOLIST", s, {}, executor)
        lst = s.pop()
        vals = [x.value for x in lst.value]
        assert vals == [1, 4, 9]

    def test_increment(self):
        s = make_stack(make_list(10, 20, 30))
        s.push(RPNProgram(["1", "+"]))
        dispatch("DOLIST", s, {}, executor)
        lst = s.pop()
        vals = [x.value for x in lst.value]
        assert vals == [11, 21, 31]


# ── STREAM (reduce/fold) ────────────────────────────────────────────

class TestStream:
    def test_sum(self):
        s = make_stack(make_list(1, 2, 3, 4))
        s.push(RPNProgram(["+"]))
        dispatch("STREAM", s, {}, executor)
        assert top(s) == 10

    def test_product(self):
        s = make_stack(make_list(1, 2, 3, 4))
        s.push(RPNProgram(["*"]))
        dispatch("STREAM", s, {}, executor)
        assert top(s) == 24


# ── NSUB ─────────────────────────────────────────────────────────────

class TestNsub:
    def test_basic(self):
        s = make_stack(make_list(10, 20, 30))
        dispatch("NSUB", s, {})
        assert top(s) == 3

    def test_empty(self):
        s = make_stack(RPNList([]))
        dispatch("NSUB", s, {})
        assert top(s) == 0
