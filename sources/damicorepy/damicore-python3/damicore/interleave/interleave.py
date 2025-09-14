"""Tests interleaving with several block sizes in a small dataset."""

import csv
import os

import datasource as ds
import ncd2 as ncd
import partition as p

from pprint import pformat
from clustering import pipeline
from compressor import get_compressor

if __name__ == '__main__':
  dataset = '../../dataset/binaries'
  dataset_ref = '../../dataset/binaries-membership.csv'
  block_sizes = (
      range(0, 128, 16) +
      range(128, 1024, 128) +
      range(1024, 32768, 1024)) + 
      range(32768-128, 32768+7*128, 128)
  factory = ds.create_factory(dataset)

  # Calculate the distance matrix for each block size
  matrix_dir = 'interleave/matrix'
  if not os.path.isdir(matrix_dir):
    os.makedirs(matrix_dir)

  for block_size in block_sizes:
    fname = os.path.join(matrix_dir, 'block_%d.csv' % block_size)
    if os.path.isfile(fname):
      continue

    print 'Calculating distance matrix for block_size = %d' % block_size
    ncd_results = ncd.distance_matrix([factory, factory],
        get_compressor('zlib'),
        interleave_block_size=block_size)

    with open(fname, 'w') as f:
      ncd.csv_write(f, ncd_results)
 
  # Compute rest of clustering pipeline
  clusters_dir = 'interleave/clusters'
  if not os.path.isdir(clusters_dir):
    os.makedirs(clusters_dir)

  comm_detection_names = ['newman']

  for comm_detection_name in comm_detection_names:
    for block_size in block_sizes:
      out_fname = os.path.join(clusters_dir, 'cluster_%d_%s.csv' % (block_size, comm_detection_name))
      if os.path.isfile(out_fname):
        continue

      print 'Clustering for block_size = %d and community detection method %s' % (block_size, comm_detection_name)
      input_fname = os.path.join(matrix_dir, 'block_%d.csv' % block_size)
      ncd_results = ncd.FilenameNcdResults(input_fname)

      results = pipeline(None, None, ncd_results,
          is_normalize_matrix=True, is_normalize_weights=True, num_clusters=2,
          community_detection_name=comm_detection_name + '-modularity')

      with open(out_fname, 'w') as f:
        membership = results['membership']
        f.write(p.membership_csv_format(membership))

  # Compute partition goodness indices
  partition_dir = 'interleave/partition'
  if not os.path.isdir(partition_dir):
    os.makedirs(partition_dir)

  table_dir = 'interleave/tables'
  if not os.path.isdir(table_dir):
    os.makedirs(table_dir)

  ref_cluster = p.membership_parse(dataset_ref, has_header=True, as_clusters=True)
  for comm_detection_name in comm_detection_names:
    for block_size in block_sizes:
      out_fname = os.path.join(partition_dir, 'indices_%d_%s.csv' % (block_size, comm_detection_name))
      table_fname = os.path.join(table_dir, 'confusion_%d_%s.txt' % (block_size, comm_detection_name))
      if os.path.isfile(out_fname) and os.path.isfile(table_fname):
        continue

      print 'Partition for block_size = %d and community detection method %s' % (block_size, comm_detection_name)
      input_fname = os.path.join(clusters_dir, 'cluster_%d_%s.csv' % (block_size, comm_detection_name))

      with open(out_fname, 'w') as out, open(table_fname, 'w') as tfile:
        clusters = p.membership_parse(input_fname, as_clusters=True)
        table = p.contingency(ref_cluster, clusters)['table']
        # Rotate columsn if they are not sorted in the best way possible.
        if p.matthews(table) < 0:
          (k1, members1), (k2, members2) = clusters.items()
          clusters = {k2: members1, k1: members2}

        d = p.compare_clusters(ref_cluster, clusters, 'all')
        w = csv.writer(out)
        w.writerows(d.items())

        (tp, fp), (fn, tn) = p.contingency(ref_cluster, clusters)['table']
        tfile.write('%3d %3d\n%3d %3d\n' % (tp, fp, fn, tn))

  # Write partition quality indices
  print 'Writing aggregated quality indices...'
  with open('interleave/indices.csv', 'w') as f:
    w = csv.DictWriter(f, ['block_size', 'method',
                           'rand',
                           'adjusted-rand',
                           'jaccard', 
                           'left-wallace',
                           'right-wallace',
                           'adjusted-left-wallace',
                           'adjusted-right-wallace',
                           'fowlkes-mallows',
                           'adjusted-fowlkes-mallows',
                           'mutual-information',
                           'nid',
                           'classification',
                           'incongruence',
                           'normalized-incongruence',
                           'precision', 'recall', 'f1', 'matthews',
                           ])
    w.writeheader()
    for comm_detection_name in comm_detection_names:
      for block_size in block_sizes:
        in_fname = os.path.join(partition_dir, 'indices_%d_%s.csv' % (block_size, comm_detection_name))
        d = {'block_size': block_size, 'method': comm_detection_name}
        with open(in_fname, 'r') as f:
          r = csv.reader(f)
          d.update(r)
        w.writerow(d)

  # Write self distances by block size
  print 'Writing aggregated self distances...'
  with open('interleave/self.csv', 'w') as f:
    w = csv.DictWriter(f, ['block_size'] + os.listdir(dataset))
    w.writeheader()
    for block_size in block_sizes:
      in_fname = os.path.join(matrix_dir, 'block_%d.csv' % block_size)
      d = {'block_size': block_size}
      with open(in_fname, 'r') as f:
        for row in csv.DictReader(f):
          x, y, dist = row['x'], row['y'], row['ncd']
          if x == y:
            d.update({x: dist})
      w.writerow(d)
