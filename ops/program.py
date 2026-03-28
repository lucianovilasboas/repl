"""RPL program execution — « » programs, control structures, EVAL."""

from operations import register, require_args, require_type, RPNError, dispatch
from rpn_types import RPNProgram, RPNNumber, RPNSymbol, rpn_copy
from parser import parse_token, tokenize


MAX_RECURSION = 1000


def execute(tokens, stack, variables, depth=0):
    """Execute a list of raw token strings on the stack.

    This is the core RPL interpreter loop. It handles control structures
    (IF/THEN/ELSE/END, FOR/NEXT, START/NEXT, WHILE/REPEAT/END, DO/UNTIL/END)
    by consuming tokens from the stream.
    """
    if depth > MAX_RECURSION:
        raise RPNError("Maximum recursion depth exceeded")

    i = 0
    upper_tokens = [t.upper() if isinstance(t, str) else t for t in tokens]

    def executor(prog_tokens, stk, vrs):
        execute(prog_tokens, stk, vrs, depth + 1)

    while i < len(tokens):
        tok = tokens[i]
        tok_upper = tok.upper() if isinstance(tok, str) else ""

        # --- IF / THEN / ELSE / END ---
        if tok_upper == "IF":
            # Collect condition tokens up to THEN
            i += 1
            cond_tokens = []
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t == "IF":
                    nest += 1
                if t == "THEN" and nest == 1:
                    break
                if t == "END":
                    nest -= 1
                cond_tokens.append(tokens[i])
                i += 1
            if i >= len(tokens):
                raise RPNError("Missing THEN")
            i += 1  # skip THEN

            # Execute condition
            execute(cond_tokens, stack, variables, depth + 1)
            require_args(stack, 1)
            cond_val = stack.pop()
            is_true = isinstance(cond_val, RPNNumber) and cond_val.value != 0

            # Collect THEN branch and optional ELSE branch up to END
            then_tokens = []
            else_tokens = []
            in_else = False
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t == "IF":
                    nest += 1
                if t == "END":
                    nest -= 1
                    if nest == 0:
                        i += 1
                        break
                if t == "ELSE" and nest == 1:
                    in_else = True
                    i += 1
                    continue
                if in_else:
                    else_tokens.append(tokens[i])
                else:
                    then_tokens.append(tokens[i])
                i += 1

            if is_true:
                execute(then_tokens, stack, variables, depth + 1)
            elif else_tokens:
                execute(else_tokens, stack, variables, depth + 1)
            continue

        # --- START / NEXT (counted loop, no variable) ---
        if tok_upper == "START":
            # Stack should have: start end on stack before START
            require_args(stack, 2)
            end_val = stack.pop()
            start_val = stack.pop()
            require_type(start_val, RPNNumber)
            require_type(end_val, RPNNumber)

            i += 1
            body_tokens = []
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t in ("START", "FOR"):
                    nest += 1
                if t in ("NEXT", "STEP") and nest == 1:
                    break
                if t in ("NEXT", "STEP"):
                    nest -= 1
                body_tokens.append(tokens[i])
                i += 1
            use_step = i < len(tokens) and tokens[i].upper() == "STEP"
            i += 1  # skip NEXT/STEP

            counter = start_val.value
            while counter <= end_val.value:
                execute(body_tokens, stack, variables, depth + 1)
                if use_step:
                    require_args(stack, 1)
                    step_val = stack.pop()
                    require_type(step_val, RPNNumber)
                    counter += step_val.value
                else:
                    counter += 1
            continue

        # --- FOR variable / NEXT ---
        if tok_upper == "FOR":
            i += 1
            if i >= len(tokens):
                raise RPNError("Missing loop variable after FOR")
            var_name = tokens[i].upper()
            i += 1

            require_args(stack, 2)
            end_val = stack.pop()
            start_val = stack.pop()
            require_type(start_val, RPNNumber)
            require_type(end_val, RPNNumber)

            body_tokens = []
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t in ("START", "FOR"):
                    nest += 1
                if t in ("NEXT", "STEP") and nest == 1:
                    break
                if t in ("NEXT", "STEP"):
                    nest -= 1
                body_tokens.append(tokens[i])
                i += 1

            use_step = i < len(tokens) and tokens[i].upper() == "STEP"
            i += 1  # skip NEXT/STEP

            counter = start_val.value
            # Save old variable value if exists
            old_val = variables.get(var_name)
            try:
                while counter <= end_val.value:
                    variables[var_name] = RPNNumber(counter)
                    execute(body_tokens, stack, variables, depth + 1)
                    if use_step:
                        require_args(stack, 1)
                        step_val = stack.pop()
                        require_type(step_val, RPNNumber)
                        counter += step_val.value
                    else:
                        counter += 1
            finally:
                # Restore or remove loop variable
                if old_val is not None:
                    variables[var_name] = old_val
                elif var_name in variables:
                    del variables[var_name]
            continue

        # --- WHILE / REPEAT / END ---
        if tok_upper == "WHILE":
            i += 1
            # Collect condition tokens (up to REPEAT)
            cond_tokens = []
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t == "WHILE":
                    nest += 1
                if t == "REPEAT" and nest == 1:
                    break
                if t == "END":
                    nest -= 1
                cond_tokens.append(tokens[i])
                i += 1
            if i >= len(tokens):
                raise RPNError("Missing REPEAT")
            i += 1  # skip REPEAT

            # Collect body (up to END)
            body_tokens = []
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t in ("WHILE", "IF", "DO", "CASE"):
                    nest += 1
                if t == "END":
                    nest -= 1
                    if nest == 0:
                        i += 1
                        break
                body_tokens.append(tokens[i])
                i += 1

            iteration = 0
            while iteration < 100000:
                execute(cond_tokens, stack, variables, depth + 1)
                require_args(stack, 1)
                cond_val = stack.pop()
                if not (isinstance(cond_val, RPNNumber) and cond_val.value != 0):
                    break
                execute(body_tokens, stack, variables, depth + 1)
                iteration += 1
            continue

        # --- DO / UNTIL / END ---
        if tok_upper == "DO":
            i += 1
            body_tokens = []
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t == "DO":
                    nest += 1
                if t == "UNTIL" and nest == 1:
                    break
                if t == "END":
                    nest -= 1
                body_tokens.append(tokens[i])
                i += 1
            if i >= len(tokens):
                raise RPNError("Missing UNTIL")
            i += 1  # skip UNTIL

            cond_tokens = []
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t in ("DO", "WHILE", "IF", "CASE"):
                    nest += 1
                if t == "END":
                    nest -= 1
                    if nest == 0:
                        i += 1
                        break
                cond_tokens.append(tokens[i])
                i += 1

            iteration = 0
            while iteration < 100000:
                execute(body_tokens, stack, variables, depth + 1)
                execute(cond_tokens, stack, variables, depth + 1)
                require_args(stack, 1)
                cond_val = stack.pop()
                if isinstance(cond_val, RPNNumber) and cond_val.value != 0:
                    break
                iteration += 1
            continue

        # --- → / -> (local variable binding) ---
        if tok_upper in ("→", "->"):
            i += 1
            # Collect local variable names
            local_vars = []
            while i < len(tokens):
                t = tokens[i]
                # Stop at program body delimiter
                if isinstance(t, str) and (t.startswith('«') or t.startswith('<<')):
                    break
                t_up = t.upper() if isinstance(t, str) else ""
                # Variable names are simple alphabetic identifiers
                if isinstance(t, str) and t.replace('_', '').isalnum() and len(t) > 0 and not t[0].isdigit():
                    local_vars.append(t_up)
                    i += 1
                else:
                    break

            if not local_vars:
                raise RPNError("Missing variable names after →")

            # Determine body: explicit program token or remaining tokens
            if i < len(tokens):
                t = tokens[i]
                if isinstance(t, str) and (t.startswith('«') or t.startswith('<<')):
                    body_prog = parse_token(t)
                    if not isinstance(body_prog, RPNProgram):
                        raise RPNError("Expected program body after → variables")
                    body_tokens = body_prog.value
                    i += 1
                else:
                    # All remaining tokens form the body
                    body_tokens = list(tokens[i:])
                    i = len(tokens)
            else:
                raise RPNError("Missing program body after → variables")

            # Pop values from stack (deepest → first variable)
            n = len(local_vars)
            require_args(stack, n)
            values = [stack.pop() for _ in range(n)]
            values.reverse()

            # Save old variable values and set locals
            saved = {}
            for name, val in zip(local_vars, values):
                if name in variables:
                    saved[name] = variables[name]
                variables[name] = val

            try:
                execute(body_tokens, stack, variables, depth + 1)
            finally:
                for name in local_vars:
                    if name in saved:
                        variables[name] = saved[name]
                    elif name in variables:
                        del variables[name]
            continue

        # --- CASE / THEN / END ---
        if tok_upper == "CASE":
            i += 1
            entries = []       # list of (cond_tokens, body_tokens)
            default_tokens = []

            while i < len(tokens):
                # Look ahead for THEN at nesting level 0
                j = i
                nest = 0
                found_then = False

                while j < len(tokens):
                    t = tokens[j].upper() if isinstance(tokens[j], str) else ""
                    if t in ("IF", "CASE", "DO", "WHILE", "FOR", "START"):
                        nest += 1
                    elif t == "END":
                        if nest > 0:
                            nest -= 1
                        else:
                            break  # outer CASE END, no THEN found
                    elif t == "THEN" and nest == 0:
                        found_then = True
                        break
                    j += 1

                if found_then:
                    cond_tokens = list(tokens[i:j])
                    i = j + 1  # skip THEN

                    # Collect body until END at nesting level 0
                    body_tokens = []
                    nest = 0
                    while i < len(tokens):
                        t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                        if t in ("IF", "CASE", "DO", "WHILE", "FOR", "START"):
                            nest += 1
                        if t == "END":
                            if nest > 0:
                                nest -= 1
                                body_tokens.append(tokens[i])
                                i += 1
                            else:
                                i += 1  # skip END
                                break
                        else:
                            body_tokens.append(tokens[i])
                            i += 1

                    entries.append((cond_tokens, body_tokens))
                else:
                    # Default action: remaining tokens until final END
                    nest = 0
                    while i < len(tokens):
                        t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                        if t in ("IF", "CASE", "DO", "WHILE", "FOR", "START"):
                            nest += 1
                        if t == "END":
                            if nest > 0:
                                nest -= 1
                                default_tokens.append(tokens[i])
                                i += 1
                            else:
                                i += 1  # skip final END
                                break
                        else:
                            default_tokens.append(tokens[i])
                            i += 1
                    break

            # Execute: first matching case wins
            matched = False
            for cond_toks, body_toks in entries:
                execute(cond_toks, stack, variables, depth + 1)
                require_args(stack, 1)
                cond_val = stack.pop()
                if isinstance(cond_val, RPNNumber) and cond_val.value != 0:
                    execute(body_toks, stack, variables, depth + 1)
                    matched = True
                    break

            if not matched and default_tokens:
                execute(default_tokens, stack, variables, depth + 1)

            continue

        # --- IFERR / THEN / ELSE / END ---
        if tok_upper == "IFERR":
            i += 1
            # Collect trap clause until THEN
            trap_tokens = []
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t in ("IF", "IFERR"):
                    nest += 1
                if t == "THEN" and nest == 1:
                    break
                if t == "END":
                    nest -= 1
                trap_tokens.append(tokens[i])
                i += 1
            if i >= len(tokens):
                raise RPNError("Missing THEN after IFERR")
            i += 1  # skip THEN

            # Collect error handler and optional ELSE (normal) branch
            error_tokens = []
            normal_tokens = []
            in_else = False
            nest = 1
            while i < len(tokens):
                t = tokens[i].upper() if isinstance(tokens[i], str) else ""
                if t in ("IF", "IFERR"):
                    nest += 1
                if t == "END":
                    nest -= 1
                    if nest == 0:
                        i += 1
                        break
                if t == "ELSE" and nest == 1:
                    in_else = True
                    i += 1
                    continue
                if in_else:
                    normal_tokens.append(tokens[i])
                else:
                    error_tokens.append(tokens[i])
                i += 1

            # Execute trap clause; if error, run error handler
            had_error = False
            try:
                execute(trap_tokens, stack, variables, depth + 1)
            except (RPNError, Exception):
                had_error = True

            if had_error:
                execute(error_tokens, stack, variables, depth + 1)
            elif normal_tokens:
                execute(normal_tokens, stack, variables, depth + 1)

            continue

        # --- Regular token: parse and dispatch ---
        parsed = parse_token(tok)
        dispatch(parsed, stack, variables, executor)
        i += 1


@register("EVAL")
def op_eval(stack, variables, executor_unused):
    """Execute a program or evaluate a symbol."""
    require_args(stack, 1)
    obj = stack.pop()
    if isinstance(obj, RPNProgram):
        execute(obj.value, stack, variables)
    elif isinstance(obj, RPNSymbol):
        name = obj.value
        if name in variables:
            val = variables[name]
            if isinstance(val, RPNProgram):
                execute(val.value, stack, variables)
            else:
                stack.push(rpn_copy(val))
        else:
            stack.push(obj)
            raise RPNError(f"Undefined Name: {name}")
    else:
        stack.push(obj)


@register("->NUM", "→NUM", "NUM")
def op_to_num(stack, variables, executor):
    """Force numeric evaluation."""
    require_args(stack, 1)
    obj = stack.peek(1)
    if isinstance(obj, RPNNumber):
        return
    # Try EVAL
    op_eval(stack, variables, executor)


@register("WAIT")
def op_wait(stack, variables, executor):
    """Wait for n seconds."""
    import time
    require_args(stack, 1)
    n = stack.pop()
    require_type(n, RPNNumber)
    time.sleep(max(0, n.value))


@register("TYPE")
def op_type(stack, variables, executor):
    """Push the type number of the top object (HP 50g convention)."""
    require_args(stack, 1)
    obj = stack.pop()
    type_map = {
        RPNNumber: 0,
        RPNProgram: 8,
        RPNSymbol: 6,
    }
    from rpn_types import RPNList, RPNString
    type_map[RPNList] = 5
    type_map[RPNString] = 2
    stack.push(obj)
    stack.push(RPNNumber(type_map.get(type(obj), -1)))
