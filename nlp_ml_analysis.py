#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import yaml
import pymysql
import datetime
import codecs

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

corpus = codecs.open('corpus.txt', 'w', encoding='utf-8')

array_of_analyzed_sentence = []
array_of_id = []
set_of_morph = set()

cur.execute("SELECT * FROM analyzed order by tweet_id")
result_analyzed = cur.fetchall()
temp_array_of_morph = []
tweet_id = result_analyzed[0][1]

for val in result_analyzed:
  # 트위터 라이브러리를 사용해 텍스트를 분석한다.
  #cur.execute("SELECT * FROM analyzed where tweet_id = " + str(row[0]))
  if tweet_id != val[1] :
    array_of_analyzed_sentence.append(temp_array_of_morph)
    array_of_id.append(tweet_id)
    tweet_id = val[1]
    temp_array_of_morph = []
  morph = "{}/{}".format(val[2], val[3])
  temp_array_of_morph.append(morph)
  # if morph == "슬픔/Noun" or morph == "놀라움/Noun" or morph == "/Noun" or morph == "분노/Noun" or morph == "호기심/Noun"  :
  #   print(morph)
  set_of_morph.add(morph)

print("- 형태소 분석 완료")

import gensim
import multiprocessing

model = gensim.models.Word2Vec.load('model_test')

#res = model.most_similar(positive=["신지예/N"], topn=20)
#print(res)
#res = model.similarity("슬픔/NNG","슬프/VA")
#print(res)
print("- Word2Vec 모델 생성 완료")

from sklearn import preprocessing
import numpy as np

cur.execute("SELECT * FROM posts")

list_of_morph = list(set_of_morph)
similarity_dictionary = {}
similarity_array = []
sentiments = ["기쁘/VA","슬프/VA","화나/VV","즐겁/VA","무섭/VA"]

for morph in list_of_morph:
  similarity_of_sentiment = []
  #print(morph)
  for sentiment in sentiments:
    try:
      val = model.similarity(sentiment,morph)
    except:
      val = 0
    finally:
      #print(sentiment, val)
      similarity_of_sentiment.append(val)
  similarity_dictionary[morph] = similarity_of_sentiment
  similarity_array.append(similarity_of_sentiment)

similarity_array = np.array(similarity_array)
min_max_scaler = preprocessing.MinMaxScaler()
scaled_similarity_array = min_max_scaler.fit_transform(similarity_array)
cnt = 0

cnt = 0
for row in scaled_similarity_array:
  similarity_dictionary[list_of_morph[cnt]] = row
  cnt+=1


print("- 스케일링 완료")

#문장 점수화를 위한 DB 생성

# # 이전에 DB가 있으면 제거한다.
# sqlDrop = "DROP TABLE IF EXISTS sentiment;"
# cur.execute(sqlDrop)

# # 분석용 DB를 생성한다.
# sqlCreate = "CREATE TABLE sentiment ( id bigint(20) unsigned NOT NULL AUTO_INCREMENT, tweet_id bigint(40) unsigned NOT NULL, morph VARCHAR(300), feeling VARCHAR(20), val float(20), PRIMARY KEY (id) )  DEFAULT CHARSET=utf8mb4;"
# cur.execute(sqlCreate)

# sqlInsert = 'INSERT INTO sentiment (tweet_id, morph, feeling, val) VALUES (%s, %s, %s, %s, %s)'

result_of_analysis = []

for index_of_sentiment in range(len(sentiments)):
  array_of_analyzed_sentiments = []
  number = 0
  total_avrg = 0
  for row in array_of_analyzed_sentence:
    # if number % 10000 == 0:
    #   print(str(number) + "개 문장 분석 완료")
    analyzed_sentence = []
    sum_of_feeling = count = 0
    for morph in row:
      val = similarity_dictionary[morph][index_of_sentiment]
      sum_of_feeling = sum_of_feeling + float(val)
      count+=1
    if count > 4:
      avrg = sum_of_feeling / float(count)
      analyzed_sentence.append(row)
      analyzed_sentence.append(avrg)
      analyzed_sentence.append(sum_of_feeling)
      analyzed_sentence.append(count)
      analyzed_sentence.append(array_of_id[number])
      array_of_analyzed_sentiments.append(analyzed_sentence)
      total_avrg += avrg
      #print(analyzed_sentence)
    #else:
      #print(row, " has no meaning")
    number+=1
  #print(sentiments[index_of_sentiment], total_avrg / len(array_of_analyzed_sentence))
  result_of_analysis.append(array_of_analyzed_sentiments)
  # db.cursor().execute(sqlInsert, (row[1], morph[0], morph[1]))

db.commit();

import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform

if platform.system() == 'Windows':
  font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
  rc('font', family=font_name)
else:
  rc('font',family='AppleGothic')

# res의 2번째 column 기준(2번 : sumfOfFeeling)으로 sort
sorted_result = []
count = 0

for list_of_results in result_of_analysis:
  sorted_result_of_analysis = sorted(list_of_results, key=lambda list_of_results : list_of_results[1])[::-1]
  sorted_result.append(sorted_result_of_analysis)
  array_of_avrg = []
  for row in list_of_results:
    array_of_avrg.append(row[1])
  plt.hist(array_of_avrg, bins='auto')
  plt.title(sentiments[count] + " Histogram")
  plt.xlabel("문장별 감정 평균")
  plt.ylabel("출현 빈도")
  plt.axis([0, 1, 0, 3000])
  #######################plt.show()
  fig = plt.gcf()
  count += 1



print("- 모든 문장의 점수화 완료")

result_file = codecs.open('result.txt', 'w', encoding='utf-8')


sqlSearch = 'SELECT * FROM posts where tweet_id = %s'

print("- 상위 10개 문장 출력")

index = 0

for sorted_result_of_sentiment in sorted_result:
  ##################print(sentiments[index])
  result_file.write(sentiments[index] + '\n')
  index += 1
  for row in sorted_result_of_sentiment[0:10]:
    #####################print(row)
    cur.execute(sqlSearch, (row[4]))
    search_sentence = cur.fetchall()
    #result_file.write(search_sentence[0][2] + '\n')
    result_file.write('점수 : ' + str(row[1]) + '\n')

result_file.close()


# 결과 DB를 생성한다.
#sqlCreate = 'CREATE TABLE IF NOT EXISTS results (id bigint(20) NOT NULL AUTO_INCREMENT, tweet_id int(11) DEFAULT NULL, tweet_text text COLLATE utf8mb4_unicode_ci, sentiment1 int(11) DEFAULT NULL, sentiment2 int(11) DEFAULT NULL, sentiment3 int(11) DEFAULT NULL, sentiment4 int(11) DEFAULT NULL, sentiment5 int(11) DEFAULT NULL, created_at datetime NOT NULL, updated_at datetime NOT NULL, PRIMARY KEY (id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
#cur.execute(sqlCreate)
sqlInsert = 'INSERT INTO results (user_id, tweet_text, sentiment1, sentiment2, sentiment3, sentiment4, sentiment5, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
#sqlInsert = 'INSERT INTO results (sentiment1, sentiment2, sentiment3, sentiment4, sentiment5) VALUES (%s, %s, %s, %s, %s)'

from konlpy.tag import Twitter
from konlpy.tag import Kkma
from konlpy.tag import Hannanum
from konlpy.tag import Komoran

twitter = Twitter()
kkma = Kkma()
hannanum = Hannanum()
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
  #print("문장 :", sentence)
  #print(result[i])
  i += 1

'''
sentence = "★마비노기 14주년 기념 축제★ 매주 그리운 NPC와 함께 상상여행을 떠나고, 돌아온 악동 4인방을 도와 축제를 꾸며주세요. 다양한 14주년 이벤트에 참여하면 역대급으로 쏟아지는 푸짐한 선물까지! #마비노기_14주년"
result = komoran.pos(sentence)
print("문장 :", sentence)
print(result)
'''


i = 0
for twit in result:
  #print(twit)
  #print(user_timeline[i])
  for index_of_sentiment in range(len(sentiments)):
    value_of_sentence = 0
    sum_of_feeling = 0
    count = 0
  #i = 0
    for word, tag in twit:
      morph = "{}/{}".format(word, tag)
      #print(morph)
      val = 0
      try:
        val = similarity_dictionary[morph][index_of_sentiment]
      except:
        count-=1
        continue
      finally:
        count+=1
        sum_of_feeling += val
      #print(i)

        if count > 0:
          avrg = sum_of_feeling / float(count)
          value_of_sentence = avrg
        else:
          print(row, " has no meaning")
        array_of_result_by_sentiment = []

        #print(sentiments[index_of_sentiment], " 감정 분석")
        #print("형태소 점수 합계 :", sum_of_feeling)
        #print("형태소 점수 평균 :", avrg)
        #print("총 문장 갯수 :", len(sorted_result[index_of_sentiment]))

        rank = 0
        for row in sorted_result[index_of_sentiment]:
          rank+=1
          if row[1] < value_of_sentence:
            #print("등수 : " , rank)
            break
        #print(sentiments[index_of_sentiment], "백분율 :",(100 - int(rank / len(sorted_result[index_of_sentiment]) * 100)))
        rank = 0


    if count > 0:
      avrg = sum_of_feeling / float(count)
      value_of_sentence = avrg
    else:
      print(row, " has no meaning")
    array_of_result_by_sentiment = []

    print(sentiments[index_of_sentiment], " 감정 분석")
    #print("형태소 점수 합계 :", sum_of_feeling)
    print("형태소 점수 평균 :", avrg)
    #print("총 문장 갯수 :", len(sorted_result[index_of_sentiment]))

    rank = 0
    for row in sorted_result[index_of_sentiment]:
      rank+=1
      if row[1] < value_of_sentence:
        print("등수 : " , rank)
        break
    pct = (100 - int(rank / len(sorted_result[index_of_sentiment]) * 100))
    print(sentiments[index_of_sentiment], "백분율 :", pct)
    rank = 0

    if sentiments[index_of_sentiment] == "기쁘/VA":
      sent1 = pct
    elif sentiments[index_of_sentiment] == "슬프/VA":
      sent2 = pct
    elif sentiments[index_of_sentiment] == "화나/VV":
      sent3 = pct
    elif sentiments[index_of_sentiment] == "즐겁/VA":
      sent4 = pct
    elif sentiments[index_of_sentiment] == "무섭/VA":
      sent5 = pct
  print(sent1, sent2, sent3, sent4, sent5)
  db.cursor().execute(sqlInsert, (twit_id[i], user_timeline[i], sent1, sent2, sent3, sent4, sent5, datetime.datetime.now(), datetime.datetime.now()))
  db.commit()
  i += 1
