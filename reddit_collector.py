from typing import Dict, Any

import reddit_data_collector as rdc
import pandas as pd
import praw
import video_maker
import os
import mongo
import random
from video_maker import video
import textwrap
import title_card

# The idea right now is, take the top x posts on TIFU, filter out posts that have images, or more than 320 words after formatting,
# or have already been made into a video. If that list is now empty, take the next x posts and repeat. Once you
# get a nonempty list, pick a post randomly and turn it into a video.
# also remove TIFUpdates


def scrape_posts():
    reddit_read_only = praw.Reddit(client_id='_',
                                   client_secret='_',
                                   user_agent='ReddReader by /u/Wide_Watercress3180'
                                   )
    subreddit = reddit_read_only.subreddit("tifu")
    posts = subreddit.top(time_filter="all", limit=150)
    posts_dict = {"Title": [], "Post Text": [],
                  "ID": [], "Score": [],
                  "Post URL": []
                  }
    dict_size = 0
    i = 0
    while dict_size == 0:
        if i == 1:
            posts = subreddit.top(time_filter="all", limit=150)
        elif i == 2:
            posts = subreddit.top(time_filter="all", limit=300)
        elif i == 3:
            posts = subreddit.top(time_filter="all", limit=600)
        elif i == 4:
            posts = subreddit.top(time_filter="all", limit=1000)
        elif i == 5:
            posts = subreddit.top(time_filter="year", limit=1000)
        elif i == 6:
            posts = subreddit.top(time_filter="month", limit=500)
        elif i == 7:
            posts = subreddit.top(time_filter="week", limit=150)
        elif i == 8:
            posts = subreddit.top(time_filter="day", limit=50)
        elif i > 8:
            print("Couldn't find a valid reddit post somehow. ")
        for post in posts:
            i += 1
            my_query: dict[str, int] = {"id": post.id}

            # get 1st quarter of text
            first_quarter = get_first_nth(post.selftext, 4)
            if (video_maker.get_no_words(video_maker.format_text(str(post.selftext))) > 20 and
                    "reddit" in str(post.url) and not
                    mongo.document_exists(my_query) and not
                    "update" in str(post.title).lower() and not
                first_quarter.upper().__contains__("TL;DR" or "TLDR" or "TL DR" or "UPDATE" or
                                                   "EDIT" or "KIND STRANGER" or "THANKS FOR THE GOLD")):
                dict_size += 1
                # Title of each post
                posts_dict["Title"].append(post.title)

                # Text inside a post
                posts_dict["Post Text"].append(post.selftext)

                # Unique ID of each post
                posts_dict["ID"].append(post.id)

                # The score of a post
                posts_dict["Score"].append(post.score)

                # URL of each post
                posts_dict["Post URL"].append(post.url)

            else:
                print(f"Post id {post.id} didnt make it lol")
    temp_list = list(posts_dict.values())
    randint = random.randint(0, dict_size-1)
    post = {
        "title": temp_list[0][randint],
        "selftext": temp_list[1][randint],
        "id": temp_list[2][randint],
        "score": temp_list[3][randint],
        "url": temp_list[4][randint]
    }
    try:
        title_card.create_title_card(post["title"])
        tifu_video = video(post["title"], post["selftext"])
        tifu_video.create_video()
        mongo.db.reddit_posts.insert_one({"id": post["id"]})
    except Exception as e:
        print(e)
        print("Couldn't make a video, or couldn't put the video in the db, or couldn't make a title card")


#Splits a string into N equal parts and returns the first Nth part
def get_first_nth(text, n):
    text_length = len(text)

    # Make sure it can be split into n equal parts. Just add space characters to the end until it divides nicely
    while text_length % n != 0:
        text += ' '
        text_length = len(text)

    part_size = int(text_length / n)
    return text[0: part_size]