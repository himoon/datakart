import os
from pathlib import Path

import dotenv
import pandas as pd

from datakart import Datagokr

dotenv.load_dotenv(Path(__file__).parent.parent / ".env", override=True)

try:
    Datagokr()
    raise AssertionError("Datagokr()에서 예외가 발생해야 합니다")
except Exception:
    assert True

DATAGO_KEY = os.getenv("DATAGO_KEY")

# 법정동 코드 조회
client = Datagokr(api_key=DATAGO_KEY)
resp = client.lawd_code("서울특별시")
pd.DataFrame(resp).info()
"""
<class 'pandas.DataFrame'>
RangeIndex: 493 entries, 0 to 492
Data columns (total 13 columns):
 #   Column         Non-Null Count  Dtype
---  ------         --------------  -----
 0   region_cd      493 non-null    str
 1   sido_cd        493 non-null    str
 2   sgg_cd         493 non-null    str
 3   umd_cd         493 non-null    str
 4   ri_cd          493 non-null    str
 5   locatjumin_cd  493 non-null    str
 6   locatjijuk_cd  493 non-null    str
 7   locatadd_nm    493 non-null    str
 8   locat_order    493 non-null    int64
 9   locat_rm       493 non-null    str
 10  locathigh_cd   493 non-null    str
 11  locallow_nm    493 non-null    str
 12  adpt_de        493 non-null    str
dtypes: int64(1), str(12)
memory usage: 50.2 KB
"""

# 아파트 거래 정보 조회
client = Datagokr(api_key=DATAGO_KEY)
resp = client.apt_trade(lawd_code="11110", deal_ym="202301")
pd.DataFrame(resp).info()
"""
<class 'pandas.DataFrame'>
RangeIndex: 7 entries, 0 to 6
Data columns (total 20 columns):
 #   Column            Non-Null Count  Dtype
---  ------            --------------  -----
 0   aptDong           4 non-null      str
 1   aptNm             7 non-null      str
 2   buildYear         7 non-null      str
 3   buyerGbn          0 non-null      object
 4   cdealDay          0 non-null      object
 5   cdealType         0 non-null      object
 6   dealAmount        7 non-null      str
 7   dealDay           7 non-null      str
 8   dealMonth         7 non-null      str
 9   dealYear          7 non-null      str
 10  dealingGbn        7 non-null      str
 11  estateAgentSggNm  7 non-null      str
 12  excluUseAr        7 non-null      str
 13  floor             7 non-null      str
 14  jibun             7 non-null      str
 15  landLeaseholdGbn  7 non-null      str
 16  rgstDate          7 non-null      str
 17  sggCd             7 non-null      str
 18  slerGbn           0 non-null      object
 19  umdNm             7 non-null      str
dtypes: object(4), str(16)
memory usage: 1.2+ KB
"""

# 아파트 거래 정보 조회
client = Datagokr(api_key=DATAGO_KEY)
resp = client.apt_trade_detailed(lawd_code="11110", deal_ym="201801")
pd.DataFrame(resp).info()
"""
<class 'pandas.DataFrame'>
RangeIndex: 89 entries, 0 to 88
Data columns (total 32 columns):
 #   Column            Non-Null Count  Dtype
---  ------            --------------  -----
 0   aptDong           0 non-null      object
 1   aptNm             89 non-null     str
 2   aptSeq            89 non-null     str
 3   bonbun            89 non-null     str
 4   bubun             89 non-null     str
 5   buildYear         89 non-null     str
 6   buyerGbn          0 non-null      object
 7   cdealDay          0 non-null      object
 8   cdealType         0 non-null      object
 9   dealAmount        89 non-null     str
 10  dealDay           89 non-null     str
 11  dealMonth         89 non-null     str
 12  dealYear          89 non-null     str
 13  dealingGbn        0 non-null      object
 14  estateAgentSggNm  0 non-null      object
 15  excluUseAr        89 non-null     str
 16  floor             89 non-null     str
 17  jibun             89 non-null     str
 18  landCd            89 non-null     str
 19  landLeaseholdGbn  89 non-null     str
 20  rgstDate          0 non-null      object
 21  roadNm            89 non-null     str
 22  roadNmBonbun      89 non-null     str
 23  roadNmBubun       89 non-null     str
 24  roadNmCd          89 non-null     str
 25  roadNmSeq         89 non-null     str
 26  roadNmSggCd       89 non-null     str
 27  roadNmbCd         87 non-null     str
 28  sggCd             89 non-null     str
 29  slerGbn           0 non-null      object
 30  umdCd             89 non-null     str
 31  umdNm             89 non-null     str
dtypes: object(8), str(24)
memory usage: 22.4+ KB
"""
