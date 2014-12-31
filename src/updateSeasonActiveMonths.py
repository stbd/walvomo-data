# -*- encoding: utf-8 -*-

import glob
import sys
import dataProcessingLib
import codecs
import datetime
import os


def monthSort(x, y):
    if x['year'] != y['year']:
        return y['year'] - x['year']
    else:
        return y['month'] - x['month']

discradOldValues = False
if not (len(sys.argv) == 2 or len(sys.argv) == 3):
    print 'Usage:', sys.argv[0], '[season starting year] [discard old values, set to one]'
    sys.exit(1)

if len(sys.argv) == 3:
    discradOldValues = True

seasonName = '../data/data_PoliticalSeasonInfo:' + sys.argv[1] + '.txt'
s = dataProcessingLib.PoliticalSeasonInfo()
f = codecs.open(seasonName, 'r', 'utf-8')
s.parseFromFile(f)
f.close()

if discradOldValues:
    s.monthsWithVotes = []

if s.endYear == 0:
    endYear = datetime.datetime.now().year

print 'Season range:', s.startYear, '-', endYear 
for y in range(s.startYear, endYear+1):
    path = '../data/data_VoteList:' + unicode(y) + '*.bin'
    #print path
    files = sorted(glob.glob(path))
    #print files
    for f in files:
        f = os.path.basename(f)
        month = f.split('.')[1]
        monthInfo = {u'month': int(month), u'year': y}
        if s.monthsWithVotes.count(monthInfo) == 0:
            s.monthsWithVotes.append(monthInfo)
        else:
            print str(monthInfo) + ' already exists, skipping'
        #print f.split('.')[1]

s.monthsWithVotes = sorted(s.monthsWithVotes, cmp=monthSort)
#print s.monthsWithVotes

f = codecs.open(seasonName, 'w', 'utf-8')
s.saveToFile(f)
f.close()




