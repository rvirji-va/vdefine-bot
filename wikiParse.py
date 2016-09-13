from __future__ import print_function
import json
from collections import OrderedDict

def createJSON(defn):
	f = open('/db/teams/' + defn['id'] + '.json', 'w+')
	f.write('{"id":"'+defn['id']+'","definition":"'+defn['definition'].replace('\n',' ') +'"}')



wiki = open('wikiDefs.txt', 'r')
w = wiki.read()

defs = w.split('|-')
definitions = []
filenames = []
dictionary = OrderedDict()
for d in defs:
	ds = d.split('\n')
	for dd in ds:
		dd = dd.replace('|', '')
		dd = dd.strip()
		definitions.append(dd)

for d in range(len(definitions)):
	if d % 5 == 0:
		dictionary = {"definition":definitions[d+1] + (("\n" + definitions[d+2]) if definitions[d+2] else ""),
				"id": definitions[d]}
		filenames.append(dictionary)

for fil in filenames:
	print(fil['definition'])

for names in filenames:
	createJSON(names)
