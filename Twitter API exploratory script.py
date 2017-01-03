# Import needed libraries
import tweepy
import json
import time

# Enter authorisations
consumer_key = "XXX"
consumer_secret = "XXX"
access_key = "XXX"
access_secret = "XXX"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)

# Set search term
searchquery = "new years resolution"

# Set up API call
api = tweepy.API(auth, parser = tweepy.parsers.JSONParser())

# The call only seems to return a max of 100 tweets. As such, I need to run multiple calls,
# which start after the last tweet returned in the previous call (search options here: https://dev.twitter.com/rest/reference/get/search/tweets)
results1 = api.search(q = searchquery, count = 1000, lang = 'en', result_type = 'mixed')
results1.values()[1][-1]['id']
results2 = api.search(q = searchquery, count = 1000, lang = 'en', result_type = 'mixed', max_id = '816071127286083584')

# Now to check whether the calls return any overlapping tweets
ids1 = []
ids2 = []
for i in range(0, 100):
    ids1.append(results1.values()[1][i]['id'])
    ids2.append(results2.values()[1][i]['id'])

any_in = lambda x, y: any(i in x for i in y)
any_in(ids1, ids2)

list(set(ids1).intersection(ids2))

# The last element in list 1 is returned again in list 2. Therefore, all calls subsequent to the first 
# should only use results from index [1] onwards (excluding the first tweet)

# Now to append the results of multiple API calls. To do this, I'll simply add the lists together.
results = results1.values()[1] + results2.values()[1]
len(results)

# Ok, now let's automate this to get 100,000 results
data = api.search(q = searchquery, count = 100, lang = 'en', result_type = 'mixed')
data_all = data.values()[1]


time.sleep(2)
last = data_all[-1]['id']
api.search(q = searchquery, count = 1000, lang = 'en', result_type = 'mixed', max_id = '816071127286083584')




