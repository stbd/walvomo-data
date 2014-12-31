import dataProcessingLib
import feedparser
import sys
import argparse
import NewsElements_pb2
import logging
import time
from datetime import datetime
from xml.sax import saxutils

LOGGER_NAME = 'feed_log'
mapLogStringToLog = {'debug':logging.DEBUG, 'info':logging.INFO, 'warn':logging.WARN, 'error':logging.ERROR}
LOGGER_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
DEAFULT_LATEST_LIMIT = 1357020000 #1.1.2013
#DEAFULT_LATEST_LIMIT = time.time() - 60*60*24*30*2

'''
    Functions
'''
def safeUrl(url):
    return url.replace('&', '&amp;')

def newsItemSorter(x, y):
    return int(x.publishedTimestamp) - int(y.publishedTimestamp)
    

def readFeed(url, logger, modified=DEAFULT_LATEST_LIMIT):
    newsItems = []
    if modified:
        data = feedparser.parse(url, modified=time.gmtime(int(modified + time.timezone)))
    else:
        data = feedparser.parse(url)
    #print data
    
    
    if len(data['items']) == 0:
        return newsItems

    logger.info("Parsing URL: " + url + " title: " + data['channel']['title'])
    
    for e in data['items']:
        
        if not e.has_key('published_parsed'):
            logger.warn('Feed ' + url + ' did not have published field')
            break

        if modified != None:
            current = None
            current = int(time.mktime(e['published_parsed']))
            if modified >= current:
                logger.debug('Skipping feed because db has stuff with timestamp ' + str(modified) + ' while current is: ' + str(current))
                break
        
        #print e['title'], '|', e['link'], datetime.fromtimestamp(mktime(e['published_parsed'])).isoformat()
        item = NewsElements_pb2.UpdateItem()
        #print mktime(e['published_parsed'])
        #datetime.fromtimestamp(mktime(e['published_parsed'])).isoformat()
        #print e['link']
        
                    
        item.publishedTimestamp = str(int(time.mktime(e['published_parsed'])))
        if len(e['title']) == 0:
            item.title = u"[Ei aihetta]"
        else:
            item.title = saxutils.escape(e['title'])
        item.url = safeUrl(e['link'])
        #item.limitedContent = '' #Not implemented at the moment
        newsItems.append(item)
    
    logger.info('Parsed ' + str(len(data['items'])) + " elements of which " + str(len(newsItems)) + ' were saved to db')
    return newsItems

def createUpdateSource(data, collection):
    updateSource = collection.updateSources.add()
    updateSource.title = data['Title']
    updateSource.description = data['Description']
    updateSource.sourceAddress = data['URL']
    updateSource.dataPath = data['DataPath']
    updateSource.latestReadItem = '0'
    
    if data.has_key('NumberOfItemsRead'):
        updateSource.numberOfItems = data['NumberOfItemsRead']
    else:
        data['NumberOfItemsRead'] = 0
        updateSource.numberOfItems = 0
    
    if data.has_key('LatestItemRead'):
        updateSource.latestReadItem = data['LatestItemRead']
    else:
        updateSource.latestReadItem = ""
        data['LatestItemRead'] = ""

    return updateSource
    
'''
    Main//////////////////////////////////////////////////////////////////////////////////////
'''
pathToData = u'../data/data_'
collectionOfUpdateSource = u'../data/data_representatives_feeds.txt'
collectionBinaryName = u'data_RepresentativeFeeds.bin'
update = False

parser = argparse.ArgumentParser(description='Feed reader.')
parser.add_argument('--log', help="Set log level, one of: debug, info, warn, error", default='info')
parser.add_argument('--update', help="Update config files", action="store_const", const=True, default=False)
parser.add_argument('--source', help="Path to file used as source: default: ../data/data_representatives_feeds.txt")
params = parser.parse_args(sys.argv[1:])

if params.source:
    collectionOfUpdateSource = params.source

if not mapLogStringToLog.has_key(params.log):
    print 'Invalid log level'
    sys.exit(1)

logging.basicConfig(level=mapLogStringToLog[params.log], format=LOGGER_FORMAT)
logger = logging.getLogger(LOGGER_NAME)

if params.update:
    logger.debug("Updating config files")
    update = True

logger.debug('Using data source ' + collectionOfUpdateSource)

sources = dataProcessingLib.NewsCollectionSource()
sources.parseFromFile(open(collectionOfUpdateSource, 'r'))
collections = NewsElements_pb2.Collections()

sourceId = 1;

for c in sources.data['Collections']:

    collection = NewsElements_pb2.CollectionOfUpdateSources()
    collection.title = c['Title']
    collection.description = c['Description']
    collection.tags = c['Tag']
    
    for s in c['Feeds']:
        try:
            updateSource = None
            if s.has_key('NotActive'):
                logger.info('Feed: ' + s['URL'] + ' set inactive, ignoring')
                continue
            updateSource = createUpdateSource(s, collection)
            updateSource.tags = u's:' + unicode(sourceId) + u';'
            sourceId = sourceId + 1
            
            items = []
            if updateSource.latestReadItem == '':#TODO: protobuf has some has key method which should be used
                logger.debug('Not using latestReadItem info')
                items = readFeed(s['FeedURL'], logger)
            else:
                logger.debug('Using latestReadItem info: ' + updateSource.latestReadItem)
                items = readFeed(s['FeedURL'], logger, int(updateSource.latestReadItem))
                
            if len(items) == 0:
                logger.debug('No items found for feed: ' + s['URL'])
                continue
            
            items = sorted(items, cmp=newsItemSorter)
                
            for i in range(len(items)):
                index = updateSource.numberOfItems + i
                filename = pathToData + u'UpdateItem:' + updateSource.dataPath + ':' + unicode(index) + u'.bin'
                f = open(filename, 'w')
                f.write(items[i].SerializeToString())
                f.close()
                logger.debug('Saved item with timestamp ' + items[i].publishedTimestamp + ' to: ' + filename)
            s['NumberOfItemsRead'] = s['NumberOfItemsRead'] + len(items)
            updateSource.numberOfItems = updateSource.numberOfItems + len(items)
            updateSource.sourceAddress = safeUrl(updateSource.sourceAddress)
            s['LatestItemRead'] = items[0].publishedTimestamp
            updateSource.latestReadItem = items[0].publishedTimestamp

            logger.debug('Updating latestItemRead to ' + str(items[0].publishedTimestamp))
        except Exception, e:
            logger.error('Error while processing feed from: ' + s['URL'] + ' Error: ' + str(e))
            import traceback
            print traceback.format_exc()
        
    itemName = c['CollectionId']
    filename = pathToData + u'Collection:' + itemName + u'.bin'
    collections.collections.append(itemName)
    f = open(filename, 'w')
    f.write(collection.SerializeToString())
    f.close()
    logger.debug('Saved collection to: ' + filename)
    
filename = pathToData + u'Collections.bin'
f = open(filename, 'w')
f.write(collections.SerializeToString())
f.close()
logger.debug('Saved collections to: ' + filename)

if update:
    logger.debug("Updating source config")
    sources.writeToFile(open('../data/data_representatives_feeds.txt', 'w'))

    
