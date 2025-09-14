#!/usr/bin/python

import tree as tree

#t, m, l = tree.test_tree()
#
#print(t)
#print(m)
#print(l)

#tree.__name__ = '__main__'
if __name__ == '__main__':
  t, expected_m, expected_ids = tree.test_tree()
  ls = tree.leafs(t)
  ids = [l.content for l in ls]
  assert set(expected_ids) == set(ids)
  permutation = [ids.index(expected) for expected in expected_ids]

  m, ids = tree.distance_matrix(t)
  n = len(ids[0])
  m = [[m[i][j] for j in permutation] for i in permutation]
  assert m == expected_m
  
  print(m)

