"""Tests for datasource.py"""

import csv
import unittest

import datasource as ds

data = 'HARDDATA'
data_fname = 'testdata/data.bin'

class TestDatasource(object):
  """Abstract test for a data source"""

  def test_get_string(self):
    self.assertEqual(data, self.source.get_string())

  def test_get_filename(self):
    fname = self.source.get_filename()
    with open(fname) as f:
      self.assertEqual(data, f.read())

  def test_string_equals_file(self):
    data = self.source.get_string()
    fname = self.source.get_filename()
    with open(fname) as f:
      self.assertEqual(data, f.read())

  def tearDown(self):
    self.source.close()

class TestStringDatasource(TestDatasource, unittest.TestCase):
  def setUp(self):
    self.source = ds.String(data)

class TestFilenameDatasource(TestDatasource, unittest.TestCase):
  def setUp(self):
    self.source = ds.Filename(data_fname)

  def test_cache_data(self):
    source = ds.Filename(data_fname, cache_data=True)
    s1 = source.get_string()
    s2 = source.get_string()
    self.assertIs(s1, s2)

class TestConcatenationDatasource(TestDatasource, unittest.TestCase):
  def setUp(self):
    self.source = ds.Concatenation(ds.String('HARD'), ds.String('DATA'))

#####################  High-order magic!! #######################
#                                                               #
#  Creates classes dinamically extending unittest.TestCase to   #
# test extensively different lengths for string or file content #
#                                                               #
#################################################################
dynamic_test_classes = []

interleavings = {
    'Equal': ('HRDT', 'ADAA'),
    'FirstSmaller': ('HR', 'ADDATA'),
    'SecondSmaller': ('HRDTA', 'ADA'),
    'FirstEmpty': ('', 'HARDDATA'),
    'SecondEmpty': ('HARDDATA', ''),
}

def makeStringInterleavingSetUp(s1, s2):
  def setUp(self):
    self.source = ds.Interleaving(ds.String(s1), ds.String(s2), block_size=1)
  return setUp

for name, (s1, s2) in interleavings.items():
  # Equivalent to 
  #   class TestInterleavingStringDatasources_{name}(TestDatasource, unittest.TestCase):
  #     def setUp(self):
  #       self.source = ds.Interleaving(ds.String({s1}), ds.String({s2}))
  #
  dynamic_test_classes.append(
      type('TestInterleavingStringDatasources_%s' % name, (TestDatasource, unittest.TestCase), {
        'setUp': makeStringInterleavingSetUp(s1, s2),
      }))

interleaving_fname1 = 'testdata/interleave1'
interleaving_fname2 = 'testdata/interleave2'
def makeFileInterleavingSetUp(s1, s2):
  def setUp(self):
    print 'Interleaving files %s and %s' % (s1, s2)
    with open(interleaving_fname1, 'w') as f: f.write(s1)
    with open(interleaving_fname2, 'w') as f: f.write(s2)
    self.source = ds.Interleaving(
      ds.Filename(interleaving_fname1),
      ds.Filename(interleaving_fname2),
      block_size=1)
  return setUp

for name, (s1, s2) in interleavings.items():
  # Equivalent to 
  #   class TestInterleavingFileDatasources_{i}(TestDatasource, unittest.TestCase):
  #     def setUp(self):
  #       with open(interleaving_fname1, 'w') as f: f.write({s1})
  #       ...
  #
  #     def tearDown(self):
  #       fileInterleavingTearDown(self)
  
  dynamic_test_classes.append(
    type('TestInterleavingFileDatasources_%s' % name, (TestDatasource, unittest.TestCase), {
      'setUp': makeStringInterleavingSetUp(s1, s2),
    }))

def load_tests(loader, tests, pattern):
  suite = unittest.TestSuite()
  suite.addTests(tests)
  for test_class in dynamic_test_classes:
    tests = loader.loadTestsFromTestCase(test_class)
    suite.addTests(tests)
  return suite

planet_names = ['MERCURY', 'VENUS', 'EARTH', 'MARS']
planets = {
    'MERCURY': 'Kickass planet with rotation period equal to two-thirds of its revolution period',
    'VENUS': 'Very hot planet, maybe hotter than Mercury, due to its infernal greenhouse effect',
    'EARTH': 'The jewel of the Solar System, or at least it considers itself so...',
    'MARS': 'A dry and almost dead planet, with a thin atmosphere and two silly asteroid moons',
    }

class Dialect(csv.excel):
  delimiter = ':'
planets_with_name = 'testdata/planets_with_name.txt'
planets_wout_name = 'testdata/planets_wout_name.txt'
planets_dir = 'testdata/planets/'
planets_subset = 'testdata/planets_subset.txt'
indirect_fname = 'testdata/subdir/indirect.dat'
indirect_first_line = '#indirect ../planets_with_name.txt ../planets/'

class TestFileLinesFactory(unittest.TestCase):
  def test_get_sources_with_name(self):
    factory = ds.FileLinesFactory(planets_with_name, csv_dialect=Dialect)
    sources = factory.get_sources()
    self.assertEqual(4, len(sources))
    for source, expected_name in zip(sources, planet_names):
      name = source.name
      self.assertEqual(expected_name, name)
      self.assertEqual(planets[name], source.get_string())

  def test_get_sources_without_name(self):
    factory = ds.FileLinesFactory(planets_wout_name, csv_dialect=None)
    sources = factory.get_sources()
    self.assertEqual(4, len(sources))
    for source, name, expected_name in zip(sources, planet_names, ['0', '1', '2', '3']):
      self.assertEqual(expected_name, source.name)
      self.assertEqual(planets[name], source.get_string())

class TestDirectoryFactory(unittest.TestCase):
  def test_get_sources(self):
    factory = ds.DirectoryFactory(planets_dir)
    sources = factory.get_sources()
    self.assertEqual(4, len(sources))
    for source, expected_name in zip(sources, sorted(planet_names)):
      name = source.name
      self.assertEqual(expected_name, name)
      self.assertEqual(planets[name], source.get_string())

class TestInMemoryFactory(unittest.TestCase):
  def test_get_sources(self):
    sources = [ds.String(value, name=key) for key, value in planets.items()]
    factory = ds.InMemoryFactory(sources)
    for source in factory.get_sources():
      self.assertIs(planets[source.name], source.get_string())

class TestIndirectFactory(unittest.TestCase):
  def test_get_sources(self):
    factory = ds.DirectoryFactory(planets_dir)
    names = ['MERCURY', 'EARTH']
    indirect = ds.IndirectFactory(factory, names)
    sources = indirect.get_sources()
    self.assertEqual(2, len(sources))
    for source in indirect.get_sources():
      self.assertEqual(planets[source.name], source.get_string())
  
  def test_exception(self):
    factory = ds.DirectoryFactory(planets_dir)
    # Name not present
    with self.assertRaises(ValueError):
      ds.IndirectFactory(factory, ['MERCURY', 'VENUS', 'SATURN'])

  def test_parse_indirect_factory_file(self):
    with open(planets_subset) as f:
      factory = ds.parse_indirect_factory_file(f)
      sources = factory.get_sources()
      self.assertEqual(2, len(sources))
      for source in sources:
        self.assertEqual(planets[source.name], source.get_string())

    with self.assertRaises(ValueError), open(planets_with_name) as f:
      ds.parse_indirect_factory_file(f)

class TestCreateFactory(unittest.TestCase):
  def test_file_lines(self):
    factory = ds.create_factory(planets_with_name, csv_dialect=Dialect)
    sources = factory.get_sources()
    self.assertEqual(4, len(sources))
    for source in sources:
      self.assertEqual(planets[source.name], source.get_string())

  def test_directory(self):
    factory = ds.create_factory(planets_dir)
    sources = factory.get_sources()
    self.assertEqual(4, len(sources))
    for source in sources:
      self.assertEqual(planets[source.name], source.get_string())

  def test_mixed(self):
    factory = ds.create_factory([planets_with_name, planets_dir], csv_dialect=Dialect)
    sources = list(factory.get_sources())
    self.assertEqual(8, len(sources))
    for source in sources:
      self.assertEqual(planets[source.name], source.get_string())

  def test_indirect(self):
    factory = ds.create_factory(planets_subset)
    sources = factory.get_sources()
    self.assertEqual(2, len(sources))
    for source in sources:
      self.assertEqual(planets[source.name], source.get_string())

class TestIndirectFile(unittest.TestCase):
  def setUp(self):
    self.paths = [planets_with_name, planets_dir]
    factory = ds.create_factory(self.paths, csv_dialect=Dialect)
    all_sources = factory.get_sources()
    self.names = ['MERCURY', 'EARTH']
    self.sources = [source for source in all_sources if source.name in self.names]

  def test_indirect_file(self):
    ds.indirect_file(indirect_fname, self.paths, self.sources)
    with open(indirect_fname) as f:
      first_line = f.readline()
      self.assertEqual(indirect_first_line, first_line[:-1])
      lines = f.readlines()
      self.assertEqual(4, len(lines))
      for line in lines:
        self.assertIn(line[:-1], self.names)

  def test_inverse(self):
    ds.indirect_file(indirect_fname, self.paths, self.sources)
    factory = ds.create_factory(indirect_fname)
    sources = factory.get_sources()
    self.assertEqual(2, len(sources))
    for source in sources:
      self.assertEqual(planets[source.name], source.get_string())

