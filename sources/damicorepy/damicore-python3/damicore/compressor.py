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
import json
from time import time

from ctypes.util import find_library
from subprocess import Popen, PIPE, call

import damicore.image_compressor as img_compressor
import damicore.bitmap as bitmap
from damicore.entro import calculate_entropy_compression

### Module stores which compressors are available when importing

available = set()

def list_compressors():
  """Returns a list of available compressors."""
  return list(available)

def get_compressor(
    name, 
    level=6, 
    model_order=6, 
    memory=10,
    restoration_method="restart", 
    lossy=0,
    json_time=None,
    tmp_dir=tempfile.gettempdir()
  ):
  """Returns the default compressor instance with the given name.
  
  Check if compressor is available with available_compressors().
  If this compressor is not available, raises KeyError.
  """
  if name not in available:
    raise KeyError(name + ' compressor not available! ' + 
      'Did you set your path correctly?')

  if name == 'zlib':
    return Zlib(level, json_time)
  if name == 'gzip':
    return Gzip(level, json_time)
  if name == 'bz2':
    return Bz2(level, json_time)
  if name == 'bzip2':
    return Bzip2(level, json_time)
  if name == 'ppmd':
    return Ppmd(model_order, memory, restoration_method, tmp_dir, json_time)
  if name == 'paq8':
    return Paq8(model_order, tmp_dir)
  if name == 'webp':
    return WebP(lossy=bool(lossy), json_time=json_time)
  if name == 'png':
    return Png(json_time=json_time)
  if name == 'jp2':
    return Jp2(lossy=bool(lossy), json_time=json_time)
  if name== 'heif':
    return Heif(json_time=json_time)
  if name == 'entropy':
    return Entropy(json_time = json_time)
  if name == 'lzma':
    return Lzma(level)

class Compressor(object):
  """Abstract compressor."""
  def __init__(self, name, json_time=None):
    self.name = name
    self.json_time = json_time

  def export_time(self, etime):
    if not self.json_time:
        return

    os.makedirs(os.path.dirname(self.json_time), exist_ok=True)

    entry = {
        'compressor': self.name,
        'execution_time': etime,
    }

    # ✅ 'a' = append mode – segura para multiprocessing com ".jsonl"
    with open(self.json_time, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

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
    def __init__(self, level=6, log_file=None):
      Compressor.__init__(self, 'zlib', log_file)
      self.level = level

    def compressed_size(self, datasrc):
      init = time()
      size = len(zlib.compress(datasrc.get_string().encode(), self.level))
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      return size
  available.add('zlib')

except ImportError:
  logger = logging.getLogger(__name__)
  logger.debug('zlib module not available')

try:
  import pyppmd

  class Ppmd(Compressor):
    """In-memory compressor using the pyppmd library."""
    def __init__(self, model_order=6, memory=10, restoration_method="restart", tmp_dir=tempfile.gettempdir(), json_time:str=None):
        Compressor.__init__(self, 'ppmd', json_time)
        self.model_order = model_order
        self.memory = memory<<20
        self.tmp_dir = tmp_dir

        # Map restoration methods to pyppmd options
        method_map = {'restart': pyppmd.PPMD8_RESTORE_METHOD_RESTART, 'cutoff': pyppmd.PPMD8_RESTORE_METHOD_CUT_OFF}
        self.restoration_method = method_map.get(restoration_method, pyppmd.PPMD8_RESTORE_METHOD_RESTART)

    def compressed_size(self, datasrc):
      # Compress the data using pyppmd
      compressor = pyppmd.PpmdCompressor(
        max_order=self.model_order, 
        mem_size=self.memory, 
        restore_method=self.restoration_method
      )

      init = time()
      size = len(compressor.compress(datasrc.get_string().encode()))
      end = time()
      compressor.flush()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      # Return the size of the compressed data
      return size

  # Add PPMd to the available compressors
  available.add('ppmd')

except ImportError:
    logger = logging.getLogger(__name__)
    logger.debug('pyppmd module not available')

try:
  class WebP(Compressor):
    def __init__(self,lossy=False, json_time:str=None):
      Compressor.__init__(self, "webp_lossy" if lossy else "webp_lossless", json_time)
      self.lossy = lossy
      
    def compressed_size(self, datasrc):
      init = time()
      bmp_data = bitmap.get_bitmap_byte_to_component(datasrc.get_string())
      size = len(img_compressor.compress_to_webp_from_bytes(bmp_data, self.lossy))
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      return size
  available.add('webp')
  
except Exception:
  logger = logging.getLogger(__name__)
  logger.debug('WEBP module not available')

try:
  class Png(Compressor):
    def __init__(self, optimize = True, json_time:str=None):
      Compressor.__init__(self, "png", json_time)
      self.optimize = optimize

    def compressed_size(self, datasrc):
      # bmp_data = bitmap.get_bitmap_hex_bytes(datasrc.get_string())
      init = time()
      bmp_data = bitmap.get_bitmap_byte_to_component(datasrc.get_string())
      size = len(img_compressor.compress_to_png_from_bytes(bmp_data, output=None, optimize=self.optimize))
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      return size
  available.add('png')
except Exception:
  logger = logging.getLogger(__name__)
  logger.debug('PNG module not available')

try:
  class Jp2(Compressor):
    def __init__(self,lossy=False, json_time:str=None, quality_layers=[50]):
      Compressor.__init__(self, "jp2_lossy" if lossy else "jp2_lossless", json_time)
      self.lossy = lossy
      self.quality_layers = quality_layers
      
    def compressed_size(self, datasrc):
      init = time()
      bmp_data = bitmap.get_bitmap_byte_to_component(datasrc.get_string())
      size = len(img_compressor.compress_to_jp2_from_bytes(bmp_data, self.lossy))
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      return size
  available.add('jp2')
  
except Exception:
  logger = logging.getLogger(__name__)
  logger.debug('JP2 module not available')

try:
  class Heif(Compressor):
    def __init__(self, json_time:str=None, quality=90):
      Compressor.__init__(self, "heif", json_time)
      self.quality=quality
      
    def compressed_size(self, datasrc):
      init = time()
      bmp_data = bitmap.get_bitmap_byte_to_component(datasrc.get_string())
      size = len(img_compressor.compress_to_heif_from_bytes(bmp_data, quality=self.quality))
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      return size
  available.add('heif')
  
except Exception:
  logger = logging.getLogger(__name__)
  logger.debug('JP2 module not available')

try:
  
  class Entropy(Compressor):
    def __init__(self, json_time:str=None):
      Compressor.__init__(self, "entropy", json_time)
    
    def compressed_size(self, datasrc):
      init = time()
      size = calculate_entropy_compression(datasrc.get_string())
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      return size
  available.add('entropy')

except Exception:
  print("[COMPRESSOR EXCEPTION]: não foi possível importar.")
  logger = logging.getLogger(__name__)
  logger.debug('ENTROPY module not available')

try:
  import lzma
  class Lzma(Compressor):
    def __init__(self, level=9, json_time:str=None):
      Compressor.__init__(self, 'lzma', json_time)
      self.level = level

    def compressed_size(self, datasrc):
      init = time()
      size = len(lzma.compress(datasrc.get_string().encode(), preset=self.level))
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      return size
  available.add('lzma')

except ImportError:
  logger = logging.getLogger(__name__)
  logger.debug('lzma module not available')

#### gzip executable
if which('gzip'):
  class Gzip(Compressor):
    """Compressor using the gzip executable."""
    def __init__(self, level=6, json_time:str=None):
      Compressor.__init__(self, 'gzip', json_time)
      self.path = which('gzip')
      self.level = level

    def compressed_size(self, datasrc):
      init = time()
      process = Popen([self.path, '-c',
        '-%d' % self.level,
        datasrc.get_filename()], stdout=PIPE)
      size = len(process.communicate()[0])
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
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
    def __init__(self, level=6, json_time:str=None):
      Compressor.__init__(self, 'bz2', json_time)
      self.level = level

    def compressed_size(self, datasrc):
      init = time()
      buf = datasrc.get_string().encode('utf-8')
      buflen = len(buf)
      maxlen = int(math.ceil(buflen * 1.01 + 600))
      src_buf = ctypes.create_string_buffer(buf, buflen)
      dest = ctypes.create_string_buffer(maxlen)
      dest_len = ctypes.c_int(maxlen)
      verbosity = 0
      work_factor = 0 # Default
      result = libbz2.BZ2_bzBuffToBuffCompress(dest, ctypes.byref(dest_len), src_buf, buflen, self.level, verbosity, work_factor)
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
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
    def __init__(self, level=6, json_time:str=None):
      Compressor.__init__(self, 'bzip2', json_time)
      self.path = which('bzip2')
      self.level = level

    def compressed_size(self, datasrc):
      init = time()
      process = Popen([self.path, '-c',
        '-%d' % self.level,
        datasrc.get_filename()], stdout=PIPE)
      size = len(process.communicate()[0])
      end = time()
      if "sample_data" in datasrc.get_filename() and  not "CONTROL" in datasrc.get_filename():
        self.export_time(end-init)
      return size
  available.add('bzip2')
else:
  logger = logging.getLogger(__name__)
  logger.debug('bzip2 executable not available')
    
### PPMd executable
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
