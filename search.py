import twint
import csv
from collections import namedtuple
from datetime import date, timedelta
from multiprocessing import Pool
import os
from itertools import repeat
import sqlite3

Interaction = namedtuple('Interaction', 'tweet, like, follow, rt, comment')

FAVE_SEARCH_TERMS = ['like', 'favorite', 'fav']
RT_SEARCH_TERMS = ['"rt to win"', '#rt2win', 'retweet to win']
BLACKLIST_USERS = ['followandrt2win', 'luisgp51', 'ilove70315673', 'PaypalCashFree', 'flores_vlogs', 'smrutimukesh', 'WinLotteryToday']

def _search(term: str, since: date) -> [twint.tweet.tweet]:
    c = twint.Config()
    c.Limit = 9999999999
    c.Since = since.strftime('%Y-%m-%d %H:%M:%S')
    c.Search = term
    c.Lang = "en"
    c.Filter_retweets = True
    c.Debug = True
    # c.Store_csv = True
    # c.Output = "search.csv"
    c.Database = "tweets.db"
    c.Resume = f"resume_file_{term}.txt"
    c.Hide_output = True
    twint.run.Search(c)

def _parse(sql_result) -> Interaction:
    (tweet_id, tweet, username) = sql_result

    if 'retweet pinned' in tweet.lower():
        return Interaction(tweet_id, False, False, False, False)

    return Interaction(
        sql_result,
        any(map(lambda term: term in tweet.lower(), FAVE_SEARCH_TERMS)),
        'follow' in tweet.lower(),
        True,
        'comment' in tweet.lower() or 'reply' in tweet.lower() or 'tag' in tweet.lower(),
    )

def _filter_tweets(tweets):
    filtered = []
    for t in tweets:
        if all([
            not t.username in BLACKLIST_USERS,
            not any(['bot' in t.username.lower(), 'b0t' in t.username.lower(), 'bot' in t.name.lower(), 'b0t' in t.name.lower()]),
            not ('kya' in t.tweet.lower() or 'jaan' in t.tweet.lower()) # basic hindi heuristic
        ]):
            filtered.append(t)

    return filtered

def find_replies(interaction):
    (tweet_id, tweet, username) = interaction.tweet

    replies = []
    while len(replies) == 0:
        c = twint.Config()
        c.Limit = 25 # we don't need a ton of replies, just get 10
        c.To = username
        # c.Hide_output = True
        c.Store_object = True
        # possible improvement: add c.Since to the timestamp of the original tweet
        print(username)
        print(twint.run.Search(c))
        
        # replies += list(filter(c.))
    return replies



def search():
    since = date.today() - timedelta(days=7)
    counter = 0
    while True:
        print(f"{counter} search iteration")
        counter += 1
        with Pool(len(RT_SEARCH_TERMS)) as pool:
            pool.starmap(_search, zip(RT_SEARCH_TERMS, repeat(since)))

def retrieve_nonseen_interactions(seen: list):
    seen_ids = ", ".join(list(map(lambda x: f"\"{seen}\"", seen)))
    screen_names = ", ".join(map(lambda x: f"\"{x}\"", BLACKLIST_USERS))
    query = """
        SELECT id, tweet, screen_name
        FROM tweets
        WHERE 
            (NOT replace(lower(screen_name), "0", "o") glob "*bot*" OR NOT replace(lower(name), "0", "o") glob "bot*") AND
            NOT screen_name IN ({}) AND
            NOT id in ({})
    """.format(screen_names, seen_ids)

    connection = sqlite3.connect('tweets.db')
    results = connection.cursor().execute(query)

    collect = []
    for r in results:
        collect.append(_parse(r))

    return collect

