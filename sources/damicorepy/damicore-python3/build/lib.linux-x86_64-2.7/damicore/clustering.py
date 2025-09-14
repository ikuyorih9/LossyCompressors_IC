"""Clustering module: functions related to DAMICORE's clustering pipeline"""

import sys
import argparse

from igraph.clustering import VertexDendrogram

import ncd2 as ncd
import tree_simplification as nj

from tree import to_graph
from _utils import frequency, normalize_list
from partition import clusters_to_membership as c2m

##### Subgraph measures ####

def subgraph_degree(g, indices):
  l = 0
  for i in indices:
    for j in g.neighbors(i):
      if j > i and j in indices:
        l += 1
  return l

def subgraph_weight(g, indices, weights):
  Sc = 0.0
  for i in indices:
    for j in g.neighbors(i):
      if j > i and j in indices:
        Sc += weights[g.get_eid(i, j)]
  return Sc

def expected_subgraph_weight(g, indices, matrix, keys):
  l = 0.0
  ks = [keys[i] for i in indices]
  for i, ki in enumerate(ks):
    for kj in enumerate(ks[i + 1:]): # Restrict to upper matrix
      l += matrix[ki][kj]
  return l

##### Unrooted binary tree modularity ####

def classify_tree_vertices(g):
  """Classify an unrooted binary tree vertices.
  
  Nodes in an unrooted binary tree can be classified as leafs (L) or inner
  nodes (I). Inner nodes, in turn, can be classified by the number of leafs
  they connect to:

  * A: connects to two leafs;
  * B: connects to one leaf;
  * C: connects to no leafs.

  If an unrooted binary tree has `n` leafs and `a` nodes of class A, then
      #B = b = n - 2a
      #C = c = a - 2
  """
  for v in g.vs:
    neighbor_degrees = [n.degree() for n in v.neighbors()]
    if len(neighbor_degrees) <= 1: v['class'] = 'L'
    elif len(neighbor_degrees) == 3:
      num_leafs = sum(1 for k in neighbor_degrees if k == 1)
      v['class'] = {0: 'C', 1: 'B', 2:'A'}[num_leafs]
    else:
      raise ValueError('Tree is not unrooted binary')

def tree_modularity(g, clustering):
  "Variant of modularity measure for unrooted binary trees."
  # Classify vertices, if necessary
  if not 'class' in g.vs.attributes():
    classify_tree_vertices(g)
  classes = g.vs['class']
 
  num_by_class = frequency(classes)
  n, a = num_by_class['L'], num_by_class['A']
  b = n - 2 * a
  c = a - 2
  i = n - 2
  N, M = float(n + i), float(2 * n - 3)

  # Probability table
  prob = {
      'L': {'L': 0.0,   'A': 2*a/N,     'B': b/N,          'C': 0.0},
      'A': {'L': 2*a/N, 'A': 0.0,       'B': a*b/(N*i),    'C': a*c/(N*i)},
      'B': {'L': b/N,   'A': a*b/(N*i), 'B': 2*b**2/(N*i), 'C': 2*b*c/(N*i)},
      'C': {'L': 0.0,   'A': a*c/(N*i), 'B': 2*b*c/(N*i),  'C': 3*c**2/(N*i)}
  }

  # Calculate modularity
  Q = 0.0
  for cluster in clustering:
    cluster = set(cluster)

    l = subgraph_degree(g, cluster)
    l_expected = expected_subgraph_weight(g, cluster, prob, classes)
    
    Q += l - l_expected
  return Q / (2 * M)

def _get_weights(g, weights=None):
  if weights:
    if weights in g.es.attributes():
      ws = g.es[weights]
    else:
      ws = weights
  else:
    ws = [1 for _ in g.es]
  return ws

def correlation(g, weights=None):
  """Computes the correlation matrix of the degree distribution."""
  corr = {}
  degs = set(g.degree())
  for k1 in degs:
    corr[k1] = dict((k2, 0) for k2 in degs)

  ws = _get_weights(g, weights)
  m = float(len(ws))
   
  for e, w in zip(g.es, ws):
    k1, k2 = [g.vs[x].degree() for x in e.tuple]
    # Expected weight should be symmetric
    corr[k1][k2] += 2 * w / m
    corr[k2][k1] += 2 * w / m
  return corr

def corr_modularity(g, clustering, weights=None, corr_matrix=None):
  """Modularity calculation using correlation between vertex
  degrees."""

  ks = g.degree()
  ws = _get_weights(g, weights)
  S = float(sum(ws))

  # Total strength and joint probability matrix
  corr_matrix = corr_matrix if corr_matrix else correlation(g, ws)

  Q = 0.0
  for cluster in clustering:
    cluster = set(cluster)

    Sc = subgraph_weight(g, cluster, ws)
    Sc_expected = expected_subgraph_weight(g, cluster, corr_matrix, ks)
    
    Q += Sc - Sc_expected
  return Q / (2 * S)

def newman_modularity(g, clustering, weights=None):
  """Compute regular Newman's modularity."""

  max_index = -1
  for cluster in clustering:
    max_index = max(max_index, max(cluster))
  membership = range(max_index + 1)

  for i, cluster in enumerate(clustering):
    for u in cluster:
      membership[u] = i

  return g.modularity(membership, weights)

def my_fastgreedy(g, modularity=None, weights=None):
  """Fast greedy modularity optimization algorithm, allowing custom modularity
  calculations.
  
  TODO(brunokim): Use modularity delta instead of calculating the whole
  modularity for each pair.
  """
  
  if modularity == 'tree':
    modularity = tree_modularity
  elif modularity == 'corr':
    corr_matrix = correlation(g, weights)
    def partial_corr_modularity(g, clustering, weights=None):
      return corr_modularity(g, clustering, weights, corr_matrix=corr_matrix)
    modularity = partial_corr_modularity
  else:
    if modularity and modularity != 'newman':
      sys.stderr.write(('Warning: unknown modularity value %s. ' +
      'Using Newman modularity') % modularity)
    modularity = newman_modularity

  n = g.vcount()
  communities = {}
  for i, v in enumerate(g.vs):
    communities[i] = {
        'adj': [u.index for u in v.neighbors()],
        'members': [i]
        }

  merges = []
  count = n
  for _ in xrange(n - 1):
    max_modularity = float("-inf")

    # For each pair (c1, c2) of adjacent communities, where
    # index(c1) < index(c2), remove c1 and c2 from the communities map.
    # clustering receives the remaining communities' members and the
    # concatenation of c1 and c2's members
    for i, community in communities.items():
      communities.pop(i)
      for j in community['adj']:
        if i >= j:
          continue
        adj_community = communities.pop(j)

        clustering = [c['members'] for c in communities.values()]
        clustering.append(community['members'] + adj_community['members'])
        Q = modularity(g, clustering)
        if Q > max_modularity:
          max_positions = (i, j)
          max_modularity = Q

        communities[j] = adj_community
      communities[i] = community

    i, j = max_positions
    c1, c2 = communities.pop(i), communities.pop(j)
    new_members = c1['members'] + c2['members']
    adj1, adj2 = c1['adj'], c2['adj']
    adj1.remove(j), adj2.remove(i)
    adj = list(set(adj1 + adj2))
    
    for idx in adj1: communities[idx]['adj'].remove(i)
    for idx in adj2: communities[idx]['adj'].remove(j)
    for idx in adj: communities[idx]['adj'].append(count)
    communities[count] = {'members': new_members, 'adj': adj}
    count += 1

    merges.append([max_positions, max_modularity])

  pairs, modularities = zip(*merges)
  best_merge_idx = max(range(n - 1), key=lambda i: modularities[i])
  optimal_count = n - best_merge_idx
  return VertexDendrogram(g, pairs, optimal_count)

community_detection_names = [
    'fast', 'newman-modularity',
    'betweenness',
    'walktrap',
    'tree-modularity',
    'correlation-modularity',
    'optimal'
    ]

def tree_clustering(g, leaf_ids, community_detection_name='fast',
    is_normalize_weights=True, num_clusters=None):
  if community_detection_name not in community_detection_names:
    raise ValueError("Unknown community detection method: %s. Known methods: %s" % (
      community_detection_name, ', '.join(community_detection_names)))

  weights = [1.0/length for length in g.es['length']]
  if is_normalize_weights:
    weights = normalize_list(weights)
  g.es['weight'] = weights

  name = community_detection_name
  if name == 'optimal':
    clustering, _ = g.community_optimal_modularity()
    dendrogram = None
  else:
    if name == 'fast' or name == 'newman-modularity':
      dendrogram = g.community_fastgreedy(weights=weights)
    elif name == 'betweenness':
      dendrogram = g.community_edge_betweenness(weights=weights)
    elif name == 'walktrap':
      dendrogram = g.community_walktrap(weights=weights)
    elif name == 'tree-modularity':
      dendrogram = my_fastgreedy(g, 'tree', weights=weights)
    elif name == 'correlation-modularity':
      dendrogram = my_fastgreedy(g, 'corr', weights=weights)

    clustering = dendrogram.as_clustering(num_clusters)

  # Maps leaf ID to cluster number
  vertex_names = [v["name"] for v in g.vs]
  membership = {}
  for id_ in leaf_ids:
    membership[id_] = clustering.membership[ vertex_names.index(id_) ]

  return membership, clustering, dendrogram

def _pipeline(ncd_results,
    is_normalize_matrix=True, is_normalize_weights=True, num_clusters=None,
    community_detection_name='fast', verbosity=0):
  
  results = list(ncd_results.get_results())

  if verbosity >= 1:
    sys.stderr.write('Simplifying graph...\n')
  if not is_normalize_matrix:
    m, (ids,_) = ncd.to_matrix(results)
  else:
    ds = normalize_list(list(result['ncd'] for result in results))
    normalized_results = [ncd.NcdResult(result, ncd=dist)
        for result, dist in zip(results, ds)]
    m, (ids,_) = ncd.to_matrix(normalized_results)

  tree = nj.neighbor_joining(m, ids)

  if verbosity >= 1:
    sys.stderr.write('Clustering elements...\n')
  g = to_graph(tree)
  membership, clustering, dendrogram = tree_clustering(g, ids,
      is_normalize_weights=is_normalize_weights,
      num_clusters=num_clusters,
      community_detection_name=community_detection_name)
 
  return {
      'ncd_results': ncd_results,
      'phylo_tree': tree,
      'leaf_ids': ids,
      'tree_graph': g,
      'dendrogram': dendrogram,
      'membership': membership,
      'clustering': clustering,
  }

def pipeline(factories=None, compressor=None, ncd_results=None,
    is_parallel=True,
    is_normalize_matrix=True, is_normalize_weights=True, num_clusters=None,
    community_detection_name='fast', verbosity=0):
  if verbosity >= 1:
    if ncd_results: sys.stderr.write('Using already computed NCD distance matrix\n')
    else:           sys.stderr.write('Performing NCD distance matrix calculation...\n')

  if not ncd_results:
    ncd_results = ncd.distance_matrix(factories, compressor,
        is_parallel=is_parallel, verbosity=verbosity)

  return _pipeline(ncd_results, is_normalize_matrix, is_normalize_weights,
      num_clusters, community_detection_name, verbosity)

def cli_parser():
  parser = argparse.ArgumentParser(add_help=False)
  group = parser.add_argument_group('Clustering options',
      'Options for clustering algorithms')
  group.add_argument('--source-mode', action='store_true',
      help='Calculate NCD distance matrix for the provided sources (default)')
  group.add_argument('--matrix-mode', action='store_true',
      help='Uses an already calculated NCD matrix in raw format')
  group.add_argument('--normalize-matrix', action='store_true',
      help='Normalize matrix before simplification')
  group.add_argument('--normalize-weights', action='store_true',
      help='Normalize tree edge weights before clustering (recommended)')
  group.add_argument('-n', '--num-clusters', type=int,
      help='Number of clusters to find. If not provided, cut dendogram ' +
      'where modularity is maximized')
  group.add_argument('--community-detection',
      choices=community_detection_names, default='fast',
      help='Community detection algorithm to use')

  return parser

def parse_args(args):
  ncd_results = None
  if args.matrix_mode:
    ncd_results = ncd.FilenameNcdResults(args.input[0])
  return {
      'is_normalize_weights': args.normalize_weights,
      'is_normalize_matrix': args.normalize_matrix,
      'num_clusters': args.num_clusters,
      'community_detection_name': args.community_detection,
      'ncd_results': ncd_results,
      }
