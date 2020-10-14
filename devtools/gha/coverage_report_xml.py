import sys, re, os.path
from xml.etree import ElementTree
from pathlib import Path
from coverage import Coverage

paths = []
for path in sys.path:
  try:
    paths.append(str(Path(path).resolve()).lower()+os.path.sep)
  except FileNotFoundError:
    pass
paths = tuple(sorted(paths, key=len, reverse=True))
unix_paths = tuple(p.replace('\\', '/') for p in paths)
packages = tuple(p.replace('/', '.') for p in unix_paths)

dst = Path('coverage.xml')

# Generate `coverage.xml` with absolute file and package names.
cov = Coverage()
cov.load()
cov.xml_report(outfile=str(dst))

# Load the report, remove the largest prefix in `packages` from attribute
# `name` of element `package`, if any, and similarly the largest prefix in
# `paths` from attribute `filename` of element `class` and from the content of
# element `source`. Matching prefixes is case insensitive for case insensitive
# file systems.
def remove_prefix(value, prefixes):
  lvalue = value.lower()
  for prefix in prefixes:
    if lvalue.startswith(prefix):
      return value[len(prefix):]
  return value
root = ElementTree.parse(str(dst))
for elem in root.iter('package'):
  for package in packages:
    if elem.get('name'):
      elem.set('name', remove_prefix(elem.get('name'), packages))
  for elem in root.iter('class'):
    if elem.get('filename'):
      elem.set('filename', remove_prefix(elem.get('filename'), unix_paths))
  for elem in root.iter('source'):
    if elem.text:
      elem.text = remove_prefix(elem.text, paths)
root.write('coverage.xml')
