from datetime import date

import pandas as pd
import pytest

from future.infrastructure.adapters.future_raw_parquet_repository import FutureRawParquetRepository


@pytest.mark.unit
def test_save_raw_writes_rows_verbatim(tmp_path, sample_rows):
    """저장한 뒤 읽으면 원본 dict와 값이 정확히 동일하다(가공 없음).

    Given: 임시 디렉토리, 원본 KRX 행 2개
    When: save_raw(target_date, rows) 호출
    Then: Parquet 파일이 생기고, 읽은 내용이 원본과 완전히 동일(콤마 포함 문자열도 그대로)
    """
    repo = FutureRawParquetRepository(base_path=tmp_path)
    target_date = date(2026, 9, 11)

    repo.save_raw(target_date, sample_rows)

    saved_files = list(tmp_path.glob("*.parquet"))
    assert len(saved_files) == 1

    df = pd.read_parquet(saved_files[0])
    assert df.to_dict(orient="records") == sample_rows


@pytest.mark.unit
def test_save_raw_overwrites_existing_data_for_same_date(tmp_path, sample_rows):
    """같은 날짜로 재실행하면 기존 데이터를 덮어쓴다(append 아님).

    Given: 이미 저장된 원본 데이터
    When: 같은 target_date로 다른(더 적은) rows를 다시 save_raw
    Then: 파일에는 새로 넘긴 rows만 남는다(기존 것과 합쳐지지 않음)
    """
    repo = FutureRawParquetRepository(base_path=tmp_path)
    target_date = date(2026, 9, 11)

    repo.save_raw(target_date, sample_rows)
    new_rows = [sample_rows[0]]
    repo.save_raw(target_date, new_rows)

    saved_files = list(tmp_path.glob("*.parquet"))
    assert len(saved_files) == 1

    df = pd.read_parquet(saved_files[0])
    assert df.to_dict(orient="records") == new_rows


@pytest.mark.unit
def test_save_raw_creates_base_path_if_missing(tmp_path, sample_rows):
    """base_path 디렉토리가 없으면 만들어서 저장한다.

    Given: 존재하지 않는 하위 디렉토리 경로
    When: save_raw 호출
    Then: 디렉토리가 생성되고 파일이 저장됨
    """
    nested_path = tmp_path / "futures" / "raw"
    repo = FutureRawParquetRepository(base_path=nested_path)

    repo.save_raw(date(2026, 9, 11), sample_rows)

    assert nested_path.exists()
    assert len(list(nested_path.glob("*.parquet"))) == 1


@pytest.mark.unit
def test_save_raw_separate_dates_produce_separate_files(tmp_path, sample_rows):
    """날짜가 다르면 서로 다른 파일에 저장한다(서로 덮어쓰지 않음).

    Given: 임시 디렉토리
    When: 서로 다른 target_date로 두 번 save_raw
    Then: 파일이 2개 생기고 각각 해당 날짜의 데이터를 담는다
    """
    repo = FutureRawParquetRepository(base_path=tmp_path)

    repo.save_raw(date(2026, 9, 10), [sample_rows[0]])
    repo.save_raw(date(2026, 9, 11), [sample_rows[1]])

    saved_files = sorted(tmp_path.glob("*.parquet"))
    assert len(saved_files) == 2
