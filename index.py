import praw
from get_all_tickers.get_tickers import get_tickers
from bs4 import BeautifulSoup
from collections import *
import pandas as pd
import warnings
from wallstreet import Stock, Call, Put
import datetime


# Suppress warning for beautiful soup parsing urls
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

# All ticker from American indexes
tickers = get_tickers()

# Capitalized strings that are likely not stock tickers
notTickers = ["CEO", "DD", "RH"]

#today
today = datetime.datetime.today()

# Utility function to print an object's properties
def logAllPropertiesUtility(obj):
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))

# Remove posts with flair that isn't interesting
def filterPostsByFlair(post):
    if(post.link_flair_text != "Shitpost" and post.link_flair_text!="EarningsThread" and post.link_flair_text != "Meme" and post.link_flair_text != "Mods" and post.link_flair_text != "Loss" and post.link_flair_text != "Gain" and post.link_flair_text != "Weekend Discussion" and post.link_flair_text != "Daily Discussion"):
        return True
    else:
        return False

# Remove posts with flair that isn't interesting
def filterPostsBySubject(post):
    if(post[0] != "none"):
        return True
    else:
        return False

# A utility function to translate markdown to plain text so the tickers can be more easily extracted
def markdownToPlainTextUtility(markdown):
    plainText = " ".join(BeautifulSoup(markdown, "html.parser").findAll(text=True))
    return plainText

# Utility function to clean strings for veryifying tickers
def cleanStringUtility(string):
    return string.replace("$", "")

# Utility function that recieves long string and gets likely tickers out
def findTickersUtility(string):
    singleWords = string.split(" ")

    def filterTickers(string):
        cleanString = cleanStringUtility(string)
        if (cleanString == cleanString.upper() and cleanString in tickers and cleanString not in notTickers):
            return True
        else:
            return False
    tickerList = filter (filterTickers, singleWords)
    return list(tickerList)

# Function that looks through comments and gets all of the tickers out
def extractTickersFromComments(comments):
    comments.replace_more(limit=15)
    allTickersList = []
    for comment in comments:
        commentTickerList = findTickersUtility(markdownToPlainTextUtility(comment.body))
        allTickersList.extend(commentTickerList)
    return allTickersList

# function to determine the underlying stock that a post is talking about by looking at the most commonly mentioned ticker in the title, description, and comments
def determinePostSubject(post):
    # Aggregate all the tickers
    titleTickers = findTickersUtility(post.title)
    descriptionTickers = findTickersUtility(markdownToPlainTextUtility(post.selftext))
    commentTickers = extractTickersFromComments(post.comments)
    allTickers = titleTickers + descriptionTickers + commentTickers

    def check_for_subject(tickerArray):
        if tickerArray:
            return tickerArray[0][0]
        else:
            return "none"

    countedTickers = Counter(map(cleanStringUtility, allTickers))
    tickerArray = countedTickers.most_common(1)
    finalTicker = check_for_subject(tickerArray) 
    return finalTicker


def get_relevant_data(subject, score, upvoteRatio, title, url):
    post = [subject, score, upvoteRatio, title, url]
    return post

def map_post(post):
    postSubject = determinePostSubject(post)

    
    # Put the relevant data in an object
    relevantPostData = get_relevant_data(postSubject, post.score, post.upvote_ratio, post.title, post.url)
    return relevantPostData

def group_posts(posts):
    df = pd.DataFrame(posts, columns=["subject", "score", "upvote_ratio", "title", "url"])
    return df.groupby("subject").agg({"score":"sum", "upvote_ratio":"mean"}).sort_values(by="score", ascending=False)

# def get_out_of_money_calls(option, price):

class Readable_Option(object):
    def __init__(self,underlying_price, strike, expiration, iv):
        self.underlying_price = underlying_price
        self.strike = strike
        self.expiration = expiration
        self.iv = iv

def create_readable_option(underlying_price, strike, expiration, iv):
    option = Readable_Option(underlying_price, strike, expiration, iv)
    return option


    
def get_option_data(ticker):
    underlying_price = Stock(ticker).price
    option_object = Call(ticker)
    possible_expirations = option_object.expirations
    expiration = possible_expirations[int(len(possible_expirations)/2)].split("-")
    possible_strikes = list(filter(lambda x: (x > underlying_price), option_object.strikes)) 
    strike = possible_strikes[int(len(possible_strikes)/2)]
    option = Call(ticker, d=int(expiration[0]), m=int(expiration[1].replace("0", "")), y=int(expiration[2]), strike=strike)
    print(option)

    # readable_option = create_readable_option(underlying_price, option.strike, option.expiration, option.implied_volatility())
    # print(readable_option)

    # return underlying_price

    
def add_option_data(df):
     df['underlying_price'] = df.apply(lambda row: get_option_data(row.name), axis=1)
     return df

reddit = praw.Reddit(
    client_id="2CnK2g9kd4r-GA",
    client_secret="FXV6MyfzzCDBQPP0dsUyn7_eEDOHJw",
    user_agent="My sick ass project alkdjfsodijfa"
)

# #get raw posts
# allPosts = reddit.subreddit("wallstreetbets").hot(limit=100)
# #filter posts by flair
# flairFilteredPosts = filter(filterPostsByFlair, allPosts)
# #map posts down to relevant data
# mappedPosts = map(map_post, flairFilteredPosts)
# #filter posts by subject
# subjectFilteredPosts = filter(filterPostsBySubject, mappedPosts)
# #put the different wsb stocks into a dataframe
# groups = group_posts(subjectFilteredPosts)
# #append options data
# full_data = add_option_data(groups)
# print(full_data)


get_option_data("GME")

