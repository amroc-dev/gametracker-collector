import os
import os.path
from os import path
import time
import sys
from tendo import singleton
import Helpers
from subprocess import Popen
import colored
from Settings import miraSettings
from Settings import rigelSettings

def deleteSaveFiles():
    miraList = os.listdir(miraSettings.OUTPUT_DIR())
    for fileName in miraList:
        os.remove(miraSettings.OUTPUT_DIR() + "/" + fileName)

    rigelList = os.listdir(rigelSettings.OUTPUT_DIR())
    for fileName in rigelList:
        os.remove(rigelSettings.OUTPUT_DIR() + "/" + fileName)

if __name__ == '__main__':
    logger = Helpers.Logger("Collector", "chartreuse_2a")
    me = singleton.SingleInstance()

    mira = None
    rigel = None
    mongo = None

    print("")

    if len(sys.argv) > 1:
        if sys.argv[1].startswith("x") or sys.argv[1].startswith("-x"):
            logger.log("Deleting save files")
            deleteSaveFiles()

    elapsedTimeUpdateCount = 4

    startTime = time.time()

    sleeper = Helpers.Sleeper(5)
 
    proxyList = [None]
    # proxyList.append('socks5://dsoKEQ:R8bc7p@196.17.169.196:8000')
    # proxyList.append('socks5://dsoKEQ:R8bc7p@196.17.168.237:8000')
    # proxyList.append('socks5://marco.mazzoli@gmail.com:nQazse76@uk751.nordvpn.com:1080')

    count = 1
    for proxy in proxyList:
        processName = "Mira " + str(count)
        if proxy is None:
            Popen(["Python3", "Mira.py", str(processName)])
            time.sleep(0.1)
        else:
            Popen(["Python3", "Mira.py", str(processName), str(proxy)])
        count += 1

    while True:
        elapsedTimeUpdateCount += 1
        if elapsedTimeUpdateCount >= 3:
            elapsedTimeUpdateCount = 0
            diff = time.time() - startTime
            hours, rem = divmod(diff, 3600)
            minutes, seconds = divmod(rem, 60)
            logger.log("Hrs:{:0>2} Mins:{:0>2} Secs:{:02.0f}".format(int(hours),int(minutes),int(seconds)))

        # if mira == None or mira.poll() is not None:
        #     mira = Popen(["Python3", "Mira.py"])

        if rigel == None or rigel.poll() is not None:
            rigel = Popen(["Python3", "Rigel.py"])

        if mongo == None or mongo.poll() is not None:
            mongo = Popen(["Python3", "Mongo.py"])
        
        sleeper.sleepIfNecessary()

