"""Tests for RPL program execution."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from stack import Stack
from rpn_types import RPNNumber, RPNProgram, RPNSymbol
from operations import dispatch, RPNError
from ops.program import execute
import ops  # noqa: F401


def make_stack(*values):
    s = Stack()
    for v in values:
        s.push(v if isinstance(v, RPNNumber) else RPNNumber(v))
    return s


def top(stack):
    return stack.peek(1).value


def executor(prog_tokens, stk, vrs):
    execute(prog_tokens, stk, vrs)


def test_eval_program():
    """« DUP * » with 5 on stack → 25."""
    s = make_stack(5)
    s.push(RPNProgram(["DUP", "*"]))
    dispatch("EVAL", s, {}, executor)
    assert top(s) == 25


def test_if_then_end():
    """IF 1 THEN 42 END."""
    s = Stack()
    variables = {}
    execute(["1", "IF", "1", "THEN", "42", "END"], s, variables)
    assert top(s) == 42


def test_if_then_else_end():
    """IF condition is false, execute ELSE branch."""
    s = Stack()
    variables = {}
    execute(["0", "IF", "0", "THEN", "42", "ELSE", "99", "END"], s, variables)
    # First 0 is pushed to stack by "0", IF pops next condition result
    # Actually: the first "0" pushes 0, then IF takes condition tokens ["0"] which pushes 0, pops it (false), goes to ELSE, pushes 99
    # But the first 0 is still on stack
    assert s.peek(1).value == 99


def test_for_next():
    """1 5 FOR i i NEXT → pushes 1 2 3 4 5."""
    s = Stack()
    variables = {}
    s.push(RPNNumber(1))
    s.push(RPNNumber(5))
    execute(["FOR", "I", "I", "NEXT"], s, variables)
    assert s.depth() == 5
    values = [s.pop().value for _ in range(5)]
    assert values == [5, 4, 3, 2, 1]


def test_start_next():
    """0 on stack, 1 5 START 1 + NEXT — adds 1 five times → 5."""
    s = Stack()
    variables = {}
    s.push(RPNNumber(0))
    s.push(RPNNumber(1))
    s.push(RPNNumber(5))
    execute(["START", "1", "+", "NEXT"], s, variables)
    assert top(s) == 5


def test_while_repeat_end():
    """Count down from 5 to 0."""
    s = Stack()
    variables = {}
    s.push(RPNNumber(5))
    execute(["WHILE", "DUP", "0", ">", "REPEAT", "1", "-", "END"], s, variables)
    assert top(s) == 0


def test_nested_if():
    """Nested IF/THEN/END."""
    s = Stack()
    variables = {}
    execute(["1", "IF", "1", "THEN", "IF", "1", "THEN", "42", "END", "END"], s, variables)
    # First "1" is pushed, then IF condition "1" → true, then inner IF condition "1" → true → 42
    assert s.peek(1).value == 42


def test_sto_eval_program():
    """Store a program and call it by name."""
    s = Stack()
    variables = {}
    s.push(RPNProgram(["DUP", "*"]))
    s.push(RPNSymbol("SQ"))
    dispatch("STO", s, variables)

    s.push(RPNNumber(7))
    dispatch("SQ", s, variables, executor)
    assert top(s) == 49


def test_do_until():
    """DO body UNTIL condition END."""
    s = Stack()
    variables = {}
    s.push(RPNNumber(0))
    execute(["DO", "1", "+", "UNTIL", "DUP", "5", "==", "END"], s, variables)
    assert top(s) == 5


def test_for_step():
    """1 10 FOR I I 2 STEP — counts 1, 3, 5, 7, 9."""
    s = Stack()
    variables = {}
    s.push(RPNNumber(1))
    s.push(RPNNumber(10))
    execute(["FOR", "I", "I", "2", "STEP"], s, variables)
    assert s.depth() == 5
    values = [s.pop().value for _ in range(5)]
    assert values == [9, 7, 5, 3, 1]


# ===================== → (local variable binding) =====================

def test_arrow_basic():
    """« → N « N NEG » » with 5 on stack → -5."""
    s = make_stack(5)
    execute(["->", "N", "<< N NEG >>"], s, {})
    assert top(s) == -5


def test_arrow_two_vars():
    """« → A B « A B - » » with 10, 3 → 7."""
    s = make_stack(10, 3)
    execute(["->", "A", "B", "<< A B - >>"], s, {})
    assert top(s) == 7


def test_arrow_preserves_outer_vars():
    """→ should restore outer variable after inner scope ends."""
    s = make_stack(99, 5)
    variables = {"N": RPNNumber(42)}
    execute(["->", "N", "<< N DUP * >>"], s, variables)
    # After → scope ends, N should be restored to 42
    assert variables["N"].value == 42
    assert top(s) == 25


def test_arrow_cleans_up_local():
    """After → scope ends, local var is removed if it didn't exist before."""
    s = make_stack(7)
    variables = {}
    execute(["->", "X", "<< X 2 * >>"], s, variables)
    assert "X" not in variables
    assert top(s) == 14


def test_arrow_remaining_tokens_as_body():
    """→ without explicit « » body uses remaining non-identifier tokens."""
    s = make_stack(3, 4)
    execute(["->", "A", "B", "<< A B + >>"], s, {})
    assert top(s) == 7


def test_arrow_nested_in_program():
    """Store a program using → and EVAL it."""
    s = Stack()
    variables = {}
    s.push(RPNProgram(["->", "N", "<< N N * >>"]))
    s.push(RPNSymbol("SQ"))
    dispatch("STO", s, variables)
    s.push(RPNNumber(6))
    dispatch("SQ", s, variables, executor)
    assert top(s) == 36


# ===================== CASE / THEN / END =====================

def test_case_first_match():
    """CASE: first matching branch executes."""
    s = make_stack(1)
    execute([
        "CASE",
        "DUP", "1", "==", "THEN", "10", "END",
        "DUP", "2", "==", "THEN", "20", "END",
        "30",
        "END"
    ], s, {})
    # Stack: 1 (from DUP in the original), 10
    assert s.peek(1).value == 10


def test_case_second_match():
    """CASE: second branch matches."""
    s = make_stack(2)
    execute([
        "CASE",
        "DUP", "1", "==", "THEN", "10", "END",
        "DUP", "2", "==", "THEN", "20", "END",
        "30",
        "END"
    ], s, {})
    assert s.peek(1).value == 20


def test_case_default():
    """CASE: no match, default executed."""
    s = make_stack(9)
    execute([
        "CASE",
        "DUP", "1", "==", "THEN", "10", "END",
        "DUP", "2", "==", "THEN", "20", "END",
        "30",
        "END"
    ], s, {})
    assert s.peek(1).value == 30


def test_case_no_default():
    """CASE with no default — nothing extra happens if no match."""
    s = make_stack(9)
    execute([
        "CASE",
        "DUP", "1", "==", "THEN", "10", "END",
        "END"
    ], s, {})
    assert s.depth() == 1
    assert top(s) == 9


# ===================== IFERR / THEN / ELSE / END =====================

def test_iferr_no_error():
    """IFERR: no error → ELSE branch executes."""
    s = make_stack(4, 2)
    execute([
        "IFERR", "/", "THEN", "0", "ELSE", "1", "END"
    ], s, {})
    # 4 / 2 = 2, no error, ELSE branch pushes 1
    assert s.peek(1).value == 1


def test_iferr_with_error():
    """IFERR: error → THEN (error handler) executes."""
    s = make_stack(4, 0)
    execute([
        "IFERR", "/", "THEN", "999", "END"
    ], s, {})
    assert s.peek(1).value == 999


def test_iferr_error_else():
    """IFERR with error — ELSE branch does NOT run."""
    s = make_stack(4, 0)
    execute([
        "IFERR", "/", "THEN", "100", "ELSE", "200", "END"
    ], s, {})
    assert s.peek(1).value == 100
