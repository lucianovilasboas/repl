"""Display formatting — HP 50g style stack display."""


def format_value(obj, num_format="STD", fix_digits=None):
    """Format an RPN object for display."""
    from rpn_types import RPNNumber
    if isinstance(obj, RPNNumber):
        return _format_number(obj.value, num_format, fix_digits)
    return obj.rpn_repr()


def _format_number(value, num_format="STD", fix_digits=None):
    """Format a number according to the display mode."""
    if isinstance(value, int):
        return str(value)

    if num_format == "FIX" and fix_digits is not None:
        return f"{value:.{fix_digits}f}"
    elif num_format == "SCI" and fix_digits is not None:
        return f"{value:.{fix_digits}e}"
    elif num_format == "ENG" and fix_digits is not None:
        return _eng_format(value, fix_digits)
    else:
        # STD: remove trailing zeros
        s = f"{value:.12g}"
        return s


def _eng_format(value, digits):
    """Format number in engineering notation (exponent multiple of 3)."""
    if value == 0:
        return "0"
    import math
    exp = int(math.floor(math.log10(abs(value))))
    eng_exp = (exp // 3) * 3
    mantissa = value / (10 ** eng_exp)
    if eng_exp == 0:
        return f"{mantissa:.{digits}f}"
    return f"{mantissa:.{digits}f}e{eng_exp}"


def display_stack(stack, lines=4, num_format="STD", fix_digits=None):
    """Return a string showing the stack in HP 50g style (4 visible levels).

    Example:
        4:
        3:
        2:           42
        1:            7
    """
    data = stack.to_list()
    output = []
    for level in range(lines, 0, -1):
        idx = len(data) - level
        if idx >= 0:
            val_str = format_value(data[idx], num_format, fix_digits)
        else:
            val_str = ""
        output.append(f"  {level}: {val_str:>40}")
    return "\n".join(output)


def display_header(angle_mode="RAD", num_format="STD", fix_digits=None):
    """Display mode indicators like the HP 50g top bar."""
    parts = [angle_mode]
    if num_format != "STD":
        parts.append(f"{num_format} {fix_digits}" if fix_digits is not None else num_format)
    else:
        parts.append("STD")
    return "  { " + " ".join(parts) + " }"
