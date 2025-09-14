"""Execute benchmarks"""

import os
import csv

from benchmarks import complearn

if __name__ == '__main__':
  res = complearn.run(
      datasets=[
        '../../dataset/Wikipedia-sample',
        '../../dataset/TCL-sample',
        '../../dataset/EuroGOV-sample',
#         'testdata/planets',
      ],
      compressors=['zlib', 'bz2'],
      repeats=30)
  for r in res:
    dataset, compressor, compare = r['dataset'], r['compressor'], r['compare']
    del r['dataset']; del r['compressor']; del r['compare']

    fname = 'benchmarks/results/%s-%s.csv' % (
        os.path.basename(dataset),
        compressor)
    with open(fname, 'w') as f:
      w = csv.DictWriter(f, ['key', 'value'])
      w.writeheader()
      for k, v in compare.items() + r.items():
        if k.endswith('-times'):
          continue
        if not isinstance(v, dict):
          w.writerow({'key': k, 'value': v})
        else:
          for k1, v1 in v.items():
            w.writerow({'key': "%s-%s" % (k, k1), 'value': v1})
    
    for k, v in r.items():
      if k.endswith('-times'):
        fname = 'benchmarks/times/%s-%s-%s.csv' % (
            os.path.basename(dataset),
            compressor,
            k.replace('-times', ''))
        with open(fname, 'w') as f:
          for time in v:
            f.write('%.3lf\n' % time)
