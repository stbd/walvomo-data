
import sys
import codecs
import dataProcessingLib

defaultFileToUse = '../data/data_representatives.txt'

def handleRepresentative(f, year, output):
    rep = dataProcessingLib.Representative()
    try:
        rep.parseFromFile(f)
    except Exception, e:
        return False

    if rep.activeSeasons.find(year) != -1:
        output.write(unicode(rep.id) + '\n' + rep.lName + '\n')
    return True


if len(sys.argv) != 2:
    print 'Usage: python ' + sys.argv[0] + ' [SeasonStartingYear]'
    sys.exit(1)


o = codecs.open('../data/data_Seating:' + sys.argv[1] + '.txt', 'w', 'utf-8')
f = codecs.open(defaultFileToUse, 'r', 'utf-8')
while 1:
    if not handleRepresentative(f, sys.argv[1], o):
        break
f.close()
o.close()
