from __future__ import annotations

import logging
import time
from calendar import monthrange
from datetime import datetime as dt
from enum import Enum
from typing import Literal

import requests
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)
session: requests.Session = None


class API_NAME(str, Enum):
    STAT_TABLE_LIST = "StatisticTableList"
    STAT_WORD = "StatisticWord"
    STAT_ITEM_LIST = "StatisticItemList"
    STAT_SEARCH = "StatisticSearch"
    KEY_STAT_LIST = "KeyStatisticList"
    STAT_META = "StatisticMeta"

    def __str__(self) -> str:
        return self.value


class FREQ(str, Enum):
    ANNUAL = "A"
    SEMMI_ANNUAL = "S"
    QUARTERLY = "Q"
    MONTHLY = "M"
    SEMMI_MONTHLY = "SM"
    DAILY = "D"

    def __str__(self) -> str:
        return self.value


def to_date_string(now: dt, freq: Literal["A", "S", "Q", "M", "SM", "D"]) -> str:
    if freq == FREQ.ANNUAL:
        return now.strftime("%Y")

    if freq == FREQ.SEMMI_ANNUAL:
        return now.strftime(f"%YS{(now.month - 1) // 6 + 1}")

    if freq == FREQ.QUARTERLY:
        return now.strftime(f"%YQ{(now.month - 1) // 3 + 1}")

    if freq == FREQ.MONTHLY:
        return now.strftime("%Y%m")

    if freq == FREQ.SEMMI_MONTHLY:
        _, days = monthrange(now.year, now.month)
        sm = "S1" if now.day <= int(days / 2) else "S2"
        return now.strftime(f"%Y%m{sm}")

    if freq == FREQ.DAILY:
        return now.strftime("%Y%m%d")

    raise ValueError(f"invalid interval, got {freq=}")


def to_datetime(date_string: str, intv: Literal["A", "S", "Q", "M", "SM", "D"]) -> dt:
    # TODO
    if intv == FREQ.ANNUAL:
        return dt.strptime(date_string, "%Y")

    if intv == FREQ.SEMMI_ANNUAL:
        year, cnt = [int(x) for x in date_string.split("S")]
        if cnt == 1:
            return dt(year=year, month=6, day=30)
        elif cnt == 2:
            return dt(year=year, month=12, day=31)
        raise ValueError(f"invalid date_string, got {date_string=}")

    if intv == FREQ.QUARTERLY:
        year, cnt = [int(x) for x in date_string.split("Q")]
        if cnt == 1:
            return dt(year=year, month=3, day=31)
        elif cnt == 2:
            return dt(year=year, month=6, day=30)
        elif cnt == 3:
            return dt(year=year, month=9, day=30)
        elif cnt == 4:
            return dt(year=year, month=12, day=31)
        raise ValueError(f"invalid date_string, got {date_string!r}")

    if intv == FREQ.MONTHLY:
        return dt.strptime(date_string, "%Y%m")

    if intv == FREQ.SEMMI_MONTHLY:
        yyyymm, cnt = date_string.split("S")
        cnt = int(cnt)
        now = dt.strptime(yyyymm, "%Y%m")
        _, days = monthrange(now.year, now.month)
        if cnt == 1:
            return now.replace(day=int(days / 2))
        elif cnt == 2:
            return now.replace(day=days)
        raise ValueError(f"invalid date_string, got {date_string!r}")

    if intv == FREQ.DAILY:
        return dt.strptime(date_string, "%Y%m%d")

    raise ValueError(f"invalid interval, got {intv!r}")


class ReqType(str, Enum):
    JSON = "json"
    XML = "xml"

    def __str__(self) -> str:
        return self.value


class RespLang(str, Enum):
    KR = "kr"
    EN = "en"

    def __str__(self) -> str:
        return self.value


class Ecos:
    """ECOS Open API"""

    def __init__(self, api_key: str = None, api_url: str = None, inc: int = 100_000, delay: float = 0.0) -> None:
        self.api_key: str = api_key if api_key else "sample"
        self.api_url: str = api_url if api_url else "https://ecos.bok.or.kr/api/"
        self.inc: int = inc
        self.delay: float = delay

    def raise_for_error(self, parsed: dict, args: dict) -> None:
        has_error = parsed.get("RESULT", {})
        if has_error:
            import json

            logger.error(f"args: {json.dumps(args, ensure_ascii=False)}")
            raise ValueError(f"({has_error.get('CODE')}) {has_error.get('MESSAGE')}")

    def _api_call(self, args: dict, limit: int = None) -> dict:
        global session
        if session is None:
            session = requests.Session()

        apiname = args["서비스명"]
        inc = 10 if self.api_key == "sample" else self.inc
        idx_start = 1
        idx_end = min(limit, inc) if limit else inc

        result = []
        while True:
            args["요청시작건수"] = f"{idx_start}"
            args["요청종료건수"] = f"{idx_end}"
            resp = session.get(f"{self.api_url}{'/'.join(args.values())}")
            parsed = resp.json()
            self.raise_for_error(parsed, args)

            parsed_name = parsed.get(apiname, {})
            total = parsed_name.get("list_total_count", 0)
            row = parsed_name.get("row", [])
            result += row
            length = len(result)

            if not row or self.api_key == "sample":
                break
            elif not limit:
                if length >= total:
                    break
            elif length >= limit:
                break
            idx_start += inc
            idx_end += inc
            if self.delay:
                time.sleep(self.delay)
        return result

    def stat_table_list(
        self,
        stat_code: str = "",
        limit: int = None,
        lang: Literal["kr", "en"] = "kr",
    ) -> list[dict]:
        """서비스 통계 목록"""
        apiname = API_NAME.STAT_TABLE_LIST
        args = {
            "서비스명": f"{apiname}",
            "인증키": f"{self.api_key}",
            "요청유형": "json",
            "언어구분": f"{lang}",
            "요청시작건수": "",
            "요청종료건수": "",
            "통계표코드": f"{stat_code}",
        }
        return self._api_call(args, limit)

    def stat_word(
        self,
        stat_word: str,
        limit: int = None,
        lang: Literal["kr", "en"] = "kr",
    ) -> list[dict]:
        """통계용어사전"""
        apiname = API_NAME.STAT_WORD
        args = {
            "서비스명": f"{apiname}",
            "인증키": f"{self.api_key}",
            "요청유형": "json",
            "언어구분": f"{lang}",
            "요청시작건수": "",
            "요청종료건수": "",
            "용어": f"{stat_word}",
        }
        return self._api_call(args, limit)

    def stat_item_list(
        self,
        stat_code: str,
        limit: int = None,
        lang: Literal["kr", "en"] = "kr",
    ) -> list[dict]:
        """통계 세부항목 목록"""
        apiname = API_NAME.STAT_ITEM_LIST
        args = {
            "서비스명": f"{apiname}",
            "인증키": f"{self.api_key}",
            "요청유형": "json",
            "언어구분": f"{lang}",
            "요청시작건수": "",
            "요청종료건수": "",
            "통계표코드": f"{stat_code}",
        }
        return self._api_call(args, limit)

    def stat_search(
        self,
        stat_code: str,
        freq: Literal["A", "S", "Q", "M", "SM", "D"],
        item_code1: str = "?",
        item_code2: str = "?",
        item_code3: str = "?",
        item_code4: str = "?",
        limit: int = None,
        start: str = "",
        end: str = "",
        lang: Literal["kr", "en"] = "kr",
    ) -> list[dict]:
        """통계 조회 조건 설정"""
        if limit:
            start, end = "", ""
            now = dt.now()
            if freq == FREQ.ANNUAL:
                end_dt = now - relativedelta(years=1)
                start_dt = end_dt - relativedelta(years=limit - 1)
            elif freq == FREQ.SEMMI_ANNUAL:
                end_dt = (dt(now.year, 1, 1) if now.month <= 6 else dt(now.year, 7, 1)) - relativedelta(months=6)
                start_dt = end_dt - relativedelta(months=(limit - 1) * 6)
            elif freq == FREQ.QUARTERLY:
                quarter = (now.month - 1) // 3 + 1
                end_dt = dt(now.year, (quarter - 1) * 3, 1)
                start_dt = end_dt - relativedelta(months=(limit - 1) * 3)
            elif freq == FREQ.MONTHLY:
                end_dt = dt(now.year, now.month - 1, 1)
                start_dt = end_dt - relativedelta(months=(limit - 1))
            elif freq == FREQ.SEMMI_MONTHLY:
                _, now_days = monthrange(now.year, now.month)
                q, r = divmod(limit - 1, 2)
                if now.day >= int(now_days / 2):
                    end_dt = dt(now.year, now.month, 1)
                    start_dt = end_dt - relativedelta(months=q)
                    if r:
                        start_dt -= relativedelta(days=1)
                else:
                    end_dt = dt(now.year, now.month, 1) - relativedelta(days=1)
                    start_dt = end_dt - relativedelta(months=q)
                    if r:
                        start_dt -= relativedelta(day=1)
            elif freq == FREQ.DAILY:
                end_dt = dt(now.year, now.month, now.day - 1)
                start_dt = end_dt - relativedelta(days=(limit - 1))
            else:
                raise ValueError(f"invalid freq, got {freq=}")
            start = to_date_string(start_dt, freq)
            end = to_date_string(end_dt, freq)
        elif not start or not end:
            raise ValueError(f"You should use the limit parameter, or both the start and end parameters, got {limit=}, {start=}, {end=}")

        apiname = API_NAME.STAT_SEARCH
        args = {
            "서비스명": f"{apiname}",
            "인증키": f"{self.api_key}",
            "요청유형": "json",
            "언어구분": f"{lang}",
            "요청시작건수": "",
            "요청종료건수": "",
            "통계표코드": f"{stat_code}",
            "주기": f"{freq}",
            "검색시작일자": f"{start}",
            "검색종료일자": f"{end}",
            "통계항목코드1": f"{item_code1}",
            "통계항목코드2": f"{item_code2}",
            "통계항목코드3": f"{item_code3}",
            "통계항목코드4": f"{item_code4}",
        }
        return self._api_call(args, limit)

    def key_stat_list(
        self,
        limit: int = None,
        lang: Literal["kr", "en"] = "kr",
    ) -> list[dict]:
        """100대 통계지표"""
        apiname = API_NAME.KEY_STAT_LIST
        args = {
            "서비스명": f"{apiname}",
            "인증키": f"{self.api_key}",
            "요청유형": "json",
            "언어구분": f"{lang}",
            "요청시작건수": "",
            "요청종료건수": "",
        }
        return self._api_call(args, limit)

    def stat_meta(
        self,
        item_name: str,
        limit: int = None,
        lang: Literal["kr", "en"] = "kr",
    ) -> list[dict]:
        """통계메타DB"""
        apiname = API_NAME.STAT_META
        args = {
            "서비스명": f"{apiname}",
            "인증키": f"{self.api_key}",
            "요청유형": "json",
            "언어구분": f"{lang}",
            "요청시작건수": "",
            "요청종료건수": "",
            "데이터명": f"{item_name}",
        }
        return self._api_call(args, limit)
