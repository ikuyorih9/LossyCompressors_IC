#!/usr/bin/python

import os
import sys
import math
import argparse
import shutil
import warnings
import csv
from random import Random

from datasource import create_factory, indirect_file
import partition as p
from _utils import format_num, linecount, listify

def copy_sources_to_dir(sources, directory, concat_in=None):
  if concat_in:
    dest_name = os.path.join(directory, concat_in)
    with open(dest_name, 'wb') as f:
      for source in sources:
        f.write(source.get_string())
  else:
    for source in sources:
      filename = source.get_filename()
      shutil.copy(filename, directory)

def append_sources_to_file(sources, filename):
  with open(filename, 'at') as f:
    writer = csv.writer(f, dialect=csv.excel)
    writer.writerows([source.name, source.get_string()]
        for source in sources)

def select(names, membership, fraction, force_fraction=True, prng=Random()):
  membership = p.filter_membership(membership, names)
  clusters = p.membership_to_clusters(membership)

  sizes = [len(members) for cluster, members in clusters.items()]
  min_fraction = 1.0 / min(sizes)
  if fraction < min_fraction:
    if force_fraction:
      warnings.warn("Some clusters will not be represented")
    else:
      fraction = min_fraction

  selected = []
  for cluster, members in clusters.items():
    members = list(members)
    # Choose which way to round randomly, favoring the closest integer.
    frac, floor = math.modf(fraction * len(members))
    if prng.random() < frac: num_selected = int(floor + 1)
    else:                    num_selected = int(floor)
    
    prng.shuffle(members)
    selected.extend(members[:num_selected])

  return selected

def partition(names, membership, num_parts, prng=Random()):
  membership = p.filter_membership(membership, names)
  clusters = p.membership_to_clusters(membership)

  part = [[] for _ in range(num_parts)]
  remaining = []
  for cluster, members in clusters.items():
    members = list(members)
    prng.shuffle(members)
    n = len(members)

    per_part, rem = n / num_parts, n % num_parts
    if per_part:
      for i in range(num_parts):
        part[i].extend(members[i * per_part: (i + 1) * per_part])
    
    if rem:
      remaining.extend(members[-rem:])
 
  for i, element in enumerate(remaining):
    part[i % num_parts].append(element)

  prng.shuffle(part)
  return part

#### Dataset manipulation

def split_dataset(factory, membership, fraction=0.5,
    dest_names=None, dest_type="indirect", dest_dir="",
    prng=Random()):
  """Splits a labelled dataset into reference and test directories."""
  sources = factory.get_sources()
  names = [source.name for source in sources]

  selected = select(names, membership, fraction, prng=prng, force_fraction=True)
  ref_sources, test_sources = [], []
  for source in sources:
    if source.name in selected: ref_sources.append(source)
    else:                       test_sources.append(source)
  
  if dest_names:
    ref_name, test_name = dest_names
  else:
    ref_name = os.path.join(dest_dir, factory.name + '-ref')
    test_name = os.path.join(dest_dir, factory.name + '-test')

  if dest_type == 'indirect' and hasattr(factory, 'inputs'):
    paths = listify(factory.inputs)
    indirect_file(ref_name, paths, ref_sources)
    indirect_file(test_name, paths, test_sources)
  elif dest_type == 'directory':
    if os.path.exists(ref_name):  shutil.rmtree(ref_name)
    if os.path.exists(test_name): shutil.rmtree(test_name)
    os.mkdir(ref_name), os.mkdir(test_name)

    copy_sources_to_dir(ref_sources, ref_name)
    copy_sources_to_dir(test_sources, test_name)
  else:
    if os.path.exists(ref_name): os.remove(ref_name)
    if os.path.exists(test_name): os.remove(test_name)
    append_sources_to_file(ref_sources, ref_name)
    append_sources_to_file(test_sources, test_name)

  return ref_name, test_name

def sample_dataset(factory, membership, fraction,
    dest_name=None, dest_type="indirect", dest_dir="",
    prng=Random()):
  """Samples a dataset keeping the proportion of class sizes unchanged."""
  sources = factory.get_sources()
  names = [source.name for source in sources]
  selected = select(names, membership, fraction, prng=prng, force_fraction=True)
  sampled_sources = [source
      for source in sources
      if source.name in selected]

  if not dest_name:
    dest_name = os.path.join(dest_dir, factory.name + '-sample')

  if dest_type == 'indirect' and hasattr(factory, 'inputs'):
    indirect_file(dest_name, listify(factory.inputs), sampled_sources)
  elif dest_type == 'directory':
    if os.path.exists(dest_name):
      shutil.rmtree(dest_name)
    os.makedirs(dest_name)
    copy_sources_to_dir(sampled_sources, dest_name)
  else:
    if os.path.exists(dest_name):
      os.remove(dest_name)
    append_sources_to_file(sampled_sources, dest_name)

  return dest_name

def partition_dataset(factory, membership, num_parts,
    dest_type='directory', dest_names=None, dest_dir="", prng=Random()):
  sources = factory.get_sources()
  names = [source.name for source in sources]
  parts = partition(names, membership, num_parts, prng)

  source_by_name = dict((source.name, source) for source in sources)
  source_partition = [[source_by_name[name] for name in part] for part in parts]

  if not dest_names:
    base_name = os.path.join(dest_dir, factory.name + '-part-')
    dest_names = [base_name + format_num(i, num_parts)
        for i in range(num_parts)]

  for source_part, dest_name in zip(source_partition, dest_names):
    if dest_type == 'indirect' and hasattr(factory, 'inputs'):
      indirect_file(dest_name, listify(factory.inputs), source_part)
    elif dest_type == 'directory':
      if os.path.exists(dest_name):
        shutil.rmtree(dest_name)
      os.makedirs(dest_name)
      copy_sources_to_dir(source_part, dest_name)
    else:
      if os.path.exists(dest_name):
        os.remove(dest_name)
      append_sources_to_file(source_part, dest_name)

  return dest_names

def pipeline(factories, membership,
    split=None, sample=None, num_parts=None,
    dest_type="indirect", dest_dir=".", verbosity=1, seed=1):
  prng = Random(seed)

  if num_parts and split:
    raise ValueError, "Can't partition and split the dataset at the same time."

  if num_parts:
    if len(factories) != 1:
      raise ValueError, "Won't partition more than one dataset"

    dest_names = partition_dataset(
        factories[0], membership, num_parts,
        dest_type=dest_type, dest_dir=dest_dir, prng=prng)
    if verbosity >= 1:
      sys.stderr.write('Partitioned %s into %d datasets\n' % (
        factories[0].name, num_parts))
    factories = [create_factory(dest_name) for dest_name in dest_names]
    if verbosity >= 2:
      for factory in factories:
        num_elements = len(factory.get_sources())
        sys.stderr.write('%s: %d elements\n' % (factory.name, num_elements))

  if split:
    if len(factories) != 1:
      raise ValueError, "Won't split more than one dataset"

    ref_name, test_name = split_dataset(
        factories[0], membership,
        fraction=split,
        dest_type=dest_type, dest_dir=dest_dir, prng=prng)
    if verbosity >= 1:
      sys.stderr.write('Split %s into %s (reference) and %s (test)\n' % (
          factories[0].name, ref_name, test_name))
    factories = [create_factory(ref_name), create_factory(test_name)]

  if sample:
    for i, factory in enumerate(factories):
      dest_name = sample_dataset(factory, membership, sample,
          dest_type=dest_type, dest_dir=dest_dir, prng=prng)
      factories[i] = create_factory(dest_name)
      if verbosity >= 1:
        sys.stderr.write('Sampled %s into %s\n' % (factory.name, dest_name))

  return factories

def cli_parser():
  parser = argparse.ArgumentParser('Dataset processing', add_help=False)
  group = parser.add_argument_group('Dataset preprocessing options')
  group.add_argument('--split', type=float,
      help="Splits the given dataset into training and test, keeping the " +
      "class proportion.")
  group.add_argument('--sample', type=float,
      help="Samples a fraction of the given dataset or datasets, keeping the " +
      "class proportion.")
  group.add_argument('--num-parts', type=int,
      help="Number of parts to partition the dataset")
  group.add_argument('--concat-references', action='store_true',
      help="Concatenate reference files when splitting a dataset")
  group.add_argument('--dest-dir',
      help="Destination directory for preprocessed dataset")
  group.add_argument('-m', '--output-mode', choices=['directory', 'file', 'indirect'],
      default='indirect', help='Output mode for files')
  group.add_argument('--no-membership', action='store_true',
      help="Ignores membership requirement")
  return parser

def parse_args(args):
  def test_fraction(name, x):
    if x is None:
      return
    if x < 0.0 or x > 1.0:
      raise ValueError, '%s fraction should be in [0,1] range' % name

  test_fraction('Split', args.split)
  test_fraction('Sample', args.sample)

  return {
      'split': args.split,
      'sample': args.sample,
      'num_parts': args.num_parts,
      'dest_type': args.output_mode,
      'dest_dir': args.dest_dir or "",
      }

if __name__ == '__main__':
  parser = argparse.ArgumentParser(parents=[cli_parser()])
  parser.add_argument('input', nargs='+', help='Datasets')
  parser.add_argument('--membership', help='Membership file')
  parser.add_argument('-v', '--verbosity', action='count')
  
  a = parser.parse_args()
  if len(a.input) > 2:
    raise ValueError, 'More than two datasets provided'

  if not (a.split or a.sample or a.num_parts):
    warnings.warn("Nothing to do...")
    exit()
 
  factories = [create_factory(fname) for fname in a.input] 
  if a.membership:
    membership = p.membership_parse(a.membership)
  elif a.no_membership:
    membership = {}
    for factory in factories:
      for source in factory.get_sources():
        membership[source.name] = 'all'
  else:
    raise ValueError, 'Membership was not provided (you may want to pass --no-membership to make it explicit)'

  pipeline(factories, membership, verbosity=a.verbosity, **parse_args(a))
