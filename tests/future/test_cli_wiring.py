from pathlib import Path

import pytest

from future.application.collect_future_use_case import CollectFutureUseCase
from future.infrastructure.adapters.future_raw_parquet_repository import (
    FutureRawParquetRepository,
)
from future.infrastructure.adapters.krx_futures_client import KrxFuturesClient
from future.presentation import cli


@pytest.mark.integration
def test_build_use_case_wires_real_client_and_repository(monkeypatch):
    """build_use_case가 실제 KrxFuturesClient/FutureRawParquetRepository를 조립한다.

    Given: KRX_USERNAME/KRX_PASSWORD/FUTURE_RAW_DATA_PATH 환경변수
    When: build_use_case() 호출
    Then: 반환된 유스케이스의 source/repo가 실제 구현체이고, 자격증명/경로가 그대로 전달됨
    """
    monkeypatch.setenv("KRX_USERNAME", "test-user")
    monkeypatch.setenv("KRX_PASSWORD", "test-pw")
    monkeypatch.setenv("FUTURE_RAW_DATA_PATH", "/tmp/futures-raw")

    use_case = cli.build_use_case()

    assert isinstance(use_case, CollectFutureUseCase)
    assert isinstance(use_case._source, KrxFuturesClient)
    assert use_case._source._username == "test-user"
    assert use_case._source._password == "test-pw"
    assert isinstance(use_case._repo, FutureRawParquetRepository)
    assert use_case._repo._base_path == Path("/tmp/futures-raw")


@pytest.mark.integration
def test_build_use_case_defaults_data_path_when_env_missing(monkeypatch):
    """FUTURE_RAW_DATA_PATH 미설정 시 기본 경로(data/future/raw)를 쓴다.

    Given: FUTURE_RAW_DATA_PATH 환경변수 없음
    When: build_use_case() 호출
    Then: repo의 base_path가 기본값 "data/future/raw"
    """
    monkeypatch.setenv("KRX_USERNAME", "test-user")
    monkeypatch.setenv("KRX_PASSWORD", "test-pw")
    monkeypatch.delenv("FUTURE_RAW_DATA_PATH", raising=False)

    use_case = cli.build_use_case()

    assert use_case._repo._base_path == Path("data/future/raw")
