# Import needed libraries
import tweepy
import json
import time
import scipy.stats as sp

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np
from pandas import Series, DataFrame
import pandas as pd

from ggplot import *

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

# Ok, now let's automate this to get 20,000 results
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

while (len(data_all) <= 20000):
    time.sleep(4)
    last = data_all[-1]['id']
    data = api.search(q = searchquery, count = 100, lang = 'en', result_type = 'mixed', max_id = last)
    data_all += data.values()[1][1:]
    
# Feed into a dataframe
# NOTE: once I finish pulling these data out, I need to check that I am getting the *right* bits of
# data to go with the specific tweet. Especially confusing in the case of retweets, so need to just
# doublecheck I have that right.

analyzer = SentimentIntensityAnalyzer()

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
    date.append(data_all[i]['created_at'])
    tweet.append(data_all[i]['text'])
    number_favourites.append(data_all[i]['favorite_count'])
    number_retweets.append(data_all[i]['retweet_count'])
    timezone.append(data_all[i]['user']['time_zone'])
    vs_compound.append(analyzer.polarity_scores(data_all[i]['text'])['compound'])
    vs_pos.append(analyzer.polarity_scores(data_all[i]['text'])['pos']) 
    vs_neu.append(analyzer.polarity_scores(data_all[i]['text'])['neu'])
    vs_neg.append(analyzer.polarity_scores(data_all[i]['text'])['neg'])

twitter_df = DataFrame({'Date': date,
                        'Tweet': tweet,
                        'Favourites': number_favourites,
                        'Retweets': number_retweets,
                        'Timezone': timezone,
                        'Compound': vs_compound,
                        'Positive': vs_pos,
                        'Neutral': vs_neu,
                        'Negative': vs_neg})
twitter_df = twitter_df[['Date', 'Tweet', 'Favourites', 'Retweets', 'Timezone', 
                        'Compound', 'Positive', 'Neutral', 'Negative']]

# Create categories of resolutions (based on Wikipedia's classifications)
twitter_df['Physical Health'] = np.where(twitter_df['Tweet'].str.contains('weight|fit|exercise|gym|muscle|health|water|smoking|alcohol|drinking|walk|run|swim', 
    flags = re.IGNORECASE), 1, 0)
twitter_df['Learning and Career'] = np.where(twitter_df['Tweet'].str.contains('business|job|career|professional|study|learn|develop|advance|grades|school|university|read|study|skill|education', 
    flags = re.IGNORECASE), 1, 0)
twitter_df['Mental Wellbeing'] = np.where(twitter_df['Tweet'].str.contains('positive|enjoy|happy|happiness|stress|depress|anxi|organised|organized|hobb|fun|psychologist|psychiatrist|sleep|meditate', 
    flags = re.IGNORECASE), 1, 0)
twitter_df['Finances'] = np.where(twitter_df['Tweet'].str.contains('save|saving|debt|credit|money|invest|wast|finance|frugal|\$', 
    flags = re.IGNORECASE), 1, 0)
twitter_df['Relationships'] = np.where(twitter_df['Tweet'].str.contains('relationship|friend|boyfriend|girlfriend|fiance|husband|wife|engaged|wedding|married|pregnant|child|kid|family|parent|father|dad|mother|mom|mum|brother|sister|dog|cat', 
    flags = re.IGNORECASE), 1, 0)
twitter_df['Travel and Holidays'] = np.where(twitter_df['Tweet'].str.contains('travel|trip|holiday|vacation|country|foreign|overseas|abroad', 
    flags = re.IGNORECASE), 1, 0)

# Have a look whether there is variance in the compound sentiment score for each - yep, we're good to go ahead
len(twitter_df[(twitter_df['Compound'] == 0)])
twitter_df['Compound'][twitter_df['Physical Health'] == 1].mean()
twitter_df['Compound'][twitter_df['Learning and Career'] == 1].mean()
twitter_df['Compound'][twitter_df['Mental Wellbeing'] == 1].mean()
twitter_df['Compound'][twitter_df['Finances'] == 1].mean()
twitter_df['Compound'][twitter_df['Relationships'] == 1].mean()
twitter_df['Compound'][twitter_df['Travel and Holidays'] == 1].mean()

# After finding no variance in the number of favourites when using sensible measures of central
# tendency (trimmed means and medians), I went with looking at the percent of tweets that got above
# a threshold of favourites (trying 5 or more)
def calculatePercentFavourite(resolution, favourites):
    number_with_favourites = float(len(twitter_df[(twitter_df[resolution] == 1) & (twitter_df['Favourites'] >= favourites)]))
    total_number = float(len(twitter_df[(twitter_df[resolution] == 1)]))
    return number_with_favourites / total_number * 100
    
calculatePercentFavourite('Physical Health', 5)
calculatePercentFavourite('Learning and Career', 5)
calculatePercentFavourite('Mental Wellbeing', 5)
calculatePercentFavourite('Finances', 5)
calculatePercentFavourite('Relationships', 5)
calculatePercentFavourite('Travel and Holidays', 5)

calculatePercentFavourite('Physical Health', 10)
calculatePercentFavourite('Learning and Career', 10)
calculatePercentFavourite('Mental Wellbeing', 10)
calculatePercentFavourite('Finances', 10)
calculatePercentFavourite('Relationships', 10)
calculatePercentFavourite('Travel and Holidays', 10)

# 5 favourites or more has good variance, let's go with that
twitter_df['Five or more favourites'] = np.where(twitter_df['Favourites'] >= 5, 1, 0)

# Now let's write the data for presenting in the blog post into a CSV, in case we lose it 
twitter_df_clean = twitter_df
twitter_df_clean = twitter_df_clean[['Date', 'Favourites', 'Retweets', 'Timezone', 'Compound', 'Positive', 
                         'Neutral', 'Negative', 'Physical Health', 'Learning and Career',
                         'Mental Wellbeing', 'Finances', 'Relationships', 'Travel and Holidays',
                         'Five or more favourites']]

#twitter_df_clean['Tweet'] = twitter_df_clean['Tweet'].str.replace("|", ",")
twitter_df_clean.to_csv("/Users/jodieburchell/Documents/Twiiter API analysis/Raw twitter data.csv",
                        sep = ",")

# Create single resolution variable
col_list= ['Physical Health', 'Learning and Career', 'Mental Wellbeing',
           'Finances', 'Relationships', 'Travel and Holidays']
col_list
twitter_df['Number of resolutions'] = twitter_df[col_list].sum(axis=1)
sum(twitter_df['Number of resolutions'] >= 1)
sum(twitter_df['Number of resolutions'] > 1)
sum((twitter_df['Number of resolutions'] > 1) & (twitter_df['Physical Health'] == 1))
sum((twitter_df['Number of resolutions'] > 1) & (twitter_df['Learning and Career'] == 1))
sum((twitter_df['Number of resolutions'] > 1) & (twitter_df['Mental Wellbeing'] == 1))
sum((twitter_df['Number of resolutions'] > 1) & (twitter_df['Finances'] == 1))
sum((twitter_df['Number of resolutions'] > 1) & (twitter_df['Relationships'] == 1))
sum((twitter_df['Number of resolutions'] > 1) & (twitter_df['Travel and Holidays'] == 1))

def createResolutionVariable(resolution):
    return np.where((twitter_df[resolution] == 1) & (twitter_df['Number of resolutions'] < 2), 
    resolution, twitter_df['Resolution type'])
      
twitter_df['Resolution type'] = np.where((twitter_df['Physical Health'] == 1) & (twitter_df['Number of resolutions'] < 2), 'Physical Health', '')
twitter_df['Resolution type'] = createResolutionVariable('Learning and Career')
twitter_df['Resolution type'] = createResolutionVariable('Mental Wellbeing')
twitter_df['Resolution type'] = createResolutionVariable('Finances')
twitter_df['Resolution type'] = createResolutionVariable('Relationships')
twitter_df['Resolution type'] = createResolutionVariable('Travel and Holidays')

sum(twitter_df['Resolution type'] == 'Physical Health')
sum(twitter_df['Resolution type'] == 'Learning and Career')
sum(twitter_df['Resolution type'] == 'Mental Wellbeing')
sum(twitter_df['Resolution type'] == 'Finances')
sum(twitter_df['Resolution type'] == 'Relationships')
sum(twitter_df['Resolution type'] == 'Travel and Holidays')

def viewMultipleTweet(row):
    return (twitter_df.loc[twitter_df['Number of resolutions'] > 1].iloc[row]['Tweet']

def setResolutionType(row, replace_resolution):
    indexn = twitter_df[twitter_df['Number of resolutions'] > 1].index.tolist()[row]
    twitter_df.loc[twitter_df.index == indexn, 'Resolution type'] = replace_resolution

# Need to check 670 tweets
viewMultipleTweet(0)
setResolutionType(0, 'Mental Wellbeing')

viewMultipleTweet(1)
setResolutionType(1, 'Learning and Career')

viewMultipleTweet(2)
setResolutionType(2, 'Physical Health')

viewMultipleTweet(3)
setResolutionType(3, 'Physical Health')

viewMultipleTweet(4)
setResolutionType(4, 'Physical Health')

viewMultipleTweet(5)
setResolutionType(5, 'Mental Wellbeing')

viewMultipleTweet(6)
setResolutionType(6, 'Learning and Career')

viewMultipleTweet(7)
setResolutionType(7, '')

viewMultipleTweet(8)
setResolutionType(8, 'Physical Health')

viewMultipleTweet(9)
setResolutionType(9, 'Mental Wellbeing')

viewMultipleTweet(10)
setResolutionType(10, 'Mental Wellbeing')

viewMultipleTweet(11)
setResolutionType(11, 'Mental Wellbeing')

viewMultipleTweet(12)
setResolutionType(12, 'Physical Health')

viewMultipleTweet(13)
setResolutionType(13, 'Physical Health')

viewMultipleTweet(14)
setResolutionType(14, 'Relationships')

viewMultipleTweet(15)
setResolutionType(15, 'Physical Health')

viewMultipleTweet(16)
setResolutionType(16, 'Mental Wellbeing')

viewMultipleTweet(17)
setResolutionType(17, 'Mental Wellbeing')

viewMultipleTweet(18)
setResolutionType(18, 'Learning and Career')

viewMultipleTweet(19)
setResolutionType(19, 'Mental Wellbeing')

viewMultipleTweet(20)
setResolutionType(20, 'Mental Wellbeing')

viewMultipleTweet(21)
setResolutionType(21, 'Mental Wellbeing')

viewMultipleTweet(22)
setResolutionType(22, 'Mental Wellbeing')

viewMultipleTweet(23)
setResolutionType(23, 'Mental Wellbeing')


