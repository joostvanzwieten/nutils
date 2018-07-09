import io, tempfile, os, contextlib
from . import *
import nutils.log, nutils.core, nutils.util, nutils.parallel

log_stdout = '''\
iterator > iter 0 (0%) > a
iterator > iter 1 (33%) > b
iterator > iter 2 (67%) > c
levels > error
levels > warning
levels > user
levels > info
forked > [1] error
forked > [1] warning
forked > [1] user
forked > [1] info
exception > ValueError('test',)
  File "??", line ??, in ??
    raise ValueError('test')
test.png
nonexistent.png
'''

log_stdout_short = '''\
iterator > iter 0 (0%) > a
iterator > iter 1 (33%) > b
iterator > iter 2 (67%) > c
levels > error
levels > warning
levels > user
levels > info
'''

log_stdout3 = '''\
levels > error
levels > warning
levels > user
forked > [1] error
forked > [1] warning
forked > [1] user
exception > ValueError('test',)
  File "??", line ??, in ??
    raise ValueError('test')
'''

log_rich_output = '''\
\033[K\033[1;30miterator\033[0m\r\
\033[K\033[1;30miterator · iter 0 (0%)\033[0m\r\
\033[K\033[1;30miterator · iter 0 (0%) · \033[0ma
\033[K\033[1;30miterator · iter 1 (33%)\033[0m\r\
\033[K\033[1;30miterator · iter 1 (33%) · \033[0mb
\033[K\033[1;30miterator · iter 2 (67%)\033[0m\r\
\033[K\033[1;30miterator · iter 2 (67%) · \033[0mc
\033[K\033[1;30miterator · iter 3 (100%)\033[0m\r\
\033[K\033[1;30mempty\033[0m\r\
\033[K\033[1;30mempty · empty\033[0m\r\
\033[K\033[1;30mlevels\033[0m\r\
\033[K\033[1;30mlevels · \033[1;31merror\033[0m
\033[K\033[1;30mlevels · \033[0;31mwarning\033[0m
\033[K\033[1;30mlevels · \033[0;33muser\033[0m
\033[K\033[1;30mlevels · \033[0minfo
\033[K\033[1;30mforked · \033[1;31m[1] error\033[0m
\033[K\033[1;30mforked · \033[0;31m[1] warning\033[0m
\033[K\033[1;30mforked · \033[0;33m[1] user\033[0m
\033[K\033[1;30mforked · \033[0m[1] info
\033[K\033[1;30mexception\033[0m\r\
\033[K\033[1;30mexception · \033[1;31mValueError(\'test\',)
  File "??", line ??, in ??
    raise ValueError(\'test\')\033[0m
\033[K\033[1;30m\033[0mtest.png
\033[K\033[1;30m\033[0mnonexistent.png
\033[K'''

log_html = '''\
"use strict"; const co = data => window.log._parse_line_co(data); const cc = data => window.log._parse_line_cc(data); const t0 = data => window.log._parse_line_t0(data); const t1 = data => window.log._parse_line_t1(data); const t2 = data => window.log._parse_line_t2(data); const t3 = data => window.log._parse_line_t3(data); const t4 = data => window.log._parse_line_t4(data); const a0 = data => window.log._parse_line_a0(data); const a1 = data => window.log._parse_line_a1(data); const a2 = data => window.log._parse_line_a2(data); const a3 = data => window.log._parse_line_a3(data); const a4 = data => window.log._parse_line_a4(data);
co("iterator")
co("iter 0 (0%)")
t3("a")
cc(null)
co("iter 1 (33%)")
t3("b")
cc(null)
co("iter 2 (67%)")
t3("c")
cc(null)
cc(null)
co("levels")
t0("error")
t1("warning")
t2("user")
t3("info")
cc(null)
co("exception")
t0("ValueError('test',)\\n  File \\"??\\", line ??, in ??\\n    raise ValueError('test')")
cc(null)
a3({"href": "test.png", "text": "test.png"})
t3("nonexistent.png")
'''

def generate_log(short=False):
  with nutils.log.context('iterator'):
    for i in nutils.log.iter('iter', 'abc'):
      nutils.log.info(i)
  with nutils.log.context('empty'):
    with nutils.log.context('empty'):
      pass
  with nutils.log.context('levels'):
    for level in ('error', 'warning', 'user', 'info'):
      getattr(nutils.log, level)(level)
  if short:
    return
  nutils.parallel.procid = 1
  with nutils.log.context('forked'):
    for level in ('error', 'warning', 'user', 'info'):
      getattr(nutils.log, level)(level)
  nutils.parallel.procid = None
  with nutils.log.context('exception'):
    nutils.log.error(
      "ValueError('test',)\n" \
      '  File "??", line ??, in ??\n' \
      "    raise ValueError('test')")
  with nutils.log.open('test.png', 'wb', level='info') as f:
    pass
  nutils.log.info('nonexistent.png')

@parametrize
class logoutput(ContextTestCase):

  def setUpContext(self, stack):
    super().setUpContext(stack)
    self.outdir = stack.enter_context(tempfile.TemporaryDirectory())
    stack.enter_context(nutils.config(
      verbose=self.verbose,
      progressinterval=-1, # make sure all progress information is written, regardless the speed of this computer
    ))

  def test(self):
    kwargs = dict(title='test') if self.logcls == nutils.log.HtmlLog else {}
    with contextlib.ExitStack() as stack:
      if issubclass(self.logcls, nutils.log.HtmlLog):
        with self.logcls(self.outdir, **kwargs):
          generate_log()
        with open(os.path.join(self.outdir, 'log.data')) as stream:
          value = stream.read()
      else:
        stream = io.StringIO()
        if self.replace_sys_stdout:
          stack.callback(setattr, sys, 'stdout', sys.stdout)
          sys.stdout = stream
        with self.logcls(stream, **kwargs):
          generate_log()
        value = stream.getvalue()
    self.assertEqual(value, self.logout)

_logoutput = lambda name, logcls, logout, verbose=len(nutils.log.LEVELS), replace_sys_stdout=False: logoutput(name, logcls=logcls, logout=logout, verbose=verbose, replace_sys_stdout=replace_sys_stdout)
_logoutput('stdout', nutils.log.StdoutLog, log_stdout)
_logoutput('stdout-replace-sys-stdout', nutils.log.StdoutLog, log_stdout, replace_sys_stdout=True)
_logoutput('stdout-verbose3', nutils.log.StdoutLog, log_stdout3, verbose=3)
_logoutput('rich_output', nutils.log.RichOutputLog, log_rich_output)
_logoutput('html', nutils.log.HtmlLog, log_html)

class tee_stdout_html(ContextTestCase):

  def setUpContext(self, stack):
    super().setUpContext(stack)
    self.outdir = stack.enter_context(tempfile.TemporaryDirectory())

  def test(self):
    stream_stdout = io.StringIO()
    with nutils.log.TeeLog(nutils.log.StdoutLog(stream_stdout), nutils.log.HtmlLog(self.outdir, title='test')):
      generate_log()
    self.assertEqual(stream_stdout.getvalue(), log_stdout)
    with open(os.path.join(self.outdir, 'log.data')) as stream_html:
      self.assertEqual(stream_html.read(), log_html)

class recordlog(ContextTestCase):

  def setUpContext(self, stack):
    super().setUpContext(stack)
    self.outdir = stack.enter_context(tempfile.TemporaryDirectory())
    stack.enter_context(nutils.config(
      outdir=self.outdir,
      verbose=len(nutils.log.LEVELS),
    ))

  def test(self):
    stream_passthrough_stdout = io.StringIO()
    with nutils.log.StdoutLog(stream_passthrough_stdout), nutils.log.RecordLog() as record:
      generate_log(short=True)
    with self.subTest('pass-through'):
      self.assertEqual(stream_passthrough_stdout.getvalue(), log_stdout_short)
    stream_replay_stdout = io.StringIO()
    with nutils.log.StdoutLog(stream_replay_stdout):
      record.replay()
    with self.subTest('replay'):
      self.assertEqual(stream_replay_stdout.getvalue(), log_stdout_short)

class html_post_mortem(ContextTestCase):

  def setUpContext(self, stack):
    super().setUpContext(stack)
    self.outdir = stack.enter_context(tempfile.TemporaryDirectory())

  def test(self):
    class TestException(Exception): pass

    virtual_module = dict(TestException=TestException)
    exec('''\
def generate_exception(level=0):
  if level == 1:
    raise TestException
  else:
    generate_exception(level+1)
''', virtual_module)
    with self.assertRaises(TestException):
      with nutils.log.HtmlLog(self.outdir, title='test'):
        virtual_module['generate_exception']()
    with open(os.path.join(self.outdir, 'log.data')) as stream:
      self.assertIn('EXHAUSTIVE STACK TRACE', stream.read())

class move_outdir(ContextTestCase):

  def setUpContext(self, stack):
    super().setUpContext(stack)
    tmpdir = stack.enter_context(tempfile.TemporaryDirectory())
    self.outdira = os.path.join(tmpdir, 'a')
    self.outdirb = os.path.join(tmpdir, 'b')

  @unittest.skipIf(not nutils.util.supports_outdirfd, 'outdirfd is not supported on this platform')
  def test(self):
    with nutils.log.HtmlLog(self.outdira, title='test'):
      os.rename(self.outdira, self.outdirb)
      generate_log()
    with open(os.path.join(self.outdirb, 'log.data')) as stream:
      self.assertEqual(stream.read(), log_html)

class log_context_manager(TestCase):

  def test_reenter(self):
    log = nutils.log.StdoutLog()
    with log:
      with self.assertRaises(RuntimeError):
        with log:
          pass

  def test_exit_before_enter(self):
    log = nutils.log.StdoutLog()
    with self.assertRaises(RuntimeError):
      log.__exit__(None, None, None)

class log_module_funcs(TestCase):

  @contextlib.contextmanager
  def assertLogs(self, desired):
    stream = io.StringIO()
    with nutils.log.StdoutLog(stream):
      yield
    self.assertEqual(stream.getvalue(), desired)

  def test_range_1(self):
    with self.assertLogs('x 0 (0%) > 0\nx 1 (50%) > 1\n'):
      for item in nutils.log.range('x', 2):
        nutils.log.user(str(item))

  def test_range_2(self):
    with self.assertLogs('x 1 (0%) > 1\nx 2 (50%) > 2\n'):
      for item in nutils.log.range('x', 1, 3):
        nutils.log.user(str(item))

  def test_range_3(self):
    with self.assertLogs('x 5 (0%) > 5\nx 3 (50%) > 3\n'):
      for item in nutils.log.range('x', 5, 1, -2):
        nutils.log.user(str(item))

  def test_iter_known_length(self):
    with self.assertLogs('x 0 (0%) > 0\nx 1 (50%) > 1\n'):
      for item in nutils.log.iter('x', [0, 1]):
        nutils.log.user(str(item))

  def test_iter_unknown_length(self):
    def items():
      yield 0
      yield 1
    with self.assertLogs('x 0 > 0\nx 1 > 1\n'):
      for item in nutils.log.iter('x', items()):
        nutils.log.user(str(item))

  def test_enumerate(self):
    with self.assertLogs('x 0 (0%) > a\nx 1 (50%) > b\n'):
      for i, v in nutils.log.enumerate('x', 'ab'):
        nutils.log.user(v)

  def test_zip_known_length(self):
    with self.assertLogs('x 0 (0%) > ax\nx 1 (50%) > by\n'):
      for v0, v1 in nutils.log.zip('x', 'ab', 'xyz'):
        nutils.log.user(v0+v1)

  def test_zip_unknown_length(self):
    def items():
      yield 'x'
      yield 'y'
      yield 'z'
    with self.assertLogs('x 0 > ax\nx 1 > by\n'):
      for v0, v1 in nutils.log.zip('x', 'ab', items()):
        nutils.log.user(v0+v1)

  def test_count(self):
    with self.assertLogs('x 0 > 0\nx 1 > 1\n'):
      count = nutils.log.count('x')
      j = 0
      for i in nutils.log.count('x'):
        nutils.log.user(str(i))
        if j == 1:
          break
        j += 1

  def test_title_noarg(self):
    @nutils.log.title
    def x():
      nutils.log.user('y')
    with self.assertLogs('x > y\n'):
      x()

  def test_title_arg_default(self):
    @nutils.log.title
    def x(title='default'):
      nutils.log.user('y')
    with self.assertLogs('default > y\n'):
      x()

  def test_title_arg_nodefault(self):
    @nutils.log.title
    def x(title):
      nutils.log.user('y')
    with self.assertLogs('arg > y\n'):
      x('arg')

  def test_title_varkw(self):
    @nutils.log.title
    def x(**kwargs):
      nutils.log.user('y')
    with self.assertLogs('arg > y\n'):
      x(title='arg')

  def test_context(self):
    with self.assertLogs('x > y\n'):
      with nutils.log.context('x'):
        nutils.log.user('y')
