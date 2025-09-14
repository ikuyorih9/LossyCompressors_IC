#!/usr/bin/python

import argparse
import os, sys
import zlib
import multiprocessing as mp
from shutil import copyfileobj, copy
from subprocess import Popen, PIPE, call

import numpy as np

from progress_bar import ProgressBar

## FIXME: Not working well with is_in_memory. Deactiviting it until we can
# find a good solution for this behavior.
def zlib_compression(fname_or_string, slowness=6, is_in_memory=True, **kwargs):
  """In-memory compression using the zlib library"""
  if not is_in_memory:
    fname = fname_or_string
    with open(fname, 'rb') as f:
      s = f.read()
  else:
    s = fname_or_string

  return len(zlib.compress(s))

def gzip_compression(fname, slowness = 6, **kwargs):
  """Compression using gzip executable.

  @param fname Name of file to compress
  @param slowness Tradeoff parameter: 1 is fastest, 9 is best compression
  @return Size of compressed file in bytes
  """
  process = Popen(['gzip', '-c', '-%d' % slowness, fname], stdout=PIPE)
  compressed_size = len(process.communicate()[0])

  return compressed_size

def bzip2_compression(fname, slowness = 6, **kwargs):
  """Compression using bzip2 executable.
  
  @param fname Name of file to compress
  @param slowness Tradeoff parameter: 1 is fastest, 9 is best compression
  @return Size of compressed file in bytes
  """
  process = Popen(['bzip2', '-c', '-%d' % slowness, fname], stdout=PIPE)
  compressed_size = len(process.communicate()[0])

  return compressed_size

def ppmd_compression(fname, model_order = 6,
    ppmd_tmp_dir = os.path.join('ppmd_tmp'), **kwargs):
  """Compression using ppmd executable.

  @param fname Name of file to compress
  @param model_order Maximum model order to use, from 2 to 16
  @param ppmd_tmp_dir Temporary directory to use for ppmd output. It should be
      different from the input file directory, as the compressed file will have
      the same name as the input.
  @return Size of compressed file in bytes
  """
  tmp_fname = os.path.join(ppmd_tmp_dir, os.path.basename(fname))

  with open(os.devnull, 'w') as devnull:
    call(['ppmd', 'e', '-o%d' % model_order, '-f%s' % tmp_fname, fname],
        stdout=devnull)
  compressed_size = os.path.getsize(tmp_fname)
  os.remove(tmp_fname)

  return compressed_size

def paq_compression(fname, model_order=5, paq_tmp_dir=os.path.join('paq_tmp'),
    **kwargs):
  """Compression using PAQ executable"""
  cp_fname = os.path.join(paq_tmp_dir, os.path.basename(fname))
  tmp_fname = os.path.join(paq_tmp_dir, os.path.basename(fname) + '.paq8l')
  copy(fname, cp_fname)

  #out = open(os.devnull, 'w')
  out = sys.stdout
  call(['paq8', '-%d' % model_order, cp_fname], stdout=out)
  if out is not sys.stdout:
    out.close()

  compressed_size = os.path.getsize(tmp_fname)
  os.remove(tmp_fname)

  return compressed_size

## Available compression functions
compression = {
    'gzip': gzip_compression,
    'bzip2': bzip2_compression,
    'ppmd': ppmd_compression,
    'paq': paq_compression,
}

#### Pairing functions ####

def concat(fname1, fname2, pair_dir = os.path.join('tmp'),
    is_in_memory=False, **kwargs):
  """Concatenates given files into a new file.

  @param fname1, fname2 Files to concatenate (in this order)
  @param pair_dir Directory to output paired file
  @param is_in_memory Whether to perform in-memory pairing
  @return Name of concatenated file, or string if is_in_memory is True
  """
  concat_name = os.path.basename(fname1) + '++' + os.path.basename(fname2)
  concat_fname = os.path.join(pair_dir, concat_name)

  with open(fname1, 'rb') as i1, open(fname2, 'rb') as i2:
    if is_in_memory:
      return i1.read() + i2.read()
    
    with open(concat_fname, 'wb') as f:
      copyfileobj(i1, f)
      copyfileobj(i2, f)
    return concat_fname

def interleave(fname1, fname2, block_size = 1024,
    pair_dir = os.path.join('tmp'), is_in_memory=False, **kwargs):
  """Interleaves blocks of the given files into a new file.

    Partitions each file into blocks with the given size, except for the last
  block, which can be smaller. Then, the blocks are interleaved in turn to
  create a new file. If the files have different sizes, the remaining blocks
  from the bigger one are concatenated.

      f1 = [--x1--][--x2--][--x3--][--x4--][--x5-]
      f2 = [--y1--][--y2--][-y3-]
      f = [--x1--][--y1--][--x2--][--y2--][--x3--][-y3-][--x4--][--x5-]

      This procedure produces NCD closer to zero for NCD(x,x), if x is bigger
  than the size limit for the compressor (32 KiB for gzip, 900 KiB for bzip2).

  @param fname1, fname2 Files to interleave (in this order)
  @param block_size Block size (in bytes)
  @param pair_dir Directory to output paired file
  @param is_in_memory Whether to use in-memory compression
  @return Name of paired file, or paired string if is_in_memory = True
  """
  maxsize = max(os.path.getsize(fname1), os.path.getsize(fname2))
  with open(fname1, 'rb') as i1, open(fname2, 'rb') as i2:
    s = ''
    for _ in xrange(0, maxsize, block_size):
      s += i1.read(block_size) + i2.read(block_size)

  if is_in_memory:
    return s

  inter_name = (os.path.basename(fname1)
      + '--' + os.path.basename(fname2)
      + '--' + str(block_size))
  fname = os.path.join(pair_dir, inter_name)

  with open(fname, 'wb') as f:
    f.write(s)
  return fname

## Available pairing functions
pairing = {
    'concat': concat,
    'interleave': interleave,
}

#### NCD functions ####

class NcdResult:
  def __init__(self, x, y, zx, zy, zxy, ncd):
    self.x = x
    self.y = y
    self.zx = zx
    self.zy = zy
    self.zxy = zxy
    self.ncd = ncd

  def __repr__(self):
    return 'NcdResult(x=%s,y=%s,zx=%d,zy=%d,zxy=%d,ncd=%f' % (self.x, self.y,
        self.zx, self.zy, self.zxy, self.ncd)

def ncd(compression_fn, pairing_fn, fname1, fname2, compressed_sizes = None,
    is_in_memory=False, **kwargs):
  """NCD calculation for a given pair of files.

      The normalized compression distance (NCD) between a pair of objects (x, y) 
  is defined as

                   Z(p(x,y)) - min{ Z(x), Z(y) }
      NCD_Z(x,y) = -----------------------------
                        max{ Z(x), Z(y) }

      where Z is the size of the compression of a given object and p is a
  pairing function that creates an object from two others. Theoretically, this
  distance is normalized between 0 and 1:
      NCD(x,x) == 0 and
      NCD(x,y) == 1 <=> Z(x) + Z(y) == Z(p(x,y))

  @param compression_fn Compression function with type
      fname, **kwargs -> compression_size
  @param pairing_fn Pairing function with type
      fname1, fname2, **kwargs -> paired_fname
      with the side-effect of creating a paired file
  @param fname1, fname2 Names of files to compare
  @param compressed_sizes Optional 2-tuple containing the compressed sizes of
      fname1 and fname2. If not provided, the sizes are calculated using
      compression_fn
  @param is_in_memory Whether to use in-memory compressors
  @param kwargs Additional arguments that are passed to compression_fn and
      pairing_fn
  @return NcdResult object containing additional information about the
      calculation
  """
  if compressed_sizes is None:
    compressed_sizes = (
        compression_fn(fname1, is_in_memory=False, **kwargs),
        compression_fn(fname2, is_in_memory=False, **kwargs))

  fname = pairing_fn(fname1, fname2, is_in_memory=is_in_memory, **kwargs)
  paired_compressed_size = compression_fn(fname, is_in_memory=is_in_memory,
      **kwargs)
  if not is_in_memory:
    os.remove(fname)

  minimum, maximum = sorted(compressed_sizes)
  result = NcdResult(
      x = os.path.basename(fname1), y = os.path.basename(fname2),
      zx = compressed_sizes[0], zy = compressed_sizes[1],
      zxy = paired_compressed_size,
      ncd = float(paired_compressed_size - minimum)/maximum)
  return result

#### Parallel wrappers ####

def _parallel_compression_worker(args):
  """Wrapper for parallel calculation of compressed sizes."""
  compression_name, fname, queue, progress_bar, kwargs = (
      args.get('cname'), args.get('fname'), args.get('queue'),
      args.get('progress'), args.get('kwargs'))

  if compression_name is None:
    raise Exception('Compression not given')
  if fname is None:
    raise Exception('Filename not given')

  compression_fn = compression[compression_name]
  x = compression_fn(fname, **kwargs)

  if queue is not None:
    queue.put(x)

  if progress_bar is not None:
    progress_bar.increment()

  return x

def _parallel_ncd_worker(args):
  """Wrapper for parallel calculation of NCD pairs."""
  compression_name, pairing_name, fname1, fname2, queue, progress_bar,\
  compressed_sizes, kwargs = (args.get('cname'), args.get('pname'),
      args.get('f1'), args.get('f2'),
      args.get('queue'), args.get('progress'), args.get('zip'),
      args.get('kwargs'))

  if compression_name is None:
    raise Exception('Compression function name not given')
  if pairing_name is None:
    raise Exception('Pairing function name not given')
  if fname1 is None or fname2 is None:
    raise Exception('Filenames not given')

  compression_fn = compression[compression_name]
  pairing_fn = pairing[pairing_name]
 
  result = ncd(compression_fn, pairing_fn, fname1, fname2, compressed_sizes,
      **kwargs)

  if queue is not None:
    queue.put(result)

  if progress_bar is not None:
    progress_bar.increment()

  return result

#### Distance matrix calculations ####

def _serial_compress_files(fnames, compression_fn, verbosity_level=1, **kwargs):
  """Serial calculation of compressed sizes."""
  
  if verbosity_level == 0:
    function = lambda fname: compression_fn(fname, **kwargs)
    compressed_sizes = map(function, fnames)
  else:
    sys.stderr.write('Compressing individual files...\n')
    progress_bar = ProgressBar(len(fnames))
    
    def update_progress(fname):
      x = compression_fn(fname, **kwargs)
      progress_bar.increment()
      return x
    compressed_sizes = map(update_progress, fnames)
    sys.stderr.write('\n')

  return dict(zip(fnames, compressed_sizes))

def _serial_compress_pairs(zip_size, file_pairs, compression_fn, pairing_fn,
    verbosity_level=1, **kwargs):
  """Serial calculation of paired file pairs compression."""
  if verbosity_level == 0:
    def process(pair):
      fname1, fname2 = pair
      return ncd(compression_fn, pairing_fn, fname1, fname2,
          (zip_size[fname1], zip_size[fname2]), **kwargs)
    return map(process, file_pairs)

  sys.stderr.write('Compressing file pairs...\n')
  progress_bar = ProgressBar(len(file_pairs))

  def update_progress(pair):
    fname1, fname2 = pair
    ncd_result = ncd(compression_fn, pairing_fn, fname1, fname2,
        (zip_size[fname1], zip_size[fname2]), **kwargs)
    progress_bar.increment()
    return ncd_result
   
  ncd_results = map(update_progress, file_pairs)

  sys.stderr.write('\n')
  return ncd_results

def _serial_distance_matrix(fnames, file_pairs, compression_fn, pairing_fn,
    **kwargs):
  """Serial calculation for distance matrix."""
  zip_size = _serial_compress_files(fnames, compression_fn, **kwargs)
  return _serial_compress_pairs(zip_size, file_pairs, compression_fn,
      pairing_fn, **kwargs)

def _maybe_make_pool_and_queue(pool=None, queue=None):
  if pool is None:
    num_cpus = mp.cpu_count()
    pool = mp.Pool(num_cpus)

  if queue is None:
    num_cpus = mp.cpu_count()
    manager = mp.Manager()
    queue = manager.Queue(2*num_cpus)

  return pool, queue

def _parallel_compress_files(fnames, compression_name, pool=None, queue=None,
    verbosity_level=1, **kwargs):
  """Parallel calculation of individual compressed sizes."""
  if verbosity_level > 0:
    sys.stderr.write('Compressing individual files...\n')
    progress_bar = ProgressBar(len(fnames))

  pool, queue = _maybe_make_pool_and_queue(pool, queue)
  compression_args = [{
    'cname': compression_name, 'fname': fname,
    'queue': queue, 'kwargs': kwargs}
    for fname in fnames]
 
  async_result = pool.map_async(_parallel_compression_worker, compression_args)

  for _ in xrange(len(fnames)):
    queue.get(timeout=None)
    progress_bar.increment() if verbosity_level > 0 else None

  compressed_sizes = async_result.get()
  sys.stderr.write('\n') if verbosity_level > 0 else None
  return dict(zip(fnames, compressed_sizes))

def _parallel_compress_pairs(zip_size, file_pairs, compression_name,
    pairing_name, pool=None, queue=None, verbosity_level=1, **kwargs):
  """Parallel calculation of paired file pairs compression."""
  if verbosity_level > 0:
    sys.stderr.write('Compressing file pairs...\n')
    progress_bar = ProgressBar(len(file_pairs))

  pool, queue = _maybe_make_pool_and_queue(pool, queue)
  ncd_args = [{
    'cname': compression_name,
    'pname': pairing_name,
    'f1': fname1, 'f2': fname2,
    'queue': queue, 'zip': (zip_size[fname1], zip_size[fname2]),
    'kwargs': kwargs} for fname1, fname2 in file_pairs]

  async_result = pool.map_async(_parallel_ncd_worker, ncd_args)

  for _ in xrange(len(file_pairs)):
    queue.get(timeout=None)
    progress_bar.increment() if verbosity_level > 0 else None

  ncd_results = async_result.get()
  sys.stderr.write('\n') if verbosity_level > 0 else None
  return ncd_results
 
def _parallel_distance_matrix(fnames, file_pairs, compression_name,
    pairing_name, **kwargs):
  """Parallel calculation of distance matrix."""

  num_cpus = mp.cpu_count()
  manager = mp.Manager()
  pool = mp.Pool(num_cpus)
  queue = manager.Queue(2*num_cpus)

  zip_size = _parallel_compress_files(fnames, compression_name, pool, queue,
      **kwargs)
  ncd_results = _parallel_compress_pairs(zip_size, file_pairs, compression_name,
    pairing_name, pool, queue, **kwargs)
  pool.close()

  return ncd_results

def get_filenames(directory):
  fnames = sorted(os.listdir(directory))
  return [os.path.join(directory, fname)
      for fname in fnames
      if os.path.isfile(os.path.join(directory, fname))]

def compress_files(fnames, compression_name, is_parallel=True, **kwargs):
  if is_parallel:
    return _parallel_compress_files(fnames, compression_name, **kwargs)

  return _serial_compress_files(fnames, compression[compression_name], **kwargs)

def compress_pairs(zip_size, file_pairs, compression_name, pairing_name,
    is_parallel=True, **kwargs):
  if is_parallel:
    return _parallel_compress_pairs(zip_size, file_pairs, compression_name,
        pairing_name, **kwargs)
  
  return _serial_compress_pairs(zip_size, file_pairs,
      compression[compression_name], pairing[pairing_name], **kwargs)

def distance_matrix(directory, compression_name, pairing_name,
    is_parallel=True, **kwargs):
  """Calculates matrix of distances between all files in a given directory.

  @param directory Directory name with files to compare, or pair of directories
    to cross-compare
  @param compression_name Name of compression function to use
  @param pairing_name Name of pairing function to use
  @param is_parallel Whether to perform computation in parallel
  @param kwargs Additional arguments for compression and pairing functions
  @return List of NcdResult objects from comparing all pairs of files
  """
  # Checks whether we should compare all files within a directory, or the files
  # from a pair of directories
  if isinstance(directory, basestring):
    fnames = get_filenames(directory)
    file_pairs = [(fname1, fname2)
        for fname1 in fnames
        for fname2 in fnames
        if fname1 < fname2]
  else:
    try:
      dir1, dir2 = directory
      fnames1, fnames2 = get_filenames(dir1), get_filenames(dir2)
      fnames = fnames1 + fnames2
      file_pairs = [(fname1, fname2)
          for fname1 in fnames1
          for fname2 in fnames2]
    except TypeError:
      raise TypeError('Provided directory is not an iterable: %s'
          % str(directory))
    except ValueError:
      raise ValueError("Provided directory doesn't have only two arguments: %s"
          % str(directory))

  if is_parallel:
    ncd_results = _parallel_distance_matrix(fnames, file_pairs,
        compression_name, pairing_name, **kwargs)
  else:
    ncd_results = _serial_distance_matrix(fnames, file_pairs,
        compression[compression_name], pairing[pairing_name], **kwargs)

  return ncd_results

#### Formatting functions ####

def csv_format(ncd_results, header=True):
  """Formats a list of NcdResult objects in CSV format.

  @param ncd_results List of NcdResult as returned by distance_matrix
  @param header Whether a header should be outputted to the CSV file
  @return String in CSV format
  """
  s = '' if not header else 'x,y,zx,zy,zxy,ncd\n'
  for result in ncd_results:
    s += '"{r.x}","{r.y}",{r.zx},{r.zy},{r.zxy},{r.ncd:.15f}\n'.format(
      r=result)
  return s

def to_matrix(ncd_results, is_self=True):
  """Converts a list of NcdResult objects to an n x m ndarray.

  @param ncd_results List of NcdResult as returned by distance_matrix
  @param is_self Whether the results are from a self-distance computation
  @return (m, ids) distance matrix with corresponding IDs
  """
  xs = [r.x for r in ncd_results]
  ys = [r.y for r in ncd_results]
  if is_self:
    names = sorted(set(xs + ys))
    ids = [names, names]
  else:
    ids = [sorted(set(xs)), sorted(set(ys))]

  m = np.zeros([len(ids[0]), len(ids[1])])

  for result in ncd_results:
    i, j = ids[0].index(result.x), ids[1].index(result.y)
    m[i][j] = result.ncd

  if is_self:
    m = m + np.transpose(m)

  return m, ids

def phylip_format(ncd_results, alternative_ids = None):
  """Formats a list of NcdResult objects in Phylip format.
   
      The Phylip format is used in phylogenetic software to store distance
  matrices between taxa. Each taxon name is limited to 10 chars, so the
  IDs used in NCD are truncated to satisfy this restriction. The format is as
  follows:

      <number-of-taxons>
      <taxon-name 1> <d(t1,t1)> <d(t1,t2)> ... <d(t1,tn)>
      <taxon-name 2> <d(t2,t1)> <d(t2,t2)> ... <d(t2,tn)>
      ...
      <taxon-name n> <d(tn,t1)> <d(tn,t2)> ... <d(tn,tn)>

  @param ncd_results List of NcdResult as returned by distance_matrix
  @param alternative_ids Optional IDs to use as taxon name. This might be
    necessary if the truncation of file names results in duplicates.
  @return String with matrix in Phylip format
  """
  m, (ids_x, ids_y) = to_matrix(ncd_results)
  if alternative_ids is not None:
    ids = alternative_ids
  else:
    ids = ids_x if ids_x == ids_y else ids_x + ids_y

  names = ['{name:<10.10}'.format(name=id_) for id_ in ids]
  # TODO(brunokim): Find conflicts and solve them

  s = '%d\n' % len(m)
  for name,row in zip(names, m):
    xs = ' '.join('%.15f' % dij for dij in row)
    s += name + ' ' + xs + '\n'

  return s

#### Command-line interface parser ####

def cli_parser():
  """Returns CLI parser for script.
  
  This may be useful for other scripts willing to call this one.
  """
  parser = argparse.ArgumentParser(add_help=False,
      description='Calculates NCD matrix between objects')
  parser.add_argument('directory', nargs='+',
      help='Directory or directories containing files to compare')
  parser.add_argument('--complete', action='store_true',
      help='Performs complete comparison in a single directory, not assuming' +
      ' that NCD(x,y) == NCD(y,x) and that NCD(x,x) == 0')

  parser.add_argument('-c', '--compressor', choices=compression.keys(),
      default='ppmd', help='Compressor to use (default: ppmd)')
  parser.add_argument('-P', '--pairing', choices=pairing.keys(),
      default='concat', help='Pairing method to use (default: concat)')
  parser.add_argument('-o', '--output', help='output file (default: stdout)')
  parser.add_argument('-f', '--matrix-format', choices=['csv', 'phylip'],
      help='Choose matrix format (default: csv)')

  compressor_group = parser.add_argument_group('Compressor options', 
      'Options to control compressor behavior')
  compressor_group.add_argument('--slowness', '--gzip-slowness',
      '--bzip2-slowness', default=6, type=int,
      help='(gzip, bzip2) slowness of compression (1-9): ' + 
      '1 is faster, 9 is best compression')
  compressor_group.add_argument('--model-order', '--ppmd-model-order',
      default=6, type=int,
      help='(ppmd) model order (2-16): 2 is faster, 16 is best')
  compressor_group.add_argument('--memory', '--ppmd-memory',
      default=10, type=int, help='(ppmd) maximum memory, in MiB (1-256)')
  compressor_group.add_argument('--block-size', '--interleave-block-size',
      default=1024, type=int,
      help='(interleave) block size for interleaving, in bytes')

  misc_group = parser.add_argument_group('General options')
  
  misc_group.add_argument('--serial', action='store_true',
      help='Compute compressions serially')
  misc_group.add_argument('--parallel', action='store_true',
      help='Compute compressions in parallel (default)')

  misc_group.add_argument('-v', '--verbose', action='count',
      help='Verbose output. Repeat to increase verbosity level (default: 1)',
      default = 1)
  misc_group.add_argument('--no-verbose', action='store_true',
      help='Turn verbosity off')
  misc_group.add_argument('-V', '--version', action='version', version='0.0.1')

  return parser

if __name__ == '__main__':
  parser = argparse.ArgumentParser(parents=[cli_parser()])
  a = parser.parse_args()

  # TODO(brunokim): refactor code to use verbosity level, probably using a
  # logging library
  # verbose=0: no output to stderr
  # verbose=1: print progress bars
  # verbose=2: print files being compressed and a 'x/total' progress info
  verbose = 0 if a.no_verbose else a.verbose
  if verbose != 1:
    sys.stderr.write('Note: verbosity level not implemented yet\n')

  if not os.path.exists('tmp') or not os.path.isdir('tmp'):
    os.mkdir('tmp')
  if a.compressor == 'ppmd' and (
      not os.path.exists('ppmd_tmp') or not os.path.isdir('ppmd_tmp')):
    os.mkdir('ppmd_tmp')
  if a.compressor == 'paq' and (
      not os.path.exists('paq_tmp') or not os.path.isdir('paq_tmp')):
    os.mkdir('paq_tmp')
  
  kwargs = {
      'pair_dir': 'tmp',
      'ppmd_tmp_dir': 'ppmd_tmp',
      'slowness': a.slowness,
      'model_order': a.model_order,
      'memory': a.memory,
      'block_size': a.block_size,
      'is_in_memory': a.compressor == 'zlib'
  }
 
  if len(a.directory) == 1:
    if a.complete:
      directory = [a.directory[0], a.directory[0]]
    else:
      directory = a.directory[0]
  elif len(a.directory) == 2:
    directory = a.directory
  else:
    raise ValueError('More than two directories provided')

  results = distance_matrix(directory, a.compressor, a.pairing,
      is_parallel = not a.serial, verbosity_level = verbose, **kwargs)

  if a.matrix_format == 'phylip':
    out = phylip_format(results)
  else:
    out = csv_format(results)
  
  if a.output is None:
    print out
  else:
    with open(a.output, 'wt') as f:
      f.write(out)

