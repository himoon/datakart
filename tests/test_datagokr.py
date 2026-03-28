from unittest.mock import MagicMock, patch

import pytest

from datakart.core.datagokr import Datagokr, RespType


class TestDatagokr:
    """Datagokr 클래스 테스트"""

    def test_init_with_valid_api_key(self):
        """유효한 API 키로 초기화"""
        api_key = "test_api_key"
        client = Datagokr(api_key=api_key)
        assert client.api_key == api_key

    def test_init_with_none_api_key(self):
        """API 키가 None인 경우 에러 발생"""
        with pytest.raises(ValueError, match="invalid api_key"):
            Datagokr(api_key=None)

    @patch("datakart.core.datagokr.requests.get")
    def test_lawd_code_success(self, mock_get):
        """지역코드 조회 성공"""
        # Mock 응답 데이터
        mock_response_data = {
            "StanReginCd": [
                {
                    "head": [{"totalCount": 2}],
                },
                {
                    "row": [
                        {
                            "ctp_cd": "11",
                            "ctp_nm": "서울특별시",
                            "sido_cd": "1100",
                            "sido_nm": "강남구",
                        },
                        {
                            "ctp_cd": "11",
                            "ctp_nm": "서울특별시",
                            "sido_cd": "1101",
                            "sido_nm": "강동구",
                        },
                    ]
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response

        client = Datagokr(api_key="test_key")
        result = client.lawd_code(region="서울", n_rows=1000)

        assert len(result) == 2
        assert result[0]["ctp_nm"] == "서울특별시"
        mock_get.assert_called_once()

    @patch("datakart.core.datagokr.requests.get")
    def test_lawd_code_with_pagination(self, mock_get):
        """지역코드 조회 - Pagination 처리"""
        # 첫 번째 페이지 응답
        first_page = {
            "StanReginCd": [
                {
                    "head": [{"totalCount": 2}],  # 총 2개
                },
                {
                    "row": [
                        {"ctp_cd": "11", "ctp_nm": "서울특별시"},
                    ]
                },
            ]
        }

        # 두 번째 페이지 응답
        second_page = {
            "StanReginCd": [
                {
                    "head": [{"totalCount": 2}],
                },
                {
                    "row": [
                        {"ctp_cd": "26", "ctp_nm": "부산광역시"},
                    ]
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.json.side_effect = [first_page, second_page]
        mock_get.return_value = mock_response

        client = Datagokr(api_key="test_key")
        result = client.lawd_code(region="test", n_rows=1)

        assert len(result) == 2
        assert result[0]["ctp_nm"] == "서울특별시"
        assert result[1]["ctp_nm"] == "부산광역시"
        assert mock_get.call_count == 2

    @patch("datakart.core.datagokr.requests.get")
    def test_lawd_code_api_error(self, mock_get):
        """지역코드 조회 - API 에러 응답"""
        error_response = {
            "RESULT": {
                "resultCode": "99",
                "resultMsg": "서비스 오류가 발생했습니다.",
            }
        }

        mock_response = MagicMock()
        mock_response.json.return_value = error_response
        mock_get.return_value = mock_response

        client = Datagokr(api_key="test_key")

        with pytest.raises(ValueError, match=r"\[99\]"):
            client.lawd_code(region="test")

    @patch("datakart.core.datagokr.requests.get")
    def test_apt_trade_success(self, mock_get):
        """아파트 거래 정보 조회 성공"""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <response>
            <header>
                <resultCode>000</resultCode>
                <resultMsg>SUCCESSFUL</resultMsg>
            </header>
            <body>
                <items>
                    <item>
                        <DEAL_ID>1</DEAL_ID>
                        <DEAL_AMOUNT>500000</DEAL_AMOUNT>
                        <DEAL_YMD>202301</DEAL_YMD>
                    </item>
                    <item>
                        <DEAL_ID>2</DEAL_ID>
                        <DEAL_AMOUNT>600000</DEAL_AMOUNT>
                        <DEAL_YMD>202301</DEAL_YMD>
                    </item>
                </items>
                <totalCount>2</totalCount>
            </body>
        </response>
        """

        mock_response = MagicMock()
        mock_response.content = xml_response.encode("utf-8")
        mock_get.return_value = mock_response

        client = Datagokr(api_key="test_key")
        result = client.apt_trade(lawd_code="11110", deal_ym="202301")

        assert len(result) == 2
        assert result[0]["DEAL_AMOUNT"] == "500000"
        mock_get.assert_called_once()

    @patch("datakart.core.datagokr.requests.get")
    def test_apt_trade_no_items(self, mock_get):
        """아파트 거래 정보 조회 - 데이터 없음"""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <response>
            <header>
                <resultCode>000</resultCode>
                <resultMsg>SUCCESSFUL</resultMsg>
            </header>
            <body>
                <items></items>
                <totalCount>0</totalCount>
            </body>
        </response>
        """

        mock_response = MagicMock()
        mock_response.content = xml_response.encode("utf-8")
        mock_get.return_value = mock_response

        client = Datagokr(api_key="test_key")
        result = client.apt_trade(lawd_code="11110", deal_ym="202301")

        assert len(result) == 0

    @patch("datakart.core.datagokr.requests.get")
    def test_apt_trade_error(self, mock_get):
        """아파트 거래 정보 조회 - 에러"""
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <response>
            <header>
                <resultCode>01</resultCode>
                <resultMsg>요청 파라미터 오류</resultMsg>
            </header>
        </response>
        """

        mock_response = MagicMock()
        mock_response.content = xml_response.encode("utf-8")
        mock_get.return_value = mock_response

        client = Datagokr(api_key="test_key")

        with pytest.raises(ValueError, match=r"\[01\]"):
            client.apt_trade(lawd_code="11110", deal_ym="202301")

    @patch("datakart.core.datagokr.requests.get")
    def test_apt_trade_detailed_success(self, mock_get):
        """아파트 거래 상세 정보 조회 성공"""
        # xmltodict는 단일 item일 경우 dict, 여러 item일 경우 list로 반환
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <response>
            <header>
                <resultCode>000</resultCode>
                <resultMsg>SUCCESSFUL</resultMsg>
            </header>
            <body>
                <items>
                    <item>
                        <DEAL_ID>1</DEAL_ID>
                        <BUILDING_NAME>서울아파트</BUILDING_NAME>
                        <DEAL_AMOUNT>500000</DEAL_AMOUNT>
                    </item>
                    <item>
                        <DEAL_ID>2</DEAL_ID>
                        <BUILDING_NAME>강남아파트</BUILDING_NAME>
                        <DEAL_AMOUNT>600000</DEAL_AMOUNT>
                    </item>
                </items>
                <totalCount>2</totalCount>
            </body>
        </response>
        """

        mock_response = MagicMock()
        mock_response.content = xml_response.encode("utf-8")
        mock_get.return_value = mock_response

        client = Datagokr(api_key="test_key")
        result = client.apt_trade_detailed(lawd_code="11110", deal_ym="202301")

        assert len(result) == 2
        assert result[0]["BUILDING_NAME"] == "서울아파트"
        assert result[1]["BUILDING_NAME"] == "강남아파트"


class TestRespType:
    """RespType Enum 테스트"""

    def test_resp_type_json(self):
        """JSON 응답 타입"""
        assert str(RespType.JSON) == "json"

    def test_resp_type_xml(self):
        """XML 응답 타입"""
        assert str(RespType.XML) == "xml"
