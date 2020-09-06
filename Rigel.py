import time
import os
import os.path
from os import path
import sys
import requests
import json
from pprint import pprint
import uuid
from Settings import miraSettings
from Settings import rigelSettings
from nested_lookup import nested_lookup
from tendo import singleton
import colored
import random
import Helpers

class Rigel:
    def __init__(self):
        self.scanSleeper = Helpers.Sleeper(rigelSettings.MIRA_OUT_SCAN_TIME())
        self.lookupSleeper = Helpers.Sleeper(rigelSettings.MIN_SEARCH_TIME())

    def run(self):
        while True:
            self.scanSleeper.sleepIfNecessary()
            miraResults = self.doMiraScan()
            if miraResults != -1:
                appEntries = self.doMetaLookup(miraResults[1])
                if appEntries != -1:
                   self.dumpResults(appEntries)
                   os.remove(miraResults[0])

    def doMiraScan(self):
        fileNameList = os.listdir(miraSettings.OUTPUT_DIR())
        
        for fileName in fileNameList:
            if fileName.startswith(miraSettings.RESULTS_FILENAME()):
                # logger.log("Reading: " + fileName)
                fullPath = miraSettings.OUTPUT_DIR() + "/" + fileName
                with open(fullPath, encoding='utf-8') as json_file:
                     miraResults = json.load(json_file)
                     return (fullPath, miraResults)

        return -1

    def hasInAppPurchases(self, metaResult):
        # check if app has in app purchases or not
        inAppResults = nested_lookup(key = rigelSettings.KEY_hasInAppPurchases(), document = metaResult)
        hasInApp = False
        if isinstance(inAppResults, list) and len(inAppResults) > 0:
            hasInApp = True
            if False in inAppResults:
                hasInApp = False
        elif inAppResults is bool:
            print("BOOL! " + inAppResults)
            hasInApp = inAppResults

        return hasInApp

    # # collect the apple genres and the search term into one list
    def getGenreList(self, searchTerm, lookupBlob):
        genreList = []
        genreList.append(searchTerm.lower())
        genres = lookupBlob[rigelSettings.KEY_genres()]
        if genres:
            for genreEntry in genres:
                genreName = genreEntry[rigelSettings.KEY_genres_name()].lower()
                if genreName == "games":
                    continue
                # if genreName not in rigelSettings.appStoreGameGenres():
                #     continue
                if genreName not in genreList:
                    genreList.append(genreName)

        return genreList

    def makeAppEntry(self, searchTerm, searchBlob, lookupBlob):
        appEntry = {}
        appEntry[rigelSettings.GAMEKEY_tags()] = self.getGenreList(searchTerm, lookupBlob)
        appEntry[rigelSettings.KEY_searchBlob()] = searchBlob
        appEntry[rigelSettings.KEY_lookupBlob()] = lookupBlob
        return appEntry

    def dumpResults(self, appEntries):
        if len(appEntries) > 0:
            uniqueID = str(uuid.uuid1().hex)
            tempPath = rigelSettings.OUTPUT_DIR() + "/" + rigelSettings.RESULTS_TEMP_FILENAME() + "_" + uniqueID + rigelSettings.RESULTS_FILENAME_EXTENSION()
            with open(tempPath, 'w', encoding='utf-8') as outfile:
                json.dump(appEntries, outfile, indent=4, ensure_ascii=False)

            fileName = rigelSettings.RESULTS_FILENAME() + "_" + uniqueID + rigelSettings.RESULTS_FILENAME_EXTENSION()
            os.rename(tempPath, rigelSettings.OUTPUT_DIR() + "/" + fileName)

    def doMetaLookup(self, miraResults):
        searchTerm = miraResults[miraSettings.MIRA_KEY_term()]
        trackIds = []
        
        allBlobs = miraResults[miraSettings.MIRA_KEY_appleSearchBlobs()]
        for blob in allBlobs:
            trackId = blob[miraSettings.KEY_trackId()]
            trackIds.append(trackId)

        # format the list into a comma seperated string, which the request API requires
        trackIdRequestList = ""
        for trackId in trackIds:
            trackIdRequestList = trackIdRequestList + str(trackId) + ","
        trackIdRequestList = trackIdRequestList[:-1]

        logger.log(" iTunes lookup...")
        self.lookupSleeper.sleepIfNecessary(logger, "Lookup")
        try:
            lookupResponse = requests.get(rigelSettings.metaLookupURL_base().replace("__ID__", trackIdRequestList, 1))
        except requests.exceptions.RequestException as e:
            logger.log(e)

        appEntries = []
        resultCount = 0
        lowReviewCount = 0

        if lookupResponse.ok:
            jsonResponse = lookupResponse.json()
            metaResults = jsonResponse[rigelSettings.KEY_results()]
            if len(metaResults.values()) != len(trackIds):
                logger.log("Warning, received only " + str(len(metaResults.values())) + "/" + str(len(trackIds)) + " lookup results")

            resultCount = len(metaResults.values())

            logger.log("Results: " + str(resultCount))
                
            for metaResult in metaResults.values():
                trackId = metaResult[rigelSettings.KEY_id()]
                trackName = metaResult[rigelSettings.KEY_name()]

                if self.hasInAppPurchases(metaResult):
                    continue

                userRating = nested_lookup(key = rigelSettings.KEY_userRating(), document = metaResult)
                ratingCount = nested_lookup(key = rigelSettings.KEY_ratingCount(), document = userRating)
      
                # double check the app has enough ratings to be considered (occasionally some apps coming from the search don't have a review count field)
                if int(ratingCount[0]) < rigelSettings.MIN_RATINGS():
                    lowReviewCount += 1
                    continue

                searchBlob = None
                for blob in allBlobs:
                    if str(blob[miraSettings.KEY_trackId()]) == str(trackId):
                        searchBlob = blob
                        break
           
                appEntries.append(self.makeAppEntry(searchTerm, searchBlob, metaResult))
            
            logger.log("Matches: " + str(len(appEntries)))
            return appEntries

        else:
            logger.log("Lookup request failed with status code:" + str(lookupResponse.status_code))

        return -1

#####################################################################

if __name__ == '__main__':
    
    logger = Helpers.Logger("Rigel", Helpers.rigelLogColor)
    logger.log("Starting")
    me = singleton.SingleInstance()

    if not os.path.exists(rigelSettings.OUTPUT_DIR()):
         os.makedirs(rigelSettings.OUTPUT_DIR())

    Rigel().run()
