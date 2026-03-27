"""Scientific/math operations."""

import math
from operations import register, require_args, require_type, RPNError
from rpn_types import RPNNumber

# --- Angle mode state ---
_angle_mode = "RAD"  # RAD, DEG, GRAD


def _get_angle_mode():
    return _angle_mode


def _to_radians(value):
    if _angle_mode == "DEG":
        return math.radians(value)
    elif _angle_mode == "GRAD":
        return value * math.pi / 200
    return value


def _from_radians(value):
    if _angle_mode == "DEG":
        return math.degrees(value)
    elif _angle_mode == "GRAD":
        return value * 200 / math.pi
    return value


@register("RAD")
def op_rad(stack, variables, executor):
    global _angle_mode
    _angle_mode = "RAD"


@register("DEG")
def op_deg(stack, variables, executor):
    global _angle_mode
    _angle_mode = "DEG"


@register("GRAD")
def op_grad(stack, variables, executor):
    global _angle_mode
    _angle_mode = "GRAD"


# --- Trigonometric ---

@register("SIN")
def op_sin(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.sin(_to_radians(a.value))))


@register("COS")
def op_cos(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.cos(_to_radians(a.value))))


@register("TAN")
def op_tan(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.tan(_to_radians(a.value))))


@register("ASIN")
def op_asin(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    if a.value < -1 or a.value > 1:
        stack.push(a)
        raise RPNError("Bad Argument Value")
    stack.push(RPNNumber(_from_radians(math.asin(a.value))))


@register("ACOS")
def op_acos(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    if a.value < -1 or a.value > 1:
        stack.push(a)
        raise RPNError("Bad Argument Value")
    stack.push(RPNNumber(_from_radians(math.acos(a.value))))


@register("ATAN")
def op_atan(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(_from_radians(math.atan(a.value))))


# --- Logarithmic / Exponential ---

@register("LOG")
def op_log(stack, variables, executor):
    """Base-10 logarithm."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    if a.value <= 0:
        stack.push(a)
        raise RPNError("Bad Argument Value")
    stack.push(RPNNumber(math.log10(a.value)))


@register("ALOG")
def op_alog(stack, variables, executor):
    """10^x."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(10 ** a.value))


@register("LN")
def op_ln(stack, variables, executor):
    """Natural logarithm."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    if a.value <= 0:
        stack.push(a)
        raise RPNError("Bad Argument Value")
    stack.push(RPNNumber(math.log(a.value)))


@register("EXP")
def op_exp(stack, variables, executor):
    """e^x."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.exp(a.value)))


# --- Power / Root ---

@register("^", "POW")
def op_pow(stack, variables, executor):
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNNumber)
    require_type(b, RPNNumber)
    try:
        stack.push(RPNNumber(a.value ** b.value))
    except (OverflowError, ValueError) as e:
        stack.push(a)
        stack.push(b)
        raise RPNError(str(e))


@register("SQRT", "√")
def op_sqrt(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    if a.value < 0:
        stack.push(a)
        raise RPNError("Bad Argument Value")
    stack.push(RPNNumber(math.sqrt(a.value)))


@register("SQ")
def op_sq(stack, variables, executor):
    """x^2."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(a.value ** 2))


@register("INV")
def op_inv(stack, variables, executor):
    """1/x."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    if a.value == 0:
        stack.push(a)
        raise RPNError("Infinite Result")
    stack.push(RPNNumber(1 / a.value))


@register("XROOT")
def op_xroot(stack, variables, executor):
    """y^(1/x)."""
    require_args(stack, 2)
    x = stack.pop()
    y = stack.pop()
    require_type(x, RPNNumber)
    require_type(y, RPNNumber)
    if x.value == 0:
        stack.push(y)
        stack.push(x)
        raise RPNError("Infinite Result")
    stack.push(RPNNumber(y.value ** (1 / x.value)))


# --- Constants ---

@register("PI", "π")
def op_pi(stack, variables, executor):
    stack.push(RPNNumber(math.pi))


@register("E")
def op_e_const(stack, variables, executor):
    stack.push(RPNNumber(math.e))


# --- Hyperbolic ---

@register("SINH")
def op_sinh(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.sinh(a.value)))


@register("COSH")
def op_cosh(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.cosh(a.value)))


@register("TANH")
def op_tanh(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.tanh(a.value)))


# --- Conversions ---

@register("D->R")
def op_d2r(stack, variables, executor):
    """Degrees to radians."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.radians(a.value)))


@register("R->D")
def op_r2d(stack, variables, executor):
    """Radians to degrees."""
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    stack.push(RPNNumber(math.degrees(a.value)))


@register("FACT", "!")
def op_factorial(stack, variables, executor):
    require_args(stack, 1)
    a = stack.pop()
    require_type(a, RPNNumber)
    if not a.is_int() or a.value < 0:
        stack.push(a)
        raise RPNError("Bad Argument Value")
    stack.push(RPNNumber(math.factorial(a.value)))
