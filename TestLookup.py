from os import path
import sys
import json
import requests
from nested_lookup import nested_lookup

import Helpers
from Shared import settings, hasTestArgs

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Please supply app trackId")
        sys.exit(1)

    trackId = sys.argv[1]

    print("Getting lookupBlob")

    try:
        lookupResponse = requests.get(settings.rigel.lookupURL_base.replace("__ID__", trackId, 1), timeout=10)
    except requests.exceptions.RequestException as e:
        print(str(e))
        sys.exit(1)

    if not lookupResponse.ok:
        print("Lookup error")
        sys.exit

    jsonResponse = lookupResponse.json()
    results = jsonResponse[settings.rigel.api_keys.results]

    if not trackId in results:
        print("Not found")
        sys.exit(1)

    lookupBlob = list(results.values())[0]
    trackName = lookupBlob["name"]

    print("Getting searchBlob")

    searchURL = settings.mira.searchURL_base.replace("__TERM__", str(trackName), 1)
    searchURL = searchURL.replace("__LIMIT__", "1", 1)
    searchURL = searchURL.replace("__OFFSET__", "0", 1)

    try:
        searchResponse = requests.get(searchURL, proxies=None, timeout=10)
    except requests.exceptions.RequestException as e:
        print("Request exception: " + str(e))
        sys.exit(1)

    if not searchResponse.ok:
        print("Search error")
        sys.exit(1)

    searchJsonResponse = searchResponse.json()
    resultCount = searchJsonResponse[settings.mira.api_keys.resultCount]
    if not resultCount == 1:
        print("Search results error")
        sys.exit(1)

    searchBlob = searchJsonResponse[settings.mira.api_keys.results][0]

    basePath = "./Test"
    lookupBlobPath = basePath + "/" + trackName + "_lookup.json"
    searchBlobPath = basePath + "/" + trackName + "_search.json"

    print("Saving: " + lookupBlobPath)
    with open(lookupBlobPath, 'w', encoding='utf-8') as outfile:
        json.dump(jsonResponse, outfile, indent=4, ensure_ascii=False)

    print("Saving: " + searchBlobPath)
    with open(searchBlobPath, 'w', encoding='utf-8') as outfile:
        json.dump(searchJsonResponse, outfile, indent=4, ensure_ascii=False)

    print("Done")
