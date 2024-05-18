import sys
import sqlite3
import getpass
import re
from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, session

databaseName = "test.db"


def getHomeHtml():
    html_content = f"""
                        <form action="/home" class="header-form">
                            <button type="submit">Home</button>
                        </form>
                    """
    return html_content


def getDate():
    date = datetime.now().strftime('%Y-%m-%d')
    # print(date)

    return date


def getSearchUserHtml():
    return f"""
                <form action="/search_users" method="post" class="header-form">
                    <label for="user-search" class="visually-hidden">Search Users</label>
                    <input type="text" id="user-search" name="keyword" placeholder="Search Users">
                    <button type="submit">Search</button>
                </form>
            """


def searchTweets(keywords):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    keywords = keywords.split()
    query = """
            SELECT tid, writer, tdate, text, replyto
            FROM tweets
            WHERE tweets.text LIKE ? COLLATE NOCASE
            """

    hashtagQuery = """
                SELECT t.tid, t.writer, t.tdate, t.text, t.replyto
                FROM mentions m
                JOIN tweets t ON m.tid = t.tid
                WHERE m.term = ? COLLATE NOCASE
                """

    matching_tweets = set()
    for keyword in keywords:
        if keyword[0] == '#':
            keyword = keyword[1:]
            cursor.execute(hashtagQuery, (keyword,))
        else:
            cursor.execute(query, (f"%{keyword}%",))
        matching_tweets.update(cursor.fetchall())

    matching_tweets = sorted(
        matching_tweets, key=lambda tweet: tweet[2], reverse=True)

    conn.close()
    return matching_tweets


def getSearchTweetHtml():
    return f"""
                <form action="/search_tweets" method="post" class="header-form">
                    <label for="tweet-search" class="visually-hidden">Search Tweets</label>
                    <input type="text" id="tweet-search" name="keyword" placeholder="Search Tweets">
                    <button type="submit">Search</button>
                </form>
            """


def getFollowers():
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()
    loggedUser = session.get('loggedUser')

    # Select followers for the user
    cursor.execute("""
                        SELECT f.flwer, u.name, u.city
                        FROM follows f, users u
                        WHERE f.flwer = u.usr AND
                        f.flwee = ?
                    """, (loggedUser,))
    followers = cursor.fetchall()
    return followers


def getRecentTweets(visitingUser):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
        Combined.tid, 
        Combined.writer, 
        MAX(Combined.dateSort) AS dateSort, 
        Combined.text, 
        Combined.replyto, 
        Combined.type
        FROM (
            SELECT 
                t.tid, 
                t.writer, 
                t.tdate AS dateSort, 
                t.text, 
                t.replyto, 
                'tweet' AS type,
                t.writer AS retweeter
            FROM tweets t
            WHERE t.writer = ?
            UNION ALL

            SELECT 
                t.tid, 
                t.writer AS writer, 
                rt.rdate AS dateSort, 
                t.text, 
                t.replyto, 
                'retweet' AS type,
                rt.usr AS retweeter
            FROM retweets rt
            JOIN tweets t ON rt.tid = t.tid
            WhERE rt.usr = ?
            ) AS Combined
        GROUP BY Combined.tid, Combined.writer, combined.retweeter
        ORDER BY dateSort DESC;
        """,
        (visitingUser, visitingUser)
    )

    recent_tweets = cursor.fetchall()

    conn.close()
    return recent_tweets


def follow(loggedUser, visitingUser):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()
    result = 0

    tdate = getDate()
    try:
        cursor.execute("INSERT INTO follows VALUES (? , ?, ?)",
                       (loggedUser, visitingUser, tdate))
        conn.commit()
        result  = 1
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return result


def getUserDetails(visitingUser):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) 
        FROM tweets 
        WHERE writer = ?
        """, (visitingUser,))
    tweet_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM follows
        WHERE flwer = ?
        """, (visitingUser,))
    following_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM follows
        WHERE flwee = ?
        """, (visitingUser,))
    followers_count = cursor.fetchone()[0]

    conn.close()
    return tweet_count, following_count, followers_count


def _htmlifyTweet(tid, writer, date, text):
    element = f"""
                    <a href="/tweets?tid={tid}" class="tweet-link">
                        <div data-tid="{tid}">
                            <p style="text-align: center; font-weight: bold;">Written by {writer} on {date}</p>
                            <br>
                            <p>{text}</p>
                        </div>
                    </a>
                    <br>
                """
    return element


def _htmlifyUser(visitingUser, visitingUserName):
    element = f"""
                <a href="/user?visitingUser={visitingUser}&visitingUserName={visitingUserName}" class="tweet-link">
                    <div data-uid="{visitingUser}">
                        <p>{visitingUser}: {visitingUserName}</p>
                    </div>
                </a>
                <br>
            """
    return element


def _retweet(tid):
    loggedUser = session.get('loggedUser')
    tdate = getDate()

    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO retweets VALUES (?, ?, ?);
        """, (loggedUser, tid, tdate))
    conn.commit()
    conn.close()


def getTweetDetails(tid):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tweets WHERE tid = ?", (tid,))
    data = cursor.fetchall()
    conn.close()
    return data


def getRepliesCount(tid):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT count(*)
        FROM tweets t1
        LEFT JOIN tweets t2 ON t1.tid = t2.replyto
        WHERE t1.replyto = ?;
        """, (tid, ))

    data = cursor.fetchall()[0][0]
    conn.close()

    return data


def getRetweetsCount(tid):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT count(r.tid) AS retweet_count
        FROM tweets t
        LEFT JOIN retweets r ON t.tid = r.tid
        WHERE t.tid = ?
        GROUP BY t.tid
        ORDER BY t.tid;
        """, (tid, ))

    data = cursor.fetchall()[0][0]
    conn.close()

    return data


def getRetweetHtml(tid):
    loggedUser = session.get('loggedUser')
    html_content = f"""
                        <form action="/retweet?tid={tid}" method="post" class="header-form">
                            <input type="hidden" name="usr" value="{ loggedUser }">
                            <button type="submit">Retweet</button>
                        </form>
                    """
    return html_content


def _htmlifyTweetDetails(tid, replyCount, retweetCount, tweetDetails):
    writer = tweetDetails[0][1]
    date = tweetDetails[0][2]
    text = tweetDetails[0][3]
    replyto = tweetDetails[0][4]

    replyHtml = getComposeTweetHtml(replyto=tid)
    retweetHtml = getRetweetHtml(tid)

    element = f"""
                <div data-tid="{tid}">
                    <p style="text-align: center; font-weight: bold;">{writer} replied to {replyto} on {date}</p>
                    <p>{text}</p>
                    <p>replies: {replyCount}  ||  retweets: {retweetCount}</p>

                    <br>

                    <div style="display: flex; justify-content: center;">
                        <div style="flex: 1; display: flex; justify-content: center; margin: 0 10px;">
                            {replyHtml}
                        </div>
                        <div style="flex: 1; display: flex; justify-content: center; margin: 0 10px;">
                            {retweetHtml}
                        </div>
                    </div>
                </div>\n
                """
    return element


def getTweetStats(tid):
    replyCount = getRepliesCount(tid)
    retweetCount = getRetweetsCount(tid)
    tweetDetails = getTweetDetails(tid)

    html_content = _htmlifyTweetDetails(
        tid, replyCount, retweetCount, tweetDetails)

    return html_content


def showNoData(e):
    html_content = f"""
                    <div class="tweet-link">
                        <div data-tid="noData">
                            <p style="text-align: center; font-weight: bold;">No {e} available</p>
                            <br>
                        </div>
                    </div>
                    """
    return html_content


def htmlifyTweets(data):
    html_content = ""
    if len(data) == 0:
        html_content += showNoData("tweets")
    else:
        for i in data:
            try:
                tid, writer, date, text, replyto, _type, retweeter = i

            except:
                try:
                    tid, writer, date, text, replyto, _type = i

                except:
                    tid, writer, date, text, replyto = i
            html_content += _htmlifyTweet(tid, writer, date, text)

    return html_content


def htmlifyUsers(data):
    html_content = ""
    if len(data) == 0:
        html_content += showNoData("users")
    else:
        for i in data:
            visitingUser, visitingUserName, city = i
            html_content += _htmlifyUser(visitingUser, visitingUserName)
    return html_content


def retrieve_flwee_tweets():
    loggedUser = session.get('loggedUser')
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 
        Combined.tid, 
        Combined.writer, 
        MAX(Combined.dateSort) AS dateSort, 
        Combined.text, 
        Combined.replyto, 
        Combined.type,
        combined.retweeter
        FROM (
            SELECT 
                t.tid, 
                t.writer, 
                t.tdate AS dateSort, 
                t.text, 
                t.replyto, 
                'tweet' AS type,
                t.writer AS retweeter
            FROM tweets t
            JOIN follows f ON f.flwee = t.writer
            WHERE f.flwer = ?

            UNION ALL

            SELECT 
                t.tid, 
                t.writer AS writer, 
                rt.rdate AS dateSort, 
                t.text, 
                t.replyto, 
                'retweet' AS type,
                rt.usr AS retweeter
            FROM retweets rt
            JOIN tweets t ON rt.tid = t.tid
            JOIN follows f ON f.flwee = rt.usr
            WHERE f.flwer = ?
            ) AS Combined
        GROUP BY Combined.tid, Combined.writer, combined.retweeter
        ORDER BY dateSort DESC;
        """, (loggedUser, loggedUser))
    data = cursor.fetchall()

    conn.close()
    return data


def createUser(loggedUser, password, name, email, city, timezone):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                   (loggedUser, password, name, email, city, timezone))
    conn.commit()
    conn.close()
    return "Success"


def usernameExists(loggedUser):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE usr = ?", (loggedUser,))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def pullUserData(loggedUser):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE usr = ?", (loggedUser,))
    row = cursor.fetchone()

    conn.close()
    return row


def searchUsers(keyword):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    data = []
    cursor.execute(
        """
        SELECT usr, name, city
        FROM users
        WHERE usr LIKE ? COLLATE NOCASE OR
            name LIKE ? COLLATE NOCASE
        ORDER BY LENGTH(name), name ASC
        """,
        (f"%{keyword}%", f"%{keyword}%")
    )

    data.extend(cursor.fetchall())

    results = cursor.fetchall()
    for row in results:
        if row not in data:
            data.append(row)

    conn.close()
    return data


def getComposeTweetHtml(replyto="None"):
    buttonText = "Write a Tweet"

    if replyto != "None":
        buttonText = "Reply"

    html_content = f"""
                        <form action="/composeTweet" method="post" class="header-form">
                            <input type="hidden" name="replyto" value="{ replyto }">
                            <button type="submit">{buttonText}</button>
                        </form>
                    """
    return html_content


def getListFollowersHtml():
    html_content = f"""
                        <form action="/followers" class="header-form">
                            <button type="submit">My Followers</button>
                        </form>
                    """
    return html_content


def pushTweet(writer_id, tweetText, replyto):
    tdate = getDate()
    hashtags = re.findall(r"#(\w+)", tweetText)

    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    # Start transaction
    conn.execute("BEGIN TRANSACTION")

    try:
        # Fetch the highest tweet ID from the tweets table
        cursor.execute("SELECT MAX(tid) FROM tweets")
        max_id = cursor.fetchone()[0]
        tweet_id = max_id + 1 if max_id is not None else 1

        # Insert the tweet with the calculated tweet ID
        cursor.execute("INSERT INTO tweets (tid, writer, tdate, text, replyto) VALUES (?, ?, ?, ?, ?)",
                       (tweet_id, writer_id, tdate, tweetText, replyto))

        # Insert hashtags and their associations with the tweet
        for i in range(len(hashtags)):
            # Ensure the hashtag is stored in the hashtags table
            hashtags[i] = hashtags[i].lower()
            cursor.execute(
                "INSERT OR IGNORE INTO hashtags (term) VALUES (?)", (hashtags[i],))

            # Insert the association of the tweet with the hashtag
            cursor.execute(
                "INSERT INTO mentions (tid, term) VALUES (?, ?)", (tweet_id, hashtags[i]))

            # print(f"Inserted mention with tweet ID: {tweet_id} and hashtag: {tag}")  # Debugging line

        # Commit the transaction if everything is successful
        conn.commit()
        conn.close()

    except sqlite3.IntegrityError as e:
        # Rollback the transaction if any error occurs
        conn.rollback()
