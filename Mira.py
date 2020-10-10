#######################################################################
# Mira
# Step 1 in Mira -> Rigel -> Mongo chain
# Traverses through all specified search term, and uses Apple search API to return matches
# results are saved to Mira_OUT folder
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
import argparse
from nested_lookup import nested_lookup
from tendo import singleton
import colored
import random
import Helpers
import tldextract
from Shared import settings


class MiraResult:
    def __init__(self, appleSearchBlob):
        self.appleSearchBlob = appleSearchBlob
        self.trackId = appleSearchBlob[settings.mira.api_keys.trackId]

class Mira:
    def __init__(self):
        self.miraResults = []
        self.logger = Helpers.Logger("Mira ", Helpers.miraLogColor)
        self.logger.log("Starting")
        self.currentTerm = None
        self.offset = 0
        self.exhaustedSearchCount = settings.mira.exhaustedSearchCount
        self.searchOngoing = False

    def setTerm(self, term):
        if len(self.miraResults) > 0:
            self.logger.log(
                "Warning, new term started but there are still miraResults left over from previous term, make sure to getMiraResults() first")

        self.miraResults = []
        self.currentTerm = term
        self.logger.log("Term: " + term)
        self.offset = 0
        self.exhaustedSearchCount = settings.mira.exhaustedSearchCount
        self.searchOngoing = True

    def getMiraResults(self):
        if len(self.miraResults) == 0:
            return None

        if self.searchOngoing and len(self.miraResults) < settings.mira.minChunkSizeForRigel:
            return None

        results = self.miraResults
        self.miraResults = []
        return results

    def update(self):
        if self.currentTerm == None:
            self.logger.log("No term set")
            return False

        if self.searchOngoing == False:
            self.logger.log("Search completed, waiting for new term")
            return False

        status = self._update()

        if status == False:
            self.searchOngoing = False

    def _update(self):
        searchURL = settings.mira.searchURL_base.replace(
            "__TERM__", str(self.currentTerm), 1)
        searchURL = searchURL.replace("__LIMIT__", str(settings.mira.limit), 1)
        searchURL = searchURL.replace("__OFFSET__", str(self.offset), 1)

        itunesSearchLogString = " iTunes search... term:" + \
            self.logger.highlight(self.currentTerm) + \
            ", offset:" + str(self.offset)
        self.logger.log(itunesSearchLogString)

        try:
            response = requests.get(searchURL, proxies=None, timeout=10)
        except requests.exceptions.RequestException as e:
            self.logger.log("Request exception: ")
            print(str(e))
            return True

        if response.ok:
            try:
                jsonResponse = response.json()
            except json.decoder.JSONDecodeError as e:
                self.logger.log("JSON decode error: ")
                print(str(e))
                return True

            resultCount = jsonResponse[settings.mira.api_keys.resultCount]
            results = jsonResponse[settings.mira.api_keys.results]
            self.logger.log("Results: " + str(resultCount))

            if resultCount < settings.mira.minResults:
                self.logger.log(
                    "Too few results (<" + str(settings.mira.minResults) + "), giving up")
                return False

            matchedResults = []
            for result in results:
                self.offset += 1

                # check and discard non paid games
                formattedPrice = nested_lookup(key='price', document=result)
                if len(formattedPrice) == 0 or float(formattedPrice[0]) == 0:
                    continue

                # check and discard games that don't meet the minimum number of ratings requirement (check for key as some old apps appear to not have this data)
                if settings.mira.api_keys.userRatingCount in result:
                    if result[settings.mira.api_keys.userRatingCount] < settings.mira.minRatings:
                        continue

                matchedResults.append(result)

            newMatchCount = len(matchedResults)

            if newMatchCount == 0:
                if self.exhaustedSearchCount > 0:
                    self.exhaustedSearchCount -= 1
                norm = 1 - (float(self.exhaustedSearchCount) /
                            settings.mira.exhaustedSearchCount)
                self.logger.log(
                    "Exhaust progress: " + Helpers.makeProgressBar(norm, settings.mira.exhaustedSearchCount))
            else:
                self.exhaustedSearchCount = settings.mira.exhaustedSearchCount
                for match in matchedResults:
                    self.miraResults.append(MiraResult(match))
                self.logger.log("Buffer size: " + str(len(self.miraResults)))
        else:
            self.logger.log(
                "Search request failed with status code:" + str(response.status_code))

        # if self.exhaustedSearchCount == 0:
        #     logger.log("Search term exhaust limit reached")
        #     return False

        # return True


# #######################################################################åå

# class Mira:
#     def __init__(self):
#         self.prepareForNewTerm()
#         self.matchedResults = []
#         self.sleeper = Helpers.Sleeper(miraSettings.MIN_SEARCH_TIME())

#     def matchedResultInBuffer(self, match):
#         trackID = match[miraSettings.KEY_trackId()]
#         inBuffer = False
#         for existingMatch in self.matchedResults:
#             if trackID == existingMatch[miraSettings.KEY_trackId()]:
#                 inBuffer = True
#                 break

#         return inBuffer

#     def addMatchedResult(self, newMatch):
#         if self.matchedResultInBuffer(newMatch) == False:
#             self.matchedResults.append(newMatch)

#         if len(self.matchedResults) == miraSettings.RESULTS_FILE_DUMP_COUNT():
#              self.dumpResults()

#     def moveToNextTerm(self):
#         self.dumpResults()
#         self.prepareForNewTerm()
#         saveFile.moveToNextTerm()
#         if saveFile.currentTerm == None:
#             return False
#         return True

#     def prepareForNewTerm(self):
#         self.exhaustedSearchCount = miraSettings.EXHAUSTED_SEARCH_COUNT()
#         self.offset = 0

#     def run(self):
#         self.prepareForNewTerm()
#         while True:
#             if self.doSearch() == False:
#                 self.moveToNextTerm()
#             if saveFile.currentTerm == None:
#                 break

#     # check there aren't too many output files waiting to be processed by Rigel (unlikely)
#     def waitForRigelIfNecessary(self):
#         while True:
#             count = 0
#             fileNameList = os.listdir(miraSettings.OUTPUT_DIR())
#             for fileName in fileNameList:
#                 if fileName.startswith(miraSettings.RESULTS_FILENAME()):
#                     count +=1

#             if count >= miraSettings.MAX_DUMPED_FILE_COUNT():
#                 logger.log("Waiting for Rigel to catch up...")
#                 time.sleep(miraSettings.MIN_SEARCH_TIME())
#             else:
#                 break

#     def dumpResults(self):
#         if len(self.matchedResults) == 0:
#             return False

#         self.waitForRigelIfNecessary()

#         data = {}
#         data[miraSettings.MIRA_KEY_term()] = saveFile.currentTerm
#         data[miraSettings.MIRA_KEY_appleSearchBlobs()] = self.matchedResults

#         uniqueID = str(uuid.uuid1().hex)
#         tempPath = miraSettings.OUTPUT_DIR() + "/" + miraSettings.RESULTS_TEMP_FILENAME() + "_" + uniqueID + miraSettings.RESULTS_FILENAME_EXTENSION()
#         with open(tempPath, 'w', encoding='utf-8') as outfile:
#             json.dump(data, outfile, indent=4, ensure_ascii=False)

#         fileName = miraSettings.RESULTS_FILENAME() + "_" + uniqueID + miraSettings.RESULTS_FILENAME_EXTENSION()
#         os.rename(tempPath, miraSettings.OUTPUT_DIR() + "/" + fileName)
#         # logger.log("*File dump*")#: " + fileName)

#         self.matchedResults.clear()

#     def doSearch(self):
#         if saveFile.currentTerm == None:
#             return False

#         searchURL = miraSettings.searchURL_base().replace("__TERM__", str(saveFile.currentTerm), 1)
#         searchURL = searchURL.replace("__LIMIT__", str(miraSettings.LIMIT()), 1)
#         searchURL = searchURL.replace("__OFFSET__", str(self.offset), 1)

#         itunesSearchLogString = " iTunes search... term:" + logger.highlight(saveFile.currentTerm) + " " + saveFile.getTermProgressString(saveFile.currentTerm) + ", offset:" + str(self.offset)
#         logger.log(itunesSearchLogString)
#         self.sleeper.sleepIfNecessary(logger, "Searching")

#         try:
#             response = requests.get(searchURL, proxies = None, timeout = 10)
#         except requests.exceptions.RequestException as e:
#             logger.log("Request exception: ")
#             print(str(e))
#             return True

#         if response.ok:
#             try:
#                 jsonResponse = response.json()
#             except json.decoder.JSONDecodeError as e:
#                 logger.log("JSON decode error: ")
#                 print(str(e))
#                 return True

#             resultCount = jsonResponse[miraSettings.KEY_resultCount()]
#             results = jsonResponse[miraSettings.KEY_results()]

#             logger.log("Results: " + str(resultCount))

#             if resultCount < miraSettings.MIN_RESULTS():
#                 logger.log("Too few results (<" + str(miraSettings.MIN_RESULTS()) + "), moving on...")
#                 return False

#             matchedResults = []
#             for result in results:
#                 self.offset += 1

#                 # check and discard non paid games
#                 formattedPrice = nested_lookup(key = 'price', document = result)
#                 if len(formattedPrice) == 0 or float(formattedPrice[0]) == 0:
#                     continue

#                 # check and discard games that don't meet the minimum number of ratings requirement (check for key as some old apps appear to not have this data)
#                 if miraSettings.KEY_userRatingCount() in result:
#                     if result[miraSettings.KEY_userRatingCount()] < miraSettings.MIN_RATINGS():
#                         continue

#                 matchedResults.append(result)

#             # check and report if app is new, ie it hasn't already been picked up in the search since the last file dump
#             addedAppsCount = 0
#             for match in matchedResults:
#                 if not self.matchedResultInBuffer(match):
#                     addedAppsCount += 1

#             logger.log("Matches: " + str(addedAppsCount))

#             if addedAppsCount == 0:
#                 if self.exhaustedSearchCount > 0:
#                     self.exhaustedSearchCount -= 1
#                 norm = 1 - (float(self.exhaustedSearchCount) / miraSettings.EXHAUSTED_SEARCH_COUNT())
#                 logger.log("Exhaust progress: " +  Helpers.makeProgressBar(norm, miraSettings.EXHAUSTED_SEARCH_COUNT()))
#             else:
#                 self.exhaustedSearchCount = miraSettings.EXHAUSTED_SEARCH_COUNT()
#                 progressNorm = float(len(self.matchedResults) + addedAppsCount) / float(miraSettings.RESULTS_FILE_DUMP_COUNT())
#                 if progressNorm > 1:
#                     progressNorm = 1
#                 logger.log("Buffer: " + Helpers.makeProgressBar(progressNorm, miraSettings.RESULTS_FILE_DUMP_COUNT()))

#             for match in matchedResults:
#                 self.addMatchedResult(match)
#         else:
#             logger.log("Search request failed with status code:" + str(response.status_code))

#         if self.exhaustedSearchCount == 0:
#             logger.log("Search term exhaust limit reached")
#             return False

#         return True

# #######################################################################

# class SaveFile:
#     def __init__(self):
#         self.path = miraSettings.OUTPUT_DIR() + "/" + miraSettings.SAVE_FILENAME()
#         self.currentTerm = None
#         self.progressString = ""
#         self.init()

#     def init(self):
#         saveData = self.__getSaveData()
#         term = saveData["working"]["term"]
#         if term is not None:
#             if not term in saveData["terms"]:
#                 logger.log("Error: working term in save file not found in terms list")
#                 term = None
#                 sys.exit(1)
#             logger.log("Resuming work")
#             self.__setCurrentTerm(term)

#     def getTermProgressString(self, term):
#         return self.progressString

#     def moveToNextTerm(self):
#         saveData = self.__getSaveData()
#         termsList = saveData["terms"]
#         nextTermIndex = termsList.index(self.currentTerm) + 1
#         nextTerm = None
#         if nextTermIndex < len(termsList):
#             nextTerm = termsList[nextTermIndex]
#         self.__setCurrentTerm(nextTerm)

#     def __getSaveData(self):
#         saveData = None
#         if not path.exists(self.path):
#             self.__createNewSaveFile()
#         with open(self.path, encoding='utf-8') as json_file:
#             saveData = json.load(json_file)
#         return saveData

#     def __setCurrentTerm(self, term):
#         self.currentTerm = term
#         saveObj = self.__getSaveData()
#         saveObj["working"]["term"] = self.currentTerm

#         with open(self.path, 'w', encoding='utf-8') as outfile:
#             json.dump(saveObj, outfile, indent=4, ensure_ascii=False)

#         if self.currentTerm is None:
#             logger.log("All terms finished")
#         else:
#             logger.log("Term: " + logger.highlight(self.currentTerm))
#             allTerms = saveObj["terms"]
#             self.progressString = str(allTerms.index(self.currentTerm)+1) + "/" + str(len(allTerms))

#     def __createNewSaveFile(self):
#         logger.log("Creating save file")
#         fileName = Helpers.getWithExtension("steamTags", miraSettings.TERMS_EXTENSION())
#         fullPath = miraSettings.TERMS_DIR() + "/" + str(fileName)
#         termsList = []
#         if path.exists(fullPath):
#             with open(fullPath, encoding='utf-8') as f:
#                 for line in f:
#                     if not line.startswith("#"):
#                         term = line.replace("\n", "")
#                         if term not in termsList:
#                             termsList.append(term)
#         data = {}
#         data["terms"] = termsList
#         firstTerm = termsList[0]
#         data["working"] = { "term" : firstTerm }
#         self.currentTerm = firstTerm
#         with open(self.path, 'w', encoding='utf-8') as outfile:
#             json.dump(data, outfile, indent=4, ensure_ascii=False)

#         return data

# #####################################################################

# if __name__ == '__main__':
#     me = singleton.SingleInstance()

#     logger = Helpers.Logger("Mira ", Helpers.miraLogColor)
#     logger.log("Starting")
