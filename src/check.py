#!/usr/bin/env python

from json import load

d = load(open('log.json'))

l = [k for k in d if 'GoTeamVim!' in dict(d[k]).values()]
for w in l:
    print w
print '{} winners!'.format(len(l))

# print sorted([d[k][-1] for k in d])
