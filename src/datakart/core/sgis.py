from __future__ import annotations

import logging
import time

import requests

logger = logging.getLogger(__name__)


class Sgis:
    """통계지리정보서비스 SGIS"""

    def __init__(
        self,
        api_key: str,
        api_sec: str,
    ) -> None:
        self.api_key: str = api_key
        self.api_sec: str = api_sec

    @staticmethod
    def raise_for_err_cd(parsed: dict) -> None:
        err_cd = parsed.get("errCd", 0)
        if err_cd:
            raise ValueError(f"[{err_cd}] {parsed.get('errMsg', 0)}")

    @property
    def access_token(self) -> str:
        if not hasattr(self, "_token") or int(self._timeout) / 1000 - 10 < time.time():
            self.auth()
        return self._token

    def auth(self) -> dict:
        # https://sgis.kostat.go.kr/developer/html/newOpenApi/api/dataApi/basics.html#auth
        url = "https://sgisapi.kostat.go.kr/OpenAPI3/auth/authentication.json"
        params = dict(consumer_key=self.api_key, consumer_secret=self.api_sec)
        resp = requests.get(url, params=params)
        parsed = resp.json()
        self.raise_for_err_cd(parsed)

        result = parsed.get("result", {})
        self._timeout = result.get("accessTimeout", 0)
        self._token = result.get("accessToken", "")
        return result

    def hadm_area(
        self,
        adm_cd: str = None,
        low_search: str = "1",
        year: str = "2023",
    ) -> dict:
        # https://sgis.kostat.go.kr/developer/html/newOpenApi/api/dataApi/addressBoundary.html#hadmarea
        # UTM-K (EPSG 5179)
        url = "https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson"
        params = dict(
            accessToken=self.access_token,
            adm_cd=adm_cd,
            low_search=low_search,
            year=year,
        )
        resp = requests.get(url, params=params)
        parsed = resp.json()
        self.raise_for_err_cd(parsed)
        return parsed
