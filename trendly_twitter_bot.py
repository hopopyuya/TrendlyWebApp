#!/usr/bin/env python
# coding: utf-8

import tweepy
import sqlite3

# twitter api
# API情報を記入
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
# Twitterオブジェクトの生成
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# sqlite接続
dbname = os.getenv('DATABASE_PATH')
conn = sqlite3.connect(dbname)
cur = conn.cursor()

# 今のトレンドワード一覧bot
filename = "./flask_trendly/static/wordcloud/trend_top.png"
media_id = []
res = api.media_upload(filename)
media_id.append(res.media_id)

cur = cur.execute('SELECT word FROM trend_word WHERE dt = (SELECT MAX(dt) FROM trend_word) ORDER BY num LIMIT 5')
cur = cur.fetchall()
word_list = []
for row in cur:
    for i in row:
        word_list.append(i)

api.update_status(status=f'【今の最新トレンドワード一覧】\nトレンドワード毎の詳細はトレンドリーで確認\nhttps://trendly-info.com/\n #{word_list[0]} #{word_list[1]} #{word_list[2]} #{word_list[3]} #{word_list[4]}', media_ids=media_id)
