from dataclasses import dataclass
from datetime import date

from future.application.ports import FuturesSourcePort, FutureRawRepositoryPort


@dataclass(frozen=True)
class CollectResult:
    """수집 실행 결과. CLI가 그대로 JSON으로 출력한다."""

    status: str
    code: str
    records: int
    message: str = ""


class CollectFutureUseCase:
    """선물 원본 데이터를 가져와 저장까지 조율하는 유스케이스."""

    def __init__(self, source: FuturesSourcePort, repo: FutureRawRepositoryPort):
        self._source = source
        self._repo = repo

    def execute(self, target_date: date) -> CollectResult:
        """지정 거래일의 데이터를 수집해 저장한다.

        Args:
            target_date: 수집 대상 거래일(KST 기준).

        Returns:
            수집 결과. 데이터가 없으면(휴장일 등) 저장을 호출하지 않고
            ``OK_NO_DATA``를 반환한다(실패 아님).
        """
        rows = self._source.fetch_raw(target_date)
        if not rows:
            return CollectResult(status="ok", code="OK_NO_DATA", records=0, message="휴장일 또는 데이터 없음")

        self._repo.save_raw(target_date, rows)
        return CollectResult(status="ok", code="OK_COLLECTED", records=len(rows))
