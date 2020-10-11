#######################################################################
# Mira
# Step 1 in Mira -> Rigel -> Mongo chain
# Traverses through all specified search term, and uses Apple search API to return matches
# results are saved to Mira_OUT folder
#######################################################################

import sys
import json
import requests
from nested_lookup import nested_lookup

import Helpers
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
        self.exhaustedSearchCount = 0
        self.searchOngoing = False

    def setTerm(self, term):
        if len(self.miraResults) > 0:
            self.logger.log(
                "Warning, new term started but there are still miraResults left over from previous term, make sure to getMiraResults() first")

        self.miraResults = []
        self.currentTerm = term
        self.offset = 0
        self.exhaustedSearchCount = 0
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
            self.searchOngoing = False

        if self.searchOngoing == False:
            # self.logger.log("Waiting for new term...")
            return

        status = self._update()
        if status == settings.mira.returnCodes.searchCompleted:
            self.logger.log("Search completed")
            self.searchOngoing = False

    def _update(self):
        searchURL = settings.mira.searchURL_base.replace(
            "__TERM__", str(self.currentTerm), 1)
        searchURL = searchURL.replace("__LIMIT__", str(settings.mira.limit), 1)
        searchURL = searchURL.replace("__OFFSET__", str(self.offset), 1)

        itunesSearchLogString = " search: term:" + \
            self.logger.highlight(self.currentTerm) + \
            ", offset:" + str(self.offset)
        self.logger.log(itunesSearchLogString)

        try:
            response = requests.get(searchURL, proxies=None, timeout=10)
        except requests.exceptions.RequestException as e:
            self.logger.log("Request exception: " + str(e))
            return

        if response.ok:
            try:
                jsonResponse = response.json()
            except json.decoder.JSONDecodeError as e:
                self.logger.log("JSON decode error: " + str(e))
                return

            resultCount = jsonResponse[settings.mira.api_keys.resultCount]
            results = jsonResponse[settings.mira.api_keys.results]
            # self.logger.log("Results: " + str(resultCount))

            if resultCount < settings.mira.minResults:
                self.logger.log(
                    "Too few results (<" + str(settings.mira.minResults) + "), giving up")
                return settings.mira.returnCodes.searchCompleted

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
                self.exhaustedSearchCount += 1
                self.logger.log(
                    "No new matches, exhaust progress: " + Helpers.makeProgressBar(self.exhaustedSearchCount, settings.mira.exhaustedSearchCount))
            else:
                self.exhaustedSearchCount = 0
                for match in matchedResults:
                    self.miraResults.append(MiraResult(match))
                # self.logger.log("Buffer size: " + str(len(self.miraResults)))
        else:
            self.logger.log(
                "Search request failed with status code:" + str(response.status_code))

        if self.exhaustedSearchCount == settings.mira.exhaustedSearchCount:
            self.logger.log("Exhaust limit reached")
            return settings.mira.returnCodes.searchCompleted
