class MiraSettings:
    def PROCESS_NAME(self):
        return "Mira"

    def TERMS_DIR(self):
        return "Terms"

    def TERMS_EXTENSION(self):
        return "terms"

    def OUTPUT_DIR(self):
        return "Out_Mira"

    def LOCK_FILE_NAME(self):
        return "__lock"

    def SAVE_FILENAME(self):
        return "MiraSave.json"

    # how many app entries should be collected before a results file is written
    def RESULTS_FILE_DUMP_COUNT(self):
        return 30

    # if there's this many results files in the directory waiting to be processed by Rigel, then system will wait until it drops below
    def MAX_DUMPED_FILE_COUNT(self):
        return 20

    def RESULTS_TEMP_FILENAME(self):
        return "_MiraResults"

    def RESULTS_FILENAME(self):
        return "MiraResults"

    def RESULTS_FILENAME_EXTENSION(self):
        return ".json"

    # KEY elements are just key identfiers in the apple request API
    def KEY_resultCount(self):
        return "resultCount"

    # KEY_ refer to key names used in the apple API
    def KEY_results(self):
        return "results"

    def KEY_trackViewUrl(self):
        return "trackViewUrl"

    def KEY_trackId(self):
        return "trackId"

    def KEY_userRatingCount(self):
        return "userRatingCount"

    def KEY_formattedPrice(self):
        return "formattedPrice"

    def MIRA_KEY_term(self):
        return "term"

    def MIRA_KEY_appleSearchBlobs(self):
        return "appleSearchBlobs"

    def searchURL_base(self):
        return 'https://itunes.apple.com/search?term=__TERM__&entity=software,iPadSoftware&genreId=6014&limit=__LIMIT__&offset=__OFFSET__'

    # amount of seconds between each main api call (apple specifies that you shouldn't go over 20 a minute)
    def MIN_SEARCH_TIME(self):
        return 6

    # minimum amount of ratings app must have to be considered
    def MIN_RATINGS(self):
        return 0

    # if this many consecutive searches results in no new apps, then move to next term
    def EXHAUSTED_SEARCH_COUNT(self):
        return 10

    # if current search term returns less results than this number, then the next term in the list will be moved to
    def MIN_RESULTS(self):
        return 5

    # how many results to request in one main api call
    def LIMIT(self):
        return 200


miraSettings = MiraSettings()

## ------------------------------------------------------------------------------------------

class RigelSettings:
    def metaLookupURL_base(self):
        return "https://uclient-api.itunes.apple.com/WebObjects/MZStorePlatform.woa/wa/lookup?version=2&id=__ID__&p=mdm-lockup&caller=MDM&platform=enterprisestore&cc=us&l=en"

    # amount of seconds between each main api call (apple specifies that you shouldn't go over 20 a minute)
    def MIN_SEARCH_TIME(self):
        return 5

    def MIRA_OUT_SCAN_TIME(self):
        return 1

    def OUTPUT_DIR(self):
        return "Out_Rigel"

    def RESULTS_TEMP_FILENAME(self):
        return "_RigelResults"

    def RESULTS_FILENAME(self):
        return "RigelResults"

    def RESULTS_FILENAME_EXTENSION(self):
        return miraSettings.RESULTS_FILENAME_EXTENSION()

    def KEY_searchTerm(self):
        return "serchTerm"

    def KEY_searchBlob(self):
        return "searchBlob"

    def KEY_lookupBlob(self):
        return "lookupBlob"

    def KEY_results(self):
        return "results"

    def KEY_id(self):
        return "id"

    def KEY_name(self):
        return "name"

    def KEY_hasInAppPurchases(self):
        return "hasInAppPurchases"

    def KEY_userRating(self):
        return "userRating"

    def KEY_ratingCount(self):
        return "ratingCount"

    def MIN_RATINGS(self):
        return miraSettings.MIN_RATINGS()

    # def KEY_artistName(self):
    #     return "artistName"

    # def KEY_deviceFamilies(self):
    #     return "deviceFamilies"

    # def KEY_releaseDate(self):
    #     return "releaseDate"

    def KEY_trackId(self):
        return miraSettings.KEY_trackId()

    def KEY_trackName(self):
        return "trackName"

    def KEY_genres(self):
        return "genres"

    def KEY_genres_name(self):
        return "name"


    def ignoreGenres(self):
        
        # enter these lower case
        return [
            'entertainment',
            'games',
            'gaming',
        ]

    # def appStoreGameGenres(self):
    #     return (    'action', \
    #                 'adventure', \
    #                 'ar games', \
    #                 'arcade', \
    #                 'board', \
    #                 'card', \
    #                 'casino', \
    #                 'casual', \
    #                 'dice', \
    #                 'education', \
    #                 'family', \
    #                 'music', \
    #                 'puzzle', \
    #                 'racing', \
    #                 'role playing', \
    #                 'simulation', \
    #                 'sports', \
    #                 'strategy', \
    #                 'trivia', \
    #                 'word')


    # GAMEKEY refers to keys used in the output file, and also the database document
    def GAMEKEY_tags(self):
        return "tags"

rigelSettings  = RigelSettings()

## ------------------------------------------------------------------------------------------

class MongoSettings:

    def OUTPUT_SCAN_INTERVAL(self):
        return 1

    def CONNECTION_STRING(self):
        return "mongodb+srv://amroc:mQazse76@cluster0.pddgq.mongodb.net/GameTracker?retryWrites=true&w=majority"

    def DATABASE_NAME(self):
        return "GameTracker"

    def COLLECTION_NAME(self):
        return "Games"

    
    def COLLECTION_META_NAME(self):
        return "Games_meta"

mongoSettings = MongoSettings()

class MongoValidatorSettings:

    def UPDATE_INTERVAL(self):
        return 6

    def LOOKUP_COUNT(self):
        return 200

    def KEY_dateValidated(self):
        return "dateValidated"

mongoValidatorSettings = MongoValidatorSettings()

class MongoIndexNames:
    
    def TEXT_INDEX(self):
        return "trackName_sellerName_tags"

    def DEVICE_FAMILIES_INDEX(self):
        return "deviceFamilies"

    # def TAGS(self):
    #     return "tags_index"

mongoIndexNames = MongoIndexNames()