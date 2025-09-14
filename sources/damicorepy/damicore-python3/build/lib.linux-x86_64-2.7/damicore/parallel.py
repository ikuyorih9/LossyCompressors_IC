"""Parallel implementation of NCD algorithms.

You shouldn't call these functions directly. Instead, call those from
ncd2 with parameter is_parallel=True.
"""

import os
import shutil
import tempfile
import csv
from random import Random
import multiprocessing as mp

from ncd2 import ncd

def chunk_indices(n, k, prng=Random()):
  """Randomize range [0:n) and partition in k parts.
  
  The last part might contain more elements if k is not a divisor of n.
  
  >>> chunk_indices(20, 4, prng=Random(42))
  [[15, 8, 6, 7, 9], [16, 13, 14, 17, 2], [18, 5, 1, 19, 10], [11, 3, 4, 0, 12]]
  >>> chunk_indices(22, 4, prng=Random(42))
  [[18, 7, 9, 6, 16], [8, 3, 10, 15, 12], [17, 2, 20, 19, 1], [21, 11, 13, 4, 5, 0, 14]]
  """
  indices = range(n)
  prng.shuffle(indices)
  step = n / k
  partition = [indices[i * step:(i + 1) * step] for i in xrange(k - 1)]
  partition.append(indices[(k - 1) * step:])

  return partition

def spawn(f):
  def fun(parent_pipe, child_pipe, args):
    parent_pipe.close()
    child_pipe.send(f(*args))
    child_pipe.close()
  return fun

#### Compress individual files

def compress_sources_worker(sources, compressor, indices):
  return [compressor.compressed_size(sources[i]) for i in indices]

def compress_sources(sources, compressor, num_proc=mp.cpu_count()):
  """Compress sources in parallel."""
  partition = chunk_indices(len(sources), num_proc)

  pipes = [mp.Pipe() for _ in xrange(num_proc)]
  args = [(parent_pipe, child_pipe, (sources, compressor, partition[i]))
      for i, (parent_pipe, child_pipe)
      in enumerate(pipes)]
  processes = [mp.Process(target=spawn(compress_sources_worker), args=arg)
      for arg in args]

  # TODO(brunokim): Print progress bar
  [p.start() for p in processes]
  results = [parent_pipe.recv() for (parent_pipe, _) in pipes]
  [p.join() for p in processes]

  v = {}
  for indices, proc_result in zip(partition, results):
    for i, result in zip(indices, proc_result):
      v[sources[i].name] = result

  return v

#### Compute NCD for file pairs

def ncd_pairs_worker(source_pairs, compressor, indices, compressed_sizes):
  fd, tmpname = tempfile.mkstemp(prefix='shard-')
  with os.fdopen(fd, 'w') as f:
    # TODO(brunokim): Extract this to a common place, avoiding a circular
    # dependency with ncd2
    writer = csv.DictWriter(f, fieldnames=['x', 'y', 'zx', 'zy', 'zxy', 'ncd'])
    for i in indices:
      ds1, ds2 = source_pairs[i]
      result = ncd(compressor, ds1, ds2, compressed_sizes)
      writer.writerow(result)
  return tmpname

def join_shards(shard_fnames):
  fd, tmpname = tempfile.mkstemp(prefix='ncd-')
  with os.fdopen(fd, 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['x', 'y', 'zx', 'zy', 'zxy', 'ncd'])
    writer.writeheader()
    for fname in shard_fnames:
      with open(fname, 'r') as shard:
        shutil.copyfileobj(shard, f)
      os.remove(fname)
  return tmpname

def ncd_pairs(source_pairs, compressor, compressed_sizes=None,
    num_proc=mp.cpu_count()):
  source_pairs = list(source_pairs)
  partition = chunk_indices(len(source_pairs), num_proc)

  pipes = [mp.Pipe() for _ in xrange(num_proc)]
  args = [(parent_pipe, child_pipe,
      (source_pairs, compressor, partition[i], compressed_sizes))
      for i, (parent_pipe, child_pipe)
      in enumerate(pipes)]
  processes = [mp.Process(target=spawn(ncd_pairs_worker), args=arg)
      for arg in args]

  # TODO(brunokim): Print progress bar
  [p.start() for p in processes]
  shard_fnames = [parent_pipe.recv() for (parent_pipe, _) in pipes]
  [p.join() for p in processes]

  tmpname = join_shards(shard_fnames)
  return tmpname

