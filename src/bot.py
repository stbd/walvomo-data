# -*- encoding: utf-8 -*-

import httplib
import logging
import argparse
import sys
import time
import datetime
import VoteInfo_pb2
import Dictionary_pb2
import RepresentativeInfo_pb2
import codecs
import readVoteRecord
import dataProcessingLib

LOGGER_NAME = 'bot_log'
LOGGER_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
DEFAULT_URL = 'www.eduskunta.fi'
mapLogStringToLog = {'debug':logging.DEBUG, 'info':logging.INFO, 'warn':logging.WARN, 'error':logging.ERROR}
defaulInputCharset = 'ISO-8859-1'
pathToRepresentativeListFile = 'data_representatives.txt'

def convertNameToRepresentative(name, listOfRepresentatives):
	s = name.split(' ')
	numberOfPartsInName = len(s)
	firstName = ' '.join(name.split(' ')[0:numberOfPartsInName-1])
	alternativeFirstName = '-'.join(name.split(' ')[0:numberOfPartsInName-1])
	lastName = name.split(' ')[numberOfPartsInName-1]
	
	rep = None
	for r in listOfRepresentatives:
		#print r.lName, '==', lastName, 'and (', r.fName, '==', firstName, 'or', r.fName, '==', alternativeFirstName, ')'                               
		if r.lName == lastName and (r.fName == firstName or r.fName ==  alternativeFirstName):
			rep = r
			break
	if rep == None:
		print 'Did not find representative with name: ' + lastName + ' ' + firstName
		raise Exception('Did not find representative with name')
	return rep

def findSegment(data, startingIndex, startTag, endTag):
	start = data[startingIndex:].find(startTag)
	end = data[startingIndex+start+1:].find(endTag) + len(endTag) + 1
	return startingIndex + start, startingIndex + start + end

class VoteListPageParser():
	def __init__(self, logger, data, limit=None, prefix=None):
		self.logger = logger
		self.listOfData = []
		self.limit = limit
		self.limitEncountered = False
		self.prefix = prefix
		
		self.parsePage(data)
		
	def parsePage(self, data):
	
		index = 0
		data = data.replace('&#160;', ' ')
		
		while 1:
			s, e = findSegment(data, index, '<div class="list-items">', '</div>')
			if s == -1 or e == -1 or s > len(data) or e > len(data):
				break
			self.logger.debug('Parsing list element from lines: ' + str(s) + '-' + str(e))
			self.parseVoteListElement(data[s:e])
			if self.limitEncountered:
				break
			index = e + 1
		
	def parseVoteListElement(self, data):
		
		s, e = findSegment(data, 0, '<b>', '</b>')
		id = self.parseValue(data[s:e])
		
		ePrev = e
		s, e = findSegment(data, ePrev, '<a', '</a>')
		handlingInfoLink = self.parseAttribute(data[s:e], 'href')
		
		ePrev = e
		s, e = findSegment(data, ePrev, '<a', '</a>')
		officialRecordLink = self.parseAttribute(data[s:e], 'href')
		
		ePrev = e
		s, e = findSegment(data, ePrev, '<b>', '</b>')
		dateAndVoteNum = self.parseValue(data[s:e]).split(' ')
		dateOfVote = dateAndVoteNum[0].strip()
		voteNum = dateAndVoteNum[-1].strip()
		
		ePrev = e
		s, e = findSegment(data, ePrev, '<a', '</a>')
		resultsLink = self.parseAttribute(data[s:e], 'href')
		
		ePrev = e
		s, e = findSegment(data, ePrev, '<a', '</a>')
		resulstDistributionLink = self.parseAttribute(data[s:e], 'href')

		br = '<br />'
		for i in range(2):
			e = data[e:].find(br) + len(br) + e
		
		description = self.parseValue(data[e:])
		description =  dataProcessingLib.fixHtmlSpecialChars(description)
		
		if self.prefix != None:
			voteLimitString = str(dateOfVote) + ':' + str(voteNum)
			self.logger.debug('Vote prefix limit comparison: ' + self.prefix + ' == ' + voteLimitString)
			if self.prefix == voteLimitString:
				self.logger.info('Found prefix vote, this vote will be last one to be skipped')
				self.prefix = None
			else:
				self.logger.info('Skipping vote ' + voteLimitString + ' because of prefix limit' + self.prefix)
				return 
	
		if self.limit != None:
			voteLimitString = str(dateOfVote) + ':' + str(voteNum)
			self.logger.debug('Vote limit comparison: ' + self.limit + ' == ' + voteLimitString)
			if voteLimitString == self.limit:
				self.logger.warn('Encountered vote equal to vote limit, stopping parsing')
				self.limitEncountered = True
				return
			
		if len(id) == 0 or len(handlingInfoLink) == 0 or len(officialRecordLink) == 0 or len(dateOfVote) == 0 or len(voteNum) == 0 or len(resultsLink) == 0 or len(resulstDistributionLink) == 0 or len(description) == 0:
			self.logger.warn('Encountered end of list, stopping parsing')
			self.limitEncountered = True
			return
	
		self.listOfData.append((id, handlingInfoLink, officialRecordLink, dateOfVote, voteNum, resultsLink, resulstDistributionLink, description))
		self.logger.info('Parsed vote element: ' + str(id) + ' ' + str(voteNum) + ' ' + str(handlingInfoLink) + ' ' + str(officialRecordLink) + ' ' + str(dateOfVote) + ' ' + str(resultsLink) + ' ' + str(resulstDistributionLink) + ' curently ' + str(len(self.listOfData)) + ' elememts in list')

	def parseAttribute(self, data, attr):
		s = data.find(attr) + len(attr)
		valStart = data[s:].find('\"') + 1 + s
		e = data[valStart:].find('\"') + valStart
		return data[valStart:e]
		
	def parseValue(self, data):
		s = data.find('>') + 1
		e = data[s:].find('<')
		#print data + ':', data[s:s+e].strip()
		return data[s:s+e].strip()
		
class VoteStatisticParser():
	def __init__(self, logger, data):
		self.logger = logger
		self.listOfVotes = []
		self.nameOfChair = None

		self.parseChair(data)
		votesDataStart, votesDataEnd = findSegment(data, 0, '<table cellspacing="0" cellpadding="0"  border="0" class="statistics">', '</table>')
		if votesDataStart == -1 or votesDataEnd == -1:
			self.logger.error('Error finding vote area from page')
			return 
		
		self.parseResultsData(data[votesDataStart:votesDataEnd])

	def parseChair(self, data):
		tag = 'toimi puhemies '
		start = data.find(tag)
		if start == -1:
			tag = 'varapuhemies '
			start = data.find(tag)
			if start == -1:
				raise Exception('Unable find chair from record page')
		end = data[start:].find('/')
		if end == -1:
                        raise Exception('Unable find chair from record page')
		name = data[start+len(tag): start+end-1]
		logger.debug('Parsed chair for vote: "' + name + '"')
		self.nameOfChair = name
		
	def parseResultsData(self, data):
		
		index = 0
		while 1:
			trs, tre = findSegment(data, index, '<tr>', '</tr>')
			if trs == -1 or tre == -1 or index > len(data):
				break
			self.logger.debug('Parsing vote table line: ' + data[trs:tre])
			if not self.parseVoteTableRow(data[trs:tre]):
				break
			index = tre

	def parseName(self, name):
		s = name.split()
		if len(s) == 0:
			return ''
		if s[-1] == u'puhemiehenä':
			s = s[0:len(s)-2]
		else:
			s = s[0:len(s)-1]
		name = []
		name.append(' '.join(s[1:len(s)]))
		name.append(s[0])
		return ' '.join(name)
			
	def parseVoteTableRow(self, data):
		name, vote, i = self.parseVote(data)
		name = self.parseName(name)
		if len(name) == 0 or len(vote) == 0:
			return False
			
		self.listOfVotes.append((name, vote))
		self.logger.debug('Parsed vote: ' + name + ' ' + vote)			
		
		name, vote, i = self.parseVote(data[i:])
		name = self.parseName(name)
		if len(name) == 0 or len(vote) == 0:
			return False

		self.listOfVotes.append((name, vote))
		self.logger.debug('Parsed vote: ' + name + ' ' + vote)
		return True
		
	def parseVote(self, data):
		tds, tde = findSegment(data, 0, '<td>', '</td>')
		name = self.parseElementData(data[tds:tde])
		tds2, tde2 = findSegment(data, tde, '<td>', '</td>')
		vote = self.parseElementData(data[tds2:tde2])
		return name, vote, tde2
		
	def parseElementData(self, data):
		s = data.find('>') + 1
		e = data[s:].find('<')
		return data[s:s+e].strip()
	
def openVoteList(currentYear, voteMonth, pathToData, logger):
	
	createNew = True
	#Check if we can update old monthList
	voteListMonth = VoteInfo_pb2.ListOfVotesForMonth()
	filename = unicode(pathToData) + u'data_VoteList:' + unicode(currentYear) + u'.' + unicode(voteMonth) + u'.bin'
	logger.info('Testing if vote list exists in path: ' + filename)
	try:
		f = open(filename, 'r')
		voteListMonth.ParseFromString(f.read())
		f.close()
		logger.info(u'Updating old Votelist ' + filename)
		createNew = False
	except Exception, e:
		logger.info(u'Tried to update old Votelist ' + filename + ' but it did not exit')
		voteListMonth = None
					
	if createNew:
		logger.info('Creating new MonthList object with month: ' + str(voteMonth) + ', year: ' + str(currentYear))
		if voteListMonth != None:
			filename = unicode(pathToData) + u'data_VoteList:' + unicode(currentYear) + u'.' + unicode(voteListMonth.month) + u'.bin'
			logger.info(u'Storing Votelist to ' + filename)
			f = open(filename, 'w')
			f.write(voteListMonth.SerializeToString())
			f.close()
		voteListMonth = VoteInfo_pb2.ListOfVotesForMonth()
		voteListMonth.month = voteMonth
		voteListMonth.year = currentYear
	return voteListMonth
	
def storeVotesListMonth(voteListMonth, currentYear, pathToData):
	filename = unicode(pathToData) + u'data_VoteList:' + unicode(currentYear) + u'.' + unicode(voteListMonth.month) + u'.bin'
	logger.info(u'Storing Votelist to ' + filename)
	f = open(filename, 'w')
	f.write(voteListMonth.SerializeToString())
	f.close()
	
def partyCompare(x, y):
	return [v for v in RepresentativeInfo_pb2._POLITICALPARTYINFO_POLITICALPARTIES.values if v.name == x][0].number - [v for v in RepresentativeInfo_pb2._POLITICALPARTYINFO_POLITICALPARTIES.values if v.name == y][0].number 
	
def parseVoteListPage(reqPath, logger, pathToData, repList, currentYear, latestLimiter, prefix):		
	
	error = False
	httpParameters = {'Accept-Charset' : 'ISO-8859-1,utf-8', 'Accept' : 'text/html,application/xhtml+xml,application/xml'}	
	con = httplib.HTTPConnection(DEFAULT_URL)
	
	logger.info('Obtaining votes from: ' + DEFAULT_URL + reqPath)
	con.request('GET', reqPath, "", httpParameters)
	rsp = con.getresponse()

	if rsp.status != 200:
		logger.error('Opening of votes list page failed, reason: ' + str(rsp.reason) + ' (' + str(rsp.status) + ')')
		return False

	logger.debug(rsp.getheaders())
	logger.info('Parsing list page')
	listData = rsp.read()
	listData = unicode(listData, defaulInputCharset)
	
	listParser = VoteListPageParser(logger, listData, latestLimiter, prefix)
	recordPage = None
	voteListMonth = None
	
	if len(listParser.listOfData) == 0:
		logger.error('Could not parse vote list page')
		return False
	
	for voteInfo in listParser.listOfData:
		
		try:
			voteInfoKey = voteInfo[3] + u':' + voteInfo[4]
			voteInfoFileName = unicode(pathToData) + u'data_VoteInfo:' + voteInfoKey + '.bin'
			voteStatFileName = unicode(pathToData) + u'data_VoteStat:' + voteInfoKey + '.bin'
			
			if recordPage == None or recordPage.date != voteInfo[3]:
				logger.info('Refreshing record information')
				if recordPage != None:
					logger.info('Saving old record')
					readVoteRecord.saveVoteRecordObject(recordPage, recordPage.date, pathToData, logger)
				recordPage = readVoteRecord.readVoteRecordInformation(DEFAULT_URL, voteInfo[2], voteInfo[3], httpParameters, logger)
			else:
				logger.info('Record page already in memory')
	
			voteMonth = int(voteInfo[3].split('.')[1])
			if voteListMonth == None or voteListMonth.month != voteMonth:
				if voteListMonth != None:
					storeVotesListMonth(voteListMonth, currentYear, pathToData)
				voteListMonth = openVoteList(currentYear, voteMonth, pathToData, logger)

			if dataProcessingLib.testIfFileExists(voteInfoFileName):
				logger.info('VoteInfo file: ' + voteInfoFileName + ' already exists, skipping vote')
				continue
	
			logger.info('Reading vote info from: ' + voteInfo[5])
			con.request('GET', voteInfo[5], "", httpParameters)
			rsp = con.getresponse()
			if rsp.status != 200:
				logger.error('Error obtaining result for vote from address: ' )#FIXME
				logger.error('Reason: ' + str(rsp.reason) + ' (' + str(rsp.status) + ')')
				continue
			
			data = rsp.read()
			data = unicode(data, defaulInputCharset)
			data =  dataProcessingLib.fixHtmlSpecialChars(data)
			resultsParser = VoteStatisticParser(logger, data)
			
			totalVariation = {}
			variationByParty = {}
			
			voteStatistics = Dictionary_pb2.Dictionary()
			vote = VoteInfo_pb2.VoteInfo()
			for v in resultsParser.listOfVotes:
				representatative = convertNameToRepresentative(v[0], repList)
				representativeVoteInfo = vote.voteInfo.add()
				mapFromStringToVoteEnum = {'Jaa' : VoteInfo_pb2.YES, 'Ei' : VoteInfo_pb2.NO, 'Poissa' : VoteInfo_pb2.AWAY, u'Tyhjää' : VoteInfo_pb2.EMPTY}
	
				representativeVoteInfo.id = representatative.id
				representativeVoteInfo.voteDecision = mapFromStringToVoteEnum[v[1]]

				#Calculate some statistics
				if totalVariation.has_key(representativeVoteInfo.voteDecision):
					totalVariation[representativeVoteInfo.voteDecision] = totalVariation[representativeVoteInfo.voteDecision] + 1
				else:
					totalVariation[representativeVoteInfo.voteDecision] = 1
				
				partyId = dataProcessingLib.mapStrPartyToEnumParty[representatative.party]
				partyName = [x for x in RepresentativeInfo_pb2._POLITICALPARTYINFO_POLITICALPARTIES.values if x.number == partyId][0].name
				if variationByParty.has_key(partyName):
					variationByParty[partyName][representativeVoteInfo.voteDecision] = variationByParty[partyName][representativeVoteInfo.voteDecision] + 1
				else:
					variationByParty[partyName] = {VoteInfo_pb2.YES : 0, VoteInfo_pb2.NO : 0, VoteInfo_pb2.AWAY : 0, VoteInfo_pb2.EMPTY : 0}
					variationByParty[partyName][representativeVoteInfo.voteDecision] = 1

			#Note: order of choises here defines the order they are shown!
			possibleChoises = [VoteInfo_pb2.YES, VoteInfo_pb2.NO, VoteInfo_pb2.EMPTY, VoteInfo_pb2.AWAY]
			for choise in possibleChoises:
				stat = vote.voteStatistics.pairs.add()
				stat.key = [x for x in VoteInfo_pb2._VOTECHOISE.values if x.number == choise][0].name
				if totalVariation.has_key(choise):
					stat.value = unicode(totalVariation[choise])
				else:
					stat.value = '0'

			partyKeys = variationByParty.keys()
			partyKeys = sorted(partyKeys, cmp=partyCompare)
			for party in partyKeys:
				#print 'Saving party', party
				for choise in possibleChoises:
					stat = voteStatistics.pairs.add()
					statKey = unicode(party) + ':' + unicode([x for x in VoteInfo_pb2._VOTECHOISE.values if x.number == choise][0].name)
					stat.key = statKey
					if variationByParty[party].has_key(choise):
						stat.value = unicode(variationByParty[party][choise])
						logger.debug(statKey + ': ' + str(stat.value))
						#print statKey, stat.value
					else:
						stat.value = '0'
					
			vote.topic = voteInfo[0]
			vote.idOfChair = convertNameToRepresentative(resultsParser.nameOfChair, repList).id
			vote.shortDescription = voteInfo[7]
			vote.linkToRecord = 'http://' + DEFAULT_URL + voteInfo[2]
			vote.linkToVote = 'http://' + DEFAULT_URL + voteInfo[6]
			vote.dateOfVote = voteInfo[3]
			vote.voteNumber = int(voteInfo[4])
	
			found = False
			for v in voteListMonth.voteId:
				if v == voteInfoKey:
					found = True
					logger.warn('For some reason voteInfoKey already exists in voteListMonth - something might be out of sync here, investigate')
					break
			if not found:
				voteListMonth.voteId.append(voteInfoKey)
	
			logger.info('Storing voteInfo with key ' + voteInfoFileName + ', Size of serialized object: ' + str(vote.ByteSize()))
			binFile = open(voteInfoFileName, 'wb')
			binFile.write(vote.SerializeToString())
			binFile.close()
			
			logger.info('Storing voteStatistics with key ' + voteStatFileName + ', Size of serialized object: ' + str(voteStatistics.ByteSize()))
			binFile = open(voteStatFileName, 'wb')
			binFile.write(voteStatistics.SerializeToString())
			binFile.close()
			
	
			logger.info('Sleepping: ZzZzZzzz')
			time.sleep(3)#So that we're not tought as DOS attack
			logger.info('RingRing!')
		
		except Exception, e:
			import traceback
			print traceback.format_exc()
			logger.error('Error catched during vote handling: ' + str(e))
			error = True
			break

	if voteListMonth != None:
		storeVotesListMonth(voteListMonth, currentYear, pathToData)
	if recordPage != None:
		readVoteRecord.saveVoteRecordObject(recordPage, recordPage.date, pathToData, logger)
		
	return listParser.limitEncountered or error
		
def main(logger, latestLimiter, pathToData, prefix = None):

	sys.path.append(pathToData + 'src/')
	import dataProcessingLib

	repList = []
	repF = codecs.open(pathToData + pathToRepresentativeListFile, 'r', 'utf-8')
	reps = dataProcessingLib.Representatives()
	reps.parseFromFile(repF)
	repList = reps.representatives
	if len(reps.representatives) == 0:
		logger.error('Could not parse representatives')
		return

	currentYear = 2012
	logger.info('Connecting to ' + DEFAULT_URL)
	'''
	for year in range(currentYear, 1996, -1):
		reqPath = '/triphome/bin/thw.cgi/trip/?${BASE}=aanestysu&${CCL}=define+merge&${FREETEXT}=aanestysvpvuosi='  + str(year) +'&${savehtml}=/thwfakta/aanestys/aax/aax.htm&${TRIPSHOW}=html=aax/aax4000&${MAXPAGE}=501&${SORT}=ISTUNTOPVM+DESC,ISTUNTONRO+DESC,AANESTYSNRO+desc&${COMBOT}=0,2,undefined#alkukohta'
		if parseVoteListPage(reqPath, logger, pathToData, repList, year, latestLimiter, prefix):
			break
	'''
	year = currentYear
	reqPath = '/triphome/bin/thw.cgi/trip/?${BASE}=aanestysu&${CCL}=define+merge&${FREETEXT}=aanestysvpvuosi='  + str(year) +'&${savehtml}=/thwfakta/aanestys/aax/aax.htm&${TRIPSHOW}=html=aax/aax4000&${MAXPAGE}=501&${SORT}=ISTUNTOPVM+DESC,ISTUNTONRO+DESC,AANESTYSNRO+desc&${COMBOT}=0,2,undefined#alkukohta'
	parseVoteListPage(reqPath, logger, pathToData, repList, year, latestLimiter, prefix)
	
def readSpecificYear(logger, latestLimiter, pathToData, year, prefix = None):

	sys.path.append(pathToData + 'src/')
	import dataProcessingLib

	repList = []
	repF = codecs.open(pathToData + pathToRepresentativeListFile, 'r', 'utf-8')
	reps = dataProcessingLib.Representatives()
	reps.parseFromFile(repF)
	repList = reps.representatives
	if len(reps.representatives) == 0:
		logger.error('Could not parse representatives')
		return

	currentYear = year
	logger.info('Reading votes from year: ' + str(currentYear))
	reqPath = '/triphome/bin/thw.cgi/trip/?${BASE}=aanestysu&${CCL}=define+merge&${FREETEXT}=aanestysvpvuosi='  + str(currentYear) +'&${savehtml}=/thwfakta/aanestys/aax/aax.htm&${TRIPSHOW}=html=aax/aax4000&${MAXPAGE}=501&${SORT}=ISTUNTOPVM+DESC,ISTUNTONRO+DESC,AANESTYSNRO+desc&${COMBOT}=0,2,undefined#alkukohta'
	parseVoteListPage(reqPath, logger, pathToData, repList, currentYear, latestLimiter, prefix)	
	
def readSpecificVoteListPage(url, currentYear, logger, latestLimiter, pathToData, prefix = None):

	sys.path.append(pathToData + 'src/')
	import dataProcessingLib

	repList = []
	repF = codecs.open(pathToData + pathToRepresentativeListFile, 'r', 'utf-8')
	reps = dataProcessingLib.Representatives()
	reps.parseFromFile(repF)
	repList = reps.representatives
	if len(reps.representatives) == 0:
		logger.error('Could not parse representatives')
		return
		
	logger.info('Obtaining votes from: specific address from year: ' + str(currentYear) + ' url: ' + DEFAULT_URL + url)
	parseVoteListPage(url, logger, pathToData, repList, int(currentYear), latestLimiter, prefix)
		

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Retrieve vote results.')
	parser.add_argument('--log', help="Set log level, one of: debug, info, warn, error", default='info')
	parser.add_argument('--logp', help="Print logs instead of storing to file", action="store_const", const=True)
	parser.add_argument('--latest', help="Latest vote read, read only votes newer than this. Format: [date]:[voteNum], eg: 21.06.2012:92", default=None)
	parser.add_argument('--prefix', help="Earliest vote to be read,i.e. read only votes that appear after this vote (and the prefix). Format: [date]:[voteNum], eg: 21.06.2012:92", default=None)
	parser.add_argument('--data', help="Path to oc_data project, default: ../data/", default='../data/')
	
	parser.add_argument('--url', help="URL to votelistpage to parse, note: requires also year parameter. Also note: replace '{' with '\{'")
	parser.add_argument('--year', help="Year of votes", type=int)
	
	params = parser.parse_args(sys.argv[1:])

	if not mapLogStringToLog.has_key(params.log):
		print 'Invalid log level'
		sys.exit(1)
	
	if params.logp:
		logging.basicConfig(level=mapLogStringToLog[params.log], format=LOGGER_FORMAT)
	else:
		logging.basicConfig(filename=LOGGER_NAME, level=mapLogStringToLog[params.log], format=LOGGER_FORMAT)
	
	logger = logging.getLogger(LOGGER_NAME)
	if params.latest != None:
		logger.info('Using \"' + params.latest + '\" as limit for reading votes')
	'''
	else:
		print '--latest not set. Set it!'
		sys.exit(1)
	'''
	
	if params.prefix:
		logger.info('Using \"' + params.prefix + '\" as prefix limit for reading votes')
		#Verify that limits make sense
		nPre = int(params.prefix.split(':')[1])
		datePre = [int(e) for e in params.prefix.split(':')[0].split('.')]
		datePre = datetime.date(datePre[2], datePre[1], datePre[0])
		
		datePost = [int(e) for e in params.latest.split(':')[0].split('.')]
		datePost = datetime.date(datePost[2], datePost[1], datePost[0])
		nPost = int(params.latest.split(':')[1])
		
		#Note that vote number is a decereasing number 
		#print datePre < datePost,  datePre == datePost,  nPre <= nPost
		if datePre < datePost or (datePre == datePost and nPre <= nPost):
			print 'Limit ' + params.latest + ' is earlier than prefix ' + params.prefix
			print 'Fixem!'
			sys.exit(1)
		
	if params.url and params.year:
		readSpecificVoteListPage(params.url.replace('\\',''), params.year, logger, params.latest, params.data, params.prefix)
	elif (params.url and not params.year):
		print 'Please specify both year and URL'
	elif (params.year and not params.url):
		readSpecificYear(logger, params.latest, params.data, params.year, params.prefix)
	else:
		main(logger, params.latest, params.data, params.prefix)
