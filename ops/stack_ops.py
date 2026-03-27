"""Stack manipulation operations."""

from operations import register, require_args, RPNError
from rpn_types import RPNNumber, rpn_copy


@register("DUP")
def op_dup(stack, variables, executor):
    require_args(stack, 1)
    stack.push(rpn_copy(stack.peek(1)))


@register("DUP2")
def op_dup2(stack, variables, executor):
    require_args(stack, 2)
    a = stack.peek(2)
    b = stack.peek(1)
    stack.push(rpn_copy(a))
    stack.push(rpn_copy(b))


@register("DUPN")
def op_dupn(stack, variables, executor):
    require_args(stack, 1)
    n_obj = stack.pop()
    if not isinstance(n_obj, RPNNumber) or not n_obj.is_int() or n_obj.value < 0:
        stack.push(n_obj)
        raise RPNError("Bad Argument Type")
    n = n_obj.value
    require_args(stack, n)
    items = [rpn_copy(stack.peek(n - i)) for i in range(n)]
    for item in items:
        stack.push(item)


@register("DROP")
def op_drop(stack, variables, executor):
    require_args(stack, 1)
    stack.pop()


@register("DROP2")
def op_drop2(stack, variables, executor):
    require_args(stack, 2)
    stack.pop()
    stack.pop()


@register("DROPN")
def op_dropn(stack, variables, executor):
    require_args(stack, 1)
    n_obj = stack.pop()
    if not isinstance(n_obj, RPNNumber) or not n_obj.is_int() or n_obj.value < 0:
        stack.push(n_obj)
        raise RPNError("Bad Argument Type")
    n = n_obj.value
    require_args(stack, n)
    for _ in range(n):
        stack.pop()


@register("SWAP")
def op_swap(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    stack.push(b)
    stack.push(a)


@register("OVER")
def op_over(stack, variables, executor):
    require_args(stack, 2)
    stack.push(rpn_copy(stack.peek(2)))


@register("ROT")
def op_rot(stack, variables, executor):
    """Rotate 3rd item to top: 3 2 1 -> 2 1 3."""
    require_args(stack, 3)
    stack.roll(3)


@register("UNROT")
def op_unrot(stack, variables, executor):
    """Reverse rotate: 3 2 1 -> 1 3 2."""
    require_args(stack, 3)
    stack.rolld(3)


@register("ROLL")
def op_roll(stack, variables, executor):
    require_args(stack, 1)
    n_obj = stack.pop()
    if not isinstance(n_obj, RPNNumber) or not n_obj.is_int() or n_obj.value < 1:
        stack.push(n_obj)
        raise RPNError("Bad Argument Type")
    n = n_obj.value
    require_args(stack, n)
    stack.roll(n)


@register("ROLLD")
def op_rolld(stack, variables, executor):
    require_args(stack, 1)
    n_obj = stack.pop()
    if not isinstance(n_obj, RPNNumber) or not n_obj.is_int() or n_obj.value < 1:
        stack.push(n_obj)
        raise RPNError("Bad Argument Type")
    n = n_obj.value
    require_args(stack, n)
    stack.rolld(n)


@register("PICK")
def op_pick(stack, variables, executor):
    require_args(stack, 1)
    n_obj = stack.pop()
    if not isinstance(n_obj, RPNNumber) or not n_obj.is_int() or n_obj.value < 1:
        stack.push(n_obj)
        raise RPNError("Bad Argument Type")
    n = n_obj.value
    require_args(stack, n)
    stack.pick(n)


@register("DEPTH")
def op_depth(stack, variables, executor):
    stack.push(RPNNumber(stack.depth()))


@register("CLEAR", "CLR")
def op_clear(stack, variables, executor):
    stack.clear()


@register("NDUP")
def op_ndup(stack, variables, executor):
    """Duplicate top item n times."""
    require_args(stack, 2)
    n_obj = stack.pop()
    if not isinstance(n_obj, RPNNumber) or not n_obj.is_int() or n_obj.value < 0:
        stack.push(n_obj)
        raise RPNError("Bad Argument Type")
    n = n_obj.value
    require_args(stack, 1)
    item = stack.peek(1)
    for _ in range(n - 1):
        stack.push(rpn_copy(item))
