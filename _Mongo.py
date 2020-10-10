
import pymongo
from pymongo import MongoClient
from _Shared import settings
import Helpers

class Mongo:
    def __init__(self):
        self.client = None
        self.database = None
        self.collection_games = None
        self.collection_games_meta = None
        self.collection_collector = None
        self.logger = Helpers.Logger("Mongo", Helpers.mongoLogColor)
        self.connect()

    def connect(self):
        self.logger.log("Connecting to database")
        try:
            self.client =  MongoClient(settings.mongo.connectionString)
            self.database = self.client[settings.mongo.databaseName]
            self.collection_games = self.database[settings.mongo.collections.games]
            self.collection_games_meta = self.database[settings.mongo.collections.gamesMeta]
            self.collection_collector = self.database[settings.mongo.collections.collector]
            self.logger.log("Connection Ok")
        except pymongo.errors.PyMongoError as e:
            self.logger.log("Connection Failure: " + str(e))
            return False

        return True