#######################################################################
# Mongo Ops
# Just a collection of tests/useful database operations
#######################################################################

from pymongo import TEXT

from Mongo import Mongo
from Shared import settings

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
            ("searchBlob.sellerName", TEXT),
            ("tags", TEXT)
        ],
        weights={
            "trackName": 2,
            "searchBlob.sellerName": 2,
            "tags": 1
        },
        name=indexName)

def setupDeviceIndex(indexName):
    mongo.collection_games.create_index("lookupBlob.deviceFamilies", name=indexName)

def setupReleaseDateIndex(indexName):
    mongo.collection_games.create_index("lookupBlob.releaseDate", name=indexName)

def setupPriceIndex(indexName):
    mongo.collection_games.create_index("searchBlob.price", name=indexName)

def setupPopularityIndex(indexName):
    mongo.collection_games.create_index("lookupBlob.userRating.ratingCount", name=indexName)

def setupMetaRankingIndex(indexName):
    mongo.collection_games.create_index("metaRanking", name=indexName)

if __name__ == '__main__':
    mongo = Mongo("MongoSetupIndexes")

    # array of creation functions, in a tuple with the name of the index
    indexNames = settings.mongo.indexNames.games
    creationFuncs = [
        (indexNames.text, setupTextIndexes),
        (indexNames.deviceFamilies, setupDeviceIndex),
        (indexNames.releaseDate, setupReleaseDateIndex),
        (indexNames.price, setupPriceIndex),
        (indexNames.popularity, setupPopularityIndex),
        (indexNames.metaRanking, setupMetaRankingIndex),
    ]

    indexes = mongo.collection_games.index_information()

    # # delete all indexes
    # for func in creationFuncs:
    #     if func[0] in indexes.keys():
    #         logger.log("Deleting index: " + func[0])
    #         mongo.collection_games.drop_index(func[0])

    ## create all indexes if they don't already exist
    for func in creationFuncs:
        setup(indexes, func[0], func[1])