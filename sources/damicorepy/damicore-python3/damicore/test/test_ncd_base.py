"""Tests for ncd_base"""

import unittest

import datasource as ds
import compressor as c
from ncd_base import ncd, NcdResult

src1 = ds.Filename('testdata/planets/MERCURY')
src2 = ds.Filename('testdata/planets/VENUS')
baseResult = NcdResult(x='MERCURY', y='VENUS')
 
class TestCompressorNcd(object):
  def test_ncd(self):
    compressor = c.get_compressor(self.name)
    res = ncd(compressor, src1, src2)
    self.assertEqual(res, self.expected_result)


class TestZlib(TestCompressorNcd, unittest.TestCase):
  def setUp(self):
    self.name = 'zlib'
    self.expected_result = NcdResult(
        baseResult,
        zx=72, zy=76, zxy=121,
        ncd=(121 - 72)/76.)


class TestGzip(TestCompressorNcd, unittest.TestCase):
  def setUp(self):
    self.name = 'gzip'
    self.expected_result = NcdResult(
        baseResult,
        zx=92, zy=94, zxy=154,
        ncd=(154 - 92)/94.)
 

class TestBz2(TestCompressorNcd, unittest.TestCase):
  def setUp(self):
    self.name = 'bz2'
    self.expected_result = NcdResult(
        baseResult,
        zx=95, zy=103, zxy=151,
        ncd=(151 - 95)/103.)


class TestBzip2(TestCompressorNcd, unittest.TestCase):
  def setUp(self):
    self.name = 'bzip2'
    self.expected_result = NcdResult(
        baseResult,
        zx=95, zy=103, zxy=151,
        ncd=(151 - 95)/103.)


class TestPpmd(TestCompressorNcd, unittest.TestCase):
  def setUp(self):
    self.name = 'ppmd'
    self.expected_result = NcdResult(
        baseResult,
        zx=86, zy=86, zxy=147,
        ncd=(147 - 86)/86.)


class TestPaq8(TestCompressorNcd, unittest.TestCase):
  def setUp(self):
    self.name = 'paq8'
    self.expected_result = NcdResult(
        baseResult,
        zx=99, zy=102, zxy=168,
        ncd=(168 - 99)/102.)

