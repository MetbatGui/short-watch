from datetime import date
from pathlib import Path

import pandas as pd


class FutureRawParquetRepository:
    """선물 원본 데이터를 Parquet 파일로 저장하는 어댑터.

    행을 가공하지 않고 그대로 저장한다(Bronze 원칙,
    collector-bronze-no-transformation ADR). 파일은 날짜별로 나뉘며,
    같은 날짜로 다시 저장하면 기존 파일을 덮어쓴다(append 아님).
    """

    def __init__(self, base_path: Path):
        self._base_path = Path(base_path)

    def save_raw(self, target_date: date, rows: list[dict]) -> None:
        """rows를 그대로 DataFrame으로 변환해 Parquet으로 저장한다.

        Args:
            target_date: 데이터가 속한 거래일. 파일명(파티션)을 구분하는 데 쓰인다.
            rows: 저장할 원본 dict 리스트. 필드명/값을 변환하지 않는다.
        """
        self._base_path.mkdir(parents=True, exist_ok=True)
        file_path = self._base_path / f"{target_date.isoformat()}.parquet"
        pd.DataFrame(rows).to_parquet(file_path, index=False)
