import time
from datetime import date
from typing import Callable

import requests

BASE_URL = "https://data.krx.co.kr"
BLD = "dbms/MDC/STAT/standard/MDCSTAT12501"
PROD_ID = "KR___FUK2I"


class KrxFuturesClient:
    """KRX Data Marketplace에서 선물 원본 데이터를 가져오는 어댑터.

    응답을 가공하지 않고 그대로 반환한다(Bronze 원칙,
    collector-bronze-no-transformation ADR).
    """

    def __init__(
        self,
        username: str,
        password: str,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_retries: int = 3,
    ):
        self._username = username
        self._password = password
        self._session = session or requests.Session()
        self._sleep = sleep
        self._max_retries = max_retries

    def fetch_raw(self, target_date: date) -> list[dict]:
        """지정 거래일의 KRX 원본 응답 행 전체를 반환한다.

        Args:
            target_date: 조회 대상 거래일(KST 기준).

        Returns:
            KRX 응답의 output 배열. 가공하지 않은 원본 dict 리스트.
            휴장일 등 데이터가 없으면 빈 리스트를 반환한다(예외 아님).

        Raises:
            RuntimeError: 로그인 실패 시 즉시 발생한다(재시도 안 함).
            ConnectionError: 네트워크 오류가 재시도 후에도 계속되면 발생한다.
        """
        self._login()
        return self._fetch(target_date)

    def _login(self) -> None:
        login_page = f"{BASE_URL}/contents/MDC/COMS/client/MDCCOMS001.cmd"
        login_jsp = f"{BASE_URL}/contents/MDC/COMS/client/view/login.jsp?site=mdc"
        login_url = f"{BASE_URL}/contents/MDC/COMS/client/MDCCOMS001D1.cmd"

        self._session.get(login_page, timeout=15)
        self._session.get(login_jsp, headers={"Referer": login_page}, timeout=15)

        payload = {
            "mbrNm": "",
            "telNo": "",
            "di": "",
            "certType": "",
            "mbrId": self._username,
            "pw": self._password,
        }
        resp = self._session.post(login_url, data=payload, headers={"Referer": login_page}, timeout=15)
        data = resp.json()
        error_code = data.get("_error_code", "")

        if error_code == "CD011":
            payload["skipDup"] = "Y"
            resp = self._session.post(login_url, data=payload, headers={"Referer": login_page}, timeout=15)
            data = resp.json()
            error_code = data.get("_error_code", "")

        if error_code != "CD001":
            raise RuntimeError(f"KRX 로그인 실패: {error_code}")

        self._session.cookies.set("mdc.client_session", "true", domain="data.krx.co.kr")
        self._session.cookies.set("lang", "ko_KR", domain="data.krx.co.kr")

    def _fetch(self, target_date: date) -> list[dict]:
        trd_dd = target_date.strftime("%Y%m%d")
        url = f"{BASE_URL}/comm/bldAttendant/getJsonData.cmd"
        params = {
            "bld": BLD,
            "locale": "ko_KR",
            "trdDd": trd_dd,
            "prodId": PROD_ID,
            "trdDdBox1": trd_dd,
            "aggBasTpCd": "",
            "rghtTpCd": "T",
            "share": "1",
            "money": "3",
            "csvxls_isNo": "false",
        }
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": BASE_URL,
            "Referer": f"{BASE_URL}/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201",
            "X-Requested-With": "XMLHttpRequest",
        }

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self._session.post(url, data=params, headers=headers, timeout=15)
                return resp.json().get("output", [])
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt < self._max_retries - 1:
                    self._sleep(2**attempt)

        raise ConnectionError(f"KRX 선물 데이터 조회 실패: {last_error}") from last_error
