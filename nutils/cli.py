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
The cli (command line interface) module provides the `cli.run` function that
can be used set up properties, initiate an output environment, and execute a
python function based arguments specified on the command line.
"""

from . import log, util, config, long_version, warnings, matrix, cache
import sys, inspect, os, datetime, pdb, signal, subprocess, contextlib, types, importlib, configparser

def _version():
  try:
    githash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], universal_newlines=True, stderr=subprocess.DEVNULL, cwd=os.path.dirname(__file__)).strip()
    if subprocess.check_output(['git', 'status', '--untracked-files=no', '--porcelain'], stderr=subprocess.DEVNULL, cwd=os.path.dirname(__file__)):
      githash += '+'
  except:
    return long_version
  else:
    return '{} (git:{})'.format(long_version, githash)

def _mkbox(*lines):
  width = max(len(line) for line in lines)
  ul, ur, ll, lr, hh, vv = '┌┐└┘─│' if config.richoutput else '++++-|'
  return '\n'.join([ul + hh * (width+2) + ur]
                 + [vv + (' '+line).ljust(width+2) + vv for line in lines]
                 + [ll + hh * (width+2) + lr])

def _sigint_handler(mysignal, frame):
  _handler = signal.signal(mysignal, signal.SIG_IGN) # temporarily disable handler
  try:
    while True:
      answer = input('interrupted. quit, continue or start debugger? [q/c/d]')
      if answer == 'q':
        raise KeyboardInterrupt
      if answer == 'c' or answer == 'd':
        break
    if answer == 'd': # after break, to minimize code after set_trace
      print(_mkbox(
        'TRACING ACTIVATED. Use the Python debugger',
        'to step through the code at source line',
        'level, list source code, set breakpoints,',
        'and evaluate arbitrary Python code in the',
        'context of any stack frame. Type "h" for',
        'an overview of commands to get going, or',
        '"c" to continue uninterrupted execution.'))
      pdb.set_trace()
  finally:
    signal.signal(mysignal, _handler)

def run(func, *, skip=1, loaduserconfig=True):
  '''parse command line arguments and call function'''

  configs = []
  new_config = configparser.ConfigParser()
  if loaduserconfig:
    home = os.path.expanduser('~')
    configs.append(dict(richoutput=sys.stdout.isatty()))
    configs.extend(path for path in (os.path.join(home, '.config', 'nutils', 'config'), os.path.join(home, '.nutilsrc')) if os.path.isfile(path))

    if os.path.exists(os.path.join(home, '.config', 'nutils', 'run.conf')):
      new_config.read(os.path.join(home, '.config', 'nutils', 'run.conf'))

  extensions = ['nutils.matrix', 'nutils.log.StdoutLog', 'nutils.log.HtmlLog', 'nutils.warnings']
  for extension in new_config.get('global', 'extensions', fallback='').split(','):
    extension = extension.strip()
    if not extension:
      continue
    elif extension.startswith('-'):
      try:
        extensions.remove(extension)
      except ValueError:
        pass
    elif extension not in extensions:
      extensions.append(extension)

  params = inspect.signature(func).parameters.values()

  if '-h' in sys.argv[skip:] or '--help' in sys.argv[skip:]:
    print('usage: {} (...)'.format(' '.join(sys.argv[:skip])))
    print()
    for param in params:
      cls = param.default.__class__
      print('  --{:<20}'.format(param.name + '=' + cls.__name__.upper() if cls != bool else '(no)' + param.name), end=' ')
      if param.annotation != param.empty:
        print(param.annotation, end=' ')
      print('[{}]'.format(param.default))
    sys.exit(1)

  kwargs = {param.name: param.default for param in params}
  cli_config = {}
  extension_args = {}

  for arg in sys.argv[skip:]:
    if arg.startswith('-') and arg[1:2] != '-':
      if '=' in arg:
        print('invalid argument {!r}'.format(arg))
        sys.exit(2)
      try:
        extensions.remove(arg[1:])
      except ValueError:
        pass
      continue
    if arg.startswith('+'):
      extension, sep, value = arg[1:].partition('=')
      if extension not in extensions:
        extensions.append(extension)
      if sep:
        extargs, extkwargs = extension_args.setdefault(extension, ([], {}))
        for extarg in value.split(','):
          if '=' in extarg:
            k, v = extarg.split('=', 1)
            extkwargs[k] = v
          elif extkwargs:
            raise ValueError('positional argument follows keyword argument: {}'.format(arg))
          else:
            extargs.append(extarg)
      continue
    name, sep, value = arg.lstrip('-').partition('=')
    if not sep:
      value = not name.startswith('no')
      if not value:
        name = name[2:]
    if name in kwargs:
      default = kwargs[name]
      args = kwargs
    else:
      try:
        default = getattr(config, name)
      except AttributeError:
        print('invalid argument {!r}'.format(arg))
        sys.exit(2)
      args = cli_config
    try:
      if isinstance(default, bool) and not isinstance(value, bool):
        raise Exception('boolean value should be specifiec as --{0}/--no{0}'.format(name))
      args[name] = default.__class__(value)
    except Exception as e:
      print('invalid argument for {!r}: {}'.format(name, e))
      sys.exit(2)

  if 'outrootdir' in cli_config:
    if not new_config.has_section('global'):
      new_config.add_section('global')
    new_config.set('global', 'outrootdir', cli_config['outrootdir'])

  with config(*configs, **cli_config):
    status = call(func, kwargs, scriptname=os.path.basename(sys.argv[0]), funcname=None if skip==1 else func.__name__, extensions=extensions, extension_args=extension_args, new_config=new_config)

  sys.exit(status)

def choose(*functions, loaduserconfig=True):
  '''parse command line arguments and call one of multiple functions'''

  assert functions, 'no functions specified'

  funcnames = [func.__name__ for func in functions]
  if len(sys.argv) == 1 or sys.argv[1] in ('-h', '--help'):
    print('usage: {} [{}] (...)'.format(sys.argv[0], '|'.join(funcnames)))
    sys.exit(1)

  try:
    ifunc = funcnames.index(sys.argv[1])
  except ValueError:
    print('invalid argument {!r}; choose from {}'.format(sys.argv[1], ', '.join(funcnames)))
    sys.exit(2)

  run(functions[ifunc], skip=2, loaduserconfig=loaduserconfig)

def call(func, kwargs, scriptname, funcname=None, extensions=(), extension_args={}, new_config=None):
  '''set up compute environment and call function'''

  starttime = datetime.datetime.now()
  _info = dict(outrootdir=os.path.expanduser(new_config.get('global', 'outrootdir', fallback='~/public_html')),
               starttime=starttime,
               scriptname=scriptname,
               funcname=funcname,
               funcargs=tuple((param.name, kwargs.get(param.name, param.default), param.annotation) for param in inspect.signature(func).parameters.values()))
  info = types.MappingProxyType(_info)

  with contextlib.ExitStack() as stack:

    for extension in extensions:
      parts = *extension.split('.'), '__nutils_run_extension__'
      for i in range(1, len(parts)):
        try:
          ext = importlib.import_module('.'.join(parts[:i]))
        except ImportError:
          pass
        else:
          break
      else:
        raise ValueError('extension not found: {}'.format(extension))
      for part in parts[i:]:
        ext = getattr(ext, part)

      extsig = inspect.signature(ext)
      if any(param.kind == param.VAR_POSITIONAL for param in extsig.parameters.values()):
        raise ValueError('Extension {} has invalid signature: {}  It should be possible to pass all arguments as keywords.'.format(extension, extsig))
      extkwargs = dict(new_config.items(extension)) if new_config and new_config.has_section(extension) else {}
      extcmdargs, extcmdkwargs = extension_args.get(extension, ([], {}))
      extkwargs.update(extcmdkwargs)
      extparams = tuple(extsig.parameters.values())[1:]
      for i, extval in enumerate(extcmdargs):
        assert extparams[i].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
        extkwargs[extparams[i].name] = extval

      stack.enter_context(ext(info, **extkwargs))

    try:
      old_sigint_handler = signal.signal(signal.SIGINT, _sigint_handler)

      log.info('nutils v{}'.format(_version()))
      log.info('start {}'.format(starttime.ctime()))

      func(**kwargs)

      endtime = datetime.datetime.now()
      _info['endtime'] = endtime
      minutes, seconds = divmod((endtime-starttime).seconds, 60)
      hours, minutes = divmod(minutes, 60)

      log.info('finish {}'.format(endtime.ctime()))
      log.info('elapsed {:.0f}:{:02.0f}:{:02.0f}'.format(hours, minutes, seconds))

    except (KeyboardInterrupt,SystemExit,pdb.bdb.BdbQuit):
      return 1
    except:
      if config.pdb:
        print(_mkbox(
          'YOUR PROGRAM HAS DIED. The Python debugger',
          'allows you to examine its post-mortem state',
          'to figure out why this happened. Type "h"',
          'for an overview of commands to get going.'))
        pdb.post_mortem()
      return 2
    else:
      return 0
    finally:
      signal.signal(signal.SIGINT, old_sigint_handler) # restore handler

# vim:sw=2:sts=2:et
