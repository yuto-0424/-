# -*- coding: utf-8 -*-

# 〈標準ライブラリ〉
import os

# 〈外部パッケージ〉
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FollowEvent,
    UnfollowEvent, LocationMessage, LocationSendMessage,
    TemplateSendMessage, MessageAction, ButtonsTemplate,
    URIAction, PostbackAction, PostbackEvent, QuickReply,
    QuickReplyButton
    )
import pandas as pd
# 距離の計算
import pyproj


# Flaskのインスタンス生成
app = Flask(__name__)

# 環境変数に設定したkeyを取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

# 各ライブラリのインスタンス生成
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# ユーザが選択した災害が入る変数
which_disaster_value = ""


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
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    # LINE DevelopersからこのreplyTokenが来たときにエラーになるのを回避
    if event.reply_token == "00000000000000000000000000000000":
        return

    # ユーザから受信したメッセージのテキスト
    text = event.message.text

    if text == '避難場所の確認':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="{}\n\n{}\n{}\n{}".format(
                    "いちばん近い避難場所を確認するよ"+chr(0x100003),
                    "避難場所は、災害の種類別に指定されているよ",
                    "災害の種類を選んでね",
                    "表示されていない災害は、横にスクロールすると出てくるよ"
                ),
                # クイックリプライ設定
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=PostbackAction(
                                label="地震",
                                text="地震",
                                data="request_location"
                            )
                        ),
                        QuickReplyButton(
                            action=PostbackAction(
                                label="津波",
                                text="津波",
                                data="request_location"
                            )
                        ),
                        QuickReplyButton(
                            action=PostbackAction(
                                label="洪水",
                                text="洪水",
                                data="request_location"
                            )
                        ),
                        QuickReplyButton(
                            action=PostbackAction(
                                label="土砂災害",
                                text="土砂災害",
                                data="request_location"
                            )
                        ),
                        QuickReplyButton(
                            action=PostbackAction(
                                label="内水氾濫",
                                text="内水氾濫",
                                data="request_location"
                            )
                        ),
                        QuickReplyButton(
                            action=PostbackAction(
                                label="高潮",
                                text="高潮",
                                data="request_location"
                            )
                        ),
                        QuickReplyButton(
                            action=PostbackAction(
                                label="大規模火災",
                                text="大規模火災",
                                data="request_location"
                            )
                        ),
                        QuickReplyButton(
                            action=PostbackAction(
                                label="火山噴火",
                                text="火山噴火",
                                data="request_location"
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

    elif text == "お役立ちリンク集":
        buttons_template = ButtonsTemplate(
            text="どのリンク集を見る？",
            actions=[
                MessageAction(label="日頃の備え",
                              text="日頃の備え"),
                MessageAction(label="安否確認サービス",
                              text="安否確認サービス"),
                MessageAction(label="災害情報",
                              text="災害情報"),
            ]
        )
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)

    elif text == "日頃の備え":
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text="日頃の備えに役立つサイトの一部を紹介するね"
                                     +chr(0x100003)),
                TextSendMessage(text="{}\n{}\n\n{}\n{}\n\n{}\n{}\n".format(
                    "NHK そなえる防災",
                    "https://www.nhk.or.jp/sonae/",
                    "東京都 防災ブック「東京防災」",
                    "https://www.bousai.metro.tokyo.lg.jp/1002147/index.html",
                    "Yahoo! JAPAN 天気・災害 「防災手帳」",
                    "https://emg.yahoo.co.jp/notebook/"
                ))
            ]
        )

    elif text == "安否確認サービス":
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text="もしものときのために、使い方を確認しておこうね"
                                     +chr(0x100003)),
                TextSendMessage(text="{}\n\n{}\n{}\n\n{}\n{}\n\n{}\n{}\n\n{}\n{}\
                \n\n{}\n{}\n\n{}\n{}\n".format(
                    "●文字で登録するもの",
                    "NTT東日本・NTT西日本 「災害用伝言板（web171）」",
                    "https://www.web171.jp/web171app/topRedirect/",
                    "NTTドコモ 「災害用伝言板」",
                    "https://www.nttdocomo.co.jp/info/disaster/disaster_board/index.html",
                    "au「災害用伝言板サービス」",
                    "https://www.au.com/mobile/anti-disaster/saigai-dengon/",
                    "ソフトバンク「災害用伝言板」",
                    "https://www.softbank.jp/mobile/service/dengon/",
                    "Y! mobile（ワイモバイル）「災害用伝言板サービス」",
                    "https://www.ymobile.jp/service/dengon/",
                    "Google 「パーソンファインダー（安否情報）」",
                    "https://www.google.org/personfinder/japan/"
                )),
                TextSendMessage(text="{}\n\n{}\n{}\n".format(
                    "●音声で登録するもの",
                    "NTT東日本・NTT西日本 「災害用伝言ダイヤル（171）」",
                    "http://www.ntt-east.co.jp/saigai/voice171/index.html"
                )),
                TextSendMessage(text="{}\n\n{}\n{}\n".format(
                    "●各サービスに登録された情報を一括検索",
                    "NTT・NHK 「J-anpi 安否情報まとめて検索」",
                    "https://anpi.jp/top"
                ))
            ]
        )

    elif text == "災害情報":
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text="災害が発生したとき、情報の確認に役立つサイトの一部を紹介するね"
                                     +chr(0x100003)),
                TextSendMessage(text="{}\n{}\n\n{}\n{}\n\n{}\n{}\n\n{}\n{}\n".format(
                    "気象庁 防災情報",
                    "https://www.jma.go.jp/jma/menu/menuflash.html",
                    "国土交通省 災害・防災情報",
                    "http://www.mlit.go.jp/saigai/index.html",
                    "NHK NEWS WEB",
                    "https://www3.nhk.or.jp/news/?utm_int=all_header_logo_news",
                    "Yahoo! JAPAN 天気・災害",
                    "https://weather.yahoo.co.jp/weather/"
                ))
            ]
        )

    elif text == "避難のQ&A":
        buttons_template = ButtonsTemplate(
            text="どのQ&Aを見る？",
            actions=[
                MessageAction(label="避難場所と避難所は違う？",
                              text="避難場所と避難所は違う？"),
                MessageAction(label="そもそも避難って何？",
                              text="そもそも避難って何？"),
                MessageAction(label="避難するタイミングは？",
                              text="避難するタイミングは？"),
                MessageAction(label="ハザードマップって何？",
                              text="ハザードマップって何？")
            ]
        )
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)

    elif text == "避難場所と避難所は違う？":
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text="避難場所と避難所は、名前は似ているけど違うものだよ"
                                     +chr(0x100002)),
                TextSendMessage(text="{}\n{}\n\n{}\n\n{}".format(
                    "「避難場所」（正式には「指定緊急避難場所」）は、",
                    "「切迫した災害の危険から命を守るために避難する場所として、\
あらかじめ市町村が指定した施設・場所」",
                    "つまり、命を守るために緊急的に避難する場所だよ",
                    "「洪水」「崖崩れ、土石流及び地滑り」「高潮」「地震」\
「津波」「大規模な火事」「内水氾濫」「火山現象」の種類ごとに指定されているよ"
                )),
                TextSendMessage(text="{}\n{}\n\n{}".format(
                    "「避難所」（正式には「指定避難所」）は、",
                    "「災害により住宅を失った場合等において、一定期間\
避難生活をする場所として、あらかじめ市町村が指定した施設」",
                    "つまり、災害で家に戻れなくなった場合などに避難生活を送る場所だよ"
                )),
                TextSendMessage(text="{}\n\n{}\n{}\n\n{}\n{}\n".format(
                    "詳しく知りたい場合はこれを見てね"+chr(0x100003),
                    "内閣府 「避難勧告等に関するガイドライン① （避難行動・情報伝達編）」",
                    "http://www.bousai.go.jp/oukyu/hinankankoku/pdf/hinan_guideline_01.pdf",
                    "国土地理院 防災関連 「指定緊急避難場所データ」",
                    "https://www.gsi.go.jp/bousaichiri/hinanbasho.html"
                ))
            ]
        )

    elif text == "そもそも避難って何？":
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text="{}\n\n{}\n\n{}\n{}\n{}".format(
                    "数分から数時間後に起こるかもしれない自然災害から「命を守るための行動」だよ"
                    +chr(0x100002),
                    "内閣府の「避難勧告等に関するガイドライン」では、命を守るためにとる、\
次の全ての行動を避難行動としているよ",
                    "①指定緊急避難場所への立退き避難",
                    "②「近隣の安全な場所」（近隣のより安全な場所・建物等）への立退き避難",
                    "③「屋内安全確保」（その時点に居る建物内において、より安全な部屋等への移動）"
                )),
                TextSendMessage(text="{}\n\n{}\n{}".format(
                    "詳しく知りたい場合はこれを見てね" + chr(0x100003),
                    "内閣府 「避難勧告等に関するガイドライン① （避難行動・情報伝達編）」",
                    "http://www.bousai.go.jp/oukyu/hinankankoku/pdf/hinan_guideline_01.pdf"
                ))
            ]
        )

    elif text == "避難するタイミングは？":
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text="{}\n\n{}\n\n{}\n{}\n{}\n{}\n\n{}\n{}".format(
                    "「自分の命は自分で守る」という意識を持って、自分の判断で避難するのが原則だよ"
                    +chr(0x100002),
                    "災害が発生する危険性が高まったら、市町村から避難情報が出ることになっているよ",
                    "でも、急な災害では避難情報を出すのが間に合わないこともあるし、",
                    "人によって住んでいる場所の地形や家の構造、家族構成などは違うから、",
                    "自分で防災気象情報などを見て避難するかどうか判断して、",
                    "身の危険を感じたらすぐに避難することが大切だよ",
                    "あらかじめ、ハザードマップなどであなたの地域の災害リスクを確認して、",
                    "災害ごとに、どのタイミングでどの避難行動をとるか考えておこうね"
                )),
                TextSendMessage(text="{}\n\n{}\n{}\n{}\n{}".format(
                    "市町村が出す「避難情報」と国や都道府県が出す「防災気象情報」は、\
5段階の「警戒レベル」に対応しているよ",
                    "ポイントは、",
                    "「警戒レベル3」→高齢者等の要配慮者は避難",
                    "「警戒レベル4」→全員避難",
                    "だよ"
                )),
                TextSendMessage(text="{}\n\n{}\n{}\n\n{}\n{}\n\n{}\n{}\n".format(
                    "詳しく知りたい場合はこれを見てね"+chr(0x100003),
                    "内閣府 「警戒レベルに関するチラシ」",
                    "http://www.bousai.go.jp/oukyu/hinankankoku/h30_hinankankoku_guideline/\
pdf/keikai_level_chirashi.pdf",
                    "内閣府 「避難勧告等に関するガイドライン① （避難行動・情報伝達編）」",
                    "http://www.bousai.go.jp/oukyu/hinankankoku/pdf/hinan_guideline_01.pdf",
                    "内閣府 「避難勧告等に関するガイドラインの改定（平成31年3月29日）」",
                    "http://www.bousai.go.jp/oukyu/hinankankoku/h30_hinankankoku_guideline/\
index.html"
                ))
            ]
        )

    elif text == "ハザードマップって何？":
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text="{}\n\n{}\n\n{}".format(
                    "災害が発生したら被害が出そうな範囲や、避難場所・避難経路などを、\
地域ごとにまとめた地図のことだよ"+chr(0x100002),
                    "「洪水」「内水」「ため池」「高潮」「津波」「土砂災害」「火山」の\
種類別に作られているよ",
                    "「ハザード（hazard）」は「危険」という意味の英語だよ"
                )),
                TextSendMessage(text="{}\n\n{}\n{}\n".format(
                    "あなたの地域のハザードマップを確認したい場合は、自治体のサイトか、これを見てね"
                    +chr(0x100003),
                    "国土交通省 「ハザードマップポータルサイト」",
                    "https://disaportal.gsi.go.jp/index.html"
                ))
            ]
        )

    elif text == "このBotを友だちに教える":
        buttons_template = ButtonsTemplate(
            text="どの方法で教える？",
            actions=[
                URIAction(label="LINEで送る", uri="line://nv/recommendOA/@087yncti"),
                URIAction(label="QRコードを表示", uri="https://qr-official.line.me/\
sid/M/087yncti.png"),
                MessageAction(label="LINE IDを表示", text="LINE IDを表示")
            ]
        )
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)

    elif text == "LINE IDを表示":
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="@087yncti"))

    elif "ありがと" in text:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="どういたしまして"+chr(0x100004)))

    elif "こんにちは" in text:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="こんにちは"+chr(0x100003)))

    elif "バイバイ" in text or "ばいばい" in text or "またね" in text or \
            "さよなら" in text or "さようなら" in text:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="バイバイ、またね"+chr(0x100003)))

    # 登録されていないメッセージを受信した場合の処理
    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="{}\n{}".format(
                "ごめんね、その言葉はわからないの…"+chr(0x100011),
                "メニューから選んでね"
            ))
        )


# クイックリプライのポストバックイベントの処理
@handler.add(PostbackEvent)
def handle_postback(event):

    # 位置情報を送ってもらうメッセージを送信
    if event.postback.data == "request_location":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="{}\n{}".format(
                "ここ↓をクリックして位置情報を送ってね",
                "line://nv/location"
            ))
        )


# 避難場所のCSVを読み込み（欠損値は""に置換）
df = pd.read_csv("shelters.csv").fillna("")


# 2点間の距離を計算する関数
def calc_distance(lat1, lon1, lat2, lon2):
    # インスタンス生成（世界測地系：WGS84）
    g = pyproj.Geod(ellps="WGS84")
    # [方位角, 逆方向の方位角, 距離]のリスト
    result = g.inv(lon1, lat1, lon2, lat2)
    # 距離を返す（小数点以下四捨五入）
    distance = result[2]
    return round(distance)


# 災害一覧の辞書
disaster_dict = {
    "earthquake": "地震", "tsunami": "津波", "flood": "洪水",
    "landslide": "土砂災害", "inflood": "内水氾濫", "hightide": "高潮",
    "fire": "大規模火災", "volcanic": "火山噴火"
}


# 災害一覧（当該避難場所が対応する災害に「◎」）を表示する関数
def format_disaster_info(row):
    message = ""
    for key in disaster_dict:
        message += f"\n{disaster_dict[key]}：{row[key]}"
    return message


# ユーザから位置情報を受信した時の処理（避難場所の確認）
@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):

    # ユーザが選択した災害の種類（辞書からkeyを取り出す）
    which_disaster_key = ""
    for key, value in disaster_dict.items():
        if value == which_disaster_value:
            which_disaster_key = key

    # 受信した位置情報（緯度・経度）から±0.05度（半径5km程度？）以内の避難場所を抽出
    from_lat = event.message.latitude - 0.05
    to_lat = event.message.latitude + 0.05
    from_lon = event.message.longitude - 0.05
    to_lon = event.message.longitude + 0.05

    df_near = df.query(
        f"{which_disaster_key} == '◎' & \
        lat > {from_lat} & lat < {to_lat} & \
        lon > {from_lon} & lon < {to_lon}"
    )

    min_distance = None
    min_row = None

    # 一番近い避難場所を検索
    for index, row in df_near.iterrows():

        shelter_lat = row["lat"]
        shelter_lon = row["lon"]

        distance = calc_distance(
            event.message.latitude, event.message.longitude,
            shelter_lat, shelter_lon
        )
        if min_distance is None or distance < min_distance:
            min_distance = distance
            min_row = row

    # 該当する避難場所がなかった場合
    if min_distance == None:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="{}\n{}".format(
                "この近くには、その災害の避難場所は登録されてないみたい…",
                "詳しく確認したい場合は、自治体のサイトなどを見てみてね"
            ))
        )

    # 該当する避難場所があった場合
    else:
        message = "{}\n「{}」\n{}\n".format(
            "いちばん近い避難場所は",
            min_row["name"],
            "だよ"+chr(0x100001)
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


# 友だち追加またはブロック解除された時（フォローイベント）
@handler.add(FollowEvent)
def handle_follow(event):
    app.logger.info("Got Follow event:" + event.source.user_id)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="{}\n{}\n\n{}\n{}".format(
            "お友だちになってくれてありがとう" + chr(0x100004),
            "もしものときのために、避難場所などを確認しておこうね",
            "しばらく使わなかった場合、次にお返事するときに少し時間がかかることがあるよ",
            "ごめんね"
        ))
    )


# ブロックされた時（フォロー解除イベント）
@handler.add(UnfollowEvent)
def handle_unfollow(event):
    app.logger.info("Got Unfollow event:" + event.source.user_id)


if __name__ == "__main__":
    # ポート番号の設定
    # 環境変数にkey"PORT"があればそのvalue、なければ5000を整数で返す
    port = int(os.getenv("PORT", 5000))

    # アプリケーションを実行（どこからでもアクセス可能）
    app.run(host="0.0.0.0", port=port)
