"""
import json
import pathlib

import pandas as pd

WORK_DIR = pathlib.Path(__file__).parent

df_raw = pd.read_csv(WORK_DIR / "naver_ad_biztp.tsv", delimiter="\t", header=None)
df_raw.columns = ["id", "name_kr", "pid", "level"]
df_raw.info()
df_raw.sort_values(["id"], inplace=True)

with open(WORK_DIR / "naver_ad_biztp.json", "w") as fp:
    json.dump(df_raw.to_dict("records"), fp, ensure_ascii=False, separators=(",", ":"))
"""
