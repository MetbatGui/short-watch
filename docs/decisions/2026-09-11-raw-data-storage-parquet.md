# ADR: 원본 데이터 저장소로 Parquet 채택

**Status**: Accepted
**Date**: 2026-09-11
**Slice**: Cross-cutting

## Context

선물, 공매도, 옵션 등 외부 소스(KRX)에서 수집한 원본 데이터를 저장해야 한다. 이 원본 데이터는 외부 API 응답을 그대로 보존하는 성격이라, 나중에 계산 로직(Bear Score 등)이 바뀌어도 다시 계산할 수 있어야 한다.

집계/계산 결과(Bear Score 등)의 저장 방식은 이 ADR의 범위가 아니다 — 별도 결정 시점에 별도 ADR로 다룬다.

## Options Considered

| 옵션 | Pros | Cons |
|---|---|---|
| Parquet (파일 기반) | 자매 프로젝트(stockistics)에서 이미 검증된 패턴 재사용, 스키마/마이그레이션 부담 없음, 컬럼형이라 시계열 원본 데이터에 적합 | 관계형 쿼리(join)는 불편함 |
| RDBMS | 쿼리/조인 용이 | 원본 데이터(외부 API 응답 그대로)를 관계형으로 넣으면 스키마가 API 변경에 취약, 이 시점에 마이그레이션 도구 새로 도입해야 함 |

## Decision

원본 데이터(선물/공매도/옵션 등 외부 소스 raw 데이터)는 Parquet 파일로 저장한다.

## Rationale

- stockistics에서 이미 검증된 저장 패턴 재사용 — 새로 리스크 감수할 이유 없음
- 원본 데이터는 조인/집계 쿼리 대상이 아니라 "나중에 다시 계산하기 위한 근거 데이터"라 컬럼형 파일 저장이 자연스러움
- 계산 결과(Bear Score 등)를 어디에 저장할지는 아직 미정 — raw 저장 방식과 독립적으로 나중에 결정

## Reconsider When

원본 데이터에 대해 실시간 관계형 쿼리가 필요해지는 경우 (현재는 예상 없음).

## References

- [stockistics 프로젝트의 FileRawRepository/ParquetIndexRepository 패턴](https://github.com/MetbatGui/stockistics) (private repo, 내부 참고)
