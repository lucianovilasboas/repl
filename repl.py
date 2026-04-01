#!/usr/bin/env python3
"""MyRPN Calculator Simulator — REPL entry point."""

import sys
import os
import getpass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stack import Stack, StackUnderflowError
from parser import parse, parse_token, tokenize
from operations import dispatch, RPNError, register, list_operations
from rpn_types import RPNObject, RPNProgram, RPNNumber
from display import display_calculator
from ops.program import execute
from db_sync import (
    init_sync_db, find_user, create_user, verify_user,
    list_sessions, create_session, delete_session,
    save_session, load_session_state, get_session,
)

# Import ops package to register all operations
import ops  # noqa: F401


# --- Settings ---
class Settings:
    def __init__(self):
        self.angle_mode = "RAD"
        self.num_format = "STD"
        self.fix_digits = None
        self.stack_lines = 4

    def to_dict(self):
        return {
            "angle_mode": self.angle_mode,
            "num_format": self.num_format,
            "fix_digits": self.fix_digits,
            "stack_lines": self.stack_lines,
        }

    def from_dict(self, d):
        self.angle_mode = d.get("angle_mode", "RAD")
        self.num_format = d.get("num_format", "STD")
        self.fix_digits = d.get("fix_digits", None)
        self.stack_lines = d.get("stack_lines", 4)


# --- Display mode operations ---
@register("FIX")
def op_fix(stack, variables, executor):
    from operations import require_args, require_type
    require_args(stack, 1)
    n = stack.pop()
    require_type(n, RPNNumber)
    _settings.num_format = "FIX"
    _settings.fix_digits = int(n.value)


@register("SCI")
def op_sci(stack, variables, executor):
    from operations import require_args, require_type
    require_args(stack, 1)
    n = stack.pop()
    require_type(n, RPNNumber)
    _settings.num_format = "SCI"
    _settings.fix_digits = int(n.value)


@register("ENG")
def op_eng(stack, variables, executor):
    from operations import require_args, require_type
    require_args(stack, 1)
    n = stack.pop()
    require_type(n, RPNNumber)
    _settings.num_format = "ENG"
    _settings.fix_digits = int(n.value)


@register("STD")
def op_std(stack, variables, executor):
    _settings.num_format = "STD"
    _settings.fix_digits = None


@register("STKL")
def op_stkl(stack, variables, executor):
    """Set the number of visible stack levels (1–32)."""
    from operations import require_args, require_type
    require_args(stack, 1)
    n = stack.pop()
    require_type(n, RPNNumber)
    val = max(1, min(32, int(n.value)))
    _settings.stack_lines = val


# Global settings instance
_settings = Settings()
_undo_stack = []
_variables = {}  # module-level ref to main variables dict


HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".rpn50g_history")


def setup_readline():
    """Setup readline for command history."""
    try:
        import readline
        readline.set_history_length(1000)
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
        return readline
    except ImportError:
        # Windows fallback — try pyreadline3
        try:
            import pyreadline3  # noqa: F401
            import readline
            readline.set_history_length(1000)
            if os.path.exists(HISTORY_FILE):
                readline.read_history_file(HISTORY_FILE)
            return readline
        except ImportError:
            return None


def save_readline_history(readline_mod):
    if readline_mod:
        try:
            readline_mod.write_history_file(HISTORY_FILE)
        except OSError:
            pass


def get_angle_mode():
    """Get angle mode from the scientific module."""
    try:
        from ops.scientific import _angle_mode
        return _angle_mode
    except ImportError:
        return "RAD"


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def executor(prog_tokens, stack, variables):
    """Callback for executing program tokens."""
    execute(prog_tokens, stack, variables)


TITLE = "  MyRPN Simulator · HELP | UNDO | QUIT"


def show_stack(username, stack, error_msg=None):
    """Clear screen and redraw the HP 50g calculator display."""
    clear_screen()
    print(TITLE)
    angle = get_angle_mode()
    print(display_calculator(
        username,
        stack, _variables, _settings.stack_lines,
        _settings.num_format, _settings.fix_digits,
        angle, error_msg,
    ))


def cmd_help():
    """Show available commands grouped by category."""
    ops = list_operations()
    # Group roughly
    print("\n  Available operations:")
    # Print in columns
    line = "  "
    for i, op in enumerate(ops):
        line += f"{op:12s}"
        if (i + 1) % 6 == 0:
            print(line)
            line = "  "
    if line.strip():
        print(line)
    print()


def _prog_depth(text: str) -> int:
    """Retorna o número de blocos << não fechados no texto."""
    return text.count("<<") - text.count(">>") + text.count("\u00ab") - text.count("\u00bb")


def _read_multiline(first_line: str) -> str:
    """Coleta linhas de continuação até todos os << >> estarem balanceados."""
    parts = [first_line]
    depth = _prog_depth(first_line)
    while depth > 0:
        try:
            cont = input("...  ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        parts.append(cont)
        depth = _prog_depth(" ".join(parts))
    return " ".join(p.strip() for p in parts if p.strip())


def _parse_section_as_program(code_str):
    """Parse a code section and return an RPNProgram.

    If *code_str* is a single ``<< >>`` (or ``« »``) block, returns the
    RPNProgram parsed from it directly.  Otherwise wraps all raw tokens
    into a new RPNProgram (treating them as the program body).
    """
    raw_tokens = tokenize(code_str)
    if not raw_tokens:
        return None
    if len(raw_tokens) == 1:
        tok = raw_tokens[0]
        if tok.startswith('<<') or tok.startswith('\u00ab'):
            result = parse_token(tok)
            if isinstance(result, RPNProgram):
                return result
    # Multi-token body → wrap as a program
    return RPNProgram(raw_tokens)


def load_rpl_file(filepath, stack, variables):
    """Load an .rpl file, storing named sections as RPNProgram variables.

    File format
    -----------
    - ``# name``  — starts a named program section.  The code that follows
                    (until the next ``# name`` marker or EOF) is parsed and
                    stored in *variables* as an :class:`RPNProgram` under
                    the key ``NAME`` (upper-cased).  If the body is a single
                    ``<< ... >>`` block its inner tokens are used; otherwise
                    all raw tokens become the program body.
    - ``//``      — comment; the rest of the line is ignored.
    - Anonymous code (before any ``#`` marker) is executed directly on the
      stack (legacy behaviour).

    Returns
    -------
    tuple (int, list[str])
        * Total item count (programs stored + anonymous tokens dispatched).
        * List of variable names that were defined (e.g. ``['SOMAR', 'NEGAR']``).
    """
    if not os.path.isabs(filepath):
        if not os.path.exists(filepath):
            alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)
            if os.path.exists(alt):
                filepath = alt

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    # Split file into sections: [(name_or_None, [cleaned_code_lines])]
    sections = []
    current_name = None
    current_lines = []

    for raw in lines:
        stripped = raw.strip()

        # Named section header: "# program_name"
        if stripped.startswith('#'):
            sections.append((current_name, current_lines))
            name_part = stripped[1:].strip()
            current_name = name_part if name_part else None
            current_lines = []
            continue

        # Strip // comments
        idx = stripped.find('//')
        if idx >= 0:
            stripped = stripped[:idx].strip()

        if stripped:
            current_lines.append(stripped)

    sections.append((current_name, current_lines))  # last section

    count = 0
    defined_names = []

    for name, code_lines in sections:
        content = " ".join(code_lines).strip()

        if name:
            # Named section → parse and store as RPNProgram variable
            var_name = name.upper()
            if content:
                prog = _parse_section_as_program(content)
                if prog is not None:
                    variables[var_name] = prog
                    defined_names.append(var_name)
                    count += 1
            else:
                # Empty body → store empty program
                variables[var_name] = RPNProgram([])
                defined_names.append(var_name)
                count += 1
        else:
            # Anonymous section → execute directly (legacy)
            if not content:
                continue
            tokens = parse(content)
            for token in tokens:
                dispatch(token, stack, variables, executor)
                count += 1

    return count, defined_names


# ── Persistence helper ───────────────────────────────────────────────

def _persist(session_id, stack, variables):
    """Save current calculator state to the database."""
    _settings.angle_mode = get_angle_mode()
    save_session(session_id, stack, variables, _settings.to_dict(), _undo_stack)


# ── Login screen ─────────────────────────────────────────────────────

def login_screen():
    """Interactive login / register prompt. Returns User or None."""
    clear_screen()
    print()
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║            MyRPN Simulator · Login            ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print()

    for _ in range(3):
        try:
            choice = input("  [L]ogin  [R]egister  [Q]uit : ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            return None

        if choice in ("Q", "QUIT"):
            return None

        if choice in ("R", "REGISTER"):
            return _register_flow()

        if choice in ("L", "LOGIN", ""):
            global user
            user = _login_flow()
            if user is not None:
                return user
            # wrong password — try again

    print("  Too many attempts.")
    return None


def _login_flow():
    try:
        username = input("  Username: ").strip()
        if not username:
            return None
        password = getpass.getpass("  Password: ")
    except (EOFError, KeyboardInterrupt):
        return None
    user = verify_user(username, password)
    if user is None:
        print("  ✗ Invalid username or password.\n")
    return user


def _register_flow():
    try:
        print()
        username = input("  Choose username: ").strip()
        if not username:
            print("  ✗ Username cannot be empty.\n")
            return None
        if find_user(username):
            print("  ✗ Username already taken.\n")
            return None
        email = input("  Email: ").strip()
        password = getpass.getpass("  Password: ")
        password2 = getpass.getpass("  Confirm password: ")
    except (EOFError, KeyboardInterrupt):
        return None

    if password != password2:
        print("  ✗ Passwords do not match.\n")
        return None
    if len(password) < 4:
        print("  ✗ Password must be at least 4 characters.\n")
        return None

    user = create_user(username, email, password)
    print(f"  ✓ User '{username}' created.\n")
    return user


# ── Session screen ───────────────────────────────────────────────────

def session_screen(user):
    """Show session list, let user pick / create / delete. Returns session dict or None (logout)."""
    while True:
        clear_screen()
        sessions = list_sessions(user.id)
        print()
        print(f"  ╔═══════════════════════════════════════════════╗")
        print(f"  ║  Sessions for {user.username:<32} ║")
        print(f"  ╚═══════════════════════════════════════════════╝")
        print()

        if sessions:
            print(f"  {'#':>3}  {'Name':<20} {'Stack':>5}  {'Updated'}")
            print(f"  {'─'*3}  {'─'*20} {'─'*5}  {'─'*19}")
            for i, s in enumerate(sessions, 1):
                ts = s["updated_at"].strftime("%Y-%m-%d %H:%M") if s["updated_at"] else "—"
                print(f"  {i:>3}  {s['name']:<20} {s['stack_depth']:>5}  {ts}")
            print()

        print("  Commands:  <number> = open session")
        print("             N       = new session")
        print("             D <n>   = delete session")
        print("             L       = logout")
        print()

        try:
            cmd = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return None

        upper = cmd.upper()

        if upper in ("L", "LOGOUT"):
            return None

        if upper in ("N", "NEW"):
            try:
                name = input("  Session name [default]: ").strip() or "default"
            except (EOFError, KeyboardInterrupt):
                continue
            sess = create_session(user.id, name)
            return sess

        if upper.startswith("D ") or upper.startswith("D"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1].isdigit():
                idx = int(parts[1]) - 1
                if 0 <= idx < len(sessions):
                    sid = sessions[idx]["id"]
                    sname = sessions[idx]["name"]
                    try:
                        confirm = input(f"  Delete '{sname}'? [y/N] ").strip().upper()
                    except (EOFError, KeyboardInterrupt):
                        continue
                    if confirm == "Y":
                        delete_session(sid, user.id)
                        print(f"  ✓ Session '{sname}' deleted.")
                continue

        if cmd.isdigit():
            idx = int(cmd) - 1
            if 0 <= idx < len(sessions):
                return sessions[idx]

        # No valid sessions and empty input → create default
        if not sessions:
            sess = create_session(user.id, "default")
            return sess


def main():
    global _settings, _variables

    init_sync_db()
    readline_mod = setup_readline()

    # ── Authentication ───────────────────────────────────────────
    user = login_screen()
    if user is None:
        print("  Goodbye!")
        return

    # ── Session selection loop ───────────────────────────────────
    while True:
        sess_dict = session_screen(user)
        if sess_dict is None:
            # user chose to logout — loop back to login
            user = login_screen()
            if user is None:
                print("  Goodbye!")
                return
            continue

        session_id = sess_dict["id"]
        session_name = sess_dict["name"]

        # Hydrate state from DB
        stack = Stack()
        _variables = {}
        variables = _variables

        stack_items, saved_vars, saved_settings, saved_undo = load_session_state(sess_dict)
        for item in stack_items:
            stack.push(item)
        variables.update(saved_vars)
        _undo_stack.clear()
        _undo_stack.extend(saved_undo)

        if saved_settings:
            _settings.from_dict(saved_settings)
            if _settings.angle_mode != "RAD":
                try:
                    import ops.scientific as sci
                    sci._angle_mode = _settings.angle_mode
                except Exception:
                    pass

        show_stack(user.username, stack)

        # ── Main REPL loop ───────────────────────────────────────
        go_to_sessions = False
        go_to_logout = False

        while True:
            try:
                line = input("\n> ").strip()
                if line and _prog_depth(line) > 0:
                    line = _read_multiline(line)
            except (EOFError, KeyboardInterrupt):
                print()
                _persist(session_id, stack, variables)
                save_readline_history(readline_mod)
                print("  State saved. Goodbye!")
                return

            if not line:
                show_stack(user.username, stack)
                continue

            upper_line = line.upper().strip()

            if upper_line in ("QUIT", "EXIT", "Q"):
                _persist(session_id, stack, variables)
                save_readline_history(readline_mod)
                print("  State saved. Goodbye!")
                return

            if upper_line in ("SESSION", "SESSIONS"):
                _persist(session_id, stack, variables)
                go_to_sessions = True
                break

            if upper_line == "LOGOUT":
                _persist(session_id, stack, variables)
                go_to_logout = True
                break

            if upper_line == "HELP":
                cmd_help()
                input("\n  Press Enter to continue...")
                show_stack(user.username, stack)
                continue

            # LOAD command: LOAD filename  or  LOAD "filename"
            if upper_line.startswith("LOAD ") or upper_line == "LOAD":
                parts = line.strip().split(None, 1)
                if len(parts) < 2:
                    show_stack(user.username, stack, error_msg="Usage: LOAD <filename>")
                    continue
                filepath = parts[1].strip().strip('"').strip("'")
                try:
                    n, defined = load_rpl_file(filepath, stack, variables)
                    _settings.angle_mode = get_angle_mode()
                    _persist(session_id, stack, variables)
                    if defined:
                        names_str = ", ".join(defined)
                        msg = f"Loaded '{os.path.basename(filepath)}': {names_str}"
                    else:
                        msg = f"Loaded '{os.path.basename(filepath)}' ({n} token(s))"
                    show_stack(user.username, stack, error_msg=msg)
                except FileNotFoundError as e:
                    show_stack(user.username, stack, error_msg=str(e))
                except RPNError as e:
                    show_stack(user.username, stack, error_msg=str(e))
                except Exception as e:
                    show_stack(user.username, stack, error_msg=f"Error loading file: {e}")
                continue

            if upper_line == "UNDO":
                if _undo_stack:
                    snapshot = _undo_stack.pop()
                    stack.restore(snapshot)
                    _persist(session_id, stack, variables)
                    show_stack(user.username, stack)
                else:
                    show_stack(user.username, stack, error_msg="Nothing to undo")
                continue

            # Save snapshot for UNDO
            _undo_stack.append(stack.snapshot())
            if len(_undo_stack) > 100:
                _undo_stack.pop(0)

            try:
                tokens = parse(line)
                for token in tokens:
                    dispatch(token, stack, variables, executor)

                # Sync angle mode to settings
                _settings.angle_mode = get_angle_mode()

            except RPNError as e:
                show_stack(user.username, stack, error_msg=str(e))
                continue
            except StackUnderflowError as e:
                show_stack(user.username, stack, error_msg=str(e))
                continue
            except Exception as e:
                show_stack(user.username, stack, error_msg=str(e))
                continue

            _persist(session_id, stack, variables)
            show_stack(user.username, stack)

        if go_to_logout:
            user = login_screen()
            if user is None:
                print("  Goodbye!")
                return
            continue
        # go_to_sessions: loop will call session_screen again


if __name__ == "__main__":
    main()
