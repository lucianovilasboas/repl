"""Arithmetic operations: +, -, *, /, NEG, ABS, MOD, IP, FP, MIN, MAX, SIGN, %."""

import math
from operations import register, require_args, require_type, RPNError
from rpn_types import RPNNumber, RPNString, RPNList


@register("+")
def op_add(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    # Number + Number
    if isinstance(a, RPNNumber) and isinstance(b, RPNNumber):
        stack.push(RPNNumber(a.value + b.value))
    # String concatenation
    elif isinstance(a, RPNString) and isinstance(b, RPNString):
        stack.push(RPNString(a.value + b.value))
    # List concatenation
    elif isinstance(a, RPNList) and isinstance(b, RPNList):
        stack.push(RPNList(a.value + b.value))
    # List + item or item + List
    elif isinstance(a, RPNList):
        stack.push(RPNList(a.value + [b]))
    elif isinstance(b, RPNList):
        stack.push(RPNList([a] + b.value))
    else:
        stack.push(a)
        stack.push(b)
        raise RPNError("Bad Argument Type")


@register("-")
def op_sub(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(a.value - b.value))


@register("*")
def op_mul(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(a.value * b.value))


@register("/")
def op_div(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    if b.value == 0:
        stack.push(a)
        stack.push(b)
        raise RPNError("Infinite Result (division by zero)")
    result = a.value / b.value
    stack.push(RPNNumber(result))


@register("NEG", "CHS")
def op_neg(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(-a.value))


@register("ABS")
def op_abs(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(abs(a.value)))


@register("MOD")
def op_mod(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    if b.value == 0:
        stack.push(a)
        stack.push(b)
        raise RPNError("Infinite Result (MOD by zero)")
    stack.push(RPNNumber(a.value % b.value))


@register("IP")
def op_ip(stack, variables, executor):
    """Integer part."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(int(a.value)))


@register("FP")
def op_fp(stack, variables, executor):
    """Fractional part."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(a.value - int(a.value)))


@register("MIN")
def op_min(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(min(a.value, b.value)))


@register("MAX")
def op_max(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(max(a.value, b.value)))


@register("SIGN")
def op_sign(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    if a.value > 0:
        stack.push(RPNNumber(1))
    elif a.value < 0:
        stack.push(RPNNumber(-1))
    else:
        stack.push(RPNNumber(0))


@register("%")
def op_percent(stack, variables, executor):
    """x % of y: y * x / 100."""
    require_args(stack, 2)
    x = stack.pop()
    y = stack.pop()
    require_type(x, RPNNumber)
    require_type(y, RPNNumber)
    stack.push(RPNNumber(y.value * x.value / 100))


@register("FLOOR")
def op_floor(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.floor(a.value)))


@register("CEIL")
def op_ceil(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.ceil(a.value)))
