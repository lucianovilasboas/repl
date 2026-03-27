"""State persistence — save/load stack and variables to JSON."""

import json
import os
from rpn_types import (
    RPNNumber, RPNString, RPNList, RPNProgram, RPNSymbol, RPNObject
)

STATE_FILE = os.path.join(os.path.expanduser("~"), ".rpn50g_state.json")


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
    else:
        return RPNString(str(v))


def save_state(stack, variables, settings=None):
    """Save stack and variables to disk."""
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
    """Load stack data and variables from disk. Returns (stack_items, variables, settings)."""
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
