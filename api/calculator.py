"""Bridge between the REST API and the RPN calculator core.

This module is the ONLY place that imports core modules (stack, parser,
operations, etc.).  Routers interact exclusively through this service.
"""

from __future__ import annotations

import json
import sys
import os
from typing import Dict, List, Optional

# Ensure project root is on sys.path so core imports work.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from stack import Stack, StackUnderflowError
from parser import parse
from operations import dispatch, RPNError, list_operations, _registry
from rpn_types import (
    RPNObject, RPNNumber, RPNString, RPNList, RPNProgram, RPNSymbol,
    RPNVector, RPNMatrix, rpn_copy,
)
from display import format_value
from state import _serialize, _deserialize
from ops.program import execute as _program_execute

# Trigger operation registration
import ops  # noqa: F401
# Also register display-mode operations that live in repl.py
import repl as _repl  # noqa: F401

from api.schemas import StackItem, ExecutionResult


# ── Helpers ──────────────────────────────────────────────────────────

_TYPE_MAP = {
    RPNNumber: "number",
    RPNString: "string",
    RPNList: "list",
    RPNProgram: "program",
    RPNSymbol: "symbol",
    RPNVector: "vector",
    RPNMatrix: "matrix",
}

_MAX_UNDO = 50


def _rpn_type_name(obj: RPNObject) -> str:
    return _TYPE_MAP.get(type(obj), "unknown")


def _serialize_value(obj: RPNObject):
    """Convert an RPNObject to a JSON-friendly Python value."""
    if isinstance(obj, RPNNumber):
        return obj.value
    if isinstance(obj, RPNString):
        return obj.value
    if isinstance(obj, RPNList):
        return [_serialize_value(item) for item in obj.value]
    if isinstance(obj, RPNProgram):
        return obj.value  # list[str]
    if isinstance(obj, RPNSymbol):
        return obj.value
    if isinstance(obj, RPNVector):
        return [item.value for item in obj.value]
    if isinstance(obj, RPNMatrix):
        return [[item.value for item in row] for row in obj.value]
    return str(obj)


def _make_stack_item(obj: RPNObject, level: int, num_format: str = "STD", fix_digits: Optional[int] = None) -> StackItem:
    return StackItem(
        level=level,
        value=_serialize_value(obj),
        type=_rpn_type_name(obj),
        display=format_value(obj, num_format, fix_digits),
    )


def value_to_rpn(value, type_name: str = "number") -> RPNObject:
    """Convert an API value + type hint into an RPNObject."""
    if type_name == "number":
        return RPNNumber(float(value) if isinstance(value, (int, float)) else float(value))
    if type_name == "string":
        return RPNString(str(value))
    if type_name == "list":
        if isinstance(value, list):
            return RPNList([value_to_rpn(v, "number") for v in value])
        raise RPNError("List value must be an array")
    if type_name == "vector":
        if isinstance(value, list):
            return RPNVector([RPNNumber(v) for v in value])
        raise RPNError("Vector value must be an array of numbers")
    if type_name == "matrix":
        if isinstance(value, list) and all(isinstance(r, list) for r in value):
            return RPNMatrix([[RPNNumber(v) for v in row] for row in value])
        raise RPNError("Matrix value must be a 2D array of numbers")
    if type_name == "program":
        if isinstance(value, list):
            return RPNProgram(value)
        raise RPNError("Program value must be a list of token strings")
    raise RPNError(f"Unknown type: {type_name}")


# ── Operation Discovery ─────────────────────────────────────────────

def _build_op_catalog() -> dict:
    """Build a catalog of operations with metadata.

    Returns {canonical_name: {aliases, category, description}}.
    """
    # Reverse map: func -> list of names
    func_to_names: Dict[int, List[str]] = {}
    for name, func in _registry.items():
        fid = id(func)
        func_to_names.setdefault(fid, []).append(name)

    # Determine category from module
    catalog: Dict[str, dict] = {}
    for fid, names in func_to_names.items():
        func = _registry[names[0]]
        module = getattr(func, "__module__", "") or ""
        if "arithmetic" in module:
            category = "arithmetic"
        elif "stack_ops" in module:
            category = "stack"
        elif "scientific" in module:
            category = "scientific"
        elif "comparison" in module:
            category = "comparison"
        elif "logic" in module:
            category = "logic"
        elif "variables" in module:
            category = "variables"
        elif "list_ops" in module:
            category = "list"
        elif "matrix" in module:
            category = "matrix"
        elif "program" in module:
            category = "program"
        elif "repl" in module:
            category = "display"
        else:
            category = "other"

        canonical = sorted(names, key=len)[0]  # shortest name as canonical
        doc = (func.__doc__ or "").strip().split("\n")[0] if func.__doc__ else None
        catalog[canonical] = {
            "aliases": sorted(names),
            "category": category,
            "description": doc,
        }
    return catalog


_op_catalog: Optional[dict] = None


def get_op_catalog() -> dict:
    global _op_catalog
    if _op_catalog is None:
        _op_catalog = _build_op_catalog()
    return _op_catalog


# ── Calculator Service ───────────────────────────────────────────────

class CalculatorService:
    """Wraps the RPN core for a single session."""

    def __init__(self):
        self.stack = Stack()
        self.variables: Dict[str, RPNObject] = {}
        self.settings = {"angle_mode": "RAD", "num_format": "STD", "fix_digits": None}
        self._undo_stack: list = []

    # ── Serialization (to/from DB JSON columns) ──────────────────────

    def serialize(self) -> dict:
        """Return JSON-serializable dict for persistence."""
        return {
            "stack": [_serialize(obj) for obj in self.stack.to_list()],
            "variables": {k: _serialize(v) for k, v in self.variables.items()},
            "settings": self.settings.copy(),
            "undo": [
                [_serialize(obj) for obj in snap]
                for snap in self._undo_stack[-_MAX_UNDO:]
            ],
        }

    @classmethod
    def from_db(cls, stack_json: str, variables_json: str, settings_json: str, undo_json: str = "[]") -> "CalculatorService":
        svc = cls()
        # Stack
        for item_data in json.loads(stack_json):
            svc.stack.push(_deserialize(item_data))
        # Variables
        for name, val_data in json.loads(variables_json).items():
            svc.variables[name] = _deserialize(val_data)
        # Settings
        svc.settings.update(json.loads(settings_json))
        # Undo
        for snap_data in json.loads(undo_json):
            svc._undo_stack.append([_deserialize(item) for item in snap_data])
        # Sync angle mode to the scientific module
        svc._sync_angle_mode()
        return svc

    def to_db_columns(self) -> dict:
        ser = self.serialize()
        return {
            "stack_json": json.dumps(ser["stack"], ensure_ascii=False),
            "variables_json": json.dumps(ser["variables"], ensure_ascii=False),
            "settings_json": json.dumps(ser["settings"], ensure_ascii=False),
            "undo_json": json.dumps(ser["undo"], ensure_ascii=False),
        }

    # ── Angle mode sync ──────────────────────────────────────────────

    def _sync_angle_mode(self):
        """Push our settings into the global scientific module (thread-unsafe but adequate for MVP)."""
        try:
            import ops.scientific as sci
            sci._angle_mode = self.settings.get("angle_mode", "RAD")
        except Exception:
            pass

    def _read_angle_mode(self):
        try:
            from ops.scientific import _angle_mode
            return _angle_mode
        except Exception:
            return "RAD"

    # ── Core operations ──────────────────────────────────────────────

    def _executor(self, prog_tokens, stack, variables):
        _program_execute(prog_tokens, stack, variables)

    def execute(self, expression: str) -> ExecutionResult:
        """Parse and execute an RPN expression. Returns the result."""
        self._sync_angle_mode()

        # Save undo snapshot
        self._undo_stack.append(self.stack.to_list())
        if len(self._undo_stack) > _MAX_UNDO:
            self._undo_stack.pop(0)

        try:
            tokens = parse(expression)
            for token in tokens:
                dispatch(token, self.stack, self.variables, self._executor)

            # Read back angle mode (operations like DEG/RAD modify global)
            self.settings["angle_mode"] = self._read_angle_mode()
            return self._result()
        except (RPNError, StackUnderflowError) as exc:
            return self._result(error=str(exc))

    def undo(self) -> ExecutionResult:
        if not self._undo_stack:
            return self._result(error="Nothing to undo")
        snapshot = self._undo_stack.pop()
        self.stack = Stack()
        for item in snapshot:
            self.stack.push(rpn_copy(item))
        return self._result()

    def push(self, value, type_name: str = "number") -> ExecutionResult:
        obj = value_to_rpn(value, type_name)
        self.stack.push(obj)
        return self._result()

    def clear(self) -> ExecutionResult:
        self.stack.clear()
        return self._result()

    def get_stack_items(self) -> List[StackItem]:
        items = self.stack.to_list()
        n = len(items)
        fmt = self.settings.get("num_format", "STD")
        dig = self.settings.get("fix_digits")
        return [_make_stack_item(items[i], n - i, fmt, dig) for i in range(n)]

    def get_variables_map(self) -> Dict[str, StackItem]:
        fmt = self.settings.get("num_format", "STD")
        dig = self.settings.get("fix_digits")
        return {
            name: _make_stack_item(val, 0, fmt, dig)
            for name, val in self.variables.items()
        }

    def update_settings(self, **kwargs):
        for key in ("angle_mode", "num_format", "fix_digits"):
            if key in kwargs and kwargs[key] is not None:
                self.settings[key] = kwargs[key]
        self._sync_angle_mode()

    def reset(self) -> ExecutionResult:
        self.stack.clear()
        self.variables.clear()
        self._undo_stack.clear()
        self.settings = {"angle_mode": "RAD", "num_format": "STD", "fix_digits": None}
        self._sync_angle_mode()
        return self._result()

    # ── Internal ─────────────────────────────────────────────────────

    def _result(self, error: Optional[str] = None) -> ExecutionResult:
        return ExecutionResult(
            stack=self.get_stack_items(),
            stack_depth=self.stack.depth(),
            error=error,
        )
