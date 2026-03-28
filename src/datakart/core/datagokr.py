from __future__ import annotations

import json
import logging
from enum import StrEnum
from typing import Any, cast

import requests
import xmltodict
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)


class RespType(StrEnum):
    JSON = "json"
    XML = "xml"

    def __str__(self) -> str:
        return self.value


class Datagokr:
    """Interface for public data portal (data.go.kr) APIs."""

    BASE_URL = "http://apis.data.go.kr"

    def __init__(self, api_key: str | None = None) -> None:
        if api_key is None:
            raise ValueError(f"invalid api_key, got {api_key!r}")
        self.api_key = api_key

    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Performs an API request and parses the response (JSON or XML)."""
        url = f"{self.BASE_URL}{endpoint}"
        params.update({"serviceKey": self.api_key})
        resp = requests.get(url, params=params)
        resp.raise_for_status()

        # If explicitly requesting JSON, try JSON first
        if params.get("type") in (RespType.JSON, "json"):
            try:
                return cast(dict[str, Any], resp.json())
            except (
                json.JSONDecodeError,
                requests.exceptions.JSONDecodeError,
                AttributeError,
            ):
                return cast(dict[str, Any], xmltodict.parse(resp.content))

        # Otherwise, try XML first (common for many data.go.kr APIs)
        try:
            return cast(dict[str, Any], xmltodict.parse(resp.content))
        except Exception:
            try:
                return cast(dict[str, Any], resp.json())
            except Exception:
                raise ValueError(
                    f"Failed to parse response: {resp.text[:100]}"
                ) from None

    @sleep_and_retry  # type: ignore
    @limits(calls=25, period=1)  # type: ignore
    def lawd_code(
        self, region: str | None = None, n_rows: int = 1000
    ) -> list[dict[str, Any]]:
        """Fetch region (lawd) codes.
        https://www.data.go.kr/data/15077871/openapi.do
        """
        endpoint = "/1741000/StanReginCd/getStanReginCdList"
        page = 1
        result: list[dict[str, Any]] = []

        while True:
            params = {
                "pageNo": page,
                "numOfRows": n_rows,
                "type": RespType.JSON,
                "locatadd_nm": region,
            }
            parsed = self._request(endpoint, params)

            if "StanReginCd" in parsed:
                data_parts = parsed["StanReginCd"]
                # Structure is typically [ {head: ...}, {row: ...} ]
                head = data_parts[0].get("head", [{}])[0]
                rows = data_parts[1].get("row", [])

                total_cnt = int(head.get("totalCount", 0))
                result.extend(rows if isinstance(rows, list) else [rows])

                if len(result) >= total_cnt or not rows:
                    return result
                page += 1

            elif "RESULT" in parsed:
                res = parsed["RESULT"]
                raise ValueError(f"[{res.get('resultCode')}] {res.get('resultMsg')}")
            else:
                raise ValueError(f"invalid response, got {parsed!r}")

    def _fetch_trade_data(
        self, endpoint: str, params: dict[str, Any], n_rows: int
    ) -> list[dict[str, Any]]:
        """Generic handler for apartment trade data pagination."""
        page = 1
        result: list[dict[str, Any]] = []

        while True:
            params.update({"pageNo": page, "numOfRows": n_rows})
            parsed = self._request(endpoint, params)

            response = parsed.get("response", {})
            header = response.get("header", {})
            result_code = header.get("resultCode")

            if result_code == "000":
                body = response.get("body", {})
                items_wrapper = body.get("items")
                if not items_wrapper:
                    return result

                items = items_wrapper.get("item", [])
                # Ensure items is always a list (xmltodict returns dict for single item)
                item_list = items if isinstance(items, list) else [items]
                result.extend(item_list)

                total_cnt = int(body.get("totalCount", 0))
                if len(result) >= total_cnt or not item_list:
                    return result
                page += 1
            else:
                raise ValueError(f"[{result_code}] {header.get('resultMsg')}")

    @sleep_and_retry  # type: ignore
    @limits(calls=25, period=1)  # type: ignore
    def apt_trade(
        self, lawd_code: str, deal_ym: str, n_rows: int = 9999
    ) -> list[dict[str, Any]]:
        """Fetch apartment trade data.
        https://www.data.go.kr/data/15126469/openapi.do
        """
        endpoint = "/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
        params = {"LAWD_CD": lawd_code, "DEAL_YMD": deal_ym}
        return self._fetch_trade_data(endpoint, params, n_rows)

    @sleep_and_retry  # type: ignore
    @limits(calls=25, period=1)  # type: ignore
    def apt_trade_detailed(
        self, lawd_code: str, deal_ym: str, n_rows: int = 1000
    ) -> list[dict[str, Any]]:
        """Fetch detailed apartment trade data.
        https://www.data.go.kr/data/15126468/openapi.do
        """
        endpoint = "/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
        params = {"LAWD_CD": lawd_code, "DEAL_YMD": deal_ym}
        return self._fetch_trade_data(endpoint, params, n_rows)
