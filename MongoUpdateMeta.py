#######################################################################
# Mongo Ops
# Just a collection of tests/useful database operations
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
from pprint import pprint


def setupTagsIndex():
    logger.log("Creating tags index")
    collection.create_index([("tags", pymongo.ASCENDING)], collation=Collation(
        locale='en', strength=CollationStrength.PRIMARY))
    # collection.createIndex( { "tags": 1}, { { collation: collationData } )


def retriveUniqueTags():
    results = collection.distinct("tags")
    return results


def showTagsByPopularity():
    allTags = retriveUniqueTags()
    tagsWithCounts = {}

    tagIndex = 0
    logger.log("Counting tags...")
    for tag in allTags:
        tagCountQuery = {"tags": {"$elemMatch": {"$eq": tag}}}
        count = collection.count_documents(tagCountQuery)
        tagsWithCounts[tag] = count
        logger.log(str(tagIndex+1) + "/" + str(len(allTags)))
        tagIndex += 1

    listofTuples = sorted(tagsWithCounts.items(),
                          reverse=True, key=lambda x: x[1])
    tagCounts = []
    tagNames = []
    # countAbove = 0
    for item in listofTuples:
        
        tagNames.append(item[0])

        tagCounts.append({
            "tag" : item[0],
            "count" : item[1]
        })

    updateOp = {
        "tags" : tagNames,
        "counts" : tagCounts,  # just overwrite everything in data
    }

    logger.log("Updating database...")
    collectionMeta.update_one({'_id': "tags"}, {'$set': updateOp}, upsert=True)
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

    showTagsByPopularity()

    sys.exit(1)
