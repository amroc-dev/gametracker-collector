#######################################################################
# Collector
# Process to run Mira, Rigel and Mongo in same terminal
#######################################################################

import sys
import time
from Mongo import Mongo

from Mira import Mira
from Rigel import Rigel
from Shared import settings, hasTestArgs
import Helpers
from GameValidator import GameValidator
from UpdateGamesMeta import UpdateGamesMeta

class Collector_MongoOps:

    @staticmethod
    def setCurrentTerm(mongo, term):
        mongo.collection_collector.update_one(
            {'_id': settings.collector.db_keys.collectorId},
            {'$set': {settings.collector.db_keys.currentTerm: term}},
            upsert=True)

    @staticmethod
    def getCurrentTerm(mongo):
        result = mongo.collection_collector.find_one({'_id': settings.collector.db_keys.collectorId})
        currentTerm = None
        if result is not None and settings.collector.db_keys.currentTerm in result:
            currentTerm = result[settings.collector.db_keys.currentTerm]
        return currentTerm

    @staticmethod
    def getTerms(mongo):
        result = mongo.collection_collector.find_one({'_id': settings.collector.db_keys.collectorId})
        terms = []
        if result is not None and settings.collector.db_keys.terms in result:
            terms = result[settings.collector.db_keys.terms]
        return terms


class Collector:
    def __init__(self):
        self.logger = Helpers.Logger("Collector", "chartreuse_2a")
        self.mongo = None
        self.mira = None
        self.rigel = None
        self.mongo = None
        self.miraSleeper = Helpers.Sleeper(settings.mira.searchWaitInterval)
        self.rigelSleeper = Helpers.Sleeper(settings.rigel.searchWaitInterval)
        self.collecterStartTime = 0
        self.lastLogTime = 0
        self.currentTerm = None

    def start(self, useTestDatabaseCollections=False):
        self.collecterStartTime = time.time()
        self.lastLogTime = self.collecterStartTime

        self.mongo = Mongo()
        self.mongo.connect(useTestDatabaseCollections)
        self.mira = Mira()
        self.rigel = Rigel(self.mongo)

        terms = Collector_MongoOps.getTerms(self.mongo)
        if len(terms) == 0:
            self.logger.log("No search terms in the database")
            sys.exit(1)

        currentTerm = Collector_MongoOps.getCurrentTerm(self.mongo)

        if currentTerm in terms:
            self.logger.log("Resuming...")
        else:
            self.logger.log("Starting from the beginning")
            currentTerm = terms[0]

        self.setCurrentTerm(currentTerm)

        while True:
            running = self.update()
            if running == False:
                self.logger.log("All terms finished")

                # after all terms complete, run some meta data operations
                GameValidator(self.mongo).start()
                UpdateGamesMeta(self.mongo).start()

                self.logger.log("Restarting")
                self.setCurrentTerm(terms[0])

    def setCurrentTerm(self, term):
        self.logger.log("Term: " + term)
        self.currentTerm = term
        Collector_MongoOps.setCurrentTerm(self.mongo, self.currentTerm)
        self.rigel.clear()
        self.mira.setTerm(self.currentTerm)

    def getNextTerm(self):
        terms = Collector_MongoOps.getTerms(self.mongo)
        i = 0
        for term in terms:
            if term == self.currentTerm:
                if (i+1) < len(terms):
                    return terms[i+1]
                else:
                    return None
            i = i+1

        return None

    def update(self):
        self.miraSleeper.sleepIfNecessary()
        self.mira.update()

        miraResults = self.mira.getMiraResults()
        if miraResults is not None:
            self.rigel.addMiraResults(miraResults)

        self.rigelSleeper.sleepIfNecessary()
        rigelStatus = self.rigel.update(self.currentTerm)

        # for all other others, keep retrying.
        # But if there is a database error then mira and rigel data will have been lost, so just the current term until
        # the database succeeds again
        if rigelStatus == settings.rigel.returnCodes.mongoWriteFail:
            self.setCurrentTerm(self.currentTerm)
        else:
            if not self.mira.searchOngoing and self.rigel.isEmpty():
                self.logger.log("Term complete")
                nextTerm = self.getNextTerm()
                if nextTerm is None:
                    Collector_MongoOps.setCurrentTerm(self.mongo, None)
                    return False
                self.setCurrentTerm(nextTerm)

        self.updateLogTime()
        return True

    def updateLogTime(self):
        self.currentTime = time.time()
        lastDiff = self.currentTime - self.lastLogTime
        if lastDiff >= settings.collector.uptimeLogInterval:
            totalDiff = self.currentTime - self.collecterStartTime
            hours, rem = divmod(totalDiff, 3600)
            minutes, seconds = divmod(rem, 60)
            self.logger.log("{:0>2}:{:0>2}:{:02.0f}".format(
                int(hours), int(minutes), int(seconds)))
            self.lastLogTime = self.currentTime


if __name__ == '__main__':

    for arg in sys.argv:
        if arg.lower() == "-nocolor":
            Helpers.Logger.useColor = False

    Collector().start(hasTestArgs(sys.argv))
