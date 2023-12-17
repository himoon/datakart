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
        session: requests.Session = None,
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
        resp = (
            session.get(url, params=params)
            if session
            else requests.get(url, params=params)
        )
        parsed = resp.json()
        self.raise_for_err_cd(parsed)
        return parsed

    def geocode_wgs84(
        self,
        address: str,
        page: int = 0,
        limit: int = 5,
        session: requests.Session = None,
    ) -> list[dict]:
        """입력된 주소 위치 제공 API(좌표계:WGS84, EPSG:4326)

        Args:
            address (str): 검색주소
            page (int, optional): 페이지. Defaults to 0.
            limit (int, optional): 결과 수. Defaults to 5.
            session (requests.Session, optional): 세션. Defaults to None.

        Returns:
            list[dict]: 검색결과
        """
        # https://sgis.kostat.go.kr/developer/html/newOpenApi/api/dataApi/addressBoundary.html#geocodewgs84
        url = "https://sgisapi.kostat.go.kr/OpenAPI3/addr/geocodewgs84.json"
        params = dict(
            accessToken=self.access_token,
            address=f"{address}",
            pagenum=f"{page}",
            resultcount=f"{limit}",
        )
        resp = (
            session.get(url, params=params)
            if session
            else requests.get(url, params=params)
        )
        parsed: dict = resp.json()
        self.raise_for_err_cd(parsed)

        result: dict = parsed.get("result", {})
        return result.get("resultdata", [])

    def geocode_utmk(
        self,
        address: str,
        page: int = 0,
        limit: int = 5,
        session: requests.Session = None,
    ) -> list[dict]:
        """입력된 주소 위치 제공 API(좌표계:UTM-K, EPSG:5179)

        Args:
            address (str): 검색주소
            page (int, optional): 페이지. Defaults to 0.
            limit (int, optional): 결과 수. Defaults to 5.
            session (requests.Session, optional): 세션. Defaults to None.

        Returns:
            list[dict]: 검색결과
        """
        # https://sgis.kostat.go.kr/developer/html/newOpenApi/api/dataApi/addressBoundary.html#geocode
        url = "https://sgisapi.kostat.go.kr/OpenAPI3/addr/geocode.json"
        params = dict(
            accessToken=self.access_token,
            address=f"{address}",
            pagenum=f"{page}",
            resultcount=f"{limit}",
        )
        resp = (
            session.get(url, params=params)
            if session
            else requests.get(url, params=params)
        )
        parsed: dict = resp.json()
        self.raise_for_err_cd(parsed)

        result: dict = parsed.get("result", {})
        return result.get("resultdata", [])
