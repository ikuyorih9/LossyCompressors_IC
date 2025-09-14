#!/usr/bin/python

import argparse
import csv
import math
import re
import sys
import warnings
import itertools as it

from io import StringIO
from pprint import pprint
from collections import OrderedDict

from damicore._utils import safediv, get_version, format_num

#### Conversion functions ####

def membership_to_clusters(membership):
  """Converts a membership map to a clusters map.
  
  >>> m = {'rat':'mammal', 'fly':'insect', 'cat':'mammal'}
  >>> membership_to_clusters(m)
  {'mammal': set(['rat','cat']), 'insect': set(['fly'])}
  """
  clusters = {}
  for member, cluster in membership.items():
    if cluster not in clusters:
      clusters[cluster] = set([member])
    else:
      clusters[cluster].add(member)
  return clusters

def clusters_to_membership(clusters):
  """Converts a membership map to a clusters map.
  
  >>> c = {'mammal':['rat','cat'], 'insect':['fly']}
  >>> clusters_to_membership(c)
  {'rat':'mammal', 'cat':'mammal', 'fly':'insect'}
  """
  membership = {}
  for cluster, members in clusters.items():
    for member in members:
      membership[member] = cluster
  return membership

def filter_membership(membership, subset):
  """Filter membership with members from the subset."""
  return dict((name, cluster)
      for name, cluster in membership.items()
      if name in subset)

def clusters_intersection(cluster1, cluster2, warn=False):
  """Filters each cluster to only the elements they both contain.
  
  If the clusters contain the same elements, returns the clusters.
  """
  m1, m2 = clusters_to_membership(cluster1), clusters_to_membership(cluster2)
  els1, els2 = set(m1.keys()), set(m2.keys())
  if els1 == els2:
    return cluster1, cluster2

  subset = els1.intersection(els2)
  M1 = filter_membership(m1, subset)
  M2 = filter_membership(m2, subset)
  C1 = membership_to_clusters(M1)
  C2 = membership_to_clusters(M2)

  if warn:
    warnings.warn("""
    Clusters have elements not in common, changed to their intersection.
    cluster1: (%3d elements, %3d clusters) -> (%3d elements, %3d clusters)
    cluster2: (%3d elements, %3d clusters) -> (%3d elements, %3d clusters)
    """ % (len(m1), len(cluster1), len(M1), len(C1),
           len(m2), len(cluster2), len(M2), len(C2)),
    stacklevel=2)
  return C1, C2

def clusters_trim(cluster1, cluster2):
  """Trim clusters only to their shared groups."""
  cs1, cs2 = set(cluster1.keys()), set(cluster2.keys())
  if cs1 == cs2:
    return cluster1, cluster2

  subset = cs1.intersection(cs2)
  C1 = dict((name, members) for name, members in cluster1.items() if name in subset)
  C2 = dict((name, members) for name, members in cluster2.items() if name in subset)
  return C1, C2

def clusters_total(cluster1, cluster2):
  """Total elements in common between clusters"""
  m1, m2 = clusters_to_membership(cluster1), clusters_to_membership(cluster2)
  subset = set(m1.keys()) & set(m2.keys())
  M1 = filter_membership(m1, subset)
  M2 = filter_membership(m2, subset)
  return len(set(m1.keys()) & set(m2.keys()))

#### Contingency matrix functions ####

def contingency(p1, p2):
  """Returns the contingency matrix between partitions (cluster sets).
  
  The contingency matrix (or confusion matrix) gives the number of elements
  in common between each cluster of a partition. Corresponding partitions can
  then be found by looking for those with a high number of matches and/or few
  disagreements.
  
  >>> p1 = {"mammals": ['rat','cat','bat','dog','panda'],
  ... "insects": ['fly','mosquito','lice']}
  >>> p2 = {"herbivore": ['rat', 'fly','panda'], "carnivore": ['cat','dog'],
  ... "hemovore": ['bat','mosquito','lice']}
  >>> contingency(p1, p2)
  {"keys1": ['mammals', 'insects'],
   "keys2": ['herbivore', 'carnivore', 'hemovore']
   "intersections": [[set(['rat','panda']), set(['cat','dog']), set(['bat'])]
                     [set(['fly']), set([]), set(['mosquito','lice'])]]
   "table": [[2, 2, 1],
             [1, 0, 2]]}
  """
  p1, p2 = clusters_intersection(p1, p2, warn=True)
  
  m, n = len(p1), len(p2)
  ks1, ks2 = sorted(p1.keys()), sorted(p2.keys())
  intersections = [[None for _ in range(n)] for _ in range(m)]

  for i,k1 in enumerate(ks1):
    for j,k2 in enumerate(ks2):
      elems1, elems2 = set(p1[k1]), set(p2[k2])
      intersections[i][j] = elems1.intersection(elems2)

  table = [[len(inter) for inter in row] for row in intersections]

  return {"keys1": ks1, "keys2": ks2,
      "intersections": intersections, "table": table}

def format_contingency(c):
  ks1, ks2, table = c['keys1'], c['keys2'], c['table']
  header = list(ks2)
  header.insert(0, '')
  s = [header]
  for k1, row in zip(ks1, table):
    strs = list(str(x) for x in row)
    strs.insert(0, k1)
    s.append(strs)
  cols = zip(*s)

  out = ''
  widths = list(max(len(x) for x in col) for col in cols)
  for row in s:
    for w, x in zip(widths, row):
      out += '%*s ' % (w, x)
    out += '\n'
  return out

def _pair_count(table):
  u = [sum(row) for row in table]
  v = [sum(col) for col in zip(*table)]
  n = sum(u)

  num_pairs = lambda x: (x*(x-1))/2
  total_pairs = num_pairs(n)
  u_pairs = sum(num_pairs(u_i) for u_i in u)
  v_pairs = sum(num_pairs(v_j) for v_j in v)
  true_positives = sum(num_pairs(n_ij) for n_ij in it.chain(*table))

  false_negatives = u_pairs - true_positives
  false_positives = v_pairs - true_positives
  disagreements = false_negatives + false_positives
  agreements = total_pairs - disagreements

  return locals()

#### Cluster comparison indices ####

## Module dictionary with provided indices
index = {}

# Rand and adjusted Rand indices

def rand_index(table):
  """Calculates the Rand index of a contingency table.
  
  >>> rand_index([[2, 2, 1]
  ...             [1, 0, 2]])
  0.5
  """
  d = _pair_count(table)
  A = d['agreements']
  N = d['total_pairs']

  return float(A)/N

def adjusted_rand_index(table):
  """Calculates the adjusted Rand index of a contingency table.

  >>> adjusted_rand_index([[2, 2, 1], [1, 0, 2]])
  -0.037037...
  """
  d = _pair_count(table)
  TP = d['true_positives']
  N = d['total_pairs']
  N_U, N_V = d['u_pairs'], d['v_pairs']

  if not N_U or not N_V: return 0

  TP_expected = float(N_U * N_V) / N
  return safediv(TP - TP_expected, 0.5 * (N_U + N_V) - TP_expected)

index['rand'] = rand_index
index['adjusted-rand'] = adjusted_rand_index

# Jaccard index

def jaccard_index(table):
  """Calculates the Jaccard index of a contingency table.
  
  >>> jaccard_index([[2, 2, 1]
  ...                [1, 0, 2]])
  0.176
  """
  d = _pair_count(table)
  TP = d['true_positives']
  D = d['disagreements']

  return float(TP)/(TP + D)

index['jaccard'] = jaccard_index

# Wallace indices

def wallace_indices(table):
  """Calculates both Wallace indices (W_U, W_V) of a contingency table.
  
  >>> wallace_indices([[2, 2, 1]
  ...                  [1, 0, 2]])
  (0.231..., 0.429...)
  """
  d = _pair_count(table)
  TP = d['true_positives']
  N_U = d['u_pairs']
  N_V = d['v_pairs']

  left = float(TP)/N_U if N_U else 0.0
  right = float(TP)/N_V if N_V else 0.0

  return left, right

def adjusted_wallace_indices(table):
  """Calculates both adjusted Wallace indices (AW_U, AW_V) of a contingency
  table.
  
  >>> adjusted_wallace_indices([[2, 2, 1], [1, 0, 2]])
  (-0.0256..., -0.0666...)
  """
  d = _pair_count(table)
  TP = d['true_positives']
  N = d['total_pairs']
  N_U, N_V = d['u_pairs'], d['v_pairs']

  TP_expected = float(N_U * N_V) / N
  AW_U = (TP - TP_expected)/(N_U - TP_expected) if N_U else 0.0
  AW_V = (TP - TP_expected)/(N_V - TP_expected) if N_V else 0.0
  return (AW_U, AW_V)

index['wallace'] = wallace_indices
index['adjusted-wallace'] = adjusted_wallace_indices
index['left-wallace'] = lambda t: wallace_indices(t)[0] 
index['right-wallace'] = lambda t: wallace_indices(t)[1] 
index['adjusted-left-wallace'] = lambda t: adjusted_wallace_indices(t)[0] 
index['adjusted-right-wallace'] = lambda t: adjusted_wallace_indices(t)[1]

# Fowlkes-Mallows index

def fowlkes_mallows_index(table):
  """Calculates the Fowlkes-Mallows index of a contingency table.
   
  >>> fowlkes_mallows_index([[2, 2, 1]
  ...                        [1, 0, 2]])
  0.314
  """
  W_U, W_V = wallace_indices(table)
  return math.sqrt(W_U * W_V)

def adjusted_fowlkes_mallows_index(table):
  """Calculates the adjusted Fowlkes-Mallows index of a contingency table.

  >>> adjusted_fowlkes_mallows_index([[2, 2, 1], [1, 0, 2]])
  -0.0397...
  """
  d = _pair_count(table)
  TP = d['true_positives']
  N = d['total_pairs']
  N_U, N_V = d['u_pairs'], d['v_pairs']

  if not (N_U and N_V):
    return 0.0

  TP_expected = float(N_U * N_V) / N
  return (TP - TP_expected)/(math.sqrt(N_U * N_V) - TP_expected)

index['fowlkes-mallows'] = fowlkes_mallows_index
index['adjusted-fowlkes-mallows'] = adjusted_fowlkes_mallows_index
index['fm'] = fowlkes_mallows_index
index['afm'] = adjusted_fowlkes_mallows_index

# Mutual information and related measures

def log2(x):
  if x <= 0.0:
    return 0.0
  return math.log(x) / math.log(2)

def _probabilities(table):
  u = [sum(row) for row in table]
  v = [sum(col) for col in zip(*table)]
  n = sum(u)

  p_u = [float(u_i)/n for u_i in u]
  p_v = [float(v_j)/n for v_j in v]
  p = [[float(n_ij)/n for n_ij in row] for row in table]
  return locals()

def partition_entropies(table):
  """Calculates the entropy of each partition of a contingency table."""
  d = _probabilities(table)
  p_u, p_v, p = d['p_u'], d['p_v'], d['p']
  H_U = -sum(u_i * log2(u_i) for u_i in p_u)
  H_V = -sum(v_i * log2(v_i) for v_i in p_v)
  return (H_U, H_V)

def joint_entropy(table):
  d = _probabilities(table)
  p = d['p']

  m = [[p_ij * log2(p_ij) for p_ij in row] for row in p]
  return -sum(it.chain(*m))

def mutual_information(table):
  """Calculates the mutual information of a contingency table."""
  d = _probabilities(table)
  p_u, p_v, p = d['p_u'], d['p_v'], d['p']

  m = [[p_ij * log2(p_ij / (p_u[i] * p_v[j]))
    for j, p_ij in enumerate(row)]
    for i, row in enumerate(p)]
  return sum(it.chain(*m))

def variation_of_information(table):
  """Calculates the variation of information distance of a contingency table."""
  return joint_entropy(table) - mutual_information(table)

def normalized_mutual_information(table, norm):
  mi = mutual_information(table)
  H_U, H_V = partition_entropies(table)
  H_UV = joint_entropy(table)
  if norm == 'max':   return mi / max(H_U, H_V)
  if norm == 'min':   return mi / min(H_U, H_V)
  if norm == 'joint': return mi / H_UV
  if norm == 'mean':  return mi / (H_U + H_V) * 2.0
  if norm == 'geom':  return mi / math.sqrt(H_U * H_V)
  raise ValueError("Unknown normalization %s" % norm)

def normalized_variation_of_information(table):
  mi = mutual_information(table)
  H  = joint_entropy(table)
  return 1 - mi / H

def normalized_information_distance(table):
  mi = mutual_information(table)
  H_U, H_V = partition_entropies(table)
  return 1 - mi / max(H_U, H_V)

index['mutual-information'] = mutual_information
index['variation-of-information'] = variation_of_information
index['mi'] = mutual_information
index['vi'] = variation_of_information

index['nmi-max']   = lambda table: normalized_mutual_information(table, 'max')
index['nmi-min']   = lambda table: normalized_mutual_information(table, 'min')
index['nmi-joint'] = lambda table: normalized_mutual_information(table, 'joint')
index['nmi-mean']  = lambda table: normalized_mutual_information(table, 'mean')
index['nmi-geom']  = lambda table: normalized_mutual_information(table, 'geom')

index['nvi'] = normalized_variation_of_information
index['nid'] = normalized_information_distance

# Matching and error indices

def asymmetric_matching(table):
  """Naive cluster matching, selecting the one with the most elements in common.
  
  This matching is asymmetric because more than one cluster in one partition may
  be mapped to the same cluster in the other partition.
  
  >>> asymmetric_matching([[2, 2, 1], [1, 0, 2]])
  [(0, 0), (1, 2)]
  >>> asymmetric_matching([[3, 2, 1], [2, 0, 1]])
  [(0, 0), (1, 0)]
  """
  def argmax(v):
    return max(range(len(v)), key=lambda i: v[i])

  m, n = len(table), len(table[0])
  indices = []
  if m < n:
    transpose = zip(*table)
    for j, col in enumerate(transpose):
      i = argmax(col)
      indices.append((i, j))
  else:
    for i, row in enumerate(table):
      j = argmax(row)
      indices.append((i, j))
  
  return indices

try:
  has_symmetric_matching = True
  from munkres import Munkres, make_cost_matrix
  def symmetric_matching(table):
    """Cluster matching that maximizes the total number of elements in common
    while matching at most one cluster to another.
    
    >>> symmetric_matching([[2, 2, 1], [1, 0, 2]])
    [(0, 0), (1, 2)]
    >>> symmetric_matching([[3, 2, 1], [2, 0, 1]])
    [(0, 0), (1, 2)]
    """
    maximum = max(it.chain(*table))
    cost_matrix = make_cost_matrix(table, lambda x: maximum - x)
    indices = Munkres().compute(cost_matrix)

    return indices

except ImportError:
  has_symmetric_matching = False
  def symmetric_matching(table):
    raise NotImplementedError("munkres package is not available")

def cluster_matching(contingency, is_symmetric=True):
  """Finds the best invertible cluster pairing for a contingency table.

  Given the amount of elements in common between clusters in different
  partitions, we say that a cluster matching is a correspondence between
  clusters. If the table is not square, not all clusters will have
  correspondence. The best pairing is the one that maximizes the number of
  elements for all pairs.

  Note that this is an instance of the assignment problem.

  If the package munkres is not available, always use asymmetric matching.

  # Example 1: A diagonal matrix
  >>> cluster_pairing({
  ...  'table': [[4, 0, 0],
  ...            [0, 9, 0],
  ...            [0, 0, 7]],
  ...  'keys1': ['U1', 'U2', 'U3'], 'keys2': ['V1', 'V2', 'V3']})
  {('U1', 'V1'): 4, ('U2', 'V2'): 9, ('U3', 'V3'): 7}

  # Example 2: A permutated diagonal matrix
  >>> cluster_pairing({
  ...  'table': [[0, 0, 7],
  ...            [4, 0, 0],
  ...            [0, 9, 0]],
  ...  'keys1': ['U1', 'U2', 'U3'], 'keys2': ['V1', 'V2', 'V3']})
  {('U1', 'V3'): 7, ('U2', 'V1'): 4, ('U3', 'V2'): 9} 

  # Example 3: A square matrix with small off-diagonal elements
  >>> cluster_pairing({
  ...  'table': [[4, 0, 2],
  ...            [0, 9, 1],
  ...            [3, 1, 7]],
  ...  'keys1': ['U1', 'U2', 'U3'], 'keys2': ['V1', 'V2', 'V3']})
  {('U1', 'V1'): 4, ('U2', 'V2'): 9, ('U3', 'V3'): 7}

  # Example 4: A non-square matrix
  >>> cluster_pairing({
  ...  'table': [[4, 0, 2, 1],
  ...            [0, 9, 1, 3],
  ...            [3, 1, 7, 3]],
  ...  'keys1': ['U1', 'U2', 'U3'], 'keys2': ['V1', 'V2', 'V3']})
  {('U1', 'V1'): 4, ('U2', 'V2'): 9, ('U3', 'V3'): 7} 
  """ 
  table, keys1, keys2 = (contingency['table'], contingency['keys1'],
      contingency['keys2'])

  if is_symmetric and has_symmetric_matching:
    indices = symmetric_matching(table)
  else:
    indices = asymmetric_matching(table)
    if is_symmetric:
      warnings.warn("munkres package is not available, can't compute" +
          " symmetric matching; defaulting to asymmetric matching",
          stacklevel=2)

  pairing = [(keys1[i], keys2[j]) for i,j in indices]
  values = [table[i][j] for i,j in indices]

  return dict(zip(pairing, values))

def _incongruences(table, is_symmetric=True):
  m, n = len(table), len(table[0])
  pairing = cluster_matching({
    'table': table, 'keys1': range(m), 'keys2': range(n)},
    is_symmetric=is_symmetric)

  N = sum(it.chain(*table))
  num_congruences = sum(pairing.values())
  num_incongruences = N - num_congruences

  return {'number': num_incongruences,
      'normalized': float(num_incongruences) / N}

def incongruence_number(table, is_symmetric=True):
  """Calculates the number of incongruences in a contingency table.

  # The cluster pairing is {(0,0): 2, (1,2): 2}
  >>> incongruence_number([[2, 2, 1]
  ...                      [1, 0, 2]])
  4
  """
  return _incongruences(table, is_symmetric=is_symmetric)['number']

def normalized_incongruence(table, is_symmetric=True):
  """Calculates the percentual of incongruences in a contingency table.
  
  # Cluster pairing is {(0,0): 2, (1,2): 2}
  # Total: 8, incongruences: 4
  >>> normalized_incongruence([[2, 2, 1]
  ...                          [1, 0, 2]])
  0.5
  """
  return _incongruences(table, is_symmetric=is_symmetric)['normalized']

index['incongruence'] = incongruence_number
index['normalized-incongruence'] = normalized_incongruence
index['classification'] = lambda t: 1 - normalized_incongruence(t)

### Binary partition ###

def _binary_pre(table):
  return len(table) == 2 and len(table[0]) == 2 and len(table[1]) == 2

def precision(table):
  assert _binary_pre(table), 'Invalid table'
  (tp, fp), (fn, tn) = table
  return float(tp) / (tp + fp)

def recall(table):
  assert _binary_pre(table), 'Invalid table'
  (tp, fp), (fn, tn) = table
  return float(tp) / (tp + fn)

def f1(table):
  assert _binary_pre(table), 'Invalid table'
  p, r = precision(table), recall(table)
  return (2.0 * p * r) / (p + r)

def f_beta(table, beta):
  assert _binary_pre(table), 'Invalid table'
  p, r = precision(table), recall(table)
  return ((1.0 + beta**2) * p * r) / (beta**2 * p + r)

def matthews(table):
  assert _binary_pre(table), 'Invalid table'
  (tp, fp), (fn, tn) = table
  n = tp + fp + fn + tn
  s = float(tp + fn) / n
  p = float(tp + fp) / n
  return (float(tp)/n - s*p) / math.sqrt(s*p*(1-s)*(1-p))

index['precision'] = precision
index['recall'] = recall
index['f1'] = f1
index['matthews'] = matthews

def list_indices():
  #in the last version: choices = index.keys()
  #choices is equal to dict_keys([]), but not list: []
  choicestmp = index.keys()
  choices = list(choicestmp)
  # or use: choices = []
  choices.append('all')
  return sorted(choices)

#### I/O functions ####

def membership_parse(filename, as_clusters=False, has_header=None,
    column=None, dialect=csv.excel):
  """Parses a membership file in CSV format.

  >>> s = \"\"\"name,cluster
  ... a.txt,0
  ... e.txt,0
  ... c.txt,1
  ... d.txt,2
  ... "u.txt",0
  ... "p""quote.txt",2
  ... \"\"\"
  >>> with open('members.csv','wt') as f:
  ...   f.write(s)
  ...
  >>> membership_parse('members.csv', as_clusters=True, has_header=True)
  {'0': ['a.txt', 'e.txt', 'u.txt'], '1': ['c.txt'],
      '2': ['d.txt', 'p"quote.txt']}
  """
  membership = {}
  with open(filename, 'rb') as f:
    if not dialect:
      rows = list([line[:-1]] for line in f)
    else:
      rows = list(row for row in csv.reader(f, dialect=dialect))
    num_rows = len(rows)

    if not column: column = 1
    if has_header: rows = rows[1:]

    for i, row in enumerate(rows):
      if len(row) == 1:
        name = format_num(i, num_rows)
        cluster = row[0]
      else:
        name, cluster = row[0], row[column]
      membership[name] = cluster

  if as_clusters:
    return membership_to_clusters(membership)
  return membership


def classification_parse(filename, as_clusters=False, untrusted_group='',
    ignore_untrusted=False, trust_threshold=1.0):
  """Parses a classification file."""
  membership = {}
  multiple, untrusted = 0, 0
  with open(filename, 'r') as f:
    r = csv.DictReader(f)
    for row in r:
      name, klass = row['name'], row['class']
      if re.match(r'\[.*\]', row['class']):
        try:    klass = eval(row['class'])
        except: pass

      if not isinstance(klass, str): #in the last version: basestring):
        multiple += 1
        if untrusted_group:    klass = untrusted_group
        elif ignore_untrusted: continue

      if row['trust']:
        trust = float(row['trust'])
        if trust < trust_threshold:
          untrusted += 1
          if untrusted_group:    klass = untrusted_group
          elif ignore_untrusted: continue

      membership[name] = klass
  
  if (untrusted_group or ignore_untrusted) and (multiple or untrusted):
    warnings.warn(
        "Untrusted elements: %d with multiple classes, %d with low trust." % (
          multiple, untrusted))

  if as_clusters:
    return membership_to_clusters(membership)
  return membership


def membership_csv_format(membership, has_header=False):
  """Returns a string with membership map in CSV format
  
  >>> membership_csv_format({'rat':'mammal', 'cat':'mammal', 'fly':'insect'})
  'name,cluster
  fly,insect
  bat,mammal
  rat,mammal
  '
  """
  output = StringIO()
  writer = csv.writer(output, dialect=csv.excel)
  if has_header: writer.writerow(['name','cluster'])

  sorted_items = sorted(membership.items(), key=lambda pair: (pair[0],pair[1])) #key=lambda (k,v): (v,k)) - in the last version
  writer.writerows(sorted_items)
  
  out = output.getvalue()
  output.close()
  return out

def compare_clusters(reference_cluster, other_cluster, index_name='mi'):
  table = contingency(reference_cluster, other_cluster)['table']
  try:
    if index_name == 'all':
      all_indices = [
          'rand', 'adjusted-rand',
          'jaccard',
          'left-wallace', 'right-wallace',
          'adjusted-left-wallace', 'adjusted-right-wallace',
          'fowlkes-mallows', 'adjusted-fowlkes-mallows',
          'mutual-information', 'nid',
          'classification',
      ]
      if _binary_pre(table):
        all_indices += [
            'precision', 'recall',
            'f1',
            'matthews',
        ]
      d = OrderedDict((name, index[name](table)) for name in all_indices)
      incongruences = _incongruences(table)
      d.update({
        'incongruence': incongruences['number'],
        'normalized-incongruence': incongruences['normalized']})
      return d
    
    if index_name not in index:
      raise ValueError('Unknown index "%s". Known indices: %s' % (
        index_name, str(index.keys())))

    return index[index_name](table)
  except:
    pprint(table, sys.stderr)
    return {}

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      description='Compares two partitions (cluster sets)')
  parser.add_argument('reference', help='Reference filename')
  parser.add_argument('test', help='Test filename')
  parser.add_argument('index', default='mutual-information',
      choices=list_indices(), help='Comparison index')

  parser.add_argument('--trim', action='store_true',
      help='Only considers clusters present in both partitions')

  parser.add_argument('--output-table', metavar='FILENAME',
      help='Outputs contingency table to filename')

  parser.add_argument('--parse-classification', action='store_true',
      help='Expects to parse a classification file, with trust column and ' +
      'possibly multiple classes')

  parser.add_argument('--trust-threshold', type=float, default=1.0,
      help='Define trustworthiness within [-1,1]')
  parser.add_argument('--ignore-untrusted', action='store_true',
      help='Ignore classes with low trust or multiple classes')
  parser.add_argument('--untrusted-group', metavar='GROUP',
      help='Group elements with low trust or multiple classes in the provided group')

  parser.add_argument('--version', '-V', action='version',
      version=get_version())
  
  a = parser.parse_args()

  ref_cluster = membership_parse(a.reference, as_clusters=True)
  if a.parse_classification:
    other_cluster = classification_parse(a.test, as_clusters=True,
        untrusted_group=a.untrusted_group,
        ignore_untrusted=a.ignore_untrusted,
        trust_threshold=a.trust_threshold)
  else:
    other_cluster = membership_parse(a.test, as_clusters=True)

  total_elements = clusters_total(ref_cluster, other_cluster)
  classified_elements = total_elements
  if a.untrusted_group:
    untrusted_els = other_cluster.get(a.untrusted_group)
    if untrusted_els:
      classified_elements -= len(untrusted_els)
  if a.trim:
    ref_cluster, other_cluster = clusters_trim(ref_cluster, other_cluster)
    classified_elements = clusters_total(ref_cluster, other_cluster)

  result = compare_clusters(ref_cluster, other_cluster, a.index)
  writer = csv.writer(sys.stdout)
  writer.writerows(result.items())
  writer.writerows([
    ['classified', float(classified_elements) / total_elements],
    ['total', total_elements],
  ])

  if a.output_table:
   c = contingency(ref_cluster, other_cluster)
   with open(a.output_table, 'w') as f:
     f.write(format_contingency(c))

