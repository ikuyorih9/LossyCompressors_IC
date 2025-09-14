"""Comparison between NCD performance and correctness compared to Complearn's NCD"""

import os
import time
from collections import OrderedDict
from subprocess import Popen, PIPE, call

import datasource as ds
import ncd2 as ncd
import compressor as c
from compressor import which

import numpy as np

if not which('ncd'):
  raise Exception, """
  Complearn's NCD is not available. In Ubuntu, install it with the following command
  to run this benchmark:

  $ sudo apt-get install complearn-tools 
  """


class ComplearnResults(ncd.InMemoryNcdResults):
  def __init__(self, out):
    names = []
    matrix = []
    for line in out.split('\n'):
      tokens = line.split(' ')
      name, values = tokens[0], tokens[1:]
      if name:
        names.append(name)

      row = []
      for v_str in values:
        if v_str:
          v = float(v_str.replace(',', '.'))
          row.append(v)
      if row:
        matrix.append(row)
    
    results = []
    for i, x in enumerate(names):
      for j, y in enumerate(names):
        results.append(ncd.NcdResult(x=x, y=y, ncd=matrix[i][j]))
    ncd.InMemoryNcdResults.__init__(self, results)


def complearn_distance_matrix(dataset, compressor):
  if os.path.isdir(dataset): mode = '-d'
  else:                      mode = '-t'

  c = {'zlib': 'zlib', 'bz2': 'bzlib'}[compressor.name]

  path = which('ncd')
  args = [path, '-c', c, mode, dataset, dataset]

  _, _, _, _, start = os.times()
  process = Popen(args, stdout=PIPE)
  out = process.communicate()[0]
  _, _, _, _, finish = os.times()

  return ComplearnResults(out), finish - start

def half_distance_matrix(dataset, compressor):
  _, _, _, _, start = os.times()
  factory = ds.create_factory(dataset)
  ncd_results = ncd.distance_matrix([factory], compressor)
  _, _, _, _, finish = os.times()
  return ncd_results, finish - start

def full_distance_matrix(dataset, compressor):
  _, _, _, _, start = os.times()
  factory = ds.create_factory(dataset)
  ncd_results = ncd.distance_matrix([factory, factory], compressor)
  _, _, _, _, finish = os.times()
  return ncd_results, finish - start

def run(datasets=['../../examples/texts'], compressors=['zlib'], repeats=5):
  res = []
  for dataset in datasets:
    for compressor in compressors:
      b_full, b_half, b_complearn = run_instance(dataset, compressor, repeats)
      d = OrderedDict([
        ('dataset', dataset),
        ('compressor', compressor),
        ('compare', compare_benchs(b_full, b_complearn)),
      ])
      for b in b_full, b_half, b_complearn:
        name, times = b['bench'], b['times']
        d.update([
          (name, describe(times)),
          (name + '-normal?', normal(times)),
          (name + '-times', times),
        ])
      res.append(d)
  return res

def run_instance(dataset, compressor_name, repeats):
  print 'Benchmarking NCD for dataset %s with compressor %s...' % (dataset, compressor_name)
  compressor = c.get_compressor(compressor_name)

  benchs = [
      {'bench': 'full-ncd2', 'func': full_distance_matrix},
      {'bench': 'half-ncd2', 'func': half_distance_matrix},
      {'bench': 'complearn', 'func': complearn_distance_matrix},
  ]

  for b in benchs:
    bench, func = b['bench'], b['func']
    print 'Benchmarking %s...' % bench
    times = []
    for _ in xrange(repeats):
      res, time = func(dataset, compressor)
      results = list(res.get_results())
      res.close()
      times.append(time)
      print '\t%.3lf seconds' % time
    b.update(times=times, results=results)

    fname = "benchmarks/matrix/%s-%s-%s.csv" % (os.path.basename(dataset), compressor_name, b['bench'])
    with open(fname, 'w') as f:
      ncd.csv_write(f, ncd.InMemoryNcdResults(results))

  return benchs

from scipy import stats, linalg

def describe(a):
  size, (min_value, max_value), mean, var, skewness, kurtosis = stats.describe(a, axis=None)
  return OrderedDict([
      ('size', size),
      ('min', min_value),
      ('max', max_value),
      ('mean', mean),
      ('var', var),
      ('skewness', skewness),
      ('kurtosis', kurtosis),
  ])

def normal(times):
  k2, p = stats.normaltest(times)
  return p

def compare_benchs(bench_full, bench_complearn):
  mat_full,      _ = ncd.to_matrix(bench_full['results'], is_self=False)
  mat_complearn, _ = ncd.to_matrix(bench_complearn['results'], is_self=False)

  # ncd2 calculates the self distance, but CompLearn defaults to zero.
  # Also, CompLearn outputs the matrix transposed in comparison.
  for i in xrange(len(mat_full)):
    mat_full[i][i] = 0.0
  mat_full = np.transpose(mat_full)

  difference = mat_full - mat_complearn
  name_full,  name_complearn  = bench_full['bench'], bench_complearn['bench']
  times_full, times_complearn = bench_full['times'], bench_complearn['times']
  t, p = stats.ttest_ind(times_full, times_complearn)
  
  return OrderedDict([
      ('frobenius', linalg.norm(difference, 'fro')),
      ('difference', describe(difference)),
      ('t-test', p),
  ])

