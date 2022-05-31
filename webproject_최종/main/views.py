from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
import xml.etree.ElementTree as et
import pandas as pd
import bs4
from lxml import html
import numpy as np
from .models import Search
from .forms import SearchForm
from datetime import datetime
import pymysql
import sqlalchemy
from sqlalchemy import create_engine
import folium
from folium import plugins
import geocoder


# Create your views here.

def main(request):
    return render(request, 'main/index.html')


def update_db(addr: str) -> pd.DataFrame:

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
    # print(gg_df.head(19))


    ## DB연결
    user = "bigdata"
    password = "Bigdata123!!"
    host = "192.168.56.101"
    port = "3306"
    db = "MapDB"
    connect_script = f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}'
    engine = create_engine(connect_script)
    conn = engine.connect()


    ## DataFrame을 DB에 저장
    # 데이터타입 지정
    dtypesql = {
            'statNm':sqlalchemy.types.VARCHAR(100), # 충전소명
            'statId':sqlalchemy.types.VARCHAR(8), # 충전소ID
            'chgerId':sqlalchemy.types.VARCHAR(2), # 충전기ID
            'chgerType':sqlalchemy.types.VARCHAR(2), # 충전기타입
            'addr':sqlalchemy.types.VARCHAR(150), # 주소
            'location':sqlalchemy.types.VARCHAR(100), # 상세위치
            'lat':sqlalchemy.types.VARCHAR(20), # 위도
            'lng':sqlalchemy.types.VARCHAR(20), # 경도
            'useTime':sqlalchemy.types.VARCHAR(50), # 이용가능시간
            'busiId':sqlalchemy.types.VARCHAR(2), # 기관 아이디
            'bnm':sqlalchemy.types.VARCHAR(50), # 기관명
            'busiNm':sqlalchemy.types.VARCHAR(50), # 운영기관명
            'busiCall':sqlalchemy.types.VARCHAR(20), # 운영기관연락처
            'stat':sqlalchemy.types.Integer(), # 충전기상태
            'statUpdDt':sqlalchemy.types.VARCHAR(14), # 상태갱신일시
            'lastTsdt':sqlalchemy.types.VARCHAR(14), # 마지막 충전시작일시
            'lastTedt':sqlalchemy.types.VARCHAR(14), # 마지막 충전종료일시
            'nowTsdt':sqlalchemy.types.VARCHAR(14), # 충전중 시작일시
            'powerType':sqlalchemy.types.VARCHAR(14), # 충전 타입
            'output':sqlalchemy.types.VARCHAR(5), # 충전용량
            'method':sqlalchemy.types.VARCHAR(10), # 충전방식
            'zcode':sqlalchemy.types.Integer(), # 지역코드
            'parkingFree':sqlalchemy.types.VARCHAR(1), # 주차료무료
            'note':sqlalchemy.types.VARCHAR(200), # 충전소 안내
            'limitYn':sqlalchemy.types.VARCHAR(1), # 이용자 제한
            'limitDetail':sqlalchemy.types.VARCHAR(100), # 이용제한 사유
            'delYn':sqlalchemy.types.VARCHAR(1), # 삭제 여부
            'delDetail':sqlalchemy.types.VARCHAR(100), # 삭제 사유
    }

    # null값 처리
    missing_fill_val = {"statNm" : "null",
                        "statId": "null",
                        "chgerId": "0",
                        "chgerType": "00",
                        "addr": "null", 
                        "location": "null",
                        "lat": "0",
                        "lng": "0",
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

    # name = db에 저장할 테이블명
    df.to_sql(name='전국_Info', con=engine, if_exists='replace',index=True,dtype=dtypesql)



    # DB에서 경기도_Info 테이블 딕셔너리형으로 불러오기
    conn = pymysql.connect(host="192.168.56.101",user="bigdata",password="Bigdata123!!",db="MapDB",charset='utf8')
    curs = conn.cursor(pymysql.cursors.DictCursor) 
    sql = 'select * from 전국_Info'
    curs.execute(sql)
    rows = curs.fetchall()

    # DB 값 리스트에 넣기
    data_list = []
    for row in rows:
        data_list.append(row)

    return pd.DataFrame(data_list)


def convertGeoLoc(h, m, s): 
    return h + (m + s / 60) / 60

g = geocoder.ip('me') # ip기반 현재위치

df = update_db("서울")

def map(request):
    # 상단 메뉴
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = SearchForm()
    address = Search.objects.all().last()
    location = g
    lat = location.lat
    lng = location.lng
    if lat == None or lng == None:
        address.delete()
        return HttpResponse('You address input is invalid')

    # 지도 생성
    m = folium.Map(
        location=g.latlng,
        # tiles='cartodbpositron',
        zoom_start=13,
        width = "100%",
    )
    # 지도 전체화면
    plugins.Fullscreen(position='topright',
                   title='Click to Expand',
                   title_cancel='Click to Exit',
                   force_separate_button=True).add_to(m)

    #지도 스크롤 가능
    plugins.MousePosition().add_to(m)

    for _, elem in df.iterrows():
        # 충전기 타입
        if elem['chgerType'] == '01':
            elem['chgerType'] = 'DC차데모'
        elif elem['chgerType'] == '02':
            elem['chgerType'] = 'AC완속'
        elif elem['chgerType'] == '03':
            elem['chgerType'] = 'DC차데모+AC3상'
        elif elem['chgerType'] == '04':
            elem['chgerType'] = 'DC콤보'
        elif elem['chgerType'] == '05':
            elem['chgerType'] = 'DC차데모+DC콤보'
        elif elem['chgerType'] == '06':
            elem['chgerType'] = 'DC차데모+AC3상+DC콤보'
        elif elem['chgerType'] == '07':
            elem['chgerType'] = 'AC3상'

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
        # 충전소 마커
        folium.Marker(
                icon = folium.Icon(color=icon_color),
                location=(float(elem['lat']), float(elem['lng'])),
                popup="<html><head><style>h4 {color:blue;font-family:'Noto Sans KR',sans-serif;}</style><body><pre><h4><b>"+elem['statNm']+"</b></h4><br> 주소: "+elem['addr']+"<br> 운영시간: "+elem['useTime']+"<br> 상태: "+elem['stat']+"<br> 충전기타입: "+elem['chgerType']+"</pre></body></html>"
            ).add_to(m)
    # 현위치 마커
    folium.Marker(
            icon = folium.Icon(color='red', icon='star'),
            location=(g.latlng),
            tooltip='ip기반 현재위치'
        ).add_to(m)

    # Get HTML Representation of Map Object
    m = m._repr_html_()
    context = {
    'm': m,
    'form': form,
    }
    return render(request, 'main/map.html', context)