# ADR: 수집기 실행 방식 — Cron+CLI로 시작, 워커풀은 나중

**Status**: Accepted
**Date**: 2026-09-11
**Slice**: Cross-cutting

## Context

[collector-separate-container](./2026-09-11-collector-separate-container.md) ADR에서 수집기를 웹서비스와 별도 컨테이너로 분리하고, "컨테이너 내부에서 소스별 워커를 asyncio/멀티프로세스로 병렬 실행"하기로 했다.

실제 첫 슬라이스(선물 수집) 설계 단계에서, 지금 시점에 상시 워커풀까지 만들 필요가 있는지 재검토했다. 현재 소스는 KRX, DART 정도로 적고, 각 소스의 갱신 시점도 하루 몇 번(정규장마감, 야간선물마감 등)으로 정해져 있다.

## Options Considered

| 옵션 | Pros | Cons |
|---|---|---|
| 상시 워커풀 (asyncio/멀티프로세스로 계속 떠있는 프로세스) | 소스 늘어나도 구조 그대로 확장, 실시간성 대응 가능 | 프로세스 생존관리·헬스체크·graceful shutdown 등 운영부담이 지금 필요 이상으로 큼 |
| Cron + CLI (그때그때 CLI 실행, 끝나면 프로세스 종료) | 운영 단순, 각 실행이 독립적이라 실패해도 다음 cron이 알아서 재시도, 디버깅이 "이번 실행 로그" 단위로 단순함 | 소스 늘어나면 cron 스케줄 관리가 번거로워질 수 있음, 초 단위 실시간성 대응 불가 |

## Decision

수집기는 cronjob이 CLI를 실행하는 방식으로 시작한다. CLI는 `CollectFutureUseCase` 같은 유스케이스를 호출해 그 시점에 한 번 수집하고 종료한다. 상시 워커풀은 지금 만들지 않는다.

## Rationale

- 지금은 소스 수가 적고 갱신 시점이 하루 몇 번으로 정해져 있어 상시 워커가 딱히 이득이 없다 — cron이 그 타이밍에 맞춰 알아서 깨워준다.
- 상시 워커풀은 지금 필요 없는 운영 복잡도(프로세스 생존관리, 헬스체크, graceful shutdown)를 같이 끌고 온다.
- Cron+CLI는 각 실행이 독립적이라 실패 격리와 재시도가 자연스럽고, 디버깅 단위가 단순하다.
- [collector-separate-container](./2026-09-11-collector-separate-container.md) ADR의 "별도 컨테이너, 소스별 병렬" 원칙은 그대로 유지된다 — 이 ADR은 그 컨테이너 안에서 "지금 당장 무엇으로 병렬을 구현하나"에 대한 실행 방식만 구체화한다.

## Reconsider When

- 소스 수가 늘어나 cron 스케줄이 서로 겹치거나 관리가 힘들어질 때
- 초 단위 반응이 필요한 실시간성 소스가 생길 때 (cron은 최소 분 단위 스케줄이 한계)
- 소스 간 상태 공유(하나 실패하면 다른 것도 잠깐 멈춰야 하는 등)가 필요해질 때

이 경우 상시 워커풀 도입을 재검토한다.

## References

- [collector-separate-container](./2026-09-11-collector-separate-container.md)
