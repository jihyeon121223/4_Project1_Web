from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
import xml.etree.ElementTree as et
import pandas as pd
import bs4
from lxml import html
import numpy as np
from datetime import datetime
import pymysql
import sqlalchemy
from sqlalchemy import create_engine
import folium
import geocoder


# url 입력
url = 'http://apis.data.go.kr/B552584/EvCharger/getChargerInfo?serviceKey'
params = {'serviceKey': 'blria7TY6VCPbn8QUgYrHz5RNNYWej29+Halh6YgL1DzuZApx70h2jqf9Y3bMDXQcfleL1v/l548DEzZXKMSWg==',
            'type': 'xml', 'numOfRows': '1000', 'pageNo': '1', 'addr': 'addr'}
response = requests.get(url, params=params)


# xml 값
xml_data = response.content.decode('utf-8')


# 한국환경공단_전기자동차 충전소 정보 API에서는 <item>태그 안에 값이 들어가므로 여기서는 item를 입력함
# bs4 사용하여 item 태그 분리
xml_obj = bs4.BeautifulSoup(xml_data,'lxml-xml')
rows = xml_obj.findAll('item')
# print(rows)


# 각 행의 컬럼, 이름, 값을 가지는 리스트 만들기
row_list = [] # 행값
name_list = [] # 열이름값
value_list = [] #데이터값

# xml 안의 데이터 수집
for i in range(0, len(rows)):
    columns = rows[i].find_all()
    #첫째 행 데이터 수집
    for j in range(0,len(columns)):
        if i ==0:
            # 컬럼 이름 값 저장
            name_list.append(columns[j].name)
        # 컬럼의 각 데이터 값 저장
        value_list.append(columns[j].text)
    # 각 행의 value값 전체 저장
    row_list.append(value_list)
    # 데이터 리스트 값 초기화
    value_list=[]

# xml값 DataFrame으로 만들기
df = pd.DataFrame(row_list, columns=name_list)
# print(df.head(19))

# null값 처리
missing_fill_val = {"statNm" : "null",
                    "statId": "null",
                    "chgerId": "0",
                    "chgerType": "00",
                    "addr": "null", 
                    "location": "null",
                    "useTime": "null",
                    "busiId": "0",
                    "bnm": "null",
                    "busiNm": "null",
                    "busiCall": "null", 
                    "stat": 0,
                    "statUpdDt": "null", 
                    "lastTsdt": "null",
                    "lastTedt": "null", 
                    "nowTsdt": "null",
                    "powerType": "null",
                    "output": "0",
                    "method": "0",
                    "zcode": 0,
                    "parkingFree": "0",
                    "note": "null",
                    "limitYn": "0",
                    "limitDetail": "null",
                    "delYn": "0",
                    "delDetail": "null"}
                    
df.fillna(missing_fill_val,inplace=True)

print(df.head(19))