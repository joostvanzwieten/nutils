import numpy, itertools, pickle, warnings as _builtin_warnings
from nutils import function, mesh, transformseq, transform, element, types, evaluable
from nutils.testing import *

class namespace(TestCase):

  def test_set_scalar(self):
    ns = function.Namespace()
    ns.scalar = 1

  def test_set_array(self):
    ns = function.Namespace()
    ns.array = function.zeros([2,3])

  def test_set_scalar_expression(self):
    ns = function.Namespace()
    ns.scalar = '1'

  def test_set_array_expression(self):
    ns = function.Namespace()
    ns.foo = function.zeros([3,3])
    ns.array_ij = 'foo_ij + foo_ji'

  def test_set_readonly(self):
    ns = function.Namespace()
    with self.assertRaises(AttributeError):
      ns._foo = None

  def test_set_readonly_internal(self):
    ns = function.Namespace()
    with self.assertRaises(AttributeError):
      ns._attributes = None

  def test_del_existing(self):
    ns = function.Namespace()
    ns.foo = function.zeros([2,3])
    del ns.foo

  def test_del_readonly_internal(self):
    ns = function.Namespace()
    with self.assertRaises(AttributeError):
      del ns._attributes

  def test_del_nonexisting(self):
    ns = function.Namespace()
    with self.assertRaises(AttributeError):
      del ns.foo

  def test_get_nonexisting(self):
    ns = function.Namespace()
    with self.assertRaises(AttributeError):
      ns.foo

  def test_invalid_default_geometry_no_str(self):
    with self.assertRaises(ValueError):
      function.Namespace(default_geometry_name=None)

  def test_invalid_default_geometry_no_variable(self):
    with self.assertRaises(ValueError):
      function.Namespace(default_geometry_name='foo_bar')

  def test_default_geometry_property(self):
    ns = function.Namespace()
    ns.x = 1
    self.assertEqual(ns.default_geometry, ns.x)
    ns = function.Namespace(default_geometry_name='y')
    ns.y = 2
    self.assertEqual(ns.default_geometry, ns.y)

  def test_copy(self):
    ns = function.Namespace()
    ns.foo = function.zeros([2,3])
    ns = ns.copy_()
    self.assertTrue(hasattr(ns, 'foo'))

  def test_copy_change_geom(self):
    ns1 = function.Namespace()
    domain, ns1.y = mesh.rectilinear([2,2])
    ns1.basis = domain.basis('spline', degree=2)
    ns2 = ns1.copy_(default_geometry_name='y')
    self.assertEqual(ns2.default_geometry_name, 'y')
    self.assertEqual(ns2.eval_ni('basis_n,i'), ns2.basis.grad(ns2.y))

  def test_copy_preserve_geom(self):
    ns1 = function.Namespace(default_geometry_name='y')
    domain, ns1.y = mesh.rectilinear([2,2])
    ns1.basis = domain.basis('spline', degree=2)
    ns2 = ns1.copy_()
    self.assertEqual(ns2.default_geometry_name, 'y')
    self.assertEqual(ns2.eval_ni('basis_n,i'), ns2.basis.grad(ns2.y))

  def test_copy_fixed_lengths(self):
    ns = function.Namespace(length_i=2)
    ns = ns.copy_()
    self.assertEqual(ns.eval_ij('δ_ij').shape, (2,2))

  def test_copy_fallback_length(self):
    ns = function.Namespace(fallback_length=2)
    ns = ns.copy_()
    self.assertEqual(ns.eval_ij('δ_ij').shape, (2,2))

  def test_eval(self):
    ns = function.Namespace()
    ns.foo = function.zeros([3,3])
    ns.eval_ij('foo_ij + foo_ji')

  def test_eval_fixed_lengths(self):
    ns = function.Namespace(length_i=2)
    self.assertEqual(ns.eval_ij('δ_ij').shape, (2,2))

  def test_eval_fixed_lengths_multiple(self):
    ns = function.Namespace(length_jk=2)
    self.assertEqual(ns.eval_ij('δ_ij').shape, (2,2))
    self.assertEqual(ns.eval_ik('δ_ik').shape, (2,2))

  def test_eval_fallback_length(self):
    ns = function.Namespace(fallback_length=2)
    self.assertEqual(ns.eval_ij('δ_ij').shape, (2,2))

  def test_matmul_0d(self):
    ns = function.Namespace()
    ns.foo = 2
    self.assertEqual('foo' @ ns, ns.foo)

  def test_matmul_1d(self):
    ns = function.Namespace()
    ns.foo = function.zeros([2])
    self.assertEqual('foo_i' @ ns, ns.foo)

  def test_matmul_2d(self):
    ns = function.Namespace()
    ns.foo = function.zeros([2, 3])
    with self.assertRaises(ValueError):
      'foo_ij' @ ns

  def test_matmul_nostr(self):
    ns = function.Namespace()
    with self.assertRaises(TypeError):
      1 @ ns

  def test_matmul_fixed_lengths(self):
    ns = function.Namespace(length_i=2)
    self.assertEqual(('1_i δ_ij' @ ns).shape, (2,))

  def test_matmul_fallback_length(self):
    ns = function.Namespace(fallback_length=2)
    self.assertEqual(('1_i δ_ij' @ ns).shape, (2,))

  def test_replace(self):
    ns = function.Namespace(default_geometry_name='y')
    ns.foo = function.Argument('arg', [2,3])
    ns.bar_ij = 'sin(foo_ij) + cos(2 foo_ij)'
    ns = ns(arg=function.zeros([2,3]))
    self.assertEqual(ns.foo, function.zeros([2,3]))
    self.assertEqual(ns.default_geometry_name, 'y')

  def test_pickle(self):
    orig = function.Namespace()
    domain, geom = mesh.unitsquare(2, 'square')
    orig.x = geom
    orig.v = domain.basis('std', 1)
    orig.u = 'v_n ?lhs_n'
    orig.f = 'cosh(x_0)'
    pickled = pickle.loads(pickle.dumps(orig))
    for attr in ('x', 'v', 'u', 'f'):
      self.assertEqual(getattr(pickled, attr), getattr(orig, attr))
    self.assertEqual(pickled.arg_shapes['lhs'], orig.arg_shapes['lhs'])

  def test_pickle_default_geometry_name(self):
    orig = function.Namespace(default_geometry_name='g')
    pickled = pickle.loads(pickle.dumps(orig))
    self.assertEqual(pickled.default_geometry_name, orig.default_geometry_name)

  def test_pickle_fixed_lengths(self):
    orig = function.Namespace(length_i=2)
    pickled = pickle.loads(pickle.dumps(orig))
    self.assertEqual(pickled.eval_ij('δ_ij').shape, (2,2))

  def test_pickle_fallback_length(self):
    orig = function.Namespace(fallback_length=2)
    pickled = pickle.loads(pickle.dumps(orig))
    self.assertEqual(pickled.eval_ij('δ_ij').shape, (2,2))

  def test_duplicate_fixed_lengths(self):
    with self.assertRaisesRegex(ValueError, '^length of index i specified more than once$'):
      function.Namespace(length_ii=2)

  def test_unexpected_keyword_argument(self):
    with self.assertRaisesRegex(TypeError, r"^__init__\(\) got an unexpected keyword argument 'test'$"):
      function.Namespace(test=2)

class eval_ast(TestCase):

  def setUp(self):
    super().setUp()
    domain, x = mesh.rectilinear([2,2])
    self.ns = function.Namespace()
    self.ns.x = x
    self.ns.altgeom_i = '<x_i, 0>_i'
    self.ns.basis = domain.basis('spline', degree=2)
    self.ns.a = 2
    self.ns.a2 = numpy.array([1,2])
    self.ns.a3 = numpy.array([1,2,3])
    self.ns.a22 = numpy.array([[1,2],[3,4]])
    self.ns.a32 = numpy.array([[1,2],[3,4],[5,6]])
    self.x = function.Argument('x',())

  def assertIdentical(self, s, f):
    self.assertEqual((s @ self.ns).simplified, f.simplified)

  def test_group(self): self.assertIdentical('(a)', self.ns.a)
  def test_arg(self): self.assertIdentical('a2_i ?x_i', function.dot(self.ns.a2, function.Argument('x', [2]), axes=[0]))
  def test_substitute(self): self.assertIdentical('(?x_i^2)(x_i=a2_i)', self.ns.a2**2)
  def test_multisubstitute(self): self.assertIdentical('(a2_i + ?x_i + ?y_i)(x_i=?y_i, y_i=?x_i)', self.ns.a2 + function.Argument('y', [2]) + function.Argument('x', [2]))
  def test_call(self): self.assertIdentical('sin(a)', function.sin(self.ns.a))
  def test_eye(self): self.assertIdentical('δ_ij a2_i', function.dot(function.eye(2), self.ns.a2, axes=[0]))
  def test_normal(self): self.assertIdentical('n_i', self.ns.x.normal())
  def test_getitem(self): self.assertIdentical('a2_0', self.ns.a2[0])
  def test_trace(self): self.assertIdentical('a22_ii', function.trace(self.ns.a22, 0, 1))
  def test_sum(self): self.assertIdentical('a2_i a2_i', function.sum(self.ns.a2 * self.ns.a2, axis=0))
  def test_concatenate(self): self.assertIdentical('<a, a2_i>_i', function.concatenate([self.ns.a[None],self.ns.a2], axis=0))
  def test_grad(self): self.assertIdentical('basis_n,0', self.ns.basis.grad(self.ns.x)[:,0])
  def test_surfgrad(self): self.assertIdentical('basis_n;altgeom_0', function.grad(self.ns.basis, self.ns.altgeom, len(self.ns.altgeom)-1)[:,0])
  def test_derivative(self): self.assertIdentical('exp(?x)_,?x', function.derivative(function.exp(self.x), self.x))
  def test_append_axis(self): self.assertIdentical('a a2_i', self.ns.a[None]*self.ns.a2)
  def test_transpose(self): self.assertIdentical('a22_ij a22_ji', function.dot(self.ns.a22, self.ns.a22.T, axes=[0,1]))
  def test_jump(self): self.assertIdentical('[a]', function.jump(self.ns.a))
  def test_mean(self): self.assertIdentical('{a}', function.mean(self.ns.a))
  def test_neg(self): self.assertIdentical('-a', -self.ns.a)
  def test_add(self): self.assertIdentical('a + ?x', self.ns.a + self.x)
  def test_sub(self): self.assertIdentical('a - ?x', self.ns.a - self.x)
  def test_mul(self): self.assertIdentical('a ?x', self.ns.a * self.x)
  def test_truediv(self): self.assertIdentical('a / ?x', self.ns.a / self.x)
  def test_pow(self): self.assertIdentical('a^2', self.ns.a**2)

  def test_unknown_opcode(self):
    with self.assertRaises(ValueError):
      function._eval_ast(('invalid-opcode',), {})

class CommonBasis:

  @staticmethod
  def mk_index_coords(coorddim, transforms):
    index, tail = function.TransformsIndexWithTail(transforms, function.TRANS)
    coords = function.ApplyTransforms(tail)
    assert coords.shape == (coorddim,)
    return index, coords

  def setUp(self):
    super().setUp()
    self.checknelems = len(self.checkcoeffs)
    self.checksupp = [[] for i in range(self.checkndofs)]
    for ielem, dofs in enumerate(self.checkdofs):
      for dof in dofs:
        self.checksupp[dof].append(ielem)
    assert len(self.checkcoeffs) == len(self.checkdofs)
    assert all(len(c) == len(d) for c, d in zip(self.checkcoeffs, self.checkdofs))

  def test_shape(self):
    self.assertEqual(self.basis.shape, (self.checkndofs,))

  def test_get_coeffshape(self):
    for ielem in range(self.checknelems):
      self.assertAllEqual(self.basis.get_coeffshape(ielem), numpy.shape(self.checkcoeffs[ielem])[1:])

  def test_get_coefficients_pos(self):
    for ielem in range(self.checknelems):
      self.assertEqual(self.basis.get_coefficients(ielem).tolist(), self.checkcoeffs[ielem])

  def test_get_coefficients_neg(self):
    for ielem in range(-self.checknelems, 0):
      self.assertEqual(self.basis.get_coefficients(ielem).tolist(), self.checkcoeffs[ielem])

  def test_get_coefficients_outofbounds(self):
    with self.assertRaises(IndexError):
      self.basis.get_coefficients(-self.checknelems-1)
    with self.assertRaises(IndexError):
      self.basis.get_coefficients(self.checknelems)

  def test_get_dofs_scalar_pos(self):
    for ielem in range(self.checknelems):
      self.assertEqual(self.basis.get_dofs(ielem).tolist(), self.checkdofs[ielem])

  def test_get_dofs_scalar_neg(self):
    for ielem in range(-self.checknelems, 0):
      self.assertEqual(self.basis.get_dofs(ielem).tolist(), self.checkdofs[ielem])

  def test_get_dofs_scalar_outofbounds(self):
    with self.assertRaises(IndexError):
      self.basis.get_dofs(-self.checknelems-1)
    with self.assertRaises(IndexError):
      self.basis.get_dofs(self.checknelems)

  def test_get_ndofs(self):
    for ielem in range(self.checknelems):
      self.assertEqual(self.basis.get_ndofs(ielem), len(self.checkdofs[ielem]))

  def test_dofs_array(self):
    for mask in itertools.product(*[[False, True]]*self.checknelems):
      mask = numpy.array(mask, dtype=bool)
      indices, = numpy.where(mask)
      for value in mask, indices:
        with self.subTest(tuple(value)):
          self.assertEqual(self.basis.get_dofs(value).tolist(), list(sorted(set(itertools.chain.from_iterable(self.checkdofs[i] for i in indices)))))

  def test_dofs_intarray_outofbounds(self):
    for i in [-1, self.checknelems]:
      with self.assertRaises(IndexError):
        self.basis.get_dofs(numpy.array([i], dtype=int))

  def test_dofs_intarray_invalidndim(self):
    with self.assertRaises(IndexError):
      self.basis.get_dofs(numpy.array([[0]], dtype=int))

  def test_dofs_boolarray_invalidshape(self):
    with self.assertRaises(IndexError):
      self.basis.get_dofs(numpy.array([True]*(self.checknelems+1), dtype=bool))
    with self.assertRaises(IndexError):
      self.basis.get_dofs(numpy.array([[True]*self.checknelems], dtype=bool))

  def test_get_support_scalar_pos(self):
    for dof in range(self.checkndofs):
      self.assertEqual(self.basis.get_support(dof).tolist(), self.checksupp[dof])

  def test_get_support_scalar_neg(self):
    for dof in range(-self.checkndofs, 0):
      self.assertEqual(self.basis.get_support(dof).tolist(), self.checksupp[dof])

  def test_get_support_scalar_outofbounds(self):
    with self.assertRaises(IndexError):
      self.basis.get_support(-self.checkndofs-1)
    with self.assertRaises(IndexError):
      self.basis.get_support(self.checkndofs)

  def test_get_support_array(self):
    for mask in itertools.product(*[[False, True]]*self.checkndofs):
      mask = numpy.array(mask, dtype=bool)
      indices, = numpy.where(mask)
      for value in mask, indices:
        with self.subTest(tuple(value)):
          self.assertEqual(self.basis.get_support(value).tolist(), list(sorted(set(itertools.chain.from_iterable(self.checksupp[i] for i in indices)))))

  def test_get_support_intarray_outofbounds(self):
    for i in [-1, self.checkndofs]:
      with self.assertRaises(IndexError):
        self.basis.get_support(numpy.array([i], dtype=int))

  def test_get_support_intarray_invalidndim(self):
    with self.assertRaises(IndexError):
      self.basis.get_support(numpy.array([[0]], dtype=int))

  def test_get_support_boolarray(self):
    for mask in itertools.product(*[[False, True]]*self.checkndofs):
      mask = numpy.array(mask, dtype=bool)
      indices, = numpy.where(mask)
      with self.subTest(tuple(indices)):
        self.assertEqual(self.basis.get_support(mask).tolist(), list(sorted(set(itertools.chain.from_iterable(self.checksupp[i] for i in indices)))))

  def test_get_support_boolarray_invalidshape(self):
    with self.assertRaises(IndexError):
      self.basis.get_support(numpy.array([True]*(self.checkndofs+1), dtype=bool))
    with self.assertRaises(IndexError):
      self.basis.get_support(numpy.array([[True]*self.checkndofs], dtype=bool))

  def test_getitem_array(self):
    for mask in itertools.product(*[[False, True]]*self.checkndofs):
      mask = numpy.array(mask, dtype=bool)
      indices, = numpy.where(mask)
      for value in mask, indices:
        with self.subTest(tuple(value)):
          maskedbasis = self.basis[value]
          self.assertIsInstance(maskedbasis, function.Basis)
          for ielem in range(self.checknelems):
            m = numpy.asarray(numeric.sorted_contains(indices, self.checkdofs[ielem]))
            self.assertEqual(maskedbasis.get_dofs(ielem).tolist(), numeric.sorted_index(indices, numpy.compress(m, self.checkdofs[ielem], axis=0)).tolist())
            self.assertEqual(maskedbasis.get_coefficients(ielem).tolist(), numpy.compress(m, self.checkcoeffs[ielem], axis=0).tolist())

  def checkeval(self, ielem, points):
    result = numpy.zeros((points.shape[0], self.checkndofs,), dtype=float)
    numpy.add.at(result, (slice(None),numpy.array(self.checkdofs[ielem], dtype=int)), numeric.poly_eval(numpy.array(self.checkcoeffs[ielem], dtype=float)[None], points))
    return result.tolist()

  def test_evalf(self):
    ref = element.PointReference() if self.basis.coords.shape[0] == 0 else element.LineReference()**self.basis.coords.shape[0]
    points = ref.getpoints('bezier', 4).coords
    with self.assertWarnsRegex(evaluable.ExpensiveEvaluationWarning, 'using explicit basis evaluation.*'):
      for ielem in range(self.checknelems):
        self.assertEqual(self.basis.evalf([ielem], points).tolist(), self.checkeval(ielem, points))

  def test_simplified(self):
    ref = element.PointReference() if self.basis.coords.shape[0] == 0 else element.LineReference()**self.basis.coords.shape[0]
    points = ref.getpoints('bezier', 4).coords
    simplified = self.basis.simplified
    with _builtin_warnings.catch_warnings():
      _builtin_warnings.simplefilter('ignore', category=evaluable.ExpensiveEvaluationWarning)
      for ielem in range(self.checknelems):
        value = simplified.prepare_eval().eval(_transforms=(self.checktransforms[ielem],), _points=points)
        if value.shape[0] == 1:
          value = numpy.tile(value, (points.shape[0], 1))
        self.assertEqual(value.tolist(), self.checkeval(ielem, points))

  def test_f_ndofs(self):
    for ielem in range(self.checknelems):
      a = self.basis.get_ndofs(ielem)
      b, = self.basis.f_ndofs(ielem).eval()
      self.assertEqual(a, b)

  def test_f_dofs(self):
    for ielem in range(self.checknelems):
      a = self.basis.get_dofs(ielem)
      b, = self.basis.f_dofs(ielem).eval()
      self.assertAllEqual(a, b)

  def test_f_coefficients(self):
    for ielem in range(self.checknelems):
      a = self.basis.get_coefficients(ielem)
      b, = self.basis.f_coefficients(ielem).eval()
      self.assertAllEqual(a, b)

class PlainBasis(CommonBasis, TestCase):

  def setUp(self):
    self.checktransforms = transformseq.PlainTransforms([(transform.Identifier(0,k),) for k in 'abcd'], 0)
    index, coords = self.mk_index_coords(0, self.checktransforms)
    self.checkcoeffs = [[1],[2,3],[4,5],[6]]
    self.checkdofs = [[0],[2,3],[1,3],[2]]
    self.basis = function.PlainBasis(self.checkcoeffs, self.checkdofs, 4, index, coords)
    self.checkndofs = 4
    super().setUp()

class DiscontBasis(CommonBasis, TestCase):

  def setUp(self):
    self.checktransforms = transformseq.PlainTransforms([(transform.Identifier(0,k),) for k in 'abcd'], 0)
    index, coords = self.mk_index_coords(0, self.checktransforms)
    self.checkcoeffs = [[1],[2,3],[4,5],[6]]
    self.basis = function.DiscontBasis(self.checkcoeffs, index, coords)
    self.checkdofs = [[0],[1,2],[3,4],[5]]
    self.checkndofs = 6
    super().setUp()

class MaskedBasis(CommonBasis, TestCase):

  def setUp(self):
    self.checktransforms = transformseq.PlainTransforms([(transform.Identifier(0,k),) for k in 'abcd'], 0)
    index, coords = self.mk_index_coords(0, self.checktransforms)
    parent = function.PlainBasis([[1],[2,3],[4,5],[6]], [[0],[2,3],[1,3],[2]], 4, index, coords)
    self.basis = function.MaskedBasis(parent, [0,2])
    self.checkcoeffs = [[1],[2],[],[6]]
    self.checkdofs = [[0],[1],[],[1]]
    self.checkndofs = 2
    super().setUp()

class PrunedBasis(CommonBasis, TestCase):

  def setUp(self):
    parent_transforms = transformseq.PlainTransforms([(transform.Identifier(0,k),) for k in 'abcd'], 0)
    parent_index, parent_coords = self.mk_index_coords(0, parent_transforms)
    indices = types.frozenarray([0,2])
    self.checktransforms = parent_transforms[indices]
    index, coords = self.mk_index_coords(0, self.checktransforms)
    parent = function.PlainBasis([[1],[2,3],[4,5],[6]], [[0],[2,3],[1,3],[2]], 4, parent_index, parent_coords)
    self.basis = function.PrunedBasis(parent, indices, index, coords)
    self.checkcoeffs = [[1],[4,5]]
    self.checkdofs = [[0],[1,2]]
    self.checkndofs = 3
    super().setUp()

class StructuredBasis1D(CommonBasis, TestCase):

  def setUp(self):
    self.checktransforms = transformseq.StructuredTransforms(transform.Identifier(1, 'test'), [transformseq.DimAxis(0,4,False)], 0)
    index, coords = self.mk_index_coords(1, self.checktransforms)
    self.basis = function.StructuredBasis([[[[1],[2]],[[3],[4]],[[5],[6]],[[7],[8]]]], [[0,1,2,3]], [[2,3,4,5]], [5], [4], index, coords)
    self.checkcoeffs = [[[1],[2]],[[3],[4]],[[5],[6]],[[7],[8]]]
    self.checkdofs = [[0,1],[1,2],[2,3],[3,4]]
    self.checkndofs = 5
    super().setUp()

class StructuredBasis1DPeriodic(CommonBasis, TestCase):

  def setUp(self):
    self.checktransforms = transformseq.StructuredTransforms(transform.Identifier(1, 'test'), [transformseq.DimAxis(0,4,True)], 0)
    index, coords = self.mk_index_coords(1, self.checktransforms)
    self.basis = function.StructuredBasis([[[[1],[2]],[[3],[4]],[[5],[6]],[[7],[8]]]], [[0,1,2,3]], [[2,3,4,5]], [4], [4], index, coords)
    self.checkcoeffs = [[[1],[2]],[[3],[4]],[[5],[6]],[[7],[8]]]
    self.checkdofs = [[0,1],[1,2],[2,3],[3,0]]
    self.checkndofs = 4
    super().setUp()

class StructuredBasis2D(CommonBasis, TestCase):

  def setUp(self):
    self.checktransforms = transformseq.StructuredTransforms(transform.Identifier(2, 'test'), [transformseq.DimAxis(0,2,False),transformseq.DimAxis(0,2,False)], 0)
    index, coords = self.mk_index_coords(2, self.checktransforms)
    self.basis = function.StructuredBasis([[[[1],[2]],[[3],[4]]],[[[5],[6]],[[7],[8]]]], [[0,1],[0,1]], [[2,3],[2,3]], [3,3], [2,2], index, coords)
    self.checkcoeffs = [[[[5]],[[6]],[[10]],[[12]]],[[[7]],[[8]],[[14]],[[16]]],[[[15]],[[18]],[[20]],[[24]]],[[[21]],[[24]],[[28]],[[32]]]]
    self.checkdofs = [[0,1,3,4],[1,2,4,5],[3,4,6,7],[4,5,7,8]]
    self.checkndofs = 9
    super().setUp()
