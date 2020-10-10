#######################################################################
# UploadTerms
# Upload search terms to the database for the collector to use
#######################################################################

import os
import os.path
from os import path
import Helpers
from Mongo import Mongo
from Shared import settings

if __name__ == '__main__':
    mongo = Mongo()

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

    results = mongo.collection_collector.update_one( 
        {'_id': settings.collector.db_keys.collectorId}, 
        {'$set': {settings.collector.db_keys.terms : termsList}}, 
        upsert=True
    )

    if results.acknowledged:
        mongo.logger.log("Done")


