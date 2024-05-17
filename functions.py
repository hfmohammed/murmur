import sys
import sqlite3
import getpass
import re
from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for

databaseName = "test.db"

def getHomeHtml(userId):
    html_content =  f"""
                        <a href="/home?userId={userId}">Home</a>
                    """
    return html_content

def getDate():
    date = datetime.now().strftime('%Y-%m-%d')
    print(date)

    return date


def getSearchUserHtml(loggedUser):
    return f"""
                <form action="/search_users?loggedUser={loggedUser}" method="post">
                    <label for="keyword">Search Users</label><br>
                    <input type="text" id="keyword" name="keyword"><br>

                    <input type="submit" value="search user">
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


def getSearchTweetHtml(loggedUser):
    return f"""
                <form action="/search_tweets?loggedUser={loggedUser}" method="post">
                    <label for="keyword">Search Tweets</label><br>
                    <input type="text" id="keyword" name="keyword"><br>

                    <input type="submit" value="search tweet">
                </form>
            """


def getFollowers(usr):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    # Select followers for the user
    cursor.execute("""
                        SELECT f.flwer, u.name, u.city
                        FROM follows f, users u
                        WHERE f.flwer = u.usr AND
                        f.flwee = ?
                    """, (usr,))
    followers = cursor.fetchall()
    return followers


def htmlifyUsers(data, loggedUser):
    html_content = ""

    for i in data:
        userId, name, city = i
        html_content += f"""
                            <a href="/user?usr={userId}&name={name}&loggedUser={loggedUser}" data-userId={userId}>{userId}: {name}</a>
                        """

    return html_content


def getRecentTweets(usr):
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
        (usr, usr)
    )

    recent_tweets = cursor.fetchall()

    conn.close()
    return recent_tweets


def getFollow_html(usr, loggedUser):
    html_content = f"""
                        <a href="/followUser?loggedUser={loggedUser}&usr={usr}">Follow</a>
                    """
    return html_content


def follow(current_usr, follower_usr):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    tdate = getDate()
    try:
        cursor.execute("INSERT INTO follows VALUES (? , ?, ?)",
                       (current_usr, follower_usr, tdate))
        conn.commit()
        print("added")
    except sqlite3.IntegrityError:
        print("alrIn")
        pass
    conn.close()


def getUserDetails(usr):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) 
        FROM tweets 
        WHERE writer = ?
        """, (usr,))
    tweet_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM follows
        WHERE flwer = ?
        """, (usr,))
    following_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM follows
        WHERE flwee = ?
        """, (usr,))
    followers_count = cursor.fetchone()[0]

    conn.close()
    return tweet_count, following_count, followers_count


def _htmlifyTweet(usr, tid, writer, date, text, replyto, _type="", retweeter=""):
    element = f"""
                <div data-tid="{tid}" data-writer="{writer}" data-date="{date}" data-text="{text}" data-replyto="{replyto}" data-_type="{_type}" data-retweeter="{retweeter}">
                    <p>{replyto} {_type} {retweeter}</p>
                    <p>{date}, {writer}</p>
                    <a href="/tweets?tid={tid}&usr={usr}">{text}</a>
                </div>
                <br>
                """
    return element


def _retweet(usr, tid):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()
    tdate = getDate()
    cursor.execute(
        """
        INSERT INTO retweets VALUES (?, ?, ?);
        """, (usr, tid, tdate))
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


def _htmlifyTweetDetails(usr, tid, replyCount, retweetCount, tweetDetails):
    writer = tweetDetails[0][1]
    date = tweetDetails[0][2]
    text = tweetDetails[0][3]
    replyto = tweetDetails[0][4]

    element = f"""
                <div data-tid="{tid}">
                    <p>Author: {writer} date: {date}, reply to: {replyto}</p>
                    <p>{text}<p>
                    <p>replies: {replyCount}  ||  retweets: {retweetCount}<p>
                    <a href="/composeTweet?usr={usr}&replyto={tid}">reply</a>
                    <a href="/retweet?usr={usr}&tid={tid}">retweet</a>
                </div>\n
                """
    return element


def getTweetStats(userId, tid):
    replyCount = getRepliesCount(tid)
    retweetCount = getRetweetsCount(tid)
    tweetDetails = getTweetDetails(tid)

    html_content = _htmlifyTweetDetails(
        userId, tid, replyCount, retweetCount, tweetDetails)

    return html_content


def htmlifyTweets(usr, data):
    htmlContent = ""

    for i in data:
        try:
            tid, writer, date, text, replyto, _type, retweeter = i
            htmlContent += _htmlifyTweet(usr, tid, writer,
                                         date, text, replyto, _type, retweeter)
        except:
            try:
                tid, writer, date, text, replyto, _type = i
                htmlContent += _htmlifyTweet(usr, tid, writer,
                                             date, text, replyto, _type)
            except:
                tid, writer, date, text, replyto = i
                htmlContent += _htmlifyTweet(usr, tid, writer,
                                             date, text, replyto)

    return htmlContent


def retrieve_flwee_tweets(usr):
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
        """, (usr, usr))
    data = cursor.fetchall()

    conn.close()
    return data


def createUser(userId, password, name, email, city, timezone):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                   (userId, password, name, email, city, timezone))
    conn.commit()
    conn.close()
    return "Success"


def usernameExists(usr):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE usr = ?", (usr,))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def pullUserData(usr):
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE usr = ?", (usr,))
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


def getComposeTweetHtml(usr):
    html_content = f"""
                        <a href="/composeTweet?usr={usr}&replyto=NULL">Compose Tweet</a>
                    """
    return html_content


def getListFollowersHtml(usr):
    html_content = f"""
                        <a href="/listFollowers?usr={usr}">List Followers</a>
                    """
    return html_content


def pushTweet(writer_id, tweetText, replyTo):
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
                       (tweet_id, writer_id, tdate, tweetText, replyTo))

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
