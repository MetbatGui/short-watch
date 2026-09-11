import json
import os
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import typer

from future.application.collect_future_use_case import CollectFutureUseCase, CollectResult
from future.infrastructure.adapters.future_raw_parquet_repository import (
    FutureRawParquetRepository,
)
from future.infrastructure.adapters.krx_futures_client import KrxFuturesClient

app = typer.Typer()

DEFAULT_RAW_DATA_PATH = "data/future/raw"


def build_use_case() -> CollectFutureUseCase:
    """실제 의존성(KrxFuturesClient, FutureRawParquetRepository)으로 유스케이스를 조립한다.

    환경변수 KRX_USERNAME/KRX_PASSWORD로 로그인하고, FUTURE_RAW_DATA_PATH
    (미설정 시 "data/future/raw")에 원본 데이터를 저장한다.
    """
    source = KrxFuturesClient(
        username=os.environ["KRX_USERNAME"],
        password=os.environ["KRX_PASSWORD"],
    )
    repo = FutureRawParquetRepository(
        base_path=Path(os.environ.get("FUTURE_RAW_DATA_PATH", DEFAULT_RAW_DATA_PATH))
    )
    return CollectFutureUseCase(source=source, repo=repo)


def _parse_target_date(date_str: str | None) -> date:
    """CLI 인자를 대상 거래일로 변환한다.

    Args:
        date_str: ``YYYYMMDD`` 형식 문자열. None이면 KST 기준 오늘을 쓴다.

    Raises:
        ValueError: date_str이 ``YYYYMMDD`` 형식이 아니면 발생한다.
    """
    if date_str is None:
        return datetime.now(ZoneInfo("Asia/Seoul")).date()
    return datetime.strptime(date_str, "%Y%m%d").date()


@app.command()
def collect(date_str: str | None = typer.Option(None, "--date")) -> None:
    """선물 원본 데이터를 수집해 저장하고 결과를 JSON으로 출력한다.

    Args:
        date_str: 대상 거래일(``YYYYMMDD``). 생략하면 KST 기준 오늘.

    성공/실패와 무관하게 결과 JSON을 stdout에 출력하고, 종료코드는
    성공 0 / 실패 1만 쓴다(ddd.md "CLI Presentation 규약").
    """
    try:
        target_date = _parse_target_date(date_str)
    except ValueError:
        result = CollectResult(status="error", code="ERR_INVALID_DATE", records=0, message="--date 형식이 YYYYMMDD가 아님")
        typer.echo(json.dumps(asdict(result), ensure_ascii=False))
        raise typer.Exit(code=1)

    try:
        use_case = build_use_case()
        result = use_case.execute(target_date)
    except (KeyError, RuntimeError) as exc:
        result = CollectResult(status="error", code="ERR_LOGIN_FAILED", records=0, message=str(exc))
    except ConnectionError as exc:
        result = CollectResult(
            status="error", code="ERR_NETWORK_RETRY_EXHAUSTED", records=0, message=str(exc)
        )

    typer.echo(json.dumps(asdict(result), ensure_ascii=False))
    raise typer.Exit(code=0 if result.status == "ok" else 1)


if __name__ == "__main__":
    app()
