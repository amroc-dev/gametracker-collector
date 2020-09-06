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
from Settings import miraSettings
from nested_lookup import nested_lookup
from tendo import singleton
import colored
import random
import Helpers
import tldextract
from filelock import Timeout, FileLock

#######################################################################åå

class Mira:
    def __init__(self):
        self.prepareForNewTerm()
        self.matchedResults = []
        self.sleeper = Helpers.Sleeper(miraSettings.MIN_SEARCH_TIME())

    def matchedResultInBuffer(self, match):
        trackID = match[miraSettings.KEY_trackId()]
        inBuffer = False
        for existingMatch in self.matchedResults:
            if trackID == existingMatch[miraSettings.KEY_trackId()]:
                inBuffer = True
                break
        
        return inBuffer

    def addMatchedResult(self, newMatch):
        if self.matchedResultInBuffer(newMatch) == False:
            self.matchedResults.append(newMatch)

        if len(self.matchedResults) == miraSettings.RESULTS_FILE_DUMP_COUNT():
             self.dumpResults()

    def moveToNextTerm(self):
        self.dumpResults()
        self.prepareForNewTerm()
        saveFile.update()
        if saveFile.currentTerm == None:
            return False
        return True

    def prepareForNewTerm(self):
        self.exhaustedSearchCount = miraSettings.EXHAUSTED_SEARCH_COUNT()
        self.offset = 0

    def run(self):
        self.prepareForNewTerm()
        while True:
            if self.doSearch() == False:
                self.moveToNextTerm()
            if saveFile.currentTerm == None:
                break

    # check there aren't too many output files waiting to be processed by Rigel (unlikely)
    def waitForRigelIfNecessary(self):
        while True:
            count = 0
            fileNameList = os.listdir(miraSettings.OUTPUT_DIR())
            for fileName in fileNameList:
                if fileName.startswith(miraSettings.RESULTS_FILENAME()):
                    count +=1

            if count >= miraSettings.MAX_DUMPED_FILE_COUNT():
                logger.log("Waiting for Rigel to catch up...")
                time.sleep(miraSettings.MIN_SEARCH_TIME())
            else:
                break

    def dumpResults(self):
        if len(self.matchedResults) == 0:
            return False

        self.waitForRigelIfNecessary()

        data = {}
        data[miraSettings.MIRA_KEY_term()] = saveFile.currentTerm
        data[miraSettings.MIRA_KEY_appleSearchBlobs()] = self.matchedResults

        uniqueID = str(uuid.uuid1().hex)
        tempPath = miraSettings.OUTPUT_DIR() + "/" + miraSettings.RESULTS_TEMP_FILENAME() + "_" + uniqueID + miraSettings.RESULTS_FILENAME_EXTENSION()
        with open(tempPath, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=4, ensure_ascii=False)

        fileName = miraSettings.RESULTS_FILENAME() + "_" + uniqueID + miraSettings.RESULTS_FILENAME_EXTENSION()
        os.rename(tempPath, miraSettings.OUTPUT_DIR() + "/" + fileName)
        # logger.log("*File dump*")#: " + fileName)

        self.matchedResults.clear()

    def doSearch(self):
        if saveFile.currentTerm == None:
            return False

        searchURL = miraSettings.searchURL_base().replace("__TERM__", str(saveFile.currentTerm), 1)
        searchURL = searchURL.replace("__LIMIT__", str(miraSettings.LIMIT()), 1)
        searchURL = searchURL.replace("__OFFSET__", str(self.offset), 1)

        itunesSearchLogString = " iTunes search... term:" + logger.highlight(saveFile.currentTerm) + " " + saveFile.getTermProgressString(saveFile.currentTerm) + ", offset:" + str(self.offset)
        logger.log(itunesSearchLogString)
        proxyDomainName = "None"
        if proxyServer is not None:
            domainExt = tldextract.extract(proxyServer)
            if len(domainExt.registered_domain) > 0:
                proxyDomainName = domainExt.subdomain + "." + domainExt.registered_domain
            else:
                proxyDomainName = domainExt.ipv4
        logger.log("Proxy: " + colored.fg('white') + proxyDomainName)

        self.sleeper.sleepIfNecessary(logger, "Searching")    

        try:
            response = requests.get(searchURL, proxies = None if proxyServer is None else {'https': proxyServer})
        except requests.exceptions.RequestException as e:
            logger.log("Request exception: ")
            print(str(e))
            return True 

        if response.ok:
            try:
                jsonResponse = response.json()
            except json.decoder.JSONDecodeError as e:
                logger.log("JSON decode error: ")
                print(str(e))
                return True
                
            resultCount = jsonResponse[miraSettings.KEY_resultCount()] 
            results = jsonResponse[miraSettings.KEY_results()]

            logger.log("Results: " + str(resultCount))

            if resultCount < miraSettings.MIN_RESULTS():
                logger.log("Too few results (<" + str(miraSettings.MIN_RESULTS()) + "), moving on...")
                return False

            matchedResults = []
            for result in results:
                self.offset += 1

                # check and discard non paid games
                formattedPrice = nested_lookup(key = 'price', document = result)
                if len(formattedPrice) == 0 or float(formattedPrice[0]) == 0:
                    continue

                # check and discard games that don't meet the minimum number of ratings requirement (check for key as some old apps appear to not have this data)
                if miraSettings.KEY_userRatingCount() in result:
                    if result[miraSettings.KEY_userRatingCount()] < miraSettings.MIN_RATINGS():
                        continue

                matchedResults.append(result)
            
            # check and report if app is new, ie it hasn't already been picked up in the search since the last file dump
            addedAppsCount = 0
            for match in matchedResults:
                if not self.matchedResultInBuffer(match):
                    addedAppsCount += 1

            logger.log("Matches: " + str(addedAppsCount))
            
            if addedAppsCount == 0:
                if self.exhaustedSearchCount > 0:
                    self.exhaustedSearchCount -= 1
                norm = 1 - (float(self.exhaustedSearchCount) / miraSettings.EXHAUSTED_SEARCH_COUNT())
                logger.log("Exhaust progress: " +  Helpers.makeProgressBar(norm, miraSettings.EXHAUSTED_SEARCH_COUNT()))
            else:
                self.exhaustedSearchCount = miraSettings.EXHAUSTED_SEARCH_COUNT()
                progressNorm = float(len(self.matchedResults) + addedAppsCount) / float(miraSettings.RESULTS_FILE_DUMP_COUNT())
                if progressNorm > 1:
                    progressNorm = 1
                logger.log("Buffer: " + Helpers.makeProgressBar(progressNorm, miraSettings.RESULTS_FILE_DUMP_COUNT()))

            for match in matchedResults:
                self.addMatchedResult(match)
        else:
            logger.log("Search request failed with status code:" + str(response.status_code))

        if self.exhaustedSearchCount == 0:
            logger.log("Search term exhaust limit reached")
            return False
            
        return True

#######################################################################

class SaveFile:
    def __init__(self):
        self.path = miraSettings.OUTPUT_DIR() + "/" + miraSettings.SAVE_FILENAME()
        self.currentTerm = None
        self.update(True)

    def getTermProgressString(self, term):
        return ""

    def update(self, tryResume = False):
        lockFilePath = miraSettings.OUTPUT_DIR() + "/" + miraSettings.LOCK_FILE_NAME()
        lock = FileLock(lockFilePath)
        lock.acquire()
        self.__update(tryResume)
        lock.release()
            
    def __update(self, tryResume = False):
        #first if there's no save file to read, create one
        data = None
        if not path.exists(self.path):
            self.__createNewSaveFile()
        with open(self.path, encoding='utf-8') as json_file:
            data = json.load(json_file)
       
        # if we're trying to resume, find a record of the current worker if there is one and pick up from there
        workers = data["workers"]
        if tryResume:
            if processName in workers:
                logger.log("Resuming work")
                self.__setCurrentTerm(workers[processName], data)
                return

        # if we're not resuming then move to the first unworked term after the latest recorded worked term
        termsList = data["terms"]
        highestWorkedTermIndex = -1
        termsBeingWorked = list(workers.values())
        if len(termsBeingWorked) > 0:
            for workedTerm in termsBeingWorked:
                tIndex = 0
                if workedTerm == None:
                    self.__setCurrentTerm(None, data)
                    return
                for term in termsList:
                    if workedTerm == term:
                        if tIndex > highestWorkedTermIndex:
                            highestWorkedTermIndex = tIndex
                            break
                    tIndex += 1
        
        nextTermIndex = 0
        if highestWorkedTermIndex > -1:
            nextTermIndex = highestWorkedTermIndex + 1

        if nextTermIndex < len(termsList):
            self.__setCurrentTerm(termsList[nextTermIndex], data)
        else:
            self.__setCurrentTerm(None, data)

    def __setCurrentTerm(self, term, fileData):
        self.currentTerm = term
        workers = fileData["workers"]
        if term is None:
            workers[processName] = None
        else:
            workers[processName] = term

        with open(self.path, 'w', encoding='utf-8') as outfile:
            json.dump(fileData, outfile, indent=4, ensure_ascii=False)

        if term is None:   
            logger.log("All terms finished")
        else:
            logger.log("Term: " + logger.highlight(self.currentTerm))

    def __createNewSaveFile(self):
        logger.log("Creating save file")
        fileName = Helpers.getWithExtension("steamTags", miraSettings.TERMS_EXTENSION())
        fullPath = miraSettings.TERMS_DIR() + "/" + str(fileName)
        termsList = []
        if path.exists(fullPath):
            with open(fullPath, encoding='utf-8') as f:
                for line in f:
                    if not line.startswith("#"):
                        term = line.replace("\n", "")
                        if term not in termsList:
                            termsList.append(term)
            # logger.log("Using terms: " + fileName)

        data = {}
        data["terms"] = termsList
        data["workers"] = {}
        workers = data["workers"]
        with open(self.path, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=4, ensure_ascii=False)

        return data

#####################################################################

if __name__ == '__main__':
    processName = miraSettings.PROCESS_NAME()
    proxyServer = None
    if len(sys.argv) > 1:
        processName = sys.argv[1]
        if len(sys.argv) > 2:
            proxyServer = sys.argv[2]
    else:
        try:
            me = singleton.SingleInstance()
        except singleton.SingleInstanceException as e:
            sys.exit(1)

    logger = Helpers.Logger(processName, Helpers.miraLogColor)
    logger.log("Starting")

    if not os.path.exists(miraSettings.TERMS_DIR()):
        os.makedirs(miraSettings.TERMS_DIR())

    if not os.path.exists(miraSettings.OUTPUT_DIR()):
         os.makedirs(miraSettings.OUTPUT_DIR())

    saveFile = SaveFile()
    if saveFile.currentTerm != None:
        Mira().run()







# #######################################################################

# class TermsFile:
#     def __init__(self):
#         self.fileName = None
#         self.terms = []
#         self.currentTermIndex = 0

#     def load(self, fileName):
#         fullPath = miraSettings.TERMS_DIR() + "/" + str(fileName)
#         if path.exists(fullPath):
#             self.terms.clear()
#             with open(fullPath, encoding='utf-8') as f:
#                 for line in f:
#                     if not line.startswith("#"):
#                         self.terms.append(line.replace("\n", ""))
#             self.currentTermIndex = 0
#             self.fileName = fileName
#             logger.log("Using terms: " + fileName)
#             return True
#         return False

#     def seekTerm(self, term):
#         index = 0
#         for t in self.terms:
#             if t == term:
#                 self.currentTermIndex = index
#                 break
#             index = index+1

#     def getTermProgressString(self, term):
#         num = 1
#         termFound = False
#         for t in self.terms:
#             if (t == term):
#                 termFound = True
#                 break
#             num += 1

#         if termFound:
#             return ("(" + str(num) + "/" + str(len(self.terms)) + ")")
#         return ("(?/" + str(len(self.terms)) + ")")

#     def hasReachedEnd(self):
#         return self.currentTermIndex >= len(self.terms)

#     def moveToNextTerm(self):
#         self.currentTermIndex = self.currentTermIndex + 1
#         if not self.hasReachedEnd():
#             logger.log(logger.highlight("New term:" + self.getCurrentTerm()))

#     def getCurrentTerm(self):
#         if self.currentTermIndex < len(self.terms):
#             return self.terms[self.currentTermIndex]
#         else:
#             return ""