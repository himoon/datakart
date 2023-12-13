from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


class Jusogokr:
    """도로명 주소 API"""

    def __init__(
        self,
        api_key: str,
    ) -> None:
        self.api_key: str = api_key

    @staticmethod
    def raise_for_common(common: dict):
        code = common.get("errorCode", "0")
        if code != "0":
            raise ValueError(f'[{code}] {common.get("errorMessage", "")}')

    def addr(
        self,
        keyword: str,
        page: int = 1,
        limit: int = 10,
        history: str = "N",
        sort: str = "none",
        detail: str = "N",
    ) -> list[dict]:
        # https://business.juso.go.kr/addrlink/openApi/searchApi.do
        url = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
        params = dict(
            confmKey=self.api_key,
            keyword=f"{keyword}",
            currentPage=f"{page}",
            countPerPage=f"{limit}",
            resultType="json",
            hstryYn=history,
            firstSort=sort,
            addInfoYn=detail,
        )
        resp = requests.get(url, params=params)
        parsed = resp.json()
        results = parsed.get("results", {})
        self.raise_for_common(results.get("common", {}))
        juso = results.get("juso", {})
        return juso
