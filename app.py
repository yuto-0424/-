from flask import Flask, request, abort
import os
import urllib3.request
import urllib.parse
import sys
import json
import pandas as pd
import pyproj
import requests
import re
import datetime
import urllib3.request as req
#import pymysql
import weather as wes
#import warning as was
import train as ts
import road as rs


from bs4 import BeautifulSoup

from linebot import (
    LineBotApi, WebhookHandler
)

from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FollowEvent, LocationMessage, LocationSendMessage,
    TemplateSendMessage, MessageAction,
    ButtonsTemplate, URIAction,
    PostbackAction, PostbackEvent,
    QuickReply, QuickReplyButton
)

from linebot.exceptions import (
    LineBotApiError
)

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["0ZVOkcQGp5HUEz+a1tRYIpcrLGiLSwSA4VISRSHsB+JJNChMXW5aOj/evLvh3e4iNVbimMiK05GS/W0KGEFo9ZvFQ3 Kto7mpEQh5unm4aJz+ヒットKYoW8qn/0KbDenX1BvUY1b8GgLoeBW1Fu1W/ZcAdB04t89/1O/w1cDnyilFU="]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(0ZVOkcQGp5HUEz+a1tRYIpcrLGiLSwSA4VISRSHsB+JJNChMXW5aOj/evLvh3e4iNVbimMiK05GS/W0KGEFo9ZvFQ3 Kto7mpEQh5unm4aJz+ヒットKYoW8qn/0KbDenX1BvUY1b8GgLoeBW1Fu1W/ZcAdB04t89/1O/w1cDnyilFU=)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# ユーザが選択した災害が入る変数
which_disaster_value = ""

# 送信メッセージ格納変数
text = ""
text_l = ""
text_m = ""
lat_base = None
lon_base = None

# 分岐に利用するグローバル変数
switch = None
switch_shelter = 1
switch_weather = 2
switch_warning = 3

# 避難場所のCSVを読み込み（欠損値は""に置換）
df = pd.read_csv("mergeFromCity.csv").fillna("")


# 2点間の距離を計算する関数
def calc_distance(lat1, lon1, lat2, lon2):
    # インスタンス生成（世界測地系：WGS84）
    g = pyproj.Geod(ellps="WGS84")
    # [方位角, 逆方向の方位角, 距離]のリスト
    result = g.inv(lon1, lat1, lon2, lat2)
    # 距離を返す
    distance = result[2]
    return round(distance)


# 災害一覧
disaster_dict = {
    "earthquake": "地震", "tsunami": "津波", "flood": "洪水",
    "landslide": "土砂災害", "inflood": "内水氾濫", "hightide": "高潮",
    "fire": "大規模火災", "volcanic": "火山噴火"
}

# 災害一覧（避難場所が対応する災害に「◎」）を表示
def format_disaster_info(row):
    message = ""
    for key in disaster_dict:
        message += f"\n{disaster_dict[key]}：{row[key]}"
    return message



# ”/callback"にアクセスした時の処理
@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)

    # プログラムの通常の操作中に発生したイベントの報告
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    # 例外処理（ステータスコード：400）
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ユーザからメッセージを受信した時の処理
@handler.add(MessageEvent, message=(TextMessage, LocationMessage))
def handle_system(event):
    # LINE DevelopersからこのreplyTokenが来たときにエラーになるのを回避
    if event.reply_token == "00000000000000000000000000000000":
        return

    global text
    global text_l
    global text_m
    global lat_base
    global lon_base

    # ユーザから位置情報を受信した時の処理
    if isinstance(event.message, LocationMessage):

        text_l = event.message.address

        lat_base = event.message.latitude
        lon_base = event.message.longitude

        buttons_template = ButtonsTemplate(
            text="位置情報からどの情報を取得しますか？",
            actions=[
                MessageAction(label="避難場所",
                              text="避難場所"),
                MessageAction(label="天気",
                              text="天気"),
#                MessageAction(label="注意報・警報",
#                              text="注意報・警報"),
            ]
        )
        template_message = TemplateSendMessage(
            alt_text='位置情報送信時ボタン', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)


    # ユーザから受信したメッセージのテキスト
    # text は ユーザからのメッセージ格納
    #text = event.message.text

    elif isinstance(event.message, TextMessage):
        text = event.message.text

        # ユーザからメッセージ受信時の動作
        if text == '避難場所':
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="{}\n\n{}\n{}".format(
                        "選択した災害に対応した最寄りの避難場所を表示します",
                        "災害の種類を選択してください",
                        "表示されていない災害は、横にスクロールすると現れます"
                    ),
                    # クイックリプライ設定
                    quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(
                                    label="地震",
                                    text="地震"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label="津波",
                                    text="津波"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label="洪水",
                                    text="洪水"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label="土砂災害",
                                    text="土砂災害"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label="内水氾濫",
                                    text="内水氾濫"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label="高潮",
                                    text="高潮"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label="大規模火災",
                                    text="大規模火災"
                                )
                            ),
                            QuickReplyButton(
                                action=MessageAction(
                                    label="火山噴火",
                                    text="火山噴火"
                                )
                            ),
                        ]
                    )
                )
            )

        elif text in [
            "地震", "津波", "洪水", "土砂災害", "内水氾濫", "高潮", "大規模火災",
            "火山噴火"
        ]:
            global which_disaster_value
            which_disaster_value = text

            # 選択した災害の種類（辞書から取り出す）
            which_disaster_key = ""
            for key, value in disaster_dict.items():
                if value == which_disaster_value:
                    which_disaster_key = key

            # 受信した緯度・経度から半径5km程度以内の避難場所を抽出
            from_lat = lat_base - 0.05
            to_lat = lat_base + 0.05
            from_lon = lon_base - 0.05
            to_lon = lon_base + 0.05

            df_near = df.query(
                f"{which_disaster_key} == '◎' & \
                lat > {from_lat} & lat < {to_lat} & \
                lon > {from_lon} & lon < {to_lon}"
            )

            min_distance = None
            min_row = None

            # 最寄りの避難場所検索
            for index, row in df_near.iterrows():

                shelter_lat = row["lat"]
                shelter_lon = row["lon"]

                distance = calc_distance(
                    lat_base, lon_base,
                    shelter_lat, shelter_lon
                )
                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    min_row = row

            # 避難場所がなかった場合
            if min_distance == None:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="{}\n{}".format(
                        "現在その場所の近くには、指定された災害の避難場所は登録されていません",
                        "詳細な情報は、自治体のサイトなどを確認ください"
                    ))
                )

            # 避難場所があった場合
            else:
                message = "{}\n「{}」\n{}\n".format(
                    "最寄りの避難場所は",
                    min_row["name"],
                    "です"
                )
                message += format_disaster_info(min_row)

                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        TextSendMessage(text=message),
                        LocationSendMessage(
                            title=f"{min_row['name']}\n（距離：{min_distance}m）",
                            address=min_row['addr'],
                            latitude=min_row['lat'],
                            longitude=min_row['lon']
                        )
                    ]
                )


        elif text == "天気":
            result_weather = wes.weather_info(text_l)
            line_bot_api.reply_message(
                event.reply_token,[
                    TextSendMessage(
                        text="{}".format(
                            "送信した地域の天気を表示します",
                        )),
                    TextSendMessage(text=result_weather)
                ]
            )

        elif text == "注意報・警報":
            #result_warning = was.warning_info(text_l)
            line_bot_api.reply_message(
                event.reply_token,[
                    TextSendMessage(
                        text="{}".format(
                            "送信した地域に発令されている警報などを表示します",
                        )),
                    TextSendMessage(text="{}\n\n{}\n{}\n{}\n{}".format(
                            "※この結果はダミーです※",
                            "新宿区:強風注意報",
                            "千代田区:強風注意報 ",
                            "中央区:強風注意報 波浪注意報",
                            "渋谷区:警報・注意報なし",
                    )),
                ]
            )

        elif text == "交通情報":
            buttons_template = ButtonsTemplate(
                text="どの情報を取得しますか",
                actions=[
                    MessageAction(label="電車運行情報",
                                  text="電車運行情報"),
                    MessageAction(label="道路交通情報",
                                  text="道路交通情報"),
                ]
            )
            template_message = TemplateSendMessage(
                alt_text='交通情報ボタン', template=buttons_template)
            line_bot_api.reply_message(event.reply_token, template_message)

        elif text == "電車運行情報":
            result_train = ts.train_info()
            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(
                    text="{}\n{}".format(
                        "電車の運行情報を表示します",
                        "現在遅延している路線のみ表示されます",
                    )
                ),
                TextSendMessage(text=result_train)
                ]
            )


        elif text == "道路交通情報":
            result_road = rs.road_info()
            line_bot_api.reply_message(
                event.reply_token,[
                TextSendMessage(
                    text="{}\n{}".format(
                        "道路の情報を表示します",
                        "渋滞などが発生している道路のみ表示されます",
                    )
                ),
                TextSendMessage(text=result_road)
                ]
            )

        elif text == "その他":
            buttons_template = ButtonsTemplate(
                text="何かお困りですか",
                actions=[
                    MessageAction(label="使い方",
                                  text="使い方"),
                    MessageAction(label="避難場所とは",
                                  text="避難場所とは"),
                    MessageAction(label="それ以外(開発者にメール)",
                                  text="お問い合わせ"),
                    MessageAction(label="システムを評価する",
                                  text="評価"),

                ]
            )
            template_message = TemplateSendMessage(
                alt_text='ヘルプボタン', template=buttons_template)
            line_bot_api.reply_message(event.reply_token, template_message)

        elif text == "使い方":
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text="{}\n{}\n{}".format(
                        "このチャットボットの使い方を説明します",
                        "最初にメニューから知りたい情報のボタンを押してください",
                        "そうするとチャットボットからメッセージが来るので同様にボタンを押してください",
                    )),
                    TextSendMessage(text="{}\n\n{}\n\n{}\n\n{}".format(
                        "「位置情報利用」ボタンを押した場合、送信した位置情報を利用した情報が提示されます",
                        "「避難場所」ボタンの場合は、下部に表示される災害ボタンから災害の種類を選択することでその災害に対応した最寄りの避難場所を提示します",
                        "「天気」ボタンの場合は、送信した地域の3時間ごと(0時から21時まで)の天気を提示します",
                        "「注意報・警報」ボタンの場合は、送信した地域に発令されている気象警報を提示します",
                    )),
                    TextSendMessage(text="{}\n\n{}\n\n{}".format(
                        "「交通情報」ボタンを押した場合は、「電車運行情報」と「道路交通情報」を選択します",
                        "「電車運行情報」ボタンを押した場合は、遅延などが発生している路線を提示します",
                        "「道路交通情報」ボタンを押した場合も同様に、渋滞や規制などで異常が発生している道路を提示します",
                    )),
                ]
            )

        elif text == "避難場所とは":
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text="{}\n{}\n{}\n\n{}\n{}\n{}\n\n{}".format(
                        "「避難場所」は",
                        "正式には「指定緊急避難場所」といい",
                        "災害の危険から命を守るために避難する場所として、自治体が指定した施設・場所のことです",
                        "「地震」「津波」「洪水」",
                        "「土砂災害(崖崩れ・土石流・地滑り)」",
                        "「高潮」「内水氾濫」「大規模火事」「火山噴火」",
                        "の種類ごとに指定されています",
                    )),
                    TextSendMessage(text="{}\n{}\n{}\n{}".format(
                        "「避難所」は、正式には「指定避難所」といい、",
                        "災害により住宅を失った場合等において、",
                        "一定期間避難生活をする場所として、",
                        "自治体が指定した施設のことです",
                    )),
                ]
            )


        elif text == "お問い合わせ":
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text="{}\n{}".format(
                        "ヘルプ項目や検索してもわからないこと、",
                        "システムの問題、意見・要望などあれば下のメールアドレスに連絡ください",
                    )),
                    TextSendMessage(text="{}".format(
                        "hogehoge",
                    )),
                ]
            )
        elif text == "評価":
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text="{}\n{}\n{}".format(
                        "ご協力ありがとうございます",
                        "5段階評価のものが4つと自由記述が2カ所あります",
                        "URLからGoogleフォームにて記入してください",
                    )),
                    TextSendMessage(text="{}".format(
                        "https://forms.gle/sYX3aR9Dqxp83DJt8",
                    )),
                ]
            )

# 友だち追加またはブロック解除された時（フォローイベント）
@handler.add(FollowEvent)
def handle_follow(event):
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="{}\n{}\n\n{}\n{}".format(
            "登録ありがとうございます",
            "このチャットボットは選択された情報について返信します",
            "しばらく使わなかった場合に応答に少し時間がかかることがあります",
            "ご了承ください"
        ))
    )

if __name__ == "__main__":
    # ポート番号の設定
    # 環境変数にkey"PORT"があればそのvalue、なければ5000を整数で返す
    port = int(os.getenv("PORT", 5000))

    # アプリケーションを実行（どこからでもアクセス可能）
    app.run(host="0.0.0.0", port=port)
