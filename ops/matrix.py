"""Matrix and vector operations — HP 50g style."""

import math
from operations import register, require_args, require_type, RPNError
from rpn_types import RPNNumber, RPNVector, RPNMatrix, RPNList, rpn_copy


# ── Helper functions ──────────────────────────────────────────────────

def _require_all_numbers(items, msg="Bad Argument Type"):
    for item in items:
        if not isinstance(item, RPNNumber):
            raise RPNError(msg)


def _vec_values(v):
    """Extract plain numbers from an RPNVector."""
    return [item.value for item in v.value]


def _mat_values(m):
    """Extract plain numbers from an RPNMatrix as list of lists."""
    return [[item.value for item in row] for row in m.value]


def _make_vector(values):
    return RPNVector([RPNNumber(v) for v in values])


def _make_matrix(rows):
    return RPNMatrix([[RPNNumber(v) for v in row] for row in rows])


def _check_square(m):
    if m.rows() != m.cols():
        raise RPNError("Invalid Dimension (not square)")


# ── Vector / Matrix creation ──────────────────────────────────────────

@register("→V", "→VECT", "->V", "->VECT", "TOVECT")
def op_to_vector(stack, variables, executor):
    """n items + n → vector: val1 val2 ... valN N →V."""
    require_args(stack, 1)
    n_obj = stack.pop()
    require_type(n_obj, RPNNumber)
    n = int(n_obj.value)
    if n < 1:
        stack.push(n_obj)
        raise RPNError("Bad Argument Value")
    require_args(stack, n)
    items = [stack.pop() for _ in range(n)]
    items.reverse()
    _require_all_numbers(items)
    stack.push(RPNVector(items))


@register("V→", "VECT→", "V->", "VECT->", "FROMVECT")
def op_from_vector(stack, variables, executor):
    """Explode vector onto stack + push dimension."""
    require_args(stack, 1)
    v = stack.pop()
    require_type(v, RPNVector)
    for item in v.value:
        stack.push(rpn_copy(item))
    stack.push(RPNNumber(len(v.value)))


@register("→MAT", "->MAT", "TOMAT")
def op_to_matrix(stack, variables, executor):
    """Build matrix from list/vector: { rows } { cols } →MAT or elements r c →MAT."""
    require_args(stack, 2)
    cols_obj = stack.pop()
    rows_obj = stack.pop()
    require_type(rows_obj, RPNNumber)
    require_type(cols_obj, RPNNumber)
    r = int(rows_obj.value)
    c = int(cols_obj.value)
    if r < 1 or c < 1:
        stack.push(rows_obj)
        stack.push(cols_obj)
        raise RPNError("Bad Argument Value")
    n = r * c
    require_args(stack, n)
    items = [stack.pop() for _ in range(n)]
    items.reverse()
    _require_all_numbers(items)
    rows = []
    for i in range(r):
        rows.append(items[i * c:(i + 1) * c])
    stack.push(RPNMatrix(rows))


@register("MAT→", "MAT->", "FROMMAT")
def op_from_matrix(stack, variables, executor):
    """Explode matrix onto stack + push {rows, cols}."""
    require_args(stack, 1)
    m = stack.pop()
    require_type(m, RPNMatrix)
    for row in m.value:
        for item in row:
            stack.push(rpn_copy(item))
    stack.push(RPNList([RPNNumber(m.rows()), RPNNumber(m.cols())]))


# ── Dimension / Size ──────────────────────────────────────────────────

@register("MDIMS")
def op_mdims(stack, variables, executor):
    """Push matrix dimensions as {rows, cols}."""
    require_args(stack, 1)
    obj = stack.peek(1)
    if isinstance(obj, RPNMatrix):
        m = stack.pop()
        stack.push(RPNList([RPNNumber(m.rows()), RPNNumber(m.cols())]))
    elif isinstance(obj, RPNVector):
        v = stack.pop()
        stack.push(RPNNumber(v.dimension()))
    else:
        raise RPNError("Bad Argument Type")


# ── Identity matrix ──────────────────────────────────────────────────

@register("IDN", "IDENTITY")
def op_idn(stack, variables, executor):
    """N IDN → N×N identity matrix."""
    require_args(stack, 1)
    n_obj = stack.pop()
    require_type(n_obj, RPNNumber)
    n = int(n_obj.value)
    if n < 1:
        stack.push(n_obj)
        raise RPNError("Bad Argument Value")
    rows = []
    for i in range(n):
        row = [RPNNumber(1 if j == i else 0) for j in range(n)]
        rows.append(row)
    stack.push(RPNMatrix(rows))


# ── Transpose ─────────────────────────────────────────────────────────

@register("TRN", "TRAN")
def op_trn(stack, variables, executor):
    """Transpose a matrix."""
    require_args(stack, 1)
    obj = stack.pop()
    require_type(obj, RPNMatrix)
    vals = _mat_values(obj)
    r, c = obj.rows(), obj.cols()
    t = [[vals[i][j] for i in range(r)] for j in range(c)]
    stack.push(_make_matrix(t))


# ── Determinant ───────────────────────────────────────────────────────

def _det(matrix):
    """Compute determinant recursively."""
    n = len(matrix)
    if n == 1:
        return matrix[0][0]
    if n == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    d = 0
    for j in range(n):
        sub = [row[:j] + row[j + 1:] for row in matrix[1:]]
        d += ((-1) ** j) * matrix[0][j] * _det(sub)
    return d


@register("DET")
def op_det(stack, variables, executor):
    """Determinant of a square matrix."""
    require_args(stack, 1)
    m = stack.pop()
    require_type(m, RPNMatrix)
    _check_square(m)
    vals = _mat_values(m)
    stack.push(RPNNumber(_det(vals)))


# ── Inverse ───────────────────────────────────────────────────────────

def _matrix_inverse(matrix):
    """Compute inverse using Gauss-Jordan elimination."""
    n = len(matrix)
    # Augment with identity
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(matrix)]

    for col in range(n):
        # Partial pivoting
        max_row = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[max_row][col]) < 1e-15:
            raise RPNError("Singular Matrix")
        aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot = aug[col][col]
        aug[col] = [x / pivot for x in aug[col]]

        for row in range(n):
            if row != col:
                factor = aug[row][col]
                aug[row] = [aug[row][k] - factor * aug[col][k] for k in range(2 * n)]

    return [row[n:] for row in aug]


@register("MINV")
def op_minv(stack, variables, executor):
    """Inverse of a square matrix (same as INV on the HP 50g for matrices)."""
    require_args(stack, 1)
    m = stack.pop()
    require_type(m, RPNMatrix)
    _check_square(m)
    vals = [[float(x) for x in row] for row in _mat_values(m)]
    inv = _matrix_inverse(vals)
    stack.push(_make_matrix(inv))


# ── Cross product ─────────────────────────────────────────────────────

@register("CROSS")
def op_cross(stack, variables, executor):
    """Cross product of two 3D vectors."""
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNVector)
    require_type(b, RPNVector)
    if a.dimension() != 3 or b.dimension() != 3:
        stack.push(a)
        stack.push(b)
        raise RPNError("Invalid Dimension (need 3D vectors)")
    av, bv = _vec_values(a), _vec_values(b)
    result = [
        av[1] * bv[2] - av[2] * bv[1],
        av[2] * bv[0] - av[0] * bv[2],
        av[0] * bv[1] - av[1] * bv[0],
    ]
    stack.push(_make_vector(result))


# ── Dot product ───────────────────────────────────────────────────────

@register("DOT")
def op_dot(stack, variables, executor):
    """Dot product of two vectors."""
    require_args(stack, 2)
    b = stack.pop()
    a = stack.pop()
    require_type(a, RPNVector)
    require_type(b, RPNVector)
    if a.dimension() != b.dimension():
        stack.push(a)
        stack.push(b)
        raise RPNError("Invalid Dimension")
    av, bv = _vec_values(a), _vec_values(b)
    stack.push(RPNNumber(sum(x * y for x, y in zip(av, bv))))


# ── Norm (ABS of a vector) ───────────────────────────────────────────

@register("VNORM")
def op_vnorm(stack, variables, executor):
    """Euclidean norm of a vector."""
    require_args(stack, 1)
    v = stack.pop()
    require_type(v, RPNVector)
    vals = _vec_values(v)
    stack.push(RPNNumber(math.sqrt(sum(x * x for x in vals))))


# ── Frobenius norm of a matrix ────────────────────────────────────────

@register("MNORM")
def op_mnorm(stack, variables, executor):
    """Frobenius norm of a matrix."""
    require_args(stack, 1)
    m = stack.pop()
    require_type(m, RPNMatrix)
    vals = _mat_values(m)
    stack.push(RPNNumber(math.sqrt(sum(x * x for row in vals for x in row))))


# ── GET / PUT for vectors and matrices ─────────────────────────────────

@register("VGET")
def op_vget(stack, variables, executor):
    """Get element from vector: vec index VGET → element."""
    require_args(stack, 2)
    idx = stack.pop()
    obj = stack.pop()
    require_type(idx, RPNNumber)
    require_type(obj, RPNVector)
    i = int(idx.value) - 1  # HP 50g uses 1-based indexing
    if i < 0 or i >= len(obj.value):
        stack.push(obj)
        stack.push(idx)
        raise RPNError("Index Out Of Range")
    stack.push(rpn_copy(obj.value[i]))


@register("VPUT")
def op_vput(stack, variables, executor):
    """Put element in vector: vec index value VPUT → modified vec."""
    require_args(stack, 3)
    val = stack.pop()
    idx = stack.pop()
    obj = stack.pop()
    require_type(idx, RPNNumber)
    require_type(val, RPNNumber)
    require_type(obj, RPNVector)
    i = int(idx.value) - 1
    if i < 0 or i >= len(obj.value):
        stack.push(obj)
        stack.push(idx)
        stack.push(val)
        raise RPNError("Index Out Of Range")
    new_v = rpn_copy(obj)
    new_v.value[i] = rpn_copy(val)
    stack.push(new_v)


@register("MGET")
def op_mget(stack, variables, executor):
    """Get element from matrix: mat {r c} MGET → element."""
    require_args(stack, 2)
    pos = stack.pop()
    obj = stack.pop()
    require_type(obj, RPNMatrix)
    require_type(pos, RPNList, msg="Bad Argument Type (expected {row col})")
    if len(pos.value) != 2:
        stack.push(obj)
        stack.push(pos)
        raise RPNError("Bad Argument Value")
    r = int(pos.value[0].value) - 1
    c = int(pos.value[1].value) - 1
    if r < 0 or r >= obj.rows() or c < 0 or c >= obj.cols():
        stack.push(obj)
        stack.push(pos)
        raise RPNError("Index Out Of Range")
    stack.push(rpn_copy(obj.value[r][c]))


@register("MPUT")
def op_mput(stack, variables, executor):
    """Put element in matrix: mat {r c} value MPUT → modified mat."""
    require_args(stack, 3)
    val = stack.pop()
    pos = stack.pop()
    obj = stack.pop()
    require_type(obj, RPNMatrix)
    require_type(pos, RPNList, msg="Bad Argument Type (expected {row col})")
    require_type(val, RPNNumber)
    if len(pos.value) != 2:
        stack.push(obj)
        stack.push(pos)
        stack.push(val)
        raise RPNError("Bad Argument Value")
    r = int(pos.value[0].value) - 1
    c = int(pos.value[1].value) - 1
    if r < 0 or r >= obj.rows() or c < 0 or c >= obj.cols():
        stack.push(obj)
        stack.push(pos)
        stack.push(val)
        raise RPNError("Index Out Of Range")
    new_m = rpn_copy(obj)
    new_m.value[r][c] = rpn_copy(val)
    stack.push(new_m)


# ── CON (constant matrix/vector) ─────────────────────────────────────

@register("CON")
def op_con(stack, variables, executor):
    """Create matrix/vector filled with a constant.
    {r c} val CON → matrix filled with val
    n val CON → vector of length n filled with val
    """
    require_args(stack, 2)
    val = stack.pop()
    dim = stack.pop()
    require_type(val, RPNNumber)
    if isinstance(dim, RPNNumber):
        n = int(dim.value)
        stack.push(RPNVector([rpn_copy(val) for _ in range(n)]))
    elif isinstance(dim, RPNList) and len(dim.value) == 2:
        r = int(dim.value[0].value)
        c = int(dim.value[1].value)
        stack.push(RPNMatrix([[rpn_copy(val) for _ in range(c)] for _ in range(r)]))
    else:
        stack.push(dim)
        stack.push(val)
        raise RPNError("Bad Argument Type")


# ── RANM (random matrix) ─────────────────────────────────────────────

@register("RANM")
def op_ranm(stack, variables, executor):
    """Create matrix with random integers.
    {r c} RANM → matrix
    """
    import random
    require_args(stack, 1)
    dim = stack.pop()
    require_type(dim, RPNList, msg="Bad Argument Type (expected {rows cols})")
    if len(dim.value) != 2:
        stack.push(dim)
        raise RPNError("Bad Argument Value")
    r = int(dim.value[0].value)
    c = int(dim.value[1].value)
    rows = [[RPNNumber(random.randint(-9, 9)) for _ in range(c)] for _ in range(r)]
    stack.push(RPNMatrix(rows))


# ── Trace ─────────────────────────────────────────────────────────────

@register("TRACE")
def op_trace(stack, variables, executor):
    """Trace of a square matrix (sum of diagonal)."""
    require_args(stack, 1)
    m = stack.pop()
    require_type(m, RPNMatrix)
    _check_square(m)
    vals = _mat_values(m)
    stack.push(RPNNumber(sum(vals[i][i] for i in range(m.rows()))))


# ── Row operations ────────────────────────────────────────────────────

@register("RREF")
def op_rref(stack, variables, executor):
    """Reduced Row Echelon Form."""
    require_args(stack, 1)
    m = stack.pop()
    require_type(m, RPNMatrix)
    vals = [[float(x) for x in row] for row in _mat_values(m)]
    r, c = m.rows(), m.cols()
    pivot_row = 0
    for col in range(c):
        if pivot_row >= r:
            break
        # Find pivot
        max_row = max(range(pivot_row, r), key=lambda i: abs(vals[i][col]))
        if abs(vals[max_row][col]) < 1e-15:
            continue
        vals[pivot_row], vals[max_row] = vals[max_row], vals[pivot_row]
        pivot = vals[pivot_row][col]
        vals[pivot_row] = [x / pivot for x in vals[pivot_row]]
        for row in range(r):
            if row != pivot_row and abs(vals[row][col]) > 1e-15:
                factor = vals[row][col]
                vals[row] = [vals[row][k] - factor * vals[pivot_row][k] for k in range(c)]
        pivot_row += 1
    stack.push(_make_matrix(vals))
