"""RPN Stack engine."""

import copy
from rpn_types import RPNObject, rpn_copy


class StackUnderflowError(Exception):
    """Raised when trying to pop from an empty stack."""
    pass


class Stack:
    """Infinite RPN stack with HP 50g-style semantics."""

    def __init__(self):
        self._data = []

    def push(self, item):
        if not isinstance(item, RPNObject):
            raise TypeError(f"Stack only accepts RPNObject, got {type(item)}")
        self._data.append(item)

    def pop(self):
        if not self._data:
            raise StackUnderflowError("Too Few Arguments")
        return self._data.pop()

    def peek(self, n=1):
        """Peek at level n (1 = top of stack)."""
        if n < 1 or n > len(self._data):
            raise StackUnderflowError("Too Few Arguments")
        return self._data[-n]

    def depth(self):
        return len(self._data)

    def clear(self):
        self._data.clear()

    def to_list(self):
        return list(self._data)

    def snapshot(self):
        """Return a deep copy of the internal data for UNDO."""
        return copy.deepcopy(self._data)

    def restore(self, snapshot):
        """Restore stack from a snapshot."""
        self._data = snapshot

    def pick(self, n):
        """Copy level n to top of stack."""
        item = self.peek(n)
        self.push(rpn_copy(item))

    def roll(self, n):
        """Roll n items: move level n to top."""
        if n < 1 or n > len(self._data):
            raise StackUnderflowError("Too Few Arguments")
        item = self._data.pop(-n)
        self._data.append(item)

    def rolld(self, n):
        """Roll down: move top to level n."""
        if n < 1 or n > len(self._data):
            raise StackUnderflowError("Too Few Arguments")
        item = self._data.pop()
        self._data.insert(-n + 1 if n > 1 else 0, item)

    def __repr__(self):
        return f"Stack({self._data})"
