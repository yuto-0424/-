import requests
from bs4 import BeautifulSoup
import re

#位置情報から天気を返す
def weather_info(original_location):
    # 住所の中から郵便番号抽出
    location = re.findall('\d{3}-\d{4}', original_location)
    #住所検索
    url = "https://weather.yahoo.co.jp/weather/search/?p=" + location[0]
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    content = soup.find(class_="serch-table")
    #URL取得
    location_url = "http:" + content.find('a').get('href')
    r = requests.get(location_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    content = soup.find(id='yjw_pinpoint_today').find_all('td')
    info = []

    for each in content[1:]:
        info.append(each.get_text().strip('\n'))

    #時間
    time = info[:8]
    #天気
    weather = info[9:17]
    #気温
    temperature = info[18:26]
    #上の3つの情報を合わせる
    weather_info = [(time[i], weather[i], temperature[i]) for i in range(8)]

    result_weather = [('{0[0]}: {0[1]}, {0[2]}°C'.format(weather_info[i])) for i in range(8)]
    result_weather = ('{}\nの今日の天気は\n'.format(original_location) + '\n'.join(result_weather) + '\nです。')

    return result_weather
