import sys
import sqlite3
import getpass
import re
from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, session
import functions

app = Flask(__name__)
app.secret_key = "test"

databaseName = "test.db"

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/approve_signup', methods=["POST"])
def approve_signup():
    loggedUser = request.form['username']
    password = request.form['password']
    loggedUserName = request.form['loggedUserName']
    email = request.form['email']
    city = request.form['city']
    timezone = 1

    if not functions.usernameExists(loggedUser):
        if functions.createUser(loggedUser, password, loggedUserName, email, city, timezone):
            session['loggedUser'] = loggedUser
            return redirect(url_for('home'))
    return redirect(url_for('signup'))

@app.route('/login')
def login():
    session.clear()
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')


@app.route('/approve_login', methods=["POST"])
def approve_login():
    loggedUser = request.form['username']
    password = request.form['password']

    if not functions.usernameExists(loggedUser):
        return redirect(url_for('login'))
    else:
        print("_________Approving__________")
        userData = functions.pullUserData(loggedUser)
        expectedPassword = userData[1]
        if expectedPassword != password:
            return redirect(url_for('login'))
        
        # Store loggedUser in session
        print("_____Logging in_____")
        session['loggedUser'] = loggedUser
        return redirect(url_for('home'))


@app.route('/tweets')
def tweets():
    tid = request.args.get('tid')

    html_content = functions.getTweetStats(tid)

    _getSearchUserHtml = functions.getSearchUserHtml()
    _getHomeHtml = functions.getHomeHtml()
    _getSearchTweetHtml = functions.getSearchTweetHtml()
    _getListFollowersHtml = functions.getListFollowersHtml()

    composeTweetHtml = functions.getComposeTweetHtml(tid)

    return render_template('tweets.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/retweet', methods=["POST"])
def retweet():
    tid = request.args.get('tid')

    try:
        functions._retweet(tid)
    except:
        pass

    print("_____Retweeted_____")
    return redirect(url_for('tweets', tid=tid))


@app.route('/composeTweet', methods=["POST"])
def composeTweet():
    loggedUser = session["loggedUser"]
    replyto = request.form["replyto"]
    print(loggedUser)

    _getSearchUserHtml = functions.getSearchUserHtml()
    _getSearchTweetHtml = functions.getSearchTweetHtml()
    _getListFollowersHtml = functions.getListFollowersHtml()
    _getHomeHtml = functions.getHomeHtml()

    formElement = f"""
                    <form action="/_composeTweet" method="post" class="tweet-form">
                        <input type="hidden" name="replyto" value="{ replyto }">
    
                        <label for="tweet"></label><br>
                        <textarea type="text" class="large-input" placeholder="Share your thoughts with the world..." id="tweet" name="tweet"></textarea>
                        <br>
                        <input type="submit" value="Tweet">
                    </form>
                    """

    return render_template('composeTweet.html', formElement=formElement, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/_composeTweet', methods=["POST"])
def _composeTweet():
    loggedUser = session["loggedUser"]
    replyto = request.form['replyto']
    tweetText = request.form['tweet']

    print("_____Pushing the Tweet_____")
    functions.pushTweet(loggedUser, tweetText, replyto)
    print("_____Tweet Pushed_____")

    print("replyto", replyto)
    if replyto != "None":
        return redirect(url_for('tweets', tid=replyto))
    else:
        return redirect(url_for('home'))


@app.route('/followUser', methods=["GET", "POST"])
def followUser():
    visitingUser = request.args.get('visitingUser')
    visitingUserName = request.args.get('visitingUserName')
    print("Attempting to follow:", visitingUser, visitingUserName)
    
    loggedUser = session.get('loggedUser')
    
    functions.follow(loggedUser, visitingUser)

    return redirect(url_for('user', visitingUser=visitingUser, visitingUserName=visitingUserName ))


def htmlUser(visitingUser, visitingUserName, tweet_count, following_count, followers_count, usersHtml):
    print("check:", visitingUser, visitingUserName)
    html_content = f"""
                        <div class="user-info-div">
                            <div class="user-info">
                                <p>Username: { visitingUser } || Name: { visitingUserName }</p>
                                <Following:>Number of Tweets: { tweet_count } || Following: { following_count } || Followers: { followers_count }</p>
                            </div>
                            <form action="/followUser?visitingUser={visitingUser}&visitingUserName={visitingUserName}" method="post" class="header-form">
                                <button>Follow</button>
                            </form>
                        </div>
                    
                        <div class="users-container">
                            { usersHtml }
                        </div>
                    """
    return html_content


@app.route('/user')
def user():
    print("_____Opening User_____")
    
    visitingUser = request.args.get('visitingUser')
    visitingUserName = request.args.get('visitingUserName')

    tweet_count, following_count, followers_count = functions.getUserDetails(visitingUser)

    recentTweets = functions.getRecentTweets(visitingUser)

    _tweetsHtml = functions.htmlifyTweets(recentTweets)

    composeTweetHtml = functions.getComposeTweetHtml()
    _getSearchUserHtml = functions.getSearchUserHtml()
    _getHomeHtml = functions.getHomeHtml()
    _getSearchTweetHtml = functions.getSearchTweetHtml()
    _getListFollowersHtml = functions.getListFollowersHtml()

    html_content = htmlUser(visitingUser, visitingUserName, tweet_count,
                            following_count, followers_count, _tweetsHtml)

    return render_template('user.html', homeHtml=_getHomeHtml, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, html_content=html_content)


@app.route('/search_users', methods=["POST"])
def search_users():
    loggedUser = request.args.get('loggedUser')
    keyword = request.form['keyword']
    data = functions.searchUsers(keyword)

    html_content = functions.htmlifyUsers(data)

    composeTweetHtml = functions.getComposeTweetHtml()
    _getSearchUserHtml = functions.getSearchUserHtml()
    _getHomeHtml = functions.getHomeHtml()
    _getSearchTweetHtml = functions.getSearchTweetHtml()
    _getListFollowersHtml = functions.getListFollowersHtml()

    return render_template('searchUsers.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/search_tweets', methods=["POST"])
def search_tweets():
    loggedUser = request.args.get('loggedUser')
    keyword = request.form['keyword']

    data = functions.searchTweets(keyword)

    html_content = functions.htmlifyTweets(data)
    composeTweetHtml = functions.getComposeTweetHtml()
    _getSearchUserHtml = functions.getSearchUserHtml()
    _getHomeHtml = functions.getHomeHtml()
    _getSearchTweetHtml = functions.getSearchTweetHtml()
    _getListFollowersHtml = functions.getListFollowersHtml()

    return render_template('searchTweets.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/followers')
def listFollowers():
    loggedUser = session.get('loggedUser')

    data = functions.getFollowers()
    html_content = functions.htmlifyUsers(data)

    composeTweetHtml = functions.getComposeTweetHtml()
    _getSearchUserHtml = functions.getSearchUserHtml()
    _getHomeHtml = functions.getHomeHtml()
    _getSearchTweetHtml = functions.getSearchTweetHtml()

    return render_template('followers.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, homeHtml=_getHomeHtml, searchTweet=_getSearchTweetHtml)


@app.route('/home')
def home():
    loggedUser = session.get('loggedUser')

    if loggedUser is None:
        return redirect(url_for('login'))
    else:
        print("Logged In")
        data = functions.retrieve_flwee_tweets()

        html_content = functions.htmlifyTweets(data)

        composeTweetHtml = functions.getComposeTweetHtml()
        _getSearchUserHtml = functions.getSearchUserHtml()
        _getSearchTweetHtml = functions.getSearchTweetHtml()
        _getListFollowersHtml = functions.getListFollowersHtml()

        return render_template('home.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml)


if __name__ == '__main__':
    app.run(port=5001)
