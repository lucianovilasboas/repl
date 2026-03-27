"""Tests for the parser."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser import parse, tokenize
from rpn_types import RPNNumber, RPNString, RPNList, RPNProgram, RPNSymbol


def test_parse_integers():
    result = parse("3 4 5")
    assert result == [RPNNumber(3), RPNNumber(4), RPNNumber(5)]


def test_parse_floats():
    result = parse("3.14 2.0")
    assert result[0] == RPNNumber(3.14)


def test_parse_negative_number():
    result = parse("-5")
    assert result == [RPNNumber(-5)]


def test_parse_scientific_notation():
    result = parse("1.5e3")
    assert result == [RPNNumber(1500)]


def test_parse_string():
    result = parse('"hello world"')
    assert result == [RPNString("hello world")]


def test_parse_list():
    result = parse("{ 1 2 3 }")
    assert len(result) == 1
    lst = result[0]
    assert isinstance(lst, RPNList)
    assert len(lst.value) == 3


def test_parse_program_unicode():
    result = parse("« DUP * »")
    assert len(result) == 1
    prog = result[0]
    assert isinstance(prog, RPNProgram)
    assert prog.value == ["DUP", "*"]


def test_parse_program_ascii():
    result = parse("<< DUP * >>")
    assert len(result) == 1
    prog = result[0]
    assert isinstance(prog, RPNProgram)
    assert prog.value == ["DUP", "*"]


def test_parse_symbol():
    result = parse("'X'")
    assert result == [RPNSymbol("X")]


def test_parse_command():
    result = parse("DUP SWAP +")
    assert result == ["DUP", "SWAP", "+"]


def test_parse_mixed():
    result = parse("3 4 + 'X' STO")
    assert result[0] == RPNNumber(3)
    assert result[1] == RPNNumber(4)
    assert result[2] == "+"
    assert result[3] == RPNSymbol("X")
    assert result[4] == "STO"


def test_tokenize_nested_program():
    tokens = tokenize("<< IF 1 THEN << 2 >> END >>")
    assert len(tokens) == 1  # whole thing is one program


def test_tokenize_nested_list():
    tokens = tokenize("{ { 1 2 } { 3 4 } }")
    assert len(tokens) == 1


def test_parse_empty():
    result = parse("")
    assert result == []
