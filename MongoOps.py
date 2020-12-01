#######################################################################
# MongoOps
# Miscellaneous useful database operations called from the command line
#######################################################################


import sys
import pymongo
import click
from os import path

from Mongo import Mongo
import Helpers
from Helpers import objectKeyFromDotString
from Shared import settings, hasTestArgs
from Rigel import calcMetaRanking

def clearAll(mongo):
    mongo.logger.log("Clearing all collections ...")
    mongo.collection_games.delete_many({})
    mongo.collection_games_meta.delete_many({})
    mongo.collection_collector.delete_many({})
    mongo.logger.log("Done.")

def clearCollector(mongo):
    mongo.logger.log("Clearing: Collector ...")
    mongo.collection_collector.delete_many({})
    mongo.logger.log("Done.")

def clearGames(mongo):
    mongo.logger.log("Clearing: Games ...")
    mongo.collection_games.delete_many({})
    mongo.logger.log("Done.")

def clearGames_meta(mongo):
    mongo.logger.log("Clearing: Games_meta ...")
    mongo.collection_games_meta.delete_many({})
    mongo.logger.log("Done.")

def updateMetaRankings(mongo):
    mongo.logger.log("Updating meta rankings...")
    ratingCountCurrentVersion_field = 'lookupBlob.' + settings.rigel.db_keys.ratingCountCurrentVersion
    ratingCurrentVersion_field = 'searchBlob.' + settings.rigel.db_keys.ratingCurrentVersion
    results = mongo.collection_games.find({}, projection={ratingCountCurrentVersion_field: True, ratingCurrentVersion_field: True})

    bulkUpdates = []

    for result in results:
        ratingCountCurrentVersion = objectKeyFromDotString(result, ratingCountCurrentVersion_field)
        ratingCurrentVersion = objectKeyFromDotString(result, ratingCurrentVersion_field)
        metaRanking = calcMetaRanking(ratingCountCurrentVersion, ratingCurrentVersion)
        bulkUpdates.append(pymongo.UpdateOne({'_id': result['_id']}, {'$set' : {settings.rigel.db_keys.metaRanking: metaRanking}}, upsert=True))

    updateResults = mongo.collection_games.bulk_write(bulkUpdates)
    mongo.logger.log("Updated: " + str(updateResults.modified_count))

# def clonegames():
#     cleartest_games()
#     cleartest_games_meta()
#     mongo = Mongo("MongoOps")
#     mongo.connect()
#     mongo.logger.log("Copying games collection from live to test ...")
#     testGamesCollection = settings.mongo.collections.testingPrefix + settings.mongo.collections.games
#     mongo.collection_games.aggregate([ { '$match': {} }, { '$out': testGamesCollection } ])
#     mongo.logger.log("Done.")

if __name__ == '__main__':

    print(str(sys.argv))

    testDB = False

    if "-t" in sys.argv:
        testDB = True

    mongo = Mongo("MongoOps")
    mongo.connect(testDB)

    if not click.confirm('Continue?', default=True):
        sys.exit(1)
    
    if "-clearAll" in sys.argv:
        clearAll(mongo)
        sys.exit(1)

    if "-clearCollector" in sys.argv:
        clearCollector(mongo)
        sys.exit(1)

    if "-clearGames" in sys.argv:
        clearGames(mongo)
        sys.exit(1)

    if "-clearGames_meta" in sys.argv:
        clearGames_meta(mongo)
        sys.exit(1)
    
    if "-updateMetaRankings" in sys.argv:
        updateMetaRankings(mongo)
        sys.exit(1)

    print("No args... exiting")



