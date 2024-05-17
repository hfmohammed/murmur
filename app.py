import sys
import sqlite3
import getpass
import re
from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for
import functions
app = Flask(__name__)

databaseName = "test.db"


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/approve_signup', methods=["POST"])
def approve_signup():
    userId = request.form['username']
    password = request.form['password']
    name = request.form['name']
    email = request.form['email']
    city = request.form['city']
    timezone = 1

    if not functions.usernameExists(userId):
        if functions.createUser(userId, password, name, email, city, timezone):
            return redirect(url_for('home', userId=userId))
    return redirect(url_for('signup'))


@app.route('/login')
def login():
    cacheData = True
    if cacheData:
        return render_template('login.html')


@app.route('/approve_login', methods=["POST"])
def approve_login():
    userId = request.form['username']
    password = request.form['password']

    if not functions.usernameExists(userId):
        return redirect(url_for('login'))
    else:
        userData = functions.pullUserData(userId)
        expectedPassword = userData[1]
        if expectedPassword != password:
            return redirect(url_for('login'))
        return redirect(url_for('home', userId=userId))


@app.route('/tweets')
def tweets():
    tid = request.args.get('tid')
    userId = request.args.get('usr')

    html_content = functions.getTweetStats(userId, tid)
    composeTweetHtml = functions.getComposeTweetHtml(userId)
    _getSearchUserHtml = functions.getSearchUserHtml(userId)
    _getHomeHtml = functions.getHomeHtml(userId)
    _getSearchTweetHtml = functions.getSearchTweetHtml(userId)
    _getListFollowersHtml = functions.getListFollowersHtml(userId)

    return render_template('searchTweets.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/retweet')
def retweet():
    tid = request.args.get('tid')
    userId = request.args.get('usr')
    print(userId)
    try:
        functions._retweet(userId, tid)
    except:
        pass
    return redirect(url_for('tweets', usr=userId, tid=tid))


@app.route('/composeTweet')
def composeTweet():

    usr = request.args.get('usr')
    replyto = request.args.get('replyto')

    _getSearchUserHtml = functions.getSearchUserHtml(usr)
    _getSearchTweetHtml = functions.getSearchTweetHtml(usr)
    _getListFollowersHtml = functions.getListFollowersHtml(usr)
    _getHomeHtml = functions.getHomeHtml(usr)

    formElement = f"""
                        <form action="/_composeTweet?usr={usr}&replyto={replyto}" method="post">
                            <label for="tweet">Text</label><br>
                            <input type="text" id="tweet" name="tweet"><br>

                            <input type="submit" value="Tweet">
                        </form>
                    """

    return render_template('composeTweet.html', formElement=formElement, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/_composeTweet', methods=["POST"])
def _composeTweet():
    usr = request.args.get('usr')
    replyTo = request.args.get('replyto')
    tweetText = request.form['tweet']
    functions.pushTweet(usr, tweetText, replyTo)

    if replyTo != "NULL":
        return redirect(url_for('tweets', usr=usr, tid=replyTo))
    else:
        return redirect(url_for('home', userId=usr))


@app.route('/followUser')
def followUser():
    usr = request.args.get('usr')
    loggedUser = request.args.get('loggedUser')
    functions.follow(loggedUser, usr)

    return redirect(url_for('home', userId=loggedUser))


def htmlUser(username, name, follow_html, tweet_count, following_count, followers_count, tweetsHtml):
    html_content =  f"""
                        <div>
                            <p>Username: { username } || Name: { name }</p>
                            { follow_html }
                            <p>Number of Tweets: { tweet_count }</p>
                            <p>Following: { following_count }</p>
                            <p>Followers: { followers_count }</p>
                        </div>
                    
                        <div>
                            { tweetsHtml }
                        </div>
                    """
    return html_content


@app.route('/user')
def user():
    usr = request.args.get('usr')
    loggedUser = request.args.get('loggedUser')
    name = request.args.get('name')

    tweet_count, following_count, followers_count = functions.getUserDetails(
        usr)

    recentTweets = functions.getRecentTweets(usr)

    _tweetsHtml = functions.htmlifyTweets(loggedUser, recentTweets)
    follow_html = functions.getFollow_html(usr, loggedUser)

    composeTweetHtml = functions.getComposeTweetHtml(loggedUser)
    _getSearchUserHtml = functions.getSearchUserHtml(loggedUser)
    _getHomeHtml = functions.getHomeHtml(loggedUser)
    _getSearchTweetHtml = functions.getSearchTweetHtml(loggedUser)
    _getListFollowersHtml = functions.getListFollowersHtml(loggedUser)

    html_content = htmlUser(usr, name, follow_html, tweet_count, following_count, followers_count, _tweetsHtml)

    return render_template('user.html', homeHtml=_getHomeHtml, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, htmlContent=html_content)


@app.route('/search_users', methods=["POST"])
def search_users():
    loggedUser = request.args.get('loggedUser')
    keyword = request.form['keyword']
    data = functions.searchUsers(keyword)

    html_content = functions.htmlifyUsers(data, loggedUser)

    composeTweetHtml = functions.getComposeTweetHtml(loggedUser)
    _getSearchUserHtml = functions.getSearchUserHtml(loggedUser)
    _getHomeHtml = functions.getHomeHtml(loggedUser)
    _getSearchTweetHtml = functions.getSearchTweetHtml(loggedUser)
    _getListFollowersHtml = functions.getListFollowersHtml(loggedUser)

    return render_template('searchUsers.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/search_tweets', methods=["POST"])
def search_tweets():
    loggedUser = request.args.get('loggedUser')
    keyword = request.form['keyword']

    data = functions.searchTweets(keyword)

    html_content = functions.htmlifyTweets(loggedUser, data)
    composeTweetHtml = functions.getComposeTweetHtml(loggedUser)
    _getSearchUserHtml = functions.getSearchUserHtml(loggedUser)
    _getHomeHtml = functions.getHomeHtml(loggedUser)
    _getSearchTweetHtml = functions.getSearchTweetHtml(loggedUser)
    _getListFollowersHtml = functions.getListFollowersHtml(loggedUser)

    return render_template('searchTweets.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/listFollowers')
def listFollowers():
    userId = request.args.get('usr')

    data = functions.getFollowers(userId)

    html_content = functions.htmlifyUsers(data, userId)

    composeTweetHtml = functions.getComposeTweetHtml(userId)
    _getSearchUserHtml = functions.getSearchUserHtml(userId)
    _getHomeHtml = functions.getHomeHtml(userId)
    _getSearchTweetHtml = functions.getSearchTweetHtml(userId)

    return render_template('listFollowers.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, homeHtml=_getHomeHtml, searchTweet=_getSearchTweetHtml)


@app.route('/home')
def home():
    userId = request.args.get('userId')
    data = functions.retrieve_flwee_tweets(userId)

    html_content = functions.htmlifyTweets(userId, data)
    composeTweetHtml = functions.getComposeTweetHtml(userId)
    _getSearchUserHtml = functions.getSearchUserHtml(userId)
    _getSearchTweetHtml = functions.getSearchTweetHtml(userId)
    _getListFollowersHtml = functions.getListFollowersHtml(userId)

    return render_template('home.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml)


if __name__ == '__main__':
    app.run(port=5001)
