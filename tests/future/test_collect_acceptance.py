import json
from datetime import date

import pytest
from typer.testing import CliRunner

from future.application.collect_future_use_case import CollectFutureUseCase
from future.presentation import cli

# 스파이크로 확보한 실제 KRX 응답 일부 (spikes/krx-futures/findings.md 기반)
FIXTURE_ROWS = [
    {
        "ISU_CD": "KR4A016C0004",
        "ISU_SRT_CD": "A016C000",
        "ISU_NM": "코스피200 F 202612 (야간)",
        "TDD_CLSPRC": "1,073.00",
        "CMPPREVDD_PRC": "-39.00",
        "ACC_TRDVOL": "24,309",
        "ACC_OPNINT_QTY": "128,759",
        "SETL_PRC": "0.00",
    },
    {
        "ISU_CD": "KR4A016C0004",
        "ISU_SRT_CD": "A016C000",
        "ISU_NM": "코스피200 F 202612 (주간)",
        "TDD_CLSPRC": "1,088.30",
        "CMPPREVDD_PRC": "-23.70",
        "ACC_TRDVOL": "104,371",
        "ACC_OPNINT_QTY": "127,733",
        "SETL_PRC": "0.00",
    },
]


class FakeFuturesSource:
    def fetch_raw(self, target_date: date) -> list[dict]:
        return FIXTURE_ROWS


class FakeFutureRawRepository:
    def __init__(self):
        self.saved: tuple[date, list[dict]] | None = None

    def save_raw(self, target_date: date, rows: list[dict]) -> None:
        self.saved = (target_date, rows)


@pytest.mark.acceptance
def test_collect_saves_all_raw_rows_and_reports_ok(monkeypatch):
    """CLI collect 실행 시 원본 행 전부를 가공 없이 저장하고 성공을 보고한다.

    Given: Fake KRX 응답(스파이크 fixture, 2행)
    When: CLI `collect --date 20260911` 실행
    Then: exit 0, JSON code=OK_COLLECTED, records=2, 저장된 데이터가 원본과 동일
    """
    fake_repo = FakeFutureRawRepository()
    monkeypatch.setattr(
        cli, "build_use_case", lambda: CollectFutureUseCase(FakeFuturesSource(), fake_repo)
    )

    runner = CliRunner()
    result = runner.invoke(cli.app, ["--date", "20260911"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["code"] == "OK_COLLECTED"
    assert payload["records"] == 2
    assert fake_repo.saved == (date(2026, 9, 11), FIXTURE_ROWS)


@pytest.mark.acceptance
def test_collect_reports_no_data_when_source_returns_empty(monkeypatch):
    """휴장일 등 원본 응답이 비어있으면 실패가 아니라 정상 종료로 처리한다.

    Given: Fake KRX 응답이 빈 리스트
    When: CLI `collect --date 20260911` 실행
    Then: exit 0, JSON code=OK_NO_DATA, records=0, 저장 호출 없음
    """

    class EmptyFakeSource:
        def fetch_raw(self, target_date: date) -> list[dict]:
            return []

    fake_repo = FakeFutureRawRepository()
    monkeypatch.setattr(
        cli, "build_use_case", lambda: CollectFutureUseCase(EmptyFakeSource(), fake_repo)
    )

    runner = CliRunner()
    result = runner.invoke(cli.app, ["--date", "20260911"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["code"] == "OK_NO_DATA"
    assert payload["records"] == 0
    assert fake_repo.saved is None


@pytest.mark.acceptance
def test_collect_reports_error_when_date_format_invalid():
    """--date 형식이 잘못되면 트레이스백 대신 구조화된 에러를 출력한다.

    Given: 존재하지 않는 --date 값
    When: CLI `collect --date not-a-date` 실행
    Then: exit 1, JSON code=ERR_INVALID_DATE
    """
    runner = CliRunner()
    result = runner.invoke(cli.app, ["--date", "not-a-date"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "ERR_INVALID_DATE"


@pytest.mark.acceptance
def test_collect_reports_login_failed_when_credentials_missing(monkeypatch):
    """KRX 자격증명 환경변수가 없으면 트레이스백 대신 로그인 실패로 처리한다.

    Given: build_use_case()가 KeyError(환경변수 누락)를 던짐
    When: CLI `collect --date 20260911` 실행
    Then: exit 1, JSON code=ERR_LOGIN_FAILED
    """

    def raise_missing_env():
        raise KeyError("KRX_USERNAME")

    monkeypatch.setattr(cli, "build_use_case", raise_missing_env)

    runner = CliRunner()
    result = runner.invoke(cli.app, ["--date", "20260911"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "ERR_LOGIN_FAILED"


@pytest.mark.acceptance
def test_collect_reports_login_failed_when_source_raises_runtime_error(monkeypatch):
    """소스가 로그인 실패(RuntimeError)를 던지면 트레이스백 대신 구조화된 에러를 출력한다.

    Given: Fake 소스가 fetch_raw에서 RuntimeError(로그인 실패)를 던짐
    When: CLI `collect --date 20260911` 실행
    Then: exit 1, JSON code=ERR_LOGIN_FAILED
    """

    class LoginFailingSource:
        def fetch_raw(self, target_date: date) -> list[dict]:
            raise RuntimeError("KRX 로그인 실패: CD999")

    fake_repo = FakeFutureRawRepository()
    monkeypatch.setattr(
        cli, "build_use_case", lambda: CollectFutureUseCase(LoginFailingSource(), fake_repo)
    )

    runner = CliRunner()
    result = runner.invoke(cli.app, ["--date", "20260911"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "ERR_LOGIN_FAILED"


@pytest.mark.acceptance
def test_collect_reports_network_retry_exhausted_when_source_raises_connection_error(monkeypatch):
    """소스가 재시도 소진(ConnectionError)을 던지면 트레이스백 대신 구조화된 에러를 출력한다.

    Given: Fake 소스가 fetch_raw에서 ConnectionError(재시도 소진)를 던짐
    When: CLI `collect --date 20260911` 실행
    Then: exit 1, JSON code=ERR_NETWORK_RETRY_EXHAUSTED
    """

    class NetworkFailingSource:
        def fetch_raw(self, target_date: date) -> list[dict]:
            raise ConnectionError("KRX 요청 실패: network down")

    fake_repo = FakeFutureRawRepository()
    monkeypatch.setattr(
        cli, "build_use_case", lambda: CollectFutureUseCase(NetworkFailingSource(), fake_repo)
    )

    runner = CliRunner()
    result = runner.invoke(cli.app, ["--date", "20260911"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["code"] == "ERR_NETWORK_RETRY_EXHAUSTED"
