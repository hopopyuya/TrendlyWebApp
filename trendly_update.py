#!/usr/bin/env python
# coding: utf-8

from pytrends.request import TrendReq
import tweepy
from GoogleNews import GoogleNews
from wordcloud import WordCloud

import pandas as pd
import matplotlib.pyplot as plt
import datetime
import sqlite3

from dotenv import load_dotenv
import os


dbname = os.getenv('DATABASE_PATH')
conn = sqlite3.connect(dbname)
cur = conn.cursor()

# Googleと Twitterのトレンドの取得~wordcloud作成

# google api
dt_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()
yesterday = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date() - datetime.timedelta(1)
current_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%y-%m-%d-%H')
# googleトレンド取得
pytrend = TrendReq(hl='ja-jp',tz=540)
google_daily_trend = pytrend.trending_searches(pn='japan')

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
#日本のWOEID
woeid = 23424856
#トレンド一覧取得
trends = api.get_place_trends(woeid)
twitter_realtime_trend = pd.DataFrame(trends[0]["trends"])

# トレンド結合
df = pd.DataFrame(pd.concat([google_daily_trend[0], twitter_realtime_trend['name']]))
df.reset_index(inplace=True)
df = df.sort_values('index')
df = df[0][df['index'] <= 9]
df = df.str.replace('#', '')
df = df.reset_index()

# wordcloud作成
font_path_gothic = './LanobePOPv2/LightNovelPOPv2.otf'
wc = WordCloud(background_color="white",width=900, height=500, font_path=font_path_gothic).generate(' '.join(df[0]))
# plt.figure(figsize=(10,30))
plt.axis("off")
wc.to_file("./flask_trendly/static/wordcloud/trend_top.png")
# plt.imshow(wc)
df = df.drop_duplicates(subset=[0])
df = df.reset_index()
df.drop(['index', 'level_0'], axis=1, inplace=True)
df.columns = ['trend_word']


# ワード毎の情報処理
cur.executescript("""
drop table if exists gnews;
drop table if exists twitter;
""")
file_num = 0
kw = []
img_key_list = []
for i in range(len(df)):
    kw_list = [df['trend_word'][i]]
    # トレンドワードの関連キーワードの取得
    pytrend.build_payload(kw_list=kw_list, timeframe=f'{yesterday}T15 {dt_now}T15', geo="JP")
    topics = pytrend.related_queries()
    df2_1 = topics[kw_list[0]]['top']
    # トレンドワードの関連topicの取得
    topics = pytrend.related_topics()
    df2_2 = topics[kw_list[0]]['top']
    # トレンドワードの関連ニュースの取得
    googlenews = GoogleNews(lang='ja', encode='utf-8', period='1d')
    googlenews.get_news(kw_list[0])
    result = googlenews.results()
    df3 = pd.DataFrame(result)
    # トレンドワードの人気ツイート取得
    search_word = f'{kw_list[0]} min_retweets:100'
    item_number = 3
    tweets = tweepy.Cursor(api.search_tweets,q=search_word, tweet_mode='extended',result_type="mixed",lang='ja').items(item_number)
    tw_data = []
    for tweet in tweets:
        oembed = api.get_oembed("https://twitter.com/"+tweet.user.screen_name+"/status/"+str(tweet.id))
        html = oembed.get("html")
        tw_data.append([tweet.id, tweet.created_at, tweet.full_text.replace('\n',''), tweet.favorite_count, tweet.retweet_count, html])
    labels=['ツイートID', 'ツイート時刻', 'ツイート本文', 'いいね数', 'リツイート数', 'html']
    df4 = pd.DataFrame(tw_data,columns=labels)
    
    if df2_1 is not None and df2_2 is not None and df3 is not None and df4 is not None:
        if len(df2_1) != 0 and len(df2_2) != 0 and len(df3) != 0 and len(df4) != 0:
            img_key = str(current_time) + '-' + str(file_num)
            kw.append(kw_list[0])
            img_key_list.append(img_key)
            df2_1 = df2_1[df2_1.index <= 9]
            df2_2 = df2_2[df2_2.index <= 9]
            df2 = pd.concat([df2_1['query'], df2_2['topic_title']])
            wc = WordCloud(background_color="#FAFAFA",width=900, height=500, font_path=font_path_gothic).generate(' '.join(df2))
            plt.axis("off")
            wc.to_file(f"./flask_trendly/static/wordcloud/{img_key}.png")
            # plt.imshow(wc)

            df3['link'] = "https://" + df3['link']
            df3.drop(['desc', 'datetime', 'media', 'site'], axis=1, inplace=True)
            df3 = df3[df3.index <= 2]
            df3['num'] = file_num
            df3.to_sql("gnews", conn, if_exists='append', index=None)
            # display(df3)

            df4 = df4.drop_duplicates()
            df4 = df4.sort_values('リツイート数', ascending=False)
            df4['num'] = file_num
            df4.to_sql("twitter", conn, if_exists='append', index=None)
            # display(df4)
            file_num += 1
        else:
            pass            
    else:
        pass
    
kw = pd.DataFrame({'word':kw, 'img_key':img_key_list})
kw.reset_index(inplace=True)
kw.columns = ['num', 'word', 'img_key']
cur.executescript("""
drop table if exists trend_word;
""")
kw.to_sql("trend_word", conn, if_exists='append', index=None)
