"""Tokenizer and parser for RPN input."""

from rpn_types import RPNNumber, RPNString, RPNList, RPNProgram, RPNSymbol, RPNVector, RPNMatrix


def tokenize(line):
    """Split input into raw token strings, respecting delimiters."""
    tokens = []
    i = 0
    s = line.strip()
    while i < len(s):
        # Skip whitespace
        if s[i].isspace():
            i += 1
            continue

        # String literal "..."
        if s[i] == '"':
            j = s.index('"', i + 1) if '"' in s[i + 1:] else len(s)
            tokens.append(s[i:j + 1])
            i = j + 1
            continue

        # Program start « or <<
        if s[i] == '«' or s[i:i + 2] == '<<':
            depth = 1
            if s[i] == '«':
                start = i
                i += 1
            else:
                start = i
                i += 2
            while i < len(s) and depth > 0:
                if s[i] == '»' or s[i:i + 2] == '>>':
                    depth -= 1
                    if depth == 0:
                        if s[i] == '»':
                            i += 1
                        else:
                            i += 2
                        break
                    else:
                        i += 1 if s[i] == '»' else 2
                elif s[i] == '«' or s[i:i + 2] == '<<':
                    depth += 1
                    i += 1 if s[i] == '«' else 2
                else:
                    i += 1
            tokens.append(s[start:i])
            continue

        # List start {
        if s[i] == '{':
            depth = 1
            start = i
            i += 1
            while i < len(s) and depth > 0:
                if s[i] == '{':
                    depth += 1
                elif s[i] == '}':
                    depth -= 1
                i += 1
            tokens.append(s[start:i])
            continue

        # Matrix [[ ... ]] or Vector [ ... ]
        if s[i] == '[':
            start = i
            if i + 1 < len(s) and s[i + 1] == '[':
                # Matrix [[ ... ]]
                depth = 1
                i += 2
                while i < len(s) and depth > 0:
                    if s[i] == '[' and i + 1 < len(s) and s[i + 1] == '[':
                        depth += 1
                        i += 2
                    elif s[i] == ']' and i + 1 < len(s) and s[i + 1] == ']':
                        depth -= 1
                        i += 2
                    else:
                        i += 1
            else:
                # Vector [ ... ]
                depth = 1
                i += 1
                while i < len(s) and depth > 0:
                    if s[i] == '[':
                        depth += 1
                    elif s[i] == ']':
                        depth -= 1
                    i += 1
            tokens.append(s[start:i])
            continue

        # Quoted symbol 'NAME'
        if s[i] == "'":
            j = i + 1
            while j < len(s) and s[j] not in ("'", " ", "\t"):
                j += 1
            if j < len(s) and s[j] == "'":
                j += 1
            tokens.append(s[i:j])
            i = j
            continue

        # Regular token (number, operator, command name)
        j = i
        while j < len(s) and not s[j].isspace() and s[j] not in ('{', '}', '[', ']', '«', '»'):
            # Check for << or >> as delimiters
            if s[j:j + 2] in ('<<', '>>'):
                break
            j += 1
        if j == i:
            j += 1
        tokens.append(s[i:j])
        i = j

    return tokens


def parse_token(token_str):
    """Parse a single token string into an RPNObject or return the string as a command."""

    # String literal
    if token_str.startswith('"') and token_str.endswith('"'):
        return RPNString(token_str[1:-1])

    # Program
    if (token_str.startswith('«') or token_str.startswith('<<')) and \
       (token_str.endswith('»') or token_str.endswith('>>')):
        inner = token_str
        # Strip delimiters
        if inner.startswith('«'):
            inner = inner[1:]
        else:
            inner = inner[2:]
        if inner.endswith('»'):
            inner = inner[:-1]
        else:
            inner = inner[:-2]
        inner = inner.strip()
        # Tokenize the program body recursively (as raw strings for lazy eval)
        prog_tokens = tokenize(inner) if inner else []
        return RPNProgram(prog_tokens)

    # List { ... }
    if token_str.startswith('{') and token_str.endswith('}'):
        inner = token_str[1:-1].strip()
        if not inner:
            return RPNList([])
        raw_tokens = tokenize(inner)
        items = [parse_token(t) for t in raw_tokens]
        return RPNList(items)

    # Matrix [[ ... ]]
    if token_str.startswith('[[') and token_str.endswith(']]'):
        inner = token_str[2:-2].strip()
        if not inner:
            return RPNMatrix([])
        # Split into rows by matching [ ... ]
        rows = []
        j = 0
        while j < len(inner):
            if inner[j] == '[':
                k = inner.index(']', j)
                row_str = inner[j + 1:k].strip()
                if row_str:
                    row_tokens = tokenize(row_str)
                    row = [parse_token(t) for t in row_tokens]
                    rows.append(row)
                else:
                    rows.append([])
                j = k + 1
            else:
                j += 1
        return RPNMatrix(rows)

    # Vector [ ... ]
    if token_str.startswith('[') and token_str.endswith(']'):
        inner = token_str[1:-1].strip()
        if not inner:
            return RPNVector([])
        raw_tokens = tokenize(inner)
        items = [parse_token(t) for t in raw_tokens]
        return RPNVector(items)

    # Quoted symbol 'NAME' or 'NAME
    if token_str.startswith("'"):
        name = token_str.strip("'")
        return RPNSymbol(name)

    # Number
    try:
        if '.' in token_str or 'e' in token_str.lower():
            return RPNNumber(float(token_str))
        else:
            return RPNNumber(int(token_str))
    except ValueError:
        pass

    # Command / operator name — return as uppercase string
    return token_str.upper()


def parse(line):
    """Parse a full input line into a list of RPNObjects and command strings."""
    raw_tokens = tokenize(line)
    return [parse_token(t) for t in raw_tokens]
