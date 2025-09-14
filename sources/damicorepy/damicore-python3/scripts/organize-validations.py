#!/usr/bin/python2.7

import os
import csv

def organize(directory, output):
  with open(output, 'w') as out:
    writer = csv.DictWriter(out, [
      'dataset', 'compressor', 'classifier',
      'total', 'classified',
      'nid',
      'classification',
      'normalized-incongruence',
      'mutual-information',

      'rand', 'adjusted-rand',
      'jaccard',
      'left-wallace', 'right-wallace',
      'adjusted-left-wallace', 'adjusted-right-wallace',
      'fowlkes-mallows', 'adjusted-fowlkes-mallows',
      'incongruence',
    ])
    writer.writeheader()

    for name in os.listdir(directory):
      fname = os.path.join(directory, name)
      if os.path.isdir(fname):
        continue
      print directory, name
      dataset, compressor, classifier, _ = name.split('_')

      with open(fname) as f:
        reader = csv.reader(f)
        row = dict((name, value) for name, value in reader)
        row.update({
          'dataset': dataset,
          'compressor': compressor,
          'classifier': classifier,
        })
        writer.writerow(row)

if __name__ == '__main__':
  organize('../../results/validation', '../../results/validation.csv')
  organize('../../results/easy_validation', '../../results/easy_validation.csv')
