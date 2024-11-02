from __future__ import annotations

import logging
import time
from typing import Literal

import requests

logger = logging.getLogger(__name__)


class Sgis:
    """통계지리정보서비스 SGIS"""

    def __init__(self, api_key: str, api_sec: str) -> None:
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
        low_search: Literal["0", "1", "2"] = "1",
        year: str = "2023",
        session: requests.Session = None,
    ) -> str:
        """행정구역 코드 이용 행정구역 경계 정보 제공 API(좌표계: WGS84 "EPSG:4326")

        Args:
            adm_cd (str, optional): 행정구역코드. Defaults to None.
            low_search (str, optional): 하위 통계 정보 유무. Defaults to "1".
            year (str, optional): 기준연도("2000" ~ "2023"). Defaults to "2023".
            session (requests.Session, optional): 세션. Defaults to None.

        Returns:
            str: GeoJSON 형식의 결과

        """
        # https://sgis.kostat.go.kr/developer/html/newOpenApi/api/dataApi/addressBoundary.html#hadmarea
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("The geopandas package is required for fetching data. You can install it using `pip install -U geopandas`")

        url = "https://sgisapi.kostat.go.kr/OpenAPI3/boundary/hadmarea.geojson"
        params = dict(
            accessToken=self.access_token,
            adm_cd=adm_cd,
            low_search=low_search,
            year=year,
        )
        resp = session.get(url, params=params) if session else requests.get(url, params=params)
        parsed = resp.json()
        self.raise_for_err_cd(parsed)

        gdf_resp: gpd.GeoDataFrame = gpd.read_file(resp.content)
        gdf_resp.set_crs("EPSG:5179", allow_override=True, inplace=True)  # 좌표계: UTM-K "EPSG:5179"
        gdf_filter: gpd.GeoDataFrame = gdf_resp.filter(["adm_cd", "adm_nm", "addr_en", "geometry"])
        return gdf_filter.to_json(drop_id=True, to_wgs84=True, separators=(",", ":"), ensure_ascii=False)  # 좌표계: WGS84 "EPSG:4326"

    def geocode_wgs84(self, address: str, page: int = 0, limit: int = 5, session: requests.Session = None) -> list[dict]:
        """입력된 주소 위치 제공 API(좌표계: WGS84 "EPSG:4326")

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
        resp = session.get(url, params=params) if session else requests.get(url, params=params)
        parsed: dict = resp.json()
        self.raise_for_err_cd(parsed)

        result: dict = parsed.get("result", {})
        return result.get("resultdata", [])

    def geocode_utmk(self, address: str, page: int = 0, limit: int = 5, session: requests.Session = None) -> list[dict]:
        """입력된 주소 위치 제공 API(좌표계: UTM-K "EPSG:5179")

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
        resp = session.get(url, params=params) if session else requests.get(url, params=params)
        parsed: dict = resp.json()
        self.raise_for_err_cd(parsed)

        result: dict = parsed.get("result", {})
        return result.get("resultdata", [])
