from __future__ import annotations

import logging
import pprint
import time
from enum import Enum

import requests


class RespType(str, Enum):
    JSON = "json"
    XML = "xml"

    def __str__(self) -> str:
        return self.value


class RespLang(str, Enum):
    KR = "kr"
    EN = "en"

    def __str__(self) -> str:
        return self.value


class RespIntv(str, Enum):
    ANNUAL = "A"
    SEMMI_ANNUAL = "S"
    QUARTERLY = "Q"
    MONTHLY = "M"
    SEMMI_MONTHLY = "SM"
    DAILY = "D"

    def __str__(self) -> str:
        return self.value


class ServiceName(str, Enum):
    STAT_TABLE_LIST = "StatisticTableList"
    STAT_WORD = "StatisticWord"
    STAT_ITEM_LIST = "StatisticItemList"
    STAT_SEARCH = "StatisticSearch"
    KEY_STAT_LIST = "KeyStatisticList"
    STAT_META = "StatisticMeta"

    def __str__(self) -> str:
        return self.value


class Ecos:
    """ECOS Open API"""

    def __init__(self, api_key: str = None, api_url: str = None) -> None:
        self.api_key = api_key if api_key else "sample"
        self.api_url = api_url if api_url else "http://ecos.bok.or.kr/api/"

    def _api_call(self, args: dict) -> dict | bytes:
        pprint.pprint(args)
        req_url = f"{self.api_url}{'/'.join(args.values())}"
        resp = requests.get(req_url)
        return resp.json() if args.get("요청유형", "") == RespType.JSON else resp.content

    def stat_table_list(
        self,
        stat_code: str = "",
        start: int = 1,
        end: int = 10,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
    ) -> dict | bytes:
        args = {
            "서비스명": f"{ServiceName.STAT_TABLE_LIST}",
            "인증키": self.api_key,
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{start}",
            "요청종료건수": f"{end}",
            "통계표코드": stat_code,
        }
        return self._api_call(args)

    def stat_word(
        self,
        stat_word: str = "",
        start: int = 1,
        end: int = 10,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
    ) -> dict | bytes:
        args = {
            "서비스명": f"{ServiceName.STAT_WORD}",
            "인증키": self.api_key,
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{start}",
            "요청종료건수": f"{end}",
            "용어": stat_word,
        }
        return self._api_call(args)

    def stat_item_list(
        self,
        stat_code: str = "",
        start: int = 1,
        end: int = 10,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
    ) -> dict | bytes:
        args = {
            "서비스명": f"{ServiceName.STAT_ITEM_LIST}",
            "인증키": self.api_key,
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{start}",
            "요청종료건수": f"{end}",
            "통계표코드": stat_code,
        }
        return self._api_call(args)

    def stat_search(
        self,
        stat_code: str,
        intv: str = RespIntv.DAILY,
        search_start: str = "",
        search_end: str = "",
        item_code1: str = "?",
        item_code2: str = "?",
        item_code3: str = "?",
        item_code4: str = "?",
        cnt_start: int = 1,
        cnt_end: int = 10,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
    ) -> dict | bytes:
        args = {
            "서비스명": f"{ServiceName.STAT_SEARCH}",
            "인증키": f"{self.api_key}",
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{cnt_start}",
            "요청종료건수": f"{cnt_end}",
            "통계표코드": f"{stat_code}",
            "주기": f"{intv}",
            "검색시작일자": f"{search_start}",
            "검색종료일자": f"{search_end}",
            "통계항목코드1": f"{item_code1}",
            "통계항목코드2": f"{item_code2}",
            "통계항목코드3": f"{item_code3}",
            "통계항목코드4": f"{item_code4}",
        }
        return self._api_call(args)

    def key_stat_list(
        self,
        cnt_start: int = 1,
        cnt_end: int = 10,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
    ) -> dict | bytes:
        args = {
            "서비스명": f"{ServiceName.KEY_STAT_LIST}",
            "인증키": f"{self.api_key}",
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{cnt_start}",
            "요청종료건수": f"{cnt_end}",
        }
        return self._api_call(args)

    def stat_meta(
        self,
        item_name: str,
        cnt_start: int = 1,
        cnt_end: int = 10,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
    ) -> dict | bytes:
        args = {
            "서비스명": f"{ServiceName.STAT_META}",
            "인증키": f"{self.api_key}",
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{cnt_start}",
            "요청종료건수": f"{cnt_end}",
            "데이터명": f"{item_name}",
        }
        return self._api_call(args)
