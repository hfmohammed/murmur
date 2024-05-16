import sys
import sqlite3
import getpass
import re
from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

databaseName = "test.db"

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


@app.route('/login')
def login():
    cacheData = True
    if cacheData:
        return render_template('login.html')



@app.route('/approve', methods=["POST"])
def approve():
    userId = request.form['username']
    password = request.form['password']


    print(userId, password)

    if not usernameExists(userId):
        return redirect(url_for('login'))
    else:
        userData = pullUserData(userId)
        expectedPassword = userData[1]
        if expectedPassword != password:
            return redirect(url_for('login'))
        return redirect(url_for('home')) 

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(port=5001)
