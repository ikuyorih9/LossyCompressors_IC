#!/usr/bin/python

import os
import sys
import shutil
import argparse
import random
import csv
import warnings

import itertools as it
from random import Random
from pprint import pprint

import _utils
import dataset
import ncd2 as ncd
import tree_simplification as nj
import partition as p
from _utils import choose_most_frequent, mean, transpose, open_outfile

def cat(srcs, dest, srcdir=None):
  with open(dest, 'a') as f:
    for src in srcs:
      fname = src if srcdir is None else os.path.join(srcdir, src)
      with open(fname, 'rb') as s:
        f.write(s.read())

def get_split(t):
  left, right = t.children()

  # @: root, +: Node, O: Leaf
  #
  #     Case 1          Case 2
  # A---x-@-y---D   A-@-x---y---D
  #     |   |           |   |
  #     B   C           B   C
  is_leaf = lambda node: not node.children()

  if not is_leaf(left) and not is_leaf(right):
    # Case 1
    a, b = left.children()
    c, d = right.children()
  else:
    # Case 2
    if is_leaf(left): a, x = left, right
    else:             a, x = right, left

    x1, x2 = x.children()
    if is_leaf(x1):   b, y = x1, x2
    else:             b, y = x2, x1

    c, d = y.children()

  sort_pair = lambda u, v: (u, v) if u < v else (v, u) 
  X = sort_pair(a.content, b.content)
  Y = sort_pair(c.content, d.content)
  split = sort_pair(X, Y)

  return split

#### Distance definitions

def point_to_set_distances(x, s, distances):
  ds = []
  for y in s:
    ds.append(distances[x][y])
  return ds

def set_to_set_distances(s1, s2, distances):
  m = []
  for x in s1:
    row = []
    for y in s2:
      row.append(distances[x][y])
    m.append(row)
  return m

def point_to_set_distance(dist, x, s, distances):
  ds = point_to_set_distances(x, s, distances)
  if dist == 'min': return min(ds)
  if dist == 'max': return max(ds)
  if dist == 'avg' or dist == 'mean': return mean(ds)
  raise ValueError, 'Unknown dist type %s! Available: [min, max, avg]' % dist

def set_to_set_distance(dist, s1, s2, distances):
  m = set_to_set_distances(s1, s2, distances)
  if dist == 'min': return min(min(row) for row in m)
  if dist == 'h' or dist == 'directed-hausdorff':
    return max(min(row) for row in m)
  if dist == 'H' or dist == 'hausdorff':
    d1 = max(min(row) for row in m)
    d2 = max(min(col) for col in zip(*m))
    return max(d1, d2)
  raise ValueError, ('Unknown dist type %s! ' + 
      'Available: [min, directed-hausdorff, hausdorff]' % dist)

def make_distance_matrix(x, U, V, distances,
    choice_method='random', point_to_set='min', set_to_set='H', prng=None):
  if not prng: prng = Random()
  i = prng.randrange(0, len(U))
  u = U.pop(i)

  d_UV = set_to_set_distance(set_to_set, U, V, distances)
  d_Uu = point_to_set_distance(point_to_set, u, U, distances)
  d_Ux = point_to_set_distance(point_to_set, x, U, distances)
  d_Vu = point_to_set_distance(point_to_set, u, V, distances)
  d_Vx = point_to_set_distance(point_to_set, x, V, distances)
  d_ux = distances[u][x]
  
  U.insert(i, u)
  return [
      [0.0,  d_UV, d_Uu, d_Ux],
      [d_UV, 0.0,  d_Vu, d_Vx],
      [d_Uu, d_Vu, 0.0,  d_ux],
      [d_Ux, d_Vx, d_ux, 0.0]]

single_split = {
    (('U', 'x'), ('V', 'u')): 'positive',
    (('U', 'u'), ('V', 'x')): 'negative',
    (('U', 'V'), ('u', 'x')): 'neutral',
    }

proof_case = {
    (('U', 'x'), ('V', 'u')): 'strong proof',
    (('U', 'u'), ('V', 'x')): 'weak counter',
    (('U', 'V'), ('u', 'x')): 'inconclusive',
    }

counter_case = {
    (('U', 'x'), ('V', 'v')): 'weak proof',
    (('U', 'v'), ('V', 'x')): 'strong counter',
    (('U', 'V'), ('v', 'x')): 'inconclusive',
    }

conclusion_matrix = {
    ('strong proof', 'weak proof'):     'strong proof',
    ('strong proof', 'strong counter'): 'strong error',
    ('strong proof', 'inconclusive'):   'neutral proof',
    ('weak counter', 'weak proof'):     'weak error',
    ('weak counter', 'strong counter'): 'strong counter',
    ('weak counter', 'inconclusive'):   'weak counter',
    ('inconclusive', 'weak proof'):     'weak proof',
    ('inconclusive', 'strong counter'): 'neutral counter',
    ('inconclusive', 'inconclusive'):   'inconclusive',
    }

def quartet_test(references, test, membership, distances,
    use_counterproof=False, dist_args={}):
  """Tests whether an instance belongs to each cluster."""
  classification = {}
  clusters = p.membership_to_clusters(membership)
  for cluster, members in clusters.items():
    category = {'proof': [], 'counter': []}
    for ref in references:
      if ref in members: category['proof'].append(ref)
      else:              category['counter'].append(ref)
    
    U, V = category['proof'], category['counter']
    if len(U) <= 1 or len(V) <= 1:
      conclusion = 'neutral' if not use_counterproof else 'inconclusive'
      classification[cluster] = conclusion
      continue

    proof_matrix = make_distance_matrix(test, U, V, distances, **dist_args)
    proof_tree = nj.neighbor_joining(proof_matrix, ['U', 'V', 'u', 'x'])

    if not use_counterproof:
      conclusion = single_split[get_split(proof_tree)]
    else:
      counter_matrix = make_distance_matrix(test, V, U, distances, **dist_args)
      counter_tree = nj.neighbor_joining(proof_matrix, ['V', 'U', 'v', 'x'])

      proof = proof_case[get_split(proof_tree)]
      counter = counter_case[get_split(counter_tree)]
      conclusion = conclusion_matrix[(proof, counter)]

    classification[cluster] = conclusion
  return classification

def quartet_classifier_with_counterproof(references, tests, membership, distances,
    dist_args={}):
  classes = {}
  for test in tests:
    classification = quartet_test(references, test, membership, distances,
        use_counterproof=True, dist_args=dist_args)

    # Get strongest proof
    conclusions = transpose(classification)
    print test, conclusions

    trust = 3
    for conclusion in ['strong proof', 'neutral proof', 'weak proof']:
      clusters = conclusions.get(conclusion)
      if clusters:
        if len(clusters) == 1:
          clusters = clusters[0]
        break
      trust -= 1
    
    classes[test] = {'class': clusters, 'trust': trust}
  return classes

def vote_analysis(classification):
  n = len(classification)
  conclusions = transpose(classification)
  positives = conclusions.get('positive', [])
  negatives = conclusions.get('negative', [])
  neutrals  = conclusions.get('neutral', [])
  num_positives = len(positives)
  num_negatives = len(negatives)
  num_neutrals  = len(neutrals)

  # Compute trust in a result
  if num_positives <= 1 and num_negatives < n:
    trust = float(num_positives + num_negatives) / n
  else:
    trust = -float(abs(num_positives - num_negatives)) / n

  # Inconclusive
  if num_neutrals == n or num_negatives == n:
    return {'class': None, 'trust': trust}

  # Positive classification
  if num_positives == 1:
    return {'class': positives[0], 'trust': trust}

  # Classification by elimination
  if num_positives == 0 and num_neutrals == 1:
    return {'class': neutrals[0], 'trust': trust}

  # Classification error: conflicting positives
  if num_positives > 1:
    return {'class': positives, 'trust': trust}

  # Classification error: no positives
  return {'class': neutrals, 'trust': trust}

def quartet_classifier(references, tests, membership, distances, dist_args={}):
  classes = {}
  for test in tests:
    classification = quartet_test(references, test, membership, distances,
        use_counterproof=False, dist_args=dist_args)
    classes[test] = vote_analysis(classification)
  return classes

def self_distances_by_class(references, self_distances, membership):
  membership = p.filter_membership(membership, references)
  clusters = p.membership_to_clusters(membership)
  
  distances = {}
  for x in references:
    ref_distances = {}
    for cluster, members in clusters.items():
      ref_distances[cluster] = [self_distances[x][y] for y in members if x != y]
    distances[x] = ref_distances
  return distances

def cross_distances_by_class(tests, cross_distances, membership):
  references = cross_distances.keys()
  membership = p.filter_membership(membership, references)
  clusters = p.membership_to_clusters(membership)

  distances = {}
  for y in tests:
    test_distances = {}
    for cluster, members in clusters.items():
      test_distances[cluster] = [cross_distances[x][y] for x in members]
    distances[y] = test_distances
  return distances

def distances_to_classes(distances_by_class, dist_fn=min):
  distance = {}
  for x, cluster_distances in distances_by_class.items():
    distance[x] = {}
    for cluster, distances in cluster_distances.items():
      distance[x][cluster] = dist_fn(distances)
  return distance

def transpose_matrix(m):
  """{first: [a b c d e], vowels: [a e i o u]} -> 
    {a: [first vowels], b: [first], c: [first], d: [first],
     e: [first vowels], i: [vowel], o: [vowel], u: [vowel]}"""
  d = {}
  for k, vs in m.items():
    for v in vs:
      if v not in d: d[v] = [k]
      else:          d[v].append(k)
  return d

def knn(k, distances_by_class):
  classes = {}
  for y, cluster_distances in distances_by_class.items():
    clusters_by_distance = transpose_matrix(cluster_distances)
    sorted_by_distance = sorted(clusters_by_distance.items())
    cluster_lists = [cluster_list for dist, cluster_list in sorted_by_distance]

    closest = cluster_lists[:k]
    clusters = it.chain(*closest)
    klass = choose_most_frequent(clusters, just_one=False)
    if len(klass) == 1: klass = klass[0]

    classes[y] = {'class': klass, 'trust': 1.0}
  return classes

def update_distance_matrix(m, results, is_symmetric=True):
  for result in results:
    x, y, dist = result['x'], result['y'], result['ncd']
    if not m.has_key(x): m[x] = {}
    m[x][y] = dist
    if is_symmetric:
      if not m.has_key(y): m[y] = {}
      m[y][x] = dist

def calc_distances(ref_factory, test_factory, compressor, ncd_args={}):
  distances = {}

  if verbosity >= 1:
    sys.stderr.write('Computing NCD from references to themselves...\n')
  self_results = ncd.distance_matrix([ref_factory], compressor, **ncd_args)
  results1 = list(self_results.get_results())
  update_distance_matrix(distances, results1)

  if verbosity >= 1:
    sys.stderr.write('Computing NCD from references to test instances...\n')
  cross_results = ncd.distance_matrix([ref_factory, test_factory], compressor,
      **ncd_args)

  results2 = list(cross_results.get_results())
  update_distance_matrix(distances, results2)

  return {
      'distances': distances,
      'self_results': results1,
      'cross_results': results2
      }

def pipeline(membership, factories=None, compressor=None, ncd_results=None,
    classifier_name='quartet', k=None, ncd_args={}, dist_args={}):

  if not ncd_results:
    ref_factory, test_factory = factories
    ref_names  = [source.name for source in ref_factory.get_sources()]
    test_names = [source.name for source in test_factory.get_sources()]
    result = calc_distances(ref_factory, test_factory, compressor, ncd_args)
    distances, self_results, cross_results = (result['distances'],
        result['self_results'], result['cross_results'])
  else:
    if len(ncd_results) == 1:
      self_results = []
      cross_results = list(ncd_results[0].get_results())
    else:
      self_ncd_results, cross_ncd_results = ncd_results
      self_results = list(self_ncd_results.get_results())
      cross_results = list(cross_ncd_results.get_results())
    distances = {}
    update_distance_matrix(distances, self_results)
    update_distance_matrix(distances, cross_results)

    ref_names = set(result['x'] for result in cross_results)
    test_names = set(result['y'] for result in cross_results)

  if verbosity >= 1:
    sys.stderr.write('Classify test elements...\n')
  if classifier_name == 'quartet':
    classes = quartet_classifier(ref_names, test_names, membership, distances,
        dist_args)
  elif classifier_name == 'use_counterproof':
    classes = quartet_classifier_with_counterproof(ref_names, test_names,
        membership, distances, dist_args)
  else:
    cross_distances = {}
    update_distance_matrix(cross_distances, cross_results, is_symmetric=False)
    classes = knn(k, cross_distances_by_class(test_names, cross_distances, membership))

  return {
      'distances': distances,
      'self_results': self_results,
      'cross_results': cross_results,
      'classes': classes,
      }

def parse_args(args):
  is_classify = not args.no_classify
  is_preprocess = args.split or args.sample
  return {
      'is_preprocess': is_preprocess, 
      'is_classify': is_classify
      }

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      parents=[_utils.cli_parser(), ncd.cli_parser(), dataset.cli_parser()],
      description='Classify test objects given a reference using NCD')

  parser.add_argument('--source-mode', action='store_true',
      help='Calculate NCD distance matrix for the provided sources (default)')
  parser.add_argument('--matrix-mode', action='store_true',
      help='Uses an already calculated NCD matrix in raw format')

  parser.add_argument('membership',
      help="Membership file for reference instances")
  parser.add_argument('--use-counterproof', action='store_true',
      help="Whether to use counterproof classifier")
  parser.add_argument('-k', type=int,
      help="Uses k-NN with the given parameter as classifier")
  parser.add_argument('--no-classify', action='store_true', 
      help="Does not classify, only performs preprocessing.")
  parser.add_argument('--partition-index', choices=p.list_indices(),
      help="Compares obtained classification with the reference membership" +
      "with the provided index")

  a = parser.parse_args()
  general_args = _utils.parse_args(a)
  dataset_args = dataset.parse_args(a)
  class_args = parse_args(a)
  output, is_parallel, verbosity = (general_args['output'],
      general_args['is_parallel'], general_args['verbosity'])
  sample, split, num_parts, dest_type, dest_dir = (dataset_args['sample'],
      dataset_args['split'], dataset_args['num_parts'],
      dataset_args['dest_type'], dataset_args['dest_dir'])
  is_preprocess, is_classify = (class_args['is_preprocess'],
      class_args['is_classify'])
 
  if a.matrix_mode:
    factories = compressor = None
    ncd_results = [ncd.FilenameNcdResults(results_fname)
        for results_fname in a.input]
  else:
    ncd_results = None
    ncd_args = ncd.parse_args(a)
    factories, compressor, matrix_format = (ncd_args['factories'],
        ncd_args['compressor'], ncd_args['matrix_format'])

  membership = p.membership_parse(a.membership, has_header=True)

  if not (is_preprocess or is_classify):
    warnings.warn("Nothing to do...")
    exit()

  if is_preprocess:
    dataset.pipeline(factories, membership, **dataset_args)

  if not is_classify:
    exit()

  if factories and len(factories) != 2:
    raise ValueError, 'Reference and test datasets not provided'
  if ncd_results and len(ncd_results) > 2:
    raise ValueError, ('More than two NCD results provided (expected either' + 
        ' single cross results, or self results)')

  ncd_args = {'is_parallel': is_parallel, 'verbosity': verbosity}
  dist_args = {
      'choice_method': 'random',
      'point_to_set': 'min',
      'set_to_set': 'hausdorff',
      'prng': Random(1)}

  classifier_name = 'knn' if a.k else 'use_counterproof' if a.use_counterproof else 'quartet'

  result = pipeline(membership,
      factories=factories, compressor=compressor,
      ncd_results=ncd_results,
      classifier_name=classifier_name, k=a.k,
      ncd_args=ncd_args, dist_args=dist_args)
  distances, self_results, cross_results, classes = (result['distances'],
      result['self_results'], result['cross_results'], result['classes'])

  with open_outfile(output) as f:
    writer = csv.DictWriter(f, fieldnames=['name','class','trust'])
    writer.writeheader()
    writer.writerows(dict(classification, name=name)
        for name, classification in classes.items())
  
  if a.partition_index:
    missing = set(name
        for name, classification in classes.items()
        if not classification['class'])
    conflicts = set(name
        for name, classification in classes.items()
        if isinstance(classification['class'], list))
    obtained_membership = dict((name, classification['class'])
        for name, classification in classes.items()
        if name not in missing and name not in conflicts)

    print '\n%d missing class, %d conflicts, %d classified' % (
        len(missing), len(conflicts), len(obtained_membership))
    test_membership = p.filter_membership(membership, obtained_membership.keys())
    pprint(p.compare_clusters(
        p.membership_to_clusters(test_membership),
        p.membership_to_clusters(obtained_membership),
        index_name=a.partition_index))
