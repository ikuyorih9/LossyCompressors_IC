# -*- encoding: utf-8 -*-

import csv

import numpy as np
import matplotlib.pyplot as plt

from collections import OrderedDict

if __name__ == '__main__':
  d = OrderedDict()
  for block_size in [0, 2**4, 2**8, 2**12, 2**15]:
    fname = 'interleave/matrix/block_%d.csv' % block_size
    with open(fname, 'r') as f:
      r = csv.DictReader(f)
      vs = [float(row['ncd']) for row in r if row]
    d[block_size] = vs

  fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(nrows=3, ncols=2, sharex=True, sharey=True)
  all_axes = [ax1, ax2, ax3, ax4, ax5, ax6]

  for ax, (b, vs) in zip(all_axes, d.items()):
    ax.set_yscale('log')
    ax.set_ylim((1, 80*80))
    ax.hist(vs, bins=11, range=(0, 1.1))

  fig.savefig('interleave/dist.svg')
