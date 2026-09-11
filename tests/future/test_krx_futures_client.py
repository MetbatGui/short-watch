from datetime import date
from unittest.mock import MagicMock

import pytest
import requests

from future.infrastructure.adapters.krx_futures_client import KrxFuturesClient


def _login_success_response():
    resp = MagicMock()
    resp.json.return_value = {"_error_code": "CD001", "MBR_NO": "1000005836"}
    return resp


def _data_response(output: list[dict]):
    resp = MagicMock()
    resp.json.return_value = {"output": output}
    return resp


@pytest.mark.unit
def test_fetch_raw_returns_output_verbatim():
    """정상 응답의 output 배열을 가공 없이 그대로 반환한다.

    Given: 로그인 성공 + getJsonData 응답에 행 2개
    When: fetch_raw(target_date) 호출
    Then: 반환값이 원본 output 리스트와 정확히 동일(가공 없음)
    """
    session = MagicMock()
    rows = [{"ISU_NM": "코스피200 F 202612 (야간)", "TDD_CLSPRC": "1,073.00"}]
    session.post.side_effect = [_login_success_response(), _data_response(rows)]

    client = KrxFuturesClient(username="u", password="p", session=session)
    result = client.fetch_raw(date(2026, 9, 11))

    assert result == rows


@pytest.mark.unit
def test_fetch_raw_returns_empty_list_on_holiday():
    """휴장일 등 output이 비어있으면 빈 리스트를 그대로 반환한다(예외 아님).

    Given: 로그인 성공 + getJsonData 응답의 output이 빈 리스트
    When: fetch_raw(target_date) 호출
    Then: 반환값은 빈 리스트, 예외 발생 안 함
    """
    session = MagicMock()
    session.post.side_effect = [_login_success_response(), _data_response([])]

    client = KrxFuturesClient(username="u", password="p", session=session)
    result = client.fetch_raw(date(2026, 9, 11))

    assert result == []


@pytest.mark.unit
def test_fetch_raw_raises_immediately_on_login_failure():
    """로그인 실패 시 재시도 없이 즉시 예외를 발생시킨다.

    Given: 로그인 응답의 _error_code가 CD001/CD011이 아님
    When: fetch_raw(target_date) 호출
    Then: RuntimeError 발생, post는 로그인 시도 1회만 호출됨(재시도 없음)
    """
    session = MagicMock()
    failure_resp = MagicMock()
    failure_resp.json.return_value = {"_error_code": "CD999"}
    session.post.side_effect = [failure_resp]

    client = KrxFuturesClient(username="u", password="p", session=session)

    with pytest.raises(RuntimeError):
        client.fetch_raw(date(2026, 9, 11))

    assert session.post.call_count == 1


@pytest.mark.unit
def test_fetch_raw_retries_three_times_on_network_error_then_raises():
    """네트워크 오류 시 지수백오프로 3회 재시도 후 실패 처리한다.

    Given: 로그인 성공 + getJsonData 호출마다 ConnectionError 3회 연속 발생
    When: fetch_raw(target_date) 호출
    Then: ConnectionError 발생, getJsonData 호출이 정확히 3회 시도됨(sleep은 주입해 무력화)
    """
    session = MagicMock()
    session.post.side_effect = [
        _login_success_response(),
        requests.exceptions.ConnectionError("network down"),
        requests.exceptions.ConnectionError("network down"),
        requests.exceptions.ConnectionError("network down"),
    ]
    sleep_calls: list[float] = []

    client = KrxFuturesClient(
        username="u", password="p", session=session, sleep=sleep_calls.append
    )

    with pytest.raises(ConnectionError):
        client.fetch_raw(date(2026, 9, 11))

    assert session.post.call_count == 1 + 3  # 로그인 1 + getJsonData 3회 시도
    assert len(sleep_calls) == 2  # 3회 시도 중 마지막 실패 후엔 대기 안 함
