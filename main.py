from time import sleep
from search import search, retrieve_nonseen_interactions, find_replies, Interaction
from multiprocessing import Process, Manager, Queue, Pool
import csv

###
### Here's my attempt at a simple bot that enters retweet to win contests.
### Inspired, like most of them, by Howard Scott's DEFCON 24 talk.
###
### My strategy is:
###     1. reduce usage of the actual twitter API - they're harsh on rate
###        rate limiting, so let's reduce our interactions with them.
###        Searching for tweets to RT can be done without the authenticated
###        API. Let's use the awesomely powerful opsec tool: twintproject's
###        twint. Searching is implemented in search.py
###     2. to hopefully grab more awesome search terms. I want to max out my
###        tweet rate - which from the talk seems to be tweet every 30 seconds?

# already_interacted.csv contains a list of IDs that we've already 
# rt'd/liked/followed etc.

already_interacted = set()
interact_queue = []

def interact(interaction: Interaction):
    if interaction.tweet.id in already_interacted:
        return

    already_interacted.add(interaction.tweet.id)
    t = interaction.tweet
    print(f"{t.id} <{t.username}> {t.tweet}")

def runloop():
    queue = []

    while True:
        if (len(queue) == 0):
            # refill queue
            # first find ids already seen in database
            with open('seen.csv', 'r') as seen:
                seen_ids = list(csv.reader(seen))
                queue += retrieve_nonseen_interactions(seen_ids)
        else:
            # queue tweet to retweet
            current_tweet = queue.pop()
            # print(current_tweet)
            if current_tweet.comment:
                print(current_tweet)
                # go find a random reply and use it as the response
                replies = find_replies(current_tweet)
                


    # global interact_queue
    # if len(interact_queue) == 0:
    #     interact_queue += search(date.today() - timedelta(days=7))
    # else:
    #     interact(interact_queue.pop())
    #     sleep(15)

# leaky bucket approach from https://stackoverflow.com/a/48976957
Process(target=runloop).start()
# while True:
#     print('running search')
#     search()
# find_replies('1219031771569971200')