#!/usr/bin/python

"""Basic functions and types for NCD"""

import csv
import tempfile

import datasource as ds

class NcdResult(dict):
  fields = ['x', 'y', 'zx', 'zy', 'zxy', 'ncd']

def ncd(compressor, ds1, ds2, compressed_sizes=None,
    tmp_dir=tempfile.gettempdir(),
    interleave_block_size=0):
  """NCD calculation for a given pair of data sources.

      The normalized compression distance (NCD) between a pair of objects (x, y) 
  is defined as

                   Z(p(x,y)) - min{ Z(x), Z(y) }
      NCD_Z(x,y) = -----------------------------
                        max{ Z(x), Z(y) }

      where Z is the size of the compression of a given object and p is a
  pairing function that creates an object from two others. Theoretically, this
  distance is normalized between 0 and 1:
      NCD(x,x) == 0 and
      NCD(x,y) == 1 <=> Z(x) + Z(y) == Z(p(x,y))

      By default, the pairing function is simple concatenation.
      If interleave_block_size > 0, the pairing function will interleave byte
      blocks with the provided size from both files.
  """
  if compressed_sizes:
    sizes = (compressed_sizes[ds1.name], compressed_sizes[ds2.name])
  else:
    sizes = (compressor.compressed_size(ds1), compressor.compressed_size(ds2))

  if interleave_block_size > 0:
    pair_ds = ds.Interleaving(ds1, ds2, tmp_dir=tmp_dir,
        block_size=interleave_block_size)
  else:
    pair_ds = ds.Concatenation(ds1, ds2, tmp_dir=tmp_dir)
  paired_compressed_size = compressor.compressed_size(pair_ds)
  pair_ds.close()

  minimum, maximum = sorted(sizes)
  result = NcdResult(
      x=ds1.name, y=ds2.name,
      zx=sizes[0], zy=sizes[1],
      zxy=paired_compressed_size,
      ncd=float(paired_compressed_size - minimum)/maximum)
  return result

def csv_write(outfile, results, output_header=True):
  writer = csv.DictWriter(outfile, fieldnames=NcdResult.fields)
  if output_header:
    writer.writeheader()
  for result in results:
    writer.writerow(result)

def csv_read(infile):
  # Automatically detect dialect
  sample = infile.read(1000)
  sniffer = csv.Sniffer()
  dialect = sniffer.sniff(sample)
  infile.seek(0) # Return to start of file

  reader = csv.DictReader(infile, dialect=dialect)
  for row in reader:
    x, y = row['x'], row['y']
    zx, zy, zxy = int(row['zx']), int(row['zy']), int(row['zxy'])
    ncd = float(row['ncd'])
    yield NcdResult(x=x, y=y, zx=zx, zy=zy, zxy=zxy, ncd=ncd)
