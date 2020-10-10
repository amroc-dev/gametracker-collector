# import os
# import os.path
# from os import path
import time
import sys
# import requests
# import json
# import pymongo
# from pymongo import MongoClient
# import bson
# from pprint import pprint
# from tendo import singleton
import colored

coolUTF8 = "⚡⭐🌀💎💥"

class Logger:
    def __init__(self, header, color):
        self.header = header
        self.color = color

    def log(self, body):
        print(colored.fg(self.color) + self.header + "   \t" + body + colored.attr('reset'))

    def highlight(self, str):
        return (colored.attr('underlined') + str + colored.attr('res_underlined'))

class Sleeper:
    def __init__(self, sleepTime):
        self.sleepTime = sleepTime
        self.sleepTimer = 0

    def sleepIfNecessary(self, logger = None, msg = ""):
        timeToSleep = self.sleepTime - (time.time() - self.sleepTimer)
        if timeToSleep > 0:
            if logger:
                logger.log(msg + " in" + " {:.1f}".format(timeToSleep) + "s" + "...")
            time.sleep(timeToSleep)
        self.sleepTimer = time.time()

def getWithExtension(fileName, extension):
    dotExt = "." + extension
    if not fileName.endswith(dotExt):
        return fileName + dotExt
    else:
        return fileName

def makeProgressBar(val, pips = 20):
    barFill = "▰"
    barEmpty = "-"
    bar = ""
    for x in range(0, pips):
        if x >= val:
            bar = bar + barEmpty
        else:
            bar = bar + barFill
    return bar


miraLogColor = "cyan_1"
rigelLogColor = "orange_1"
mongoLogColor = "light_magenta"
mongoValidatorLogColor = "chartreuse_1"

