"""Tests for vector and matrix operations."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import math
from stack import Stack
from rpn_types import RPNNumber, RPNVector, RPNMatrix, RPNList
from operations import dispatch, RPNError
from parser import parse
import ops  # noqa: F401


def make_stack(*values):
    s = Stack()
    for v in values:
        if isinstance(v, (RPNVector, RPNMatrix, RPNList)):
            s.push(v)
        else:
            s.push(v if isinstance(v, RPNNumber) else RPNNumber(v))
    return s


def top(stack):
    return stack.peek(1)


def top_val(stack):
    return stack.peek(1).value


# ── Parsing ───────────────────────────────────────────────────────────

def test_parse_vector():
    tokens = parse("[ 1 2 3 ]")
    assert len(tokens) == 1
    v = tokens[0]
    assert isinstance(v, RPNVector)
    assert len(v.value) == 3
    assert v.value[0].value == 1
    assert v.value[2].value == 3


def test_parse_matrix():
    tokens = parse("[[ [ 1 2 ] [ 3 4 ] ]]")
    assert len(tokens) == 1
    m = tokens[0]
    assert isinstance(m, RPNMatrix)
    assert m.rows() == 2
    assert m.cols() == 2
    assert m.value[0][0].value == 1
    assert m.value[1][1].value == 4


def test_parse_empty_vector():
    tokens = parse("[ ]")
    assert isinstance(tokens[0], RPNVector)
    assert len(tokens[0].value) == 0


def test_vector_repr():
    v = RPNVector([RPNNumber(1), RPNNumber(2), RPNNumber(3)])
    assert v.rpn_repr() == "[ 1 2 3 ]"


def test_matrix_repr():
    m = RPNMatrix([[RPNNumber(1), RPNNumber(2)], [RPNNumber(3), RPNNumber(4)]])
    assert m.rpn_repr() == "[[ [ 1 2 ] [ 3 4 ] ]]"


# ── Vector arithmetic ─────────────────────────────────────────────────

def test_vector_add():
    s = make_stack(
        RPNVector([RPNNumber(1), RPNNumber(2)]),
        RPNVector([RPNNumber(3), RPNNumber(4)])
    )
    dispatch("+", s, {})
    r = top(s)
    assert isinstance(r, RPNVector)
    assert [x.value for x in r.value] == [4, 6]


def test_vector_sub():
    s = make_stack(
        RPNVector([RPNNumber(5), RPNNumber(3)]),
        RPNVector([RPNNumber(1), RPNNumber(2)])
    )
    dispatch("-", s, {})
    r = top(s)
    assert [x.value for x in r.value] == [4, 1]


def test_vector_scalar_mul():
    s = make_stack(
        RPNVector([RPNNumber(1), RPNNumber(2), RPNNumber(3)]),
        RPNNumber(2)
    )
    dispatch("*", s, {})
    r = top(s)
    assert [x.value for x in r.value] == [2, 4, 6]


def test_vector_scalar_div():
    s = make_stack(
        RPNVector([RPNNumber(4), RPNNumber(6)]),
        RPNNumber(2)
    )
    dispatch("/", s, {})
    r = top(s)
    assert [x.value for x in r.value] == [2, 3]


def test_vector_neg():
    s = make_stack(RPNVector([RPNNumber(1), RPNNumber(-2)]))
    dispatch("NEG", s, {})
    r = top(s)
    assert [x.value for x in r.value] == [-1, 2]


def test_vector_abs():
    """ABS of a vector returns Euclidean norm."""
    s = make_stack(RPNVector([RPNNumber(3), RPNNumber(4)]))
    dispatch("ABS", s, {})
    assert top_val(s) == 5


def test_vector_dimension_mismatch():
    s = make_stack(
        RPNVector([RPNNumber(1), RPNNumber(2)]),
        RPNVector([RPNNumber(1)])
    )
    with pytest.raises(RPNError, match="Invalid Dimension"):
        dispatch("+", s, {})


# ── Matrix arithmetic ─────────────────────────────────────────────────

def _mat2x2(a, b, c, d):
    return RPNMatrix([[RPNNumber(a), RPNNumber(b)], [RPNNumber(c), RPNNumber(d)]])


def test_matrix_add():
    s = make_stack(_mat2x2(1, 2, 3, 4), _mat2x2(5, 6, 7, 8))
    dispatch("+", s, {})
    r = top(s)
    assert isinstance(r, RPNMatrix)
    assert r.value[0][0].value == 6
    assert r.value[1][1].value == 12


def test_matrix_sub():
    s = make_stack(_mat2x2(5, 6, 7, 8), _mat2x2(1, 2, 3, 4))
    dispatch("-", s, {})
    r = top(s)
    assert r.value[0][0].value == 4
    assert r.value[1][1].value == 4


def test_matrix_mul():
    """[1 2; 3 4] * [5 6; 7 8] = [19 22; 43 50]."""
    s = make_stack(_mat2x2(1, 2, 3, 4), _mat2x2(5, 6, 7, 8))
    dispatch("*", s, {})
    r = top(s)
    assert r.value[0][0].value == 19
    assert r.value[0][1].value == 22
    assert r.value[1][0].value == 43
    assert r.value[1][1].value == 50


def test_matrix_scalar_mul():
    s = make_stack(_mat2x2(1, 2, 3, 4), RPNNumber(3))
    dispatch("*", s, {})
    r = top(s)
    assert r.value[0][0].value == 3
    assert r.value[1][1].value == 12


def test_matrix_neg():
    s = make_stack(_mat2x2(1, -2, 3, -4))
    dispatch("NEG", s, {})
    r = top(s)
    assert r.value[0][0].value == -1
    assert r.value[0][1].value == 2


def test_matrix_vector_mul():
    """[1 2; 3 4] * [5 6] = [17 39]."""
    m = _mat2x2(1, 2, 3, 4)
    v = RPNVector([RPNNumber(5), RPNNumber(6)])
    s = make_stack(m, v)
    dispatch("*", s, {})
    r = top(s)
    assert isinstance(r, RPNVector)
    assert [x.value for x in r.value] == [17, 39]


# ── Specific matrix operations ────────────────────────────────────────

def test_identity():
    s = make_stack(3)
    dispatch("IDN", s, {})
    m = top(s)
    assert m.rows() == 3 and m.cols() == 3
    assert m.value[0][0].value == 1
    assert m.value[0][1].value == 0
    assert m.value[1][1].value == 1


def test_transpose():
    m = RPNMatrix([[RPNNumber(1), RPNNumber(2), RPNNumber(3)],
                    [RPNNumber(4), RPNNumber(5), RPNNumber(6)]])
    s = make_stack(m)
    dispatch("TRN", s, {})
    r = top(s)
    assert r.rows() == 3 and r.cols() == 2
    assert r.value[0][0].value == 1
    assert r.value[0][1].value == 4
    assert r.value[2][0].value == 3


def test_determinant():
    s = make_stack(_mat2x2(1, 2, 3, 4))
    dispatch("DET", s, {})
    assert top_val(s) == -2


def test_determinant_3x3():
    m = RPNMatrix([
        [RPNNumber(1), RPNNumber(2), RPNNumber(3)],
        [RPNNumber(0), RPNNumber(1), RPNNumber(4)],
        [RPNNumber(5), RPNNumber(6), RPNNumber(0)],
    ])
    s = make_stack(m)
    dispatch("DET", s, {})
    assert top_val(s) == 1


def test_inverse():
    s = make_stack(_mat2x2(1, 2, 3, 4))
    dispatch("MINV", s, {})
    r = top(s)
    # inv([1 2; 3 4]) = [-2 1; 1.5 -0.5]
    assert abs(r.value[0][0].value - (-2)) < 1e-10
    assert abs(r.value[0][1].value - 1) < 1e-10
    assert abs(r.value[1][0].value - 1.5) < 1e-10
    assert abs(r.value[1][1].value - (-0.5)) < 1e-10


def test_trace():
    s = make_stack(_mat2x2(1, 2, 3, 4))
    dispatch("TRACE", s, {})
    assert top_val(s) == 5


def test_cross_product():
    a = RPNVector([RPNNumber(1), RPNNumber(0), RPNNumber(0)])
    b = RPNVector([RPNNumber(0), RPNNumber(1), RPNNumber(0)])
    s = make_stack(a, b)
    dispatch("CROSS", s, {})
    r = top(s)
    assert [x.value for x in r.value] == [0, 0, 1]


def test_dot_product():
    a = RPNVector([RPNNumber(1), RPNNumber(2), RPNNumber(3)])
    b = RPNVector([RPNNumber(4), RPNNumber(5), RPNNumber(6)])
    s = make_stack(a, b)
    dispatch("DOT", s, {})
    assert top_val(s) == 32


def test_vnorm():
    s = make_stack(RPNVector([RPNNumber(3), RPNNumber(4)]))
    dispatch("VNORM", s, {})
    assert top_val(s) == 5


def test_to_vector():
    s = make_stack(1, 2, 3, 3)
    dispatch("TOVECT", s, {})
    r = top(s)
    assert isinstance(r, RPNVector)
    assert [x.value for x in r.value] == [1, 2, 3]


def test_from_vector():
    s = make_stack(RPNVector([RPNNumber(10), RPNNumber(20)]))
    dispatch("FROMVECT", s, {})
    dim = s.pop()
    assert dim.value == 2
    assert s.pop().value == 20
    assert s.pop().value == 10


def test_mdims_matrix():
    s = make_stack(_mat2x2(1, 2, 3, 4))
    dispatch("MDIMS", s, {})
    r = top(s)
    assert isinstance(r, RPNList)
    assert [x.value for x in r.value] == [2, 2]


def test_mdims_vector():
    s = make_stack(RPNVector([RPNNumber(1), RPNNumber(2), RPNNumber(3)]))
    dispatch("MDIMS", s, {})
    assert top_val(s) == 3


def test_vget():
    s = make_stack(RPNVector([RPNNumber(10), RPNNumber(20), RPNNumber(30)]), RPNNumber(2))
    dispatch("VGET", s, {})
    assert top_val(s) == 20


def test_vput():
    v = RPNVector([RPNNumber(10), RPNNumber(20), RPNNumber(30)])
    s = make_stack(v, RPNNumber(2), RPNNumber(99))
    dispatch("VPUT", s, {})
    r = top(s)
    assert r.value[1].value == 99


def test_mget():
    m = _mat2x2(1, 2, 3, 4)
    s = make_stack(m, RPNList([RPNNumber(2), RPNNumber(1)]))
    dispatch("MGET", s, {})
    assert top_val(s) == 3


def test_mput():
    m = _mat2x2(1, 2, 3, 4)
    s = make_stack(m, RPNList([RPNNumber(1), RPNNumber(2)]), RPNNumber(99))
    dispatch("MPUT", s, {})
    r = top(s)
    assert r.value[0][1].value == 99


def test_con_vector():
    s = make_stack(RPNNumber(3), RPNNumber(5))
    dispatch("CON", s, {})
    r = top(s)
    assert isinstance(r, RPNVector)
    assert len(r.value) == 3
    assert all(x.value == 5 for x in r.value)


def test_con_matrix():
    s = make_stack(RPNList([RPNNumber(2), RPNNumber(3)]), RPNNumber(7))
    dispatch("CON", s, {})
    r = top(s)
    assert isinstance(r, RPNMatrix)
    assert r.rows() == 2 and r.cols() == 3
    assert all(r.value[i][j].value == 7 for i in range(2) for j in range(3))


def test_to_matrix():
    s = make_stack(1, 2, 3, 4, 5, 6, 2, 3)
    dispatch("TOMAT", s, {})
    r = top(s)
    assert isinstance(r, RPNMatrix)
    assert r.rows() == 2 and r.cols() == 3
    assert r.value[0][0].value == 1
    assert r.value[1][2].value == 6


def test_rref():
    """RREF of [[1 2 3][4 5 6]] should give [[1 0 -1][0 1 2]]."""
    m = RPNMatrix([
        [RPNNumber(1), RPNNumber(2), RPNNumber(3)],
        [RPNNumber(4), RPNNumber(5), RPNNumber(6)],
    ])
    s = make_stack(m)
    dispatch("RREF", s, {})
    r = top(s)
    assert abs(r.value[0][0].value - 1) < 1e-10
    assert abs(r.value[0][2].value - (-1)) < 1e-10
    assert abs(r.value[1][1].value - 1) < 1e-10
    assert abs(r.value[1][2].value - 2) < 1e-10
