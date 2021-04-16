#########################################
##### Name: Guan-Ying Lai           #####
##### Uniqname: evylai              #####
#########################################

from requests_oauthlib import OAuth1
import json
import requests
import base64
import datetime
import webbrowser
import tweepy
from urllib.parse import urlencode
from wordcloud import WordCloud
import matplotlib.pyplot as plt

import secret_key as secret_key # file that contains your OAuth credentials

CACHE_FILENAME = "twitter_cache.json"

CACHE_DICT = {}

client_key = secret_key.TWITTER_API_KEY
client_secret = secret_key.TWITTER_API_SECRET
access_token = secret_key.TWITTER_ACCESS_TOKEN
access_token_secret = secret_key.TWITTER_ACCESS_TOKEN_SECRET

client_key_s = secret_key.spotify_id
client_secret_s = secret_key.spotify_secret

oauth = OAuth1(client_key,
            client_secret=client_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret)

auth = tweepy.OAuthHandler(client_key, client_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

class SpotifyAPI(object):
    access_token_s = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_key_s = None
    client_secret_s = None
    token_url = "https://accounts.spotify.com/api/token"


    def __init__(self, client_key_s, client_secret_s, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_key_s = client_key_s
        self.client_secret_s = client_secret_s
    
    def get_clien_credentials(self):
        """
        return a base64 encoded string
        """
        client_key_s = self.client_key_s
        client_secret_s = self.client_secret_s
        if client_key_s == None or client_secret_s == None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f"{client_key_s}:{client_secret_s}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
    
    def get_token_headers(self):
        '''
        Find the token header
        '''
        client_creds_b64 = self.get_clien_credentials()
        return {
            'Authorization': f"Basic {client_creds_b64}"
        }

    def get_token_data(self):
        '''
        Find the token data
        '''
        return {
            'grant_type': "client_credentials"
        }

    def perform_auth(self):
        '''
        Test if the auth works
        '''
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
        data = r.json()
        now = datetime.datetime.now()
        access_token_s = data["access_token"]
        expires_in = data["expires_in"]
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token_s = access_token_s
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True

    def get_access_token(self):
        '''
        Get the access of the token for the searching
        '''
        token = self.access_token_s
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token
    
    def search(self, query, search_type="track"):
        '''
        Search based on the query(user input), the searching type is limited to the track
        '''
        access_token_s = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token_s}"
        }
        endpoint = "https://api.spotify.com/v1/search"
        data = urlencode({
            "q": query.lower(),
            "type": search_type.lower(),
            "limit": 3
        })
        lookup_url = f"{endpoint}?{data}"
        # print(lookup_url)
        r = requests.get(lookup_url, headers=headers)
        # print(r.status_code)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()["tracks"]["items"]

def sort_list(search_results):
    '''
    Find the song name, artist, album, and url from the json file

    Parameters
    ------------------------
    json file
        searching result from the spotify API

    Results
    ------------------------
    lists
        a list of the track, a list of the url, and a list of song name
    '''

    print_song_name = []
    print_track_list = []
    print_url_list = []
    print_popularity = []
    for result in search:
        try:
            song = result["name"]
            artist = result["artists"][0]["name"]
            album = result["album"]["name"]
            url = result["external_urls"]["spotify"]
            popularity = result["popularity"]
        except:
            artist = "N/A"
            album = "N/A"
            url = "N/A"
        print_track_list.append(f"'{song}' by {artist} - {album}")
        print_url_list.append(url)
        print_song_name.append(song)
        print_popularity.append(popularity)
    return print_track_list, print_url_list, print_song_name, print_popularity
        
def test_oauth():
    ''' Helper function that returns an HTTP 200 OK response code and a 
    representation of the requesting user if authentication was 
    successful; returns a 401 status code and an error message if 
    not. Only use this method to test if supplied user credentials are 
    valid. Not used to achieve the goal of this assignment.'''

    url = "https://api.twitter.com/1.1/account/verify_credentials.json"
    auth = OAuth1(client_key, client_secret, access_token, access_token_secret)
    authentication_state = requests.get(url, auth=auth).json()
    return authentication_state

def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its baseurl and params

    AUTOGRADER NOTES: To correctly test this using the autograder, use an underscore ("_") 
    to join your baseurl with the params and all the key-value pairs from params
    E.g., baseurl_key1_value1
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs
    
    Returns
    -------
    string
        the unique key as a string
    '''

    param_strings = []
    for k, v in params.items():
        param_strings.append(f"{k}_{v}")
    param_strings.sort()
    unique_key = f"{baseurl}_{param_strings}"
    return unique_key
    

def make_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs
    
    Returns
    -------
    dict
        the data returned from making the request in the form of 
        a dictionary
    '''
    response = requests.get(baseurl, params=params, auth=oauth)
    return response.json()


def make_request_with_cache(baseurl, hashtag, count):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    AUTOGRADER NOTES: To test your use of caching in the autograder, please do the following:
    If the result is in your cache, print "fetching cached data"
    If you request a new result using make_request(), print "making new request"

    Do no include the print statements in your return statement. Just print them as appropriate.
    This, of course, does not ensure that you correctly retrieved that data from your cache, 
    but it will help us to see if you are appropriately attempting to use the cache.
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    hashtag: string
        The hashtag to search(i.e.#MarchMadness2021)
    count: int
        The number of tweets toretrieve
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    params={
        "q": hashtag.lower(), 
        "count": count
    }
    request_key = construct_unique_key(baseurl, params)
    if request_key in CACHE_DICT.keys():
        print("fetching cached data")
        # print(CACHE_DICT[request_key]["statuses"])
        return CACHE_DICT[request_key]["statuses"]
    else:
        print("making new request")
        CACHE_DICT[request_key] = make_request(baseurl, params)
        save_cache(CACHE_DICT)
        # print(CACHE_DICT[request_key])
        return CACHE_DICT[request_key]

def find_cooccurring_hashtag(tweet_data):
    ''' Finds the hashtag that most commonly co-occurs with the hashtag
    queried in make_request_with_cache().

    Parameters
    ----------
    tweet_data: dict
        Twitter data as a dictionary for a specific query

    Returns
    -------
    string
        the hashtag that most commonly co-occurs with the hashtag 
        queried in make_request_with_cache()

    '''

    hashtags_dict={}
    for dictionary in tweet_data:
        for item in dictionary["entities"]["hashtags"]:
            tag = item["text"].lower()
            if tag in hashtags_dict:
                hashtags_dict[tag] += 1
            else:
                hashtags_dict[tag] = 1
    
    return hashtags_dict

def tweetSearch(query, limit = 20, language = "en", remove = []):
    '''
    User the query (user input) to search for a text of most freguently mentioned words related to the hashtag

    Parameters
    -------------------
    str
        user input searching keyword
    int
        the limitation of the related words
    
    Results
    -------------------
    str
        most frequently mentioned words realted to the query
    '''
    text = ""
    for tweet in tweepy.Cursor(api.search, q=query, lang=language).items(limit):
        text += tweet.text.lower()

    remove_words = ["https","co"]
    remove_words += remove

    for word in remove_words:
        text = text.replace(word, "")
    return text


if __name__ == "__main__":
    keyword = input(f"Enter a search track, or 'exit' to quit: ")
    if keyword == 'exit':
        print("Bye!")
        quit()
    else:
        spotify = SpotifyAPI(client_key_s, client_secret_s)
        search = spotify.search(keyword)
        results = sort_list(search)[0]
        urls = sort_list(search)[1]
        popularity = sort_list(search)[3]
        i = 1
        for result in results:
            print(f"[{i}] {result}")
            i+=1
        for item in urls:
            print(item)


    while True:
        if not client_key or not client_secret:
            print("You need to fill in CLIENT_KEY and CLIENT_SECRET in secret_data.py.")
            exit()
        if not access_token or not access_token_secret:
            print("You need to fill in ACCESS_TOKEN and ACCESS_TOKEN_SECRET in secret_data.py.")
            exit()
        term = input(f"Enter a number for more info, or another search term, or exit: ")
        if term == 'exit':
            print("Bye!")
            quit()
        else:
            if term.isnumeric() and int(term) <= len(results):
                num = int(term)
                print(f"Launching {results[num-1]} in web browser...")
                webbrowser.open(urls[num-1])
                CACHE_DICT = open_cache()
                baseurl = "https://api.twitter.com/1.1/search/tweets.json"
                song_name = sort_list(search)[2][num-1].lower()
                hashtag = f"#{song_name.replace(' ','')}"
                count = 20
                tweet_data = make_request_with_cache(baseurl, hashtag, count)
                cooccurring_hashtag = find_cooccurring_hashtag(tweet_data)
                # print(cooccurring_hashtag)
                twitter_search = tweetSearch(song_name)
                while True:
                    option = input(f"Do you want to see the wordcloud or barchart for the twitter result, or type new to start a new search? (please key in wordcloud, barchart, new): ")
                    if option == "wordcloud":
                        print(f"Showing the wordcloud...")
                        wordcloud = WordCloud(width = 1000, height = 500).generate_from_frequencies(cooccurring_hashtag)
                        plt.figure(figsize=(15,8))
                        plt.imshow(wordcloud)
                        plt.show()
                        pass
                    elif option == "barchart":
                        print(f"Showing the bar chart...")
                        pass
                    elif option == "new":
                        break
                    else:
                        print(f"Wrong key word, please type wordcloud or barchart")
                        pass
            else:
                results.clear()
                spotify = SpotifyAPI(client_key_s, client_secret_s)
                search = spotify.search(term)
                results = sort_list(search)[0]
                urls = sort_list(search)[1]
                i = 1
                for result in results:
                    print(f"[{i}] {result}")
                    i+=1
