#######################################################################
# MongoUpdateGames
# Scans all existing games in database, performing two checks:
# 1. Does the app have IAP (this could happen if the developer has since added IAP in an update)
# 2. Does the app no longer return a result in the iTunes lookup API (guess this means the app has been removed from sale?)
# If either of these two conditions are met, the game is deleted from the database
#######################################################################

import time
import requests
import pymongo
import bson
from nested_lookup import nested_lookup
import datetime

from Mongo import Mongo
from Shared import settings
import Helpers

class MongoValidator:
    def __init__(self, mongo):
        self.logger = Helpers.Logger(__class__.__name__, Helpers.mongoLogColor)
        self.mongo = mongo

    def start(self):
        while True:
            t = time.time()
            result = self.update()
            if False == result:
                break

            sleepTime = settings.mongoValidator.updateInterval - (time.time() - t)
            if sleepTime > 0:
                time.sleep(sleepTime)

        self.logger.log("All games up to date")

    def hasInAppPurchases(self, metaResult):
        # check if app has in app purchases or not
        inAppResults = nested_lookup(
            key=settings.rigel.api_keys.hasInAppPurchases, document=metaResult)
        hasInApp = False
        if isinstance(inAppResults, list) and len(inAppResults) > 0:
            hasInApp = True
            if False in inAppResults:
                hasInApp = False
        elif inAppResults is bool:
            hasInApp = inAppResults

        return hasInApp

    def update(self):
        dateValidatedKey = settings.mongoValidator.db_keys.dateValidated
        sortType = [(dateValidatedKey, -1)]
        # query = {"dateValidated" : {"$lte": dateQuery}}
        # query = {"$or" : [{"trackName": "Kiwanuka"}, {"trackName": "Downwell"}]}
        # query = {"trackName": {"$exists" : False}}
        dateQuery = str(datetime.datetime.now() - datetime.timedelta(days=1))
        query = {"$or":
                 [{dateValidatedKey: {"$exists": False}},
                  {dateValidatedKey: {"$lte": dateQuery}}]
                 }
        results = self.mongo.collection_games.find(
            query, limit=settings.mongoValidator.lookupCount, sort=sortType)

        trackIds = []
        for result in results:
            # logger.log(result["trackName"] + ": " + result["searchBlob"]["releaseDate"])
            trackIds.append(result["searchBlob"]["trackId"])

        self.logger.log("Collected " + str(len(trackIds)))

        if (len(trackIds) == 0):
            return False

        # format the list into a comma seperated string, which the request API requires
        trackIdRequestList = ""
        for trackId in trackIds:
            trackIdRequestList = trackIdRequestList + str(trackId) + ","
        trackIdRequestList = trackIdRequestList[:-1]

        self.logger.log(" iTunes lookup...")
        try:
            lookupResponse = requests.get(
                settings.rigel.lookupURL_base.replace("__ID__", trackIdRequestList, 1))
        except requests.exceptions.RequestException as e:
            self.logger.log(e)

        resultCount = 0
        bulkUpdatesArray = []

        if lookupResponse.ok:
            jsonResponse = lookupResponse.json()
            metaResults = jsonResponse[settings.rigel.api_keys.results]
            resultCount = len(metaResults.values())
            self.logger.log("Results: " + str(resultCount))

            dateNow = str(datetime.datetime.now())

            # If iTunes returns no results for the current trackIds, then go ahead and delete them from the database
            if resultCount == 0:
                for trackId in trackIds:
                    bulkUpdatesArray.append(pymongo.DeleteOne(
                        {'_id': bson.int64.Int64(trackId)}))
            else:
                for metaResult in metaResults.values():
                    trackId = metaResult[settings.rigel.api_keys.id]
                    trackName = metaResult[settings.rigel.api_keys.name]
                    dateValidatedEntry = {dateValidatedKey: dateNow}

                    # if IAP is detected, delete the game
                    if self.hasInAppPurchases(metaResult):
                        self.logger.log(
                            "IAP detected for: " + trackName + " (" + str(trackId) + "), deleting...")
                        bulkUpdatesArray.append(pymongo.DeleteOne(
                            {'_id': bson.int64.Int64(trackId)}))
                    # otherwise, update the date validated with the current date
                    else:
                        bulkUpdatesArray.append(pymongo.UpdateOne(
                            {'_id': bson.int64.Int64(trackId)}, {'$set': dateValidatedEntry}, upsert=True)
                        )

            if len(bulkUpdatesArray) > 0:
                dbResults = self.mongo.collection_games.bulk_write(bulkUpdatesArray)
                self.logger.log("Databased updated. Modified: " + str(
                    dbResults.modified_count) + ", Deleted: " + str(dbResults.deleted_count))

        return True


if __name__ == '__main__':
    mongo = Mongo("MongoValidator")
    MongoValidator(mongo).start()
