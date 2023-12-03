from __future__ import annotations

import logging
from enum import Enum

import requests
import xmltodict

logger = logging.getLogger(__name__)


class RespType(str, Enum):
    JSON = "json"
    XML = "xml"

    def __str__(self) -> str:
        return self.value


class Datagokr:
    def __init__(self, api_key: str = None) -> None:
        if not api_key:
            raise ValueError(f"invalid api_key, got {api_key!r}")
        self.api_key = api_key

    def lawd_code(self, region: str = None, n_rows: int = 1000) -> list[dict]:
        # https://www.data.go.kr/data/15077871/openapi.do
        def _api_call(region: str, n_rows: int, page: int) -> dict:
            url = "http://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList"
            params = {
                "serviceKey": f"{self.api_key}",
                "pageNo": f"{page}",
                "numOfRows": f"{n_rows}",
                "type": f"{RespType.JSON}",
                "locatadd_nm": region,
            }
            resp = requests.get(url, params=params)
            return resp.json()

        page: int = 1
        total_cnt: int = None
        total_page: int = None
        result: list[dict] = []
        while True:
            parsed = _api_call(region=region, n_rows=n_rows, page=page)
            if "StanReginCd" in parsed:
                first, second = parsed.get("StanReginCd", [])
                if not total_cnt:
                    head = first.get("head", [])
                    total_cnt = head[0].get("totalCount", 0)
                row = second.get("row", [])
                if total_cnt <= n_rows:
                    return row
                result += row

                if not total_page:
                    total_page, remainder = divmod(total_cnt, n_rows)
                    if remainder > 0:
                        total_page += 1
                if page >= total_page:
                    return result
                page += 1

            elif "RESULT" in parsed:
                err_code = parsed.get("RESULT", {})
                e_code = err_code.get("resultCode", "")
                e_msg = err_code.get("resultMsg", "")
                raise ValueError(f"[{e_code}] {e_msg}")

            else:
                raise ValueError(f"invalid response, got {parsed!r}")

    def apt_trans(self, lawd_code: str, deal_ym: str) -> list[dict]:
        # https://www.data.go.kr/data/15058747/openapi.do?recommendDataYn=Y
        url = "http://openapi.molit.go.kr:8081/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTrade"
        params = {"serviceKey": self.api_key, "LAWD_CD": lawd_code, "DEAL_YMD": deal_ym}
        resp = requests.get(url, params=params)
        parsed: dict = xmltodict.parse(resp.content)
        response: dict = parsed.get("response", {})
        header: dict = response.get("header", {})
        result_code = header.get("resultCode", "")
        if result_code == "00":
            body: dict = response.get("body", {})
            items = body.get("items", {})
            if items:
                item: list = body.get("items", {}).get("item", [])
                total_cnt = int(body.get("totalCount", 0))
                if len(item) != total_cnt:
                    logger.warning(f"invalid totalCount {total_cnt}, got {len(item)!r}")
                return item
            return []
        raise ValueError(f'[{result_code}] {header.get("resultMsg","")}')

    def apt_trans_detailed(
        self, lawd_code: str, deal_ym: str, n_rows: int = 1000
    ) -> list[dict]:
        # https://www.data.go.kr/data/15057511/openapi.do?recommendDataYn=Y

        def _api_call(lawd_code: str, deal_ym: str, n_rows: int, page: int) -> dict:
            url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev"
            params = {
                "serviceKey": f"{self.api_key}",
                "LAWD_CD": f"{lawd_code}",
                "DEAL_YMD": f"{deal_ym}",
                "pageNo": f"{page}",
                "numOfRows": f"{n_rows}",
            }
            resp = requests.get(url, params=params)
            parsed: dict = xmltodict.parse(resp.content)
            return parsed

        page: int = 1
        total_cnt: int = None
        total_page: int = None
        result: list[dict] = []
        while True:
            parsed = _api_call(
                lawd_code=lawd_code,
                deal_ym=deal_ym,
                n_rows=n_rows,
                page=page,
            )
            response: dict = parsed.get("response", {})
            header: dict = response.get("header", {})
            result_code = header.get("resultCode", "")
            if result_code == "00":
                body: dict = response.get("body", {})
                items = body.get("items", {})
                if items:
                    item: list = body.get("items", {}).get("item", [])
                    if not total_cnt:
                        total_cnt = int(body.get("totalCount", 0))
                    if total_cnt <= n_rows:
                        return item
                    result += item

                    if not total_page:
                        total_page, remainder = divmod(total_cnt, n_rows)
                        if remainder > 0:
                            total_page += 1
                    if page >= total_page:
                        return result
                    page += 1
                else:
                    return result
            else:
                raise ValueError(f'[{result_code}] {header.get("resultMsg","")}')
