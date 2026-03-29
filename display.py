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


# ── HP 50g full calculator display ───────────────────────────────────

_W = 47  # inner width between ║ chars
_COL = 7  # soft-key column width (6 × 7 + 5 separators = 47)


def display_calculator(username, stack, variables, lines=4, num_format="STD",
                       fix_digits=None, angle_mode="RAD", error_msg=None):
    """Render the full HP 50g calculator display.

    ╔═══════════════════════════════════════════════╗
    ║ RAD  STD                           { HOME }  ║
    ╟───────────────────────────────────────────────╢
    ║  1:                                        7  ║
    ╠═══════╤═══════╤═══════╤═══════╤═══════╤═══════╣
    ║  VAR1 │  VAR2 │       │       │       │       ║
    ╚═══════╧═══════╧═══════╧═══════╧═══════╧═══════╝
    """
    W = _W
    top = f"  ╔{'═' * W}╗"
    sep = f"  ╟{'─' * W}╢"

    # ── Status bar ───────────────────────────────────────────────
    fmt_label = num_format
    if num_format != "STD" and fix_digits is not None:
        fmt_label = f"{num_format} {fix_digits}"
    status_l = f"{angle_mode}  {fmt_label}"
    status_r = f"{ {username} }"
    if error_msg:
        err_text = f">> {error_msg}"
        # space available between status_l + separator and status_r
        max_err = W - 2 - len(status_l) - 3 - len(status_r) - 1
        if max_err < 1:
            max_err = 1
        if len(err_text) > max_err:
            err_text = err_text[:max_err - 1] + "\u2026"
        mid = f" {err_text}"
        gap = W - 2 - len(status_l) - len(mid) - len(status_r)
        if gap < 1:
            gap = 1
        header = f"  ║ {status_l}{mid}{' ' * gap}{status_r} ║"
    else:
        gap = W - 2 - len(status_l) - len(status_r)
        if gap < 1:
            gap = 1
        header = f"  ║ {status_l}{' ' * gap}{status_r} ║"

    # ── Stack levels ─────────────────────────────────────────────
    data = stack.to_list()
    val_w = W - 6  # ' '(1) + level(2) + ':'(1) + ' '(1) + value(val_w) + ' '(1)
    rows = []
    for lvl in range(lines, 0, -1):
        idx = len(data) - lvl
        if idx >= 0:
            vs = format_value(data[idx], num_format, fix_digits)
        else:
            vs = ""
        if len(vs) > val_w:
            vs = vs[:val_w - 1] + "\u2026"
        rows.append(f"  ║ {lvl:>2}: {vs:>{val_w}} ║")

    # ── Soft-key bar (variables) ─────────────────────────────────
    names = list(variables.keys())[:6]
    names += [""] * (6 - len(names))

    sk_top = f"  ╠{'╤'.join('═' * _COL for _ in range(6))}╣"
    sk_mid = f"  ║{'│'.join(f'{n[:_COL]:^{_COL}}' for n in names)}║"
    sk_bot = f"  ╚{'╧'.join('═' * _COL for _ in range(6))}╝"

    # ── Assemble ─────────────────────────────────────────────────
    out = [top, header, sep]
    out.extend(rows)
    out.extend([sk_top, sk_mid, sk_bot])

    return "\n".join(out)
