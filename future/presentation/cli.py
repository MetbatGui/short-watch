import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import typer

from future.application.collect_future_use_case import CollectFutureUseCase

app = typer.Typer()


def build_use_case() -> CollectFutureUseCase:
    raise NotImplementedError("Wire-up 전 - Task #10에서 실제 구현으로 교체")


def _parse_target_date(date_str: str | None) -> date:
    if date_str is None:
        return datetime.now(ZoneInfo("Asia/Seoul")).date()
    return datetime.strptime(date_str, "%Y%m%d").date()


@app.command()
def collect(date: str | None = typer.Option(None, "--date")) -> None:
    target_date = _parse_target_date(date)
    use_case = build_use_case()
    result = use_case.execute(target_date)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False))
    raise typer.Exit(code=0 if result.status == "ok" else 1)


if __name__ == "__main__":
    app()
