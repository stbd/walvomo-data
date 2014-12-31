# -*- encoding: utf-8 -*-

import httplib
import sys
import codecs
import dataProcessingLib

outputDir = '../data/'
httpParameters = {'Accept-Charset' : 'ISO-8859-1', 'Accept' : 'text/html,application/xhtml+xml,application/xml'}
nameListStartTag = '<div class="listing">'
nameListEndTag = 'id=\"luettelo-loppu'

def parseElementData(data):
    s = data.find('>') + 1
    e = data[s:].find('<')
    return data[s:s+e].strip()

def findSegment(data, startingIndex, startTag, endTag):
        start = data[startingIndex:].find(startTag)
        end = data[startingIndex+start+1:].find(endTag) + len(endTag) + 1
        return startingIndex + start, startingIndex + start + end

def fixHtmlSpecialChars(string):
        return string.replace('&auml;', u'ä').replace('&Auml;', u'Ä').replace('&ouml;', u'ö').replace('&Ouml;', u'Ö').replace('&eacute;', u'é').replace('&nbsp;', u' ')

def parseAttribute(data, attr):
    s = data.find(attr) + len(attr)
    valStart = data[s:].find('\"') + 1 + s
    e = data[valStart:].find('\"') + valStart
    return data[valStart:e]

if len(sys.argv) != 1:
    print 'Usage: python ' + sys.argv[0]
    sys.exit(1)

con = httplib.HTTPConnection('www.eduskunta.fi')
con.request('GET', '/triphome/bin/hex3000.sh?LAJITNIMI=$', "", httpParameters)

rsp = con.getresponse()
if rsp.status != 200:
    print 'Opening of votes list page failed, reason: ' + str(rsp.reason) + ' (' + str(rsp.status) + ')'
    sys.exit(1)

pageData = unicode(rsp.read(), 'ISO-8859-1')
s = pageData.find(nameListStartTag) + len(nameListStartTag)
e = pageData.find(nameListEndTag) 

data = pageData[s:e]
i = 0

reps = dataProcessingLib.Representatives()
filename = outputDir + 'data_representatives.txt'

if dataProcessingLib.testIfFileExists(filename):
    inputFile = codecs.open(filename, 'r', 'utf-8')
    reps.parseFromFile(inputFile)
    inputFile.close()

representative1d = len(reps.representatives) + 1
print 'representative1d initialized to', representative1d
while 1:
    s, e = findSegment(data, i, '<a href=', '</a>')
    if s == -1 or e == -1 or s >= len(data):
        break
    name = parseElementData(data[s:e])
    link = parseAttribute(data[s:e], 'href')

    i = e
    s, e = findSegment(data, i, '<td >', '</td>')
    if s == -1 or e == -1:
        break
    region = parseElementData(data[s:e])
    i = e

    if len(name) == 0 or len(region) == 0:
        break

    name = fixHtmlSpecialChars(name)
    region = fixHtmlSpecialChars(region)

    nameList = name.split(' ')
    party = nameList[-1][1:]
    lName = nameList[0]
    fName = ' '.join(nameList[1:-1])

    if not reps.hasRepresentative(fName, lName):
        rep = dataProcessingLib.Representative()
        rep.fName = fName
        rep.lName = lName
        rep.id = representative1d
        rep.party = party
        rep.region = region
        rep.activeSeasons = '2011'
        #Seems that for some reason, links seem to expire
        rep.link = 'http://www.eduskunta.fi/triphome/bin/hex3000.sh?LAJITNIMI=$'
        #rep.link = 'http://www.eduskunta.fi' + link
        reps.addRepresentative(rep)
    else:
        print 'Skipping representative ' + fName + ' ' + lName + ' because it exist already'

    representative1d = representative1d + 1

outputFile = codecs.open(filename, 'w', 'utf-8')
reps.writeToFile(outputFile)
outputFile.close()

