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
    SEMI_ANNUAL = "S"
    QUARTERLY = "Q"
    MONTHLY = "M"
    SEMI_MONTHLY = "SM"
    DAILY = "D"

    def __str__(self) -> str:
        return self.value


def to_date_string(now: dt, freq: Literal["A", "S", "Q", "M", "SM", "D"]) -> str:
    """
    주어진 날짜와 주기에 따라 날짜 문자열을 반환합니다.

    매개변수:
        now (dt): 날짜 객체.
        freq (Literal["A", "S", "Q", "M", "SM", "D"]): 날짜 객채의 주기.
            - "A": 연간 (예: "2023")
            - "S": 반기 (예: "2023S1" 또는 "2023S2")
            - "Q": 분기 (예: "2023Q1", "2023Q2", "2023Q3", "2023Q4")
            - "M": 월간 (예: "202301")
            - "SM": 반월간 (예: "202301S1" 또는 "202301S2")
            - "D": 일간 (예: "20230101")

    반환값:
        str: 주어진 주기에 맞는 날짜 문자열.

    예외:
        ValueError: 유효하지 않은 주기가 주어졌을 때 발생합니다.
    """
    if freq == FREQ.ANNUAL:
        return now.strftime("%Y")

    if freq == FREQ.SEMI_ANNUAL:
        return now.strftime(f"%YS{(now.month - 1) // 6 + 1}")

    if freq == FREQ.QUARTERLY:
        return now.strftime(f"%YQ{(now.month - 1) // 3 + 1}")

    if freq == FREQ.MONTHLY:
        return now.strftime("%Y%m")

    if freq == FREQ.SEMI_MONTHLY:
        _, days = monthrange(now.year, now.month)
        sm = "S1" if now.day <= days // 2 else "S2"
        return now.strftime(f"%Y%m{sm}")

    if freq == FREQ.DAILY:
        return now.strftime("%Y%m%d")

    raise ValueError(f"invalid interval, got {freq=}")


def to_datetime(date_string: str, freq: Literal["A", "S", "Q", "M", "SM", "D"]) -> dt:
    """
    주어진 날짜 문자열과 주기를 기반으로 datetime 객체를 반환합니다.

    매개변수:
        date_string (str): 날짜를 나타내는 문자열.
        freq (Literal["A", "S", "Q", "M", "SM", "D"]): 날짜 문자열의 주기.
            - "A": 연간 (예: "2023")
            - "S": 반기 (예: "2023S1" 또는 "2023S2")
            - "Q": 분기 (예: "2023Q1", "2023Q2", "2023Q3", "2023Q4")
            - "M": 월간 (예: "202301")
            - "SM": 반월간 (예: "202301S1" 또는 "202301S2")
            - "D": 일간 (예: "20230101")

    반환값:
        datetime: 주어진 날짜 문자열과 주기에 해당하는 datetime 객체.

    Raises:
        ValueError: 유효하지 않은 날짜 문자열 또는 주기가 주어진 경우.
    """
    if freq == FREQ.ANNUAL:
        return dt.strptime(date_string, "%Y")

    if freq == FREQ.SEMI_ANNUAL:
        year, half_year = [int(x) for x in date_string.split("S")]
        if half_year == 1:
            return dt(year=year, month=6, day=30)
        elif half_year == 2:
            return dt(year=year, month=12, day=31)
        raise ValueError(f"invalid date_string, got {date_string=}")

    if freq == FREQ.QUARTERLY:
        year, quarter = [int(x) for x in date_string.split("Q")]
        if quarter == 1:
            return dt(year=year, month=3, day=31)
        elif quarter == 2:
            return dt(year=year, month=6, day=30)
        elif quarter == 3:
            return dt(year=year, month=9, day=30)
        elif quarter == 4:
            return dt(year=year, month=12, day=31)
        raise ValueError(f"invalid date_string, got {date_string=}")

    if freq == FREQ.MONTHLY:
        return dt.strptime(date_string, "%Y%m")

    if freq == FREQ.SEMI_MONTHLY:
        yyyymm, semi_month = date_string.split("S")
        semi_month_period = int(semi_month)
        now = dt.strptime(yyyymm, "%Y%m")
        _, days = monthrange(now.year, now.month)
        if semi_month_period == 1:
            return now.replace(day=days // 2)
        elif semi_month_period == 2:
            return now.replace(day=days)
        raise ValueError(f"invalid date_string, got {date_string=}")

    if freq == FREQ.DAILY:
        return dt.strptime(date_string, "%Y%m%d")

    raise ValueError(f"invalid interval, got {freq=}")


class Ecos:
    """
    Ecos 클래스는 ECOS Open API와 상호작용하기 위한 기능을 제공합니다.
    """

    session = requests.Session()

    def __init__(self, api_key: str = None, api_url: str = None, inc: int = 100_000, delay: float = 0.0) -> None:
        """
        Ecos 클래스의 생성자 메서드입니다.

        매개변수:
            api_key (str, optional): API 키. 기본값은 "sample"입니다.
            api_url (str, optional): API URL. 기본값은 "https://ecos.bok.or.kr/api/"입니다.
            inc (int, optional): 증가 값. 기본값은 100,000입니다.
            delay (float, optional): 지연 시간(초). 기본값은 0.0초입니다.
        """
        self.api_key: str = api_key if api_key else "sample"
        self.api_url: str = api_url if api_url else "https://ecos.bok.or.kr/api/"
        self.inc: int = inc
        self.delay: float = delay

    def _api_call(self, args: dict, limit: int = None) -> dict:
        """
        주어진 인자를 사용하여 API 호출을 수행하고 결과를 반환합니다.

        매개변수:
            args (dict): API 호출에 필요한 인자. "서비스명", "요청시작건수", "요청종료건수" 등을 포함해야 합니다.
            limit (int, optional): 가져올 데이터의 최대 개수. 기본값은 None으로, 이 경우 가능한 모든 데이터를 가져옵니다.

        반환값:
            dict: API 호출 결과를 포함하는 딕셔너리.

        예외:
            Exception: API 호출 중 오류가 발생한 경우 예외를 발생시킵니다.
        """
        apiname = args["서비스명"]
        inc = 10 if self.api_key == "sample" else self.inc
        idx_start = 1
        idx_end = min(limit, inc) if limit else inc

        result = []
        while True:
            args["요청시작건수"] = f"{idx_start}"
            args["요청종료건수"] = f"{idx_end}"
            resp = Ecos.session.get(f"{self.api_url}{'/'.join(args.values())}")
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

    def raise_for_error(self, parsed: dict, args: dict) -> None:
        """
        주어진 파싱된 결과에서 오류가 있는지 확인하고, 오류가 있으면 로그를 기록하고 예외를 발생시킵니다.

        매개변수:
            parsed (dict): 파싱된 결과를 포함하는 딕셔너리입니다.
            args (dict): 요청에 사용된 인수를 포함하는 딕셔너리입니다.

        예외:
            ValueError: 파싱된 결과에 오류가 포함된 경우 예외를 발생시킵니다.
        """
        has_error = parsed.get("RESULT", {})
        if has_error:
            import json

            logger.error(f"args: {json.dumps(args, ensure_ascii=False)}")
            raise ValueError(f"({has_error.get('CODE')}) {has_error.get('MESSAGE')}")

    def stat_table_list(
        self,
        stat_code: str = "",
        limit: int = None,
        lang: Literal["kr", "en"] = "kr",
    ) -> list[dict]:
        """
        서비스 통계 목록을 반환합니다.

        매개변수:
            stat_code (str, optional): 통계표 코드. 기본값은 빈 문자열입니다.
            limit (int, optional): 가져올 데이터의 최대 개수. 기본값은 None입니다.
            lang (Literal["kr", "en"], optional): 응답 언어 구분. "kr"은 한국어, "en"은 영어를 의미합니다. 기본값은 "kr"입니다.

        반환값:
            list[dict]: 통계 목록을 포함하는 딕셔너리의 리스트.

        예제:
        ```python
            >>> ecos = Ecos("your_api_key")
            >>> ecos.stat_table_list()
            [{'P_STAT_CODE': '*', 'STAT_CODE': '0000000001', 'STAT_NAME': '1. 통화/금융', ...}, ...]
        ```
        """
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
        """
        통계용어사전에서 통계 용어 정의를 검색합니다.

        매개변수:
            stat_word (str): 검색할 통계 용어.
            limit (int, optional): 가져올 데이터의 최대 개수. 기본값은 None입니다.
            lang (Literal["kr", "en"], optional): 응답 언어 구분. "kr"은 한국어, "en"은 영어를 의미합니다. 기본값은 "kr"입니다.

        반환값:
            list[dict]: 통계 용어 정의를 포함하는 딕셔너리의 리스트.

        예제:
        ```python
            >>> ecos = Ecos("your_api_key")
            >>> ecos.stat_word("국내총생산", lang="kr")
            [{'WORD': '국내총생산(GDP)', 'CONTENT': '일정 기간 동안 한 나라 영토 안에서 생산된 재화와 서비스의 시장가치의 합계를 말한다. \nGDP(Gross domestic product)라고 함'},
             {'WORD': '국내총생산-시장가격', 'CONTENT': '시장가격에 의한 국내총생산은 모든 거주자 생산자의 생산자가격에 의한 총부가가치에 수입세(보조금 차감)와 모든 공제불능 부가가치세를 더한 것임'}]
        ```
        """
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
        """
        통계 세부항목 목록을 반환합니다.

        매개변수:
            stat_code (str): 통계표 코드.
            limit (int, optional): 가져올 데이터의 최대 개수. 기본값은 None입니다.
            lang (Literal["kr", "en"], optional): 응답 언어 구분. "kr"은 한국어, "en"은 영어를 의미합니다. 기본값은 "kr"입니다.

        반환값:
            list[dict]: 통계 세부항목을 포함하는 딕셔너리의 리스트.

        예제:
        ```python
            >>> ecos = Ecos("your_api_key")
            >>> resp = ecos.stat_item_list(stat_code="601Y002")
            >>> resp[0]
            {'STAT_CODE': '601Y002', 'STAT_NAME': '7.5.2. 지역별 소비유형별 개인 신용카드', 'GRP_CODE': ...}
        ```
        """
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
        """
        조회 조건에 따라 통계 조회 결과를 반환합니다.

        매개변수:
            stat_code (str): 검색할 통계의 코드.
            freq (Literal["A", "S", "Q", "M", "SM", "D"]): 날짜 문자열의 주기.
                - "A": 연간 (예: "2023")
                - "S": 반기 (예: "2023S1" 또는 "2023S2")
                - "Q": 분기 (예: "2023Q1", "2023Q2", "2023Q3", "2023Q4")
                - "M": 월간 (예: "202301")
                - "SM": 반월간 (예: "202301S1" 또는 "202301S2")
                - "D": 일간 (예: "20230101")
            item_code1 (str, optional): 통계의 첫 번째 항목 코드. 기본값은 "?"입니다.
            item_code2 (str, optional): 통계의 두 번째 항목 코드. 기본값은 "?"입니다.
            item_code3 (str, optional): 통계의 세 번째 항목 코드. 기본값은 "?"입니다.
            item_code4 (str, optional): 통계의 네 번째 항목 코드. 기본값은 "?"입니다.
            limit (int, optional): 가져올 데이터의 최대 개수. 기본값은 None입니다. 이 값이 제공된 경우 `start`와 `end`는 무시됩니다.
            start (str, optional): 검색 시작 날짜 (YYYYMMDD 형식). 기본값은 ""입니다.
            end (str, optional): 검색 종료 날짜 (YYYYMMDD 형식). 기본값은 ""입니다.
            lang (Literal["kr", "en"], optional): 응답 언어 구분. "kr"은 한국어, "en"은 영어를 의미합니다. 기본값은 "kr"입니다.

        반환값:
            list[dict]: 검색 결과를 포함하는 딕셔너리의 리스트.

        예외:
            ValueError: `limit` 또는 `start`와 `end`가 모두 제공되지 않거나, 유효하지 않은 주기가 주어진 경우 발생합니다.

        예제:
        ```python
            >>> ecos = Ecos("your_api_key")
            >>> ecos.stat_search(stat_code="200Y001", freq="A", item_code1="10101", start="2015", end="2021")
            [{'STAT_CODE': '200Y001', 'STAT_NAME': '2.7.1.1. 주요지표(연간지표)', ...}, ...]
        ```
        """
        if limit:
            start, end = "", ""
            now = dt.now()
            if freq == FREQ.ANNUAL:
                end_dt = now - relativedelta(years=1)
                start_dt = end_dt - relativedelta(years=limit - 1)
            elif freq == FREQ.SEMI_ANNUAL:
                end_dt = (dt(now.year, 1, 1) if now.month <= 6 else dt(now.year, 7, 1)) - relativedelta(months=6)
                start_dt = end_dt - relativedelta(months=(limit - 1) * 6)
            elif freq == FREQ.QUARTERLY:
                quarter = (now.month - 1) // 3 + 1
                end_dt = dt(now.year, (quarter - 1) * 3, 1)
                start_dt = end_dt - relativedelta(months=(limit - 1) * 3)
            elif freq == FREQ.MONTHLY:
                end_dt = dt(now.year, now.month - 1, 1)
                start_dt = end_dt - relativedelta(months=(limit - 1))
            elif freq == FREQ.SEMI_MONTHLY:
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
        """
        100대 통계지표를 반환합니다.

        매개변수:
            limit (int, optional): 가져올 최대 레코드 수. 기본값은 None입니다.
            lang (Literal["kr", "en"], optional): 응답 언어 구분. "kr"은 한국어, "en"은 영어를 의미합니다. 기본값은 "kr"입니다.
            "kr"은 한국어, "en"은 영어를 의미합니다. 기본값은 "kr"입니다.

        반환값:
            list[dict]: 주요 통계 지표를 포함하는 딕셔너리의 리스트.

        예제:
        ```python
            >>> ecos = Ecos("your_api_key")
            >>> ecos.key_stat_list()
            [{'CLASS_NAME': '시장금리', 'KEYSTAT_NAME': '한국은행 기준금리', ...}, ...]
        ```
        """
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
        """
        통계 데이터베이스에서 메타데이터를 검색합니다.

        매개변수:
            item_name (str): 메타데이터를 검색할 데이터 항목의 이름.
            limit (int, optional): 반환할 최대 레코드 수. 기본값은 None입니다.
            lang (Literal["kr", "en"], optional): 응답 언어 구분. "kr"은 한국어, "en"은 영어를 의미합니다. 기본값은 "kr"입니다.

        반환값:
            list[dict]: 지정된 데이터 항목에 대한 메타데이터를 포함하는 딕셔너리의 리스트.

        예제:
        ```python
            >>> ecos = Ecos("your_api_key")
            >>> ecos.stat_meta("경제심리지수")
            [{'LVL': '2', 'P_CONT_CODE': '0000000108', 'CONT_CODE': 'N13', ...}, ...]
        ```
        """
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
