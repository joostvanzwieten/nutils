# -*- coding: utf8 -*-
#
# Module MESH
#
# Part of Nutils: open source numerical utilities for Python. Jointly developed
# by HvZ Computational Engineering, TU/e Multiscale Engineering Fluid Dynamics,
# and others. More info at http://nutils.org <info@nutils.org>. (c) 2014

"""
The mesh module provides mesh generators: methods that return a topology and an
accompanying geometry function. Meshes can either be generated on the fly, e.g.
:func:`rectilinear`, or read from external an externally prepared file,
:func:`gmesh`, :func:`igatool`, and converted to nutils format. Note that no
mesh writers are provided at this point; output is handled by the
:mod:`nutils.plot` module.
"""

from __future__ import print_function, division
from . import topology, function, util, element, numpy, numeric, transform, log, _
import os, warnings, itertools

# MESH GENERATORS

def rectilinear( richshape, periodic=(), name='rect', revolved=False ):
  'rectilinear mesh'

  ndims = len(richshape)
  shape = []
  offset = []
  scale = []
  uniform = True
  for v in richshape:
    if isinstance( v, int ):
      assert v > 0
      shape.append( v )
      scale.append( 1 )
      offset.append( 0 )
    elif numpy.equal( v, numpy.linspace(v[0],v[-1],len(v)) ).all():
      shape.append( len(v)-1 )
      scale.append( (v[-1]-v[0]) / float(len(v)-1) )
      offset.append( v[0] )
    else:
      shape.append( len(v)-1 )
      uniform = False
  indices = numeric.grid( shape )
  structure = numpy.empty( indices.shape[1:], dtype=object )

  if isinstance( name, str ):
    wrap = tuple( sh if i in periodic else 0 for i, sh in enumerate(shape) )
    root = transform.roottrans( name, wrap )
  else:
    assert all( ( name.take(0,i) == name.take(2,i) ).all() for i in periodic )
    root = transform.roottransedges( name, shape )

  reference = element.getsimplex(1)**ndims
  for index in indices.reshape( ndims, -1 ).T:
    structure[tuple(index)] = element.Element( reference, root << transform.affine(0,index) )
  topo = topology.StructuredTopology( structure, periodic=periodic )
  if uniform:
    if all( o == offset[0] for o in offset[1:] ):
      offset = offset[0]
    if all( s == scale[0] for s in scale[1:] ):
      scale = scale[0]
    geom = function.ElemFunc( ndims ) * scale + offset
  else:
    funcsp = topo.splinefunc( degree=1, periodic=() )
    coords = numeric.meshgrid( *richshape ).reshape( ndims, -1 )
    geom = ( funcsp * coords ).sum( -1 )

  if revolved:
    topo = topology.RevolvedTopology(topo)
    theta = function.RevolutionAngle()
    if topo.ndims == 1:
      r, = function.revolved(geom)
      geom = r * function.stack([ function.cos(theta), function.sin(theta) ])
    elif topo.ndims == 2:
      r, y = function.revolved(geom)
      geom = function.stack([ r * function.cos(theta), y, r * function.sin(theta) ])
    else:
      raise NotImplementedError( 'ndims={}'.format( topo.ndims ) )

  return topo, geom

def multipatch( patches, elems, patchverts=None, name='multipatch' ):
  '''multipatch rectilinear mesh generator

  Multipatch sphere example:

      # structure:
      #
      #   3----7
      #  /|   /|
      # 2----6 |     y
      # | |  | |     |
      # | 1--|-5     | z
      # |/   |/      |/
      # 0----4       *----x

      topo, cube = multipatch(
        patches=[
          # the order of the vertices is chosen such that normals point outward
          [2,3,0,1],
          [4,5,6,7],
          [4,6,0,2],
          [1,3,5,7],
          [1,5,0,4],
          [2,6,3,7],
        ],
        patchverts=tuple(itertools.product(*([[-1,1]]*3))),
        elems=10,
      )
      sphere = cube/function.sqrt((cube**2).sum(0))
  '''

  patches = numpy.array( patches )
  if patches.dtype != int:
    raise ValueError( '`patches` should be an array of ints.' )
  if len( patches.shape ) != 2:
    raise ValueError( '`patches` should be an array with two axes (patches, patch vertices).' )

  # determine topological dimension of patches

  ndims = 0
  while 2**ndims < patches.shape[1]:
    ndims += 1
  if 2**ndims > patches.shape[1]:
    raise ValueError( 'Only hyperrectangular patches are supported: ' \
      'number of patch vertices should be a power of two.' )

  # group all common patch edges (and/or boundaries?)

  if not isinstance( elems, int ):
    raise NotImplementedError

  # create patch topologies, geometries

  if patchverts is not None:
    patchverts = numpy.array( patchverts )
    indices = set( patches.flat )
    if tuple( sorted( indices ) ) != tuple( range( len( indices ) ) ):
      raise ValueError( 'Patch vertices in `patches` should be numbered consecutively, starting at 0.' )
    if len( patchverts ) != len( indices ):
      raise ValueError( 'Number of `patchverts` does not equal number of vertices specified in `patches`.' )
    if len( patchverts.shape ) != 2:
      raise ValueError( 'Every patch vertex should be an array of dimension 1.' )

  topos = []
  coords = []
  for i, patch in enumerate( patches ):
    # find shape of patch and local patch coordinates
    if isinstance( elems, int ):
      shape = [ elems ] * ndims
      if patchverts is None:
        patchcoords = [ numpy.arange(elems+1) ] * ndims
      else:
        patchcoords = [ numpy.linspace(0, 1, elems+1) ] * ndims
    else:
      raise NotImplementedError
    # create patch topology
    topos.append( rectilinear( shape, name='{}{}'.format(name, i) )[0] )
    # compute patch geometry
    patchcoords = numeric.meshgrid( *patchcoords ).reshape( ndims, -1 )
    if patchverts is not None:
      patchcoords = numpy.array([
        sum(
          patchverts[j]*util.product(c if s else 1-c for c, s in zip(coord, side))
          for j, side in zip(patch, itertools.product(*[[0,1]]*ndims))
        )
        for coord in patchcoords.T
      ]).T
    coords.append( patchcoords )

  # build patch boundary data

  boundarydata = topology.MultipatchTopology.build_boundarydata( patch.reshape( (2,)*ndims ) for patch in patches )

  # join patch topologies, geometries

  topo = topology.MultipatchTopology( zip( topos, boundarydata ) )
  funcsp = topo.splinefunc( degree=1, patchcontinuous=False )
  geom = ( funcsp * numpy.concatenate( coords, axis=1 ) ).sum( -1 )

  return topo, geom

def gmesh( fname, tags={}, name=None, use_elementary=False ):
  """Gmesh parser

  Parser for Gmesh files in `.msh` format. See the `Gmesh manual <http://geuz.org/gmsh/doc/texinfo/gmsh.html>`_ for details.

  Args:
      fname (str): Path to mesh file
      tags (dict, optional): Dictionary mapping gmesh group IDs to names
      name (str, optional): Name of parsed topology, defaults to None
      use_elementary (bool, optional): Option to indicate whether Gmsh is used with elementary groups only (i.e. no physical groups are defined), defaults to False

  Returns:
      topo (:class:`nutils.topology.Topology`): Topology of parsed Gmesh file
      geom (:class:`nutils.function.ArrayFunc`): Isoparametric map

  """

  if isinstance( tags, str ):
    warnings.warn('String format for groups is depricated, please use dictionary format instead with (key,value)=(physical ID,group name)',DeprecationWarning)
    tags = { i+1: tag for i, tag in enumerate( tags.split(',') ) }

  #Parse the file
  sections = {}
  lines = iter(open(fname,'r') if isinstance(fname,str) else fname)
  for line in lines:
    line = line.strip()
    assert line[0]=='$'
    sname = line[1:]
    slines = []
    for sline in lines:
      sline = sline.strip()
      if sline=='$End%s'%sname:
        break
      slines.append( sline ) 
    sections[sname] = slines  

  #PhysicalNames
  names = sections.pop( 'PhysicalNames', [0] )
  assert int(names.pop(0)) == len(names)
  for line in names:
    words = line.split()
    nid = int(words[1])
    name = words[2].strip( '"' )
    if nid not in tags:
      tags[nid] = name
    else:
      warnings.warn( 'renamed physical group name {!r} to {!r}'.format( name, tags[nid] ) )
        
  #Nodes
  nodedata = sections.pop('Nodes')
  nnodes = int(nodedata.pop(0))
  assert len(nodedata)==nnodes
        
  coords = numpy.empty((nnodes,3))
  coords[:] = numpy.nan
  nidmap = {}
  for line in nodedata:
    words = line.split()
    nid = len(nidmap)
    nidmap[int(words[0])] = nid
    coords[nid] = [ float(n) for n in words[1:] ]
  assert not numpy.isnan(coords).any()
  assert numpy.all( coords[:,2] ) == 0, 'ndims=3 case not yet implemented.'
  coords = coords[:,:2]

  #Elements
  elemdata = sections.pop('Elements')
  nelems = int(elemdata.pop(0))
  assert len(elemdata)==nelems
  flip = transform.affine( -1, [1] )

  elems = {}
  elemgroups = {}
  edges = {}
  ifaces = {}
  vertexgroups = {}
  vertices = {}
  edgegroups = {}
  fmap = {}
  nmap = {}
  for line in elemdata:
    words = line.split()
    etype = int(words[1])
    ntags = int(words[2])
    if use_elementary:
      assert words[3] == '0', 'option use_elementary=True conflicts with non-zero physical tag'
      tag = tags.get( int( words[4] ), 'elementary' + words[4] )
    else:
      tag = tags.get( int( words[3] ), 'physical' + words[3] )

    nids = numpy.array([ nidmap[int(gmshid)] for gmshid in words[3+ntags:] ])
    elemkey = tuple(sorted(nids))
    if etype == 1: # Linear line
      edgegroups.setdefault(tag,[]).append(elemkey)
    elif etype == 2: # linear triangle
      assert len(nids)==3
      try:
        elem = elems[elemkey]
      except KeyError:
        elemcoords = coords[nids]
        if numpy.linalg.det( elemcoords[:2] - elemcoords[2] ) < 0:
          nids[:2] = nids[1], nids[0]
        ref = element.getsimplex(2)
        maptrans = transform.maptrans(ref.vertices,nids if not name else [name+str(nid) for nid in nids])
        elem = element.Element(ref,maptrans)
        elems[elemkey] = elem
        fmap[maptrans] = (ref.stdfunc(1),None),
        nmap[maptrans] = nids

        #Extract the edges
        for iedge, iverts in enumerate([[1,2],[0,2],[0,1]]):
          edge = elem.edge(iedge)
          key = tuple(sorted(nids[iverts]))
          try:
            opposite = edges.pop( key )
          except KeyError:
            edges[key] = edge
          else:
            assert edge.reference == opposite.reference
            iface = element.Element( edge.reference, edge.transform, opposite.transform << flip )
            #assert iface.transform.apply( iface.reference.vertices ) == iface.opposite.apply( iface.reference.vertices )
            ifaces[key] = iface

        #Extract the vertices
        vref = element.getsimplex(0)
        for ivertex in range(3): #GMSH and Nutils node ordering coincide
          zeroD_to_twoD = transform.affine( linear=numpy.zeros(shape=(2,0),dtype=int), offset=ref.vertices[ivertex], isflipped=False )
          vmaptrans = maptrans << zeroD_to_twoD
          vertexkey = (nids[ivertex],)
          velem = element.Element(vref,vmaptrans)
          vertices.setdefault(vertexkey,[]).append(velem)

      elemgroups.setdefault(tag,[]).append(elem)
    elif etype == 15:
      if not use_elementary:
        vertexgroups.setdefault(tag,[]).append(elemkey)
    else:
      raise NotImplementedError('Unknown GMSH element type %i' % etype)

  topo = topology.Topology( elems.values() )
  for group, grouptopo in elemgroups.items():
    topo[group] = topology.Topology( grouptopo )

  topo.boundary = topology.Topology( edges.values() )
  topo.interfaces = topology.Topology( ifaces.values() )
  for group, keys in edgegroups.items():
    bgrouptopo = []
    igrouptopo = []
    for key in keys:
      try:
        bgrouptopo.append( edges[key] )
      except KeyError:
        igrouptopo.append( ifaces[key] )
    if bgrouptopo:
      topo.boundary[group] = topology.Topology( bgrouptopo )
    if igrouptopo:
      topo.interfaces[group] = topology.Topology( igrouptopo )

  topo.points = topology.Topology( [vertex for vertexkeys in vertexgroups.values() for vertexkey in vertexkeys for vertex in vertices[vertexkey]], ndims=0 )
  for group, vertexkeys in vertexgroups.items():
    topo.points[group] = topology.Topology([vertex for vertexkey in vertexkeys for vertex in vertices[vertexkey]])

  for tag in tags.values():
    if tag not in topo.groupnames and \
       tag not in topo.boundary.groupnames and \
       tag not in topo.interfaces.groupnames and \
       tag not in topo.points.groupnames:

      warnings.warn('tag %r defined but not used' % tag )

  log.info('parsed GMSH file:')
  log.info('* nodes (#%d)' % nnodes)
  log.info('* topology (#%d) with groups: %s' % (len(topo), ', '.join('%s (#%d)' % (name,len(topo[name])) for name in topo.groupnames)))
  log.info('* boundary (#%d) with groups: %s' % (len(topo.boundary), ', '.join('%s (#%d)' % (name,len(topo.boundary[name])) for name in topo.boundary.groupnames)))
  log.info('* interfaces (#%d) with groups: %s' % (len(topo.interfaces), ', '.join('%s (#%d)' % (name,len(topo.interfaces[name])) for name in topo.interfaces.groupnames)))
  log.info('* points (#%d) with groups: %s' % (len(topo.points), ', '.join('%s (#%d)' % (name,len(topo.points[name])) for name in topo.points.groupnames)))

  linearfunc = function.function( fmap=fmap, nmap=nmap, ndofs=nnodes, ndims=topo.ndims )
  geom = ( linearfunc[:,_] * coords ).sum(0)
  return topo, geom

def triangulation( vertices, nvertices ):
  'triangulation'

  raise NotImplementedError

  bedges = {}
  nmap = {}
  I = numpy.array( [[2,0],[0,1],[1,2]] )
  for n123 in vertices:
    elem = element.getsimplex(2)
    nmap[ elem ] = n123
    for iedge, (n1,n2) in enumerate( n123[I] ):
      try:
        del bedges[ (n2,n1) ]
      except KeyError:
        bedges[ (n1,n2) ] = elem, iedge

  dofaxis = function.DofAxis( nvertices, nmap )
  stdelem = element.PolyTriangle( 1 )
  linearfunc = function.Function( dofaxis=dofaxis, stdmap=dict.fromkeys(nmap,stdelem) )

  connectivity = dict( bedges.iterkeys() )
  N = list( connectivity.popitem() )
  while connectivity:
    N.append( connectivity.pop( N[-1] ) )
  assert N[0] == N[-1]

  structure = []
  for n12 in zip( N[:-1], N[1:] ):
    elem, iedge = bedges[ n12 ]
    structure.append( elem.edge( iedge ) )
    
  topo = topology.Topology( nmap )
  topo.boundary = topology.StructuredTopology( structure, periodic=(1,) )
  return topo

def igatool( path, name=None ):
  'igatool mesh'

  if name is None:
    name = os.path.basename(path)

  import vtk

  reader = vtk.vtkXMLUnstructuredGridReader()
  reader.SetFileName( path )
  reader.Update()

  mesh = reader.GetOutput()

  FieldData = mesh.GetFieldData()
  CellData = mesh.GetCellData()

  NumberOfPoints = int( mesh.GetNumberOfPoints() )
  NumberOfElements = mesh.GetNumberOfCells()
  NumberOfArrays = FieldData.GetNumberOfArrays()

  points = util.arraymap( mesh.GetPoint, float, range(NumberOfPoints) )
  Cij = FieldData.GetArray( 'Cij' )
  Cv = FieldData.GetArray( 'Cv' )
  Cindi = CellData.GetArray( 'Elem_extr_indi')

  elements = []
  degree = 3
  ndims = 2
  nmap = {}
  fmap = {}

  poly = element.PolyLine( element.PolyLine.bernstein_poly( degree ) )**ndims

  for ielem in range(NumberOfElements):

    cellpoints = vtk.vtkIdList()
    mesh.GetCellPoints( ielem, cellpoints )
    nids = util.arraymap( cellpoints.GetId, int, range(cellpoints.GetNumberOfIds()) )

    assert mesh.GetCellType(ielem) == vtk.VTK_HIGHER_ORDER_QUAD
    nb = (degree+1)**2
    assert len(nids) == nb

    n = range( *util.arraymap( Cindi.GetComponent, int, ielem, [0,1] ) )
    I = util.arraymap( Cij.GetComponent, int, n, 0 )
    J = util.arraymap( Cij.GetComponent, int, n, 1 )
    Ce = numpy.zeros(( nb, nb ))
    Ce[I,J] = util.arraymap( Cv.GetComponent, float, n, 0 )

    vertices = [ element.PrimaryVertex( '%s(%d:%d)' % (name,ielem,ivertex) ) for ivertex in range(2**ndims) ]
    elem = element.QuadElement( vertices=vertices, ndims=ndims )
    elements.append( elem )

    fmap[ elem ] = element.ExtractionWrapper( poly, Ce.T )
    nmap[ elem ] = nids

  splinefunc = function.function( fmap, nmap, NumberOfPoints, ndims )

  boundaries = {}
  elemgroups = {}
  vertexgroups = {}
  renumber   = (0,3,1,2)
  for iarray in range( NumberOfArrays ):
    name = FieldData.GetArrayName( iarray )
    index = name.find( '_group_' )
    if index == -1:
      continue
    grouptype = name[:index]
    groupname = name[index+7:]
    A = FieldData.GetArray( iarray )
    I = util.arraymap( A.GetComponent, int, range(A.GetSize()), 0 )
    if grouptype == 'edge':
      belements = [ elements[i//4].edge( renumber[i%4] ) for i in I ]
      boundaries[ groupname ] = topology.Topology( belements )
    elif grouptype == 'vertex':
      vertexgroups[ groupname ] = I
    elif grouptype == 'element':
      elemgroups[ groupname ] = topology.Topology( elements[i] for i in I )
    else:
      raise Exception( 'unknown group type: %r' % grouptype )

  topo = topology.Topology( elements )
  for groupname, grouptopo in elemgroups.items():
    topo[groupname] = grouptopo

  if boundaries:
    topo.boundary = topology.Topology( elem for topo in boundaries.values() for elem in topo )
    for groupname, grouptopo in boundaries.items():
      topo.boundary[groupname] = grouptopo

  for group in elemgroups.values():
    myboundaries = {}
    for name, boundary in boundaries.items():
      belems = [ belem for belem in boundary.elements if belem.parent[0] in group ]
      if belems:
        myboundaries[ name ] = topology.Topology( belems )
    if myboundaries:
      group.boundary = topology.Topology( elem for topo in myboundaries.values() for elem in topo )
      for groupname, grouptopo in myboundaries.items():
        group.boundary[groupname] = grouptopo

  funcsp = topo.splinefunc( degree=degree )
  coords = ( funcsp[:,_] * points ).sum( 0 )
  return topo, coords #, vertexgroups

def fromfunc( func, nelems, ndims, degree=1 ):
  'piecewise'

  if isinstance( nelems, int ):
    nelems = [ nelems ]
  assert len( nelems ) == func.__code__.co_argcount
  topo, ref = rectilinear( [ numpy.linspace(0,1,n+1) for n in nelems ] )
  funcsp = topo.splinefunc( degree=degree ).vector( ndims )
  coords = topo.projection( func, onto=funcsp, coords=ref, exact_boundaries=True )
  return topo, coords

def demo( xmin=0, xmax=1, ymin=0, ymax=1 ):
  'demo triangulation of a rectangle'

  phi = numpy.arange( 1.5, 13 ) * (2*numpy.pi) / 12
  P = numpy.array([ numpy.cos(phi), numpy.sin(phi) ])
  P /= abs(P).max(axis=0)
  phi = numpy.arange( 1, 9 ) * (2*numpy.pi) / 8
  Q = numpy.array([ numpy.cos(phi), numpy.sin(phi) ])
  Q /= 2 * numpy.sqrt( abs(Q).max(axis=0) / numpy.sqrt(2) )
  R = numpy.zeros([2,1])

  coords = numpy.round( numpy.hstack( [P,Q,R] ).T * 2**5 ) / 2**5

  vertices = numpy.array(
    [ [ 12+(i-i//3)%8, i, (i+1)%12 ] for i in range(12) ]
  + [ [ i+1+(i//2), 12+(i+1)%8, 12+i ] for i in range(8) ]
  + [ [ 20, 12+i, 12+(i+1)%8 ] for i in range(8) ] )
  
  root = transform.roottrans( 'demo', shape=(0,0) )
  reference = element.getsimplex(2)
  elements = [ element.Element( reference, root << transform.simplex(coords[iverts]) ) for iverts in vertices ]
  belems = [ elem.edge(0) for elem in elements[:12] ]
  bgroups = { 'top': belems[0:3], 'left': belems[3:6], 'bottom': belems[6:9], 'right': belems[9:12] }

  topo = topology.Topology( elements )
  topo.boundary = topology.Topology( belems )
  for tag, group in bgroups.items():
    topo.boundary[tag] = topology.Topology( group )

  geom = [.5*(xmin+xmax),.5*(ymin+ymax)] \
       + [.5*(xmax-xmin),.5*(ymax-ymin)] * function.ElemFunc( 2 )

  return topo, geom

# vim:shiftwidth=2:softtabstop=2:expandtab:foldmethod=indent:foldnestmax=1
