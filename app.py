from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import helperFunctions as hf
import hashlib

app = Flask(__name__)
app.secret_key = "test"
databaseName = "twitterClone.db"


@app.route('/approve_login', methods=["POST"])
def approve_login():
    loggedUser = request.form['username']
    password = request.form['password']
    password = hashlib.sha256(password.encode()).hexdigest()

    error_message = "Username or password does not match our records"

    if not hf.usernameExists(loggedUser):
        flash(error_message)
        # print("Flashed error: username does not exist")
        return redirect(url_for('login'))
    else:
        # print("_________Approving__________")
        userData = hf.pullUserData(loggedUser)
        expectedPassword = userData[1]

        if expectedPassword != password:
            flash(error_message)
            # print("Flashed error: username does not exist")
            return redirect(url_for('login'))

        # Store loggedUser in session
        # print("_____Logging in_____")
        session['loggedUser'] = loggedUser
        return redirect(url_for('home'))


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/check_username', methods=["GET"])
def check_username():
    username = request.args.get('username')
    if hf.usernameExists(username):
        return jsonify(available=False)
    else:
        return jsonify(available=True)


@app.route('/approve_signup', methods=["POST"])
def approve_signup():
    loggedUser = request.form['username']
    password = request.form['password']
    password = hashlib.sha256(password.encode()).hexdigest()
    print(password)
    print(len(password))
    loggedUserName = request.form['name']
    email = request.form['email']
    city = request.form['city']

    if not hf.usernameExists(loggedUser):
        if hf.createUser(loggedUser, password, loggedUserName, email, city):
            session['loggedUser'] = loggedUser
            flash("Welcome, your account has been successfully created!")
            return redirect(url_for('home'))
    return redirect(url_for('signup'))


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/tweets')
def tweets():
    tid = request.args.get('tid')

    html_content = hf.getTweetStats(tid)

    _getSearchUserHtml = hf.getSearchUserHtml()
    _getHomeHtml = hf.getHomeHtml()
    _getSearchTweetHtml = hf.getSearchTweetHtml()
    _getListFollowersHtml = hf.getListFollowersHtml()

    composeTweetHtml = hf.getComposeTweetHtml(tid)

    return render_template('tweets.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/retweet', methods=["POST"])
def retweet():
    tid = request.args.get('tid')

    try:
        hf._retweet(tid)
        flash("Retweeted successfully!")
    except:
        flash("You have already retweeted this tweet!")

    # print("_____Retweeted_____")
    return redirect(url_for('tweets', tid=tid))


@app.route('/composeTweet', methods=["POST"])
def composeTweet():
    replyto = request.form["replyto"]
    # print(loggedUser)

    _getSearchUserHtml = hf.getSearchUserHtml()
    _getSearchTweetHtml = hf.getSearchTweetHtml()
    _getListFollowersHtml = hf.getListFollowersHtml()
    _getHomeHtml = hf.getHomeHtml()

    url = ""
    if replyto != "None":
        url = f"tweets?tid={replyto}"
    else:
        url = f"home"

    formElement = f"""
                    <a href="{url}"><i class="fa fa-arrow-left"></i> Back</a>
                    <br>
                    <br>
                    <form action="/_composeTweet" method="post" class="tweet-form">
                        <input type="hidden" name="replyto" value="{ replyto }">
    
                        <label for="tweet"></label>

                        <textarea type="text" class="large-input" placeholder="Share your thoughts with the world..." id="tweet" name="tweet"></textarea>
                        

                        <p id="char-count">0/500</p>
                        <p id="error-message" style="color:red; display:none;">Your tweet exceeds 500 characters!</p>

                        <input type="submit" value="Tweet" id="tweet-button">
                    </form>
                    """

    return render_template('composeTweet.html', formElement=formElement, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/_composeTweet', methods=["POST"])
def _composeTweet():
    loggedUser = session["loggedUser"]
    replyto = request.form['replyto']
    tweetText = request.form['tweet']

    # print("_____Pushing the Tweet_____")
    hf.pushTweet(loggedUser, tweetText, replyto)
    # print("_____Tweet Pushed_____")

    # print("replyto", replyto)
    if replyto != "None":
        flash("Your reply has been posted.")
        return redirect(url_for('tweets', tid=replyto))
    else:
        flash("Your tweet has been posted successfully.")
        return redirect(url_for('home'))


@app.route('/followUser', methods=["GET", "POST"])
def followUser():
    visitingUser = request.args.get('visitingUser')
    visitingUserName = request.args.get('visitingUserName')
    # print("Attempting to follow:", visitingUser, visitingUserName)

    loggedUser = session.get('loggedUser')

    if hf.follow(loggedUser, visitingUser):
        flash(f"You are now following {visitingUserName}")
    else:
        flash(f"You are already following {visitingUserName}")

    return redirect(url_for('user', visitingUser=visitingUser, visitingUserName=visitingUserName))


def htmlUser(visitingUser, visitingUserName, tweet_count, following_count, followers_count, usersHtml):
    # print("check:", visitingUser, visitingUserName)
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
    # print("_____Opening User_____")

    visitingUser = request.args.get('visitingUser')
    visitingUserName = request.args.get('visitingUserName')

    tweet_count, following_count, followers_count = hf.getUserDetails(
        visitingUser)

    recentTweets = hf.getRecentTweets(visitingUser)

    _tweetsHtml = hf.htmlifyTweets(recentTweets)

    composeTweetHtml = hf.getComposeTweetHtml()
    _getSearchUserHtml = hf.getSearchUserHtml()
    _getHomeHtml = hf.getHomeHtml()
    _getSearchTweetHtml = hf.getSearchTweetHtml()
    _getListFollowersHtml = hf.getListFollowersHtml()

    html_content = htmlUser(visitingUser, visitingUserName, tweet_count,
                            following_count, followers_count, _tweetsHtml)

    return render_template('user.html', homeHtml=_getHomeHtml, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, html_content=html_content)


@app.route('/search_users', methods=["POST"])
def search_users():

    keyword = request.form['keyword']
    data = hf.searchUsers(keyword)

    html_content = hf.htmlifyUsers(data)

    composeTweetHtml = hf.getComposeTweetHtml()
    _getSearchUserHtml = hf.getSearchUserHtml()
    _getHomeHtml = hf.getHomeHtml()
    _getSearchTweetHtml = hf.getSearchTweetHtml()
    _getListFollowersHtml = hf.getListFollowersHtml()

    return render_template('searchUsers.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/search_tweets', methods=["POST"])
def search_tweets():

    keyword = request.form['keyword']

    data = hf.searchTweets(keyword)

    html_content = hf.htmlifyTweets(data)
    composeTweetHtml = hf.getComposeTweetHtml()
    _getSearchUserHtml = hf.getSearchUserHtml()
    _getHomeHtml = hf.getHomeHtml()
    _getSearchTweetHtml = hf.getSearchTweetHtml()
    _getListFollowersHtml = hf.getListFollowersHtml()

    return render_template('searchTweets.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml, homeHtml=_getHomeHtml)


@app.route('/followers')
def listFollowers():

    data = hf.getFollowers()
    html_content = hf.htmlifyUsers(data)

    composeTweetHtml = hf.getComposeTweetHtml()
    _getSearchUserHtml = hf.getSearchUserHtml()
    _getHomeHtml = hf.getHomeHtml()
    _getSearchTweetHtml = hf.getSearchTweetHtml()

    return render_template('followers.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, homeHtml=_getHomeHtml, searchTweet=_getSearchTweetHtml)


@app.route('/home')
def home():
    loggedUser = session.get('loggedUser')

    if loggedUser is None:
        # print("Error")
        return redirect(url_for('login'))
    else:
        # print("Logged In")
        data = hf.retrieve_flwee_tweets()

        html_content = hf.htmlifyTweets(data)

        composeTweetHtml = hf.getComposeTweetHtml()
        _getSearchUserHtml = hf.getSearchUserHtml()
        _getSearchTweetHtml = hf.getSearchTweetHtml()
        _getListFollowersHtml = hf.getListFollowersHtml()

        return render_template('home.html', html_content=html_content, composeTweetHtml=composeTweetHtml, searchUser=_getSearchUserHtml, listFollowers=_getListFollowersHtml, searchTweet=_getSearchTweetHtml)


if __name__ == '__main__':
    app.run(port=5001)
