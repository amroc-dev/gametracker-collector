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
        self.mongo.connect()
        self.mira = Mira()
        self.rigel = Rigel(self.mongo)
        self.currentTerm = "Indie"
        self.mira.setTerm(self.currentTerm)

        while True :
            self.update()

    def update(self):
        self.miraSleeper.sleepIfNecessary()
        self.mira.update()

        self.checkDumpToRigel()

        self.rigelSleeper.sleepIfNecessary()
        self.rigel.update(self.currentTerm)

        self.updateLogTime()

    def checkDumpToRigel(self):
        results = self.mira.getMiraResults()
        if results is not None:
            self.rigel.addMiraResults(results)

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


