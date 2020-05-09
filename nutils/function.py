# Copyright (c) 2014 Evalf
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Function module.
"""

from . import evaluable, types, expression, util, numeric, warnings
from .evaluable import Array, asarray, replace, TransformsIndexWithTail, ApplyTransforms, TRANS, Inflate, Polyval, ElemwiseFromCallable, Elemwise, Range
import abc, re, inspect, operator, types as builtin_types, numpy, itertools, functools

Argument = evaluable.Argument
Constant = evaluable.Constant
simplified = evaluable.simplified

# FUNCTIONS

add = evaluable.add
multiply = evaluable.multiply
sum = evaluable.sum
product = evaluable.product
power = evaluable.power
dot = evaluable.dot
transpose = evaluable.transpose
swapaxes = evaluable.swapaxes
isarray = evaluable.isarray
iszero = evaluable.iszero
zeros = evaluable.zeros
zeros_like = evaluable.zeros_like
ones = evaluable.ones
ones_like = evaluable.ones_like
reciprocal = evaluable.reciprocal
grad = evaluable.grad
symgrad = evaluable.symgrad
div = evaluable.div
negative = evaluable.negative
nsymgrad = evaluable.nsymgrad
ngrad = evaluable.ngrad
sin = evaluable.sin
cos = evaluable.cos
rotmat = evaluable.rotmat
tan = evaluable.tan
arcsin = evaluable.arcsin
arccos = evaluable.arccos
arctan = evaluable.arctan
exp = evaluable.exp
ln = evaluable.ln
mod = evaluable.mod
log2 = evaluable.log2
log10 = evaluable.log10
sqrt = evaluable.sqrt
arctan2 = evaluable.arctan2
greater = evaluable.greater
equal = evaluable.equal
less = evaluable.less
min = evaluable.min
max = evaluable.max
abs = evaluable.abs
sinh = evaluable.sinh
cosh = evaluable.cosh
tanh = evaluable.tanh
arctanh = evaluable.arctanh
piecewise = evaluable.piecewise
partition = evaluable.partition
trace = evaluable.trace
normalized = evaluable.normalized
norm2 = evaluable.norm2
heaviside = evaluable.heaviside
divide = evaluable.divide
subtract = evaluable.subtract
mean = evaluable.mean
jump = evaluable.jump
add_T = evaluable.add_T
blocks = evaluable.blocks
rootcoords = evaluable.rootcoords
opposite = evaluable.opposite
bifurcate1 = evaluable.bifurcate1
bifurcate2 = evaluable.bifurcate2
bifurcate = evaluable.bifurcate
curvature = evaluable.curvature
laplace = evaluable.laplace
symgrad = evaluable.symgrad
div = evaluable.div
tangent = evaluable.tangent
ngrad = evaluable.ngrad
nsymgrad = evaluable.nsymgrad
expand_dims = evaluable.expand_dims
trignormal = evaluable.trignormal
trigtangent = evaluable.trigtangent
eye = evaluable.eye
insertaxis = evaluable.insertaxis
stack = evaluable.stack
chain = evaluable.chain
vectorize = evaluable.vectorize
repeat = evaluable.repeat
get = evaluable.get
jacobian = evaluable.jacobian
matmat = evaluable.matmat
determinant = evaluable.determinant
inverse = evaluable.inverse
takediag = evaluable.takediag
derivative = evaluable.derivative
localgradient = evaluable.localgradient
dotnorm = evaluable.dotnorm
normal = evaluable.normal
kronecker = evaluable.kronecker
diagonalize = evaluable.diagonalize
concatenate = evaluable.concatenate
cross = evaluable.cross
outer = evaluable.outer
sign = evaluable.sign
eig = evaluable.eig
elemwise = evaluable.elemwise
take = evaluable.take
find = evaluable.find
mask = evaluable.mask
J = evaluable.J
unravel = evaluable.unravel
ravel = evaluable.ravel
normal = evaluable.normal
grad = evaluable.grad
dotnorm = evaluable.dotnorm
RevolutionAngle = evaluable.RevolutionAngle
Sampled = evaluable.Sampled

# BASES

class Basis(Array):
  '''Abstract base class for bases.

  A basis is a sequence of elementwise polynomial functions.

  Parameters
  ----------
  ndofs : :class:`int`
      The number of functions in this basis.
  index : :class:`Array`
      The element index.
  coords : :class:`Array`
      The element local coordinates.

  Notes
  -----
  Subclasses must implement :meth:`get_dofs` and :meth:`get_coefficients` and
  if possible should redefine :meth:`get_support`.
  '''

  __slots__ = 'ndofs', 'nelems', 'index', 'coords'
  __cache__ = '_computed_support'

  @types.apply_annotations
  def __init__(self, ndofs:types.strictint, nelems:types.strictint, index:asarray, coords:asarray):
    self.ndofs = ndofs
    self.nelems = nelems
    self.index = index
    self.coords = coords
    super().__init__(args=(index, coords), shape=(ndofs,), dtype=float)

  def evalf(self, index, coords):
    warnings.warn('using explicit basis evaluation; this is usually a bug.', evaluable.ExpensiveEvaluationWarning)
    index, = index
    values = numeric.poly_eval(self.get_coefficients(index)[None], coords)
    inflated = numpy.zeros((coords.shape[0], self.ndofs), float)
    numpy.add.at(inflated, (slice(None), self.get_dofs(index)), values)
    return inflated

  @property
  def _computed_support(self):
    support = [set() for i in range(self.ndofs)]
    for ielem in range(self.nelems):
      for dof in self.get_dofs(ielem):
        support[dof].add(ielem)
    return tuple(types.frozenarray(numpy.fromiter(sorted(ielems), dtype=int), copy=False) for ielems in support)

  def get_support(self, dof):
    '''Return the support of basis function ``dof``.

    If ``dof`` is an :class:`int`, return the indices of elements that form the
    support of ``dof``.  If ``dof`` is an array, return the union of supports
    of the selected dofs as a unique array.  The returned array is always
    unique, i.e. strict monotonic increasing.

    Parameters
    ----------
    dof : :class:`int` or array of :class:`int` or :class:`bool`
        Index or indices of basis function or a mask.

    Returns
    -------
    support : sorted and unique :class:`numpy.ndarray`
        The elements (as indices) where function ``dof`` has support.
    '''

    if numeric.isint(dof):
      return self._computed_support[dof]
    elif numeric.isintarray(dof):
      if dof.ndim != 1:
        raise IndexError('dof has invalid number of dimensions')
      if len(dof) == 0:
        return numpy.array([], dtype=int)
      dof = numpy.unique(dof)
      if dof[0] < 0 or dof[-1] >= self.ndofs:
        raise IndexError('dof out of bounds')
      if self.get_support == __class__.get_support.__get__(self, __class__):
        return numpy.unique([ielem for ielem in range(self.nelems) if numpy.in1d(self.get_dofs(ielem), dof, assume_unique=True).any()])
      else:
        return numpy.unique(numpy.fromiter(itertools.chain.from_iterable(map(self.get_support, dof)), dtype=int))
    elif numeric.isboolarray(dof):
      if dof.shape != (self.ndofs,):
        raise IndexError('dof has invalid shape')
      return self.get_support(numpy.where(dof)[0])
    else:
      raise IndexError('invalid dof')

  @abc.abstractmethod
  def get_dofs(self, ielem):
    '''Return an array of indices of basis functions with support on element ``ielem``.

    If ``ielem`` is an :class:`int`, return the dofs on element ``ielem``
    matching the coefficients array as returned by :meth:`get_coefficients`.
    If ``ielem`` is an array, return the union of dofs on the selected elements
    as a unique array, i.e. a strict monotonic increasing array.

    Parameters
    ----------
    ielem : :class:`int` or array of :class:`int` or :class:`bool`
        Element number(s) or mask.

    Returns
    -------
    dofs : :class:`numpy.ndarray`
        A 1D Array of indices.
    '''

    if numeric.isint(ielem):
      raise NotImplementedError
    elif numeric.isintarray(ielem):
      if ielem.ndim != 1:
        raise IndexError('invalid ielem')
      if len(ielem) == 0:
        return numpy.array([], dtype=int)
      ielem = numpy.unique(ielem)
      if ielem[0] < 0 or ielem[-1] >= self.nelems:
        raise IndexError('ielem out of bounds')
      return numpy.unique(numpy.fromiter(itertools.chain.from_iterable(map(self.get_dofs, ielem)), dtype=int))
    elif numeric.isboolarray(ielem):
      if ielem.shape != (self.nelems,):
        raise IndexError('ielem has invalid shape')
      return self.get_dofs(numpy.where(ielem)[0])
    else:
      raise IndexError('invalid index')

  def get_ndofs(self, ielem):
    '''Return the number of basis functions with support on element ``ielem``.'''

    return len(self.get_dofs(ielem))

  @abc.abstractmethod
  def get_coefficients(self, ielem):
    '''Return an array of coefficients for all basis functions with support on element ``ielem``.

    Parameters
    ----------
    ielem : :class:`int`
        Element number.

    Returns
    -------
    coefficients : :class:`nutils.types.frozenarray`
        Array of coefficients with shape ``(nlocaldofs,)+(degree,)*ndims``,
        where the first axis corresponds to the dofs returned by
        :meth:`get_dofs`.
    '''

    raise NotImplementedError

  def get_coeffshape(self, ielem):
    '''Return the shape of the array of coefficients for basis functions with support on element ``ielem``.'''

    return numpy.asarray(self.get_coefficients(ielem).shape[1:])

  def f_ndofs(self, index):
    return ElemwiseFromCallable(self.get_ndofs, index, dtype=int, shape=())

  def f_dofs(self, index):
    return ElemwiseFromCallable(self.get_dofs, index, dtype=int, shape=(self.f_ndofs(index),))

  def f_coefficients(self, index):
    coeffshape = ElemwiseFromCallable(self.get_coeffshape, index, dtype=int, shape=self.coords.shape)
    return ElemwiseFromCallable(self.get_coefficients, index, dtype=float, shape=(self.f_ndofs(index), *coeffshape))

  @property
  def simplified(self):
    return Inflate(Polyval(self.f_coefficients(self.index), self.coords), self.f_dofs(self.index), self.shape[0], axis=0).simplified

  def _derivative(self, var, seen):
    return self.simplified._derivative(var, seen)

  def __getitem__(self, index):
    if numeric.isintarray(index) and index.ndim == 1 and numpy.all(numpy.greater(numpy.diff(index), 0)):
      return MaskedBasis(self, index)
    elif numeric.isboolarray(index) and index.shape == (self.ndofs,):
      return MaskedBasis(self, numpy.where(index)[0])
    else:
      return super().__getitem__(index)

strictbasis = types.strict[Basis]

class PlainBasis(Basis):
  '''A general purpose implementation of a :class:`Basis`.

  Use this class only if there exists no specific implementation of
  :class:`Basis` for the basis at hand.

  Parameters
  ----------
  coefficients : :class:`tuple` of :class:`nutils.types.frozenarray` objects
      The coefficients of the basis functions per transform.  The order should
      match the ``transforms`` argument.
  dofs : :class:`tuple` of :class:`nutils.types.frozenarray` objects
      The dofs corresponding to the ``coefficients`` argument.
  ndofs : :class:`int`
      The number of basis functions.
  index : :class:`Array`
      The element index.
  coords : :class:`Array`
      The element local coordinates.
  '''

  __slots__ = '_coeffs', '_dofs'

  @types.apply_annotations
  def __init__(self, coefficients:types.tuple[types.frozenarray], dofs:types.tuple[types.frozenarray], ndofs:types.strictint, index:asarray, coords:asarray):
    self._coeffs = coefficients
    self._dofs = dofs
    assert len(self._coeffs) == len(self._dofs)
    assert all(c.ndim == 1+coords.shape[0] for c in self._coeffs)
    assert all(len(c) == len(d) for c, d in zip(self._coeffs, self._dofs))
    super().__init__(ndofs, len(coefficients), index, coords)

  def get_dofs(self, ielem):
    if not numeric.isint(ielem):
      return super().get_dofs(ielem)
    return self._dofs[ielem]

  def get_coefficients(self, ielem):
    return self._coeffs[ielem]

  def f_ndofs(self, index):
    ndofs = numpy.fromiter(map(len, self._dofs), dtype=int, count=len(self._dofs))
    return get(types.frozenarray(ndofs, copy=False), 0, index)

  def f_dofs(self, index):
    return Elemwise(self._dofs, index, dtype=int)

  def f_coefficients(self, index):
    return Elemwise(self._coeffs, index, dtype=float)

class DiscontBasis(Basis):
  '''A discontinuous basis with monotonic increasing dofs.

  Parameters
  ----------
  coefficients : :class:`tuple` of :class:`nutils.types.frozenarray` objects
      The coefficients of the basis functions per transform.  The order should
      match the ``transforms`` argument.
  index : :class:`Array`
      The element index.
  coords : :class:`Array`
      The element local coordinates.
  '''

  __slots__ = '_coeffs', '_offsets'

  @types.apply_annotations
  def __init__(self, coefficients:types.tuple[types.frozenarray], index:asarray, coords:asarray):
    self._coeffs = coefficients
    assert all(c.ndim == 1+coords.shape[0] for c in self._coeffs)
    self._offsets = types.frozenarray(numpy.cumsum([0, *map(len, self._coeffs)]), copy=False)
    super().__init__(self._offsets[-1], len(coefficients), index, coords)

  def get_support(self, dof):
    if not numeric.isint(dof):
      return super().get_support(dof)
    ielem = numpy.searchsorted(self._offsets[:-1], numeric.normdim(self.ndofs, dof), side='right')-1
    return numpy.array([ielem], dtype=int)

  def get_dofs(self, ielem):
    if not numeric.isint(ielem):
      return super().get_dofs(ielem)
    ielem = numeric.normdim(self.nelems, ielem)
    return numpy.arange(self._offsets[ielem], self._offsets[ielem+1])

  def get_ndofs(self, ielem):
    return self._offsets[ielem+1] - self._offsets[ielem]

  def get_coefficients(self, ielem):
    return self._coeffs[ielem]

  def f_ndofs(self, index):
    ndofs = numpy.diff(self._offsets)
    return get(types.frozenarray(ndofs, copy=False), 0, index)

  def f_dofs(self, index):
    return Range(self.f_ndofs(index), offset=get(self._offsets, 0, index))

  def f_coefficients(self, index):
    return Elemwise(self._coeffs, index, dtype=float)

class MaskedBasis(Basis):
  '''An order preserving subset of another :class:`Basis`.

  Parameters
  ----------
  parent : :class:`Basis`
      The basis to mask.
  indices : array of :class:`int`\\s
      The strict monotonic increasing indices of ``parent`` basis functions to
      keep.
  '''

  __slots__ = '_parent', '_indices'

  @types.apply_annotations
  def __init__(self, parent:strictbasis, indices:types.frozenarray[types.strictint]):
    if indices.ndim != 1:
      raise ValueError('`indices` should have one dimension but got {}'.format(indices.ndim))
    if len(indices) and not numpy.all(numpy.greater(numpy.diff(indices), 0)):
      raise ValueError('`indices` should be strictly monotonic increasing')
    if len(indices) and (indices[0] < 0 or indices[-1] >= len(parent)):
      raise ValueError('`indices` out of range \x5b0,{}\x29'.format(0, len(parent)))
    self._parent = parent
    self._indices = indices
    super().__init__(len(self._indices), parent.nelems, parent.index, parent.coords)

  def get_dofs(self, ielem):
    return numeric.sorted_index(self._indices, self._parent.get_dofs(ielem), missing='mask')

  def get_coeffshape(self, ielem):
    return self._parent.get_coeffshape(ielem)

  def get_coefficients(self, ielem):
    mask = numeric.sorted_contains(self._indices, self._parent.get_dofs(ielem))
    return self._parent.get_coefficients(ielem)[mask]

  def get_support(self, dof):
    if numeric.isintarray(dof) and dof.ndim == 1 and numpy.any(numpy.less(dof, 0)):
      raise IndexError('dof out of bounds')
    return self._parent.get_support(self._indices[dof])

class StructuredBasis(Basis):
  '''A basis for class:`nutils.transformseq.StructuredTransforms`.

  Parameters
  ----------
  coeffs : :class:`tuple` of :class:`tuple`\\s of arrays
      Per dimension the coefficients of the basis functions per transform.
  start_dofs : :class:`tuple` of arrays of :class:`int`\\s
      Per dimension the dof of the first entry in ``coeffs`` per transform.
  stop_dofs : :class:`tuple` of arrays of :class:`int`\\s
      Per dimension one plus the dof of the last entry  in ``coeffs`` per
      transform.
  dofs_shape : :class:`tuple` of :class:`int`\\s
      The tensor shape of the dofs.
  transforms_shape : :class:`tuple` of :class:`int`\\s
      The tensor shape of the transforms.
  index : :class:`Array`
      The element index.
  coords : :class:`Array`
      The element local coordinates.
  '''

  __slots__ = '_coeffs', '_start_dofs', '_stop_dofs', '_dofs_shape', '_transforms_shape'

  @types.apply_annotations
  def __init__(self, coeffs:types.tuple[types.tuple[types.frozenarray]], start_dofs:types.tuple[types.frozenarray[types.strictint]], stop_dofs:types.tuple[types.frozenarray[types.strictint]], dofs_shape:types.tuple[types.strictint], transforms_shape:types.tuple[types.strictint], index:asarray, coords:asarray):
    self._coeffs = coeffs
    self._start_dofs = start_dofs
    self._stop_dofs = stop_dofs
    self._dofs_shape = dofs_shape
    self._transforms_shape = transforms_shape
    super().__init__(util.product(dofs_shape), util.product(transforms_shape), index, coords)

  def _get_indices(self, ielem):
    ielem = numeric.normdim(self.nelems, ielem)
    indices = []
    for n in reversed(self._transforms_shape):
      ielem, index = divmod(ielem, n)
      indices.insert(0, index)
    if ielem != 0:
      raise IndexError
    return tuple(indices)

  def get_dofs(self, ielem):
    if not numeric.isint(ielem):
      return super().get_dofs(ielem)
    indices = self._get_indices(ielem)
    dofs = numpy.array(0)
    for start_dofs_i, stop_dofs_i, ndofs_i, index_i in zip(self._start_dofs, self._stop_dofs, self._dofs_shape, indices):
      dofs_i = numpy.arange(start_dofs_i[index_i], stop_dofs_i[index_i], dtype=int) % ndofs_i
      dofs = numpy.add.outer(dofs*ndofs_i, dofs_i)
    return types.frozenarray(dofs.ravel(), dtype=types.strictint, copy=False)

  def get_ndofs(self, ielem):
    indices = self._get_indices(ielem)
    ndofs = 1
    for start_dofs_i, stop_dofs_i, index_i in zip(self._start_dofs, self._stop_dofs, indices):
      ndofs *= stop_dofs_i[index_i] - start_dofs_i[index_i]
    return ndofs

  def get_coefficients(self, ielem):
    return functools.reduce(numeric.poly_outer_product, map(operator.getitem, self._coeffs, self._get_indices(ielem)))

  def f_coefficients(self, index):
    coeffs = []
    for coeffs_i in self._coeffs:
      if any(coeffs_ij != coeffs_i[0] for coeffs_ij in coeffs_i[1:]):
        return super().f_coefficients(index)
      coeffs.append(coeffs_i[0])
    return Constant(functools.reduce(numeric.poly_outer_product, coeffs))

  def f_ndofs(self, index):
    ndofs = 1
    for start_dofs_i, stop_dofs_i in zip(self._start_dofs, self._stop_dofs):
      ndofs_i = stop_dofs_i - start_dofs_i
      if any(ndofs_ij != ndofs_i[0] for ndofs_ij in ndofs_i[1:]):
        return super().f_ndofs(index)
      ndofs *= ndofs_i[0]
    return Constant(ndofs)

  def get_support(self, dof):
    if not numeric.isint(dof):
      return super().get_support(dof)
    dof = numeric.normdim(self.ndofs, dof)
    ndofs = 1
    ntrans = 1
    supports = []
    for start_dofs_i, stop_dofs_i, ndofs_i, ntrans_i in zip(reversed(self._start_dofs), reversed(self._stop_dofs), reversed(self._dofs_shape), reversed(self._transforms_shape)):
      dof, dof_i = divmod(dof, ndofs_i)
      supports_i = []
      while dof_i < stop_dofs_i[-1]:
        stop_ielem = numpy.searchsorted(start_dofs_i, dof_i, side='right')
        start_ielem = numpy.searchsorted(stop_dofs_i, dof_i, side='right')
        supports_i.append(numpy.arange(start_ielem, stop_ielem, dtype=int))
        dof_i += ndofs_i
      supports.append(numpy.unique(numpy.concatenate(supports_i)) * ntrans)
      ndofs *= ndofs_i
      ntrans *= ntrans_i
    assert dof == 0
    return types.frozenarray(functools.reduce(numpy.add.outer, reversed(supports)).ravel(), copy=False, dtype=types.strictint)

class PrunedBasis(Basis):
  '''A subset of another :class:`Basis`.

  Parameters
  ----------
  parent : :class:`Basis`
      The basis to prune.
  transmap : one-dimensional array of :class:`int`\\s
      The indices of transforms in ``parent`` that form this subset.
  index : :class:`Array`
      The element index.
  coords : :class:`Array`
      The element local coordinates.
  '''

  __slots__ = '_parent', '_transmap', '_dofmap'

  @types.apply_annotations
  def __init__(self, parent:strictbasis, transmap:types.frozenarray[types.strictint], index:asarray, coords:asarray):
    self._parent = parent
    self._transmap = transmap
    self._dofmap = parent.get_dofs(self._transmap)
    super().__init__(len(self._dofmap), len(transmap), index, coords)

  def get_dofs(self, ielem):
    if numeric.isintarray(ielem) and ielem.ndim == 1 and numpy.any(numpy.less(ielem, 0)):
      raise IndexError('dof out of bounds')
    return types.frozenarray(numpy.searchsorted(self._dofmap, self._parent.get_dofs(self._transmap[ielem])), copy=False)

  def get_coefficients(self, ielem):
    return self._parent.get_coefficients(self._transmap[ielem])

  def get_support(self, dof):
    if numeric.isintarray(dof) and dof.ndim == 1 and numpy.any(numpy.less(dof, 0)):
      raise IndexError('dof out of bounds')
    return numeric.sorted_index(self._transmap, self._parent.get_support(self._dofmap[dof]), missing='mask')

  def f_ndofs(self, index):
    return self._parent.f_ndofs(get(self._transmap, 0, index))

  def f_coefficients(self, index):
    return self._parent.f_coefficients(get(self._transmap, 0, index))

# NAMESPACE

@replace
def replace_arguments(value, arguments):
  '''Replace :class:`Argument` objects in ``value``.

  Replace :class:`Argument` objects in ``value`` according to the ``arguments``
  map, taking into account derivatives to the local coordinates.

  Args
  ----
  value : :class:`Array`
      Array to be edited.
  arguments : :class:`collections.abc.Mapping` with :class:`Array`\\s as values
      :class:`Argument`\\s replacements.  The key correspond to the ``name``
      passed to an :class:`Argument` and the value is the replacement.

  Returns
  -------
  :class:`Array`
      The edited ``value``.
  '''
  if isinstance(value, Argument) and value._name in arguments:
    v = asarray(arguments[value._name])
    assert value.shape[:value.ndim-value._nderiv] == v.shape
    for ndims in value.shape[value.ndim-value._nderiv:]:
      v = localgradient(v, ndims)
    return v

def _eval_ast(ast, functions):
  '''evaluate ``ast`` generated by :func:`nutils.expression.parse`'''

  op, *args = ast
  if op is None:
    value, = args
    return value

  args = (_eval_ast(arg, functions) for arg in args)
  if op == 'group':
    array, = args
    return array
  elif op == 'arg':
    name, *shape = args
    return Argument(name, shape)
  elif op == 'substitute':
    array, *arg_value_pairs = args
    subs = {}
    assert len(arg_value_pairs) % 2 == 0
    for arg, value in zip(arg_value_pairs[0::2], arg_value_pairs[1::2]):
      assert isinstance(arg, Argument) and arg._nderiv == 0
      assert arg._name not in subs
      subs[arg._name] = value
    return replace_arguments(array, subs)
  elif op == 'call':
    func, *args = args
    return functions[func](*args)
  elif op == 'jacobian':
    geom, ndims = args
    return J(geom, ndims)
  elif op == 'eye':
    length, = args
    return eye(length)
  elif op == 'normal':
    geom, = args
    return normal(geom)
  elif op == 'getitem':
    array, dim, index = args
    return get(array, dim, index)
  elif op == 'trace':
    array, n1, n2 = args
    return trace(array, n1, n2)
  elif op == 'sum':
    array, axis = args
    return sum(array, axis)
  elif op == 'concatenate':
    return concatenate(args, axis=0)
  elif op == 'grad':
    array, geom = args
    return grad(array, geom)
  elif op == 'surfgrad':
    array, geom = args
    return grad(array, geom, len(geom)-1)
  elif op == 'derivative':
    func, target = args
    return derivative(func, target)
  elif op == 'append_axis':
    array, length = args
    return insertaxis(array, -1, length)
  elif op == 'transpose':
    array, trans = args
    return transpose(array, trans)
  elif op == 'jump':
    array, = args
    return jump(array)
  elif op == 'mean':
    array, = args
    return mean(array)
  elif op == 'neg':
    array, = args
    return -asarray(array)
  elif op in ('add', 'sub', 'mul', 'truediv', 'pow'):
    left, right = args
    return getattr(operator, '__{}__'.format(op))(asarray(left), asarray(right))
  else:
    raise ValueError('unknown opcode: {!r}'.format(op))

class Namespace:
  '''Namespace for :class:`Array` objects supporting assignments with tensor expressions.

  The :class:`Namespace` object is used to store :class:`Array` objects.

  >>> from nutils import function
  >>> ns = function.Namespace()
  >>> ns.A = function.zeros([3, 3])
  >>> ns.x = function.zeros([3])
  >>> ns.c = 2

  In addition to the assignment of :class:`Array` objects, it is also possible
  to specify an array using a tensor expression string — see
  :func:`nutils.expression.parse` for the syntax.  All attributes defined in
  this namespace are available as variables in the expression.  If the array
  defined by the expression has one or more dimensions the indices of the axes
  should be appended to the attribute name.  Examples:

  >>> ns.cAx_i = 'c A_ij x_j'
  >>> ns.xAx = 'x_i A_ij x_j'

  It is also possible to simply evaluate an expression without storing its
  value in the namespace by passing the expression to the method ``eval_``
  suffixed with appropriate indices:

  >>> ns.eval_('2 c')
  Array<>
  >>> ns.eval_i('c A_ij x_j')
  Array<3>
  >>> ns.eval_ij('A_ij + A_ji')
  Array<3,3>

  For zero and one dimensional expressions the following shorthand can be used:

  >>> '2 c' @ ns
  Array<>
  >>> 'A_ij x_j' @ ns
  Array<3>

  Sometimes the dimension of an expression cannot be determined, e.g. when
  evaluating the identity array:

  >>> ns.eval_ij('δ_ij')
  Traceback (most recent call last):
  ...
  nutils.expression.ExpressionSyntaxError: Length of axis cannot be determined from the expression.
  δ_ij
    ^

  There are two ways to inform the namespace of the correct lengths.  The first is to
  assign fixed lengths to certain indices via keyword argument ``length_<indices>``:

  >>> ns_fixed = function.Namespace(length_ij=2)
  >>> ns_fixed.eval_ij('δ_ij')
  Array<2,2>

  Note that evaluating an expression with an incompatible length raises an
  exception:

  >>> ns = function.Namespace(length_i=2)
  >>> ns.a = numpy.array([1,2,3])
  >>> 'a_i' @ ns
  Traceback (most recent call last):
  ...
  nutils.expression.ExpressionSyntaxError: Length of index i is fixed at 2 but the expression has length 3.
  a_i
    ^

  The second is to define a fallback length via the ``fallback_length`` argument:

  >>> ns_fallback = function.Namespace(fallback_length=2)
  >>> ns_fallback.eval_ij('δ_ij')
  Array<2,2>

  When evaluating an expression through this namespace the following functions
  are available: ``opposite``, ``sin``, ``cos``, ``tan``, ``sinh``, ``cosh``,
  ``tanh``, ``arcsin``, ``arccos``, ``arctan2``, ``arctanh``, ``exp``, ``abs``,
  ``ln``, ``log``, ``log2``, ``log10``, ``sqrt`` and ``sign``.

  Args
  ----
  default_geometry_name : :class:`str`
      The name of the default geometry.  This argument is passed to
      :func:`nutils.expression.parse`.  Default: ``'x'``.
  fallback_length : :class:`int`, optional
      The fallback length of an axis if the length cannot be determined from
      the expression.
  length_<indices> : :class:`int`
      The fixed length of ``<indices>``.  All axes in the expression marked
      with one of the ``<indices>`` are asserted to have the specified length.

  Attributes
  ----------
  arg_shapes : :class:`dict`
      A readonly map of argument names and shapes.
  default_geometry_name : :class:`str`
      The name of the default geometry.  See argument with the same name.
  '''

  __slots__ = '_attributes', '_arg_shapes', 'default_geometry_name', '_fixed_lengths', '_fallback_length'

  _re_assign = re.compile('^([a-zA-Zα-ωΑ-Ω][a-zA-Zα-ωΑ-Ω0-9]*)(_[a-z]+)?$')

  _functions = dict(
    opposite=opposite, sin=sin, cos=cos, tan=tan, sinh=sinh, cosh=cosh,
    tanh=tanh, arcsin=arcsin, arccos=arccos, arctan=arctan, arctan2=arctan2, arctanh=arctanh,
    exp=exp, abs=abs, ln=ln, log=ln, log2=log2, log10=log10, sqrt=sqrt,
    sign=sign,
  )
  _functions_nargs = {k: len(inspect.signature(v).parameters) for k, v in _functions.items()}

  @types.apply_annotations
  def __init__(self, *, default_geometry_name='x', fallback_length:types.strictint=None, **kwargs):
    if not isinstance(default_geometry_name, str):
      raise ValueError('default_geometry_name: Expected a str, got {!r}.'.format(default_geometry_name))
    if '_' in default_geometry_name or not self._re_assign.match(default_geometry_name):
      raise ValueError('default_geometry_name: Invalid variable name: {!r}.'.format(default_geometry_name))
    fixed_lengths = {}
    for name, value in kwargs.items():
      if not name.startswith('length_'):
        raise TypeError('__init__() got an unexpected keyword argument {!r}'.format(name))
      for index in name[7:]:
        if index in fixed_lengths:
          raise ValueError('length of index {} specified more than once'.format(index))
        fixed_lengths[index] = value
    super().__setattr__('_attributes', {})
    super().__setattr__('_arg_shapes', {})
    super().__setattr__('_fixed_lengths', types.frozendict({i: l for indices, l in fixed_lengths.items() for i in indices} if fixed_lengths else {}))
    super().__setattr__('_fallback_length', fallback_length)
    super().__setattr__('default_geometry_name', default_geometry_name)
    super().__init__()

  def __getstate__(self):
    'Pickle instructions'
    attrs = '_arg_shapes', '_attributes', 'default_geometry_name', '_fixed_lengths', '_fallback_length'
    return {k: getattr(self, k) for k in attrs}

  def __setstate__(self, d):
    'Unpickle instructions'
    for k, v in d.items(): super().__setattr__(k, v)

  @property
  def arg_shapes(self):
    return builtin_types.MappingProxyType(self._arg_shapes)

  @property
  def default_geometry(self):
    ''':class:`nutils.function.Array`: The default geometry, shorthand for ``getattr(ns, ns.default_geometry_name)``.'''
    return getattr(self, self.default_geometry_name)

  def __call__(*args, **subs):
    '''Return a copy with arguments replaced by ``subs``.

    Return a copy of this namespace with :class:`Argument` objects replaced
    according to ``subs``.

    Args
    ----
    **subs : :class:`dict` of :class:`str` and :class:`nutils.function.Array` objects
        Replacements of the :class:`Argument` objects, identified by their names.

    Returns
    -------
    ns : :class:`Namespace`
        The copy of this namespace with replaced :class:`Argument` objects.
    '''

    if len(args) != 1:
      raise TypeError('{} instance takes 1 positional argument but {} were given'.format(type(self).__name__, len(args)))
    self, = args
    ns = Namespace(default_geometry_name=self.default_geometry_name)
    for k, v in self._attributes.items():
      setattr(ns, k, replace_arguments(v, subs))
    return ns

  def copy_(self, *, default_geometry_name=None):
    '''Return a copy of this namespace.'''

    if default_geometry_name is None:
      default_geometry_name = self.default_geometry_name
    ns = Namespace(default_geometry_name=default_geometry_name, fallback_length=self._fallback_length, **{'length_{i}': l for i, l in self._fixed_lengths.items()})
    for k, v in self._attributes.items():
      setattr(ns, k, v)
    return ns

  def __getattr__(self, name):
    '''Get attribute ``name``.'''

    if name.startswith('eval_'):
      return lambda expr: _eval_ast(expression.parse(expr, variables=self._attributes, functions=self._functions_nargs, indices=name[5:], arg_shapes=self._arg_shapes, default_geometry_name=self.default_geometry_name, fixed_lengths=self._fixed_lengths, fallback_length=self._fallback_length)[0], self._functions)
    try:
      return self._attributes[name]
    except KeyError:
      pass
    raise AttributeError(name)

  def __setattr__(self, name, value):
    '''Set attribute ``name`` to ``value``.'''

    if name in self.__slots__:
      raise AttributeError('readonly')
    m = self._re_assign.match(name)
    if not m or m.group(2) and len(set(m.group(2))) != len(m.group(2)):
      raise AttributeError('{!r} object has no attribute {!r}'.format(type(self), name))
    else:
      name, indices = m.groups()
      indices = indices[1:] if indices else ''
      if isinstance(value, str):
        ast, arg_shapes = expression.parse(value, variables=self._attributes, functions=self._functions_nargs, indices=indices, arg_shapes=self._arg_shapes, default_geometry_name=self.default_geometry_name, fixed_lengths=self._fixed_lengths, fallback_length=self._fallback_length)
        value = _eval_ast(ast, self._functions)
        self._arg_shapes.update(arg_shapes)
      else:
        assert not indices
      self._attributes[name] = asarray(value)

  def __delattr__(self, name):
    '''Delete attribute ``name``.'''

    if name in self.__slots__:
      raise AttributeError('readonly')
    elif name in self._attributes:
      del self._attributes[name]
    else:
      raise AttributeError('{!r} object has no attribute {!r}'.format(type(self), name))

  def __rmatmul__(self, expr):
    '''Evaluate zero or one dimensional ``expr`` or a list of expressions.'''

    if isinstance(expr, (tuple, list)):
      return tuple(map(self.__rmatmul__, expr))
    if not isinstance(expr, str):
      return NotImplemented
    try:
      ast = expression.parse(expr, variables=self._attributes, functions=self._functions_nargs, indices=None, arg_shapes=self._arg_shapes, default_geometry_name=self.default_geometry_name, fixed_lengths=self._fixed_lengths, fallback_length=self._fallback_length)[0]
    except expression.AmbiguousAlignmentError:
      raise ValueError('`expression @ Namespace` cannot be used because the expression has more than one dimension.  Use `Namespace.eval_...(expression)` instead')
    return _eval_ast(ast, self._functions)

# vim:sw=2:sts=2:et
