"""Variable operations: STO, RCL, PURGE, VARS."""

from operations import register, require_args, require_type, RPNError
from rpn_types import RPNSymbol, RPNNumber, RPNString, rpn_copy


@register("STO")
def op_sto(stack, variables, executor):
    """Store: value 'NAME' STO."""
    require_args(stack, 2)
    name_obj = stack.pop()
    value = stack.pop()
    if isinstance(name_obj, RPNSymbol):
        name = name_obj.value
    elif isinstance(name_obj, RPNString):
        name = name_obj.value.upper()
    else:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError("Bad Argument Type (expected 'name')")
    variables[name] = rpn_copy(value)


@register("RCL")
def op_rcl(stack, variables, executor):
    """Recall: 'NAME' RCL."""
    require_args(stack, 1)
    name_obj = stack.pop()
    if isinstance(name_obj, RPNSymbol):
        name = name_obj.value
    elif isinstance(name_obj, RPNString):
        name = name_obj.value.upper()
    else:
        stack.push(name_obj)
        raise RPNError("Bad Argument Type")
    if name not in variables:
        stack.push(name_obj)
        raise RPNError(f"Undefined Name: {name}")
    stack.push(rpn_copy(variables[name]))


@register("PURGE")
def op_purge(stack, variables, executor):
    """Delete a variable: 'NAME' PURGE."""
    require_args(stack, 1)
    name_obj = stack.pop()
    if isinstance(name_obj, RPNSymbol):
        name = name_obj.value
    elif isinstance(name_obj, RPNString):
        name = name_obj.value.upper()
    else:
        stack.push(name_obj)
        raise RPNError("Bad Argument Type")
    if name in variables:
        del variables[name]


@register("VARS")
def op_vars(stack, variables, executor):
    """List all variable names — prints to console."""
    if not variables:
        print("  (no variables)")
    else:
        for name, val in sorted(variables.items()):
            print(f"  {name}: {val.rpn_repr()}")


@register("SNEG")
def op_sneg(stack, variables, executor):
    """Negate value in variable: 'NAME' SNEG (STO NEGate)."""
    require_args(stack, 1)
    name_obj = stack.pop()
    if isinstance(name_obj, RPNSymbol):
        name = name_obj.value
    else:
        stack.push(name_obj)
        raise RPNError("Bad Argument Type")
    if name not in variables:
        stack.push(name_obj)
        raise RPNError(f"Undefined Name: {name}")
    val = variables[name]
    require_type(val, RPNNumber, msg="Bad Argument Type (variable is not a number)")
    variables[name] = RPNNumber(-val.value)


@register("STO+")
def op_sto_add(stack, variables, executor):
    """Add to variable: value 'NAME' STO+."""
    require_args(stack, 2)
    name_obj = stack.pop()
    value = stack.pop()
    if isinstance(name_obj, RPNSymbol):
        name = name_obj.value
    else:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError("Bad Argument Type")
    if name not in variables:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError(f"Undefined Name: {name}")
    require_type(value, RPNNumber)
    require_type(variables[name], RPNNumber, msg="Bad Argument Type (variable is not a number)")
    variables[name] = RPNNumber(variables[name].value + value.value)


@register("STO-")
def op_sto_sub(stack, variables, executor):
    require_args(stack, 2)
    name_obj = stack.pop()
    value = stack.pop()
    if isinstance(name_obj, RPNSymbol):
        name = name_obj.value
    else:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError("Bad Argument Type")
    if name not in variables:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError(f"Undefined Name: {name}")
    require_type(value, RPNNumber)
    require_type(variables[name], RPNNumber, msg="Bad Argument Type")
    variables[name] = RPNNumber(variables[name].value - value.value)


@register("STO*")
def op_sto_mul(stack, variables, executor):
    require_args(stack, 2)
    name_obj = stack.pop()
    value = stack.pop()
    if isinstance(name_obj, RPNSymbol):
        name = name_obj.value
    else:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError("Bad Argument Type")
    if name not in variables:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError(f"Undefined Name: {name}")
    require_type(value, RPNNumber)
    require_type(variables[name], RPNNumber, msg="Bad Argument Type")
    variables[name] = RPNNumber(variables[name].value * value.value)


@register("STO/")
def op_sto_div(stack, variables, executor):
    require_args(stack, 2)
    name_obj = stack.pop()
    value = stack.pop()
    if isinstance(name_obj, RPNSymbol):
        name = name_obj.value
    else:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError("Bad Argument Type")
    if name not in variables:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError(f"Undefined Name: {name}")
    require_type(value, RPNNumber)
    require_type(variables[name], RPNNumber, msg="Bad Argument Type")
    if value.value == 0:
        stack.push(value)
        stack.push(name_obj)
        raise RPNError("Infinite Result")
    variables[name] = RPNNumber(variables[name].value / value.value)
