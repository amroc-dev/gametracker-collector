#######################################################################
# MongoValidator
# Scans all existing games in database, performing two checks:
# 1. Does the app have IAP (this could happen if the developer has since added IAP in an update)
# 2. Does the app no longer return a result in the iTunes lookup API (guess this means the app has been removed from sale?)
# If either of these two conditions are met, the game is deleted from the database
#######################################################################

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
from Settings import mongoValidatorSettings
from nested_lookup import nested_lookup
from datetime import datetime
import Helpers
import colored
import datetime

class MongoValidator:
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

    def hasInAppPurchases(self, metaResult):
        # check if app has in app purchases or not
        inAppResults = nested_lookup(key = rigelSettings.KEY_hasInAppPurchases(), document = metaResult)
        hasInApp = False
        if isinstance(inAppResults, list) and len(inAppResults) > 0:
            hasInApp = True
            if False in inAppResults:
                hasInApp = False
        elif inAppResults is bool:
            hasInApp = inAppResults

        return hasInApp

    def update(self):
        dateValidatedKey = mongoValidatorSettings.KEY_dateValidated()
        sortType = [(dateValidatedKey, -1)]
        # query = {"dateValidated" : {"$lte": dateQuery}}
        # query = {"$or" : [{"trackName": "Kiwanuka"}, {"trackName": "Downwell"}]}
        # query = {"trackName": {"$exists" : False}}
        dateQuery = str(datetime.datetime.now() - datetime.timedelta(days=1))
        query = {"$or" : 
            [{dateValidatedKey: {"$exists" : False}}, 
             {dateValidatedKey : {"$lte": dateQuery}}]
        }
        results = self.collection.find(query, limit=mongoValidatorSettings.LOOKUP_COUNT(), sort=sortType)

        trackIds = []
        for result in results:
            # logger.log(result["trackName"] + ": " + result["searchBlob"]["releaseDate"])
            trackIds.append(result["searchBlob"]["trackId"])

        logger.log("Collected " + str(len(trackIds)))

        if (len(trackIds) == 0):
            return False

        # format the list into a comma seperated string, which the request API requires
        trackIdRequestList = ""
        for trackId in trackIds:
            trackIdRequestList = trackIdRequestList + str(trackId) + ","
        trackIdRequestList = trackIdRequestList[:-1]

        logger.log(" iTunes lookup...")
        try:
            lookupResponse = requests.get(rigelSettings.metaLookupURL_base().replace("__ID__", trackIdRequestList, 1))
        except requests.exceptions.RequestException as e:
            logger.log(e)

        appEntries = []
        resultCount = 0
        bulkUpdatesArray = []

        if lookupResponse.ok:
            jsonResponse = lookupResponse.json()
            metaResults = jsonResponse[rigelSettings.KEY_results()]
            resultCount = len(metaResults.values())
            logger.log("Results: " + str(resultCount))

            dateNow = str(datetime.datetime.now())

            # If iTunes returns no results for the current trackIds, then go ahead and delete them from the database
            if resultCount == 0:
                for trackId in trackIds:
                    bulkUpdatesArray.append(pymongo.DeleteOne( {'_id': bson.int64.Int64(trackId)} ))
            else:
                for metaResult in metaResults.values():
                    trackId = metaResult[rigelSettings.KEY_id()]
                    trackName = metaResult[rigelSettings.KEY_name()]
                    dateValidatedEntry = { dateValidatedKey : dateNow }

                    # if IAP is detected, delete the game
                    if self.hasInAppPurchases(metaResult):
                        logger.log("IAP detected for: " + trackName + " (" + str(trackId) + "), deleting...")
                        bulkUpdatesArray.append(pymongo.DeleteOne( {'_id': bson.int64.Int64(trackId)} ))
                    # otherwise, update the date validated with the current date
                    else:
                        bulkUpdatesArray.append(pymongo.UpdateOne(
                            {'_id': bson.int64.Int64(trackId)}, {'$set': dateValidatedEntry}, upsert=True)
                        )
    
            if len(bulkUpdatesArray) > 0:
                dbResults = self.collection.bulk_write(bulkUpdatesArray)
                logger.log("Databased updated. Modified: " + str(dbResults.modified_count) + ", Deleted: " + str(dbResults.deleted_count))
        
        return True
                    
if __name__ == '__main__':
    logger = Helpers.Logger("MongoValidator", Helpers.mongoValidatorLogColor)

    me = singleton.SingleInstance()
    logger.log("Starting")
    mongoValidator = MongoValidator()

    if False == mongoValidator.connect():
        logger.log("Retrying")
        os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)
    while True:
        t = time.time()
        result = mongoValidator.update()
        if False == result:
            break

        sleepTime = mongoValidatorSettings.UPDATE_INTERVAL() - (time.time() - t)
        if sleepTime > 0:
            time.sleep(sleepTime)

    logger.log("All games up to date")
