"""Comparison operations — push 1 (true) or 0 (false) like the HP 50g."""

from operations import register, require_args, require_type
from rpn_types import RPNNumber


@register("==", "SAME")
def op_eq(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    stack.push(RPNNumber(1 if a == b else 0))


@register("!=", "≠")
def op_ne(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    stack.push(RPNNumber(0 if a == b else 1))


@register("<")
def op_lt(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(1 if a.value < b.value else 0))


@register(">")
def op_gt(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(1 if a.value > b.value else 0))


@register("<=", "≤")
def op_le(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(1 if a.value <= b.value else 0))


@register(">=", "≥")
def op_ge(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(1 if a.value >= b.value else 0))
