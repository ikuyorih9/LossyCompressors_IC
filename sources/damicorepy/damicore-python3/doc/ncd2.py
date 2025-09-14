#!/usr/bin/python

"""Implementation of distance matrix with NCD algorithms."""

import os
import sys
import shutil
import tempfile
import csv
import logging
import argparse
import math

import multiprocessing as mp

from io import StringIO
from random import Random

import numpy as np

import ncd_base
import _utils
import compressor as c
from ncd_base import NcdResult, ncd
from datasource import create_factory
from _utils import frequency, open_outfile

#### Class for a collection of NcdResults, which can be obtained from an in-
#### memory computation (serial) or from a tempfile (parallel).

global parallel_compress_sources

class NcdResults(object):
  def get_results(self):
    raise NotImplementedError()

  def get_filename(self):
    raise NotImplementedError()

  def close(self):
    pass

class InMemoryNcdResults(NcdResults):
  def __init__(self, results):
    self.results = results
    self.tmpname = None

  def get_results(self):
    return self.results

  def get_filename(self):
    fd, tmpname = tempfile.mkstemp(prefix='ncd-')
    with os.fdopen(fd, 'w') as f:
      ncd_base.write_csv(f, self.results, output_header=True)
    self.tmpname = tmpname
    return tmpname
  
  def close(self):
    if self.tmpname:
      os.remove(self.tmpname)

class FilenameNcdResults(NcdResults):
  def __init__(self, fname):
    self.fname = fname
    self.f = None

  def get_results(self):
    self.f = open(self.fname, 'rt')
    return ncd_base.csv_read(self.f)
  
  def get_filename(self):
    return self.fname

  def close(self):
    if self.f:
      self.f.close()

class TempfileNcdResults(FilenameNcdResults):
  def close(self):
    FilenameNcdResults.close(self)
    os.remove(self.fname)

#### Parallel utilities

def chunk_indices(n, k, prng=Random()):
  """Randomize range [0:n) and partition in k parts as equally as possible."""
  #indices = range(n)# In Python3, output is: range(0, 10), thus it requires list(range(n))
  indices = list(range(n))
  prng.shuffle(indices)
  small, big = n // k, (n + k - 1) // k #n / k, (n + k - 1) / k # in the last version
  partition = []
  last = 0
  for i in range(n % k):# it was range(n % k): in Python2 last version
    partition.append(indices[last:last+big])
    last += big
  for i in range(k - n % k):# it was range(k - n % k): in Python2 last version
    partition.append(indices[last:last+small])
    last += small
  return partition

def spawn(f):
  def fun(parent_pipe, child_pipe, args):
    parent_pipe.close()
    child_pipe.send(f(*args))
    child_pipe.close()
  return fun

def index_to_pos(x, n):
  """Converts a sequential index x into a (i,j) position in an upper triangular
  matrix with size n.
  """
  if n < 1 or x < 0 or x >= n * (n - 1)/2:
    raise ValueError
  i, limit = 0, n - 1
  while x >= limit:
    x -= limit
    i, limit = i + 1, limit - 1
  return i, i + x + 1

def pairs(seq1, seq2, is_upper, seed=None, start=0, stop=1): #old versioon -- stop=None):
  m, n = len(seq1), len(seq2)
  if is_upper:
    assert m == n
    num_pairs = (n * (n - 1)) / 2
  else:
    num_pairs = m * n

  if stop is None:
    stop = num_pairs

  if seed is not None:
    v = range(num_pairs)
    prng = Random(seed)
    prng.shuffle(v)
    indices = v[start:stop]
  else:
    indices = list(range(start, stop))

  for x in indices:
    if is_upper: i, j = index_to_pos(x, n)
    else:        i, j = x / n, x % n

    yield seq1[i], seq2[j]

#### Parallel individual file compression

def compress_sources_worker(sources, compressor, indices):
  return [compressor.compressed_size(sources[i]) for i in indices]

def parallel_compress_sources(sources, compressor, num_proc=mp.cpu_count()):
  """Compress sources in parallel."""
  partition = chunk_indices(len(sources), num_proc)

  pipes = [mp.Pipe() for _ in range(num_proc)]
  args = [(parent_pipe, child_pipe, (sources, compressor, partition[i]))
      for i, (parent_pipe, child_pipe)
      in enumerate(pipes)]
  processes = [mp.Process(target=spawn(compress_sources_worker), args=arg)
      for arg in args]

  # TODO(brunokim): show progress bar
  [p.start() for p in processes]
  results = [parent_pipe.recv() for (parent_pipe, _) in pipes]
  [p.join() for p in processes]

  v = {}
  for indices, proc_result in zip(partition, results):
    for i, result in zip(indices, proc_result):
      v[sources[i].name] = result

  return v

#### Parallel NCD computation for file pairs

csv_dialect = 'excel'

def ncd_pairs_worker(sources1, sources2, compressor, compressed_sizes, tmp_dir,
    pairs_args, interleave_block_size):
  """Computes NCD for a subset of all pairs of sources1 X sources2, as given by
  the pairs function. Stores the results in a CSV temporary file without header."""
  fd, tmpname = tempfile.mkstemp(prefix='shard-', dir=tmp_dir)
  with os.fdopen(fd, 'w') as f:
    writer = csv.DictWriter(f, fieldnames=NcdResult.fields, dialect=csv_dialect)
    for src1, src2 in pairs(sources1, sources2, **pairs_args):
      result = ncd(compressor, src1, src2, compressed_sizes, tmp_dir,
          interleave_block_size)
      writer.writerow(result)
  return tmpname

def join_shards(shard_fnames, tmp_dir=tempfile.gettempdir()):
  """Joins temporary files containing results from NCD calculations, and stores
  it in a CSV temporary filename with header."""
  fd, tmpname = tempfile.mkstemp(prefix='ncd-', dir=tmp_dir)
  with os.fdopen(fd, 'w') as f:
    writer = csv.DictWriter(f, fieldnames=NcdResult.fields, dialect=csv_dialect)
    writer.writeheader()
    for fname in shard_fnames:
      with open(fname, 'r') as shard:
        shutil.copyfileobj(shard, f)
      os.remove(fname)
  return tmpname

def parallel_ncd_pairs(sources1, sources2, compressor, compressed_sizes=None,
    is_upper=True, tmp_dir=tempfile.gettempdir(), num_proc=mp.cpu_count(),
    interleave_block_size=0):

  parent_pipes = []
  processes = []
  for i in range(num_proc):
    m, n = len(sources1), len(sources2)
    if is_upper: num_pairs = (n * (n - 1)) // 2 # it was: / in the version for Python2
    else:        num_pairs = m * n
    pairs_args = {
        'is_upper': is_upper,
        # 'seed': 42, 
        'start': (i * num_pairs) // num_proc, # it was: / in the version for Python2
        'stop':  ((i + 1) * num_pairs) // num_proc # it was: / in the version for Python2
        }
    parent_pipe, child_pipe = mp.Pipe()
    worker_args = (parent_pipe, child_pipe,
      (sources1, sources2, compressor, compressed_sizes, tmp_dir, pairs_args,
       interleave_block_size))
    process = mp.Process(target=spawn(ncd_pairs_worker), args=worker_args)

    parent_pipes.append(parent_pipe)
    processes.append(process)

  # TODO(brunokim): show progress bar
  [p.start() for p in processes]
  shard_fnames = [pipe.recv() for pipe in parent_pipes]
  [p.join() for p in processes]

  tmpname = join_shards(shard_fnames, tmp_dir)
  return TempfileNcdResults(tmpname)

#### Serial computation ####

def serial_compress_sources(sources, compressor):
  # TODO(brunokim): show progress bar
  return dict((source.name, compressor.compressed_size(source))
      for source in sources)

def serial_ncd_pairs(sources1, sources2, compressor, compressed_sizes=None,
    is_upper=True, interleaved_block_size=0):
  # TODO(brunokim): show progress bar
  return InMemoryNcdResults(
      ncd(compressor, src1, src2, compressed_sizes, interleaved_block_size)
      for src1, src2 in pairs(sources1, sources2, is_upper))

#### API calls ####

def compress_sources(sources, compressor, is_parallel=True):
  """Compress every source in a datasource and returns a dict from name to size.
  """
  if is_parallel:
    return parallel_compress_sources(sources, compressor)
  return serial_compress_sources(sources, compressor)

def ncd_pairs(sources1, sources2, compressor, compressed_sizes=None,
    is_upper=True, is_parallel=True, tmp_dir=tempfile.gettempdir(),
    interleave_block_size=0):
  """Calculate NCD for all given datasource pairs.
 
  Returns a NcdResults object, either containing a temporary file name with
  results in CSV format, or a generator for a sequence of results.
  """
  if not is_parallel: 
    return serial_ncd_pairs(sources1, sources2, compressor, compressed_sizes,
        is_upper, interleave_block_size)

  return parallel_ncd_pairs(sources1, sources2, compressor, compressed_sizes,
      is_upper, tmp_dir, interleave_block_size=interleave_block_size)

def distance_matrix(factories, compressor, is_parallel=True,
    verbosity=0, tmp_dir=tempfile.gettempdir(),
    interleave_block_size=0):
  """Calculates matrix of distances between all sources provided by a factory.
  """
  if not factories or len(factories) > 2:
    raise ValueError('Invalid factories argument')

  if len(factories) == 1:
    factory = factories[0]
    sources = sources1 = sources2 = factory.get_sources()
    is_upper = True
  else:
    factory1, factory2 = factories
    sources1, sources2 = factory1.get_sources(), factory2.get_sources()
    sources = sources1 + sources2
    is_upper = False
  
  if verbosity >= 1:
    sys.stderr.write('Compressing individual sources...\n')
  compressed_sizes = compress_sources(sources, compressor, is_parallel)

  if verbosity >= 1:
    sys.stderr.write('Compressing source pairs...\n')
  return ncd_pairs(sources1, sources2, compressor, compressed_sizes,
      is_upper=is_upper, is_parallel=is_parallel, tmp_dir=tmp_dir,
      interleave_block_size=interleave_block_size)

#### I/O and formatting functions ####

def csv_write(outfile, ncd_results, write_header=True):
  """Writes a list of NcdResults in CSV format to outfile.

  @param outfile File-like object as output
  @param ncd_results Output of distance_matrix
  @param write_header Whether a header should be outputted to the CSV file
  """
  if isinstance(ncd_results, TempfileNcdResults):
    with open(ncd_results.get_filename(), 'rt') as f:
      if not write_header:
        f.readline() # Reads header line and discard it
      shutil.copyfileobj(f, outfile)
    return

  results = ncd_results.get_results()
  ncd_base.csv_write(outfile, results, output_header=write_header)

def to_matrix(ncd_results, is_self=True):
  """Converts a list of NcdResult objects to an n x m ndarray of NCD values.

  @param ncd_results List of NcdResult as returned by distance_matrix
  @param is_self Whether the results are from a self-distance computation
  @return (m, ids) distance matrix with corresponding IDs
  """
  xs = [result['x'] for result in ncd_results]
  ys = [result['y'] for result in ncd_results]
  if is_self:
    names = sorted(set(xs + ys))
    ids = [names, names]
  else:
    ids = [sorted(set(xs)), sorted(set(ys))]

  m = np.zeros([len(ids[0]), len(ids[1])])

  for result in ncd_results:
    i, j = ids[0].index(result['x']), ids[1].index(result['y'])
    m[i][j] = result['ncd']

  if is_self:
    m = m + np.transpose(m)

  return m, ids

def safe_truncate(ids, limit=10):
  truncations = list(_id[:limit] for _id in ids)
  freq = frequency(truncations)

  if len(freq) == len(ids):
    return truncations

  conflicts = dict((k, 0) for k, v in freq.items() if v > 1)

  truncs = []
  for i, trunc in enumerate(truncations):
    if trunc not in conflicts:
      truncs.append(trunc)
      continue

    count = conflicts[trunc]
    total = freq[trunc]
    conflicts[trunc] += 1

    # TODO(brunokim): Still unsafe!! It might happen that as we truncate further
    # to append a number other truncations will conflict. For example:
    # [aaaa aaab aaac aaba aabb aabc aaca], limit=3 -> [aa0 aa1 aa2 aa1 aa2 aa3 aac]
    truncs.append('{name:>{cut}.{cut}}{num}'.format(
      name=trunc, cut=limit - num_digits, num=format_num(count, total)))

  return truncs

def write_phylip(outfile, ncd_results, alternative_ids=None):
  """Writes a NcdResults object in Phylip format.
   
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
  m, (ids_x, ids_y) = to_matrix(ncd_results.get_results())
  if alternative_ids:  ids = alternative_ids
  elif ids_x == ids_y: ids = ids_x
  else:                ids = ids_x + ids_y

  names = safe_truncate(ids, 10)

  outfile.write('%d\n' % len(m))
  for name,row in zip(names, m):
    xs = ' '.join('%.15f' % dij for dij in row)
    outfile.write(name + ' ' + xs + '\n')

#### Command-line interface parser ####

def cli_parser():
  """Returns CLI parser for script."""
  parser = argparse.ArgumentParser(add_help=False,
      description='Calculates NCD matrix between objects')

  ncd_group = parser.add_argument_group('NCD options',
      'Options to control NCD inputs and outputs')
  ncd_group.add_argument('--complete', action='store_true',
      help='Performs complete comparison in a single source, not assuming' +
      ' that NCD(x,y) == NCD(y,x) and that NCD(x,x) == 0')
  ncd_group.add_argument('-c', '--compressor', choices=c.list_compressors(),
      default='ppmd', help='Compressor to use (default: ppmd)')
  ncd_group.add_argument('--matrix-format', choices=['raw', 'csv', 'phylip'],
      help='Choose matrix format (default: raw)')

  compressor_group = parser.add_argument_group('Compressor options', 
      'Options to control compressor behavior')
  compressor_group.add_argument('-L', '--level', default=6, type=int,
      help='(zlib, gzip, bz2, bzip2) level of compression (1-9): ' + 
      '1 is faster, 9 is best compression')
  compressor_group.add_argument('-O', '--model-order', default=6, type=int,
      help='(ppmd, paq8) model order, smaller is faster. ppmd: (2-16), paq8: (1-9)')
  compressor_group.add_argument('-M', '--memory', default=10, type=int,
      help='(ppmd) maximum memory, in MiB (1-256)')
  compressor_group.add_argument('-R', '--restoration', default="restart",
      choices=["restart", "cutoff", "freeze"],
      help="(ppmd) restoration method in case of memory exhaustion.")

  return parser

def parse_args(args):
  if len(args.input) == 1:
    factory = create_factory(args.input[0])
    if args.complete: factories = [factory, factory]
    else:             factories = [factory]
  elif len(args.input) == 2:
    factories = [create_factory(args.input[0]), create_factory(args.input[1])]
  else:
    raise ValueError('More than two sources provided')

  compressor = c.get_compressor(args.compressor, level=args.level,
      model_order=args.model_order, memory=args.memory,
      restoration_method=args.restoration)

  return {
      'factories': factories,
      'compressor': compressor,
      'matrix_format': args.matrix_format,
      }

if __name__ == '__main__':
  logging.basicConfig()
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)

  parser = argparse.ArgumentParser(parents=[_utils.cli_parser(), cli_parser()])
  a = parser.parse_args()
  general_args = _utils.parse_args(a)
  ncd_args     = parse_args(a)

  output, is_parallel, verbosity = (general_args['output'],
      general_args['is_parallel'], general_args['verbosity'])
  factories, compressor, matrix_format = (ncd_args['factories'],
        ncd_args['compressor'], ncd_args['matrix_format'])

  ncd_results = distance_matrix(factories, compressor, is_parallel=is_parallel,
      verbosity=verbosity)

  with open_outfile(output) as f:
    csv_write(f, ncd_results, write_header=True)
  ncd_results.close()
