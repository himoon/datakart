from __future__ import annotations

import json
import logging
import pathlib
import time
from typing import Literal

import requests

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """[-401] 인증정보가 존재하지 않습니다"""

    def __init__(self, *args):
        super().__init__(*args)


class Sgis:
    """통계지리정보서비스 SGIS"""

    def __init__(self, api_key: str, api_sec: str) -> None:
        self.api_key: str = api_key
        self.api_sec: str = api_sec

    @property
    def timeout(self) -> float:
        if hasattr(self, "_timeout"):
            return int(self._timeout) / 1000
        return 0.0

    @property
    def access_token(self) -> str:
        if not hasattr(self, "_token") or self.timeout - 60 * 60 < time.time():
            self.auth()
        return self._token

    def raise_for_err_cd(self, parsed: dict) -> None:
        err_cd, err_msg = parsed.get("errCd", 0), parsed.get("errMsg", "")
        if f"{err_cd}" == "-401":
            raise AuthenticationError(f"[{err_cd}] {err_msg}")
        if err_cd:
            raise ValueError(f"[{err_cd}] {err_msg}")

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

    @staticmethod
    def hadm_codes() -> list[dict]:
        # https://sgis.kostat.go.kr/view/board/faqView?post_no=11
        path_to_json = pathlib.Path(__file__).parent / "assets" / "adm_codes_2306.json"
        with open(path_to_json, "r", encoding="utf-8") as fp:
            return json.load(fp)

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
        for cnt in range(200):
            try:
                resp = session.get(url, params=params) if session else requests.get(url, params=params)
                parsed: dict = resp.json()
                self.raise_for_err_cd(parsed)
                result: dict = parsed.get("result", {})
                return result.get("resultdata", [])
            except AuthenticationError as err:
                logger.warning(f"{err}")
                time.sleep(10)
                self.auth()
            except ValueError as err:
                logger.warning(f"{err}")
                time.sleep(10)
        raise ValueError(f"invalid cnt, {cnt=}")

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
