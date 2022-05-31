from turtle import width
from django.shortcuts import render
import requests
from urllib import parse
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import folium
import geocoder
import streamlit as st
from urllib.request import urlopen
import re
import time
import numpy as np

# Create your views here.

def main(request):
    return render(request, 'main/index.html')

######################################## 지역코드 입력하세요 
z = 26 ## 
###################################
statnm = []  # 이름
chgertype = []  # 충전기 타입
addr = []  # 주소
lat = []  # 위도
lng = []  # 경도
usetime = [] # 이용가능시간
stat = []  # 충전기 상태
outputs = []  # 충전용량 3, 7, 50, 100, 200
methods = []  # 충전방식 단독 or 동시
zcodes = []  # 지역코드
limitYn = []  # 이용자 제한 Y or N
limitDetail = []  # 이용자 제한 사유
parkingfree = []   # 주차료 무료 Y or N

def getEvCharger(addr: str) -> pd.DataFrame:
    url = 'http://apis.data.go.kr/B552584/EvCharger/getChargerInfo?'
    ServiceKey='64gKOJqVRDnGcTGnxudjY1CQQeu0IKAcjtYZb83FEOMueJmGVcthWM1KlsxDUGUyG9pFDTeU%2FclsiRUm7xWPbw%3D%3D'



    while 1:
        page_num = 1
        response = (url + 'ServiceKey=' + ServiceKey + '&numOfRows=1000' + '&pageNo='+ str(page_num) +'&zcode=' + str(z))
        url_new = response.encode('utf-8')
        req = requests.get(url_new)
        bs=BeautifulSoup(req.text, 'html.parser')

        statnm = bs.findAll('statnm')
        chgertype = bs.findAll('chgertype')
        addr = bs.findAll('addr')
        lat = bs.findAll('lat')
        lng = bs.findAll('lng')
        usetime = bs.findAll('usetime')
        stat = bs.findAll('stat')
        output = bs.findAll('output')
        method = bs.findAll('method')
        zcode = bs.findAll('zcode')
        limitYn = bs.findAll('limitYn')
        limitDetail = bs.findAll('limitDetail')
        parkingfree = bs.findAll('parkingfree')

        total_num = str(bs.find('totalcount'))
        total = int(re.findall('\d+', total_num)[0])
        
        if page_num < total // 1000 + 1:
            for i in range(1000):
                statnm.append(statnm[i].text)
                chgertype.append(chgertype[i].text)
                addr.append(addr[i].text)
                lat.append(lat[i].text)
                lng.append(lng[i].text)
                usetime.append(usetime[i].text)
                stat.append(stat[i].text)
                output.append(output[i].text)
                method.append(method[i].text)
                zcodes.append(zcode[i].text)
                try:
                    limitYn.append(limitYn[i].text)
                    limitDetail.append(limitDetail[i].text)
                except:
                    limitYn.append('')
                    limitDetail.append('')
                parkingfree.append(parkingfree[i].text)
                
            page_num += 1


        else:
            for i in range(total%1000):
                statnm.append(statnm[i].text)
                chgertype.append(chgertype[i].text)
                addr.append(addr[i].text)
                lat.append(lat[i].text)
                lng.append(lng[i].text)
                usetime.append(usetime[i].text)
                stat.append(stat[i].text)
                outputs.append(output[i].text)
                methods.append(method[i].text)
                zcodes.append(zcode[i].text)
                try:
                    limitYn.append(limitYn[i].text)
                    limitDetail.append(limitDetail[i].text)
                except:
                    limitYn.append('')
                    limitDetail.append('')
                parkingfree.append(parkingfree[i].text)
                
            break

def store_one_hour_state():
    stat = []
    page_num = 1
    while 1:
        response = (url + 'ServiceKey=' + ServiceKey + '&numOfRows=1000' + '&pageNo='+ str(page_num) +'&zcode=' + str(z)) ## zcode 50이 제주도
        url_new = response.encode('utf-8')
        req = requests.get(url_new)
        bs=BeautifulSoup(req.text, 'html.parser')

        stat = bs.findAll('stat')

        total_num = str(bs.find('totalcount'))
        total = int(re.findall('\d+', total_num)[0])

        if page_num >= total // 1000 + 1:
            for i in range(total%1000):
                stat.append(stat[i].text)
            break
            
        else:
            for i in range(1000):
                stat.append(stat[i].text)
            page_num += 1
    stat
    return stat

df = pd.DataFrame([statnm, chgertype, addr, lat, lng, usetime, zcodes, limitYn, limitDetail, parkingfree, stat]).T
df.columns=['이름','충전타입','주소', '위도','경도', '이용시간', '지역코드', '이용자제한', '이용자제한사유', '무료 주차','실시간 상태(20분)']

def convertGeoLoc(h, m, s): 
    return h + (m + s / 60) / 60

g = geocoder.ip('me') # ip기반 현재위치

df = getEvCharger("서울")

def map(request):
    m = folium.Map(
        location=g.latlng,
        # tiles='cartodbpositron',
        zoom_start=13,
    )
    for _, elem in df.iterrows():
        # 충전기 타입
        if elem['chgertype'] == '01':
            elem['chgertype'] = 'DC차데모'
        elif elem['chgertype'] == '02':
            elem['chgertype'] = 'AC완속'
        elif elem['chgertype'] == '03':
            elem['chgertype'] = 'DC차데모+AC3상'
        elif elem['chgertype'] == '04':
            elem['chgertype'] = 'DC콤보'
        elif elem['chgertype'] == '05':
            elem['chgertype'] = 'DC차데모+DC콤보'
        elif elem['chgertype'] == '06':
            elem['chgertype'] = 'DC차데모+AC3상+DC콤보'
        elif elem['chgertype'] == '07':
            elem['chgertype'] = 'AC3상'

        # 충전소 상태
        if elem['stat'] == 1:
            elem['stat'] = '통신이상'
            icon_color = 'darkpurple'
        elif elem['stat'] == 2:
            elem['stat'] = '충전대기'
            icon_color = 'green'
        elif elem['stat'] == 3:
            elem['stat'] = '충전중'
            icon_color = 'orange'
        elif elem['stat'] == 4:
            elem['stat'] = '운영중지'
            icon_color = 'black'
        elif elem['stat'] == 5:
            elem['stat'] = '점검중'
            icon_color = 'blue'
        elif elem['stat'] == 9:
            elem['stat'] = '상태미확인'
            icon_color = 'gray'
        folium.Marker(         # 전체 마커
                icon = folium.Icon(color=icon_color),
                location=(elem['lat'], elem['lng']),
                popup="<html><head><style>h4 {color:blue;font-family:'Noto Sans KR',sans-serif;}</style><body><pre><h4><b>"+elem['statnm']+"</b></h4><br> 주소: "+elem['addr']+"<br> 운영시간: "+elem['usetime']+"<br> 상태: "+elem['stat']+"<br> 충전기타입: "+elem['chgertype']+"</pre></body></html>"
            ).add_to(m)
    folium.Marker(          # 현위치 마커
            icon = folium.Icon(color='red', icon='star'),
            location=(g.latlng),
            tooltip='ip기반 현재위치'
        ).add_to(m)
    maps = m._repr_html_()
    return render(request, 'main/map.html',{'map':maps})