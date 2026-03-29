"""State serialization — convert RPN objects to/from JSON-friendly dicts.

The old file-based persistence (save_state / load_state) has been replaced
by database-backed sessions via db_sync.py.  Only the serialisation helpers
remain here because they are used by both the API and the REPL.
"""

import json
import os
from rpn_types import (
    RPNNumber, RPNString, RPNList, RPNProgram, RPNSymbol, RPNObject,
    RPNVector, RPNMatrix
)


def _serialize(obj):
    """Convert RPNObject to JSON-serializable dict."""
    if isinstance(obj, RPNNumber):
        return {"type": "number", "value": obj.value}
    elif isinstance(obj, RPNString):
        return {"type": "string", "value": obj.value}
    elif isinstance(obj, RPNList):
        return {"type": "list", "value": [_serialize(item) for item in obj.value]}
    elif isinstance(obj, RPNProgram):
        return {"type": "program", "value": obj.value}
    elif isinstance(obj, RPNSymbol):
        return {"type": "symbol", "value": obj.value}
    elif isinstance(obj, RPNVector):
        return {"type": "vector", "value": [_serialize(item) for item in obj.value]}
    elif isinstance(obj, RPNMatrix):
        return {"type": "matrix", "value": [[_serialize(item) for item in row] for row in obj.value]}
    else:
        return {"type": "unknown", "value": str(obj)}


def _deserialize(data):
    """Convert JSON dict back to RPNObject."""
    t = data["type"]
    v = data["value"]
    if t == "number":
        return RPNNumber(v)
    elif t == "string":
        return RPNString(v)
    elif t == "list":
        return RPNList([_deserialize(item) for item in v])
    elif t == "program":
        return RPNProgram(v)
    elif t == "symbol":
        return RPNSymbol(v)
    elif t == "vector":
        return RPNVector([_deserialize(item) for item in v])
    elif t == "matrix":
        return RPNMatrix([[_deserialize(item) for item in row] for row in v])
    else:
        return RPNString(str(v))


# ── Legacy helpers (kept for gui.py compatibility) ───────────────────

STATE_FILE = os.path.join(os.path.expanduser("~"), ".rpn50g_state.json")


def save_state(stack, variables, settings=None):
    """Save stack and variables to disk (legacy JSON file)."""
    state = {
        "stack": [_serialize(obj) for obj in stack.to_list()],
        "variables": {name: _serialize(val) for name, val in variables.items()},
    }
    if settings:
        state["settings"] = settings
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"  Warning: Could not save state: {e}")


def load_state():
    """Load stack data and variables from disk (legacy JSON file)."""
    if not os.path.exists(STATE_FILE):
        return [], {}, {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
        stack_items = [_deserialize(item) for item in state.get("stack", [])]
        variables = {name: _deserialize(val) for name, val in state.get("variables", {}).items()}
        settings = state.get("settings", {})
        return stack_items, variables, settings
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"  Warning: Could not load state: {e}")
        return [], {}, {}
