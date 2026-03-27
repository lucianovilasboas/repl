"""List operations."""

from operations import register, require_args, require_type, RPNError
from rpn_types import RPNNumber, RPNList, rpn_copy


@register("LIST->", "LIST→", "OBJ->")
def op_list_explode(stack, variables, executor):
    """Explode list onto stack: { 1 2 3 } LIST→ → 1 2 3 3."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    for item in lst.value:
        stack.push(rpn_copy(item))
    stack.push(RPNNumber(len(lst.value)))


@register("->LIST", "→LIST")
def op_list_build(stack, variables, executor):
    """Build list from n stack items: 1 2 3 3 →LIST → { 1 2 3 }."""
    require_args(stack, 1)
    n_obj = stack.pop()
    require_type(n_obj, RPNNumber)
    if not n_obj.is_int() or n_obj.value < 0:
        stack.push(n_obj)
        raise RPNError("Bad Argument Type")
    n = n_obj.value
    require_args(stack, n)
    items = []
    for _ in range(n):
        items.insert(0, stack.pop())
    stack.push(RPNList(items))


@register("GET")
def op_get(stack, variables, executor):
    """Get item from list: { list } index GET → item."""
    require_args(stack, 2)
    idx_obj = stack.pop()
    lst = stack.pop()
    require_type(lst, RPNList)
    require_type(idx_obj, RPNNumber)
    if not idx_obj.is_int():
        stack.push(lst)
        stack.push(idx_obj)
        raise RPNError("Bad Argument Type")
    idx = idx_obj.value
    if idx < 1 or idx > len(lst):
        stack.push(lst)
        stack.push(idx_obj)
        raise RPNError("Bad Argument Value (index out of range)")
    stack.push(rpn_copy(lst.value[idx - 1]))


@register("PUT")
def op_put(stack, variables, executor):
    """Put item into list: { list } index value PUT → { new_list }."""
    require_args(stack, 3)
    value = stack.pop()
    idx_obj = stack.pop()
    lst = stack.pop()
    require_type(lst, RPNList)
    require_type(idx_obj, RPNNumber)
    if not idx_obj.is_int():
        stack.push(lst)
        stack.push(idx_obj)
        stack.push(value)
        raise RPNError("Bad Argument Type")
    idx = idx_obj.value
    if idx < 1 or idx > len(lst):
        stack.push(lst)
        stack.push(idx_obj)
        stack.push(value)
        raise RPNError("Bad Argument Value (index out of range)")
    new_list = rpn_copy(lst)
    new_list.value[idx - 1] = rpn_copy(value)
    stack.push(new_list)


@register("SIZE")
def op_size(stack, variables, executor):
    """Size of list or string."""
    require_args(stack, 1)
    obj = stack.pop()
    if isinstance(obj, RPNList):
        stack.push(RPNNumber(len(obj.value)))
    elif isinstance(obj, (str,)):
        stack.push(RPNNumber(len(obj)))
    else:
        from rpn_types import RPNString
        if isinstance(obj, RPNString):
            stack.push(RPNNumber(len(obj.value)))
        else:
            stack.push(obj)
            raise RPNError("Bad Argument Type")


@register("HEAD")
def op_head(stack, variables, executor):
    """First element of list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    if len(lst) == 0:
        stack.push(lst)
        raise RPNError("Bad Argument Value (empty list)")
    stack.push(rpn_copy(lst.value[0]))


@register("TAIL")
def op_tail(stack, variables, executor):
    """List without first element."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    if len(lst) == 0:
        stack.push(lst)
        raise RPNError("Bad Argument Value (empty list)")
    stack.push(RPNList(lst.value[1:]))


@register("REVLIST")
def op_revlist(stack, variables, executor):
    """Reverse a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    stack.push(RPNList(list(reversed(lst.value))))


@register("SORT")
def op_sort(stack, variables, executor):
    """Sort a list of numbers."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    try:
        sorted_items = sorted(lst.value, key=lambda x: x.value)
        stack.push(RPNList(sorted_items))
    except (AttributeError, TypeError):
        stack.push(lst)
        raise RPNError("Bad Argument Type (can only sort numbers)")
