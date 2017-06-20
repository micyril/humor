import argparse
import json
import sys
import time

import six
import tweepy

# Fill in your secret keys. Learn more how to get them on the page
# https://dev.twitter.com/oauth/overview/application-owner-access-tokens
CONSUMER_KEY = ""
CONSUMER_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""

def create_argparser():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("ids", nargs='?', default="ids.txt")
    argparser.add_argument("-o", "--output", default="tweets.json")
    return argparser

def read_ids(filename):
    try:
        with open(filename) as f:
            return [int(id) for id in f.read().split()]
    except IOError as e:
        six.print_("Can't read the file", filename)
        exit(1)

def init_api():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    return tweepy.API(auth)

def iter_by_hundreds(ids):
    i = 0
    while i < len(ids):
        yield ids[i:i + 100]
        i += 100

def retrieve_statuses(api, ids_portion):
    try:
        return api.statuses_lookup(ids_portion)
    except tweepy.error.RateLimitError:
        six.print_("\nRate limit has been achieved. Waiting...")
        while True:
            try:
                return api.statuses_lookup(ids_portion)
            except tweepy.error.RateLimitError:
                time.sleep(30)
    except tweepy.error.TweepError as e:
        six.print_("Failed to look up:", str(e))
        exit(1)

def write_json(obj, filename):
    with open(filename, "w") as f:
        json.dump(obj, f, sort_keys=True, indent=4, ensure_ascii=False)

args = create_argparser().parse_args()

ids = read_ids(args.ids)
api = init_api()

tweets = []
missed_tweets = 0
for hundred in iter_by_hundreds(ids):
    statuses = retrieve_statuses(api, hundred)
    missed_tweets += 100 - len(statuses)
    tweets.extend({"id": s.id, "text": s.text, "favorites": s.favorite_count,
                   "retweets": s.retweet_count, "user": s.user.screen_name}
                  for s in statuses)
    percents = 100 * len(tweets) / (len(ids) - missed_tweets)
    six.print_("Retrieved %d tweets (%d%%) \r" % (len(tweets), percents),
               end="")
    sys.stdout.flush()

write_json(tweets, args.output)
