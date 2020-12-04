#######################################################################
# Mongo Ops
# Just a collection of tests/useful database operations
#######################################################################

import sys
from pymongo import TEXT

from Mongo import Mongo
from Shared import settings, hasTestArgs

def setup(indexes, indexName, createFunc):
    if indexName in indexes.keys():
        mongo.logger.log("Index exists: " + indexName)
        return False
    else:
        mongo.logger.log("Creating index: " + indexName)
        createFunc(indexName)
        return True

def setupTextIndexes(indexName):
    mongo.collection_games.create_index( 
        [
            ("trackName", TEXT), 
            ("searchBlob.artistName", TEXT),
            ("tags", TEXT)
        ],
        weights={
            "trackName": 2,
            "searchBlob.artistName": 2,
            "tags": 1
        },
        name=indexName)

def setupPopularity(indexName):
    mongo.collection_games.create_index("lookupBlob.userRating.ratingCount", name=indexName)

def setupRatingCountCurrentVersion(indexName):
    mongo.collection_games.create_index("lookupBlob.userRating.ratingCountCurrentVersion", name=indexName)

def setupRatingCurrentVersion(indexName):
    mongo.collection_games.create_index("searchBlob.averageUserRatingForCurrentVersion", name=indexName)

def setupReleaseDate(indexName):
    mongo.collection_games.create_index("searchBlob.releaseDate", name=indexName)

def setupCurrentVersionReleaseDate(indexName):
    mongo.collection_games.create_index("searchBlob.currentVersionReleaseDate", name=indexName)

def setupDevice(indexName):
    mongo.collection_games.create_index("lookupBlob.deviceFamilies", name=indexName)

# def setupPriceIndex(indexName):
#     mongo.collection_games.create_index("searchBlob.price", name=indexName)

def setupMetaRanking(indexName):
    mongo.collection_games.create_index("metaRanking", name=indexName)

if __name__ == '__main__':
    mongo = Mongo("MongoSetupIndexes")
    mongo.connect(hasTestArgs(sys.argv))

    # array of creation functions, in a tuple with the name of the index
    indexNames = settings.mongo.indexNames.games
    creationFuncs = [
        (indexNames.text, setupTextIndexes),
        (indexNames.deviceFamilies, setupDevice),
        (indexNames.releaseDate, setupReleaseDate),
        (indexNames.currentVersionReleaseDate, setupCurrentVersionReleaseDate),
        # (indexNames.price, setupPriceIndex),
        (indexNames.popularity, setupPopularity),
        (indexNames.ratingCountCurrentVersion, setupRatingCountCurrentVersion),
        (indexNames.metaRanking, setupMetaRanking),
    ]

    indexes = mongo.collection_games.index_information()

    # # delete all indexes
    # for func in creationFuncs:
    #     if func[0] in indexes.keys():
    #         mongo.logger.log("Deleting index: " + func[0])
    #         mongo.collection_games.drop_index(func[0])

    ## create all indexes if they don't already exist
    for func in creationFuncs:
        setup(indexes, func[0], func[1])