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
from Settings import mongoSettings
from Settings import miraSettings
from Settings import rigelSettings
from datetime import datetime
import Helpers
import json
import functools
from pprint import pprint

def sortFunc(tagPairA, tagPairB):
    if tagPairA[1] == tagPairB[1]:  
        return -1 if tagPairA[0] < tagPairB[0] else 1
    return 1 if tagPairA[1] < tagPairB[1] else -1

def updatTagsRecord():
    logger.log("Querying...")
    results = collection.find( {}, projection={rigelSettings.GAMEKEY_tags(): True} )

    tagPairs = {}
    for result in results:
        for tag in result[rigelSettings.GAMEKEY_tags()]:
            if tag in tagPairs:
                tagPairs[tag] = tagPairs[tag] + 1
            else:
                tagPairs[tag] = 0

    tagPairsArray = []

    for key in tagPairs:
        tagPairsArray.append( (str(key), int(tagPairs[key])) )
    
    tagPairsArray.sort(key=functools.cmp_to_key(sortFunc))

    logger.log("Found " + str(len(tagPairsArray)) + " unique tags")

    entries = []
    for item in tagPairsArray:
        entries.append({
            "name" : item[0],
            "count" : item[1]
        })

    logger.log("Updating database...")
    collectionMeta.update_one({'_id': "tags"}, {'$set': {"tags" : entries} }, upsert=True)
    logger.log("Done")

if __name__ == '__main__':
    logger = Helpers.Logger("MongoUpdateMeta", Helpers.mongoLogColor)
    logger.log("Connecting to database")

    client = None
    database = None
    gamesCollection = None
    collectionMeta = None

    try:
        client = MongoClient(mongoSettings.CONNECTION_STRING())
        database = client[mongoSettings.DATABASE_NAME()]
        collection = database[mongoSettings.COLLECTION_NAME()]
        collectionMeta = database[mongoSettings.COLLECTION_META_NAME()]
        logger.log("Connection Ok")
    except pymongo.errors.PyMongoError as e:
        logger.log("Connection Failure: " + str(e))
        sys.exit(1)

    updatTagsRecord()

    sys.exit(1)
