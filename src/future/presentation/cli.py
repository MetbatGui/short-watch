import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import typer

from future.application.collect_future_use_case import CollectFutureUseCase

app = typer.Typer()


def build_use_case() -> CollectFutureUseCase:
    """실제 의존성(KrxFuturesClient, FutureRawParquetRepository)으로 유스케이스를 조립한다.

    Raises:
        NotImplementedError: Wire-up(Task #10) 전까지는 항상 발생한다.
    """
    raise NotImplementedError("Wire-up 전 - Task #10에서 실제 구현으로 교체")


def _parse_target_date(date_str: str | None) -> date:
    """CLI 인자를 대상 거래일로 변환한다.

    Args:
        date_str: ``YYYYMMDD`` 형식 문자열. None이면 KST 기준 오늘을 쓴다.
    """
    if date_str is None:
        return datetime.now(ZoneInfo("Asia/Seoul")).date()
    return datetime.strptime(date_str, "%Y%m%d").date()


@app.command()
def collect(date: str | None = typer.Option(None, "--date")) -> None:
    """선물 원본 데이터를 수집해 저장하고 결과를 JSON으로 출력한다.

    Args:
        date: 대상 거래일(``YYYYMMDD``). 생략하면 KST 기준 오늘.

    성공/실패와 무관하게 결과 JSON을 stdout에 출력하고, 종료코드는
    성공 0 / 실패 1만 쓴다(ddd.md "CLI Presentation 규약").
    """
    target_date = _parse_target_date(date)
    use_case = build_use_case()
    result = use_case.execute(target_date)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False))
    raise typer.Exit(code=0 if result.status == "ok" else 1)


if __name__ == "__main__":
    app()
