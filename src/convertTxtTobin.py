
import RepresentativeInfo_pb2
import sys
import argparse
import codecs
import glob
import dataProcessingLib
import PoliticalSeason_pb2 
import SiteNews_pb2
#import VisualWidget_pb2
import datetime

debugPrints = False

def createRepresentativeProtoBufObjects(f):
    representatives = dataProcessingLib.Representatives()
    representatives.parseFromFile(f)
    for r in representatives.representatives:
        rep = RepresentativeInfo_pb2.RepresentativeInfo()
        rep.firstName = r.fName
        rep.lastName = r.lName
        rep.id = r.id
        rep.infoLink = r.link
        rep.currentPoliticalParty.party = dataProcessingLib.mapStrPartyToEnumParty[r.party]
        rep.currentPoliticalParty.region = r.region

        filename = u'../data/data_RepresentativeInfo:' + unicode(r.id) + u'.bin'

        fo = open(filename, 'w')
        fo.write(rep.SerializeToString())
        fo.close()

def createRepresentativeSeatingInfo(seatingFilename, representativesFilename):
    seating = RepresentativeInfo_pb2.PoliticalSeasonSeating()
    seatingDb = dataProcessingLib.SeasonSeating()
    representatives = dataProcessingLib.Representatives()
    f = codecs.open(seatingFilename, 'r', 'utf-8')
    seatingDb.parseFromFile(f)

    repsFile = codecs.open(representativesFilename, 'r', 'utf-8')
    representatives.parseFromFile(repsFile)
    repsFile.close()
    
    for id in seatingDb.listOfIdSeatPairs:
        seatInfo = seating.representativeSeat.add()
        seatInfo.seat = int(seatingDb.listOfIdSeatPairs[id])
        seatInfo.representativeKey = int(id)

        found = False
        for r in representatives.representatives:
            if int(r.id) == int(id):
                seatInfo.partyId = dataProcessingLib.mapStrPartyToEnumParty[r.party]
                found = True
                break
        if not found:
            raise Exception('Representative not found in createRepresentativeSeatingInfo with id')


    for c in seatingDb.listOfSeatChanges:
        change = seating.seatChange.add()
        change.reason = seatingDb.listOfSeatChanges[c]['Reason']
        change.representativeSeat.seat = seatingDb.listOfSeatChanges[c]['Seat']
        change.representativeSeat.representativeKey = int(c)
        found = False
        for r in representatives.representatives:
            if int(r.id) == int(c):
                change.representativeSeat.partyId = dataProcessingLib.mapStrPartyToEnumParty[r.party]
                found = True
                break
        if not found:
            raise Exception('Representative not found in createRepresentativeSeatingInfo with id')
        
        

    sOut = seatingFilename.replace('.txt', '.bin')
    sOutF = open(sOut, 'w')
    sOutF.write(seating.SerializeToString())
    sOutF.close()
    f.close()

def createPoliticalPartyNameInfo(outputFilename):
    partyInfo = RepresentativeInfo_pb2.PoliticalPartyNames()

    partyName1 = partyInfo.party.add()
    partyName1.party = RepresentativeInfo_pb2.PoliticalPartyInfo.RKP
    partyName1.name = u'RKP'

    partyName2 = partyInfo.party.add()
    partyName2.party = RepresentativeInfo_pb2.PoliticalPartyInfo.KOKOOMUS
    partyName2.name = u'Kokoomus'

    partyName3 = partyInfo.party.add()
    partyName3.party = RepresentativeInfo_pb2.PoliticalPartyInfo.KD
    partyName3.name = u'Kristilliset'

    partyName4 = partyInfo.party.add()
    partyName4.party = RepresentativeInfo_pb2.PoliticalPartyInfo.KESKUSTA
    partyName4.name = u'Keskusta'

    partyName5 = partyInfo.party.add()
    partyName5.party = RepresentativeInfo_pb2.PoliticalPartyInfo.PS
    partyName5.name = u'PS'

    partyName6 = partyInfo.party.add()
    partyName6.party = RepresentativeInfo_pb2.PoliticalPartyInfo.VIHREAT
    partyName6.name = u'Vihreat'

    partyName7 = partyInfo.party.add()
    partyName7.party = RepresentativeInfo_pb2.PoliticalPartyInfo.SDP
    partyName7.name = u'SDP'

    partyName8 = partyInfo.party.add()
    partyName8.party = RepresentativeInfo_pb2.PoliticalPartyInfo.VASEMMISTO
    partyName8.name = u'Vasemmisto'

    sOutF = open(outputFilename, 'w')
    sOutF.write(partyInfo.SerializeToString())
    sOutF.close()

def createSeasonsListInfo(filename):
    seasons = 0
    seasonsListBin = PoliticalSeason_pb2.PoliticalSeasonsList()
    f = codecs.open(filename, 'r', 'utf-8')
    seasonsListTxt = dataProcessingLib.PoliticalSeasonsList()
    seasonsListTxt.parseFromFile(f)
    
    seasonsListBin.PoliticalSeasonsStartingYears.extend(seasonsListTxt.startingYears)
    seasonsListBin.latestSeason = seasonsListTxt.currentSeason
    
    sOut = filename.replace(u'.txt', u'.bin')
    sOutF = open(sOut, 'w')#, 'utf-8')
    sOutF.write(seasonsListBin.SerializeToString())
    sOutF.close()
    f.close()

def createPoliticalSeasonInfo(filename):
    f = codecs.open(filename, 'r', 'utf-8')
    seasonInfo = dataProcessingLib.PoliticalSeasonInfo()
    seasonInfo.parseFromFile(f)
    f.close()

    seasonBin = PoliticalSeason_pb2.PoliticalSeason()
    seasonBin.startYear = seasonInfo.startYear
    seasonBin.endYear = seasonInfo.endYear
    seasonBin.representativeIds.extend(seasonInfo.representativeIds)

    for m in seasonInfo.monthsWithVotes:
        month = seasonBin.monthsContainingVotes.add()
        month.month = m['month']
        month.year = m['year']

    sOut = filename.replace(u'.txt', u'.bin')
    sOutF = open(sOut, 'w')
    sOutF.write(seasonBin.SerializeToString())
    sOutF.close()

def convertNews():
    f = open('../data/data_sitenews.txt')
    newsData = dataProcessingLib.News()
    newsData.parseFromFile(f)
    newsItems = newsData.data['News']

    newsItemsByDate = {}

    for e in newsItems:
        if e.has_key('NotPublished'):
            continue
        
        dateStr = e['Published'].split(' ')[0].split('.')
        timeStr = e['Published'].split(' ')[1].split('.') 
        date = datetime.datetime(int(dateStr[2]), int(dateStr[1]), int(dateStr[0]), int(timeStr[0]), int(timeStr[1]))

        dbTitle = unicode(e['Published']).replace(' ', '-')
        newsItemsByDate[date] = dbTitle

        itemObj = SiteNews_pb2.NewsItem()
        itemObj.title = unicode(e['Title'])
        itemObj.content = unicode(e['Content'])
        itemObj.published = unicode(e['Published'])

        sOutF = open(u'../data/data_NewsItem:' + dbTitle + u'.bin', 'w')
        sOutF.write(itemObj.SerializeToString())
        sOutF.close()

    newsIndex = SiteNews_pb2.NewsIndex()        
    for key in sorted(newsItemsByDate.iterkeys(), reverse=True):
        if debugPrints:
            print newsItemsByDate[key]
        newsIndex.newsKeys.append(newsItemsByDate[key])
    
    filename = u'../data/data_NewsIndex.bin'
    sOutF = open(filename, 'w')
    sOutF.write(newsIndex.SerializeToString())
    sOutF.close()
    
def createVisualWidgets():
    global debugPrints
    
    widgetListPath = u'../data/data_VisualWidgets'
    f = open(widgetListPath + u'.txt')
    widgets = dataProcessingLib.Widgets()
    widgets.parseFromFile(f)
    
    listObj = VisualWidget_pb2.ListOfWidgets()
    widgetId = 1;
    for i in widgets.widgets:
        '''
        if i.has_key('NotPublished'):
            continue
        '''
        if debugPrints: print 'Creating visualization vidget:', i['Title']
        
        widgetBasePath = u'../data/data_VisualWidget'
        widgetHeaderPath = widgetBasePath + u'Header:' + unicode(widgetId) + u'.bin' 
        widgetDataPath = widgetBasePath + u'Data:' + unicode(widgetId) + u'.bin'
        headerObj = VisualWidget_pb2.VisualWidgetHeader()
        dataObj = VisualWidget_pb2.VisualWidgetData()
        widgetStateStringToType = {'WORK_IN_PROGRESS':VisualWidget_pb2.WORK_IN_PROGRESS, "FINAL":VisualWidget_pb2.FINAL, "ON_GOING":VisualWidget_pb2.ON_GOING}
        
        headerObj.title = i['Title']
        headerObj.author = i['Author']
        headerObj.authorId = i['AuthorId']
        headerObj.published = i['Published']
        headerObj.version = i['Version']
        
        headerObj.state = widgetStateStringToType[i['State']]
        
        fData = codecs.open('../data/' + i['CodeFile'])
        dataObj.code = fData.read()
        fData.close()
        dataObj.description = i['Description']
        for s in i['Sources']:
            reference = dataObj.references.add()
            reference.id = s['ID']
            if s['Type'] == u'URL':
                if debugPrints: print 'Adding URL reference'
                reference.type = VisualWidget_pb2.URL
                reference.url = s['URL']
                reference.viewed = s['Viewed']
            elif s['Type'] == u'Article':
                if debugPrints: print 'Adding article reference'
                reference.type = VisualWidget_pb2.ARTICLE
                reference.sourceDescription = s['Source']
                if s.has_key('OptionalLink'):
                    reference.optionalLinkToSource = s['OptionalLink']
        
        fCode = open(widgetDataPath, 'w')
        fCode.write(dataObj.SerializeToString())
        fCode.close()

        fHeader = open(widgetHeaderPath, 'w')
        fHeader.write(headerObj.SerializeToString())
        fHeader.close()
        
        listObj.widgetIds.append(widgetId)
        if debugPrints:
            print 'Widget: ' + headerObj.title + ' stored with id ' + unicode(widgetId)
        widgetId = widgetId + 1
    
    fList = open(widgetListPath + u'.bin', 'w')
    fList.write(listObj.SerializeToString())
    fList.close()
    
    if debugPrints:
        print unicode(len(listObj.widgetIds)) + ' widgets saved to list obj'

def main():
    global debugPrints
    
    parser = argparse.ArgumentParser(description='Convert txt to bin.')
    parser.add_argument('--no_reps', help="Do not convert representatives", action="store_const", const=True, default=False)
    parser.add_argument('--verbose', help="More prints", action="store_const", const=True, default=False)
    params = parser.parse_args(sys.argv[1:])
    
    debugPrints = params.verbose
    
    if not params.no_reps:
        f = codecs.open('../data/data_representatives.txt', 'r', 'utf-8')
        createRepresentativeProtoBufObjects(f)
        f.close()

    createPoliticalPartyNameInfo('../data/data_PoliticalPartyNames.bin')
    listOfSeatingFiles = glob.glob('../data/data_Seating:*.txt')
    for s in listOfSeatingFiles:
        createRepresentativeSeatingInfo(s, '../data/data_representatives.txt')
            
    createSeasonsListInfo(u'../data/data_PoliticalSeasonsList.txt')

    listOfSeasonFiles = glob.glob('../data/data_PoliticalSeasonInfo:*.txt')
    for s in listOfSeasonFiles:
        createPoliticalSeasonInfo(s)
        
    convertNews()
    #createVisualWidgets()

if __name__ == "__main__":
    main()
    #createVisualWidgets()
