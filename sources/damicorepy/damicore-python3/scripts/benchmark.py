#!/usr/bin/python

import os, sys
from time import time
from pprint import pprint
import csv

import damicore.datasource as ds
import damicore.compressor as c
import damicore.ncd2 as ncd
from damicore.progress_bar import ProgressBar

def main():
  sys.path.append('paq8/')

  num_repeat = 30
  compressor_names = ['zlib', 'gzip', 'bzip2', 'ppmd']
  factory = ds.DirectoryFactory('examples/newsgroups')

  #sys.stderr = open('/dev/null', 'w') # Redirect stderr to devnull
  progress = ProgressBar(num_repeat * len(compressor_names), stream=sys.stdout)

  with open('scripts/benchmark.csv', 'wt') as f:
    writer = csv.DictWriter(f, fieldnames=['compressor', 'run', 'time'])
    writer.writeheader()
    for repeat in xrange(num_repeat):
      for compressor_name in compressor_names:
        compressor = c.get_compressor(compressor_name)
        start = time()
        ncd.distance_matrix(factory, compressor, is_parallel=True)
        end = time()
        writer.writerow({
          'compressor': compressor_name,
          'run': repeat,
          'time': end - start})
        progress.increment()
    print

if __name__ == '__main__':
  main()
