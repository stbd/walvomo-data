# -*- encoding: utf-8 -*-

import httplib
import logging
import argparse
import sys
import time
import datetime
import VoteInfo_pb2
import codecs
import glob
import dataProcessingLib

LOGGER_NAME = 'record_reader_log'

class ParseRecordPage():
    def __init__(self, logger, data, source, date):
        self.source = data
        self.logger = logger
        self.infos = []
        self.date = date
        
        startTag = '<tulos><te>'
        endTag = '<aanviit'

        i = 0
        num = 1
        
        '''
        if self.source.count(startTag) != self.source.count(endTag):
            logger.error('Number of tags not equal in sgm')
            sys.exit(1)
        '''
        #Be very afraid of the indexing
        while 1:
            start = self.source[i:].find(startTag)
            if start == -1:
                logger.info('Start not found')
                break
            end = self.source[i + start:].find(endTag)
            if end == -1:
                logger.info('End not found')
                break
            if (i + start + end) < (i + start):
                break

            #Cleanup the string
            description = dataProcessingLib.fixHtmlSpecialChars(self.source[(i + start + len(startTag)):(i + start + end)])
            description = ' '.join(description.splitlines()).splitlines()[0]     #Replace unicode line endings: http://stackoverflow.com/questions/2201633/replace-newlines-in-a-unicode-string
            description = ' '.join(description.split())                            #Replace double spaces
            description = description.replace('</te>', '').replace('<te>', '')
            self.infos.append(description)
            num = num + 1
            i = i + start + end + len(endTag)
            if i >= len(self.source):
                break
        
        self.logger.info('Parsed ' + str(len(self.infos)) + ' vote info elements')

def saveVoteRecordObject(recordPage, date, pathToData, logger):
        voteRecord = VoteInfo_pb2.VoteRecord()
        for e in recordPage.infos:
            voteRecord.voteDescription.append(e)

        recordFilename = unicode(pathToData) + 'data_VoteRecord:' + date + '.bin'
        logger.info('Storing record object with key ' + recordFilename + ', Size of serialized object: ' + str(voteRecord.ByteSize()))
        f = open(recordFilename, 'wb')
        f.write(voteRecord.SerializeToString())
        f.close()

def readVoteRecordInformation(siteAddress, path, date, httpParameters, logger):
    con = httplib.HTTPConnection(siteAddress)
    con.request('GET', path, "", httpParameters)
    rsp = con.getresponse()
    if rsp.status == 302:
        redirected = False
        for e in rsp.getheaders():
            if e[0] == 'location':
                con = httplib.HTTPConnection(siteAddress)
                con.request('GET', e[1], "", httpParameters)
                rsp = con.getresponse()
                redirected = True
        if not redirected:
            logger.error('Redirect address not found')
            sys.exit(1)

    if rsp.status != 200:
        logger.error('Reading of record page failed: ' + str(rsp.reason) + ' (' + str(rsp.status) + ')')
        logger.error(rsp.getheaders())
        sys.exit(1)
    recordData = rsp.read()

    endI = recordData.find('.sgm') + 4
    startI = recordData[0:endI].rfind('\"') + 1
    recordUrl = recordData[startI:endI]
    logger.info('Parsing record information from ' + recordUrl)

    con = httplib.HTTPConnection(siteAddress)
    con.request('GET', recordUrl, "", httpParameters)
    rsp = con.getresponse()
    if rsp.status != 200:
        logger.error('Reading of record page failed: ' + str(rsp.reason) + ' (' + str(rsp.status) + ')')
        logger.error(rsp.getheaders())
        sys.exit(1)
    recordSgm = rsp.read()
    recordPage = ParseRecordPage(logger, recordSgm, path, date)
    if len(recordPage.infos) == 0:
        logger.warn('Did not parse any record for record page')
    return recordPage

def main():
    logger = logging.getLogger(LOGGER_NAME)
    logging.basicConfig(level=logging.INFO)
    
    httpParameters = {'Accept-Charset' : 'ISO-8859-1,utf-8', 'Accept' : 'text/html,application/xhtml+xml,application/xml'} 
    path = '../data/data_VoteInfo:*'
    files = glob.glob(path)
    
    for f in files:
        logger.debug('Examining vote ' + f)
        vote = VoteInfo_pb2.VoteInfo()
        file = open(f, 'r')
        vote.ParseFromString(file.read())
        
        recordFilename = '../data/data_VoteRecord:' + vote.dateOfVote + '.bin'
        if dataProcessingLib.testIfFileExists(recordFilename):
            logger.info('Found record info for vote ' + f + ' (record filename: ' +  recordFilename + ') - skipping')
            continue
        rootUrl = vote.linkToRecord.replace("http://", '')
        rootEnd = rootUrl.find('.fi') + 3
        url = rootUrl[rootEnd:]
        rootUrl = rootUrl[0:rootEnd]
        vote.linkToRecord
        
        logger.info('Did not found record info for vote ' + f)
        logger.info('Downloading it from ' + rootUrl + url)
        voteRecordInfo = readVoteRecordInformation(rootUrl, url, vote.dateOfVote, httpParameters, logger)
        saveVoteRecordObject(voteRecordInfo, vote.dateOfVote, '../data/', logger)

if __name__ == "__main__":
    main()