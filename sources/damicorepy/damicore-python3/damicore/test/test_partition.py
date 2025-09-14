"""Tests for partition.py"""

import csv
import unittest
import warnings

import partition as p

m1 = {
    'bat': 'mammal',
    'cat': 'mammal',
    'dog': 'mammal',
    'cow': 'mammal',
    'rat': 'mammal',
    'emu': 'bird',
    'jay': 'bird',
    'owl': 'bird',
    'ant': 'insect',
    'fly': 'insect',
    }

m2 = {
    'bat': 'hemovore',
    'mosquito': 'hemovore',
    'cat': 'carnivore',
    'dog': 'carnivore',
    'jay': 'omnivore',
    'cow': 'herbivore',
    'fly': 'herbivore',
    }

c1 = {
    'mammal': set(['bat', 'cat', 'dog', 'cow', 'rat']),
    'bird': set(['emu', 'jay', 'owl']),
    'insect': set(['ant', 'fly']),
    }

c2 = {
    'hemovore': set(['bat', 'mosquito']),
    'carnivore': set(['cat', 'dog']),
    'omnivore': set(['jay']),
    'herbivore': set(['cow', 'fly']),
    }
 
c3 = {
    'hemovore': set(['bat', 'mosquito']),
    'omnivore': set(['jay', 'man']),
    'herbivore': set(['cow']),
    'fungivore': set(['slug']),
    }

class TestConversion(unittest.TestCase):
  def test_membership_to_clusters(self):
    self.assertEqual(c1, p.membership_to_clusters(m1))
    self.assertEqual(c2, p.membership_to_clusters(m2))

  def test_clusters_to_membership(self):
    self.assertEqual(m1, p.clusters_to_membership(c1))
    self.assertEqual(m2, p.clusters_to_membership(c2))

  def test_clusters_to_membership_with_list(self):
    c = {
        'odd': [1, 5, 13],
        'even': [20, 100],
        }
    expected = {
        1: 'odd',
        5: 'odd',
        13: 'odd',
        20: 'even',
        100: 'even',
        }
    self.assertEqual(expected, p.clusters_to_membership(c))

  def test_filter_membership(self):
    flying = set(['bat', 'fly', 'jay', 'mosquito', 'owl'])
    ex1 = {
        'bat': 'mammal',
        'jay': 'bird',
        'owl': 'bird',
        'fly': 'insect',
        }
    ex2 = {
        'bat': 'hemovore',
        'mosquito': 'hemovore',
        'jay': 'omnivore',
        'fly': 'herbivore',
        }
    self.assertEqual(ex1, p.filter_membership(m1, flying))
    self.assertEqual(ex2, p.filter_membership(m2, flying))

  def test_clusters_intersection(self):
    ex1 = {
        'mammal': set(['bat', 'cat', 'cow', 'dog']),
        'bird': set(['jay']),
        'insect': set(['fly']),
        }
    ex2 = {
        'hemovore': set(['bat']),
        'carnivore': set(['cat', 'dog']),
        'omnivore': set(['jay']),
        'herbivore': set(['cow', 'fly']),
        }
    got1, got2 = p.clusters_intersection(c1, c2)
    self.assertEqual(ex1, got1)
    self.assertEqual(ex2, got2)

  def test_clusters_intersection_with_warning(self):
    with warnings.catch_warnings(record=True) as w:
      warnings.simplefilter("always")
      p.clusters_intersection(c1, c2, warn=True)
      self.assertTrue(len(w) == 1)

  def test_clusters_intersection_disable_warning(self):
    with warnings.catch_warnings(record=True) as w:
      warnings.simplefilter("always")
      p.clusters_intersection(c1, c2, warn=False)
      self.assertFalse(w)

  def test_clusters_intersection_no_warning(self):
    with warnings.catch_warnings(record=True) as w:
      warnings.simplefilter("always")
      # First run does not warn, in the second classes have the same elements.
      x1, x2 = p.clusters_intersection(c1, c2, warn=False)
      p.clusters_intersection(x1, x2, warn=True)
      self.assertFalse(w)

  def test_membership_csv_format(self):
    expected = """name,cluster
cat,carnivore
dog,carnivore
bat,hemovore
mosquito,hemovore
cow,herbivore
fly,herbivore
jay,omnivore
"""
    expected = expected.replace('\n', csv.excel.lineterminator)
    self.assertEqual(expected, p.membership_csv_format(m2, has_header=True))

  def test_clusters_trim(self):
    x2, x3 = p.clusters_trim(c2, c3)
    self.assertEqual(x2, {
      'hemovore': set(['bat', 'mosquito']),
      'omnivore': set(['jay']),
      'herbivore': set(['cow', 'fly']),
    })
    self.assertEqual(x3, {
      'hemovore': set(['bat', 'mosquito']),
      'omnivore': set(['jay', 'man']),
      'herbivore': set(['cow']),
    })
 
class TestContingency(unittest.TestCase):
  def test_contingency(self):
    expected = {
        'keys1': ['bird', 'insect', 'mammal'],
        'keys2': ['carnivore', 'hemovore', 'herbivore', 'omnivore'],
        'intersections': [
         # bird
          [
            set(),        # carnivore
            set(),        # hemovore
            set(),        # herbivore
            set(['jay']), # omnivore
            ],
          # insect
          [
            set(),        # carnivore
            set(),        # hemovore
            set(['fly']), # herbivore
            set(),        # omnivore
          ],
          # mammal
          [
            set(['cat', 'dog']), # carnivore
            set(['bat']), # hemovore
            set(['cow']), # herbivore
            set(),        # omnivore
          ],
        ],
        'table': [
          [0, 0, 0, 1],
          [0, 0, 1, 0],
          [2, 1, 1, 0],
        ],
        }

    # Swallow warning
    with warnings.catch_warnings() as w:
      warnings.simplefilter("ignore")
      d = p.contingency(c1, c2)

    self.assertEqual(expected, d)

tables = {
  'perfect': [
    [4, 0, 0, 0],
    [0, 8, 0, 0],
    [0, 0, 2, 0],
    [0, 0, 0, 2],
    ],

  'rectangular': [
    [4, 1, 0, 1],
    [2, 8, 0, 1],
    [0, 0, 6, 0],
    ],

  'noise': [
    [4, 4, 4, 4],
    [2, 2, 2, 2],
    ],
  }

class TestEntropyMetrics(unittest.TestCase):
  def test_partition_entropies(self):
    expected = {
        'perfect':     (1.75,      1.75),
        'rectangular': (1.5203751, 1.8475239),
        'noise':       (0.9182958, 2.0),
        }
    for name, table in tables.items():
      got = p.partition_entropies(table)
      for entropy, want, got in zip(['H_U', 'H_V'], expected[name], got):
        msg = '%s: expected %.7lf, got %.7lf for %s' % (name, want, got, entropy)
        self.assertAlmostEqual(want, got, msg=msg)

  def test_joint_entropy(self):
    expected = {
        'perfect':     1.75,      # H_UV = max{H_U,H_V}
        'rectangular': 2.3709630, # max{H_U, H_V} < H_UV < H_U + H_V
        'noise':       2.9182958, # H_UV = H_U + H_V
        }
    for name, table in tables.items():
      got = p.joint_entropy(table)
      msg = '%s: expected %.7lf, got %.7lf' % (name, expected[name], got)
      self.assertAlmostEqual(expected[name], got, msg=msg)

  def test_mutual_information(self):
    expected = {
        'perfect':     1.75,
        'rectangular': 0.9969360,
        'noise':       0.0,
        }
    for name, table in tables.items():
      got = p.mutual_information(table)
      msg = '%s: expected %.7lf, got %.7lf' % (name, expected[name], got)
      self.assertAlmostEqual(expected[name], got, msg=msg)

  def test_variation_of_information(self):
    expected = {
        'perfect':     0.0,
        'rectangular': 1.3740271,
        'noise':       2.9182958,
        }
    for name, table in tables.items():
      got = p.variation_of_information(table)
      msg = '%s: expected %.7lf, got %.7lf' % (name, expected[name], got)
      self.assertAlmostEqual(expected[name], got, msg=msg)

  def test_normalized_mutual_information(self):
    for norm in ['max', 'min', 'joint', 'mean', 'geom']:
      nmi_perfect = p.normalized_mutual_information(tables['perfect'], norm)
      self.assertAlmostEqual(1.0, nmi_perfect, msg='%s: %.7lf' % (norm, nmi_perfect))

      nmi_noise = p.normalized_mutual_information(tables['noise'], norm)
      self.assertAlmostEqual(0.0, nmi_noise, msg='%s: %.7lf' % (norm, nmi_noise))

      nmi_rect = p.normalized_mutual_information(tables['rectangular'], norm)
      self.assertGreater(1.0, nmi_rect, msg='%s: %.7lf' % (norm, nmi_rect))
      self.assertLess(0.0, nmi_rect, msg='%s: %.7lf' % (norm, nmi_rect))
 
  def test_normalized_variation_of_information(self):
    expected = {
        'perfect':     0.0,
        'rectangular': 0.5795228,
        'noise':       1.0,
        }
    for name, table in tables.items():
      got = p.normalized_variation_of_information(table)
      msg = '%s: expected %.7lf, got %.7lf' % (name, expected[name], got)
      self.assertAlmostEqual(expected[name], got, msg=msg)
    
  def test_normalized_information_distance(self):
    expected = {
        'perfect':     0.0,
        'rectangular': 0.4603935,
        'noise':       1.0,
        }
    for name, table in tables.items():
      got = p.normalized_information_distance(table)
      msg = '%s: expected %.7lf, got %.7lf' % (name, expected[name], got)
      self.assertAlmostEqual(expected[name], got, msg=msg)
