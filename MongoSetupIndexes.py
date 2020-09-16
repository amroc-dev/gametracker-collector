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

def setupAll():
    indexes = collection.index_information()
    if mongoIndexNames.TRACKNAME_SELLER() in indexes.keys():
        logger.log("Index exists: " + mongoIndexNames.TRACKNAME_SELLER())
    else:
        setupTextIndexes();
    if mongoIndexNames.TAGS() in indexes.keys():
        logger.log("Index exists: " + mongoIndexNames.TAGS())
    else:
        setupTagsIndex();

def setupTextIndexes():
    indexName = mongoIndexNames.TRACKNAME_SELLER()
    logger.log("Creating index: " + indexName)
    collection.create_index([(
        "trackName", TEXT), 
        ("searchBlob.sellerName", TEXT)],
        name=indexName)

def setupTagsIndex():
    indexName = mongoIndexNames.TAGS()
    logger.log("Creating index: " + indexName)
    collection.create_index([("tags", pymongo.ASCENDING)],
        name=indexName)

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

    setupAll()

    sys.exit(1)
