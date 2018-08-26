# -*- coding: utf-8 -*-
#!/usr/bin/python

import tweepy
import os
import sys
import yaml
import pymysql
import datetime

# config 파일 불러옴
with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

# 디비 연결

db = pymysql.connect(host = cfg['mysql']['host'],       # 호스트
                     user = cfg['mysql']['user'],       # 유저이름
                     passwd = cfg['mysql']['passwd'],   # 비밀번호
                     db = cfg['mysql']['db'],           # 디비 이름
                     charset = 'utf8mb4')               # utf-8
cur = db.cursor()

# API 인증요청
consumer_key = cfg['twitter']['consumer_key']
consumer_secret = cfg['twitter']['consumer_secret']
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

# access 토큰 요청
access_token = cfg['twitter']['access_token']
access_token_secret = cfg['twitter']['access_token_secret']
auth.set_access_token(access_token, access_token_secret)

# twitter API 생성
api = tweepy.API(auth, wait_on_rate_limit = True, wait_on_rate_limit_notify = True)

wfile = open(os.getcwd()+"/user_text.txt", mode='w', encoding='utf8')    # 쓰기 모드

array = []
numberOfItems = 40  # 검색횟수 입력
user = sys.argv[1]
if user == '':
  user = '@shanarchist7'

print(user)

# 이전에 DB가 있으면 제거한다.
#sqlDrop = "DROP TABLE IF EXISTS user_tweets;"
#cur.execute(sqlDrop)
# 분석용 DB를 생성한다.
#sqlCreate = "CREATE TABLE user_text ( id bigint(20) unsigned NOT NULL AUTO_INCREMENT, tweet_id bigint(40) unsigned NOT NULL, text VARCHAR(400) NOT NULL, created datetime, PRIMARY KEY (id) )  DEFAULT CHARSET=utf8mb4;"
#cur.execute(sqlCreate)

sqlInsert = 'INSERT INTO user_tweets (tweet_id, tweet_text, created_at, updated_at) VALUES (%s, %s, %s, %s)'

cursor = tweepy.Cursor(api.user_timeline, screen_name=user, include_rts=False, count=numberOfItems).items(numberOfItems)
# 트위터에서 크롤링
try:
  for tweet in cursor:
    if 'https' in tweet.text or 'com' in tweet.text or '@' in tweet.text or '&' in tweet.text or 'domain' in tweet.text:
      continue
    print(tweet.text)
    db.cursor().execute(sqlInsert, (tweet.id, tweet.text, tweet.created_at, tweet.created_at))
  db.commit()
finally:
  db.close()
