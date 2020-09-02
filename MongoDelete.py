import sys
import pymongo
from pymongo import MongoClient
from Settings import mongoSettings

if __name__ == '__main__':
    print("Connecting to database")

    client = None
    database = None
    collection = None

    try:
        client = MongoClient(mongoSettings.CONNECTION_STRING())
        database = client[mongoSettings.DATABASE_NAME()]
        collection = database[mongoSettings.COLLECTION_NAME()]
        print("Connection Ok")
    except pymongo.errors.PyMongoError as e:
        print("Connection Failure: " + str(e))
        sys.exit(1)

    val = input("Delete entire collection? -> " + mongoSettings.COLLECTION_NAME() + " (type YES): ")
    if str(val).lower() == "yes":
        collection.delete_many({})
        print("Delete successful")
    else:
        print("Cancelled") 

    sys.exit(1)
