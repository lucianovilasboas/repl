"""Logic operations and conditional helpers."""

from operations import register, require_args, require_type
from rpn_types import RPNNumber


def _truthy(obj):
    """HP 50g truthiness: 0 is false, non-zero is true."""
    if isinstance(obj, RPNNumber):
        return obj.value != 0
    return True


@register("AND")
def op_and(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(1 if _truthy(a) and _truthy(b) else 0))


@register("OR")
def op_or(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(1 if _truthy(a) or _truthy(b) else 0))


@register("XOR")
def op_xor(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    stack.push(RPNNumber(1 if _truthy(a) != _truthy(b) else 0))


@register("NOT")
def op_not(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(0 if _truthy(a) else 1))


@register("IFT")
def op_ift(stack, variables, executor):
    """IF-THEN: condition obj IFT -> if condition, push obj."""
    require_args(stack, 2)
    then_obj = stack.pop()
    cond = stack.pop()
    if _truthy(cond):
        from rpn_types import RPNProgram
        if isinstance(then_obj, RPNProgram) and executor:
            executor(then_obj.value, stack, variables)
        else:
            stack.push(then_obj)


@register("IFTE")
def op_ifte(stack, variables, executor):
    """IF-THEN-ELSE: condition then_obj else_obj IFTE."""
    require_args(stack, 3)
    else_obj = stack.pop()
    then_obj = stack.pop()
    cond = stack.pop()
    chosen = then_obj if _truthy(cond) else else_obj
    from rpn_types import RPNProgram
    if isinstance(chosen, RPNProgram) and executor:
        executor(chosen.value, stack, variables)
    else:
        stack.push(chosen)
