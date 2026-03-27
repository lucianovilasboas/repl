"""RPN type system — data types for the HP 50g simulator."""

import copy


class RPNObject:
    """Base class for all RPN objects."""

    def rpn_repr(self):
        return repr(self)

    def __eq__(self, other):
        return type(self) is type(other) and self.value == other.value

    def __hash__(self):
        return hash((type(self), self._hashable()))

    def _hashable(self):
        return self.value


class RPNNumber(RPNObject):
    """Integer or float number."""

    def __init__(self, value):
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, int):
            self.value = value
        else:
            self.value = float(value)
            if self.value == int(self.value) and not (self.value == float('inf') or self.value == float('-inf')):
                self.value = int(self.value)

    def rpn_repr(self):
        return str(self.value)

    def __repr__(self):
        return f"RPNNumber({self.value})"

    def is_int(self):
        return isinstance(self.value, int)


class RPNString(RPNObject):
    """String delimited by double quotes."""

    def __init__(self, value):
        self.value = str(value)

    def rpn_repr(self):
        return f'"{self.value}"'

    def __repr__(self):
        return f'RPNString("{self.value}")'


class RPNList(RPNObject):
    """List delimited by { }."""

    def __init__(self, items=None):
        self.value = list(items) if items else []

    def rpn_repr(self):
        inner = " ".join(item.rpn_repr() for item in self.value)
        return "{ " + inner + " }"

    def __repr__(self):
        return f"RPNList({self.value})"

    def _hashable(self):
        return tuple(self.value)

    def __len__(self):
        return len(self.value)


class RPNProgram(RPNObject):
    """Program delimited by « » or << >>. Stores raw token strings."""

    def __init__(self, tokens=None):
        self.value = list(tokens) if tokens else []

    def rpn_repr(self):
        inner = " ".join(self.value)
        return "« " + inner + " »"

    def __repr__(self):
        return f"RPNProgram({self.value})"

    def _hashable(self):
        return tuple(self.value)


class RPNSymbol(RPNObject):
    """Quoted symbol / variable name (e.g. 'X')."""

    def __init__(self, name):
        self.value = name.upper()

    def rpn_repr(self):
        return f"'{self.value}'"

    def __repr__(self):
        return f"RPNSymbol('{self.value}')"


def rpn_copy(obj):
    """Deep copy an RPN object."""
    return copy.deepcopy(obj)


def to_rpn_object(value):
    """Convert a Python value to an RPNObject if it isn't one already."""
    if isinstance(value, RPNObject):
        return value
    if isinstance(value, (int, float)):
        return RPNNumber(value)
    if isinstance(value, str):
        return RPNString(value)
    if isinstance(value, list):
        return RPNList([to_rpn_object(v) for v in value])
    raise TypeError(f"Cannot convert {type(value)} to RPNObject")
