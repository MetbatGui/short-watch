from datetime import date
from typing import Protocol


class FuturesSourcePort(Protocol):
    """선물 원본 데이터를 가져오는 소스에 대한 계약."""

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
        ...


class FutureRawRepositoryPort(Protocol):
    """선물 원본 데이터를 저장하는 저장소에 대한 계약."""

    def save_raw(self, target_date: date, rows: list[dict]) -> None:
        """행을 가공 없이 그대로 저장한다.

        같은 target_date로 다시 호출하면 기존 데이터를 덮어쓴다(append 아님).

        Args:
            target_date: 데이터가 속한 거래일. 저장 위치(파티션)를 구분하는 데 쓰인다.
            rows: 저장할 원본 dict 리스트. 필드명/값을 변환하지 않는다.
        """
        ...
