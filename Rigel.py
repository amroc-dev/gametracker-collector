#######################################################################
# Rigel
# Step 2 in Mira -> Rigel -> Mongo chain
# Collects results from Mira_OUT folder, then performs an Apple Api Lookup request
# This returns other essential information (particularly whether the app has in app purchases or not)
# Apps which pass this stage are saved to Rigel_OUT
#######################################################################


import time
import os
import os.path
from os import path
import sys
import requests
import json
from pprint import pprint
import uuid
from nested_lookup import nested_lookup
from tendo import singleton
import colored
import random
import Helpers
import math
import pymongo
from pymongo import MongoClient
import bson
import numpy
from Mongo import Mongo
from Shared import settings
import datetime

########################################################################


class AppEntry:
    def __init__(self, searchTerm, searchBlob, lookupBlob):
        self.tags = self.getGenreList(searchTerm, lookupBlob)
        self.searchBlob = searchBlob
        self.lookupBlob = lookupBlob
        self.metaRanking = self.calcRanking()
        self.trackId = searchBlob[settings.mira.api_keys.trackId]

    # MetaRanking is a ranking caluculated from a combination of:
    # The game's popularity (lookupBlob.userRating.ratingCount), and:
    # The game's user rating (lookupBlob.userRating.value)
    # algorithm from: https://steamdb.info/blog/steamdb-rating/
    def calcRanking(self):
        userRatingField = self.lookupBlob["userRating"]
        ratingCount = userRatingField["ratingCount"]
        rating = userRatingField["value"]
        normRating = rating / 5.0
        return normRating - (normRating - 0.5) * pow(2, -math.log10(ratingCount + 1))

    def getGenreList(self, searchTerm, lookupBlob):
        genreList = []
        genreList.append(searchTerm)
        genres = lookupBlob[settings.rigel.api_keys.genres]
        if genres:
            for genreEntry in genres:
                genreName = genreEntry[settings.rigel.api_keys.genres_name]
                if genreName.lower() in settings.rigel.ignoreGenres:
                    continue
                if genreName not in genreList:
                    genreList.append(genreName)

        return genreList


########################################################################
class MongoWriter:

    def __init__(self, mongo):
        self.mongo = mongo

    def write(self, appEntries):
        bulkUpdates = []
        for appEntry in appEntries:
            self.addEntryToBulkUpdates(appEntry, bulkUpdates)
        try:
            results = self.mongo.collection_games.bulk_write(
                bulkUpdates)
            self.mongo.logger.log("Databased updated. Added: " + str(results.upserted_count) +
                                         ", modified: " + str(results.modified_count))
        except pymongo.errors.PyMongoError as e:
            self.mongo.log("bulk_write error: " + str(e))
            return False

        return True

    def addEntryToBulkUpdates(self, appEntry, bulkUpdatesArray):
        dateNow = str(datetime.datetime.now())
        
        data = {
            settings.rigel.api_keys.trackName: appEntry.searchBlob[settings.rigel.api_keys.trackName],
            settings.rigel.db_keys.metaRanking: appEntry.metaRanking,
            settings.rigel.db_keys.searchBlob: appEntry.searchBlob,
            settings.rigel.db_keys.lookupBlob: appEntry.lookupBlob,
            settings.mongoValidator.db_keys.dateValidated: dateNow,
        }

        # the db update operation for a game entry
        groupUpdate = {
            '$set': data,  # just overwrite everything in data
            # merge any new tags into the existing array of tags
            '$addToSet': {"tags": {"$each": appEntry.tags}}
        }

        trackId = bson.int64.Int64(appEntry.trackId)
        bulkUpdatesArray.append(pymongo.UpdateOne(
            {'_id': trackId}, groupUpdate, upsert=True))


########################################################################
class Rigel:
    def __init__(self, mongo):
        self.logger = Helpers.Logger("Rigel", Helpers.rigelLogColor)
        self.logger.log("Starting")
        self.miraResults = [] # this is the list of results that get added from Mira. Rigel will process this list from the front and remove them when done
        self.mongoWriter = MongoWriter(mongo)

    def addMiraResults(self, results):
        for r in results:
            self.miraResults.append(r)

    def removeFromMiraResults(self, trackId):
        idx = 0
        for entry in self.miraResults:
            if numpy.int64(trackId) == numpy.int64(entry.trackId):
                self.miraResults.pop(idx)
                return
            idx = idx + 1

    def clear(self):
        self.miraResults = []

    def isEmpty(self):
        return len(self.miraResults) == 0

    def update(self, searchTerm):
        if len(self.miraResults) == 0:
            self.logger.log("Waiting...")
            return

        chunkOfResults = self.miraResults[0:settings.mira.limit]
        appEntries = []
        self.doMetaLookup(chunkOfResults, searchTerm, appEntries)

        if len(appEntries) > 0:
            writeStatusOk = self.mongoWriter.write(appEntries)
            if not writeStatusOk:
                return settings.rigel.returnCodes.mongoWriteFail

        return

    def doMetaLookup(self, miraResultsChunk, searchTerm, appEntriesOUT):
        trackIds = []

        for miraResult in miraResultsChunk:
            trackId = miraResult.appleSearchBlob[settings.mira.api_keys.trackId]
            trackIds.append(trackId)

        # format the list into a comma seperated string, which the request API requires
        trackIdRequestList = ""
        for trackId in trackIds:
            trackIdRequestList = trackIdRequestList + str(trackId) + ","
        trackIdRequestList = trackIdRequestList[:-1]

        requestString = str(len(miraResultsChunk))
        if len(self.miraResults) > len(miraResultsChunk):
            requestString = requestString + " of " + str(len(self.miraResults))
        self.logger.log(" iTunes lookup... requesting: " + requestString)
        try:
            lookupResponse = requests.get(settings.rigel.lookupURL_base.replace(
                "__ID__", trackIdRequestList, 1), timeout=10)
        except requests.exceptions.RequestException as e:
            self.logger.log(str(e))
            return

        resultCount = 0
        lowReviewCount = 0

        if lookupResponse.ok:
            jsonResponse = lookupResponse.json()
            lookupBlobs = jsonResponse[settings.rigel.api_keys.results]
            resultCount = len(lookupBlobs.values())

            # Remove all the results that are returned, from self.miraResults
            processedTrackIds = []
            for lookupBlob in lookupBlobs.values():
                processedTrackIds.append(
                    lookupBlob[settings.rigel.api_keys.id])
            for processedTrackId in processedTrackIds:
                self.removeFromMiraResults(processedTrackId)

            # Special case: if no results come back, then remove all self.miraResults that are withing this chunk
            # Not sure if this will ever happen but its probably possible.
            # This just ensures if there's an discrepencies between the Apple search and lookup servers, rigel won't get stuck for ever trying to lookup trackIds that don't exist
            if resultCount == 0:
                for miraResult in miraResultsChunk:
                    self.removeFromMiraResults(miraResult.trackId)

            for lookupBlob in lookupBlobs.values():
                trackId = lookupBlob[settings.rigel.api_keys.id]

                if self.hasInAppPurchases(lookupBlob):
                    continue

                userRating = nested_lookup(
                    key=settings.rigel.api_keys.userRating, document=lookupBlob)
                ratingCount = nested_lookup(
                    key=settings.rigel.api_keys.ratingCount, document=userRating)

                # double check the app has enough ratings to be considered (occasionally some apps coming from the search don't have a review count field)
                if int(ratingCount[0]) < settings.mira.minRatings:
                    lowReviewCount += 1
                    continue

                # associate the result back with the searchBlob
                matchingSearchBlob = None
                for miraResult in miraResultsChunk:
                    if str(miraResult.appleSearchBlob[settings.mira.api_keys.trackId]) == str(trackId):
                        matchingSearchBlob = miraResult.appleSearchBlob
                        break

                # this should never happen
                if matchingSearchBlob == None:
                    self.logger.log(
                        "Warning, lookup returned a trackId that wasn't requested!?")

                appEntriesOUT.append(
                    AppEntry(searchTerm, matchingSearchBlob, lookupBlob))

            self.logger.log("Results: " + str(resultCount) + ", matches: " + str(len(appEntriesOUT)))
        else:
            self.logger.log(
                "Lookup request failed with status code:" + str(lookupResponse.status_code))

    def hasInAppPurchases(self, lookupBlob):
        # check if app has in app purchases or not
        inAppResults = nested_lookup(
            key=settings.rigel.api_keys.hasInAppPurchases, document=lookupBlob)
        hasInApp = False
        if isinstance(inAppResults, list) and len(inAppResults) > 0:
            hasInApp = True
            if False in inAppResults:
                hasInApp = False
        elif inAppResults is bool:
            hasInApp = inAppResults

        return hasInApp

# class Rigel:
#     def __init__(self):
#         self.scanSleeper = Helpers.Sleeper(rigelSettings.MIRA_OUT_SCAN_TIME())
#         self.lookupSleeper = Helpers.Sleeper(rigelSettings.MIN_SEARCH_TIME())

#     def run(self):
#         while True:
#             self.scanSleeper.sleepIfNecessary()
#             miraResults = self.doMiraScan()
#             if miraResults != -1:
#                 appEntries = self.doMetaLookup(miraResults[1])
#                 if appEntries != -1:
#                    self.dumpResults(appEntries)
#                    os.remove(miraResults[0])

#     def doMiraScan(self):
#         fileNameList = os.listdir(miraSettings.OUTPUT_DIR())

#         for fileName in fileNameList:
#             if fileName.startswith(miraSettings.RESULTS_FILENAME()):
#                 # logger.log("Reading: " + fileName)
#                 fullPath = miraSettings.OUTPUT_DIR() + "/" + fileName
#                 with open(fullPath, encoding='utf-8') as json_file:
#                      miraResults = json.load(json_file)
#                      return (fullPath, miraResults)

#         return -1

#     def hasInAppPurchases(self, metaResult):
#         # check if app has in app purchases or not
#         inAppResults = nested_lookup(key = rigelSettings.KEY_hasInAppPurchases(), document = metaResult)
#         hasInApp = False
#         if isinstance(inAppResults, list) and len(inAppResults) > 0:
#             hasInApp = True
#             if False in inAppResults:
#                 hasInApp = False
#         elif inAppResults is bool:
#             hasInApp = inAppResults

#         return hasInApp

#     # # collect the apple genres and the search term into one list
#     def getGenreList(self, searchTerm, lookupBlob):
#         genreList = []
#         genreList.append(searchTerm)
#         genres = lookupBlob[rigelSettings.KEY_genres()]
#         if genres:
#             for genreEntry in genres:
#                 genreName = genreEntry[rigelSettings.KEY_genres_name()]
#                 if genreName == "games":
#                     continue
#                 if genreName.lower() in rigelSettings.ignoreGenres():
#                     continue
#                 if genreName not in genreList:
#                     genreList.append(genreName)

#         return genreList

#     def makeAppEntry(self, searchTerm, searchBlob, lookupBlob):
#         appEntry = {}
#         appEntry[rigelSettings.GAMEKEY_tags()] = self.getGenreList(searchTerm, lookupBlob)
#         appEntry[rigelSettings.KEY_searchBlob()] = searchBlob
#         appEntry[rigelSettings.KEY_lookupBlob()] = lookupBlob

#         # calc the metaRanking
#         appEntry[rigelSettings.GAMEKEY_metaRanking()] = calcRanking(appEntry)

#         return appEntry

#     def dumpResults(self, appEntries):
#         if len(appEntries) > 0:
#             uniqueID = str(uuid.uuid1().hex)
#             tempPath = rigelSettings.OUTPUT_DIR() + "/" + rigelSettings.RESULTS_TEMP_FILENAME() + "_" + uniqueID + rigelSettings.RESULTS_FILENAME_EXTENSION()
#             with open(tempPath, 'w', encoding='utf-8') as outfile:
#                 json.dump(appEntries, outfile, indent=4, ensure_ascii=False)

#             fileName = rigelSettings.RESULTS_FILENAME() + "_" + uniqueID + rigelSettings.RESULTS_FILENAME_EXTENSION()
#             os.rename(tempPath, rigelSettings.OUTPUT_DIR() + "/" + fileName)

#     def doMetaLookup(self, miraResults):
#         searchTerm = miraResults[miraSettings.MIRA_KEY_term()]
#         trackIds = []

#         allBlobs = miraResults[miraSettings.MIRA_KEY_appleSearchBlobs()]
#         for blob in allBlobs:
#             trackId = blob[miraSettings.KEY_trackId()]
#             trackIds.append(trackId)

#         # format the list into a comma seperated string, which the request API requires
#         trackIdRequestList = ""
#         for trackId in trackIds:
#             trackIdRequestList = trackIdRequestList + str(trackId) + ","
#         trackIdRequestList = trackIdRequestList[:-1]

#         logger.log(" iTunes lookup...")
#         self.lookupSleeper.sleepIfNecessary(logger, "Lookup")
#         try:
#             lookupResponse = requests.get(rigelSettings.metaLookupURL_base().replace("__ID__", trackIdRequestList, 1), timeout = 10)
#         except requests.exceptions.RequestException as e:
#             logger.log(e)

#         appEntries = []
#         resultCount = 0
#         lowReviewCount = 0

#         if lookupResponse.ok:
#             jsonResponse = lookupResponse.json()
#             metaResults = jsonResponse[rigelSettings.KEY_results()]
#             if len(metaResults.values()) != len(trackIds):
#                 logger.log("Warning, received only " + str(len(metaResults.values())) + "/" + str(len(trackIds)) + " lookup results")

#             resultCount = len(metaResults.values())

#             logger.log("Results: " + str(resultCount))

#             for metaResult in metaResults.values():
#                 trackId = metaResult[rigelSettings.KEY_id()]

#                 if self.hasInAppPurchases(metaResult):
#                     continue

#                 userRating = nested_lookup(key = rigelSettings.KEY_userRating(), document = metaResult)
#                 ratingCount = nested_lookup(key = rigelSettings.KEY_ratingCount(), document = userRating)

#                 # double check the app has enough ratings to be considered (occasionally some apps coming from the search don't have a review count field)
#                 if int(ratingCount[0]) < rigelSettings.MIN_RATINGS():
#                     lowReviewCount += 1
#                     continue

#                 searchBlob = None
#                 for blob in allBlobs:
#                     if str(blob[miraSettings.KEY_trackId()]) == str(trackId):
#                         searchBlob = blob
#                         break

#                 appEntries.append(self.makeAppEntry(searchTerm, searchBlob, metaResult))

#             logger.log("Matches: " + str(len(appEntries)))
#             return appEntries

#         else:
#             logger.log("Lookup request failed with status code:" + str(lookupResponse.status_code))

#         return -1

# #####################################################################

# if __name__ == '__main__':

#     logger = Helpers.Logger("Rigel", Helpers.rigelLogColor)
#     logger.log("Starting")
#     me = singleton.SingleInstance()

#     if not os.path.exists(rigelSettings.OUTPUT_DIR()):
#          os.makedirs(rigelSettings.OUTPUT_DIR())

#     Rigel().run()
