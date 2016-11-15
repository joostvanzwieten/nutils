# -*- coding: utf8 -*-
#
# Module PARALLEL
#
# Part of Nutils: open source numerical utilities for Python. Jointly developed
# by HvZ Computational Engineering, TU/e Multiscale Engineering Fluid Dynamics,
# and others. More info at http://nutils.org <info@nutils.org>. (c) 2014

"""
The parallel module provides tools aimed at parallel computing. At this point
all parallel solutions use the ``fork`` system call and are supported on limited
platforms, notably excluding Windows. On unsupported platforms parallel features
will disable and a warning is printed.
"""

from __future__ import print_function, division
from . import core, log, numpy, debug, numeric
import os, sys, multiprocessing, tempfile, mmap

procid = None # current process id, None for unforked

class Fork( object ):
  'nested fork context, unwinds at exit'

  def __init__( self, nprocs ):
    'constructor'

    self.nprocs = nprocs

  def __enter__( self ):
    'fork and return iproc'

    global procid
    if procid is not None:
      self.child_pid = None
      log.warning( 'ignoring fork for already forked process' )
      return None
    for procid in range( self.nprocs-1 ):
      self.child_pid = os.fork()
      if self.child_pid:
        break
    else:
      self.child_pid = 0
      procid = self.nprocs-1
    return procid

  def __exit__( self, exctype, excvalue, tb ):
    'kill all processes but first one'

    if self.child_pid is None: # not forked
      return
    global procid
    status = 0
    try:
      if exctype == KeyboardInterrupt:
        status = 1
      elif exctype == GeneratorExit:
        if procid:
          log.error( 'generator failed with unknown exception' )
        status = 1
      elif exctype:
        if procid:
          log.stack( repr(excvalue), debug.frames_from_traceback(tb) )
        status = 1
      if self.child_pid:
        child_pid, child_status = os.waitpid( self.child_pid, 0 )
        if child_pid != self.child_pid:
          log.error( 'pid failure! got %s, was waiting for %s' % (child_pid,self.child_pid) )
          status = 1
        elif child_status:
          status = 1
    except: # should not happen.. but just to be sure
      status = 1
    if procid:
      os._exit( status )
    procid = None
    if not exctype:
      assert status == 0, 'one or more subprocesses failed'

class AlternativeFork( object ):
  'single master, multiple slave fork context, unwinds at exit'

  def __init__( self, nprocs ):
    'constructor'

    self.nprocs = nprocs
    self.children = None

  def __enter__( self ):
    'fork and return iproc'

    global procid
    if procid is not None:
      log.warning( 'ignoring fork for already forked process' )
      return None
    children = []
    for procid in range( 1, self.nprocs ):
      child_pid = os.fork()
      if not child_pid:
        break
      children.append( child_pid )
    else:
      self.children = children
      procid = 0
    return procid

  def __exit__( self, exctype, excvalue, tb ):
    'kill all processes but first one'

    global procid
    status = 0
    try:
      if exctype:
        log.stack( repr(excvalue), debug.frames_from_traceback(tb) )
        status = 1
      while self.children:
        child_pid, child_status = os.wait()
        self.children.remove( child_pid )
        if child_status:
          status = 1
    except: # should not happen.. but just to be sure
      status = 1
    if procid:
      os._exit( status )
    procid = None
    if not exctype:
      assert status == 0, 'one or more subprocesses failed'

def waitpid_noerr( pid ):
  try:
    os.waitpid( pid, 0 )
  except:
    pass

def fork( func, nice=19 ):
  'fork and run (return value is lost)'

  if not hasattr( os, 'fork' ):
    log.warning( 'fork does not exist on this platform; running %s in serial' % func.__name__ )
    return func

  import thread
  def wrapped( *args, **kwargs ):
    pid = os.fork()
    if pid:
      thread.start_new_thread( waitpid_noerr, (pid,) ) # kill the zombies
      # see: http://stackoverflow.com/a/13331632/445031
      # this didn't work: http://stackoverflow.com/a/6718735/445031
      return pid
    try:
      os.nice( nice )
      func( *args, **kwargs )
    except KeyboardInterrupt:
      pass
    except:
      exc, frames = debug.exc_info()
      log.stack( repr(exc), frames )
    finally:
      os._exit( 0 )

  return wrapped

def shzeros( shape, dtype=float ):
  'create zero-initialized array in shared memory'

  nprocs = core.getprop( 'nprocs', 1 )
  if nprocs == 1:
    return numpy.zeros( shape, dtype=dtype ) # TODO: toggle to numpy for debugging

  if numeric.isint( shape ):
    shape = shape,
  else:
    assert all( numeric.isint(sh) for sh in shape )
  dtype = numpy.dtype( dtype )
  size = ( numpy.product( shape ) if shape else 1 ) * dtype.itemsize
  if size == 0:
    return numpy.zeros( shape, dtype )
  fd, name = tempfile.mkstemp( dir=core.getprop( 'shmdir', default=None ) )
  try:
    os.unlink(name)
    # Make sure the entire file is allocated by writing zeros.  If we omit
    # this, writing to the mmap array will cause the process to be killed with
    # SIGBUS if there is no memory available.
    with open( fd, 'wb', closefd=False ) as f:
      bs = 1024 * 1024
      if size >= bs:
        zeros = b'\0' * bs
        for i in range( size // bs ):
          f.write( zeros )
        del zeros
      f.write( b'\0' * (size % bs) )
      assert f.tell() == size
    buf = mmap.mmap( fd, size )
  finally:
    os.close(fd)
  array = numpy.frombuffer( buf, dtype ).reshape( shape )
  assert array.ravel()[0] == 0, '{!r} is not interpreted as 0 ({})'.format(b'\x00'*dtype.itemsize, dtype)
  return array

def pariter( iterable ):
  'iterate parallel'

  nprocs = core.getprop( 'nprocs', 1 )
  return iterable if nprocs <= 1 else _pariter( iterable, nprocs )

def _pariter( iterable, nprocs ):
  'iterate parallel, helper generator'

  shared_iter = multiprocessing.RawValue( 'i', nprocs )
  lock = multiprocessing.Lock()
  with Fork( nprocs ):
    iiter = procid
    for n, it in enumerate( iterable ):
      if n < iiter:
        continue
      assert n == iiter
      yield it
      with lock:
        iiter = shared_iter.value
        shared_iter.value = iiter + 1

def parmap( func, iterable, shape=(), dtype=float ):
  n = len(iterable)
  out = shzeros( (n,)+shape, dtype=dtype )
  for i, item in pariter( enumerate(iterable) ):
    out[i] = func( item )
  return out

# vim:shiftwidth=2:softtabstop=2:expandtab:foldmethod=indent:foldnestmax=1
