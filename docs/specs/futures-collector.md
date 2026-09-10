# futures-collector Spec

## 개요

KOSPI200 선물(주간/야간, 근월물/차월물) 일별매매정보를 KRX Data Marketplace에서 수집해 원본 데이터를 Parquet으로 저장한다. cronjob이 하루 2번(야간마감 후, 정규장마감 후) CLI를 실행해서 수집한다.

## 입력/출력

**입력**: 없음(CLI 인자로 대상일자 생략 가능 — 생략 시 **KST 기준** 오늘 날짜 사용. 컨테이너 시스템 타임존에 의존하지 않는다). 필요시 `--date YYYYMMDD`로 특정일 재수집 가능.

**출력**: 대상일자의 KOSPI200 선물 데이터가 Parquet 파일로 저장됨.
- 근월물(만기 가장 가까운 계약월) 주간/야간 각 1건, 차월물(그 다음 계약월) 주간/야간 각 1건 — **총 4건**
- 근월물만으론 만기 임박 주간에 유동성이 차월물로 옮겨가는 롤오버 왜곡이 생겨서 둘 다 필요함
- 각 레코드 필드: 거래일, 계약월구분(근월/차월), 종목명, 종가, 시가, 고가, 저가, 전일대비, 현물가, 정산가(주간만 유효, 야간은 null), 누적거래량, 누적거래대금, 미결제약정수량, 세션구분(주간/야간)

**CLI 명령어는 1개**(`collect`). 세션(주간/야간)을 CLI 인자로 구분하지 않는다 — 매 실행마다 근월/차월 × 주간/야간 4건을 전부 조회해서 저장한다. 아직 시작 안 한 세션(예: 06:10 실행 시점의 주간)은 원본 응답 자체가 결측값 위주("-"/0)라 그대로 저장해도, 같은 날짜 재실행 시 덮어쓰기 규칙(아래 AC)에 의해 해당 세션 마감 후 실행에서 정상 값으로 자연 교체된다.

## 데이터 소스 (스파이크로 확인됨)

- Endpoint: `POST https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd`
- 로그인 필요 (KRX_USERNAME/KRX_PASSWORD 환경변수)
- bld: `dbms/MDC/STAT/standard/MDCSTAT12501`, prodId: `KR___FUK2I` (코스피200 선물)
- 참고: `spikes/krx-futures/findings.md` (승인 후 `docs/research/`로 정제 예정)

## Acceptance Criteria

### 정입력 케이스

- 대상일자가 거래일이고 데이터가 존재하면, 응답에서 **근월물+차월물**의 주간/야간 레코드를 각 1건씩, 총 4건 추출해 Parquet에 저장한다.
- 계약월은 하드코딩하지 않는다 — 응답 리스트의 만기순서로 동적으로 근월/차월을 판별한다 (9월물→12월물 롤오버 스파이크로 확인됨).
- 숫자 필드는 콤마 제거 후 숫자로 변환한다. 결측("-")은 null로 저장한다.
- 야간 레코드의 정산가는 항상 null로 저장한다 (구조적으로 KRX가 야간거래 단독정산을 하지 않음 — 스파이크로 확인됨. 이 필드로 이상감지 하지 않는다).

### 오류/예외 케이스

- 대상일자가 휴장일이거나 데이터가 없으면(응답 `output`이 비어있거나 근월/차월 못 찾으면), 실패로 취급하지 않고 정상 종료한다(exit 0, JSON `code: OK_NO_DATA`).
- 로그인 실패(KRX_USERNAME/PASSWORD 누락 또는 인증 실패) 시 즉시 종료한다(재시도 안 함 — 계정 문제는 사람이 확인해야 함). exit 1, `code: ERR_LOGIN_FAILED`.
- KRX 서버 네트워크 오류/타임아웃 시 지수백오프로 최대 3회 재시도 후 실패 처리한다. exit 1, `code: ERR_NETWORK_RETRY_EXHAUSTED`.
- 같은 날짜로 재실행 시(예: 재수집, 세션 미개장 상태에서의 자연 갱신 포함) 기존 Parquet 레코드를 덮어쓴다 — 중복 append 하지 않는다.

### CLI 출력 (ddd.md "CLI Presentation 규약" 참고)

- exit code는 `0`(성공)/`1`(실패)만 쓴다.
- 결과는 구조화된 JSON으로 stdout 출력한다: `{"status": "ok"|"error", "code": "OK_COLLECTED"|"OK_NO_DATA"|"ERR_LOGIN_FAILED"|"ERR_NETWORK_RETRY_EXHAUSTED", "records": N, "message": "..."}`
- 테스트는 Typer `CliRunner`로 검증한다 (`result.exit_code` + `json.loads(result.output)["code"]`).

## 스케줄 (참고, cron 설정은 별도)

- 야간마감(KST 06:00) 이후 **06:10** 실행 — 스파이크로 확정(06:07 시점 이미 거래량 고정 확인됨)
- 정규장마감(KST 15:40 추정) 이후 **15:50** 실행 — 오늘 15:35~ 관찰로 검증 진행 중, 확정되면 갱신

## 설계 경계 (이 Slice 밖)

- 옵션/공매도 데이터 수집은 별도 Slice
- Bear Score 계산(가격×미결제약정 해석 등)은 이 Slice 범위 밖 — 이 Slice는 원본 데이터 저장까지만
- 야간선물 실시간 조회, 표시(프론트엔드)는 범위 밖
