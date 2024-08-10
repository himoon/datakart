import json
import logging
import shutil
import time
from datetime import datetime as dt
from pathlib import Path
from typing import Literal

import requests
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

API_URL_REAL = "https://openapi.koreainvestment.com:9443"
API_URL_MOCK = "https://openapivts.koreainvestment.com:29443"
KIS_DIR = Path.home() / ".kis"
M_EXCD = {
    "kospi": (  # 코스피
        "kospi_code.mst.zip",
        "kospi_code.mst",
        "https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
    ),
    "kosdaq": (  # 코스닥
        "kosdaq_code.mst.zip",
        "kosdaq_code.mst",
        "https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
    ),
    "konex": (  # 코넥스
        "konex_code.mst.zip",
        "konex_code.mst",
        "https://new.real.download.dws.co.kr/common/master/konex_code.mst.zip",
    ),
    "nas": (  # 나스닥
        "nasmst.cod.zip",
        "nasmst.cod",
        "https://new.real.download.dws.co.kr/common/master/nasmst.cod.zip",
    ),
    "nys": (  # 뉴욕
        "nysmst.cod.zip",
        "nysmst.cod",
        "https://new.real.download.dws.co.kr/common/master/nysmst.cod.zip",
    ),
    "ams": (  # 아멕스
        "amsmst.cod.zip",
        "amsmst.cod",
        "https://new.real.download.dws.co.kr/common/master/amsmst.cod.zip",
    ),
    "shs": (  # 상해
        "shsmst.cod.zip",
        "shsmst.cod",
        "https://new.real.download.dws.co.kr/common/master/shsmst.cod.zip",
    ),
    "shi": (  # 상해지수
        "shimst.cod.zip",
        "shimst.cod",
        "https://new.real.download.dws.co.kr/common/master/shimst.cod.zip",
    ),
    "szs": (  # 심천
        "szsmst.cod.zip",
        "szsmst.cod",
        "https://new.real.download.dws.co.kr/common/master/szsmst.cod.zip",
    ),
    "szi": (  # 심천지수
        "szimst.cod.zip",
        "szimst.cod",
        "https://new.real.download.dws.co.kr/common/master/szimst.cod.zip",
    ),
    "tse": (  # 도쿄
        "tsemst.cod.zip",
        "tsemst.cod",
        "https://new.real.download.dws.co.kr/common/master/tsemst.cod.zip",
    ),
    "hks": (  # 홍콩
        "hksmst.cod.zip",
        "hksmst.cod",
        "https://new.real.download.dws.co.kr/common/master/hksmst.cod.zip",
    ),
    "hnx": (  # 하노이
        "hnxmst.cod.zip",
        "hnxmst.cod",
        "https://new.real.download.dws.co.kr/common/master/hnxmst.cod.zip",
    ),
    "hsx": (  # 호치민
        "hsxmst.cod.zip",
        "hsxmst.cod",
        "https://new.real.download.dws.co.kr/common/master/hsxmst.cod.zip",
    ),
}
T_EXCD_SYMBOL = Literal[
    "kospi",  # 코스피
    "kosdaq",  # 코스닥
    "konex",  # 코넥스
    "nas",  # 나스닥
    "nys",  # 뉴욕
    "ams",  # 아멕스
    "shs",  # 상해
    "shi",  # 상해지수
    "szs",  # 심천
    "szi",  # 심천지수
    "tse",  # 도쿄
    "hks",  # 홍콩
    "hnx",  # 하노이
    "hsx",  # 호치민
]
T_EXCD_OVERSEAS = Literal[
    "nas",  # 나스닥
    "nys",  # 뉴욕
    "ams",  # 아멕스
    "shs",  # 상해
    "shi",  # 상해지수
    "szs",  # 심천
    "szi",  # 심천지수
    "tse",  # 도쿄
    "hks",  # 홍콩
    "hnx",  # 하노이
    "hsx",  # 호치민
    "bay",  # 뉴욕(주간)
    "baq",  # 나스닥(주간)
    "baa",  # 아멕스(주간)
]
T_TIMEFRAME = Literal["D", "W", "M"]


def get_api_url(mock: bool = True) -> str:
    return API_URL_MOCK if mock else API_URL_REAL


def fetch_access_token(api_key: str, api_sec: str, mock: bool = True):
    # https://apiportal.koreainvestment.com/apiservice/oauth2#L_fa778c98-f68d-451e-8fff-b1c6bfe5cd30
    api_url = get_api_url(mock=mock)
    end_point = "/oauth2/tokenP"
    params = {"grant_type": "client_credentials", "appkey": api_key, "appsecret": api_sec}
    resp = requests.post(f"{api_url}{end_point}", json=params)
    resp.raise_for_status()
    with open(KIS_DIR / "access_token.json", "wb") as fp:
        fp.write(resp.content)


def fetch_symbols(market: T_EXCD_SYMBOL):
    KIS_DIR.mkdir(exist_ok=True)
    filename, unzipped, url = M_EXCD.get(market, [])
    try:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        with open(KIS_DIR / filename, "wb") as fp:
            for chunk in resp:
                fp.write(chunk)
        shutil.unpack_archive(KIS_DIR / filename, KIS_DIR)
        if not (KIS_DIR / unzipped).is_file():
            raise FileNotFoundError(f"{unzipped} not found")
    except Exception as err:
        logger.error(err)
    finally:
        (KIS_DIR / filename).unlink(missing_ok=True)


def fetch_kline(
    access_token: str,
    api_key: str,
    api_sec: str,
    symbol: str,
    timeframe: T_TIMEFRAME,
    start: str,
    end: str,
    adj_price: bool = True,
    mock: bool = True,
) -> dict:
    # https://apiportal.koreainvestment.com/apiservice/apiservice-domestic-stock-quotations2#L_a08c3421-e50f-4f24-b1fe-64c12f723c77
    api_url = get_api_url(mock=mock)
    end_point = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    headers = {
        "content-type": "application/json",
        "authorization": access_token,
        "appKey": api_key,
        "appSecret": api_sec,
        "tr_id": "FHKST03010100",
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": symbol,
        "FID_INPUT_DATE_1": start,
        "FID_INPUT_DATE_2": end,
        "FID_PERIOD_DIV_CODE": timeframe,
        "FID_ORG_ADJ_PRC": "0" if adj_price else "1",  # 수정주가 원주가 가격 여부 0:수정주가 1:원주가
    }
    resp = requests.get(f"{api_url}{end_point}", headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_kline_overseas(
    access_token: str,
    api_key: str,
    api_sec: str,
    excd: T_EXCD_OVERSEAS,
    symbol: str,
    timeframe: T_TIMEFRAME,
    end: str,
    adj_price: bool = True,
    mock: bool = True,
) -> dict:
    # https://apiportal.koreainvestment.com/apiservice/apiservice-oversea-stock-quotations#L_0e9fb2ba-bbac-4735-925a-a35e08c9a790
    api_url = get_api_url(mock=mock)
    end_point = "/uapi/overseas-price/v1/quotations/dailyprice"
    headers = {
        "content-type": "application/json",
        "authorization": access_token,
        "appKey": api_key,
        "appSecret": api_sec,
        "tr_id": "HHDFS76240000",
    }
    params = {
        "AUTH": "",  # 사용자권한정보
        "EXCD": excd.upper(),  # 거래소코드
        "SYMB": symbol,  # 종목코드
        "GUBN": (
            "0" if timeframe == "D" else "1" if timeframe == "W" else "2" if timeframe == "M" else ""
        ),  # 일/주/월구분(0 : 일, 1 : 주,2 : 월)
        "BYMD": end,  # 조회기준일자
        "MODP": "1" if adj_price else "0",  # 수정주가반영여부(0 : 미반영, 1 : 반영)
        "KEYB": None,  # NEXT KEY BUFF
    }
    resp = requests.get(f"{api_url}{end_point}", headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


class Kis:
    def __init__(self, api_key: str, api_sec: str, mock: bool = False) -> None:
        self.api_key = api_key
        self.api_sec = api_sec
        self.mock = mock

    @staticmethod
    def get_excd() -> tuple:
        return (
            ("kospi", "코스피"),
            ("kosdaq", "코스닥"),
            ("konex", "코넥스"),
            ("nas", "나스닥"),
            ("nys", "뉴욕"),
            ("ams", "아멕스"),
            ("shs", "상해"),
            ("shi", "상해지수"),
            ("szs", "심천"),
            ("szi", "심천지수"),
            ("tse", "도쿄"),
            ("hks", "홍콩"),
            ("hnx", "하노이"),
            ("hsx", "호치민"),
            ("baq", "나스닥(주간)"),
            ("bay", "뉴욕(주간)"),
            ("baa", "아멕스(주간)"),
        )

    @staticmethod
    def get_symbols(excd: T_EXCD_SYMBOL, force_fetch: bool = False) -> list[dict]:
        filename, unzipped, url = M_EXCD.get(excd, [])
        fullpath = KIS_DIR / unzipped
        if not fullpath.is_file() or force_fetch:
            fetch_symbols(market=excd)
            if not fullpath.is_file():
                raise FileNotFoundError(fullpath.as_posix())
        if excd == "kospi":
            # (소스) https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/kis_kospi_code_mst.py
            result = []
            with open(fullpath, encoding="cp949") as fp:
                for row in fp:
                    rf1 = row[0 : len(row) - 228]
                    rf1_1 = rf1[0:9].rstrip()
                    rf1_2 = rf1[9:21].rstrip()
                    rf1_3 = rf1[21:].strip()
                    result.append({"단축코드": rf1_1, "표준코드": rf1_2, "한글명": rf1_3})
            return result
        elif excd == "kosdaq":
            # (소스) https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/kis_kosdaq_code_mst.py
            result = []
            with open(fullpath, encoding="cp949") as fp:
                for row in fp:
                    rf1 = row[0 : len(row) - 222]
                    rf1_1 = rf1[0:9].rstrip()
                    rf1_2 = rf1[9:21].rstrip()
                    rf1_3 = rf1[21:].strip()
                    result.append({"단축코드": rf1_1, "표준코드": rf1_2, "한글명": rf1_3})
            return result
        elif excd == "konex":
            # (소스) https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/kis_konex_code_mst.py
            result = []
            with open(fullpath, encoding="cp949") as fp:
                for row in fp:
                    row = row.strip()
                    mksc_shrn_iscd = row[0:9].strip()
                    stnd_iscd = row[9:21].strip()
                    hts_kor_isnm = row[21:-184].strip()
                    result.append({"단축코드": mksc_shrn_iscd, "표준코드": stnd_iscd, "한글명": hts_kor_isnm})
            return result
        else:
            # (소스) https://github.com/koreainvestment/open-trading-api/blob/main/stocks_info/overseas_stock_code.py
            result = []
            with open(fullpath, encoding="cp949") as fp:
                for row in fp:
                    splitted = row.split("\t")
                    result.append(
                        {
                            "국가코드": splitted[0],
                            "거래소ID": splitted[1],
                            "거래소코드": splitted[2],
                            "거래소이름": splitted[3],
                            "심볼": splitted[4],
                            "실시간심볼": splitted[5],
                            "한글명": splitted[6],
                            "영문명": splitted[7],
                            "통화": splitted[9],
                            "소수점": splitted[10],
                        }
                    )
            return result

    @property
    def access_token(self) -> str:
        fullpath = KIS_DIR / "access_token.json"
        if not fullpath.is_file():
            fetch_access_token(api_key=self.api_key, api_sec=self.api_sec, mock=self.mock)

        with open(fullpath) as fp:
            parsed: dict = json.load(fp)
        date_string = parsed.get("access_token_token_expired")
        expires = dt.fromisoformat(date_string).timestamp() - 60 * 60
        if dt.now().timestamp() < expires:
            return f'{parsed.get("token_type", "")} {parsed.get("access_token", "")}'

        fetch_access_token(api_key=self.api_key, api_sec=self.api_sec, mock=self.mock)
        with open(fullpath) as fp:
            parsed: dict = json.load(fp)
        return f'{parsed.get("token_type", "")} {parsed.get("access_token", "")}'

    def get_kline(
        self,
        symbol: str,
        timeframe: T_TIMEFRAME,
        start: str = None,
        end: str = None,
        limit: int = 100,
        adj_price=True,
        sleep: float = 0.1,
    ) -> list[dict]:
        if start and end:
            start_dt = dt.strptime(start, "%Y%m%d")
            end_dt = dt.strptime(end, "%Y%m%d")
        else:
            limit = min(limit, 100)
            now_dt = dt.now()
            if timeframe == "D":
                start_dt = now_dt - relativedelta(days=limit - 1)
                end_dt = now_dt
            elif timeframe == "W":
                base_dt = now_dt - relativedelta(days=now_dt.weekday())
                start_dt = base_dt - relativedelta(weeks=limit - 1)
                end_dt = base_dt + relativedelta(days=6)
            elif timeframe == "M":
                base_dt = now_dt.replace(day=1)
                start_dt = base_dt - relativedelta(months=limit - 1)
                end_dt = base_dt + relativedelta(months=1, days=-1)
            elif timeframe == "Y":
                base_dt = now_dt.replace(month=1, day=1)
                start_dt = base_dt - relativedelta(years=limit - 1)
                end_dt = base_dt + relativedelta(years=1, days=-1)
            else:
                raise ValueError(f"invalid timeframe, got {timeframe=}")

        params = dict(
            access_token=self.access_token,
            api_key=self.api_key,
            api_sec=self.api_sec,
            symbol=symbol,
            timeframe=timeframe,
            start=start_dt.strftime("%Y%m%d"),
            end=end_dt.strftime("%Y%m%d"),
            adj_price=adj_price,
            mock=self.mock,
        )
        result = []
        while True:
            resp = fetch_kline(**params)
            rows = [
                dict(
                    date_string=row.get("stck_bsop_date", ""),
                    open=row.get("stck_oprc", ""),
                    high=row.get("stck_hgpr", ""),
                    low=row.get("stck_lwpr", ""),
                    close=row.get("stck_clpr", ""),
                    volume=row.get("acml_vol", ""),
                )
                for row in resp.get("output2", [])
                if row
            ]
            if not rows:
                break
            result += rows
            date_string = result[-1].get("date_string", "")
            if date_string > params.get("start", ""):
                end_dt = dt.strptime(date_string, "%Y%m%d") - relativedelta(days=1)
                params["end"] = end_dt.strftime("%Y%m%d")
            else:
                break
            time.sleep(sleep)
        return result

    def get_kline_overseas(
        self,
        excd: T_EXCD_OVERSEAS,
        symbol: str,
        timeframe: T_TIMEFRAME,
        start: str = None,
        end: str = None,
        limit: int = 100,
        adj_price=True,
        sleep: float = 1.0,
    ) -> list[dict]:
        if start and end:
            start_dt = dt.strptime(start, "%Y%m%d")
            end_dt = dt.strptime(end, "%Y%m%d")
            limit = None
        else:
            limit = min(limit, 100)
            now_dt = dt.now()
            if timeframe == "D":
                start_dt = now_dt - relativedelta(days=limit - 1)
                end_dt = now_dt
            elif timeframe == "W":
                base_dt = now_dt - relativedelta(days=now_dt.weekday())
                start_dt = base_dt - relativedelta(weeks=limit - 1)
                end_dt = base_dt + relativedelta(days=6)
            elif timeframe == "M":
                base_dt = now_dt.replace(day=1)
                start_dt = base_dt - relativedelta(months=limit - 1)
                end_dt = base_dt + relativedelta(months=1, days=-1)
            else:
                raise ValueError(f"invalid timeframe, got {timeframe=}")

        params = dict(
            access_token=self.access_token,
            api_key=self.api_key,
            api_sec=self.api_sec,
            excd=excd,
            symbol=symbol,
            timeframe=timeframe,
            end=end_dt.strftime("%Y%m%d"),
            adj_price=adj_price,
            mock=self.mock,
        )
        result = []
        while True:
            resp = fetch_kline_overseas(**params)
            rows = [
                dict(
                    date_string=row.get("xymd", ""),
                    open=row.get("open", ""),
                    high=row.get("high", ""),
                    low=row.get("low", ""),
                    close=row.get("clos", ""),
                    volume=row.get("tvol", ""),
                )
                for row in resp.get("output2", [])
                if row
            ]
            if not rows:
                break
            result += rows
            date_string = result[-1].get("date_string", "")
            if date_string > start_dt.strftime("%Y%m%d"):
                end_dt = dt.strptime(date_string, "%Y%m%d") - relativedelta(days=1)
                params["end"] = end_dt.strftime("%Y%m%d")
            else:
                break
            time.sleep(sleep)

        if start and end:
            return [row for row in result if row.get("date_string", "") >= start]
        return result[:limit]
