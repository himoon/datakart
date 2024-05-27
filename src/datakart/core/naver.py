from __future__ import annotations

import logging
from typing import Dict, List, Literal, Tuple

import requests

logger = logging.getLogger(__name__)


class Naver:
    """NAVER Service API"""

    def __init__(self, api_key: str, api_sec: str) -> None:
        self.api_key: str = api_key
        self.api_sec: str = api_sec

    @property
    def headers(self) -> Dict:
        return {"X-Naver-Client-Id": self.api_key, "X-Naver-Client-Secret": self.api_sec}

    def adult(self, query: str) -> Dict:
        """성인 검색어 판별 결과 조회"""
        # https://developers.naver.com/docs/serviceapi/search/adult/adult.md
        url = "https://openapi.naver.com/v1/search/adult.json"
        params = {"query": query}
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def blog(self, query: str, display: int = 10, start: int = 1, sort: Literal["sim", "date"] = "sim") -> Dict:
        """블로그 검색 결과 조회"""
        # https://developers.naver.com/docs/serviceapi/search/blog/blog.md
        url = "https://openapi.naver.com/v1/search/blog.json"
        params = {"query": query, "display": f"{display}", "start": f"{start}", "sort": f"{sort}"}
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def local(self, query: str, display: int = 5, start: int = 1, sort: Literal["random", "comment"] = "random") -> Dict:
        """지역 검색 결과 조회"""
        # https://developers.naver.com/docs/serviceapi/search/local/local.md
        url = "https://openapi.naver.com/v1/search/local.json"
        params = {"query": query, "display": f"{display}", "start": f"{start}", "sort": f"{sort}"}
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def shop(
        self,
        query: str,
        display: int = 10,
        start: int = 1,
        sort: Literal["sim", "date", "asc", "dsc"] = "sim",
        filter: Literal["naverpay"] = None,
        exclude: Literal["used", "rental", "cbshop"] = None,
    ) -> Dict:
        """쇼핑 검색 결과 조회"""
        # https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md
        url = "https://openapi.naver.com/v1/search/shop.json"
        params = {
            "query": query,
            "display": f"{display}",
            "start": f"{start}",
            "sort": f"{sort}",
            **(dict(filter=filter) if filter else {}),
            **(dict(exclude=exclude) if exclude else {}),
        }
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def lab_search(
        self,
        start_date: str,
        end_date: str,
        time_unit: Literal["date", "week", "month"],
        keyword_groups: List[Tuple[str, Tuple[str, ...]]],
        device: Literal["pc", "mo"] = None,
        gender: Literal["m", "f"] = None,
        ages: List[Literal["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]] = None,
    ) -> Dict:
        """네이버 통합 검색어 트렌드 조회"""
        # https://developers.naver.com/docs/serviceapi/datalab/search/search.md
        url = "https://openapi.naver.com/v1/datalab/search"
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": [{"groupName": name, "keywords": kw} for name, kw in keyword_groups],
            **(dict(device=device) if device else {}),
            **(dict(gender=gender) if gender else {}),
            **(dict(ages=ages) if ages else {}),
        }
        resp = requests.post(url, json=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def lab_shopping(
        self,
        start_date: str,
        end_date: str,
        time_unit: Literal["date", "week", "month"],
        category: List[Tuple[str, Tuple[str, ...]]],
        device: Literal["pc", "mo"] = None,
        gender: Literal["m", "f"] = None,
        ages: List[Literal["10", "20", "30", "40", "50", "60"]] = None,
    ) -> Dict:
        """쇼핑인사이트 분야별 트렌드 조회"""
        # https://developers.naver.com/docs/serviceapi/datalab/shopping/shopping.md
        url = "https://openapi.naver.com/v1/datalab/shopping/categories"
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "category": [{"name": name, "param": kw} for name, kw in category],
            **(dict(device=device) if device else {}),
            **(dict(gender=gender) if gender else {}),
            **(dict(ages=ages) if ages else {}),
        }
        resp = requests.post(url, json=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()
