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

class UpdateGamesMeta:
    def __init__(self, mongo):
        self.logger = Helpers.Logger(__class__.__name__, Helpers.mongoLogColor)
        self.mongo = mongo

    def start(self):
        self.updateTagsRecord()
        self.updatePopularityIntervals()

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

        allCounts = []
        min = 99999999
        max = 0
        for result in results:
            count = result['lookupBlob']['userRating']['ratingCount']
            if count < min:
                min = count
            if count > max:
                max = count
            allCounts.append(count)

        allCounts.sort(reverse=True)

        maxSize = 6
        intervals=[max]
        currentSize=0
        for count in allCounts:
            currentSize += 1
            if currentSize >= maxSize:
                if count != intervals[0]:
                    intervals.insert(0, count)
                    currentSize = 0
                    if count == 4:
                        break

        self.logger.log("Processed " + str(len(intervals)) + " intervals")
        self.logger.log("Updating database...")
        self.mongo.collection_games_meta.update_one({'_id': settings.gamesMeta.db_keys.popularity_intervals}, {'$set': {settings.gamesMeta.db_keys.popularity_intervals: intervals}}, upsert=True)
        self.logger.log("Done")

if __name__ == '__main__':
    mongo = Mongo()
    mongo.connect(hasTestArgs(sys.argv))
    UpdateGamesMeta(mongo).start()
