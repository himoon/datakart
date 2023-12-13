from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


class Naver:
    """NAVER Service API"""

    def __init__(
        self,
        api_key: str,
        api_sec: str,
    ) -> None:
        self.api_key: str = api_key
        self.api_sec: str = api_sec

    def local(
        self,
        query: str,
        display: int = 1,
        start: int = 1,
        sort: str = "random",
    ) -> list[dict]:
        # https://developers.naver.com/docs/serviceapi/search/local/local.md#%EC%A7%80%EC%97%AD
        url = "https://openapi.naver.com/v1/search/local.json"
        params = {
            "query": query,
            "display": f"{display}",
            "start": f"{start}",
            "sort": f"{sort}",
        }
        headers = {
            "X-Naver-Client-Id": self.api_key,
            "X-Naver-Client-Secret": self.api_sec,
        }
        resp = requests.get(url, params=params, headers=headers)
        parsed = resp.json()
        return parsed.get("items", [])
