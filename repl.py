#!/usr/bin/env python3
"""HP 50g RPN Calculator Simulator — REPL entry point."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stack import Stack, StackUnderflowError
from parser import parse
from operations import dispatch, RPNError, register, list_operations
from rpn_types import RPNObject, RPNProgram, RPNNumber
from display import display_calculator
from state import save_state, load_state
from ops.program import execute

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


TITLE = "  HP 50g RPN Simulator · HELP | UNDO | QUIT"


def show_stack(stack, error_msg=None):
    """Clear screen and redraw the HP 50g calculator display."""
    clear_screen()
    print(TITLE)
    angle = get_angle_mode()
    print(display_calculator(
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


def main():
    global _settings, _variables

    readline_mod = setup_readline()

    # Initialize
    stack = Stack()
    _variables = {}
    variables = _variables  # local alias (same dict object)

    # Load saved state
    stack_items, saved_vars, saved_settings = load_state()
    for item in stack_items:
        stack.push(item)
    variables.update(saved_vars)
    if saved_settings:
        _settings.from_dict(saved_settings)
        # Restore angle mode
        if _settings.angle_mode != "RAD":
            try:
                import ops.scientific as sci
                sci._angle_mode = _settings.angle_mode
            except Exception:
                pass

    show_stack(stack)

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            show_stack(stack)
            continue

        upper_line = line.upper().strip()

        if upper_line in ("QUIT", "EXIT", "Q"):
            break

        if upper_line == "HELP":
            cmd_help()
            input("\n  Press Enter to continue...")
            show_stack(stack)
            continue

        if upper_line == "UNDO":
            if _undo_stack:
                snapshot = _undo_stack.pop()
                stack.restore(snapshot)
                show_stack(stack)
            else:
                show_stack(stack, error_msg="Nothing to undo")
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
            show_stack(stack, error_msg=str(e))
            continue
        except StackUnderflowError as e:
            show_stack(stack, error_msg=str(e))
            continue
        except Exception as e:
            show_stack(stack, error_msg=str(e))
            continue

        show_stack(stack)

    # Save state on exit
    _settings.angle_mode = get_angle_mode()
    save_state(stack, variables, _settings.to_dict())
    save_readline_history(readline_mod)
    print("  State saved. Goodbye!")


if __name__ == "__main__":
    main()
