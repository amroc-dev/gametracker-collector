#######################################################################
# Collector
# Process to run Mira, Rigel and Mongo in same terminal
#######################################################################

import os
import os.path
from os import path
import time
import sys
from tendo import singleton
import Helpers
from subprocess import Popen
import colored
import pymongo
from pymongo import MongoClient
from Mongo import Mongo
from Mira import Mira
from Rigel import Rigel
from Shared import settings
import numpy

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
 
    def start(self):
        self.collecterStartTime = time.time()
        self.lastLogTime = self.collecterStartTime

        self.mongo = Mongo()
        self.mira = Mira()
        self.rigel = Rigel(self.mongo)
       
        self.setCurrentTerm("Indie")
        
        while True :
            self.update()

    def setCurrentTerm(self, term):
        self.logger.log("Term: " + term)
        self.currentTerm = term
        self.rigel.clear()
        self.mira.setTerm(self.currentTerm)

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

        self.updateLogTime()

    def updateLogTime(self):
        self.currentTime = time.time()
        lastDiff = self.currentTime - self.lastLogTime
        if lastDiff >= settings.collector.uptimeLogInterval:
            totalDiff = self.currentTime - self.collecterStartTime
            hours, rem = divmod(totalDiff, 3600)
            minutes, seconds = divmod(rem, 60)
            self.logger.log("Hrs:{:0>2} Mins:{:0>2} Secs:{:02.0f}".format(int(hours),int(minutes),int(seconds)))
            self.lastLogTime = self.currentTime

if __name__ == '__main__':
    Collector().start()


