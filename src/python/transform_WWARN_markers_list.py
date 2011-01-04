import sys

from pprint import pprint

markersIn = open(sys.argv[1])
markersOut = open(sys.argv[2], 'w')

markersDict = {}
for line in markersIn:
    elems = line.rstrip('\n').split('\t')

    if elems[2] == 'null':
        continue

    (locusName, locusPos, genotype) = (elems[0], elems[1], elems[2])

    markersDict.setdefault(locusName + locusPos, [])
    markersDict[locusName + locusPos].append(genotype)

for marker in markersDict:
    # Add 'No Data' and 'Null' to our list of markers here
    markersDict[marker].extend(['No Data', 'Null'])

    markersOut.write("%s\t%s\n" % (marker, ",".join(markersDict.get(marker))))
