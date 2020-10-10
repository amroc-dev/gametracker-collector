# MetaRanking.py is a ranking caluculated from a combination of:
# The game's popularity (lookupBlob.userRating.ratingCount), and:
# The game's user rating (lookupBlob.userRating.value)
# algorithm from: https://steamdb.info/blog/steamdb-rating/

import math

def calcRanking(appEntry):
    userRatingField = appEntry["lookupBlob"]["userRating"]
    ratingCount = userRatingField["ratingCount"]
    rating = userRatingField["value"]
    normRating = rating / 5.0
    return normRating - (normRating - 0.5) * pow(2, -math.log10(ratingCount + 1))