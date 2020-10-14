from typing import Any

def debug(*args: Any) -> None:
  print(*args)

info = debug

def warning(*args: Any) -> None:
  for line in ' '.join(map(str, args)).split('\n'):
    print('::warning ::{}'.format(line))

def error(*args: Any) -> None:
  for line in ' '.join(map(str, args)).split('\n'):
    print('::error ::{}'.format(line))

def set_output(key: str, value: str) -> None:
  print('::set-output name={}::{}'.format(key, value))
  print('OUTPUT: {}={}'.format(key, value))
