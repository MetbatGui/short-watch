# futures-collector Plan

Spec: [../specs/futures-collector.md](../specs/futures-collector.md)

## 접합부 설계 (Port/Endpoint 시그니처)

Domain 계층 없음 — 이 Slice는 파싱/검증을 하지 않는 순수 Bronze 수집기다.

```
Presentation:  future/presentation/cli.py
  Typer app, 명령어 1개: collect(date: str | None = None)
  date 생략 시 KST 기준 오늘 (datetime.now(ZoneInfo("Asia/Seoul")).date())
  결과를 구조화 JSON으로 stdout 출력, exit code 0/1 (ddd.md "CLI Presentation 규약")

Application:   future/application/collect_future_use_case.py
  class CollectFutureUseCase:
      def __init__(self, source: FuturesSourcePort, repo: FutureRawRepositoryPort)
      def execute(self, target_date: date) -> CollectResult
          rows = self.source.fetch_raw(target_date)
          if not rows: return CollectResult(code="OK_NO_DATA", records=0)
          self.repo.save_raw(target_date, rows)
          return CollectResult(code="OK_COLLECTED", records=len(rows))

Ports:         future/application/ports.py
  class FuturesSourcePort(Protocol):
      def fetch_raw(self, target_date: date) -> list[dict]: ...
  class FutureRawRepositoryPort(Protocol):
      def save_raw(self, target_date: date, rows: list[dict]) -> None: ...

Infrastructure: future/infrastructure/adapters/krx_futures_client.py
  class KrxFuturesClient(FuturesSourcePort):
      def __init__(self, username: str, password: str)
      def fetch_raw(self, target_date: date) -> list[dict]
          # 로그인(MDCCOMS001 흐름) + getJsonData.cmd 호출, 3회 지수백오프 재시도
          # 로그인 실패는 재시도 안 하고 즉시 예외
          # 반환값은 KRX 응답 output 배열 그대로 (필드명/값 변환 없음)

future/infrastructure/adapters/future_raw_parquet_repository.py
  class FutureRawParquetRepository(FutureRawRepositoryPort):
      def __init__(self, base_path: Path)
      def save_raw(self, target_date: date, rows: list[dict]) -> None
          # rows를 그대로 DataFrame으로 변환(pd.DataFrame(rows)) 후 Parquet 저장
          # 파일 경로/파티션은 target_date로 구분, 같은 날짜 재실행 시 덮어씀
          # 행 내부 값은 가공하지 않음 (KRX가 준 문자열/필드명 그대로)
```

## Phase 1: Walking Skeleton (Stub + Acceptance Test)

- Acceptance Test 1개, **Typer `CliRunner`**로 검증: "CLI `collect` 실행하면 exit 0 + JSON `code: OK_COLLECTED` + records 개수 일치"
- Stub Green:
  - `FakeFuturesSource`가 스파이크로 확보한 실제 응답(`spikes/krx-futures/findings.md`, `snapshot_0819.json`)을 고정 반환
  - Repository는 in-memory list로 스텁
- 이 단계에서 실제 KRX 네트워크 호출/실제 Parquet 파일쓰기 없음
- Port(`FuturesSourcePort`, `FutureRawRepositoryPort`)는 이 Task에서 정의됨

## Phase 2: 실제 구현

1. **Infrastructure Client** (`KrxFuturesClient`) — Unit Test
   - 실제 KRX 서버 호출 안 함 — Fake HTTP transport로 대체
   - 로그인 실패 시 즉시 예외(재시도 없음), 네트워크 오류 시 3회 지수백오프 재시도 검증
   - 휴장일(빈 output) 케이스 검증
   - 반환값이 KRX 원본 그대로인지 확인(필드 변형 없음을 검증하는 것 자체가 테스트 포인트)
2. **Repository** (`FutureRawParquetRepository`) — Unit Test (임시 디렉토리 fixture)
   - 저장 후 읽으면 원본 dict와 값 일치(타입까지 그대로, 콤마 포함 문자열 그대로)
   - 같은 날짜 재실행 시 덮어쓰기 확인
3. **Wire-up** — CLI에 실제 구현 연결, Acceptance Test 여전히 green

## Phase 3: 부가 기능

- (없음)

## Tasks (Task = PR 1개 = feature 브랜치 1개)

- [ ] `feature/futures-collector-acceptance` — Port 정의 + Acceptance Test + Stub Green (CliRunner)
- [ ] `feature/futures-collector-client` — KrxFuturesClient 실구현
- [ ] `feature/futures-collector-repository` — FutureRawParquetRepository 실구현
- [ ] `feature/futures-collector-wire` — Wire-up, Integration Test

## Milestone 완료 기준

모든 Task 완료 + 위 Integration/Acceptance Test 전부 green.
