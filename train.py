import pandas as pd
import sys

def train_info():
    df = pd.read_html("https://transit.yahoo.co.jp/traininfo/area", index_col=0)[0]
    result_train = df.to_csv(header=False)

    return result_train
