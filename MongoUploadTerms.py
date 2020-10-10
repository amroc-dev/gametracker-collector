#######################################################################
# UploadTerms
# Upload search terms to the database for the collector to use
#######################################################################

import os
import os.path
from os import path
import Helpers
from Mongo import Mongo
import pymongo
from Shared import settings

if __name__ == '__main__':
    mongo = Mongo("MongoUploadTerms")

    fileName = Helpers.getWithExtension("steamTags", settings.collector.termsFileExtension)
    fullPath = settings.collector.termsDir + "/" + str(fileName)
    mongo.logger.log("Uploading file: " + fullPath)
    termsList = []
    if path.exists(fullPath):
        with open(fullPath, encoding='utf-8') as f:
            for line in f:
                if not line.startswith("#"):
                    term = line.replace("\n", "")
                    if term not in termsList:
                        termsList.append(term)

    updates = []

    updates.append(pymongo.UpdateOne(
        {'_id': settings.collector.db_keys.collectorId}, 
        {'$set': {settings.collector.db_keys.terms : termsList}}, 
        upsert=True)
    )

    updates.append(pymongo.UpdateOne(
        {'_id': settings.collector.db_keys.collectorId}, 
        {'$set': {settings.collector.db_keys.currentTerm : ""}}, 
        upsert=True)
    )

    results = mongo.collection_collector.bulk_write(updates)

    if results.acknowledged:
        mongo.logger.log("Done")


