"""General and miscellanous utilities"""

import os
import sys
import math
import argparse
from contextlib import contextmanager
from pkg_resources import resource_string

def safediv(a, b):
  try:
    return float(a) / b
  except ZeroDivisionError:
    zero_sign = math.copysign(1.0, b)
    positive_inf = float("Inf")
    negative_inf = float("-Inf")
    if a > 0: return positive_inf if zero_sign > 0 else negative_inf
    if a < 0: return negative_inf if zero_sign > 0 else positive_inf
    return float("nan")

def format_num(i, n):
  num_digits = int(math.ceil(math.log10(n)))
  return '{num:0{len}}'.format(num=i, len=num_digits)

def frequency(v):
  freq = {}
  for x in v:
    freq[x] = freq.get(x, 0) + 1
  return freq

def choose_most_frequent(v, just_one=True):
  freq = frequency(v)
  max_freq = max(freq.values())
  max_keys = [k for k, v in freq.items() if v == max_freq]

  if just_one: return random.choice(max_keys)
  return max_keys

def transpose(m):
  t = {}
  for k, v in m.items():
    if v in t: t[v].append(k)
    else:      t[v] = [k]
  return t

def score(x, mean, sd, constant=1):
  return constant + float(x - mean)/sd

def mean(xs):
  return float(sum(xs)) / len(xs)

def mean_sd(xs):
  n = len(xs)
  mean = float(sum(xs)) / n
  var = sum((x - mean)**2 for x in xs) / n
  sd = math.sqrt(var)
  return mean, sd

def normalize_list(xs, constant=1):
  mean, sd = mean_sd(xs)
  scores = [score(x, mean, sd, constant) for x in xs]
  min_score = min(scores)
  return [constant + (s - min_score) for s in scores]

def dir_basename(directory):
  name = os.path.basename(directory)
  if len(name) == 0:
    # Removes trailing slash
    # os.path.basename('dir/subdir/subsubdir/') -> ''
    # os.path.basename('dir/subdir/subsubdir') -> 'subsubdir'
    name = os.path.basename(directory[:-1])
  return name

def listify(x):
  if isinstance(x, basestring):
    return [x]
  return list(x)

@contextmanager
def open_outfile(output):
  """Opens the provided file, or return stdout if None."""
  if output:
    with open(output, 'wt') as f:
      yield f
  else:
    yield sys.stdout

def linecount(filename):
  with open(filename, 'r') as f:
    return len(f)

def get_version():
  return resource_string("damicore", "VERSION")

def cli_parser():
  parser = argparse.ArgumentParser(add_help=False,
      description='General options for command-line inputs')

  parser.add_argument('input', nargs='+', help='Script inputs')
  parser.add_argument('-o', '--output',
      help='Output file (default: stdout)')

  misc_group = parser.add_argument_group('Miscellaneous options',
      'Miscellaneous options')
  misc_group.add_argument('--serial', action='store_true',
      help='Compute compressions serially')
  misc_group.add_argument('--parallel', action='store_true',
      help='Compute compressions in parallel (default)')

  misc_group.add_argument('-v', '--verbose', action='count',
      help='Verbose output. Repeat to increase verbosity level (default: 1)',
      default=1)
  misc_group.add_argument('--no-verbose', action='store_true',
      help='Turn verbosity off')

  misc_group.add_argument('-V', '--version', action='version',
      version=get_version())

  return parser

def parse_args(args):
  return {
      'input': args.input,
      'output': args.output,
      'is_parallel': args.parallel or not args.serial,
      'verbosity': 0 if args.no_verbose else args.verbose,
      }
