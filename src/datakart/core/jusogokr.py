from __future__ import annotations

import logging
from typing import Literal

import requests

logger = logging.getLogger(__name__)


class Jusogokr:
    """도로명 주소 API"""

    def __init__(self, api_key: str) -> None:
        self.api_key: str = api_key

    @staticmethod
    def raise_for_status(status: dict):
        code = status.get("errorCode", "0")
        if code != "0":
            raise ValueError(f'[{code}] {status.get("errorMessage", "")}')

    def addr(
        self,
        keyword: str,  # 주소 검색어
        currentPage: int = 1,  # 요청 페이지 번호
        countPerPage: int = 10,  # 페이지당 출력 할 결과 Row 수
        firstSort: Literal["none", "road", "location"] = "none",  # 정확도 정렬 (none), 우선정렬(road: 도로명 포함, location: 지번 포함)
        hstryYn: Literal["Y", "N"] = "N",  # 변동된 주소정보 포함 여부
        addInfoYn: Literal["Y", "N"] = "N",  # 출력결과에 추가된 항목(hstryYn, relJibun, hemdNm) 제공여부
    ) -> dict:
        """검색API: 도로명주소"""
        if keyword := keyword.strip():
            # https://business.juso.go.kr/addrlink/openApi/searchApi.do
            url = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
            params = dict(
                confmKey=self.api_key,
                keyword=keyword,
                currentPage=f"{currentPage}",
                countPerPage=f"{countPerPage}",
                firstSort=firstSort,
                hstryYn=hstryYn,
                addInfoYn=addInfoYn,
                resultType="json",
            )
            resp = requests.get(url, params=params)
            parsed = resp.json()
            results = parsed.get("results", {})
            self.raise_for_status(results.get("common", {}))
            return results
        return {}

    def addr_coord(
        self,
        admCd: str,  # 행정구역코드
        rnMgtSn: str,  # 도로명코드
        udrtYn: Literal["0", "1"],  # 지하여부(0:지상, 1:지하)
        buldMnnm: str,  # 건물본번
        buldSlno: str,  # 건물부번
        **kwargs,
    ) -> dict:
        """검색API: 좌표제공"""
        # https://business.juso.go.kr/addrlink/openApi/searchApi.do
        url = "https://business.juso.go.kr/addrlink/addrCoordApi.do"
        params = dict(
            confmKey=self.api_key,
            admCd=admCd,
            rnMgtSn=rnMgtSn,
            udrtYn=udrtYn,
            buldMnnm=buldMnnm,
            buldSlno=buldSlno,
            resultType="json",
        )
        resp = requests.get(url, params=params)
        parsed = resp.json()
        results = parsed.get("results", {})
        self.raise_for_status(results.get("common", {}))
        return results
