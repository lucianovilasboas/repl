"""Operation registry and dispatch for RPN commands."""

from rpn_types import RPNObject, RPNSymbol, RPNProgram
from stack import StackUnderflowError

# Global registry: command_name (uppercase) -> handler function
_registry = {}


class RPNError(Exception):
    """User-facing RPN error (shown, doesn't crash REPL)."""
    pass


def register(*names):
    """Decorator to register an operation handler under one or more names."""
    def decorator(func):
        for name in names:
            _registry[name.upper()] = func
        return func
    return decorator


def get_operation(name):
    """Look up an operation by name."""
    return _registry.get(name.upper())


def list_operations():
    """Return sorted list of registered operation names."""
    return sorted(set(_registry.keys()))


def require_args(stack, n):
    """Assert that the stack has at least n items."""
    if stack.depth() < n:
        raise RPNError("Too Few Arguments")


def require_type(obj, *types, msg="Bad Argument Type"):
    """Assert that obj is one of the given types."""
    if not isinstance(obj, types):
        raise RPNError(msg)


def dispatch(token, stack, variables, executor=None):
    """Dispatch a parsed token.

    - If token is an RPNObject, push it on the stack.
    - If token is a string, look up the operation or variable.
    - executor is a callback to run RPNProgram tokens (for EVAL, IF, etc.)
    """
    if isinstance(token, RPNObject):
        stack.push(token)
        return

    name = token.upper() if isinstance(token, str) else str(token)

    # Check operation registry first
    op = get_operation(name)
    if op is not None:
        op(stack, variables, executor)
        return

    # Check if it's a variable name
    if name in variables:
        val = variables[name]
        if isinstance(val, RPNProgram) and executor:
            executor(val.value, stack, variables)
        else:
            from rpn_types import rpn_copy
            stack.push(rpn_copy(val))
        return

    raise RPNError(f"Undefined Name: {name}")
