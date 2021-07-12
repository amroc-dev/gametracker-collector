#######################################################################
# UpdateGamesMeta
# Updates the Games_meta collection
#######################################################################

import sys
import functools
from Mongo import Mongo
from Shared import settings, hasTestArgs
import math
import Helpers
import collections
from Helpers import objectKeyFromDotString

class UpdateGamesMeta:
    def __init__(self, mongo):
        self.logger = Helpers.Logger(__class__.__name__, Helpers.mongoLogColor)
        self.mongo = mongo

    def start(self):
        self.updateTagsRecord()
        self.updatePopularityIntervals()
        self.updateReleaseYears()

    def sortFunc(self, tagPairA, tagPairB):
        if tagPairA[1] == tagPairB[1]:
            return -1 if tagPairA[0] < tagPairB[0] else 1
        return 1 if tagPairA[1] < tagPairB[1] else -1

    def updateTagsRecord(self):
        self.logger.log("Updating Tags record...")
        results = self.mongo.collection_games.find({}, projection={settings.gamesMeta.db_keys.tags: True})

        tagPairs = {}
        for result in results:
            for tag in result[settings.gamesMeta.db_keys.tags]:
                if tag in tagPairs:
                    tagPairs[tag] = tagPairs[tag] + 1
                else:
                    tagPairs[tag] = 1

        tagPairsArray = []

        for key in tagPairs:
            tagPairsArray.append((str(key), int(tagPairs[key])))

        tagPairsArray.sort(key=functools.cmp_to_key(self.sortFunc))

        self.logger.log("Found " + str(len(tagPairsArray)) + " unique tags")

        entries = []
        for item in tagPairsArray:
            entries.append({
                "name": item[0],
                "count": item[1]
            })

        self.logger.log("Updating database...")
        self.mongo.collection_games_meta.update_one({'_id': settings.gamesMeta.db_keys.tags}, {'$set': {settings.gamesMeta.db_keys.tags: entries}}, upsert=True)
        self.logger.log("Done")

    def updatePopularityIntervals(self):
        self.logger.log("Updating Popularity intervals...")
        POPULARITY_FIELD = 'lookupBlob.userRating.ratingCount'
        results = self.mongo.collection_games.find({}, projection={POPULARITY_FIELD: True})

        MIN_POPULARITY = 5
        countAll = 0
        countMinOrMore = 0
        allCounts = []
        tallies = {}

        for result in results:
            pop = result['lookupBlob']['userRating']['ratingCount']
            if pop >= MIN_POPULARITY:
                countMinOrMore += 1
            countAll += 1
            allCounts.append(pop)
            if not pop in tallies:
                tallies[pop] = 0
    
            tallies[pop] += 1

        tallies = collections.OrderedDict(sorted(tallies.items()))

        buckets = [(MIN_POPULARITY,0)]

        countLeft = countMinOrMore 
        for key in tallies:
            divisor = 100 - len(buckets)
            maxBucketCount = countLeft / divisor if divisor > 0 else countAll
            
            if key < MIN_POPULARITY:
                continue
            val = tallies[key]
            if buckets[-1][1] >= maxBucketCount:
                buckets.append( (key, 0) )

            countLeft -= val  

            buckets[-1] = (buckets[-1][0], buckets[-1][1] + val)

        bucketIndex = 1
        for bucket in buckets:
            self.logger.log(str(bucketIndex) + ":" + str(bucket))
            bucketIndex += 1

        intervals = []
        for bucket in buckets:
            intervals.append(bucket[0])

        self.logger.log("Processed " + str(len(intervals)) + " intervals")
        self.logger.log("Updating database...")
        self.mongo.collection_games_meta.update_one({'_id': settings.gamesMeta.db_keys.popularity_intervals}, {'$set': {settings.gamesMeta.db_keys.popularity_intervals: intervals}}, upsert=True)
        self.logger.log("Done")

    def updateReleaseYears(self):
        self.logger.log("Updating release years...")
        FIELD = 'lookupBlob.releaseDate'
        results = self.mongo.collection_games.find({}, projection={FIELD: True})

        SANITY_MIN = 2000
        SANITY_MAX = 2050
        minYear = 3000
        maxYear = 0
        for result in results:
            releaseDate = objectKeyFromDotString(result, FIELD)
            if len(releaseDate) > 4:
                year = int(releaseDate[0:4])
                if year > SANITY_MIN and year < SANITY_MAX:
                    if year < minYear:
                        minYear = year
                    elif year > maxYear:
                        maxYear = year



        if not (minYear > SANITY_MIN and minYear < SANITY_MAX and maxYear > minYear and maxYear < SANITY_MAX):
            self.logger.log("Years didn't parse sanity check. min:" + str(minYear) + ", max:" + str(maxYear))
            sys.exit(1)
        
        self.logger.log("Range: " + str(minYear) + " to " + str(maxYear));
        self.logger.log("Updating database...")
        entries = [minYear, maxYear]
        self.mongo.collection_games_meta.update_one({'_id': settings.gamesMeta.db_keys.releaseYears}, {'$set': {settings.gamesMeta.db_keys.releaseYears: entries}}, upsert=True)
        self.logger.log("Done")



if __name__ == '__main__':
    mongo = Mongo()
    mongo.connect(hasTestArgs(sys.argv))
    UpdateGamesMeta(mongo).start()
