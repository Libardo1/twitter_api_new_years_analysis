# Import needed libraries
import tweepy
import json
import time

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

# Enter authorisations
consumer_key = "XXX"
consumer_secret = "XXX"
access_key = "XXX"
access_secret = "XXX"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)

# Set search term
searchquery = '"new years resolution" -filter:retweets'

# Set up API call
api = tweepy.API(auth, parser = tweepy.parsers.JSONParser())

# The call only seems to return a max of 100 tweets. As such, I need to run multiple calls,
# which start after the last tweet returned in the previous call (search options here: https://dev.twitter.com/rest/reference/get/search/tweets)
results1 = api.search(q = searchquery, count = 1, lang = 'en', result_type = 'mixed')
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

# Ok, now let's automate this to get 50,000 results
data = api.search(q = searchquery, count = 100, lang = 'en', result_type = 'mixed')
data_all = data.values()[1]

while (len(data_all) <= 200):
    time.sleep(2)
    last = data_all[-1]['id']
    data = api.search(q = searchquery, count = 100, lang = 'en', result_type = 'mixed', max_id = last)
    data_all += data.values()[1][1:]

# Checking I got rid of the duplicate extraction of the last tweet
ids = []
for i in range(0, 298):
    ids.append(data_all[i]['id'])

set([x for x in ids if ids.count(x) > 1])
len(ids) != len(set(ids))

# Final call
data = api.search(q = searchquery, count = 100, lang = 'en', result_type = 'mixed')
data_all = data.values()[1]

while (len(data_all) <= 10000):
    time.sleep(2)
    last = data_all[-1]['id']
    data = api.search(q = searchquery, count = 100, lang = 'en', result_type = 'mixed', max_id = last)
    data_all += data.values()[1][1:]
    
# Feed into a dataframe
# NOTE: once I finish pulling these data out, I need to check that I am getting the *right* bits of
# data to go with the specific tweet. Especially confusing in the case of retweets, so need to just
# doublecheck I have that right.

analyzer = SentimentIntensityAnalyzer()

tweet_id = []
user = []
date = []
tweet = []
number_favourites = []
number_retweets = []
timezone = []
vs_compound = []
vs_pos = [] 
vs_neu = []
vs_neg = []

for i in range(0, len(data_all)):
    tweet_id.append(data_all[i]['id'])
    user.append(data_all[i]['user']['screen_name'])
    date.append(data_all[i]['created_at'])
    tweet.append(data_all[i]['text'])
    number_favourites.append(data_all[i]['favorite_count'])
    number_retweets.append(data_all[i]['retweet_count'])
    timezone.append(data_all[i]['user']['time_zone'])
    vs_compound.append(analyzer.polarity_scores(data_all[i]['text'])['compound'])
    vs_pos.append(analyzer.polarity_scores(data_all[i]['text'])['pos']) 
    vs_neu.append(analyzer.polarity_scores(data_all[i]['text'])['neu'])
    vs_neg.append(analyzer.polarity_scores(data_all[i]['text'])['neg'])

twitter_df = DataFrame({'ID': tweet_id,
                        'Date': date,
                        'Tweet': tweet,
                        'Favourites': number_favourites,
                        'Retweets': number_retweets,
                        'Timezone': timezone,
                        'Compound': vs_compound,
                        'Positive': vs_pos,
                        'Neutral': vs_neu,
                        'Negative': vs_neg})
twitter_df = twitter_df[['ID', 'Date', 'Tweet', 'Favourites', 'Retweets', 'Timezone', 
                        'Compound', 'Positive', 'Neutral', 'Negative']]
twitter_df2 = twitter_df[['ID', 'Date', 'Favourites', 'Retweets', 'Timezone', 
                        'Compound', 'Positive', 'Neutral', 'Negative']]

twitter_df2.to_csv("/Users/jburchell/Documents/Twitter API analysis/Raw twitter data.csv",
                  sep = ",", encoding = "utf-8")
                        
twitter_df[:20]
