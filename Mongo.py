#######################################################################
# Mongo
# Class to connect to database and collections
#######################################################################

import pymongo
from pymongo import MongoClient

from Shared import settings
import Helpers

class Mongo:
    def __init__(self, nameOverride="Mongo"):
        self.client = None
        self.database = None
        self.collection_games = None
        self.collection_games_meta = None
        self.collection_collector = None
        self.logger = Helpers.Logger(nameOverride, Helpers.mongoLogColor)

    def connect_test(self):
        self.connect(True)

    def connect(self, useTestingCollections = False):
        testString = "test" if useTestingCollections else "live"
        self.logger.log("Connecting to " + testString + " database")
        try:
            self.client =  MongoClient(settings.mongo.connectionString)
            self.database = self.client[settings.mongo.databaseName]

            testPrefix = settings.mongo.collections.testingPrefix if useTestingCollections else ""

            self.collection_games = self.database[testPrefix + settings.mongo.collections.games]
            self.collection_games_meta = self.database[testPrefix + settings.mongo.collections.gamesMeta]
            self.collection_collector = self.database[testPrefix + settings.mongo.collections.collector]

            self.logger.log("Connection Ok")
        except pymongo.errors.PyMongoError as e:
            self.logger.log("Connection Failure: " + str(e))
            return False

        return True