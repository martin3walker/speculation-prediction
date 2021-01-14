import praw
from get_all_tickers.get_tickers import get_tickers
from bs4 import BeautifulSoup
from collections import *
import pandas as pd
import warnings

# Suppress warning for beautiful soup parsing urls
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

# All ticker from American indexes
tickers = get_tickers()

# Capitalized strings that are likely not stock tickers
notTickers = ["CEO", "DD", "RH"]

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
    if(post.subject != "none"):
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

#Class for post data strcuture
class Post(object):
    subject = ""
    score = 0
    upvoteRatio = 0

    def __init__(self, subject, score, upvoteRatio, title, url):
        self.subject = subject
        self.score = score
        self.upvoteRatio = upvoteRatio
        # self.title = title
        self.url = url
    
    def __str__(self):
        return str(self.__dict__)

def get_relevant_data(subject, score, upvoteRatio, title, url):
    post = Post( subject, score, upvoteRatio, title, url)
    return post

def map_post(post):
    postSubject = determinePostSubject(post)
    
    # Put the relevant data in an object
    relevantPostData = get_relevant_data(postSubject, post.score, post.upvote_ratio, post.title, post.url)
    return relevantPostData

def group_posts(posts):
    df = pd.DataFrame(posts)
    return df.groupby("subject")["score"].count()
    


reddit = praw.Reddit(
    client_id="2CnK2g9kd4r-GA",
    client_secret="FXV6MyfzzCDBQPP0dsUyn7_eEDOHJw",
    user_agent="My sick ass project alkdjfsodijfa"
)

#get raw posts
allPosts = reddit.subreddit("wallstreetbets").hot(limit=30)
#filter posts by flair
flairFilteredPosts = filter(filterPostsByFlair, allPosts)
#map posts down to relevant data
mappedPosts = map(map_post, flairFilteredPosts)
#filter posts by subject
subjectFilteredPosts = filter(filterPostsBySubject, mappedPosts)

# groups = group_posts(subjectFilteredPosts)
# print(groups)

for post in subjectFilteredPosts:
    print(post)

   



