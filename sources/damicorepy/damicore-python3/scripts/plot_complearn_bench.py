# -*- encoding: utf-8 -*-
"""Plots result for CompLearn benchmark."""

import os
import csv
import math
import re

from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

times_dir = 'damicore/benchmarks/times'
figs_dir = '../thesis/images'
datasets = ['Wikipedia', 'TCL', 'EuroGOV']

def read_times(fname):
  vs = []
  with open(fname) as f:
    for line in f:
      v_str = line[:-1]
      if v_str:
        vs.append(float(v_str))
  return vs

def read_all_times(directory):
  res = []
  fnames = os.listdir(directory)
  for fname in fnames:
    parts = re.split('-|\.', fname) # split by '-' or '.'
    dataset, compressor, impl = parts[0], parts[2], parts[3]
    if dataset not in datasets:
      continue

    times = read_times(os.path.join(directory, fname))
    res.append({
      'dataset': dataset,
      'compressor': compressor, 
      'impl': impl,
      'times': times,
    })
  return res

if __name__ == '__main__':
  from pprint import pprint
  ts = read_all_times(times_dir)
  pprint(ts, width=300)

  data = OrderedDict() 
  for compressor in ['zlib', 'bz2']:
    data[compressor] = OrderedDict()
    for impl in ['half', 'full', 'complearn']:
      data[compressor][impl] = OrderedDict()
      for v in ['ys', 'err', 'times']:
        data[compressor][impl][v] = [0 for _ in xrange(3)]

  for t in ts:
    _, _, mean, var, _, _ = stats.describe(t['times'])
    by_compressor = data[t['compressor']]
    by_impl = by_compressor[t['impl']]
    i = datasets.index(t['dataset'])

    by_impl['ys'][i] = mean
    by_impl['err'][i] = math.sqrt(var)
    by_impl['times'][i] = t['times']

  pprint(data)

  for compressor, by_compressor in data.items():
    num_impl = len(by_compressor)
    fig, axes = plt.subplots(figsize=(7,2), ncols=num_impl, sharey=True, squeeze=True)
    for i, (ax, (impl, by_impl)) in enumerate(zip(axes, by_compressor.items())):
      ax.plot([1, 2, 3], by_impl['ys'], marker='*')
      bp = ax.boxplot(by_impl['times'], patch_artist=True)
      plt.setp(bp['boxes'], color='black', alpha=0.5)
      plt.setp(bp['whiskers'], color='black')
      plt.setp(bp['fliers'], color='red', marker='+')

      ax.set_xticklabels(datasets, size=8)
      ax.set_yticklabels(range(0, 70, 10), size=8)
      
      ax.set_title({
        'half': 'ncd2 parcial',  
        'full': 'ncd2 completa',  
        'complearn': 'CompLearn',  
      }[impl], fontsize=10)
      if i == 0:
        ax.set_ylabel(u'Tempo de execução (s)', fontsize=8)
      if i == num_impl/2:
        ax.set_xlabel('Datasets', fontsize=10)

    fig.savefig(os.path.join(figs_dir, 'time-%s.pdf' % compressor))
