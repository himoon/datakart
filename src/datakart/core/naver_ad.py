from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Dict, List

import requests


class NaverAd:
    """NAVER Search Ad API"""

    def __init__(self, api_key: str, api_sec: str, cust_id: str) -> None:
        self.api_key: str = api_key
        self.api_sec: str = api_sec
        self.cust_id: str = cust_id
        self.host_url = "https://api.searchad.naver.com"

    def signature(self, timestamp: int, method: str, url: str) -> bytes:
        message = f"{timestamp}.{method}.{url}"
        hash = hmac.new(self.api_sec.encode(), message.encode(), hashlib.sha256)
        return base64.b64encode(hash.digest())

    def get_header(self, method, url) -> Dict:
        timestamp = int(round(time.time() * 1000))
        return {
            "X-Timestamp": f"{timestamp}",
            "X-API-KEY": self.api_key,
            "X-Customer": self.cust_id,
            "X-Signature": self.signature(timestamp, method, url),
        }

    def keywords_tool(
        self,
        *,
        site_id: str = None,
        biztp_id: int = None,
        keywords: str = None,
        event: int = None,
        month: int = None,
        show_detail: bool = False,
    ) -> Dict[str, List]:
        # https://naver.github.io/searchad-apidoc/#/tags/RelKwdStat
        method = "GET"
        url = "/keywordstool"
        headers = self.get_header(method, url)
        params = {
            "showDetail": 1 if show_detail else 0,
            **({"siteId": site_id} if site_id else {}),
            **({"biztpId": biztp_id} if biztp_id else {}),
            **({"hintKeywords": keywords} if keywords else {}),
            **({"event": event} if event else {}),
            **({"month": month} if month else {}),
        }
        resp = requests.get(self.host_url + url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_biztp_codes() -> List[Dict]:
        import json
        import pathlib

        with open(pathlib.Path(__file__).parent / "assets" / "naver_ad_biztp.json") as fp:
            return json.load(fp)

    @staticmethod
    def get_event_codes() -> List[Dict]:
        # https://gist.github.com/naver-searchad/235202ffb08f9433b6f7cb10e45875f7#file-seasonal_event_code-md
        import json
        import pathlib

        with open(pathlib.Path(__file__).parent / "assets" / "naver_ad_event.json") as fp:
            return json.load(fp)
