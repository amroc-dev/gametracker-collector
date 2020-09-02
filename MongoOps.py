import os
from os import path
import sys
import pymongo
from pymongo.collation import Collation, CollationStrength
from pymongo import MongoClient
from Settings import mongoSettings
from Settings import miraSettings
from Settings import rigelSettings
import Helpers
from pprint import pprint

def setupTagsIndex():
    logger.log("Creating tags index")
    collection.create_index([("tags", pymongo.ASCENDING)], collation = Collation(locale='en', strength = CollationStrength.PRIMARY))
    # collection.createIndex( { "tags": 1}, { { collation: collationData } )

def retriveUniqueTags():
    results = collection.distinct("tags")
    return results

def showTagsByPopularity():
    allTags = retriveUniqueTags()
        # for tag in allTags:
    #     print(tag)

    tagsWithCounts = {}

    tagIndex = 0
    print ("Counting tags...")
    for tag in allTags:
        tagCountQuery = {"tags" : {"$elemMatch": {"$eq" : tag}}}
        count = collection.count_documents(tagCountQuery)
        tagsWithCounts[tag] = count
        print("\r" + str(tagIndex+1) + "/" + str(len(allTags)), end='')
        tagIndex += 1

    print("\n\nResults:")

    listofTuples = sorted(tagsWithCounts.items() ,reverse=True, key=lambda x: x[1])
    # countAbove = 0
    for item in listofTuples:
        # if item[1] > 10:
        #     countAbove += 1
        print(str(item))

    print("")

    # fileName = Helpers.getWithExtension("steamTags", miraSettings.TERMS_EXTENSION())
    # fullPath = miraSettings.TERMS_DIR() + "/" + str(fileName)
    # termsList = []
    # if path.exists(fullPath):
    #     with open(fullPath, encoding='utf-8') as f:
    #         for line in f:
    #             if not line.startswith("#"):
    #                 term = line.replace("\n", "").lower()
    #                 if term not in termsList:
    #                     termsList.append(term)

    # for term in termsList:
    #     termFound = False
    #     for item in listofTuples:
    #         if str(item[0]) == term:
    #             termFound = True
    #             break
        
    #     if not termFound:
    #         print("Not found: " + term)

def showGamesByPopularity():
    results = collection.find({})
    reivewPairs = {}
    for result in results:
        name = result[rigelSettings.KEY_trackName()]
        rating = result[rigelSettings.KEY_userRating()][rigelSettings.KEY_ratingCount()]
        reivewPairs[name] = rating

    listofTuples = sorted(reivewPairs.items() ,reverse=True, key=lambda x: x[1])

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

    listofTuples = sorted(reivewPairs.items() ,reverse=True, key=lambda x: x[1])

    num = 1
    for item in listofTuples:
        print(str(num) + " : " + str(item))
        num += 1

def testWrite():
    logger.log("testWrite")
    num = 0

if __name__ == '__main__':
    logger = Helpers.Logger("MongoSetupIndexes", Helpers.mongoLogColor)
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

    testWrite()
    #setupTagsIndex()
    # showTagsByPopularity()
    #showGamesByPopularity()
    #showGamesByReleaseDate()

    sys.exit(1)
