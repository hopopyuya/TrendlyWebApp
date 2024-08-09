#!/usr/bin/env python
# coding: utf-8

from flask import Flask, render_template, request, redirect, g, url_for, session, make_response
from flask_paginate import Pagination, get_page_parameter
import sqlite3
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DATABASE = os.getenv('DATABASE_PATH')
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.route("/")
def index():
    db = get_db()
    cur = db.execute("SELECT num, word, img_key FROM trend_word")
    words = cur.fetchall()
    cur = db.execute(f'SELECT num, title, link, img FROM gnews')
    gnewss = cur.fetchall()
    cur = db.execute(f'SELECT num, html FROM twitter')
    tweets = cur.fetchall()
    return render_template('index.html', words=words, gnewss=gnewss, tweets=tweets)

if __name__ == "__main__":
    app.debug = False
    app.run(host='0.0.0.0', port=8888)
