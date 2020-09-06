import os
import os.path
from os import path
import time
import sys
import requests
import json
import pymongo
from pymongo import MongoClient
import bson
from pprint import pprint
from tendo import singleton
from Settings import rigelSettings
from Settings import mongoSettings
import Helpers
import colored
import datetime


class Mongo:
    def __init__(self):
        self.client = None
        self.database = None
        self.collection = None

    def connect(self):
        logger.log("Connecting to database")
        try:
            self.client = MongoClient(mongoSettings.CONNECTION_STRING())
            self.database = self.client[mongoSettings.DATABASE_NAME()]
            self.collection = self.database[mongoSettings.COLLECTION_NAME()]
            logger.log("Connection Ok")
        except pymongo.errors.PyMongoError as e:
            logger.log("Connection Failure: " + str(e))
            return False

        return True

    def updateOutputScan(self):
        fileNameList = os.listdir(rigelSettings.OUTPUT_DIR())
        fileProcessed = False

        for fileName in fileNameList:
            if fileName.startswith(rigelSettings.RESULTS_FILENAME()):
                self.processFile(fileName)
                fileProcessed = True

        return fileProcessed

    def processFile(self, fileName):
        fullPath = rigelSettings.OUTPUT_DIR() + "/" + fileName
        with open(fullPath, encoding='utf-8') as json_file:
            rigelResults = json.load(json_file)
            bulkUpdates = []
            for result in rigelResults:
                self.addEntryToBulkUpdates(result, bulkUpdates)
            try:
                results = mongo.collection.bulk_write(bulkUpdates)
                logger.log("Databased updated. Added: " + str(results.upserted_count) +
                       ", modified: " + str(results.modified_count))
            except pymongo.errors.PyMongoError as e:
                logger.log("bulk_write error: " + str(e))
        os.remove(fullPath)

    def addEntryToBulkUpdates(self, result, bulkUpdatesArray):
        tags = result[rigelSettings.GAMEKEY_tags()]
        searchBlob = result[rigelSettings.KEY_searchBlob()]
        lookupBlob = result[rigelSettings.KEY_lookupBlob()]
        trackId = bson.int64.Int64(searchBlob[rigelSettings.KEY_trackId()])
        trackName = searchBlob[rigelSettings.KEY_trackName()]

        data = {
            rigelSettings.KEY_trackName() : trackName,
            rigelSettings.GAMEKEY_tags() : tags,
            rigelSettings.KEY_searchBlob() : searchBlob,
            rigelSettings.KEY_lookupBlob() : lookupBlob,
        }

        bulkUpdatesArray.append(pymongo.UpdateOne(
            {'_id': trackId}, {'$set': data}, upsert=True))

if __name__ == '__main__':
    logger = Helpers.Logger("Mongo", Helpers.mongoLogColor)

    me = singleton.SingleInstance()
    logger.log("Starting")
    mongo = Mongo()

    if False == mongo.connect():
        logger.log("Retrying")
        os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)
    while True:
        t = time.time()
        mongo.updateOutputScan()
        sleepTime = mongoSettings.OUTPUT_SCAN_INTERVAL() - (time.time() - t)
        if sleepTime > 0:
            time.sleep(sleepTime)
