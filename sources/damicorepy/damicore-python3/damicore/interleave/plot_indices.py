# -*- encoding: utf-8 -*-
import csv
import os

import pandas

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

if __name__ == '__main__':

  df = pandas.read_csv('interleave/indices.csv', index_col=0)

  fig, ((prec, rec), (f1, matthews)) = plt.subplots(nrows=2, ncols=2, sharex=True, sharey=True)
  axes = [prec, rec, f1, matthews]
  for ax, index in zip(axes, ['precision', 'recall', 'f1', 'matthews']):
    ax.semilogx(df.index[1:], [df[index][0] for x in df.index[1:]], basex=2,
        color='red', ls='dotted', label=u'Concatenação')
    ax.semilogx(df[index][1:], basex=2, color='blue', label=u'Intercalação')
    ax.set_title({
      'precision': u'Precisão',
      'recall': u'Sensitividade',
      'f1': u'F',
      'matthews': 'Matthews',
    }[index])
    ax.legend(loc='lower right', fontsize=10)

  xlabel = fig.text(0.5, -0.025, u'Tamanho de bloco', ha='center')
  ylabel = fig.text(-0.025, 0.5, u'Índice', va='center', rotation=90)
  fig.tight_layout(pad=1)
  fig.savefig('interleave/indices.svg', bbox_extra_artists=[xlabel, ylabel], bbox_inches='tight')
