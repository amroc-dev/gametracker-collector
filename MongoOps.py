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

if __name__ == '__main__':

    print(str(sys.argv))

    for arg in sys.argv:
        if arg.lower() == "-cleartest":
            mongo = Mongo("MongoOps")
            mongo.connect_test()
            mongo.logger.log("Clearing test collections...")
            mongo.collection_games.delete_many({})
            mongo.collection_games_meta.delete_many({})
            mongo.collection_collector.delete_many({})
            mongo.logger.log("Done...")
            sys.exit(1)

        if arg.lower() == "-cleartest_collector":
            mongo = Mongo("MongoOps")
            mongo.connect_test()
            mongo.logger.log("Clearing test collection: Collector")
            mongo.collection_collector.delete_many({})
            mongo.logger.log("Done...")
            sys.exit(1)

        if arg.lower() == "-cleartest_games":
            mongo = Mongo("MongoOps")
            mongo.connect_test()
            mongo.logger.log("Clearing test collection: Games")
            mongo.collection_games.delete_many({})
            mongo.logger.log("Done...")
            sys.exit(1)

        if arg.lower() == "-cleartest_games_meta":
            mongo = Mongo("MongoOps")
            mongo.connect_test()
            mongo.logger.log("Clearing test collection: Games_meta")
            mongo.collection_games_meta.delete_many({})
            mongo.logger.log("Done...")
            sys.exit(1)
    
    print("No args... exiting")



