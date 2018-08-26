#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import yaml
import pymysql
import datetime
import codecs
import gensim
import multiprocessing
import numpy as np
import matplotlib.pyplot as plt
import platform
import time
from konlpy.tag import Komoran

time.sleep(5)
print('analyze_user_timeline.py start')


# config 파일 불러옴
with open('config.yml', 'r') as ymlfile:
  cfg = yaml.load(ymlfile)

# 디비 연결
db = pymysql.connect(host = cfg['mysql']['host'],       # 호스트
                     user = cfg['mysql']['user'],       # 유저이름
                     passwd = cfg['mysql']['passwd'],   # 비밀번호
                     db = cfg['mysql']['db'],           # 디비 이름
                     charset = 'utf8mb4')               # utf-8
cur = db.cursor()

sentiments = ['기쁘/VA', '슬프/VA', '화나/VV', '즐겁/VA', '무섭/VA']
similarity_dictionary = {}
sorted_result = []

# DB로부터 정보 가져옴

# 형태소 분석 DB 가져옴
sqlSearch = 'SELECT * FROM morph where sentiment = %s'
cur.execute(sqlSearch, (0))
morph_info = cur.fetchall()
for morph in morph_info:
    similarity_dictionary[morph[2]]= []

for index_of_sentiment in range(len(sentiments)):
  cur.execute(sqlSearch, (index_of_sentiment))
  morph_info = cur.fetchall()
  for morph in morph_info:
    similarity_dictionary[morph[2]].append(morph[3])
    #print(morph, similarity_dictionary[morph[2]])

# 문장 분석 DB 가져옴
sqlSearch = 'SELECT * FROM sentence_rank where sentiment = %s order by value desc'
for index_of_sentiment in range(len(sentiments)):
  cur.execute(sqlSearch, (index_of_sentiment))
  rank_info = cur.fetchall()
  sorted_result.append(rank_info)

# 결과 DB를 생성한다.
sqlInsert = 'INSERT INTO results (user_id, tweet_text, sentiment1, sentiment2, sentiment3, sentiment4, sentiment5, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'

komoran = Komoran()

sqlSearchTimeline = 'SELECT * from user_tweets'
cur.execute(sqlSearchTimeline)
timeline = cur.fetchall()
sentence = []
result = []
i = 0

twit_id = []
user_timeline = []
sent1 = []
sent2 = []
sent3 = []
sent4 = []
sent5 = []

for content in timeline:
  sentence = content[2]
  user_timeline.append(sentence)
  twit_id.append(str(content[1]))
  result.append(komoran.pos(sentence))
  i += 1

i = 0
for twit in result:
  print(user_timeline[i])
  for index_of_sentiment in range(len(sentiments)):
    value_of_sentence = 0
    sum_of_feeling = 0
    count = 0
    for word, tag in twit:
      morph = '{}/{}'.format(word, tag)
      #print(morph)
      val = 0
      try:
        val = similarity_dictionary[morph][index_of_sentiment]
      except:
        count -= 1
        continue
      finally:
        count += 1
        sum_of_feeling += val

        if count > 0:
          avrg = sum_of_feeling / float(count)
          value_of_sentence = avrg
        else:
          print(twit, ' has no meaning')
        array_of_result_by_sentiment = []

    if count > 0:
      avrg = sum_of_feeling / float(count)
      value_of_sentence = avrg
    else:
      print(twit, ' has no meaning')
    array_of_result_by_sentiment = []

    print(sentiments[index_of_sentiment], ' 감정 분석')

    rank = 0
    for row in sorted_result[index_of_sentiment]:
      rank+=1
      if row[2] < value_of_sentence:
        print('등수 : ' , rank)
        break
    pct = (100 - int(rank / len(sorted_result[index_of_sentiment]) * 100))
    print(sentiments[index_of_sentiment], '백분율 : ', pct)
    rank = 0

    if sentiments[index_of_sentiment] == '기쁘/VA':
      sent1 = pct
    elif sentiments[index_of_sentiment] == '슬프/VA':
      sent2 = pct
    elif sentiments[index_of_sentiment] == '화나/VV':
      sent3 = pct
    elif sentiments[index_of_sentiment] == '즐겁/VA':
      sent4 = pct
    elif sentiments[index_of_sentiment] == '무섭/VA':
      sent5 = pct

  print(sent1, sent2, sent3, sent4, sent5)
  db.cursor().execute(sqlInsert, (twit_id[i], user_timeline[i], sent1, sent2, sent3, sent4, sent5, datetime.datetime.now(), datetime.datetime.now()))
  db.commit()
  i += 1
