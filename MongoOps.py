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
import bson
from pprint import pprint


def setupTagsIndex():
    logger.log("Creating tags index")
    collection.create_index([("tags", pymongo.ASCENDING)], collation=Collation(
        locale='en', strength=CollationStrength.PRIMARY))
    # collection.createIndex( { "tags": 1}, { { collation: collationData } )


def retriveUniqueTags():
    results = collection.distinct("tags")
    return results

def deleteTag(tagName):
    collection.update_many(
            {}, 
            {'$pull': {'tags': tagName}}
        )


def showTagsByPopularity():
    allTags = retriveUniqueTags()
        # for tag in allTags:
    #     print(tag)

    tagsWithCounts = {}

    tagIndex = 0
    print("Counting tags...")
    for tag in allTags:
        tagCountQuery = {"tags": {"$elemMatch": {"$eq": tag}}}
        count = collection.count_documents(tagCountQuery)
        tagsWithCounts[tag] = count
        print("\r" + str(tagIndex+1) + "/" + str(len(allTags)), end='')
        tagIndex += 1

    print("\n\nResults:")

    listofTuples = sorted(tagsWithCounts.items(),
                          reverse=True, key=lambda x: x[1])
    # countAbove = 0
    for item in listofTuples:
        # if item[1] > 10:
        #     countAbove += 1
        print(str(item))

    print("")


def showGamesByPopularity():
    results = collection.find({})
    reivewPairs = {}
    for result in results:
        name = result[rigelSettings.KEY_trackName()]
        rating = result[rigelSettings.KEY_userRating(
        )][rigelSettings.KEY_ratingCount()]
        reivewPairs[name] = rating

    listofTuples = sorted(reivewPairs.items(),
                          reverse=True, key=lambda x: x[1])

    num = 1
    for item in listofTuples:
        print(str(num) + " : " + str(item))
        num += 1


def showGamesByReleaseDate():
    results = collection.find({})
    reivewPairs = {}
    for result in results:
        name = result[rigelSettings.KEY_trackName()]
        releaseDate = result[rigelSettings.KEY_releaseDate()]
        reivewPairs[name] = releaseDate

    listofTuples = sorted(reivewPairs.items(),
                          reverse=True, key=lambda x: x[1])

    num = 1
    for item in listofTuples:
        print(str(num) + " : " + str(item))
        num += 1


def bigBlobTestWrite():
    with open('Test/BigBlob.json', encoding='utf-8') as json_file:
        bigBlog = json.load(json_file)
        collection.insert_one(bigBlog[0])

def deleteEntireCollecion():
    val = input("Delete entire collection? -> " + mongoSettings.COLLECTION_NAME() + " (type YES): ")
    if str(val).lower() == "yes":
        collection.delete_many({})
        print("Delete successful")
    else:
        print("Cancelled") 


def overwriteTest():

    bulkUpdates = []
    tags = ["balls", "indie", "hurrah"]

    dataTest = {
        "one" : "one",
    }

    groupUpdate = {
        '$set': dataTest,
        '$addToSet': {"tags" : { "$each" : tags }}
    }

    bulkUpdates.append(pymongo.UpdateOne(
            {'_id': 123}, groupUpdate, upsert=True)
        )

    # bulkUpdates.append(pymongo.UpdateOne(
    #     {'_id': 123}, 
    #     {'$addToSet': {"tags" : { "$each" : tags }}}, 
    #     upsert=True)
    # )
        
    try:
        results = collection.bulk_write(bulkUpdates)
        logger.log("Databased updated. Added: " + str(results.upserted_count) + ", modified: " + str(results.modified_count))
    except pymongo.errors.PyMongoError as e:
        logger.log("bulk_write error: " + str(e))

def overwriteTest2():
    bulkUpdatesArray = []
    dateNow = str(datetime.now())
    updateData = { "dateValidated" : dateNow }

    bulkUpdatesArray.append(pymongo.UpdateOne(
        {'_id': 284653044}, {'$set': updateData}, upsert=True)
    )

    collection.bulk_write(bulkUpdatesArray)

def showDeviceFamilies():
    results = collection.find({})
    
    count = 0
    
    for result in results:
        logger.log(str(result.get("lookupBlob").get("deviceFamilies")))
        count = count + 1
        if count == 1000:
            break


if __name__ == '__main__':
    logger = Helpers.Logger("MongoOps", Helpers.mongoLogColor)
    logger.log("Connecting to database")

    client = None
    database = None
    collection = None

    try:
        client = MongoClient(mongoSettings.CONNECTION_STRING())
        database = client[mongoSettings.DATABASE_NAME()]
        collection = database[mongoSettings.COLLECTION_NAME()]
        logger.log("Connection Ok")
    except pymongo.errors.PyMongoError as e:
        logger.log("Connection Failure: " + str(e))
        sys.exit(1)

    #overwriteTest()
    # setupTagsIndex()
    # showTagsByPopularity()
    # showGamesByPopularity()
    # showGamesByReleaseDate()
    # deleteTag("Games")
    # showDeviceFamilies()

    # bulkUpdates = []
    # bulkUpdates.append(pymongo.DeleteOne( {'_id': bson.int64.Int64('1520736876')} ))
    # results = collection.bulk_write(bulkUpdates)
    # logger.log("Databased updated. Deleted: " + str(results.deleted_count))


    results = collection.count_documents( {"dateValidated": {"$exists" : False}} )
    logger.log("Result: " + str(results))

    sys.exit(1)
