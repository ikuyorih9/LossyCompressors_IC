#!/usr/bin/python

import os
import sys
import re
import argparse
import csv
import itertools as it

from pprint import pformat

import igraph

import _utils
import ncd2 as ncd
import partition as p
import clustering as c

from tree import newick_format
from _utils import frequency, normalize_list, dir_basename, open_outfile, get_version
from clustering import community_detection_names

# TODO(brunokim): use a cladogram layout, which igraph seems to be lacking
def graph_style(g, ids):
    style = {}
    seed_layout = g.layout('rt_circular')

    layout = g.layout('fr', seed=seed_layout.coords, weights='weight')
    style['layout'] = layout

    is_leafs = [(v['name'] in ids) for v in g.vs]
    style['vertex_size'] = [15 if is_leaf else 5 for is_leaf in is_leafs]
    style['vertex_label'] = [v['name'] if is_leaf else ''
        for is_leaf, v in zip(is_leafs,g.vs)]

    return style

#if __name__ == '__main__':
#def main(argv):
def parser_args(args):
  parser = argparse.ArgumentParser(parents=[
    _utils.cli_parser(), ncd.cli_parser(), c.cli_parser()],
    fromfile_prefix_chars='+',
    description="Compute the clustering of a given dataset using the DAMICORE" +
    " methodology.")
  parser.add_argument('--ncd-output', help='File to output NCD result',
      metavar="FILE")
  parser.add_argument('--tree-output', help='File to output tree result',
      metavar="FILE")
  parser.add_argument('--graph-image', help='File to output graph image',
      metavar="FILE")
  parser.add_argument('--results-dir', metavar="DIR", 
      help='Directory to output all obtained results')

  partition_group = parser.add_argument_group('Clustering comparison options',
      'Options for comparison between partitions')
  partition_group.add_argument('--compare-to',
      help='Reference membership file to compare the resulting clustering',
      metavar="FILE")
  partition_group.add_argument('--partition-index', choices=p.list_indices(),
      default='wallace', help='Partition comparison index to use')
  partition_group.add_argument('--partition-output', metavar="FILE",
      help="File to output partition comparison (default:stdout)")

  return parser.parse_args(args)


#if __name__ == '__main__':
#  a = parser.parse_args()
def main(args): 
#  a = parser_args(sys.argv[1:])
  a = parser_args(args)
  general_args = _utils.parse_args(a)
  clustering_args = c.parse_args(a)
  output, is_parallel, verbosity = (general_args['output'],
      general_args['is_parallel'], general_args['verbosity'])
  is_normalize_weights, is_normalize_matrix, num_clusters = (
      clustering_args['is_normalize_weights'],
      clustering_args['is_normalize_matrix'], clustering_args['num_clusters'])
  community_detection_name, ncd_results = (
      clustering_args['community_detection_name'],
      clustering_args['ncd_results'])
      
  if ncd_results:
    factories = compressor = None
  else:
    ncd_args = ncd.parse_args(a)
    factories, compressor, matrix_format = (ncd_args['factories'],
        ncd_args['compressor'], ncd_args['matrix_format'])

  result = c.pipeline(factories, compressor, ncd_results,
      is_parallel=is_parallel,
      is_normalize_weights=is_normalize_weights,
      is_normalize_matrix=is_normalize_matrix,
      num_clusters=num_clusters,
      community_detection_name=community_detection_name,
      verbosity=verbosity)
  ncd_results, phylo_tree, tree_graph, leaf_ids, membership, clustering = (
      result['ncd_results'], result['phylo_tree'], result['tree_graph'],
      result['leaf_ids'], result['membership'], result['clustering'])
  dendrogram = result['dendrogram']
  
  # Outputs NCD step
  if a.ncd_output:
    with open(a.ncd_output, 'wt') as f:
      if matrix_format == 'phylip':
        ncd.write_phylip(f, ncd_results)
      else:
        ncd.write_csv(f, ncd_results, write_header=True)

  # Outputs tree in Newick format
  if a.tree_output:
    with open(a.tree_output, 'wt') as f:
      f.write(newick_format(phylo_tree))

  # Outputs graph image
  if a.graph_image:
    tree_style = graph_style(tree_graph, leaf_ids)
    igraph.plot(clustering, target=a.graph_image, **tree_style)

  # Outputs clustering result
  with open_outfile(output) as f:
    f.write(p.membership_csv_format(membership))

  # Outputs index, if comparison reference was provided
  if a.compare_to:
    with open_outfile(a.partition_output) as f:
      reference_cluster = p.membership_parse(a.compare_to, as_clusters=True)
      obtained_cluster = p.membership_to_clusters(membership)
      index = p.compare_clusters(reference_cluster, obtained_cluster,
          index_name=a.partition_index)
      f.write('%s\n' % pformat(index))

  # Output everything to directory
  if a.results_dir:
    # Create dir if it does not exist
    if not os.path.exists(a.results_dir):
      os.mkdir(a.results_dir)

    # Creates subdirectory containing results for this run
    subdirname = dir_basename(a.input[0])
    subpath = os.path.join(a.results_dir, subdirname)
    if not os.path.exists(subpath):
      os.mkdir(subpath)

    # Finds maximum index in subdirectory
    fnames = os.listdir(subpath)
    matches = [re.match('\d+', fname) for fname in fnames]
    indices = [int(match.group(0)) for match in matches if match]
    max_index = max([0] + indices) # if indices is empty, return 0
    index = max_index + 1
    
    # Writes all results
    base = os.path.join(subpath, '%03d-' % index)
    #with open(base + 'version', 'wt') as f:    f.write(get_version())
    with open(base + 'args.txt', 'wt') as f:   f.write('\n'.join(sys.argv[1:]))
    with open(base + 'ncd.csv', 'wt') as f:    ncd.csv_write(f, ncd_results)
    with open(base + 'ncd.phylip', 'wt') as f: ncd.write_phylip(f, ncd_results)
    with open(base + 'tree.newick', 'wt') as f:
      f.write(newick_format(phylo_tree))
    with open(base + 'membership.csv', 'wt') as f:
      f.write(p.membership_csv_format(membership))
    if a.compare_to:
      with open(base + 'partition.csv', 'wt') as f:
        all_indices = p.compare_clusters(reference_cluster, obtained_cluster,
            index_name='all')
        writer = csv.DictWriter(f, fieldnames=['index name', 'value'])
        writer.writeheader()
        writer.writerows({'index name': k, 'value': v}
            for k, v in all_indices.items())

    tree_style = graph_style(tree_graph, leaf_ids)
    igraph.plot(clustering, target=base + 'tree.svg', **tree_style)


if __name__ == '__main__':
    main(sys.argv[1:])

