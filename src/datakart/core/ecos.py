from __future__ import annotations

import logging
from calendar import monthrange
from datetime import datetime as dt
from enum import Enum

import requests

logger = logging.getLogger(__name__)


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


class ServName(str, Enum):
    STAT_TABLE_LIST = "StatisticTableList"
    STAT_WORD = "StatisticWord"
    STAT_ITEM_LIST = "StatisticItemList"
    STAT_SEARCH = "StatisticSearch"
    KEY_STAT_LIST = "KeyStatisticList"
    STAT_META = "StatisticMeta"

    def __str__(self) -> str:
        return self.value


def dt_to_str(now: dt, intv: str) -> str:
    if intv == RespIntv.ANNUAL:
        return now.strftime("%Y")

    if intv == RespIntv.SEMMI_ANNUAL:
        s = "S1" if now.month <= 6 else "S2"
        return now.strftime(f"%Y{s}")

    if intv == RespIntv.QUARTERLY:
        return now.strftime(f"%YQ{now.month//4 +1}")

    if intv == RespIntv.MONTHLY:
        return now.strftime("%Y%m")

    if intv == RespIntv.SEMMI_MONTHLY:
        _, days = monthrange(now.year, now.month)
        sm = "S1" if now.day <= int(days / 2) else "S2"
        return now.strftime(f"%Y%m{sm}")

    if intv == RespIntv.DAILY:
        return now.strftime("%Y%m%d")

    raise ValueError(f"invalid interval, got {intv!r}")


def str_to_dt(date_string: str, intv: str) -> dt:
    if intv == RespIntv.ANNUAL:
        return dt.strptime(date_string, "%Y")

    if intv == RespIntv.SEMMI_ANNUAL:
        year, cnt = [int(x) for x in date_string.split("S")]
        if cnt == 1:
            return dt(year=year, month=6, day=30)
        elif cnt == 2:
            return dt(year=year, month=12, day=31)
        raise ValueError(f"invalid date_string, got {date_string!r}")

    if intv == RespIntv.QUARTERLY:
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

    if intv == RespIntv.MONTHLY:
        return dt.strptime(date_string, "%Y%m")

    if intv == RespIntv.SEMMI_MONTHLY:
        yyyymm, cnt = date_string.split("S")
        cnt = int(cnt)
        now = dt.strptime(yyyymm, "%Y%m")
        _, days = monthrange(now.year, now.month)
        if cnt == 1:
            return now.replace(day=int(days / 2))
        elif cnt == 2:
            return now.replace(day=days)
        raise ValueError(f"invalid date_string, got {date_string!r}")

    if intv == RespIntv.DAILY:
        return dt.strptime(date_string, "%Y%m%d")

    raise ValueError(f"invalid interval, got {intv!r}")


class Ecos:
    """ECOS Open API"""

    def __init__(self, api_key: str = None, api_url: str = None) -> None:
        self.api_key = api_key if api_key else "sample"
        self.api_url = api_url if api_url else "http://ecos.bok.or.kr/api/"

    def _api_call(self, args: dict) -> dict | bytes:
        req_url = f"{self.api_url}{'/'.join(args.values())}"
        resp = requests.get(req_url)
        if args.get("요청유형", "") == RespType.JSON:
            parsed = resp.json()
            result = parsed.get("RESULT", {})
            if result:
                logger.error(args)
                raise ValueError(f"({result.get('CODE')}) {result.get('MESSAGE')}")
            return parsed
        return resp.content

    def stat_table_list(
        self,
        stat_code: str = "",
        row_from: int = 1,
        row_to: int = 100_000,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
        raw: bool = False,
    ) -> dict | bytes:
        """서비스 통계 목록 조회

        Args:
            stat_code (str, optional): 통계표코드. Defaults to "".
            row_from (int, optional): 요청시작건수. Defaults to 1.
            row_to (int, optional): 요청종료견수. Defaults to 100_000.
            resp_type (str, optional): 요청유형. Defaults to RespType.JSON.
            resp_lang (str, optional): 언어구분. Defaults to RespLang.KR.
            raw (bool, optional): Raw데이터여부. Defaults to False.

        Returns:
            dict | bytes: 딕셔너리(JSON 요청 시), 또는 바이트(XML 요청 시)
        """
        sname = ServName.STAT_TABLE_LIST
        args = {
            "서비스명": f"{sname}",
            "인증키": self.api_key,
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{row_from}",
            "요청종료건수": f"{row_to}",
            "통계표코드": f"{stat_code}",
        }
        result = self._api_call(args)
        return (
            result.get(f"{sname}", {}).get("row", [])
            if not raw and resp_type == RespType.JSON
            else result
        )

    def stat_word(
        self,
        stat_word: str,
        row_from: int = 1,
        row_to: int = 100_000,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
        raw: bool = False,
    ) -> dict | bytes:
        """통계용어사전

        Args:
            stat_word (str): 용어
            row_from (int, optional): 요청시작건수. Defaults to 1.
            row_to (int, optional): 요청종료견수. Defaults to 100_000.
            resp_type (str, optional): 요청유형. Defaults to RespType.JSON.
            resp_lang (str, optional): 언어구분. Defaults to RespLang.KR.
            raw (bool, optional): Raw데이터여부. Defaults to False.

        Returns:
            dict | bytes: 딕셔너리(JSON 요청 시), 또는 바이트(XML 요청 시)
        """
        sname = ServName.STAT_WORD
        args = {
            "서비스명": f"{sname}",
            "인증키": self.api_key,
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{row_from}",
            "요청종료건수": f"{row_to}",
            "용어": f"{stat_word}",
        }
        result = self._api_call(args)
        return (
            result.get(f"{sname}", {}).get("row", [])
            if not raw and resp_type == RespType.JSON
            else result
        )

    def stat_item_list(
        self,
        stat_code: str,
        row_from: int = 1,
        row_to: int = 100_000,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
        raw: bool = False,
    ) -> dict | bytes:
        """통계 세부항목 목록

        Args:
            stat_code (str, optional): 통계표코드. Defaults to "".
            row_from (int, optional): 요청시작건수. Defaults to 1.
            row_to (int, optional): 요청종료견수. Defaults to 100_000.
            resp_type (str, optional): 요청유형. Defaults to RespType.JSON.
            resp_lang (str, optional): 언어구분. Defaults to RespLang.KR.
            raw (bool, optional): Raw데이터여부. Defaults to False.

        Returns:
            dict | bytes: 딕셔너리(JSON 요청 시), 또는 바이트(XML 요청 시)
        """
        sname = ServName.STAT_ITEM_LIST
        args = {
            "서비스명": f"{sname}",
            "인증키": self.api_key,
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{row_from}",
            "요청종료건수": f"{row_to}",
            "통계표코드": stat_code,
        }
        result = self._api_call(args)
        return (
            result.get(f"{sname}", {}).get("row", [])
            if not raw and resp_type == RespType.JSON
            else result
        )

    def stat_search(
        self,
        stat_code: str,
        intv: str = RespIntv.DAILY,
        search_from: str = "",
        search_to: str = "",
        item_code1: str = "?",
        item_code2: str = "?",
        item_code3: str = "?",
        item_code4: str = "?",
        row_from: int = 1,
        row_to: int = 100_000,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
        raw: bool = False,
    ) -> list | dict | bytes:
        """통계 조회 조건 설정

        Args:
            stat_code (str): 통계표코드
            intv (str, optional): 주기. Defaults to RespIntv.DAILY.
            search_from (str, optional): 검색시작일자. Defaults to "".
            search_to (str, optional): 검색종료일자. Defaults to "".
            item_code1 (str, optional): 통계항목코드1. Defaults to "?".
            item_code2 (str, optional): 통계항목코드2. Defaults to "?".
            item_code3 (str, optional): 통계항목코드3. Defaults to "?".
            item_code4 (str, optional): 통계항목코드4. Defaults to "?".
            row_from (int, optional): 요청시작건수. Defaults to 1.
            row_to (int, optional): 요청종료견수. Defaults to 100_000.
            resp_type (str, optional): 요청유형. Defaults to RespType.JSON.
            resp_lang (str, optional): 언어구분. Defaults to RespLang.KR.
            raw (bool, optional): Raw데이터여부. Defaults to False.

        Returns:
            dict | bytes: 딕셔너리(JSON 요청 시), 또는 바이트(XML 요청 시)
        """

        if not search_to:
            search_to = dt_to_str(dt.now(), intv)
        if not search_from:
            search_from = dt_to_str(dt.fromtimestamp(0), intv)
        sname = ServName.STAT_SEARCH
        args = {
            "서비스명": f"{sname}",
            "인증키": f"{self.api_key}",
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{row_from}",
            "요청종료건수": f"{row_to}",
            "통계표코드": f"{stat_code}",
            "주기": f"{intv}",
            "검색시작일자": f"{search_from}",
            "검색종료일자": f"{search_to}",
            "통계항목코드1": f"{item_code1}",
            "통계항목코드2": f"{item_code2}",
            "통계항목코드3": f"{item_code3}",
            "통계항목코드4": f"{item_code4}",
        }
        result = self._api_call(args)
        return (
            result.get(f"{sname}", {}).get("row", [])
            if not raw and resp_type == RespType.JSON
            else result
        )

    def key_stat_list(
        self,
        row_from: int = 1,
        row_to: int = 100_000,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
        raw: bool = False,
    ) -> list | dict | bytes:
        """100대 통계지표

        Args:
            row_from (int, optional): 요청시작건수. Defaults to 1.
            row_to (int, optional): 요청종료견수. Defaults to 100_000.
            resp_type (str, optional): 요청유형. Defaults to RespType.JSON.
            resp_lang (str, optional): 언어구분. Defaults to RespLang.KR.
            raw (bool, optional): Raw데이터여부. Defaults to False.

        Returns:
            dict | bytes: 딕셔너리(JSON 요청 시), 또는 바이트(XML 요청 시)
        """
        sname = ServName.KEY_STAT_LIST
        args = {
            "서비스명": f"{ServName.KEY_STAT_LIST}",
            "인증키": f"{self.api_key}",
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{row_from}",
            "요청종료건수": f"{row_to}",
        }
        result = self._api_call(args)
        return (
            result.get(f"{sname}", {}).get("row", [])
            if not raw and resp_type == RespType.JSON
            else result
        )

    def stat_meta(
        self,
        item_name: str,
        row_from: int = 1,
        row_to: int = 100_000,
        resp_type: str = RespType.JSON,
        resp_lang: str = RespLang.KR,
        raw: bool = False,
    ) -> list | dict | bytes:
        """통계메타DB

        Args:
            item_name (str): 데이터명
            row_from (int, optional): 요청시작건수. Defaults to 1.
            row_to (int, optional): 요청종료견수. Defaults to 100_000.
            resp_type (str, optional): 요청유형. Defaults to RespType.JSON.
            resp_lang (str, optional): 언어구분. Defaults to RespLang.KR.
            raw (bool, optional): Raw데이터여부. Defaults to False.

        Returns:
            dict | bytes: 딕셔너리(JSON 요청 시), 또는 바이트(XML 요청 시)
        """
        sname = ServName.STAT_META
        args = {
            "서비스명": f"{sname}",
            "인증키": f"{self.api_key}",
            "요청유형": f"{resp_type}",
            "언어구분": f"{resp_lang}",
            "요청시작건수": f"{row_from}",
            "요청종료건수": f"{row_to}",
            "데이터명": f"{item_name}",
        }
        result = self._api_call(args)
        return (
            result.get(f"{sname}", {}).get("row", [])
            if not raw and resp_type == RespType.JSON
            else result
        )
