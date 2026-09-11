# ADR: 수집기는 원본 그대로 저장, Domain 계층 생략 가능 (Bronze 원칙)

**Status**: Accepted
**Date**: 2026-09-12
**Slice**: Cross-cutting

## Context

futures-collector Spec/Plan 설계 과정에서 처음엔 필드 파싱(콤마제거, "-"→null), 근월/차월 선택, 세션 태깅을 담당하는 Domain 모델(FutureQuote)을 만들려 했다. 그런데 이미 [raw-data-storage-parquet ADR](./2026-09-11-raw-data-storage-parquet.md)에서 "원본을 판단 없이 그대로 보존"하기로 정했다는 걸 다시 확인하면서, Domain 계층에서 하려던 파싱/선택 자체가 이미 "판단"(변환)이라 그 원칙과 모순됨을 발견했다. Medallion Architecture(Bronze/Silver/Gold)의 표준 정의를 확인한 결과 "Bronze holds raw data exactly as it arrived from the source system, with no transformation"이 정설임을 확인했다.

이 결정은 futures-collector뿐 아니라 앞으로 만들 모든 수집기 Slice(공매도, 옵션 등)에 동일하게 적용되는 cross-cutting 원칙이라 별도 ADR로 승격한다.

## Options Considered

| 옵션 | Pros | Cons |
|---|---|---|
| 수집 시점에 파싱/선택/타입변환(Domain 모델) 수행 | 저장 데이터가 바로 쓰기 편함 | Bronze 원칙 위반(판단 개입), 소스 필드명이 바뀌면 수집기까지 고쳐야 함, 필터링한 필드가 나중에 필요해지면 재수집해야 함 |
| Bronze는 원본 그대로 저장, 파싱/선택은 읽는 쪽(Silver 단계, 별도 Slice)이 담당 | 원본 100% 보존(나중에 어떤 필드가 필요해질지 몰라도 안전), 소스 응답 변경에 수집기 자체는 영향 없음, 수집기 Slice가 Domain 계층 없이 단순해짐 | 저장 데이터가 그대로는 안 쓰이고 매번 Silver 단계에서 재해석해야 함 |

## Decision

수집기(Collector) Slice는 외부 소스 응답을 필드명/타입/값 변환 없이 그대로 저장한다(Bronze). 파싱, 타입 변환, 특정 항목 필터링(예: 근월/차월 선택), 세션 구분 같은 해석은 수집기 Slice의 책임이 아니다 — 이 데이터를 읽어서 쓰는 후속 Slice(Silver 단계)의 책임이다.

이에 따라 수집기 Slice는 **Domain 계층을 생략할 수 있다** — 파싱/검증할 게 없으면 Domain 모델 자체가 불필요하다. Application 계층(UseCase)은 Port를 통해 fetch→save만 오케스트레이션한다.

## Rationale

- Medallion Architecture Bronze 계층의 표준 정의("원본 그대로, 변환 없음")를 그대로 따른다.
- 앞서 정한 [raw-data-storage-parquet ADR](./2026-09-11-raw-data-storage-parquet.md)의 "판단 없이 원본 보존" 원칙과 일관성을 유지한다 — 수집 시점에 필드를 고르거나 변환하면 이미 판단이 개입된 것이다.
- 수집기가 단순해진다(Port + Client + Repository만, Domain 없음) — Walking Skeleton도 그만큼 가벼워진다.
- 나중에 새로운 필드가 필요해져도 재수집 없이 이미 저장된 원본에서 다시 뽑아 쓸 수 있다.

## Reconsider When

- 저장 용량/비용이 문제가 될 만큼 불필요한 필드가 많을 때 (그때는 수집 시점 필터링 재검토)
- 소스 응답 자체가 너무 커서(대용량) 원본 그대로 저장이 비효율적일 때

## References

- [raw-data-storage-parquet](./2026-09-11-raw-data-storage-parquet.md)
- [docs/specs/futures-collector.md](../specs/futures-collector.md) — 이 원칙이 처음 적용된 Slice
- Medallion Architecture (Bronze/Silver/Gold) 표준 정의
