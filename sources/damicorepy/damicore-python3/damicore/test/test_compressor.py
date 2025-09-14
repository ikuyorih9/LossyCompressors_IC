"""Tests for compressor package"""

import unittest

import compressor as c
import datasource as ds

class TestCompressor(object):
 
  def test_available(self):
    self.assertIn(self.name, c.list_compressors())

  def test_compressed_size(self):
    datasrc = ds.Filename('testdata/planets/EARTH')
    compressor = c.get_compressor(self.name)
    self.assertEqual(self.size, compressor.compressed_size(datasrc))


class TestZlib(TestCompressor, unittest.TestCase):
  def setUp(self):
    self.name = 'zlib'
    self.size = 69

class TestGzip(TestCompressor, unittest.TestCase):
  def setUp(self):
    self.name = 'gzip'
    self.size = 87

class TestBz2(TestCompressor, unittest.TestCase):
  def setUp(self):
    self.name = 'bz2'
    self.size = 91

class TestBzip2(TestCompressor, unittest.TestCase):
  def setUp(self):
    self.name = 'bzip2'
    self.size = 91

class TestPpmd(TestCompressor, unittest.TestCase):
  def setUp(self):
    self.name = 'ppmd'
    self.size = 78

class TestPaq8(TestCompressor, unittest.TestCase):
  def setUp(self):
    self.name = 'paq8'
    self.size = 94

