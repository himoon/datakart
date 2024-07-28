from __future__ import annotations

import logging
from typing import Literal

import requests

logger = logging.getLogger(__name__)
session: requests.Session = None


class Fss:
    """금융감독원 `금융상품 한눈에` Open API"""

    def __init__(self, api_key: str, api_url: str = None, delay: float = 0.0) -> None:
        self.api_key: str = api_key
        self.api_url: str = api_url if api_url else "http://finlife.fss.or.kr"
        self.delay: float = delay

    def deposit_search(
        self,
        fin_grp: Literal["은행", "여신전문금융", "저축은행", "보험", "금융투자"] = "은행",
        intr_rate_type: Literal["단리", "복리"] = "단리",
        save_trm: Literal["1", "3", "6", "12", "24", "36"] = "12",
        join_member: Literal["제한없음", "서민전용", "일부제한"] = None,
    ) -> list:
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas package is required")

        global session
        if session is None:
            session = requests.Session()

        fin_grp_code = {"은행": "020000", "여신전문금융": "030200", "저축은행": "030300", "보험": "050000", "금융투자": "060000"}.get(
            fin_grp
        )
        join_deny = {"제한없음": "1", "서민전용": "2", "일부제한": "3"}.get(join_member)

        page_no = 1
        concat = []
        while True:
            url = f"/finlifeapi/depositProductsSearch.json?auth={self.api_key}&topFinGrpNo={fin_grp_code}&pageNo={page_no}"
            resp = session.get(self.api_url + url)
            parsed = resp.json()
            result = parsed.get("result", {})

            base_list = result.get("baseList", [])
            option_list = result.get("optionList", [])
            if not base_list or not option_list:
                break

            df_base = pd.DataFrame(base_list)
            df_option = pd.DataFrame(option_list)
            df_merge = pd.merge(
                df_base.query(f"join_deny=='{join_deny}'") if join_deny else df_base,
                df_option.query(f"intr_rate_type_nm=='{intr_rate_type}' and save_trm=='{save_trm}'"),
                on=["dcls_month", "fin_co_no", "fin_prdt_cd"],
                how="inner",
            )
            df_drop = df_merge.drop(columns=["dcls_month", "fin_co_no", "fin_prdt_cd", "max_limit", "dcls_end_day"])
            concat.append(df_drop)

            max_page_no = result.get("max_page_no", 0)
            now_page_no = result.get("now_page_no", 0)
            if max_page_no <= now_page_no:
                break
            page_no += 1

        return pd.concat(concat).to_dict(orient="records") if concat else []
