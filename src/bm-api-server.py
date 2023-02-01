#!/usr/bin/env python3

import os, calendar, requests, logging
from random import randrange
from datetime import date, datetime, timedelta
from flask import Flask, jsonify, render_template
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


app = Flask(__name__.split('.')[0], static_url_path='/static')
ver = os.environ['VERSION']
bjrurl = "https://www.bonjourmadame.fr/"

app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

def randomDate():
    """
    Return a random datetime between two dates
    """
    start = datetime.strptime('2018-12-10', '%Y-%m-%d')
    end = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)

def formatDate(date):
    """
    Format date to YYYY-MM-DD
    """
    return date.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')

def formatURI(date):
    """
    Format URI to YYYY-MM-DD
    """
    dateY = str(date).split('-')[0]
    dateM = str(date).split('-')[1]
    dateD = str(date).split('-')[2].split(' ')[0]
    uri = "{}/{}/{}/".format(dateY, dateM, dateD)
    return uri

def todayURL():
    """
    Return today's URL
    """
    return bjrurl+"{}".format(formatURI(formatDate(datetime.now())))

def randomURL():
    """
    Generate a random URL from a random URI
    """
    url = bjrurl+"{}".format(formatURI(randomDate()))
    return url

def parser(html):
    """
    Parse HTML content and return a picture URLformatDate
    """

    soup = BeautifulSoup(html, 'html.parser')
    if soup.find('div', class_='post-content'):
        if soup.find('div', class_='post-content').find('img'):
            img = soup.find('div', class_='post-content').find('img', class_='alignnone')
            if img['src']:
                imgUrl = img['src']
                imgUrl = urljoin(imgUrl, urlparse(imgUrl).path)
            else:
                imgUrl = ""
        else:
            imgUrl = ""

    else:
        imgUrl = ""

    if soup.find('h1', class_='post-title'):
        t = soup.find('h1', class_='post-title').find('a')
        title = t.text
    else:
        title = ""

    if soup.find('div', class_='post-content'):
        t = soup.find('div', class_='post-content').find('a').get('href')
        if t == "https://fr.tipeee.com/bonjour-madame-soutien-et-amour-de-la-madame":
            tipee = True
        else:
            tipee = False
    return {
        'title': title,
        'imgUrl': imgUrl,
        'tipee': tipee,
    }

def getURL(action):
    """
    Get content from website and return a picture URL
    """

    if action == "random":

        picture_url = ""
        retries_now = 0
        retries_max = 10
        if "RETRIES_MAX" in os.environ:
            retries_max = os.environ['RETRIES_MAX']
        while picture_url == "" and picture_url.split('/')[-1] != "noclub.png" and retries_now <= retries_max:
            url = randomURL()
            response = requests.get(url)
            if response.status_code != 200:
                retries_now = retries_now + 1
                continue

            p = parser(response.content)
            picture_url = p['imgUrl']
            title = p['title']

            """
            if p['tipee'] == True: Samedi/Dimanche
            """
            if p['tipee']:
                retries_now = retries_now + 1
                continue

            break
        if not picture_url or picture_url == "" or picture_url.split('/')[-1] == "noclub.png":
            return None, retries_now, ""
        else:
            return picture_url, retries_now, title

    elif action == "today":

        picture_url = ""
        retries_now = 0
        retries_max = 2
        if "RETRIES_MAX" in os.environ:
            retries_max = os.environ['RETRIES_MAX']
        while picture_url == "" and picture_url.split('/')[-1] != "noclub.png" and retries_now <= retries_max:
            url = todayURL()
            response = requests.get(url)
            if response.status_code != 200:
                retries_now = retries_now + 1
                continue

            p = parser(response.content)
            picture_url = p['imgUrl']
            title = p['title']

            """
            if p['tipee'] == True: Samedi/Dimanche
            """
            if p['tipee']:
                return None, retries_now, "Pas de bonjour madame le weekend"

            break
        if not picture_url or picture_url == "" or picture_url.split('/')[-1] == "noclub.png":
            return None, retries_now, ""
        else:
            return picture_url, retries_now, title    

    

@app.route('/health', methods=['GET'])
def health():
	# Handle here any business logic for ensuring you're application is healthy (DB connections, etc...)
    return "Healthy: OK"

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
    url, retry, title = getURL("today")
    return jsonify(
        node = os.environ['HOSTNAME'],
        title = title,
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
    url, retry, title = getURL("random")
    return jsonify(
        node = os.environ['HOSTNAME'],
        title = title,
        description = "Return random picture URL",
        url = url,
        retry = retry)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=os.environ['FLASK_DEBUG'])
