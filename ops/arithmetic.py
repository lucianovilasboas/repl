"""Arithmetic operations: +, -, *, /, NEG, ABS, MOD, IP, FP, MIN, MAX, SIGN, %."""

import math
from operations import register, require_args, require_type, RPNError
from rpn_types import RPNNumber, RPNString, RPNList, RPNVector, RPNMatrix


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
    # Vector + Vector
    elif isinstance(a, RPNVector) and isinstance(b, RPNVector):
        if len(a.value) != len(b.value):
            stack.push(a); stack.push(b)
            raise RPNError("Invalid Dimension")
        stack.push(RPNVector([RPNNumber(x.value + y.value) for x, y in zip(a.value, b.value)]))
    # Matrix + Matrix
    elif isinstance(a, RPNMatrix) and isinstance(b, RPNMatrix):
        if a.shape() != b.shape():
            stack.push(a); stack.push(b)
            raise RPNError("Invalid Dimension")
        rows = [[RPNNumber(a.value[i][j].value + b.value[i][j].value)
                 for j in range(a.cols())] for i in range(a.rows())]
        stack.push(RPNMatrix(rows))
    # Scalar + Vector / Vector + Scalar
    elif isinstance(a, RPNVector) and isinstance(b, RPNNumber):
        stack.push(RPNVector([RPNNumber(x.value + b.value) for x in a.value]))
    elif isinstance(a, RPNNumber) and isinstance(b, RPNVector):
        stack.push(RPNVector([RPNNumber(a.value + x.value) for x in b.value]))
    # Scalar + Matrix / Matrix + Scalar
    elif isinstance(a, RPNMatrix) and isinstance(b, RPNNumber):
        rows = [[RPNNumber(a.value[i][j].value + b.value)
                 for j in range(a.cols())] for i in range(a.rows())]
        stack.push(RPNMatrix(rows))
    elif isinstance(a, RPNNumber) and isinstance(b, RPNMatrix):
        rows = [[RPNNumber(a.value + b.value[i][j].value)
                 for j in range(b.cols())] for i in range(b.rows())]
        stack.push(RPNMatrix(rows))
    else:
        stack.push(a)
        stack.push(b)
        raise RPNError("Bad Argument Type")


@register("-")
def op_sub(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    # Number - Number
    if isinstance(a, RPNNumber) and isinstance(b, RPNNumber):
        stack.push(RPNNumber(a.value - b.value))
    # Vector - Vector
    elif isinstance(a, RPNVector) and isinstance(b, RPNVector):
        if len(a.value) != len(b.value):
            stack.push(a); stack.push(b)
            raise RPNError("Invalid Dimension")
        stack.push(RPNVector([RPNNumber(x.value - y.value) for x, y in zip(a.value, b.value)]))
    # Matrix - Matrix
    elif isinstance(a, RPNMatrix) and isinstance(b, RPNMatrix):
        if a.shape() != b.shape():
            stack.push(a); stack.push(b)
            raise RPNError("Invalid Dimension")
        rows = [[RPNNumber(a.value[i][j].value - b.value[i][j].value)
                 for j in range(a.cols())] for i in range(a.rows())]
        stack.push(RPNMatrix(rows))
    # Scalar - Vector / Vector - Scalar
    elif isinstance(a, RPNVector) and isinstance(b, RPNNumber):
        stack.push(RPNVector([RPNNumber(x.value - b.value) for x in a.value]))
    elif isinstance(a, RPNNumber) and isinstance(b, RPNVector):
        stack.push(RPNVector([RPNNumber(a.value - x.value) for x in b.value]))
    # Scalar - Matrix / Matrix - Scalar
    elif isinstance(a, RPNMatrix) and isinstance(b, RPNNumber):
        rows = [[RPNNumber(a.value[i][j].value - b.value)
                 for j in range(a.cols())] for i in range(a.rows())]
        stack.push(RPNMatrix(rows))
    elif isinstance(a, RPNNumber) and isinstance(b, RPNMatrix):
        rows = [[RPNNumber(a.value - b.value[i][j].value)
                 for j in range(b.cols())] for i in range(b.rows())]
        stack.push(RPNMatrix(rows))
    else:
        stack.push(a); stack.push(b)
        raise RPNError("Bad Argument Type")


@register("*")
def op_mul(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    # Number * Number
    if isinstance(a, RPNNumber) and isinstance(b, RPNNumber):
        stack.push(RPNNumber(a.value * b.value))
    # Scalar * Vector / Vector * Scalar
    elif isinstance(a, RPNVector) and isinstance(b, RPNNumber):
        stack.push(RPNVector([RPNNumber(x.value * b.value) for x in a.value]))
    elif isinstance(a, RPNNumber) and isinstance(b, RPNVector):
        stack.push(RPNVector([RPNNumber(a.value * x.value) for x in b.value]))
    # Scalar * Matrix / Matrix * Scalar
    elif isinstance(a, RPNMatrix) and isinstance(b, RPNNumber):
        rows = [[RPNNumber(a.value[i][j].value * b.value)
                 for j in range(a.cols())] for i in range(a.rows())]
        stack.push(RPNMatrix(rows))
    elif isinstance(a, RPNNumber) and isinstance(b, RPNMatrix):
        rows = [[RPNNumber(a.value * b.value[i][j].value)
                 for j in range(b.cols())] for i in range(b.rows())]
        stack.push(RPNMatrix(rows))
    # Matrix * Matrix
    elif isinstance(a, RPNMatrix) and isinstance(b, RPNMatrix):
        if a.cols() != b.rows():
            stack.push(a); stack.push(b)
            raise RPNError("Invalid Dimension")
        av, bv = [[x.value for x in row] for row in a.value], [[x.value for x in row] for row in b.value]
        rows = [[RPNNumber(sum(av[i][k] * bv[k][j] for k in range(a.cols())))
                 for j in range(b.cols())] for i in range(a.rows())]
        stack.push(RPNMatrix(rows))
    # Matrix * Vector (treat vector as column)
    elif isinstance(a, RPNMatrix) and isinstance(b, RPNVector):
        if a.cols() != len(b.value):
            stack.push(a); stack.push(b)
            raise RPNError("Invalid Dimension")
        av = [[x.value for x in row] for row in a.value]
        bv = [x.value for x in b.value]
        result = [RPNNumber(sum(av[i][k] * bv[k] for k in range(a.cols()))) for i in range(a.rows())]
        stack.push(RPNVector(result))
    else:
        stack.push(a); stack.push(b)
        raise RPNError("Bad Argument Type")


@register("/")
def op_div(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    # Number / Number
    if isinstance(a, RPNNumber) and isinstance(b, RPNNumber):
        if b.value == 0:
            stack.push(a); stack.push(b)
            raise RPNError("Infinite Result (division by zero)")
        result = a.value / b.value
        stack.push(RPNNumber(result))
    # Vector / Scalar
    elif isinstance(a, RPNVector) and isinstance(b, RPNNumber):
        if b.value == 0:
            stack.push(a); stack.push(b)
            raise RPNError("Infinite Result (division by zero)")
        stack.push(RPNVector([RPNNumber(x.value / b.value) for x in a.value]))
    # Matrix / Scalar
    elif isinstance(a, RPNMatrix) and isinstance(b, RPNNumber):
        if b.value == 0:
            stack.push(a); stack.push(b)
            raise RPNError("Infinite Result (division by zero)")
        rows = [[RPNNumber(a.value[i][j].value / b.value)
                 for j in range(a.cols())] for i in range(a.rows())]
        stack.push(RPNMatrix(rows))
    else:
        stack.push(a); stack.push(b)
        raise RPNError("Bad Argument Type")


@register("NEG", "CHS")
def op_neg(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    if isinstance(a, RPNNumber):
        stack.push(RPNNumber(-a.value))
    elif isinstance(a, RPNVector):
        stack.push(RPNVector([RPNNumber(-x.value) for x in a.value]))
    elif isinstance(a, RPNMatrix):
        rows = [[RPNNumber(-a.value[i][j].value)
                 for j in range(a.cols())] for i in range(a.rows())]
        stack.push(RPNMatrix(rows))
    else:
        stack.push(a)
        raise RPNError("Bad Argument Type")


@register("ABS")
def op_abs(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    if isinstance(a, RPNNumber):
        stack.push(RPNNumber(abs(a.value)))
    elif isinstance(a, RPNVector):
        # ABS of a vector = Euclidean norm (like HP 50g)
        vals = [x.value for x in a.value]
        stack.push(RPNNumber(math.sqrt(sum(x * x for x in vals))))
    else:
        stack.push(a)
        raise RPNError("Bad Argument Type")


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
