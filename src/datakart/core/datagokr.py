from __future__ import annotations

import json
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
            try:
                return resp.json()
            except json.JSONDecodeError:
                return xmltodict.parse(resp.content)

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
                if n_rows >= total_cnt:
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

    def apt_trade(self, lawd_code: str, deal_ym: str, n_rows: int = 9999) -> list[dict]:
        # https://www.data.go.kr/data/15126469/openapi.do
        def _api_call(lawd_code: str, deal_ym: str, n_rows: int, page: int) -> dict:
            url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
            params = {
                "serviceKey": f"{self.api_key}",
                "LAWD_CD": f"{lawd_code}",
                "DEAL_YMD": f"{deal_ym}",
                "numOfRows": f"{n_rows}",
                "pageNo": f"{page}",
            }
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            return xmltodict.parse(resp.content)

        page: int = 1
        total_cnt: int = None
        result: list[dict] = []
        while True:
            parsed = _api_call(lawd_code=lawd_code, deal_ym=deal_ym, n_rows=n_rows, page=page)
            response: dict = parsed.get("response", {})
            header: dict = response.get("header", {})
            result_code = header.get("resultCode", "")
            if result_code == "000":
                body: dict = response.get("body", {})
                items: dict = body.get("items", {})
                if items:
                    item: list = items.get("item", [])
                    result += item
                    total_cnt = int(body.get("totalCount", 0))
                    if len(result) >= total_cnt:
                        return result
                    page += 1
                else:
                    return result
            else:
                raise ValueError(f'[{result_code}] {header.get("resultMsg","")}')

    def apt_trade_detailed(self, lawd_code: str, deal_ym: str, n_rows: int = 1000) -> list[dict]:
        # https://www.data.go.kr/data/15126468/openapi.do
        def _api_call(lawd_code: str, deal_ym: str, n_rows: int, page: int) -> dict:
            url = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
            params = {
                "serviceKey": f"{self.api_key}",
                "LAWD_CD": f"{lawd_code}",
                "DEAL_YMD": f"{deal_ym}",
                "numOfRows": f"{n_rows}",
                "pageNo": f"{page}",
            }
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            return xmltodict.parse(resp.content)

        page: int = 1
        total_cnt: int = None
        result: list[dict] = []
        while True:
            parsed = _api_call(lawd_code=lawd_code, deal_ym=deal_ym, n_rows=n_rows, page=page)
            response: dict = parsed.get("response", {})
            header: dict = response.get("header", {})
            result_code = header.get("resultCode", "")
            if result_code == "000":
                body: dict = response.get("body", {})
                items: dict = body.get("items", {})
                if items:
                    item: list = items.get("item", [])
                    result += item
                    total_cnt = int(body.get("totalCount", 0))
                    if len(result) >= total_cnt:
                        return result
                    page += 1
                else:
                    return result
            else:
                raise ValueError(f'[{result_code}] {header.get("resultMsg","")}')
