import json
import pandas as pd

# jsonファイルを辞書として読み込み
with open("shelters.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)

# DataFrame生成（列ラベル設定）
df = pd.DataFrame(columns=[
    "name", "addr", "flood", "landslide", "hightide", "earthquake",
    "tsunami", "fire", "inflood", "volcanic"
])

# featuresごとに各項目を変数に入れる
for feature in data["features"]:
    # 緯度
    lat = feature["geometry"]["coordinates"][1]
    # 経度
    lon = feature["geometry"]["coordinates"][0]
    name = feature["properties"]["指定緊急避難場所"]
    addr = feature["properties"]["所在地"]
    flood = feature["properties"]["洪水"]
    landslide = feature["properties"]["がけ崩れ、土石流及び地滑り"]
    hightide = feature["properties"]["高潮"]
    earthquake = feature["properties"]["地震"]
    tsunami = feature["properties"]["津波"]
    fire = feature["properties"]["大規模な火事"]
    inflood = feature["properties"]["内水氾濫"]
    volcanic = feature["properties"]["火山現象"]

    # 各変数でSeries生成
    se = pd.Series(
        {"name": name, "addr": addr, "lat": lat, "lon": lon,
         "flood": flood, "landslide": landslide, "hightide": hightide,
         "earthquake": earthquake, "tsunami": tsunami, "fire": fire,
         "inflood": inflood, "volcanic": volcanic}
    )

    # DataFrameに縦方向に連結（行ラベルは0から振り直し）
    df = df.append(se, ignore_index=True)


# CSVファイルに書き出し（行ラベルなし）
df.to_csv("shelters.csv", index=False)