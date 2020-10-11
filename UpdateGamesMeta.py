#######################################################################
# UpdateGamesMeta
# Updates the Games_meta collection
#######################################################################

import sys
import functools
from Mongo import Mongo
from Shared import settings, hasTestArgs
import Helpers

class UpdateGamesMeta:
    def __init__(self, mongo):
        self.logger = Helpers.Logger(__class__.__name__, Helpers.mongoLogColor)
        self.mongo = mongo

    def start(self):
        self.updateTagsRecord()

    def sortFunc(self, tagPairA, tagPairB):
        if tagPairA[1] == tagPairB[1]:  
            return -1 if tagPairA[0] < tagPairB[0] else 1
        return 1 if tagPairA[1] < tagPairB[1] else -1

    def updateTagsRecord(self):
        self.logger.log("Querying...")
        results = self.mongo.collection_games.find( {}, projection={settings.rigel.db_keys.tags: True} )

        tagPairs = {}
        for result in results:
            for tag in result[settings.rigel.db_keys.tags]:
                if tag in tagPairs:
                    tagPairs[tag] = tagPairs[tag] + 1
                else:
                    tagPairs[tag] = 1

        tagPairsArray = []

        for key in tagPairs:
            tagPairsArray.append( (str(key), int(tagPairs[key])) )
        
        tagPairsArray.sort(key=functools.cmp_to_key(self.sortFunc))

        self.logger.log("Found " + str(len(tagPairsArray)) + " unique tags")

        entries = []
        for item in tagPairsArray:
            entries.append({
                "name" : item[0],
                "count" : item[1]
            })

        self.logger.log("Updating database...")
        self.mongo.collection_games_meta.update_one({'_id': "tags"}, {'$set': {"tags" : entries} }, upsert=True)
        self.logger.log("Done")

if __name__ == '__main__':
    mongo = Mongo()
    mongo.connect(hasTestArgs(sys.argv))
    UpdateGamesMeta(mongo).start()
