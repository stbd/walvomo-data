# -*- encoding: utf-8 -*-

import json
import RepresentativeInfo_pb2

mapStrPartyToEnumParty = {
    'kd' : RepresentativeInfo_pb2.PoliticalPartyInfo.KD,
    'vihr' : RepresentativeInfo_pb2.PoliticalPartyInfo.VIHREAT,
    'kesk' : RepresentativeInfo_pb2.PoliticalPartyInfo.KESKUSTA,
    'vas' : RepresentativeInfo_pb2.PoliticalPartyInfo.VASEMMISTO,
    'kok' : RepresentativeInfo_pb2.PoliticalPartyInfo.KOKOOMUS,
    'sd' : RepresentativeInfo_pb2.PoliticalPartyInfo.SDP,
    'r' : RepresentativeInfo_pb2.PoliticalPartyInfo.RKP,
    'ps' : RepresentativeInfo_pb2.PoliticalPartyInfo.PS,
    'vr' : RepresentativeInfo_pb2.PoliticalPartyInfo.VASEMMISTO,
}
 
def fixHtmlSpecialChars(string):
    return string.replace('&auml;', u'ä').replace('&Auml;', u'Ä').replace('&ouml;', u'ö').replace('&Ouml;', u'Ö').replace('&eacute;', u'é').replace('&nbsp;', u' ').replace('&sol;',u'/')
 
def testIfFileExists(filename):
    try:
        open(filename, 'r')
    except Exception, e:
        return False;
    return True;

class NewsCollectionSource():
    def __init__(self):
        self.data = None
    
    def parseFromFile(self, f):
        dataTxt = f.read()
        self.data = json.loads(dataTxt)
        
    def writeToFile(self, f):
        f.write(json.dumps(self.data, indent=2))
 
class Representatives():
    def stripName(self, name):
        return name.strip().lower().replace('-', '').replace('', '')

    def hasRepresentative(self, name1, name2):
        for r in self.representatives:
            f = self.stripName(r.fName)
            l = self.stripName(r.lName)
            n1 = self.stripName(name1)
            n2 = self.stripName(name2)
            if (f == n1 and l == n2) or (f == n2 and l == n1):
                return True
        return False

    def findRepresentativeId(self, name1, name2):
        for r in self.representatives:
            f = self.stripName(r.fName)
            l = self.stripName(r.lName)
            n1 = self.stripName(name1)
            n2 = self.stripName(name2)
            if (f == n1 and l == n2) or (f == n2 and l == n1):
                return r.id
        print 'Did not find:', name1, name2
        raise Exception('Representative not found')

    def __init__(self):
        self.representatives = []
        self.data = json.loads('{"Representatives" : []}')

    def addRepresentative(self, rep):
        self.representatives.append(rep)

    def writeToFile(self, f):
        representativesList = []
        for r in self.representatives:
            attributes = {}
            attributes['Id'] = r.id
            attributes['FirstName'] = r.fName
            attributes['LastName'] = r.lName
            attributes['Seasons'] = r.activeSeasons
            attributes['Party'] = r.party
            attributes['Region'] = r.region
            attributes['Link'] = r.link
            representativesList.append(attributes)
        self.data['Representatives'] = representativesList
        f.write(json.dumps(self.data, indent=2))

    def parseFromFile(self, f):
        self.data = json.loads(f.read())
        representativesList = self.data['Representatives']
        for r in representativesList:
            rep = Representative()
            rep.fName = r['FirstName']
            rep.id = r['Id']
            rep.lName = r['LastName']
            rep.party = r['Party']
            rep.region = r['Region']
            rep.link = r['Link']
            rep.activeSeasons = r['Seasons']
            self.representatives.append(rep)

class Representative():
    def __init__(self):
        self.fName = None
        self.lName = None
        self.activeSeasons = None
        self.party = None
        self.region = None
        self.link = None
        self.id = None

class PoliticalSeasonsList():
    def __init__(self):
        self.startingYears = None
        self.currentSeason = None

    def parseFromFile(self, f):
        dataTxt = f.read()
        data = json.loads(dataTxt)
        self.startingYears = data['seasonsList']
        self.currentSeason = data['latestSeason']

class PoliticalSeasonInfo():
    def __init__(self):
        self.startYear = None
        self.endYear = None
        self.representativeIds = None
        self.monthsWithVotes = None
        self.data = None

    def parseFromFile(self, f):
        dataTxt = f.read()
        self.data = json.loads(dataTxt)
        self.startYear = self.data['StartingYear']
        self.endYear = self.data['EndingYear']
        self.representativeIds = self.data['RepresentativeIds']
        self.monthsWithVotes = self.data['MonthsWithVotes']

    def saveToFile(self, f):
        self.data['StartingYear'] = self.startYear
        self.data['EndingYear'] = self.endYear
        self.data['RepresentativeIds'] = self.representativeIds
        self.data['MonthsWithVotes'] = self.monthsWithVotes
        
        f.write(json.dumps(self.data))

class SeasonSeating():
    def __init__(self):
        self.listOfIdSeatPairs = {}
        self.listOfSeatChanges = []
        self.data = json.loads('{"IdToSeat":[], "SeatChanges": []}')

    def parseFromFile(self, f):
        self.data = json.loads(f.read())
        self.listOfIdSeatPairs = self.data['IdToSeat']
        self.listOfSeatChanges = self.data['SeatChanges']
        self.sanityChecks()

    def sanityChecks(self):
        usedSeats = []
        for id in self.listOfIdSeatPairs:
            for s in usedSeats:
                if s == self.listOfIdSeatPairs[id]:
                    print 'Two representatives with same seat, id2', id, 'seat', s
                    raise Exception('Two representatives with same seat')
            usedSeats.append(self.listOfIdSeatPairs[id])

    def saveToFile(self, f):
        self.sanityChecks()
        self.data['IdToSeat'] = self.listOfIdSeatPairs
        self.data['SeatChanges'] = self.listOfSeatChanges
        f.write(json.dumps(self.data, indent=2))

class Widgets():
    def __init__(self):
        self.data = None
        self.widgets = None
    
    def parseFromFile(self, f):
        self.data = json.loads(f.read())
        self.widgets = self.data['Widgets']

class News():
    def __init__(self):
        self.data = None

    def parseFromFile(self, f):
        dataTxt = f.read()
        self.data = json.loads(dataTxt)

