from nutils import *
from . import register, unittest

@register( 'point', [0], numpy.zeros((0,)) )
@register( 'line', [1], [.5] )
@register( 'triangle', [2], [1/3]*2 )
@register( 'tetrahedron', [3], [1/4]*3 )
@register( 'square', [1,1], [.5]*2 )
@register( 'hexagon', [1,1,1], [.5]*3 )
@register( 'prism1', [2,1], [1/3,1/3,1/2] )
@register( 'prism2', [1,2], [1/2,1/3,1/3] )
def elem( ndims, exactcentroid ):

  ref = element.getsimplex( ndims[0] )
  for ndim in ndims[1:]:
    ref *= element.getsimplex( ndim )
  assert ref.ndims == sum(ndims)

  @unittest
  def centroid():
    numpy.testing.assert_almost_equal(ref.centroid, exactcentroid, decimal=15)

  if ref.ndims >= 1 and not isinstance( ref, element.TetrahedronReference ):
    @unittest
    def children():
      childvol = sum( abs(trans.det) * child.volume for trans, child in ref.children )
      numpy.testing.assert_almost_equal( childvol, ref.volume )

  if ref.ndims >= 2:
    @unittest
    def ribbons():
      ref.ribbons
