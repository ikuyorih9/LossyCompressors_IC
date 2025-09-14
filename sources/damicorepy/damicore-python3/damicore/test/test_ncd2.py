"""Tests for ncd2"""

import csv
import unittest
import itertools as it

import datasource as ds
import compressor as c
import ncd2 as ncd

from ncd_base import NcdResult

class TestParallelUtilities(unittest.TestCase):
  def test_chunk_indices(self):
    class FakePrng(object):
      def shuffle(self, v): return v
    prng = FakePrng()

    self.assertEqual(ncd.chunk_indices( 0, 4, prng), [[ ], [ ], [ ], [ ]])
    self.assertEqual(ncd.chunk_indices( 1, 4, prng), [[0], [ ], [ ], [ ]])
    self.assertEqual(ncd.chunk_indices( 2, 4, prng), [[0], [1], [ ], [ ]])
    self.assertEqual(ncd.chunk_indices( 3, 4, prng), [[0], [1], [2], [ ]])
    self.assertEqual(ncd.chunk_indices( 4, 4, prng), [[0], [1], [2], [3]])
    self.assertEqual(ncd.chunk_indices( 7, 4, prng), [[0, 1],    [2, 3],    [4, 5],    [6]])
    self.assertEqual(ncd.chunk_indices( 8, 4, prng), [[0, 1],    [2, 3],    [4, 5],    [6, 7]])
    self.assertEqual(ncd.chunk_indices( 9, 4, prng), [[0, 1, 2], [3, 4],    [5, 6],    [7, 8]])
    self.assertEqual(ncd.chunk_indices(10, 4, prng), [[0, 1, 2], [3, 4, 5], [6, 7],    [8, 9]])
    self.assertEqual(ncd.chunk_indices(11, 4, prng), [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10]])
    self.assertEqual(ncd.chunk_indices(12, 4, prng), [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]])

  def test_index_to_pos(self):
    """
    - 0 1 2 3
      - 4 5 6
        - 7 8
          - 9
            -
    """
    self.assertEqual(ncd.index_to_pos(0, 5), (0, 1))
    self.assertEqual(ncd.index_to_pos(1, 5), (0, 2))
    self.assertEqual(ncd.index_to_pos(2, 5), (0, 3))
    self.assertEqual(ncd.index_to_pos(3, 5), (0, 4))

    self.assertEqual(ncd.index_to_pos(4, 5), (1, 2))
    self.assertEqual(ncd.index_to_pos(5, 5), (1, 3))
    self.assertEqual(ncd.index_to_pos(6, 5), (1, 4))
   
    self.assertEqual(ncd.index_to_pos(7, 5), (2, 3))
    self.assertEqual(ncd.index_to_pos(8, 5), (2, 4))
    
    self.assertEqual(ncd.index_to_pos(9, 5), (3, 4))

    for i, n in [(-1, 5), (10, 5), (0, 0), (0, 1)]:
      with self.assertRaises(ValueError):
        ncd.index_to_pos(i, n)

  def test_pairs(self):
    self.assertEqual(list(ncd.pairs(['a', 'b', 'c'], [1, 2, 3, 4], is_upper=False)),
        [('a', 1), ('a', 2), ('a', 3), ('a', 4),
         ('b', 1), ('b', 2), ('b', 3), ('b', 4),
         ('c', 1), ('c', 2), ('c', 3), ('c', 4),
        ])
    self.assertEqual(list(ncd.pairs(['a', 'b', 'c', 'd'], [1, 2, 3, 4], is_upper=True)),
        [('a', 2), ('a', 3), ('a', 4),
                   ('b', 3), ('b', 4),
                             ('c', 4),
        ])
    self.assertEqual(list(ncd.pairs(range(10), range(20), is_upper=False)),
        list(it.chain(
          ncd.pairs(range(10), range(20), is_upper=False, start=0, stop=73),
          ncd.pairs(range(10), range(20), is_upper=False, start=73, stop=156),
          ncd.pairs(range(10), range(20), is_upper=False, start=156))))
    self.assertEqual(list(ncd.pairs(range(20), range(20), is_upper=True)),
        list(it.chain(
          ncd.pairs(range(20), range(20), is_upper=True, start=0, stop=73),
          ncd.pairs(range(20), range(20), is_upper=True, start=73, stop=156),
          ncd.pairs(range(20), range(20), is_upper=True, start=156))))

compressor = c.get_compressor('zlib')

class Dialect(csv.excel):
  delimiter = ':'
factory = ds.create_factory('testdata/planets_with_name.txt', csv_dialect=Dialect)
sources = factory.get_sources()

zs = {
    'MERCURY': 72,
    'VENUS':   76,
    'EARTH':   69,
    'MARS':    75,
}

zxys = {
    ('MERCURY', 'MERCURY'): 76,
    ('MERCURY', 'VENUS'):   121,
    ('MERCURY', 'EARTH'):   114,
    ('MERCURY', 'MARS'):    117,

    ('VENUS', 'MERCURY'):   121,
    ('VENUS', 'VENUS'):     81,
    ('VENUS', 'EARTH'):     119,
    ('VENUS', 'MARS'):      123,

    ('EARTH', 'MERCURY'):   115,
    ('EARTH', 'VENUS'):     117,
    ('EARTH', 'EARTH'):     74,
    ('EARTH', 'MARS'):      116,

    ('MARS', 'MERCURY'):    117,
    ('MARS', 'VENUS'):      122,
    ('MARS', 'EARTH'):      116,
    ('MARS', 'MARS'):       78,
}

def expected_results(is_upper):
  planets = ['MERCURY', 'VENUS', 'EARTH', 'MARS']
  results = []
  for i, p1 in enumerate(planets):
    for j, p2 in enumerate(planets):
      if not is_upper or i < j:
        zx, zy, zxy = zs[p1], zs[p2], zxys[(p1, p2)]
        results.append(NcdResult(
          x=p1, zx=zx,
          y=p2, zy=zy,
          zxy=zxy,
          ncd=float(zxy - min(zx, zy))/max(zx, zy)))
  return results


class TestPipeline(object):
  def test_compress_sources(self):
    compressed_sources = ncd.compress_sources(sources, compressor, self.is_parallel)
    self.assertEqual(compressed_sources, zs)

  def _test_ncd_pairs(self, is_upper):
    res = ncd.ncd_pairs(sources, sources, compressor, is_upper=is_upper,
        is_parallel=self.is_parallel)
    results = res.get_results()
    sort_results = lambda rs: sorted(list(rs), key=lambda r: (r['x'], r['y']))
    self.assertEqual(
        sort_results(results),
        sort_results(expected_results(is_upper)))
    results.close()

  def test_ncd_pairs_upper(self):
    self._test_ncd_pairs(is_upper=True)
 
  def test_ncd_pairs_full(self):
    self._test_ncd_pairs(is_upper=False)


class TestSerial(TestPipeline, unittest.TestCase):
  def setUp(self):
    self.is_parallel = False


class TestParallel(TestPipeline, unittest.TestCase):
  def setUp(self):
    self.is_parallel = True
