#######################################################################
# MongoUpdateMeta
# Updates the Games_meta collection
#######################################################################

import os
from os import path
import sys
import pymongo
from pymongo.collation import Collation, CollationStrength
from pymongo import MongoClient
from datetime import datetime
import Helpers
import json
import functools
from Mongo import Mongo
from Shared import settings
from pprint import pprint

def sortFunc(tagPairA, tagPairB):
    if tagPairA[1] == tagPairB[1]:  
        return -1 if tagPairA[0] < tagPairB[0] else 1
    return 1 if tagPairA[1] < tagPairB[1] else -1

def updateTagsRecord():
    mongo.logger.log("Querying...")
    results = mongo.collection_games.find( {}, projection={settings.rigel.db_keys.tags: True} )

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
    
    tagPairsArray.sort(key=functools.cmp_to_key(sortFunc))

    mongo.logger.log("Found " + str(len(tagPairsArray)) + " unique tags")

    entries = []
    for item in tagPairsArray:
        entries.append({
            "name" : item[0],
            "count" : item[1]
        })

    mongo.logger.log("Updating database...")
    mongo.collection_games_meta.update_one({'_id': "tags"}, {'$set': {"tags" : entries} }, upsert=True)
    mongo.logger.log("Done")

if __name__ == '__main__':
    mongo = Mongo("MongoUpdateMeta")
    updateTagsRecord()
