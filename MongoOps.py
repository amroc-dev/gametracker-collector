#######################################################################
# MongoOps
# Miscellaneous useful database operations called from the command line
#######################################################################


import sys
import pymongo
from os import path

from Mongo import Mongo
import Helpers
from Shared import settings, hasTestArgs

def clearTest():
    mongo = Mongo("MongoOps")
    mongo.connect_test()
    mongo.logger.log("Clearing test collections ...")
    mongo.collection_games.delete_many({})
    mongo.collection_games_meta.delete_many({})
    mongo.collection_collector.delete_many({})
    mongo.logger.log("Done.")

def cleartest_collector():
    mongo = Mongo("MongoOps")
    mongo.connect_test()
    mongo.logger.log("Clearing test collection: Collector ...")
    mongo.collection_collector.delete_many({})
    mongo.logger.log("Done.")

def cleartest_games():
    mongo = Mongo("MongoOps")
    mongo.connect_test()
    mongo.logger.log("Clearing test collection: Games ...")
    mongo.collection_games.delete_many({})
    mongo.logger.log("Done.")

def cleartest_games_meta():
    mongo = Mongo("MongoOps")
    mongo.connect_test()
    mongo.logger.log("Clearing test collection: Games_meta ...")
    mongo.collection_games_meta.delete_many({})
    mongo.logger.log("Done.")

def clonegames():
    cleartest_games()
    cleartest_games_meta()
    mongo = Mongo("MongoOps")
    mongo.connect()
    mongo.logger.log("Copying games collection from live to test ...")
    testGamesCollection = settings.mongo.collections.testingPrefix + settings.mongo.collections.games
    mongo.collection_games.aggregate([ { '$match': {} }, { '$out': testGamesCollection } ])
    mongo.logger.log("Done.")


if __name__ == '__main__':

    print(str(sys.argv))

    for arg in sys.argv:
        if arg.lower() == "-cleartest":
            clearTest()
            sys.exit(1)

        if arg.lower() == "-cleartest_collector":
            cleartest_collector()
            sys.exit(1)

        if arg.lower() == "-cleartest_games":
            cleartest_games()
            sys.exit(1)

        if arg.lower() == "-cleartest_games_meta":
            cleartest_games_meta()
            sys.exit(1)

        if arg.lower() == "-clonegames":
            clonegames()
            sys.exit(1)

    
    print("No args... exiting")



