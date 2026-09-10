# futures-collector Plan

Spec: [../specs/futures-collector.md](../specs/futures-collector.md)

## 접합부 설계 (Port/Domain/Endpoint 시그니처)

```
Presentation:  future/presentation/cli.py
  Typer app, 명령어 1개: collect(date: str | None = None)
  date 생략 시 KST 기준 오늘 (datetime.now(ZoneInfo("Asia/Seoul")).date())
  결과를 구조화 JSON으로 stdout 출력, exit code 0/1 (ddd.md "CLI Presentation 규약")

Application:   future/application/collect_future_use_case.py
  class CollectFutureUseCase:
      def __init__(self, source: FuturesSourcePort, repo: FutureRepositoryPort)
      def execute(self, target_date: date) -> CollectResult
          raw = self.source.fetch_raw(target_date)
          if not raw: return CollectResult(code="OK_NO_DATA", records=0)
          quotes = (근월/차월 선택 + FutureQuote 파싱, 4건)  # Task2에서 구체화
          self.repo.save(quotes)
          return CollectResult(code="OK_COLLECTED", records=len(quotes))

Ports:         future/application/ports.py
  class FuturesSourcePort(Protocol):
      def fetch_raw(self, target_date: date) -> list[dict]: ...
  class FutureRepositoryPort(Protocol):
      def save(self, quotes: list[FutureQuote]) -> None: ...

Domain:        future/domain/future_quote.py
  class Session(Enum): DAY, NIGHT
  class ContractMonth(Enum): NEAR, NEXT   # 근월/차월
  class FutureQuote: ...
  # Task1(Walking Skeleton)에서는 빈 껍데기(pass)로 시작 — 필드/파싱로직은 Task2에서.
  # 최근월물/차근월물 선택 로직, from_raw() 파싱 등 구체 시그니처도 Task2에서 정한다
  #   (지금 이름 확정 안 함 — vertical-slices.md "Plan 최소추정" 원칙)

Infrastructure: future/infrastructure/adapters/krx_futures_client.py
  class KrxFuturesClient(FuturesSourcePort):
      def __init__(self, username: str, password: str)
      def fetch_raw(self, target_date: date) -> list[dict]
          # 로그인(MDCCOMS001 흐름) + getJsonData.cmd 호출, 3회 지수백오프 재시도
          # 로그인 실패는 재시도 안 하고 즉시 예외

future/infrastructure/adapters/future_parquet_repository.py
  class FutureParquetRepository(FutureRepositoryPort):
      def __init__(self, base_path: Path)
      def save(self, quotes: list[FutureQuote]) -> None
          # 대상일자 파일 있으면 덮어씀 (append 아님)
```

## Phase 1: Walking Skeleton (Stub + Acceptance Test)

- Acceptance Test 1개, **Typer `CliRunner`**로 검증: "CLI `collect` 실행하면 exit 0 + JSON `code: OK_COLLECTED`"
- Stub Green:
  - `FakeFuturesSource`가 스파이크로 확보한 실제 응답(`spikes/krx-futures/findings.md`, `snapshot_0819.json`)을 고정 반환
  - Repository는 in-memory list로 스텁
  - `FutureQuote`는 **빈 껍데기**(`class FutureQuote: pass`) — 필드도 아직 없음. UseCase는 Fake 데이터를 세부검증 없이 개수만 맞춰 통과시킴
  - Acceptance Test는 필드값이 아니라 **레코드 "개수"**(4건)와 exit code/JSON code만 확인
- 이 단계에서 실제 KRX 네트워크 호출/실제 Parquet 파일쓰기 없음
- Port(`FuturesSourcePort`, `FutureRepositoryPort`)는 이 Task에서 정의됨 (뒤 Task들이 이 계약을 구현)

## Phase 2: 실제 구현 (Inside-Out TDD, Stub 하나씩 교체)

1. **Domain** (`FutureQuote` 필드/파싱 + 근월·차월 선택 로직) — Unit Test
   - 콤마 파싱, "-" → None, NIGHT 세션 settlement_price 강제 None
   - 근월/차월 동적 선택 (9월물→12월물 롤오버 케이스를 fixture로 테스트)
2. **Repository** (`FutureParquetRepository`) — Unit Test (임시 디렉토리 fixture)
   - 저장 후 읽으면 값 일치, 같은 날짜 재실행 시 덮어쓰기 확인
3. **Infrastructure Client** (`KrxFuturesClient`) — Unit Test
   - 실제 KRX 서버 호출 안 함 — Fake HTTP transport로 대체 (self-review 계약: 외부 서비스 실제 요청 금지)
   - 로그인 실패 시 즉시 예외(재시도 없음), 네트워크 오류 시 3회 지수백오프 재시도 검증
   - 휴장일(빈 output) 케이스 검증
4. **Wire-up** — CLI에 실제 구현 연결, Acceptance Test 여전히 green (이제 필드값까지 검증하도록 강화)

## Phase 3: 부가 기능

- (없음 — 이 Slice는 수집+저장까지가 전부)

## Tasks (Task = PR 1개 = feature 브랜치 1개)

- [ ] `feature/futures-collector-acceptance` — Port 정의 + Acceptance Test + Stub Green (CliRunner)
- [ ] `feature/futures-collector-domain` — FutureQuote 필드/파싱 + 근월·차월 선택
- [ ] `feature/futures-collector-repository` — FutureParquetRepository 실구현 (Port는 이미 있음, 구현만)
- [ ] `feature/futures-collector-client` — KrxFuturesClient 실구현
- [ ] `feature/futures-collector-wire` — Wire-up, Integration Test

## Milestone 완료 기준

모든 Task 완료 + 위 Integration/Acceptance Test 전부 green.
