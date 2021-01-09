import os
import praw

try:
    from passwords import REDDIT
except:
    import ast
    REDDIT = ast.literal_eval(os.environ.get('REDDIT'))

client_id = REDDIT['client_id']
client_secret = REDDIT['client_secret']
username = REDDIT['username']
password = REDDIT['password']
user_agent = REDDIT['user_agent']

reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, username=username, password=password, user_agent=user_agent)
subreddit = reddit.subreddit('RLPC')

def list_top(limit = 5):
    title = []
    author = []
    ups = []
    downs = []
    comments = []
    contents = []
    links = []
    for submission in subreddit.top(limit=limit):
        title.append(submission.title)
        author.append(submission.author)
        ups.append(submission.ups)
        downs.append(submission.downs)
        comments.append(submission.num_comments)
        contents.append(submission.selftext)
        links.append(submission.permalink)
    return (title, author, ups, downs, comments, contents, links)

def list_hot(limit = 5):
    title = []
    author = []
    ups = []
    downs = []
    comments = []
    contents = []
    links = []
    for submission in subreddit.hot(limit=limit+2):
        if not submission.stickied:
            title.append(submission.title)
            author.append(submission.author)
            ups.append(submission.ups)
            downs.append(submission.downs)
            comments.append(submission.num_comments)
            contents.append(submission.selftext)
            links.append(submission.permalink)
    return (title, author, ups, downs, comments, contents, links)

def list_new(limit = 5):
    title = []
    author = []
    ups = []
    downs = []
    comments = []
    contents = []
    links = []
    for submission in subreddit.new(limit=limit):
        if not submission.stickied:
            title.append(submission.title)
            author.append(submission.author)
            ups.append(submission.ups)
            downs.append(submission.downs)
            comments.append(submission.num_comments)
            contents.append(submission.selftext)
            links.append(submission.permalink)
    return (title, author, ups, downs, comments, contents, links)

def get_post(type, number):
    if type.casefold() == "new":
        posts = list_new(limit=number+5)
    elif type.casefold() == "hot":
        posts = list_hot(limit=number+5)
    elif type.casefold() == "top":
        posts = list_top(limit=number+5)
    title = posts[0][number-1]
    author = posts[1][number-1]
    ups = posts[2][number-1]
    downs = posts[3][number-1]
    contents = posts[5][number-1]
    links = posts[6][number-1]
    return (title, author, ups, downs, contents, links)