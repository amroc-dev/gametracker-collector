import time
import sys
import colored

coolUTF8 = "⚡⭐🌀💎💥"

class Logger:
    useColor = True
    spacing = 12

    def __init__(self, header, color):
        self.header = (header[:self.spacing-3] + '..') if len(header) > self.spacing-3 else header
        self.color = color
        self.indent = "".ljust(max(0, self.spacing - len(self.header)) )

    def log(self, body):
        if Logger.useColor:
            print(colored.fg(self.color) + self.header + self.indent + body + colored.attr('reset'))
        else:
            print(self.header + self.indent + body)

    def highlight(self, str):
        if Logger.useColor:
            return (colored.attr('underlined') + str + colored.attr('res_underlined'))
        else:
            return str

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

def objectKeyFromDotString( obj, key ):
    parts = key.split( "." )
    prop = obj
    for i in range(0, len(parts)):
        prop = prop[parts[i]];
    return prop;

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

