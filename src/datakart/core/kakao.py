from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)


class Kakao:
    """Kakao API"""

    def __init__(self, api_key: str) -> None:
        self.api_key: str = api_key

    def local_keyword(
        self,
        query: str,
        format: str = "JSON",
        category_group_code: str = None,
        x: str = None,
        y: str = None,
        radius: int = None,
        rect: str = None,
        page: int = None,
        limit: int = None,
        sort: str = None,
    ) -> list[dict]:
        # https://developers.kakao.com/docs/latest/ko/local/dev-guide#search-by-keyword
        url = f"https://dapi.kakao.com/v2/local/search/keyword.{format}"
        params = dict(
            query=query,
            category_group_code=category_group_code,
            x=x,
            y=y,
            radius=radius,
            rect=rect,
            page=page,
            size=limit,
            sort=sort,
        )
        headers = dict(Authorization=f"KakaoAK {self.api_key}")
        resp = requests.get(url, params=params, headers=headers)
        parsed = resp.json()
        return parsed.get("documents", [])
