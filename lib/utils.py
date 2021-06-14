import os


def mkpath(*paths):
  """Make path."""
  path = os.path.join(*[str(path) for path in paths])
  path = os.path.realpath(path)
  return path
