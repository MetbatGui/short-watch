from dataclasses import dataclass
from datetime import date

from future.application.ports import FuturesSourcePort, FutureRawRepositoryPort


@dataclass(frozen=True)
class CollectResult:
    status: str
    code: str
    records: int
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "code": self.code,
            "records": self.records,
            "message": self.message,
        }


class CollectFutureUseCase:
    def __init__(self, source: FuturesSourcePort, repo: FutureRawRepositoryPort):
        self._source = source
        self._repo = repo

    def execute(self, target_date: date) -> CollectResult:
        rows = self._source.fetch_raw(target_date)
        if not rows:
            return CollectResult(status="ok", code="OK_NO_DATA", records=0, message="휴장일 또는 데이터 없음")

        self._repo.save_raw(target_date, rows)
        return CollectResult(status="ok", code="OK_COLLECTED", records=len(rows))
