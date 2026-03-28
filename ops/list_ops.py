"""List operations."""

import math
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


# ── Helper ────────────────────────────────────────────────────────────

def _require_num_list(lst):
    """Assert all elements are RPNNumber and list is non-empty."""
    if len(lst.value) == 0:
        raise RPNError("Bad Argument Value (empty list)")
    for item in lst.value:
        if not isinstance(item, RPNNumber):
            raise RPNError("Bad Argument Type (list must contain only numbers)")
    return [item.value for item in lst.value]


# ── Aggregate / Statistical ──────────────────────────────────────────

@register("ΣLIST", "SUMLIST")
def op_sumlist(stack, variables, executor):
    """Sum of all elements in a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    stack.push(RPNNumber(sum(vals)))


@register("SSQLIST")
def op_ssqlist(stack, variables, executor):
    """Sum of squares of elements in a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    stack.push(RPNNumber(sum(x * x for x in vals)))


@register("ΠLIST", "PRODLIST")
def op_prodlist(stack, variables, executor):
    """Product of all elements in a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    result = 1
    for v in vals:
        result *= v
    stack.push(RPNNumber(result))


@register("MAXLIST")
def op_maxlist(stack, variables, executor):
    """Maximum element of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    stack.push(RPNNumber(max(vals)))


@register("MINLIST")
def op_minlist(stack, variables, executor):
    """Minimum element of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    stack.push(RPNNumber(min(vals)))


@register("MEAN")
def op_mean(stack, variables, executor):
    """Arithmetic mean of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    stack.push(RPNNumber(sum(vals) / len(vals)))


@register("MEDIAN")
def op_median(stack, variables, executor):
    """Median of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    s = sorted(vals)
    n = len(s)
    if n % 2 == 1:
        stack.push(RPNNumber(s[n // 2]))
    else:
        stack.push(RPNNumber((s[n // 2 - 1] + s[n // 2]) / 2))


@register("SDEV")
def op_sdev(stack, variables, executor):
    """Sample standard deviation (n-1) of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    n = len(vals)
    if n < 2:
        stack.push(lst)
        raise RPNError("Too Few Arguments (need at least 2 elements)")
    mean = sum(vals) / n
    var = sum((x - mean) ** 2 for x in vals) / (n - 1)
    stack.push(RPNNumber(math.sqrt(var)))


@register("PSDEV")
def op_psdev(stack, variables, executor):
    """Population standard deviation (n) of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    n = len(vals)
    if n < 1:
        stack.push(lst)
        raise RPNError("Bad Argument Value (empty list)")
    mean = sum(vals) / n
    var = sum((x - mean) ** 2 for x in vals) / n
    stack.push(RPNNumber(math.sqrt(var)))


@register("VAR")
def op_var(stack, variables, executor):
    """Sample variance (n-1) of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    n = len(vals)
    if n < 2:
        stack.push(lst)
        raise RPNError("Too Few Arguments (need at least 2 elements)")
    mean = sum(vals) / n
    stack.push(RPNNumber(sum((x - mean) ** 2 for x in vals) / (n - 1)))


@register("PVAR")
def op_pvar(stack, variables, executor):
    """Population variance (n) of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    n = len(vals)
    if n < 1:
        stack.push(lst)
        raise RPNError("Bad Argument Value (empty list)")
    mean = sum(vals) / n
    stack.push(RPNNumber(sum((x - mean) ** 2 for x in vals) / n))


@register("TOTAL")
def op_total(stack, variables, executor):
    """Running totals (cumulative sum) of a list."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    acc = 0
    result = []
    for v in vals:
        acc += v
        result.append(RPNNumber(acc))
    stack.push(RPNList(result))


@register("DELTALIST", "ΔLIST")
def op_deltalist(stack, variables, executor):
    """Successive differences: {a b c} → {b-a c-b}."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    vals = _require_num_list(lst)
    if len(vals) < 2:
        stack.push(lst)
        raise RPNError("Too Few Arguments (need at least 2 elements)")
    result = [RPNNumber(vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
    stack.push(RPNList(result))


@register("ADD")
def op_add_lists(stack, variables, executor):
    """Element-wise addition of two lists of same size."""
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNList)
    require_type(b, RPNList)
    if len(a.value) != len(b.value):
        stack.push(a); stack.push(b)
        raise RPNError("Invalid Dimension")
    result = []
    for x, y in zip(a.value, b.value):
        if not isinstance(x, RPNNumber) or not isinstance(y, RPNNumber):
            stack.push(a); stack.push(b)
            raise RPNError("Bad Argument Type")
        result.append(RPNNumber(x.value + y.value))
    stack.push(RPNList(result))


@register("SUB")
def op_sub_lists(stack, variables, executor):
    """Extract sublist: { list } start end SUB → { sublist }."""
    require_args(stack, 3)
    end_obj = stack.pop()
    start_obj = stack.pop()
    lst = stack.pop()
    require_type(lst, RPNList)
    require_type(start_obj, RPNNumber)
    require_type(end_obj, RPNNumber)
    s = int(start_obj.value) - 1
    e = int(end_obj.value)
    if s < 0 or e > len(lst.value) or s >= e:
        stack.push(lst); stack.push(start_obj); stack.push(end_obj)
        raise RPNError("Bad Argument Value")
    stack.push(RPNList(lst.value[s:e]))


@register("DOLIST")
def op_dolist(stack, variables, executor):
    """Apply a program to each element of a list: { list } « prog » DOLIST."""
    require_args(stack, 2)
    from rpn_types import RPNProgram
    prog = stack.pop()
    lst = stack.pop()
    require_type(lst, RPNList)
    require_type(prog, RPNProgram)
    if executor is None:
        stack.push(lst); stack.push(prog)
        raise RPNError("No executor available")
    from stack import Stack
    result = []
    for item in lst.value:
        tmp = Stack()
        tmp.push(rpn_copy(item))
        executor(prog.value, tmp, variables)
        if tmp.depth() > 0:
            result.append(tmp.pop())
    stack.push(RPNList(result))


@register("MAPLIST")
def op_maplist(stack, variables, executor):
    """Apply program to each element, push results as list (alias DOLIST kept for HP compat)."""
    op_dolist(stack, variables, executor)


@register("STREAM")
def op_stream(stack, variables, executor):
    """Reduce/fold a list with a binary program: { list } « prog » STREAM."""
    require_args(stack, 2)
    from rpn_types import RPNProgram
    prog = stack.pop()
    lst = stack.pop()
    require_type(lst, RPNList)
    require_type(prog, RPNProgram)
    vals = lst.value
    if len(vals) < 2:
        stack.push(lst); stack.push(prog)
        raise RPNError("Too Few Arguments (need at least 2 elements)")
    if executor is None:
        stack.push(lst); stack.push(prog)
        raise RPNError("No executor available")
    from stack import Stack
    acc = rpn_copy(vals[0])
    for item in vals[1:]:
        tmp = Stack()
        tmp.push(rpn_copy(acc))
        tmp.push(rpn_copy(item))
        executor(prog.value, tmp, variables)
        acc = tmp.pop()
    stack.push(acc)


@register("NSUB")
def op_nsub(stack, variables, executor):
    """Number of elements (same as SIZE for lists, kept for HP 50g compat)."""
    require_args(stack, 1)
    lst = stack.pop()
    require_type(lst, RPNList)
    stack.push(RPNNumber(len(lst.value)))
