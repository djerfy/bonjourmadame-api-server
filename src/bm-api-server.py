#!/usr/bin/env python3

import os, re, sys, calendar, requests
from random import randrange
from datetime import date, datetime, timedelta
from flask import Flask, abort, jsonify, request, render_template

app = Flask(__name__.split('.')[0])
ver = os.environ['VERSION']

def randomDate(start, end):
    """
    Return a random datetime between two dates
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)

def randomURI(dateNow):
    """
    Generate a random URI since 2018-12-10, website migrated to WordPress platform and now
    """
    dateInt = datetime.strptime('2018-12-10', '%Y-%m-%d')
    dateRandom = randomDate(dateInt, dateNow)
    dateRandomY = str(dateRandom).split('-')[0]
    dateRandomM = str(dateRandom).split('-')[1]
    dateRandomD = str(dateRandom).split('-')[2].split(' ')[0]
    uri = "{}/{}/{}/".format(dateRandomY, dateRandomM, dateRandomD)
    return uri

def getURL(url):
    """
    Get content from website and return a picture URL
    """
    picture_url = ""
    retries_now = 0
    retries_max = 10
    if "RETRIES_MAX" in os.environ:
        retries_max = os.environ['RETRIES_MAX']
    while picture_url == "" and picture_url.split('/')[-1] != "noclub.png" and retries_now <= retries_max:
        response = requests.get(url)
        if response.status_code != 200:
            retries_now = retries_now + 1
            continue
        filtered = re.search(r'<img loading="lazy" class="alignnone .+" src="(.+)\?resize=.+" alt .+ data-lazy-srcset="', str(response.content))
        if not filtered:
            retries_now = retries_now + 1
            continue
        picture_url = filtered.group(1)
        break
    if not picture_url or picture_url == "" or picture_url.split('/')[-1] == "noclub.png":
        return None, retries_now
    else:
        return picture_url, retries_now

@app.route('/')
def index():
    """
    Return index page from HTML template
    """
    return render_template('index.html', version=ver)

@app.route('/api/ping')
def ping():
    """
    Return pong response
    """
    return jsonify(response = "pong")

@app.route('/api/version')
def version():
    """
    Return application version
    """
    return jsonify(response = ver)

@app.route('/api/latest')
def latest():
    """
    Return latest picture URL
    """
    dtoday = date.today()
    dname = calendar.day_name[dtoday.weekday()]
    url, retry = getURL("https://www.bonjourmadame.fr/")
    return jsonify(
        node = os.environ['HOSTNAME'],
        title = "BonjourMadame, {} {} (latest)".format(str(dname), str(dtoday.day)),
        description = "Return latest picture URL",
        url = url,
        retry = retry)

@app.route('/api/random')
def random():
    """
    Return random picture URL
    """
    dtoday = date.today()
    dname = calendar.day_name[dtoday.weekday()]
    dateNow = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    url, retry = getURL("https://www.bonjourmadame.fr/{}".format(randomURI(dateNow)))
    return jsonify(
        node = os.environ['HOSTNAME'],
        title = "BonjourMadame, {} {} (random)".format(str(dname), str(dtoday.day)),
        description = "Return random picture URL",
        url = url,
        retry = retry)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
