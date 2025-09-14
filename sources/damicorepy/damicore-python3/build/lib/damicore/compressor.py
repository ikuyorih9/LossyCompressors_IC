"""Compressor objects.

Attributes:
  available: set of available compressor names.

Functions:
  list_compressors() -> list of available compressor names
  get_compressor(name) -> returns the default compressor instance for this name
"""

import os
import sys
import math
import tempfile
import logging
import shutil
import ctypes

from ctypes.util import find_library
from subprocess import Popen, PIPE, call

### Module stores which compressors are available when importing

available = set()

def list_compressors():
  """Returns a list of available compressors."""
  return list(available)

def get_compressor(name, level=6, model_order=6, memory=10,
    restoration_method="restart", tmp_dir=tempfile.gettempdir()):
  """Returns the default compressor instance with the given name.
  
  Check if compressor is available with available_compressors().
  If this compressor is not available, raises KeyError.
  """
  if name not in available:
    raise KeyError(name + ' compressor not available! ' + 
      'Did you set your path correctly?')

  if name == 'zlib':
    return Zlib(level)
  if name == 'gzip':
    return Gzip(level)
  if name == 'bz2':
    return Bz2(level)
  if name == 'bzip2':
    return Bzip2(level)
  if name == 'ppmd':
    return Ppmd(model_order, memory, restoration_method, tmp_dir)
  if name == 'paq8':
    return Paq8(model_order, tmp_dir)

class Compressor(object):
  """Abstract compressor."""
  def __init__(self, name):
    self.name = name

  def compressed_size(self, datasrc):
    raise NotImplementedError("compressed_size not implemented")

# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program, other_dirs=[]):
  """Returns the complete path to a program.
  
  other_dirs may contain a list of additional directories to look for an
  executable.
  """
  def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

  fpath, fname = os.path.split(program)
  if fpath:
    if is_exe(program):
      return program
  else:
    for path in os.environ["PATH"].split(os.pathsep) + other_dirs:
      path = path.strip('"')
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file

  return None

#### zlib library
try:
  import zlib

  class Zlib(Compressor):
    """In-memory compressor using the zlib library."""
    def __init__(self, level=6):
      Compressor.__init__(self, 'zlib')
      self.level = level

    def compressed_size(self, datasrc):
      return len(zlib.compress(datasrc.get_string(), self.level))
  available.add('zlib')

except ImportError:
  logger = logging.getLogger(__name__)
  logger.debug('zlib module not available')

#### gzip executable
if which('gzip'):
  class Gzip(Compressor):
    """Compressor using the gzip executable."""
    def __init__(self, level=6):
      Compressor.__init__(self, 'gzip')
      self.path = which('gzip')
      self.level = level

    def compressed_size(self, datasrc):
      process = Popen([self.path, '-c',
        '-%d' % self.level,
        datasrc.get_filename()], stdout=PIPE)
      size = len(process.communicate()[0])

      return size
  available.add('gzip')
else:
  logger = logging.getLogger(__name__)
  logger.debug('gzip executable not available')

#### bz2 library
if find_library("bz2"):
  libbz2 = ctypes.cdll.LoadLibrary(find_library("bz2"))
  class Bz2(Compressor):
    """Compressor using the libbz2 library."""
    def __init__(self, level=6):
      Compressor.__init__(self, 'bz2')
      self.level = level

    def compressed_size(self, datasrc):
      buf = datasrc.get_string()
      buflen = len(buf)
      maxlen = int(math.ceil(buflen * 1.01 + 600))

      dest = ctypes.create_string_buffer(maxlen)
      dest_len = ctypes.c_int(maxlen)
      verbosity = 0
      work_factor = 0 # Default
      result = libbz2.BZ2_bzBuffToBuffCompress(dest, ctypes.byref(dest_len),
          buf, buflen, self.level, verbosity, work_factor)
      if result == 0:
        return dest_len.value
      raise RuntimeError("bz2 compress returned %d" % result)
  available.add('bz2')
else:
  logger = logging.getLogger(__name__)
  logger.debug('bz2 library not available')

if which("bzip2"):
  class Bzip2(Compressor):
    """Compressor using the bzip2 executable."""
    def __init__(self, level=6):
      Compressor.__init__(self, 'bzip2')
      self.path = which('bzip2')
      self.level = level

    def compressed_size(self, datasrc):
      process = Popen([self.path, '-c',
        '-%d' % self.level,
        datasrc.get_filename()], stdout=PIPE)
      size = len(process.communicate()[0])

      return size
  available.add('bzip2')
else:
  logger = logging.getLogger(__name__)
  logger.debug('bzip2 executable not available')
    
#### PPMd executable
if which('ppmd', ['../ppmdi2']):
  class Ppmd(Compressor):
    """Compressor using the ppmd executable."""
    def __init__(self, model_order=6, memory=10, restoration_method="restart",
        tmp_dir=tempfile.gettempdir()):
      Compressor.__init__(self, 'ppmd')
      self.path = which('ppmd', ['../ppmdi2'])
      self.model_order = model_order
      self.tmp_dir = tmp_dir
      self.memory = memory

      method_map = {'restart': 0, 'cutoff': 1, 'freeze': 2}
      self.restoration_method = method_map.get(restoration_method, 0)

    def compressed_size(self, datasrc):
      tmpname = tempfile.mktemp(prefix=str(datasrc.name), dir=self.tmp_dir)

      with open(os.devnull, 'w') as devnull:
        call([self.path, 'e',  '-o%d' %  self.model_order, '-f%s' % tmpname,
          '-m%d' % self.memory, '-r%d' % self.restoration_method,
          datasrc.get_filename()], stdout=devnull)
      size = os.path.getsize(tmpname)
      os.remove(tmpname)

      return size
  available.add('ppmd')
else:
  logger = logging.getLogger(__name__)
  logger.debug('ppmd executable not available.' + 
      ' Consider make-ing it at ppmdi2 directory.')

#### PAQ8 executable
if which('paq8', ['../paq8']):
  class Paq8(Compressor):
    """Compressor using the paq8 executable"""
    def __init__(self, model_order=3, tmp_dir=tempfile.gettempdir()):
      Compressor.__init__(self, 'paq8')
      self.path = which('paq8', ['../paq8'])
      self.model_order = model_order
      self.tmp_dir = tmp_dir

    def compressed_size(self, datasrc):
      tmpname = tempfile.mktemp(prefix=str(datasrc.name), dir=self.tmp_dir)
      shutil.copy(datasrc.get_filename(), tmpname)

      with open(os.devnull, 'w') as devnull:
        call([self.path, '-%d' % self.model_order, tmpname], stdout=devnull)

      compressed_tmpname = tmpname + '.paq8l'
      compressed_size = os.path.getsize(compressed_tmpname)

      os.remove(compressed_tmpname)
      os.remove(tmpname)
      return compressed_size
  available.add('paq8')
else:
  logger = logging.getLogger(__name__)
  logger.debug('paq8 executable not available.' +
      ' Consider make-ing it at paq8 directory.')
