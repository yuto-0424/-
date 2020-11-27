# supported by 近藤さん
import urllib.request, urllib.error
from bs4 import BeautifulSoup
import re

# チャットボットから位置情報取得し、データ取得
def warning_info(areaurl, original_location):

    # 正規表現で '市区町村郡' を抽出
    city_pattern = '(...??[都道府県])((?:旭川|伊達|石狩|盛岡|奥州|田村|南相馬|那須塩原|東村山\
                    |武蔵村山|羽村|十日町|上越|富山|野々市|大町|蒲郡|四日市|姫路|大和郡山|廿日市|下>松|岩国\
                    |田川|大村|宮古|富良野|別府|佐伯|黒部|小諸|塩尻|玉野|周南)市|(?:余市|高市|[^市]{2,3}?)郡\
                    (?:玉村|大町|.{1,5}?)[町村]|(?:.{1,4}市)?[^町]{1,4}?区|.{1,7}?[市町村])(.+)'
    city = re.split(city_pattern, original_location)

    # 取得したURLにアクセス
    areahtml = urllib.request.urlopen(areaurl)
    # htmlをBeautifulSoupで扱う
    areasoup = BeautifulSoup(areahtml, "html.parser")
    areaprefecture = areasoup.select("head > headline > information[type$='（府県予報区等）'] > item > areas > name")[0].text

    # 末尾が"(市町村等)"である<type>を含む<warning>を取得
    # つまり<Warning type="気象警報・注意報（市町村等）">を取得
    information = areasoup.find("information", type = re.compile(".*（市町村等）$"))
    item = information.find_all("item")
    for areainfo in item:
        areacity = areainfo.select("item > areas > name")[0].text

        print(areacity + " : ", end="")
        kind = areainfo.find_all("kind")
        areastatus = ""
        for disast in kind:
            if disast.find("name") is not None:
                areastatus = areastatus + disast.find("name").string + " "
            if areastatus == "解除 ":
                areastatus = "警報・注意報なし"
        print(areastatus)

    print(areacity + " : ", end="")
#--- xmlにアクセスし、各URLから各気象台の情報を取得 ---

# アクセスするURL
url = "http://www.data.jma.go.jp/developer/xml/feed/extra_l.xml"
# URLのhtmlを取得
html = urllib.request.urlopen(url)
# htmlをBeautifulSoupで扱う
soup = BeautifulSoup(html, "xml")
# <entry>(気象台)毎にデータを格納する
entry = soup.find_all("entry")
# 検索ワード (最新版データ)
xmlver = "気象警報・注意報（Ｈ２７）"
# 検索ワード (対象の気象台)
moname = [
'旭川地方気象台',
'宇都宮地方気象台',
'横浜地方気象台',
'岡山地方気象台',
'沖縄気象台',
'下関地方気象台',
'岐阜地方気象台',
'気象庁',
'気象庁予報部',
'宮古島地方気象台',
'宮崎地方気象台',
'京都地方気象台',
'金沢地方気象台',
'釧路地方気象台',
'熊谷地方気象台',
'熊本地方気象台',
'広島地方気象台',
'甲府地方気象台',
'高松地方気象台',
'高知地方気象台',
'佐賀地方気象台',
'札幌管区気象台',
'山形県 山形地方気象台',
'山形地方気象台',
'鹿児島地方気象台',
'室蘭地方気象台',
'秋田県 秋田地方気象台',
'秋田地方気象台',
'松江地方気象台',
'松山地方気象台',
'新潟地方気象台',
'神戸地方気象台',
'水戸地方気象台',
'盛岡地方気象台',
'青森地方気象台',
'静岡地方気象台',
'石垣島地方気象台',
'仙台管区気象台',
'前橋地方気象台',
'帯広測候所',
'大阪管区気象台',
'大分地方気象台',
'稚内地方気象台',
'銚子地方気象台',
'長崎地方気象台',
'長野地方気象台',
'鳥取地方気象台',
'津地方気象台',
'徳島県 徳島地方気象台',
'徳島地方気象台',
'奈良地方気象台',
'南大東島地方気象台',
'函館地方気象台',
'彦根地方気象台',
'富山地方気象台',
'福井地方気象台',
'福岡管区気象台',
'福島地方気象台',
'名古屋地方気象台',
'名瀬測候所',
'網走地方気象台',
'和歌山地方気象台'
]

# 検索ワード含む最初の<entry>の<link>内URLを取得
for moname in moname:
    for info in entry:
        if info.find("title").string == xmlver:
            if info.find("name").string == moname:
                areaurl = info.find("link").get("href")
                warning_info(areaurl)
                break

#---                ここまで                 ---
