import pandas as pd
import sys

def road_info():
    df = pd.read_html("https://roadway.yahoo.co.jp/list", index_col=0)[0]
    result_road = df.to_csv(header=False)

    return result_road
