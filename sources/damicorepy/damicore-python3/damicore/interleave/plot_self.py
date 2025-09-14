# -*- encoding: utf-8 -*-

import os
import pandas

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

dataset_dir = '../../dataset/binaries'
fnames = os.listdir(dataset_dir)
size = lambda fname: os.stat(os.path.join(dataset_dir, fname)).st_size
sizes = dict((fname, size(fname)) for fname in fnames)

if __name__ == '__main__':
  df = pandas.read_csv('interleave/self.csv', index_col=0)

  xticks = [2**4, 2**8, 2**12, 2**16]
  minor_xticks = [2**i for i in xrange(4, 17)]
  xlabels = [u'2\u2074', u'2\u2078', u'2\u00b9\u00b2', u'2\u00b9\u2076']

  fig, ((io1, cpu1), (io2, cpu2), (io3, cpu3)) = plt.subplots(nrows=3, ncols=2, sharex=True, sharey=True)
  io_axes = [io1, io2, io3]
  cpu_axes = [cpu1, cpu2, cpu3]
  all_axes = io_axes + cpu_axes
  instances = ['randrw', 'io_thrash', 'genisoimage', 'vecsum----', 'fractal---', 'mandelbulber']
  
  for ax, instance in zip(all_axes, instances):
    ax.set_xscale('log')
    ax.set_xlim((8, 65536))
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    ax.set_xticks(minor_xticks, minor=True) 
    
    ax.set_yscale('log')
    ax.set_ylim([0.01, 1.5]) 
    ax.set_yticklabels([0.01, 0.1, 1])
    
    ax.set_title('%s (%d KiB)' % (
        instance.replace('-', ''),
        sizes[instance] / 1024))
    
    ax.axhline(df[instance][0], color='r')
    ax.plot(df.index[1:], df[instance][1:], color='b')
    
    ax.get_lines()[0].set_linestyle('dotted')

  io2.set_ylabel('NCD(x,x)')

  concat = mpatches.Patch(color='red', label=u'Concatenação', ls='dotted')
  inter = mpatches.Patch(color='blue', label=u'Intercalação')
  legend = fig.legend(
    handles = [concat, inter],
    labels=[u'Concatenação', u'Intercalação'],
    bbox_to_anchor=(0.85, 0.95), loc=2, borderaxespad=0.)

  xlabel = fig.text(0.5, -0.025, u'Tamanho de bloco', ha='center')
  fig.tight_layout(pad=1)
  fig.savefig('interleave/self.svg', bbox_extra_artists=[legend, xlabel], bbox_inches='tight')
