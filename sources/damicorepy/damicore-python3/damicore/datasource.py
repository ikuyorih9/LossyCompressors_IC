"""Common data sources used to efficiently store and use compressors for NCD."""

import os
import sys
import tempfile
import shutil
import logging
import math
import csv

import itertools as it

from damicore._utils import dir_basename, format_num

class DataSource(object):
  """Abstract data source."""
  def __init__(self, name=None):
    self.name = name

  def get_string(self):
    """Returns the data provided by this source as a string."""
    raise NotImplementedError("get_bytes not implemented")

  def get_filename(self):
    """Returns a file name containing the data provided by this source."""
    raise NotImplementedError("get_filename not implemented")

  def close(self):
    """Releases any resource potentially created by this data source."""
    pass

  def _has_string(self):
    """Returns whether the data source has data cached."""
    raise NotImplementedError("_has_string not implemented")

  def _has_filename(self):
    """Returns whether the data source has a backing filename."""
    raise NotImplementedError("_has_filename not implemented")

class String(DataSource):
  """Data source from a string.

  If a temporary directory is provided, creates a file to provide a
  filename if/when get_filename is called.
  """
  def __init__(self, data, tmp_dir=tempfile.gettempdir(), name=None):
    DataSource.__init__(self, hash(data) if name is None else name)
    self.data = data
    self.tmp_dir = tmp_dir
    self.filename = None

  def get_string(self):
    return self.data

  def get_filename(self):
    if self.filename:
      return str(self.filename) # in the last version: return self.filename

    self.filename = tempfile.mktemp(dir=self.tmp_dir, prefix=str(hash(self.data)))
    if os.path.exists(self.filename):
      # This shouldn' happen at all, but...
      logger = logging.getLogger(__name__)
      logger.info('File %s already exists. First 100 bytes: %.100s' %
          (self.filename, self.data))

    with open(self.filename, 'w') as f:
      f.write(self.data)

    return self.filename

  def close(self):
    if self.filename:
      try:
        os.unlink(self.filename)
      except OSError: # Tempfile was already deleted
        pass
      self.filename = None

  def _has_string(self):
    return True

  def _has_filename(self):
    return self.filename

class Filename(DataSource):
  """Data source from a file name.
  
  If get_bytes is called, opens and read the file contents.
  """
  def __init__(self, fname, cache_data=False, name=None):
    DataSource.__init__(self, os.path.basename(fname) if name is None else name)
    self.fname = fname
    self.cache_data = cache_data

    self.has_data = False
    self.data = None

  def get_string(self):
    if self.cache_data and self.has_data:
      return self.data

    with open(self.fname, 'r') as f:
      data = f.read()
      if self.cache_data:
        self.data = data
        self.has_data = True

    return data

  def get_filename(self):
    return self.fname

  def close(self):
    if self.cache_data and self.has_data:
      self.has_data = False
      del self.data

  def _has_string(self):
    return self.has_data

  def _has_filename(self):
    return True

class Pairing(DataSource):
  """Abstract datasource that pairs two other datasources.

  This data source creates the concatenation lazily, only at the first request
  for a string or filename. It is then possible to create several datasources
  without filling up the memory with string pairs or the disk with file
  concatenations.

  Concrete implementations must implement _gen_string and _gen_filename, which
  should call, respectively, get_string() and get_filename() from the input
  sources and return a new source.
  This allows optimizing for when both sources are files, using file operations
  directly instead of slurping the whole file and dealing with strings.
  """

  def __init__(self, ds1, ds2, tmp_dir=tempfile.gettempdir()):
    DataSource.__init__(self, (ds1.name, ds2.name))
    self.ds1 = ds1
    self.ds2 = ds2
    self.tmp_dir = tmp_dir

    self.source = None
    self.has_created_file = False

  def _gen_filename(self):
    raise NotImplementedError("_gen_filename not implemented")

  def _gen_string(self):
    raise NotImplementedError("_gen_string not implemented")

  def _gen_source(self):
    if self.ds1._has_filename() and self.ds2._has_filename():
      self.source = self._gen_filename()
      self.has_created_file = True
    else:
      self.source = self._gen_string()

  def _get_source(self):
    if not self.source:
      self._gen_source()
    return self.source
    
  def get_string(self):
    return self._get_source().get_string()

  def get_filename(self):
    return str(self._get_source().get_filename())

  def close(self):
    if self.source:
      self.source.close()
      if self.has_created_file:
        os.unlink(self.source.get_filename())
      del self.source

  def _has_string(self):
    return self._get_source()._has_string()

  def _has_filename(self):
    return self._get_source()._has_filename()

class Concatenation(Pairing):
  """Datasource that concatenates two other sources."""

  def __init__(self, ds1, ds2, tmp_dir=tempfile.TemporaryDirectory()):#previously tempfile.gettempdir()):
    Pairing.__init__(self, ds1, ds2, tmp_dir)

  def _gen_filename(self):
    fname1, fname2 = self.ds1.get_filename(), self.ds2.get_filename()
    names = self.ds1.name, self.ds2.name

    #temp files are placed inb a default directory that depends on the platform
    # since dir is not specificed. Such a choice solved incompatibility when using it on Mac
    fd, tmpname = tempfile.mkstemp(prefix='%s++%s' % names)#, dir=self.tmp_dir)

    with os.fdopen(fd, 'w') as f,\
        open(fname1, 'r', errors='ignore') as s1, open(fname2, 'r', errors='ignore') as s2:
      shutil.copyfileobj(s1, f)
      shutil.copyfileobj(s2, f)

    return Filename(tmpname)

  def _gen_string(self):
    return String(
        self.ds1.get_string() + self.ds2.get_string(),
        self.tmp_dir)

class Interleaving(Pairing):
  """Datasource that interleave blocks for two other sources.

  This data source partitions both sources in blocks with fixed size, and then
  outputs these blocks interleaved.
  """

  def __init__(self, ds1, ds2, tmp_dir=tempfile.gettempdir(), block_size=1024):
    Pairing.__init__(self, ds1, ds2, tmp_dir)
    self.block_size = block_size

  def _gen_filename(self):
    fname1, fname2 = self.ds1.get_filename(), self.ds2.get_filename()
    names = str(self.ds1.name), str(self.ds2.name)

    fd, tmpname = tempfile.mkstemp(prefix='%s++%s' % names, dir=self.tmp_dir)
    with os.fdopen(fd, 'w') as f,\
        open(fname1, 'r', errors='ignore') as s1, open(fname2, 'r', errors='ignore') as s2:
      # Read chunks from both files and interleave them in the dest file.
      is_eof1, is_eof2 = False, False
      while not is_eof1 and not is_eof2:
        chunk1, chunk2 = s1.read(self.block_size), s2.read(self.block_size)
        f.write(chunk1 + chunk2)
        if len(chunk1) < self.block_size: is_eof1 = True
        if len(chunk2) < self.block_size: is_eof2 = True
      # Copy remainder of bigger file
      if not is_eof1 and is_eof2:
        shutil.copyfileobj(s1, f)
      if is_eof1 and not is_eof2:
        shutil.copyfileobj(s2, f)

    return Filename(tmpname)

  def _gen_string(self):
    s1, s2 = self.ds1.get_string(), self.ds2.get_string()
    # Calculates how many chunks per string
    num_chunks = lambda s: (len(s) + self.block_size - 1) / self.block_size
    n1, n2 = num_chunks(s1), num_chunks(s2)
    # Generators
    chunks = lambda s, b, n: (s[i * b : (i + 1) * b] for i in range(n))
    cs1, cs2 = chunks(s1, self.block_size, n1), chunks(s2, self.block_size, n2)
    zipped = it.izip_longest(cs1, cs2)          # abc, defgh -> ((a,d), (b,e), (c,f), (None,g), (None,h))
    flattened = it.chain.from_iterable(zipped)  #            -> (a, d, b, e, c, f, None, g, None, h)
    filtered = (x for x in flattened if x)      #            -> (a, d, b, e, c, f, g, h)
    interleaved = ''.join(filtered)             #            -> adbecfgh
    return String(interleaved, self.tmp_dir)

class DataSourceFactory(object):
  """Abstract factory for data sources."""
  def __init__(self, name=None):
    self.name = name

  def get_sources(self):
    raise NotImplementedError("get_sources not implemented")

class FileLinesFactory(DataSourceFactory):
  """Factory of string data sources from lines in a file."""
  def __init__(self, fname, tmp_dir=tempfile.gettempdir(),
      csv_dialect=csv.excel):
    DataSourceFactory.__init__(self, os.path.basename(fname))
    self.sources = []

    with open(fname, 'rt') as f:
      if csv_dialect: rows = list(csv.reader(f, csv_dialect))
      else:           rows = list([line[:-1]] for line in f)

    num_rows = len(rows)
    for i, row in enumerate(rows):
      if not row or not row[0]:
        # Ignore empty line
        continue
      if len(row) == 1:
        name = format_num(i, num_rows)
        data = row[0]
      else:
        name, data = row[0], row[1]
      string_source = String(data, tmp_dir, name)
      self.sources.append(string_source)

  def get_sources(self):
    return self.sources

class DirectoryFactory(DataSourceFactory):
  """Factory of file data sources from a directory."""
  def __init__(self, directory, cache_data=False):
    DataSourceFactory.__init__(self, dir_basename(directory))
    names = os.listdir(directory)
    self.fnames = sorted(os.path.join(directory, name) for name in names)
    self.sources = list(Filename(fname, cache_data) for fname in self.fnames)

  def get_sources(self):
    return self.sources

class InMemoryFactory(DataSourceFactory):
  """Factory of already created datasources."""
  def __init__(self, sources):
    names = tuple(source.name for source in sources)
    DataSourceFactory.__init__(self, names)
    self.sources = sources

  def get_sources(self):
    return self.sources

class CollectionFactory(DataSourceFactory):
  """Factory of data sources from a collection of factories."""
  def __init__(self, factories):
    self.factories = list(factories)
    basenames = '_'.join(factory.name for factory in self.factories)
    DataSourceFactory.__init__(self, basenames)
    self.sources = list(self._get_sources())

  def _get_sources(self):
    for factory in self.factories:
      for source in factory.get_sources():
        yield source

  def get_sources(self):
    return self.sources

class DirectoriesFactory(CollectionFactory):
  """Factory of file data sources from several directories."""
  def __init__(self, directories, cache_data=False):
    factories = [DirectoryFactory(directory, cache_data)
        for directory in directories]
    CollectionFactory.__init__(self, factories)

class FilesFactory(CollectionFactory):
  """Factory of lines data sources from several files."""
  def __init__(self, filenames, tmp_dir=tempfile.gettempdir(),
      csv_dialect=csv.excel):
    factories = [FileLinesFactory(filename, tmp_dir, cache_data)
        for filename in filenames]
    CollectionFactory.__init__(self, factories)

class IndirectFactory(DataSourceFactory):
  """Factory of pointers to another's factory sources."""
  def __init__(self, factory, names):
    DataSourceFactory.__init__(self,
        '%s-%s' % (factory.name, str(len(names)) if names else 'all'))
    # If names is empty, use all sources from factory.
    if not names:
      self.sources = factory.get_sources()
      return

    self.sources = []
    name_set = set(names)
    for source in factory.get_sources():
      if source.name in name_set:
        name_set.discard(source.name)
        self.sources.append(source)
    if name_set:
      raise ValueError("Names were not found in factory: %s" % name_set)

  def get_sources(self):
    return self.sources

def parse_indirect_factory_file(f, **kwargs):
  reader = csv.reader(f, delimiter=' ')
  line = reader.next()
  if not line[0] == '#indirect':
    raise ValueError('Not an indirect factory')

  filedir = os.path.dirname(f.name)
  rel_inputs = line[1:]
  inputs = [os.path.join(filedir, rel_input) for rel_input in rel_inputs]
  names = [name for name, in reader]
  factory = IndirectFactory(create_factory(inputs, **kwargs), names)
  factory.name = os.path.basename(f.name)
  return factory

def indirect_file(filename, paths, sources):
  """Creates an indirect factory file, that uses paths as factory."""
  rel = os.path.dirname(filename)
  relpaths = []

  for path in paths:
    # Paths in file must be relative to file location.
    # File: /home/user/my/location/indirect/file.txt
    # Dataset: /home/user/my/fantastic/dataset.dat
    # Path relative to file: ../../fantastic/dataset.dat
    basedir, basename = os.path.dirname(path), os.path.basename(path)
    reldirpath = os.path.relpath(basedir, start=rel)
    relpath = os.path.join(reldirpath, basename)
    relpaths.append(relpath)
  with open(filename, 'w') as f:
    w = csv.writer(f, delimiter=' ', lineterminator='\n')
    w.writerow(['#indirect'] + relpaths)
    w.writerows([source.name] for source in sources)

def create_factory(inputs, cache_data=False, tmp_dir=tempfile.gettempdir(),
    csv_dialect=csv.excel):
  """Create a factory given an input or input names, checking for each if it
  is a directory or file."""
  factory = _create_factory(inputs, cache_data, tmp_dir, csv_dialect)
  factory.inputs = inputs
  return factory

def _create_factory(inputs, cache_data=False, tmp_dir=tempfile.gettempdir(),
    csv_dialect=csv.excel):
  if isinstance(inputs, str): #basestring): in last version - in Python 2, basestring was an way of transition from plain strings to unicode
    input_name = inputs
    if os.path.isdir(input_name):
      return DirectoryFactory(input_name, cache_data)
    try:
      with open(input_name) as f:
        return parse_indirect_factory_file(f, cache_data=cache_data, tmp_dir=tmp_dir,
            csv_dialect=csv_dialect)
    except ValueError:
      return FileLinesFactory(input_name, tmp_dir, csv_dialect)

  return CollectionFactory(
    create_factory(input_name, cache_data, tmp_dir, csv_dialect)
      for input_name in inputs)

