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
from pymongo import TEXT
from Settings import mongoSettings
from Settings import miraSettings
from Settings import rigelSettings
from Settings import mongoIndexNames
from datetime import datetime
import Helpers
import json
from pprint import pprint

def setup(indexes, indexName, createFunc):
    if indexName in indexes.keys():
        logger.log("Index exists: " + indexName)
        return False
    else:
        logger.log("Creating index: " + indexName)
        createFunc(indexName)
        return True

def setupTextIndexes(indexName):
    collection.create_index( 
        [
            ("trackName", TEXT), 
            ("searchBlob.sellerName", TEXT),
            ("tags", TEXT)
        ],
        weights={
            "trackName": 2,
            "searchBlob.sellerName": 2,
            "tags": 1
        },
        name=indexName)

def setupDeviceIndex(indexName):
    collection.create_index("lookupBlob.deviceFamilies", name=indexName)

def setupReleaseDateIndex(indexName):
    collection.create_index("lookupBlob.releaseDate", name=indexName)

def setupPriceIndex(indexName):
    collection.create_index("searchBlob.price", name=indexName)

def setupPopularityIndex(indexName):
    collection.create_index("lookupBlob.userRating.ratingCount", name=indexName)

def setupMetaRankingIndex(indexName):
    collection.create_index("metaRanking", name=indexName)

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

    # array of creation functions, in a tuple with the name of the index
    creationFuncs = [
        (mongoIndexNames.TEXT_INDEX(), setupTextIndexes),
        (mongoIndexNames.DEVICE_FAMILIES_INDEX(), setupDeviceIndex),
        (mongoIndexNames.RELEASE_DATE_INDEX(), setupReleaseDateIndex),
        (mongoIndexNames.PRICE_INDEX(), setupPriceIndex),
        (mongoIndexNames.POPULARITY_INDEX(), setupPopularityIndex),
        (mongoIndexNames.METARANKING_INDEX(), setupMetaRankingIndex),
    ]

    indexes = collection.index_information()

    # # delete all indexes
    # for func in creationFuncs:
    #     if func[0] in indexes.keys():
    #         logger.log("Deleting index: " + func[0])
    #         collection.drop_index(func[0])

    ## create all indexes if they don't already exist
    for func in creationFuncs:
        setup(indexes, func[0], func[1])

    sys.exit(1)
